"""Reconstructable derivative execution and observation lifecycle."""

from __future__ import annotations

import json
from typing import Any

from .control import ControlLedger
from .recording import (
    ReaderDeclaration, ReaderUndeclared, RecordingChanged, SourceChanged, StaleLease,
)
from .storage import AssetStore, PayloadIntegrityError, new_id, now


class DerivativeLifecycle:
    """Own declared derivative runs without owning authority or storage mechanics."""

    def __init__(self, store: AssetStore, control: ControlLedger):
        self.store = store
        self.db = store.db
        self.control = control

    def request(
        self,
        asset_id: str,
        version_id: str,
        actor: str,
        reader: ReaderDeclaration | None,
        kind: str,
    ) -> str:
        """Declare a reconstructable derivative operation before leasing work."""
        self.control.require(actor, "operate:derive", asset_id, "asset", asset_id)
        try:
            if not isinstance(reader, ReaderDeclaration):
                raise ReaderUndeclared("reader must be a ReaderDeclaration")
            reader.validate()
            source_version, _ = self.store.verified_version(version_id)
            if source_version["asset_id"] != asset_id:
                raise ReaderUndeclared("source version does not belong to the asset")
        except (PayloadIntegrityError, ReaderUndeclared) as error:
            integrity_failed = isinstance(error, PayloadIntegrityError)
            reason = "SOURCE_CHANGED" if integrity_failed else "READER_UNDECLARED"
            self.control.receipt(
                "REFUSED",
                "operation.request",
                "asset",
                asset_id,
                actor,
                {"reason": reason, "source_id": version_id},
            )
            self.db.commit()
            if integrity_failed:
                raise SourceChanged(version_id) from error
            raise
        run_id = new_id("run")
        source_digest = f"sha256:{source_version['digest']}"
        self.db.execute(
            "INSERT INTO runs(id,kind,asset_id,input_version_id,requester,status,created_at) "
            "VALUES(?,?,?,?,?,'PENDING',?)",
            (run_id, kind, asset_id, version_id, actor, now()),
        )
        self.db.execute(
            "INSERT INTO derivative_plans VALUES(?,?,?,?,?,?,?,?,?)",
            (
                run_id,
                version_id,
                source_digest,
                reader.reader_id,
                reader.reader_version,
                reader.configuration_digest,
                reader.output_role,
                reader.fidelity,
                json.dumps(reader.omissions),
            ),
        )
        self.control.receipt(
            "ATTEMPTED",
            "operation.request",
            "run",
            run_id,
            actor,
            {
                "kind": kind,
                "source_id": version_id,
                "source_digest": source_digest,
                "reader_id": reader.reader_id,
                "reader_version": reader.reader_version,
                "configuration_digest": reader.configuration_digest,
                "fidelity": reader.fidelity,
                "omissions": list(reader.omissions),
            },
        )
        self.db.commit()
        return run_id

    def claim(self, run_id: str, worker: str, ttl_seconds: float) -> int:
        """Lease one pending derivative run with an increasing fence."""
        run = self.db.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        if run is None:
            raise KeyError(run_id)
        if run["status"] not in ("PENDING", "LEASED"):
            raise RuntimeError("run is not claimable")
        if run["status"] == "LEASED" and (run["lease_expires"] or 0) > now():
            raise RuntimeError("active lease exists")
        fence = run["lease_fence"] + 1
        self.db.execute(
            "UPDATE runs SET status='LEASED',worker=?,lease_fence=?,lease_expires=? WHERE id=?",
            (worker, fence, now() + ttl_seconds, run_id),
        )
        self.control.receipt(
            "COMMITTED", "lease.claim", "run", run_id, worker,
            {"fence": fence, "ttl_seconds": ttl_seconds},
        )
        self.db.commit()
        return fence

    def report(
        self,
        run_id: str,
        worker: str,
        fence: int,
        output: bytes,
        mime: str,
    ) -> str:
        """Record worker output without treating the report as settlement."""
        run = self.db.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        if (
            run is None
            or run["worker"] != worker
            or run["lease_fence"] != fence
            or (run["lease_expires"] or 0) <= now()
            or run["status"] != "LEASED"
        ):
            if run is not None:
                self.control.receipt(
                    "REFUSED",
                    "operation.report",
                    "run",
                    run_id,
                    worker,
                    {"reason": "STALE_LEASE", "fence": fence},
                )
                self.db.commit()
            raise StaleLease(run_id)
        plan = self.db.execute(
            "SELECT * FROM derivative_plans WHERE run_id=?", (run_id,)
        ).fetchone()
        if plan is None:
            self._refuse(run_id, worker, "READER_UNDECLARED")
            raise ReaderUndeclared(run_id)
        try:
            source_version, _ = self.store.verified_version(plan["source_id"])
        except PayloadIntegrityError as error:
            self._refuse(run_id, worker, "SOURCE_CHANGED")
            raise SourceChanged(plan["source_id"]) from error
        if f"sha256:{source_version['digest']}" != plan["source_digest"]:
            self._refuse(run_id, worker, "SOURCE_CHANGED")
            raise SourceChanged(plan["source_id"])

        digest, blob = self.store.store_blob(output)
        version_id = new_id("version")
        recording_id = new_id("recording")
        payload_digest = f"sha256:{digest}"
        produced_at = now()
        self.db.execute(
            "INSERT INTO versions VALUES(?,?,?,?,?,?,?,?,?,?)",
            (
                version_id,
                run["asset_id"],
                None,
                digest,
                mime,
                len(output),
                str(blob),
                "DERIVATIVE",
                json.dumps({"recording_id": recording_id}),
                produced_at,
            ),
        )
        self.db.execute(
            "INSERT INTO recordings VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                recording_id,
                run_id,
                version_id,
                plan["source_id"],
                plan["source_digest"],
                plan["reader_id"],
                plan["reader_version"],
                plan["configuration_digest"],
                plan["output_role"],
                f"cas:sha256:{digest}",
                payload_digest,
                plan["fidelity"],
                plan["omissions_json"],
                produced_at,
                worker,
                "RECORDED",
            ),
        )
        self.db.execute(
            "UPDATE runs SET status='REPORTED',output_version_id=?,report_json=? WHERE id=?",
            (
                version_id,
                json.dumps({"digest": payload_digest, "recording_id": recording_id}),
                run_id,
            ),
        )
        self.control.receipt(
            "ATTEMPTED",
            "operation.report",
            "run",
            run_id,
            worker,
            {
                "output_version_id": version_id,
                "recording_id": recording_id,
                "digest": payload_digest,
            },
        )
        self.db.commit()
        return version_id

    def _refuse(self, run_id: str, actor: str, reason: str) -> None:
        self.db.execute("UPDATE runs SET status='REFUSED' WHERE id=?", (run_id,))
        self.control.receipt(
            "REFUSED", "operation.report", "run", run_id, actor, {"reason": reason}
        )
        self.db.commit()

    def reconstruct(self, recording_or_version_id: str) -> dict[str, Any]:
        """Reconstruct one recording and independently verify both payloads."""
        recording = self.db.execute(
            "SELECT * FROM recordings WHERE id=? OR output_version_id=?",
            (recording_or_version_id, recording_or_version_id),
        ).fetchone()
        if recording is None:
            raise KeyError(recording_or_version_id)
        run = self.db.execute(
            "SELECT kind FROM runs WHERE id=?", (recording["run_id"],)
        ).fetchone()
        if run is None:
            raise KeyError(recording["run_id"])
        try:
            source, _ = self.store.verified_version(recording["source_id"])
        except PayloadIntegrityError as error:
            raise SourceChanged(recording["source_id"]) from error
        if f"sha256:{source['digest']}" != recording["source_digest"]:
            raise SourceChanged(recording["source_id"])
        try:
            output, _ = self.store.verified_version(recording["output_version_id"])
        except PayloadIntegrityError as error:
            raise RecordingChanged(recording["output_version_id"]) from error
        if f"sha256:{output['digest']}" != recording["payload_digest"]:
            raise RecordingChanged(recording["output_version_id"])
        return {
            "recording_id": recording["id"],
            "run_id": recording["run_id"],
            "operation": run["kind"],
            "output_version_id": recording["output_version_id"],
            "source_id": recording["source_id"],
            "source_digest": recording["source_digest"],
            "reader_id": recording["reader_id"],
            "reader_version": recording["reader_version"],
            "configuration_digest": recording["configuration_digest"],
            "output_role": recording["output_role"],
            "payload_address": recording["payload_address"],
            "payload_digest": recording["payload_digest"],
            "fidelity": recording["fidelity"],
            "omissions": json.loads(recording["omissions_json"]),
            "produced_at": recording["produced_at"],
            "produced_by": recording["produced_by"],
            "standing": recording["standing"],
        }
