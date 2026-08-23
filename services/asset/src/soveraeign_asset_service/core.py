"""Dependency-free Asset Service lifecycle over replaceable local mechanisms."""

from __future__ import annotations

import json
import mimetypes
from pathlib import Path
from typing import Any

from .control import ControlLedger
from .derivatives import DerivativeLifecycle
from .observations import RunObservations
from .projections import AssetProjections
from .recording import ReaderDeclaration, ReaderMaterials
from .storage import AssetStore, new_id, now


class AssetService:
    """Reference participant preserving the existing public lifecycle surface."""

    def __init__(self, root: str | Path):
        self._store = AssetStore(root)
        self.db = self._store.db
        self._control = ControlLedger(self.db)
        self._readers = ReaderMaterials(self._store)
        self._derivatives = DerivativeLifecycle(
            self._store, self._control, self._readers
        )
        self._observations = RunObservations(
            self._store, self._control, self._derivatives
        )
        self._projections = AssetProjections(self._store, self._control)

    def close(self) -> None:
        self._store.close()

    def grant(self, issuer: str, actor: str, capability: str, scope: str = "*") -> str:
        return self._control.grant(issuer, actor, capability, scope)

    def ingest(
        self,
        path: str | Path,
        label: str,
        actor: str,
        locator: str | None = None,
    ) -> dict[str, str]:
        """Capture one immutable source and its first asset version."""
        source_path = Path(path)
        data = source_path.read_bytes()
        digest, blob = self._store.store_blob(data)
        source_id = new_id("source")
        asset_id = new_id("asset")
        version_id = new_id("version")
        self.db.execute(
            "INSERT INTO sources VALUES(?,?,?,?)",
            (source_id, locator or source_path.resolve().as_uri(), digest, now()),
        )
        self.db.execute("INSERT INTO assets VALUES(?,?,?)", (asset_id, label, now()))
        mime = mimetypes.guess_type(source_path.name)[0] or "application/octet-stream"
        self.db.execute(
            "INSERT INTO versions VALUES(?,?,?,?,?,?,?,?,?,?)",
            (
                version_id,
                asset_id,
                source_id,
                digest,
                mime,
                len(data),
                str(blob),
                "ORIGINAL",
                None,
                now(),
            ),
        )
        receipt_id = self._control.receipt(
            "COMMITTED",
            "asset.ingest",
            "asset",
            asset_id,
            actor,
            {"source_id": source_id, "version_id": version_id, "digest": digest},
        )
        self.db.commit()
        return {
            "asset_id": asset_id,
            "source_id": source_id,
            "version_id": version_id,
            "digest": digest,
            "receipt_id": receipt_id,
        }

    def propose(
        self,
        asset_id: str,
        actor: str,
        payload: dict[str, Any],
        required_authority: str = "ratify:judgement",
    ) -> str:
        proposal_id = new_id("proposal")
        self.db.execute(
            "INSERT INTO proposals VALUES(?,?,?,?,?,?,?)",
            (
                proposal_id,
                asset_id,
                actor,
                json.dumps(payload, sort_keys=True),
                "RECORDED",
                required_authority,
                now(),
            ),
        )
        self._control.receipt(
            "COMMITTED",
            "proposal.record",
            "proposal",
            proposal_id,
            actor,
            {"asset_id": asset_id, "standing": "RECORDED"},
        )
        self.db.commit()
        return proposal_id

    def ratify(self, proposal_id: str, actor: str) -> str:
        proposal = self.db.execute(
            "SELECT * FROM proposals WHERE id=?", (proposal_id,)
        ).fetchone()
        if proposal is None:
            raise KeyError(proposal_id)
        self._control.require(
            actor,
            proposal["required_authority"],
            proposal["asset_id"],
            "proposal",
            proposal_id,
        )
        payload = json.loads(proposal["payload_json"])
        self.db.execute("UPDATE proposals SET standing='RATIFIED' WHERE id=?", (proposal_id,))
        relation = payload.get("relationship")
        if relation:
            relationship_id = new_id("rel")
            self.db.execute(
                "INSERT INTO relationships VALUES(?,?,?,?,?,?,?)",
                (
                    relationship_id,
                    proposal["asset_id"],
                    relation["predicate"],
                    relation["dst_asset"],
                    proposal_id,
                    "EFFECTIVE",
                    now(),
                ),
            )
        receipt_id = self._control.receipt(
            "COMMITTED",
            "proposal.ratify",
            "proposal",
            proposal_id,
            actor,
            {"asset_id": proposal["asset_id"]},
        )
        self.db.commit()
        return receipt_id

    def request_derivative(
        self,
        asset_id: str,
        version_id: str,
        actor: str,
        *,
        reader: ReaderDeclaration | None = None,
        kind: str = "metadata-card",
    ) -> str:
        return self._derivatives.request(asset_id, version_id, actor, reader, kind)

    def claim(self, run_id: str, worker: str, ttl_seconds: float = 60) -> int:
        return self._derivatives.claim(run_id, worker, ttl_seconds)

    def report_derivative(
        self,
        run_id: str,
        worker: str,
        fence: int,
        output: bytes,
        mime: str = "application/json",
    ) -> str:
        return self._derivatives.report(run_id, worker, fence, output, mime)

    def reconstruct_recording(self, recording_or_version_id: str) -> dict[str, Any]:
        return self._derivatives.reconstruct(recording_or_version_id)

    def observe(self, run_id: str, observer: str) -> str:
        return self._observations.observe(run_id, observer)

    def retract(self, target_type: str, target_id: str, actor: str, reason: str) -> str:
        scope = target_id
        if target_type == "relationship":
            row = self.db.execute(
                "SELECT src_asset FROM relationships WHERE id=?", (target_id,)
            ).fetchone()
            if row is None:
                raise KeyError(target_id)
            scope = row["src_asset"]
        self._control.require(actor, "retract:record", scope, target_type, target_id)
        retraction_id = new_id("retract")
        self.db.execute(
            "INSERT INTO retractions VALUES(?,?,?,?,?,?)",
            (retraction_id, target_type, target_id, actor, reason, now()),
        )
        if target_type == "relationship":
            self.db.execute(
                "UPDATE relationships SET standing='COUNTERED' WHERE id=?", (target_id,)
            )
        receipt_id = self._control.receipt(
            "COUNTERED",
            "record.retract",
            target_type,
            target_id,
            actor,
            {"retraction_id": retraction_id, "reason": reason},
        )
        self.db.commit()
        return receipt_id

    def rebuild_projections(self, actor: str = "projector") -> dict[str, int]:
        return self._projections.rebuild(actor)

    def search(self, query: str) -> list[str]:
        return self._projections.search(query)

    def neighbors(self, asset_id: str) -> list[dict[str, str]]:
        return self._projections.neighbors(asset_id)

    def federation_cross(self, actor: str, asset_id: str) -> str:
        receipt_id = self._control.receipt(
            "REFUSED",
            "federation.cross",
            "asset",
            asset_id,
            actor,
            {"reason": "UNCONFIGURED", "node_two": None},
        )
        self.db.commit()
        return receipt_id

    def receipts(self) -> list[dict[str, Any]]:
        return [
            dict(row)
            for row in self.db.execute("SELECT * FROM receipts ORDER BY created_at,id")
        ]
