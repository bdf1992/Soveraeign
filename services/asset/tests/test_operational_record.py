from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "services" / "asset" / "src"))
sys.path.insert(0, str(ROOT / "services" / "record" / "src"))

from soveraeign_asset_service import AssetService  # noqa: E402
from soveraeign_record_service import RecordService  # noqa: E402


class FailingJournal:
    def entries(self):
        return []

    def append(self, *args, **kwargs):
        raise RuntimeError("record unavailable")


class OperationalRecordBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / "source.txt"
        self.source.write_bytes(b"operational history")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    @staticmethod
    def mirrors(record: RecordService) -> list[dict]:
        return [entry for entry in record.reconstruct()
                if entry["kind"] == "RECEIPT"
                and entry.get("source_address") == "asset-service"]

    def test_ingest_terminal_receipt_reaches_record_without_moving_domain_state(self) -> None:
        record = RecordService(self.root / "record")
        asset = AssetService(self.root / "asset", operational_record=record)
        try:
            result = asset.ingest(self.source, "Source", "operator")
            mirrors = self.mirrors(record)
            self.assertEqual(len(mirrors), 1)
            detail = mirrors[0]["payload"]["detail"]
            self.assertEqual(detail["asset_receipt_id"], result["receipt_id"])
            self.assertEqual(mirrors[0]["payload"]["event"], "asset.ingest-asset")
            self.assertEqual(mirrors[0]["payload"]["outcome"], "COMMITTED")
            self.assertEqual(asset.store.pending_operational_history(), [])
            self.assertEqual(asset.history(result["asset_id"])[0]["id"],
                             result["version_id"])
        finally:
            asset.close()
            record.close()

    def test_record_outage_leaves_a_durable_outbox_that_replays_on_restart(self) -> None:
        asset = AssetService(self.root / "asset", operational_record=FailingJournal())
        result = asset.ingest(self.source, "Source", "operator")
        self.assertEqual(asset.store.pending_operational_history(), [result["receipt_id"]])
        asset.close()

        record = RecordService(self.root / "record")
        resumed = AssetService(self.root / "asset", operational_record=record)
        try:
            self.assertEqual(resumed.store.pending_operational_history(), [])
            mirrors = self.mirrors(record)
            self.assertEqual(len(mirrors), 1)
            self.assertEqual(mirrors[0]["payload"]["detail"]["asset_receipt_id"],
                             result["receipt_id"])
        finally:
            resumed.close()
            record.close()

    def test_replaying_an_unacknowledged_outbox_does_not_duplicate_record_history(self) -> None:
        record = RecordService(self.root / "record")
        asset = AssetService(self.root / "asset", operational_record=record)
        try:
            result = asset.ingest(self.source, "Source", "operator")
            self.assertEqual(len(self.mirrors(record)), 1)
            asset.db.execute(
                "UPDATE operational_outbox SET record_entry_id=NULL,delivered_at=NULL "
                "WHERE receipt_id=?", (result["receipt_id"],))
            asset.db.commit()
            self.assertEqual(asset.store.flush_operational_history(), 1)
            self.assertEqual(len(self.mirrors(record)), 1)
            self.assertEqual(asset.store.pending_operational_history(), [])
        finally:
            asset.close()
            record.close()

    def test_other_receipted_asset_transitions_share_the_same_bridge(self) -> None:
        record = RecordService(self.root / "record")
        asset = AssetService(self.root / "asset", operational_record=record)
        try:
            session = asset.open_session("operator", "human")
            asset.grant("operator", "operator", "operate:derive", session_id=session)
            events = [entry["payload"]["event"] for entry in self.mirrors(record)]
            self.assertIn("session.open", events)
            self.assertIn("authority.grant", events)
        finally:
            asset.close()
            record.close()


if __name__ == "__main__":
    unittest.main()
