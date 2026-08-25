"""Rebuildable derived views over the asset ledger.

`CLASSIFICATION.md` defines a Projection as a derived view that never becomes
authoritative by convenience. Both tables here are dropped and rebuilt from
ratified records on every rebuild, so a row written straight into one survives
only until the next rebuild and carries no receipt behind it.
"""

from __future__ import annotations

from typing import Any
import json
import sqlite3

from soveraeign_asset_service.store import Store


SCHEMA = """
CREATE TABLE IF NOT EXISTS search_projection(
  asset_id TEXT PRIMARY KEY, text_value TEXT NOT NULL, source_receipt TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS graph_projection(
  relationship_id TEXT PRIMARY KEY, src_asset TEXT NOT NULL,
  predicate TEXT NOT NULL, dst_asset TEXT NOT NULL,
  source_receipt TEXT NOT NULL);
"""

UNRATIFIED = "UNRATIFIED_LABEL"


class Projections:
    """The search and graph views, and the rebuild that is their only writer."""

    def __init__(self, store: Store) -> None:
        self.store = store
        self.db = store.db

    def _ratify_receipt(self, proposal_id: str) -> str | None:
        """The newest ratification receipt for a proposal, which sources its projected row."""
        row = self.db.execute(
            "SELECT id FROM receipts WHERE event='asset.ratify-proposal' AND subject_id=? "
            "ORDER BY created_at DESC LIMIT 1", (proposal_id,)).fetchone()
        return row["id"] if row else None

    def rebuild(self, actor: str = "projector") -> dict[str, int]:
        """Drop both views and derive them again from ratified records only."""
        self.db.execute("DELETE FROM search_projection")
        self.db.execute("DELETE FROM graph_projection")
        for asset in self.db.execute("SELECT * FROM assets").fetchall():
            self._project_asset(asset)
        for relation in self.db.execute(
                "SELECT * FROM relationships WHERE standing='EFFECTIVE'").fetchall():
            self.db.execute(
                "INSERT INTO graph_projection VALUES(?,?,?,?,?)",
                (relation["id"], relation["src_asset"], relation["predicate"],
                 relation["dst_asset"], self._ratify_receipt(relation["proposal_id"])))
        counts = {
            "search": self.db.execute("SELECT COUNT(*) FROM search_projection").fetchone()[0],
            "edges": self.db.execute("SELECT COUNT(*) FROM graph_projection").fetchone()[0],
        }
        self.store.receipt("COMMITTED", "asset.rebuild-projection", "projection", "all", actor, counts)
        self.db.commit()
        return counts

    def _project_asset(self, asset: sqlite3.Row) -> None:
        """One search row: the label plus every ratified description, and its source receipt."""
        text = [asset["label"]]
        source_receipt = ""
        ratified = self.db.execute(
            "SELECT id,payload_json FROM proposals WHERE asset_id=? AND standing='RATIFIED'",
            (asset["id"],)).fetchall()
        for proposal in ratified:
            payload = json.loads(proposal["payload_json"])
            text.extend(str(value) for key, value in payload.items() if key != "relationship")
            source_receipt = self._ratify_receipt(proposal["id"]) or source_receipt
        self.db.execute("INSERT INTO search_projection VALUES(?,?,?)",
                        (asset["id"], " ".join(text), source_receipt or UNRATIFIED))

    def search(self, query: str) -> list[str]:
        """Assets whose projected text contains the query, case-insensitively."""
        return [row["asset_id"] for row in self.db.execute(
            "SELECT asset_id FROM search_projection WHERE lower(text_value) LIKE ? "
            "ORDER BY asset_id", (f"%{query.lower()}%",))]

    def neighbors(self, asset_id: str) -> list[dict[str, Any]]:
        """Projected edges touching an asset, in a stable order."""
        return [dict(row) for row in self.db.execute(
            "SELECT src_asset,predicate,dst_asset,source_receipt FROM graph_projection "
            "WHERE src_asset=? OR dst_asset=? ORDER BY predicate,dst_asset",
            (asset_id, asset_id))]
