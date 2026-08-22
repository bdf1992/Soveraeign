from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sys
import time
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from soveraeign_asset_service import AssetService, AuthorityRefused, StaleLease


class WalkingSkeleton(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.service = AssetService(self.root / "state")
        self.service.grant("Bdo", "Bdo", "operate:derive")
        self.service.grant("Bdo", "Bdo", "ratify:judgement")
        self.service.grant("Bdo", "Bdo", "retract:record")

    def tearDown(self):
        self.service.close()
        self.tmp.cleanup()

    def source(self, name: str, content: bytes) -> Path:
        path = self.root / name
        path.write_bytes(content)
        return path

    def test_agentic_asset_walk(self):
        original = self.source("campaign-hero.txt", b"ORIGINAL CAMPAIGN ASSET\n")
        campaign = self.source("campaign.txt", b"Autumn launch\n")
        before = original.read_bytes()
        asset = self.service.ingest(original, "Campaign Hero", "Bdo")
        campaign_asset = self.service.ingest(campaign, "Autumn Campaign", "Bdo")

        run = self.service.request_derivative(asset["asset_id"], asset["version_id"], "Bdo")
        fence = self.service.claim(run, "local-worker")
        card = json.dumps({"title": "Campaign Hero", "source": asset["digest"]}).encode()
        output_version = self.service.report_derivative(run, "local-worker", fence, card)
        self.assertEqual(self.service.db.execute("SELECT status FROM runs WHERE id=?", (run,)).fetchone()[0], "REPORTED")
        self.service.observe(run, "independent-observer")
        self.assertEqual(self.service.db.execute("SELECT status FROM runs WHERE id=?", (run,)).fetchone()[0], "COMMITTED")
        self.assertEqual(original.read_bytes(), before)

        proposal = self.service.propose(asset["asset_id"], "claude-adapter", {
            "description": "Primary visual for the autumn launch",
            "tags": ["autumn", "hero"],
            "relationship": {"predicate": "USED_BY", "dst_asset": campaign_asset["asset_id"]},
        })
        with self.assertRaises(AuthorityRefused):
            self.service.ratify(proposal, "claude-adapter")
        self.service.ratify(proposal, "Bdo")
        counts = self.service.rebuild_projections()
        self.assertEqual(counts, {"search": 2, "edges": 1})
        self.assertIn(asset["asset_id"], self.service.search("autumn"))
        edges = self.service.neighbors(asset["asset_id"])
        self.assertEqual(edges[0]["predicate"], "USED_BY")
        self.assertTrue(edges[0]["source_receipt"].startswith("rcpt_"))

        relation_id = self.service.db.execute("SELECT id FROM relationships").fetchone()[0]
        self.service.retract("relationship", relation_id, "Bdo", "wrong campaign use")
        self.service.rebuild_projections()
        self.assertEqual(self.service.neighbors(asset["asset_id"]), [])
        self.assertIsNotNone(self.service.db.execute(
            "SELECT id FROM relationships WHERE id=? AND standing='COUNTERED'", (relation_id,)).fetchone())
        self.assertIsNotNone(self.service.db.execute("SELECT id FROM versions WHERE id=?", (output_version,)).fetchone())

        receipt = self.service.federation_cross("Bdo", asset["asset_id"])
        outcome = self.service.db.execute("SELECT outcome,payload_json FROM receipts WHERE id=?", (receipt,)).fetchone()
        self.assertEqual(outcome["outcome"], "REFUSED")
        self.assertEqual(json.loads(outcome["payload_json"])["reason"], "UNCONFIGURED")

    def test_stale_worker_cannot_settle(self):
        path = self.source("asset.txt", b"asset")
        asset = self.service.ingest(path, "Asset", "Bdo")
        run = self.service.request_derivative(asset["asset_id"], asset["version_id"], "Bdo")
        stale = self.service.claim(run, "worker-a", ttl_seconds=0.001)
        time.sleep(0.01)
        current = self.service.claim(run, "worker-b")
        with self.assertRaises(StaleLease):
            self.service.report_derivative(run, "worker-a", stale, b"stale")
        self.service.report_derivative(run, "worker-b", current, b"current")

    def test_same_bytes_do_not_collapse_asset_identity(self):
        path = self.source("same.bin", b"same")
        first = self.service.ingest(path, "First use", "Bdo")
        second = self.service.ingest(path, "Second use", "Bdo")
        self.assertEqual(first["digest"], second["digest"])
        self.assertNotEqual(first["asset_id"], second["asset_id"])
        self.assertEqual(len(list((self.root / "state" / "blobs" / "sha256").glob("*/*"))), 1)


if __name__ == "__main__":
    unittest.main()
