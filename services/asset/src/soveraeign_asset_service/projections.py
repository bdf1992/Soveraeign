"""Rebuildable derived views over the asset ledger, and the drift check over them.

`CLASSIFICATION.md` defines a Projection as a derived view that never becomes
authoritative by convenience. Both tables here are dropped and rebuilt from
ratified records on every rebuild, so a row written straight into one survives
only until the next rebuild and carries no receipt behind it.

That property was proven and still is. What was missing beside it was any way to
*ask* whether a projection currently matches the ledger. The only answer available
was to rebuild, which destroys the evidence in the act of collecting it, so
callers compared row counts instead. A count is blind to the failure that matters:
rewriting a projected row in place leaves the count identical, and the view then
returns a forged asset for a forged query while the real label finds nothing.

``derived`` is therefore split out as the single derivation both callers use.
``rebuild`` stores what it returns; ``drift`` compares against it and writes
nothing. The two cannot disagree about what the ledger implies, because there is
only one implementation of implying it.
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

#: How a projected row can disagree with the ledger. Each names what is wrong with
#: the row rather than only that something is, because the three have different
#: causes: a view that has not been rebuilt, a row nothing supports, and a row
#: whose stored values were changed after derivation.
BEHIND = "PROJECTION_BEHIND"
UNSOURCED = "PROJECTION_UNSOURCED"
ALTERED = "PROJECTION_ALTERED"


class Projections:
    """The search and graph views, the rebuild that is their only writer, and drift."""

    def __init__(self, store: Store) -> None:
        self.store = store
        self.db = store.db

    def _ratify_receipt(self, proposal_id: str) -> str | None:
        """The newest ratification receipt for a proposal, which sources its projected row."""
        row = self.db.execute(
            "SELECT id FROM receipts WHERE event='asset.ratify-proposal' AND subject_id=? "
            "ORDER BY created_at DESC LIMIT 1", (proposal_id,)).fetchone()
        return row["id"] if row else None

    def derived(self) -> tuple[dict[str, tuple], dict[str, tuple]]:
        """The exact rows a rebuild would write, keyed by primary key. Writes nothing.

        This is the whole derivation. ``rebuild`` stores the result and ``drift``
        compares against it, so neither can hold a private idea of what the ledger
        implies.
        """
        search: dict[str, tuple] = {}
        for asset in self.db.execute("SELECT * FROM assets").fetchall():
            row = self._project_asset(asset)
            search[row[0]] = row
        edges: dict[str, tuple] = {}
        for relation in self.db.execute(
                "SELECT * FROM relationships WHERE standing='EFFECTIVE'").fetchall():
            edges[relation["id"]] = (
                relation["id"], relation["src_asset"], relation["predicate"],
                relation["dst_asset"], self._ratify_receipt(relation["proposal_id"]))
        return search, edges

    def rebuild(self, actor: str = "projector") -> dict[str, int]:
        """Drop both views and derive them again from ratified records only."""
        search, edges = self.derived()
        self.db.execute("DELETE FROM search_projection")
        self.db.execute("DELETE FROM graph_projection")
        self.db.executemany("INSERT INTO search_projection VALUES(?,?,?)", search.values())
        self.db.executemany("INSERT INTO graph_projection VALUES(?,?,?,?,?)", edges.values())
        counts = {"search": len(search), "edges": len(edges)}
        self.store.receipt("COMMITTED", "asset.rebuild-projection", "projection", "all", actor, counts)
        self.db.commit()
        return counts

    def drift(self) -> list[dict[str, Any]]:
        """Every projected row that disagrees with the ledger, without rebuilding.

        Returns one entry per disagreeing row, naming the table, the key, and which
        of the three disagreements it is. An empty list means the stored views are
        exactly what a rebuild would produce right now - which is a claim a row
        count cannot make, since rewriting a row in place leaves the count intact.

        This never writes: not to the projections, and not a receipt. It is a read
        over state the caller already holds, and a check that changed what it
        checks would be answering about a different store than the one asked about.
        """
        search, edges = self.derived()
        defects: list[dict[str, Any]] = []
        defects.extend(self._compare(
            "search_projection", "asset_id", search,
            "SELECT asset_id,text_value,source_receipt FROM search_projection"))
        defects.extend(self._compare(
            "graph_projection", "relationship_id", edges,
            "SELECT relationship_id,src_asset,predicate,dst_asset,source_receipt "
            "FROM graph_projection"))
        return defects

    def _compare(self, table: str, key: str, expected: dict[str, tuple],
                 query: str) -> list[dict[str, Any]]:
        """Grade one stored table against the rows the ledger implies for it."""
        stored = {row[0]: tuple(row) for row in self.db.execute(query)}
        defects: list[dict[str, Any]] = []
        for identity in sorted(set(expected) | set(stored)):
            if identity not in stored:
                defects.append({"table": table, key: identity, "defect": BEHIND,
                                "detail": "the ledger implies this row and the view omits it"})
            elif identity not in expected:
                defects.append({"table": table, key: identity, "defect": UNSOURCED,
                                "detail": "the view carries a row no ratified record supports"})
            elif stored[identity] != expected[identity]:
                defects.append({"table": table, key: identity, "defect": ALTERED,
                                "detail": "the stored row differs from the derived one; "
                                          "a row count cannot see this"})
        return defects

    def _project_asset(self, asset: sqlite3.Row) -> tuple:
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
        return (asset["id"], " ".join(text), source_receipt or UNRATIFIED)

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
