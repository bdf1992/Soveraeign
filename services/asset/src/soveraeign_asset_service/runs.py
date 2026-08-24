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
import json

from soveraeign_asset_service.authority import Authority
from soveraeign_asset_service.store import Store, new_id


SCHEMA = """
CREATE TABLE IF NOT EXISTS runs(
  id TEXT PRIMARY KEY, kind TEXT NOT NULL, asset_id TEXT NOT NULL,
  input_version_id TEXT NOT NULL, requester TEXT NOT NULL,
  status TEXT NOT NULL, worker TEXT, lease_fence INTEGER NOT NULL DEFAULT 0,
  lease_expires REAL, output_version_id TEXT, report_json TEXT,
  observation_id TEXT, created_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS observations(
  id TEXT PRIMARY KEY, run_id TEXT NOT NULL, observer TEXT NOT NULL,
  evidence_json TEXT NOT NULL, passed INTEGER NOT NULL,
  created_at REAL NOT NULL);
"""

DEFAULT_LEASE_TTL_SECONDS = 60.0


class StaleLease(RuntimeError):
    """A worker reported against a lease it no longer holds."""


class Runs:
    """The leased-derivation lifecycle for one service root."""

    def __init__(self, store: Store, authority: Authority) -> None:
        self.store = store
        self.authority = authority
        self.db = store.db
        self.now = store.now

    def request(self, asset_id: str, version_id: str, actor: str,
                kind: str = "metadata-card") -> str:
        """Request a derived version. The request is an attempt, not a result."""
        self.authority.require(actor, "operate:derive", asset_id, "asset", asset_id)
        run = new_id("run")
        self.db.execute(
            "INSERT INTO runs(id,kind,asset_id,input_version_id,requester,status,created_at) "
            "VALUES(?,?,?,?,?,'PENDING',?)",
            (run, kind, asset_id, version_id, actor, self.now()))
        self.store.receipt("ATTEMPTED", "operation.request", "run", run, actor,
                           {"kind": kind, "input_version_id": version_id})
        self.db.commit()
        return run

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
            "UPDATE runs SET status='LEASED',worker=?,lease_fence=?,lease_expires=? WHERE id=?",
            (worker, fence, self.now() + ttl_seconds, run_id))
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
        derivation = {"operation": run["kind"], "run_id": run_id,
                      "input_version_id": run["input_version_id"], "lossy": True}
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
        self.db.execute("UPDATE runs SET status=?,observation_id=? WHERE id=?",
                        (status, observation, run_id))
        self.store.receipt(status, "operation.observe", "run", run_id, observer, evidence)
        self.db.commit()
        return observation
