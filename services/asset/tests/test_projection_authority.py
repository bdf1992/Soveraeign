"""Positive and defeating cases for the contract predicate `direct-projection-authority`.

`services/asset/contracts/service.json` forbids `direct-projection-authority`;
CLASSIFICATION.md defines a Projection as a rebuildable derived view that never
becomes authoritative by convenience. These cases establish BUILT evidence only:
a row written straight into a projection table, bypassing every kernel
transition, is visible until the next rebuild and then disappears because it has
no canonical record or receipt behind it.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from soveraeign_asset_service import AssetService

FORGED_RECEIPT = "rcpt_forged"
FORGED_ASSET = "asset_forged"
FORGED_TEXT = "forgedtoken"


class ProjectionAuthority(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.service = AssetService(self.root / "state")
        self.service.grant("Bdo", "Bdo", "ratify:judgement")

    def tearDown(self):
        self.service.close()
        self.tmp.cleanup()

    def source(self, name: str, content: bytes) -> Path:
        path = self.root / name
        path.write_bytes(content)
        return path

    def ratified_pair(self) -> tuple[str, str]:
        """Ingest two assets and ratify one USED_BY relationship through the kernel."""
        hero = self.service.ingest(self.source("hero.txt", b"hero"), "Campaign Hero", "Bdo")
        campaign = self.service.ingest(
            self.source("campaign.txt", b"campaign"), "Autumn Campaign", "Bdo")
        proposal = self.service.propose(hero["asset_id"], "claude-adapter", {
            "description": "Primary visual for the autumn launch",
            "relationship": {"predicate": "USED_BY", "dst_asset": campaign["asset_id"]},
        })
        self.service.ratify(proposal, "Bdo")
        return hero["asset_id"], campaign["asset_id"]

    def receipt_event(self, receipt_id: str) -> str | None:
        row = self.service.db.execute(
            "SELECT event FROM receipts WHERE id=?", (receipt_id,)).fetchone()
        return None if row is None else row["event"]

    def test_rebuild_derives_projection_from_ratified_records(self):
        hero, campaign = self.ratified_pair()

        counts = self.service.rebuild_projections()

        self.assertEqual(counts, {"search": 2, "edges": 1})
        edges = self.service.neighbors(hero)
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]["src_asset"], hero)
        self.assertEqual(edges[0]["predicate"], "USED_BY")
        self.assertEqual(edges[0]["dst_asset"], campaign)
        self.assertEqual(self.receipt_event(edges[0]["source_receipt"]), "asset.ratify-proposal")
        rebuilds = [r for r in self.service.receipts() if r["event"] == "asset.rebuild-projection"]
        self.assertEqual([r["outcome"] for r in rebuilds], ["COMMITTED"])

    def test_direct_projection_write_does_not_survive_rebuild(self):
        hero, campaign = self.ratified_pair()

        # Forge rows straight into the projection tables, bypassing every kernel
        # transition. Column order follows AssetService._schema exactly.
        self.service.db.execute(
            "INSERT INTO graph_projection VALUES(?,?,?,?,?)",
            ("rel_forged", campaign, "OWNS", hero, FORGED_RECEIPT))
        self.service.db.execute(
            "INSERT INTO search_projection VALUES(?,?,?)",
            (FORGED_ASSET, FORGED_TEXT, FORGED_RECEIPT))
        self.service.db.commit()

        # Visible before rebuild: the tables are derived views, not guarded authority.
        forged_edges = [e for e in self.service.neighbors(hero) if e["predicate"] == "OWNS"]
        self.assertEqual(len(forged_edges), 1)
        self.assertEqual(forged_edges[0]["source_receipt"], FORGED_RECEIPT)
        self.assertEqual(self.service.search(FORGED_TEXT), [FORGED_ASSET])
        self.assertIsNone(self.receipt_event(FORGED_RECEIPT))

        counts = self.service.rebuild_projections()

        # Gone after rebuild: only canonical records survive the derivation.
        self.assertEqual(counts, {"search": 2, "edges": 1})
        edges = self.service.neighbors(hero)
        self.assertEqual([e["predicate"] for e in edges], ["USED_BY"])
        self.assertNotEqual(edges[0]["source_receipt"], FORGED_RECEIPT)
        self.assertEqual(self.receipt_event(edges[0]["source_receipt"]), "asset.ratify-proposal")
        self.assertEqual(self.service.search(FORGED_TEXT), [])
        self.assertNotIn(FORGED_ASSET, self.service.search("campaign"))
        self.assertEqual(self.service.db.execute(
            "SELECT COUNT(*) FROM graph_projection WHERE source_receipt=?",
            (FORGED_RECEIPT,)).fetchone()[0], 0)
        self.assertEqual(self.service.db.execute(
            "SELECT COUNT(*) FROM search_projection WHERE source_receipt=?",
            (FORGED_RECEIPT,)).fetchone()[0], 0)
        self.assertNotIn(FORGED_RECEIPT, [r["id"] for r in self.service.receipts()])


if __name__ == "__main__":
    unittest.main()
