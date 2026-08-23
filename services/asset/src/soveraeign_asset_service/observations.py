"""Independent durable-output observations for Asset Service runs."""

from __future__ import annotations

import json

from .control import ControlLedger
from .storage import AssetStore, PayloadIntegrityError, new_id, now


class RunObservations:
    """Observe durable run outputs without relying on worker reports."""

    def __init__(self, store: AssetStore, control: ControlLedger):
        self.store = store
        self.db = store.db
        self.control = control

    def observe(self, run_id: str, observer: str) -> str:
        """Verify the durable output and record the observed outcome."""
        run = self.db.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        if run is None or run["status"] != "REPORTED":
            raise RuntimeError("run has no independently observable report")
        try:
            version, data = self.store.verified_version(run["output_version_id"])
            passed = True
            evidence = {
                "digest": f"sha256:{version['digest']}",
                "size": len(data),
                "exists": True,
            }
        except PayloadIntegrityError:
            passed = False
            evidence = {"digest": None, "size": None, "exists": False}
        observation_id = new_id("obs")
        self.db.execute(
            "INSERT INTO observations VALUES(?,?,?,?,?,?)",
            (
                observation_id,
                run_id,
                observer,
                json.dumps(evidence, sort_keys=True),
                int(passed),
                now(),
            ),
        )
        status = "COMMITTED" if passed else "FAILED"
        self.db.execute(
            "UPDATE runs SET status=?,observation_id=? WHERE id=?",
            (status, observation_id, run_id),
        )
        self.control.receipt(
            status, "operation.observe", "run", run_id, observer, evidence
        )
        self.db.commit()
        return observation_id
