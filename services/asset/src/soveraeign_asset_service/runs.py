"""Leased derivation runs: request, claim, report, and observe.

Reports never settle themselves; observation reads durable output independently.
"""

from __future__ import annotations

from hashlib import sha256
from typing import Any
import json

from soveraeign_asset_service.authority import Authority
from soveraeign_asset_service.reconstruction import RecordingReconstructor
from soveraeign_asset_service.recording import (
    ConfigurationChanged,
    ReaderChanged,
    ReaderDeclaration,
    ReaderMaterials,
    ReaderUndeclared,
    ReconstructionError,
    SourceChanged,
)
from soveraeign_asset_service.store import PayloadIntegrityError, Store, new_id


SCHEMA = """
CREATE TABLE IF NOT EXISTS runs(
  id TEXT PRIMARY KEY, kind TEXT NOT NULL, asset_id TEXT NOT NULL,
  input_version_id TEXT NOT NULL, requester TEXT NOT NULL,
  status TEXT NOT NULL, worker TEXT, lease_fence INTEGER NOT NULL DEFAULT 0,
  lease_expires REAL, output_version_id TEXT, report_json TEXT,
  observation_id TEXT, created_at REAL NOT NULL,
  started_at REAL, completed_at REAL);
CREATE TABLE IF NOT EXISTS observations(
  id TEXT PRIMARY KEY, run_id TEXT NOT NULL, observer TEXT NOT NULL,
  evidence_json TEXT NOT NULL, passed INTEGER NOT NULL,
  created_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS derivative_plans(
  run_id TEXT PRIMARY KEY REFERENCES runs(id),
  source_id TEXT NOT NULL, source_digest TEXT NOT NULL,
  reader_id TEXT NOT NULL, reader_version TEXT NOT NULL,
  reader_address TEXT NOT NULL, reader_digest TEXT NOT NULL,
  configuration_address TEXT NOT NULL, configuration_digest TEXT NOT NULL,
  output_role TEXT NOT NULL, fidelity TEXT NOT NULL, omissions_json TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS recordings(
  id TEXT PRIMARY KEY, run_id TEXT NOT NULL UNIQUE REFERENCES runs(id),
  output_version_id TEXT NOT NULL UNIQUE REFERENCES versions(id),
  source_id TEXT NOT NULL, source_digest TEXT NOT NULL,
  reader_id TEXT NOT NULL, reader_version TEXT NOT NULL,
  reader_address TEXT NOT NULL, reader_digest TEXT NOT NULL,
  configuration_address TEXT NOT NULL, configuration_digest TEXT NOT NULL,
  output_role TEXT NOT NULL, payload_address TEXT NOT NULL,
  payload_digest TEXT NOT NULL, fidelity TEXT NOT NULL,
  omissions_json TEXT NOT NULL, produced_at REAL NOT NULL,
  produced_by TEXT NOT NULL, standing TEXT NOT NULL);
"""

DEFAULT_LEASE_TTL_SECONDS = 60.0

# Existing stores need the timing columns because CREATE TABLE IF NOT EXISTS does
# not advance their schema. SQLite honestly fills historical rows with NULL.
TIMING_COLUMNS = (("started_at", "REAL"), ("completed_at", "REAL"))


class StaleLease(RuntimeError):
    """A worker reported against a lease it no longer holds."""


class Runs:
    """The leased-derivation lifecycle for one service root."""

    def __init__(self, store: Store, authority: Authority) -> None:
        self.store = store
        self.authority = authority
        self.db = store.db
        self.now = store.now
        self.readers = ReaderMaterials(store)
        self.reconstructor = RecordingReconstructor(store, self.readers)
        self._add_timing_columns()

    def _add_timing_columns(self) -> None:
        """Bring a store written before the timing columns existed up to the schema."""
        held = {row["name"] for row in self.db.execute("PRAGMA table_info(runs)")}
        for column, kind in TIMING_COLUMNS:
            if column not in held:
                self.db.execute(f"ALTER TABLE runs ADD COLUMN {column} {kind}")
        self.db.commit()

    def request(self, asset_id: str, version_id: str | list[str], actor: str,
                kind: str = "metadata-card",
                reader: ReaderDeclaration | None = None) -> str:
        """Request a derived version from one input version, or from several.

        Composition is this operation with more than one input, not a separate
        kind of asset: an assembly of several versions is derived from all of
        them, and the derivation records every one so the result can be rebuilt
        and attributed. A single input is stored as a list of one, so a reader
        never has to handle two shapes.
        """
        inputs = [version_id] if isinstance(version_id, str) else list(version_id)
        if not inputs:
            raise ValueError("a derivation needs at least one input version")
        self.authority.require(actor, "operate:derive", asset_id, "asset", asset_id)
        plan: dict[str, str] | None = None
        if reader is not None:
            try:
                if len(inputs) != 1:
                    raise ReaderUndeclared("a recording requires exactly one source version")
                reader.validate()
                source, _ = self.store.verified_version(inputs[0])
                if source["asset_id"] != asset_id:
                    raise ReaderUndeclared("source version does not belong to the asset")
                plan = self.readers.materialize(reader)
                plan.update({"source_id": inputs[0],
                             "source_digest": f"sha256:{source['digest']}"})
            except (ConfigurationChanged, PayloadIntegrityError,
                    ReaderChanged, ReaderUndeclared) as error:
                reason = "SOURCE_CHANGED" if isinstance(error, PayloadIntegrityError) \
                    else error.reason_code
                self.store.receipt("REFUSED", "asset.request-derivative", "asset",
                                   asset_id, actor, {"reason": reason})
                self.db.commit()
                if isinstance(error, PayloadIntegrityError):
                    raise SourceChanged(inputs[0]) from error
                raise
        run = new_id("run")
        self.db.execute(
            "INSERT INTO runs(id,kind,asset_id,input_version_id,requester,status,created_at) "
            "VALUES(?,?,?,?,?,'PENDING',?)",
            (run, kind, asset_id, json.dumps(inputs), actor, self.now()))
        payload: dict[str, Any] = {"kind": kind, "input_version_ids": inputs,
                                   "composite": len(inputs) > 1}
        if plan is not None and reader is not None:
            self.db.execute(
                "INSERT INTO derivative_plans VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (run, plan["source_id"], plan["source_digest"], reader.reader_id,
                 reader.reader_version, plan["reader_address"], plan["reader_digest"],
                 plan["configuration_address"], reader.configuration_digest,
                 reader.output_role, reader.fidelity, json.dumps(reader.omissions)))
            payload.update({"reader_id": reader.reader_id,
                            "reader_version": reader.reader_version,
                            "source_digest": plan["source_digest"]})
        self.store.receipt("ATTEMPTED", "asset.request-derivative", "run", run,
                           actor, payload)
        self.db.commit()
        return run

    @staticmethod
    def inputs_of(run: Any) -> list[str]:
        """The input versions of a run, whether stored as one id or as a list."""
        stored = run["input_version_id"]
        if stored.startswith("["):
            return json.loads(stored)
        return [stored]

    def claim(self, run_id: str, worker: str,
              ttl_seconds: float = DEFAULT_LEASE_TTL_SECONDS) -> int:
        """Lease a run to one worker and return the fencing token it must report with."""
        row = self.db.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        if row is None:
            raise KeyError(run_id)
        if row["status"] not in ("PENDING", "LEASED"):
            raise RuntimeError("run is not claimable")
        if row["status"] == "LEASED" and (row["lease_expires"] or 0) > self.now():
            raise RuntimeError("active lease exists")
        fence = row["lease_fence"] + 1
        self.db.execute(
            "UPDATE runs SET status='LEASED',worker=?,lease_fence=?,lease_expires=?,"
            "started_at=COALESCE(started_at,?) WHERE id=?",
            (worker, fence, self.now() + ttl_seconds, self.now(), run_id))
        self.store.receipt("COMMITTED", "lease.claim", "run", run_id, worker,
                           {"fence": fence, "ttl_seconds": ttl_seconds})
        self.db.commit()
        return fence

    def report(self, run_id: str, worker: str, fence: int, output: bytes,
               mime: str = "application/json") -> str:
        """Accept a worker's report. A report is not an observation and settles nothing."""
        run = self.db.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        if (run is None or run["worker"] != worker or run["lease_fence"] != fence
                or (run["lease_expires"] or 0) <= self.now() or run["status"] != "LEASED"):
            if run is not None:
                self.store.receipt("REFUSED", "operation.report", "run", run_id, worker,
                                   {"reason": "STALE_LEASE", "fence": fence})
                self.db.commit()
            raise StaleLease(run_id)
        inputs = self.inputs_of(run)
        plan = self.db.execute(
            "SELECT * FROM derivative_plans WHERE run_id=?", (run_id,)
        ).fetchone()
        if plan is not None:
            try:
                self.readers.resolve(plan)
                source, _ = self.store.verified_version(plan["source_id"])
                if f"sha256:{source['digest']}" != plan["source_digest"]:
                    raise SourceChanged(plan["source_id"])
            except (ConfigurationChanged, ReaderChanged,
                    PayloadIntegrityError, SourceChanged) as error:
                reason = "SOURCE_CHANGED" if isinstance(error, PayloadIntegrityError) \
                    else error.reason_code
                self._refuse(run_id, worker, reason)
                if isinstance(error, PayloadIntegrityError):
                    raise SourceChanged(plan["source_id"]) from error
                raise
        digest, blob = self.store.store_blob(output)
        version = new_id("version")
        recording = new_id("recording") if plan is not None else None
        derivation = {"operation": run["kind"], "run_id": run_id,
                      "input_version_ids": inputs, "composite": len(inputs) > 1,
                      "lossy": True}
        if recording is not None:
            derivation["recording_id"] = recording
        self.db.execute("INSERT INTO versions VALUES(?,?,?,?,?,?,?,?,?,?)",
                        (version, run["asset_id"], None, digest, mime, len(output),
                         str(blob), "DERIVATIVE", json.dumps(derivation, sort_keys=True),
                         self.now()))
        if plan is not None and recording is not None:
            payload_digest = f"sha256:{digest}"
            self.db.execute(
                "INSERT INTO recordings VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (recording, run_id, version, plan["source_id"], plan["source_digest"],
                 plan["reader_id"], plan["reader_version"], plan["reader_address"],
                 plan["reader_digest"], plan["configuration_address"],
                 plan["configuration_digest"], plan["output_role"],
                 f"cas:{payload_digest}", payload_digest, plan["fidelity"],
                 plan["omissions_json"], self.now(), worker, "RECORDED"))
        self.db.execute(
            "UPDATE runs SET status='REPORTED',output_version_id=?,report_json=? WHERE id=?",
            (version, json.dumps({"digest": digest, "recording_id": recording}), run_id))
        receipt_payload = {"output_version_id": version, "digest": digest}
        if recording is not None:
            receipt_payload["recording_id"] = recording
        self.store.receipt("ATTEMPTED", "operation.report", "run", run_id, worker,
                           receipt_payload)
        self.db.commit()
        return version

    def observe(self, run_id: str, observer: str) -> str:
        """Check a reported run against its durable output, not against its report."""
        run = self.db.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        if run is None or run["status"] != "REPORTED":
            raise RuntimeError("run has no independently observable report")
        plan = self.db.execute(
            "SELECT 1 FROM derivative_plans WHERE run_id=?", (run_id,)
        ).fetchone()
        if plan is not None:
            try:
                recording = self.reconstructor.reconstruct(run["output_version_id"])
                passed = True
                evidence = {key: recording[key] for key in
                            ("recording_id", "source_digest", "reader_digest",
                             "configuration_digest", "payload_digest")}
            except (KeyError, ReaderUndeclared, ReconstructionError) as error:
                passed = False
                evidence = {"reason": getattr(error, "reason_code", "RECORDING_MISSING")}
        else:
            version, data = self.store.verified_version(run["output_version_id"])
            passed = sha256(data).hexdigest() == version["digest"]
            evidence = {"digest": sha256(data).hexdigest(), "size": len(data),
                        "exists": True}
        observation = new_id("obs")
        self.db.execute("INSERT INTO observations VALUES(?,?,?,?,?,?)",
                        (observation, run_id, observer, json.dumps(evidence, sort_keys=True),
                         int(passed), self.now()))
        status = "COMMITTED" if passed else "FAILED"
        self.db.execute(
            "UPDATE runs SET status=?,observation_id=?,completed_at=? WHERE id=?",
            (status, observation, self.now(), run_id))
        self.store.receipt(status, "operation.observe", "run", run_id, observer, evidence)
        self.db.commit()
        return observation

    def _refuse(self, run_id: str, actor: str, reason: str) -> None:
        self.db.execute("UPDATE runs SET status='REFUSED' WHERE id=?", (run_id,))
        self.store.receipt("REFUSED", "operation.report", "run", run_id, actor,
                           {"reason": reason})
        self.db.commit()

    def reconstruct(self, recording_or_version_id: str) -> dict[str, Any]:
        """Resolve a recording by its own id or its output-version id."""
        return self.reconstructor.reconstruct(recording_or_version_id)

    def elapsed(self, run_id: str) -> float | None:
        """Wall clock from first lease to terminal observation, or None if open.

        Request time is not work time. This is WALLCLOCK only, never cost,
        budget, or valuation.
        """
        row = self.db.execute(
            "SELECT started_at, completed_at FROM runs WHERE id=?", (run_id,)).fetchone()
        if row is None:
            raise KeyError(run_id)
        if row["started_at"] is None or row["completed_at"] is None:
            return None
        return row["completed_at"] - row["started_at"]
