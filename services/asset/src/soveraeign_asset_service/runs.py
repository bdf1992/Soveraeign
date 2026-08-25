"""Leased derivation runs: request, claim, report, observe.

The four states this module moves a run through are deliberately not one step.
A request is an attempt. A lease is exclusive and carries a fencing token, so a
worker whose lease expired cannot report over a newer holder. A report is the
worker's own claim about what it did. Only observation reads the durable output
independently of that report and decides whether the run committed
(`AGENTS.md`, State and execution: workers may emit reports; independent
observation decides whether a run committed).
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any
import json

from soveraeign_asset_service.authority import Authority
from soveraeign_asset_service.store import Store, new_id


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
"""

DEFAULT_LEASE_TTL_SECONDS = 60.0

#: Columns added to `runs` after the table shipped. `CREATE TABLE IF NOT EXISTS` leaves
#: an existing store untouched, so a store written before 2026-08-24 would keep a table
#: with no timing columns and fail on the first claim. Adding them on open is cheaper
#: than a migration record and cannot lose data: SQLite fills the existing rows with
#: NULL, which is the honest value for a run nobody timed.
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
        self._add_timing_columns()

    def _add_timing_columns(self) -> None:
        """Bring a store written before the timing columns existed up to the schema."""
        held = {row["name"] for row in self.db.execute("PRAGMA table_info(runs)")}
        for column, kind in TIMING_COLUMNS:
            if column not in held:
                self.db.execute(f"ALTER TABLE runs ADD COLUMN {column} {kind}")
        self.db.commit()

    def request(self, asset_id: str, version_id: str | list[str], actor: str,
                kind: str = "metadata-card") -> str:
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
        run = new_id("run")
        self.db.execute(
            "INSERT INTO runs(id,kind,asset_id,input_version_id,requester,status,created_at) "
            "VALUES(?,?,?,?,?,'PENDING',?)",
            (run, kind, asset_id, json.dumps(inputs), actor, self.now()))
        self.store.receipt("ATTEMPTED", "asset.request-derivative", "run", run, actor,
                           {"kind": kind, "input_version_ids": inputs,
                            "composite": len(inputs) > 1})
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
        digest, blob = self.store.store_blob(output)
        version = new_id("version")
        inputs = self.inputs_of(run)
        derivation = {"operation": run["kind"], "run_id": run_id,
                      "input_version_ids": inputs, "composite": len(inputs) > 1,
                      "lossy": True}
        self.db.execute("INSERT INTO versions VALUES(?,?,?,?,?,?,?,?,?,?)",
                        (version, run["asset_id"], None, digest, mime, len(output),
                         str(blob), "DERIVATIVE", json.dumps(derivation, sort_keys=True),
                         self.now()))
        self.db.execute(
            "UPDATE runs SET status='REPORTED',output_version_id=?,report_json=? WHERE id=?",
            (version, json.dumps({"digest": digest}), run_id))
        self.store.receipt("ATTEMPTED", "operation.report", "run", run_id, worker,
                           {"output_version_id": version, "digest": digest})
        self.db.commit()
        return version

    def observe(self, run_id: str, observer: str) -> str:
        """Check a reported run against its durable output, not against its report."""
        run = self.db.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        if run is None or run["status"] != "REPORTED":
            raise RuntimeError("run has no independently observable report")
        version = self.db.execute("SELECT * FROM versions WHERE id=?",
                                  (run["output_version_id"],)).fetchone()
        data = Path(version["blob_path"]).read_bytes()
        passed = sha256(data).hexdigest() == version["digest"] and len(data) == version["size"]
        observation = new_id("obs")
        evidence = {"digest": sha256(data).hexdigest(), "size": len(data), "exists": True}
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

    def elapsed(self, run_id: str) -> float | None:
        """Wall clock from the first lease to the terminal observation, or None if open.

        `SPEC.md`'s `Run` declares `started_at` and `completed_at`; before 2026-08-24
        this table carried only `created_at`, so the elapsed time of a delegated run
        was not recoverable even in principle. Request time is deliberately not the
        start: a run that waited an hour for a worker did not take an hour of work,
        and reporting the queue as effort would inflate every measure taken from it.

        This is WALLCLOCK and nothing else. It is not a cost, not a budget, and not a
        valuation; those are separate measures and collapsing them here is the defeat
        this docstring exists to refuse.
        """
        row = self.db.execute(
            "SELECT started_at, completed_at FROM runs WHERE id=?", (run_id,)).fetchone()
        if row is None:
            raise KeyError(run_id)
        if row["started_at"] is None or row["completed_at"] is None:
            return None
        return row["completed_at"] - row["started_at"]
