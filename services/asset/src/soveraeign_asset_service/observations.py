"""Independent durable-output observations for Asset Service runs."""

from __future__ import annotations

import json

from .control import ControlLedger
from .derivatives import DerivativeLifecycle
from .recording import ReaderUndeclared, ReconstructionError
from .storage import AssetStore, new_id, now


class RunObservations:
    """Observe durable run outputs without relying on worker reports."""

    def __init__(
        self,
        store: AssetStore,
        control: ControlLedger,
        derivatives: DerivativeLifecycle,
    ):
        self.store = store
        self.db = store.db
        self.control = control
        self.derivatives = derivatives

    def observe(self, run_id: str, observer: str) -> str:
        """Verify the durable output and record the observed outcome."""
        run = self.db.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        if run is None or run["status"] != "REPORTED":
            raise RuntimeError("run has no independently observable report")
        try:
            recording = self.derivatives.reconstruct(run["output_version_id"])
            passed = True
            evidence = {
                "configuration_digest": recording["configuration_digest"],
                "payload_digest": recording["payload_digest"],
                "reader_digest": recording["reader_digest"],
                "recording_id": recording["recording_id"],
                "source_digest": recording["source_digest"],
            }
        except ReconstructionError as error:
            passed = False
            evidence = {"reason": error.reason_code}
        except ReaderUndeclared as error:
            passed = False
            evidence = {"reason": error.reason_code}
        except (KeyError, ValueError):
            passed = False
            evidence = {"reason": "RECORDING_MISSING"}
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
