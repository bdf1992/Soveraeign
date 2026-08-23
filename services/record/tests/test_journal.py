from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from soveraeign_record_service import (  # noqa: E402
    BrokenChain,
    DesignRecordRefused,
    ProjectionNotAuthoritative,
    RecordService,
)


class OperationalSystemOfRecord(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self.tmp.name) / "state"
        self.service = RecordService(self.root)

    def tearDown(self):
        self.service.close()
        self.tmp.cleanup()

    def reopen(self) -> RecordService:
        """Close and reopen, the way a process restart would."""
        self.service.close()
        self.service = RecordService(self.root)
        return self.service

    def test_witness_walk(self):
        """The witness procedure declared on issue #7, performed end to end.

        Commit, interrupt, restart, reconstruct, retract, drop every projection,
        rebuild them, and compare the resulting record addresses and receipts.
        """
        first = self.service.append("EVENT", "run-1", "Bdo", {"step": "begin"})
        receipt = self.service.receipt("COMMITTED", "operation.begin", "run-1", "Bdo")

        # interrupt: a transaction that never commits leaves nothing behind
        raw = sqlite3.connect(self.root / "record-service.sqlite3")
        raw.execute(
            "INSERT INTO journal(entry_id,kind,subject,actor,source_address,"
            "payload_json,recorded_at,prev_digest,entry_digest) "
            "VALUES('entry_interrupted','EVENT','run-1','Bdo',NULL,'{}',0,'x','y')"
        )
        raw.close()

        before = self.reopen().reconstruct()
        addresses_before = [entry["entry_digest"] for entry in before]
        self.assertEqual(len(before), 2)
        self.assertNotIn("entry_interrupted", [entry["entry_id"] for entry in before])

        self.service.counter(first["entry_id"], "Bdo", "superseded by a later reading")
        self.service.rebuild_projections()
        projected = self.service.projection("run-1")

        self.service.drop_projections()
        self.service.rebuild_projections()
        rebuilt = self.service.projection("run-1")

        self.assertEqual(projected, rebuilt)
        after = self.service.reconstruct()
        self.assertEqual([e["entry_digest"] for e in after][:2], addresses_before)
        self.assertEqual(self.service.entry(receipt["entry_id"])["payload"]["outcome"],
                         "COMMITTED")
        self.assertTrue(self.service.countered(first["entry_id"]))

    def test_committed_records_survive_restart(self):
        entry = self.service.append("EVENT", "asset-1", "Bdo", {"step": "ingest"})
        head = self.service.head()
        self.reopen()
        self.assertEqual(self.service.head(), head)
        self.assertEqual(self.service.entry(entry["entry_id"])["payload"], {"step": "ingest"})
        self.assertEqual(len(self.service.reconstruct()), 1)

    def test_partial_write_never_becomes_effective(self):
        self.service.append("EVENT", "asset-1", "Bdo", {"step": "one"})
        head = self.service.head()
        raw = sqlite3.connect(self.root / "record-service.sqlite3")
        raw.execute(
            "INSERT INTO journal(entry_id,kind,subject,actor,source_address,"
            "payload_json,recorded_at,prev_digest,entry_digest) "
            "VALUES('entry_partial','EVENT','asset-1','Bdo',NULL,'{}',0,'x','y')"
        )
        raw.close()  # never committed
        self.reopen()
        self.assertEqual(self.service.head(), head)
        self.service.reconstruct()

    def test_retraction_preserves_the_original(self):
        original = self.service.append("EVENT", "claim-1", "Bdo", {"claim": "effective"})
        counter = self.service.counter(original["entry_id"], "Bdo", "withdrawn")
        preserved = self.service.entry(original["entry_id"])
        self.assertEqual(preserved["payload"], {"claim": "effective"})
        self.assertTrue(self.service.countered(original["entry_id"]))
        self.assertEqual(counter["payload"]["counters"], original["entry_id"])
        self.assertEqual(len(self.service.entries()), 2)

    def test_projections_rebuild_identically(self):
        for step in ("one", "two", "three"):
            self.service.append("EVENT", "run-2", "Bdo", {"step": step})
        self.service.rebuild_projections()
        before = self.service.projection("run-2")
        self.service.drop_projections()
        with self.assertRaises(KeyError):
            self.service.projection("run-2")
        self.service.rebuild_projections()
        self.assertEqual(self.service.projection("run-2"), before)

    def test_a_projection_cannot_become_authoritative(self):
        self.service.append("EVENT", "run-3", "Bdo", {"step": "one"})
        self.service.rebuild_projections()
        with self.assertRaises(ProjectionNotAuthoritative):
            self.service.append_from_projection("run-3")

    def test_design_documents_are_refused_as_event_storage(self):
        with self.assertRaises(DesignRecordRefused):
            self.service.append("EVENT", "spec", "Bdo", {"note": "x"},
                                source_address="SPEC.md")
        with self.assertRaises(DesignRecordRefused):
            self.service.append("EVENT", "status", "Bdo", {"note": "x"},
                                source_address="/repo/STATUS.yaml")
        self.assertEqual(self.service.entries(), [])

    def test_rewritten_history_stops_verifying(self):
        self.service.append("EVENT", "run-4", "Bdo", {"step": "one"})
        self.service.append("EVENT", "run-4", "Bdo", {"step": "two"})
        self.service.close()
        raw = sqlite3.connect(self.root / "record-service.sqlite3")
        raw.execute("UPDATE journal SET payload_json='{\"step\":\"rewritten\"}' WHERE seq=1")
        raw.commit()
        raw.close()
        self.service = RecordService(self.root)
        with self.assertRaises(BrokenChain):
            self.service.reconstruct()


if __name__ == "__main__":
    unittest.main()
