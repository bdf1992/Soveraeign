"""Disposable search and graph projections over canonical asset records."""

from __future__ import annotations

import json

from .control import ControlLedger
from .storage import AssetStore


class AssetProjections:
    """Rebuild query surfaces without acquiring authoritative state."""

    def __init__(self, store: AssetStore, control: ControlLedger):
        self.db = store.db
        self.control = control

    def rebuild(self, actor: str) -> dict[str, int]:
        self.db.execute("DELETE FROM search_projection")
        self.db.execute("DELETE FROM graph_projection")
        for asset in self.db.execute("SELECT * FROM assets"):
            ratified = self.db.execute(
                "SELECT id,payload_json FROM proposals WHERE asset_id=? AND standing='RATIFIED'",
                (asset["id"],),
            ).fetchall()
            text = [asset["label"]]
            source_receipt = ""
            for proposal in ratified:
                payload = json.loads(proposal["payload_json"])
                text.extend(
                    str(value)
                    for key, value in payload.items()
                    if key != "relationship"
                )
                receipt = self.db.execute(
                    "SELECT id FROM receipts WHERE event='proposal.ratify' AND subject_id=? "
                    "ORDER BY created_at DESC LIMIT 1",
                    (proposal["id"],),
                ).fetchone()
                source_receipt = receipt["id"] if receipt else source_receipt
            self.db.execute(
                "INSERT INTO search_projection VALUES(?,?,?)",
                (asset["id"], " ".join(text), source_receipt or "UNRATIFIED_LABEL"),
            )
        for relation in self.db.execute(
            "SELECT * FROM relationships WHERE standing='EFFECTIVE'"
        ):
            receipt = self.db.execute(
                "SELECT id FROM receipts WHERE event='proposal.ratify' AND subject_id=? "
                "ORDER BY created_at DESC LIMIT 1",
                (relation["proposal_id"],),
            ).fetchone()
            self.db.execute(
                "INSERT INTO graph_projection VALUES(?,?,?,?,?)",
                (
                    relation["id"],
                    relation["src_asset"],
                    relation["predicate"],
                    relation["dst_asset"],
                    receipt["id"],
                ),
            )
        counts = {
            "search": self.db.execute("SELECT COUNT(*) FROM search_projection").fetchone()[0],
            "edges": self.db.execute("SELECT COUNT(*) FROM graph_projection").fetchone()[0],
        }
        self.control.receipt(
            "COMMITTED", "projection.rebuild", "projection", "all", actor, counts
        )
        self.db.commit()
        return counts

    def search(self, query: str) -> list[str]:
        return [
            row["asset_id"]
            for row in self.db.execute(
                "SELECT asset_id FROM search_projection WHERE lower(text_value) LIKE ? "
                "ORDER BY asset_id",
                (f"%{query.lower()}%",),
            )
        ]

    def neighbors(self, asset_id: str) -> list[dict[str, str]]:
        return [
            dict(row)
            for row in self.db.execute(
                "SELECT src_asset,predicate,dst_asset,source_receipt FROM graph_projection "
                "WHERE src_asset=? OR dst_asset=? ORDER BY predicate,dst_asset",
                (asset_id, asset_id),
            )
        ]
