"""Positive and defeating cases for journal export and restore (decisions/0049).

Every store here writes with `synchronous=FULL`, which is the point of the
service and costs real milliseconds. So the cases that only read an exported
document build one store for the whole class, and only the cases that actually
restore pay for a store each. The repository verification budget is three
seconds for everything; a durability feature should not spend it.

Passing establishes `BUILT` for the durability row. It witnesses nothing.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import copy
import json
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from soveraeign_record_service.core import BrokenChain, RecordService  # noqa: E402
from soveraeign_record_service.custody import (  # noqa: E402
    ExportRefused, RestoreRefused, TruncatedExport, export_document, restore,
    restore_file, verify_export, write_export,
)


def populate(service: RecordService) -> None:
    for index in range(4):
        service.append("EVENT", f"subject-{index % 2}", "principal:bdo", {"step": index})
    service.receipt("COMMITTED", "walk", "subject-0", "principal:bdo")


class ExportDocument(unittest.TestCase):
    """Cases that only read an exported document. One store for the whole class."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = TemporaryDirectory()
        cls.service = RecordService(Path(cls.tmp.name) / "live")
        populate(cls.service)
        cls.head = cls.service.head()
        cls.document = export_document(cls.service)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.service.close()
        cls.tmp.cleanup()

    def altered(self) -> dict:
        """A private copy, so one case cannot corrupt the next."""
        return copy.deepcopy(self.document)

    # -- positive ------------------------------------------------------------

    def test_export_declares_the_head_it_reaches(self) -> None:
        self.assertEqual(self.document["head_digest"], self.head)
        self.assertEqual(self.document["entry_count"], len(self.document["entries"]))

    def test_export_verifies_standalone_without_a_database(self) -> None:
        travelled = json.loads(json.dumps(self.document))
        self.assertEqual(verify_export(travelled), self.head)

    # -- defeating -----------------------------------------------------------

    def test_edited_payload_is_caught(self) -> None:
        document = self.altered()
        document["entries"][1]["payload"] = {"step": 99}
        with self.assertRaises(BrokenChain):
            verify_export(document)

    def test_edited_actor_is_caught(self) -> None:
        document = self.altered()
        document["entries"][2]["actor"] = "principal:someone-else"
        with self.assertRaises(BrokenChain):
            verify_export(document)

    def test_reordered_entries_are_caught(self) -> None:
        document = self.altered()
        document["entries"][1], document["entries"][2] = (
            document["entries"][2], document["entries"][1])
        with self.assertRaises(BrokenChain):
            verify_export(document)

    def test_entry_removed_from_the_middle_is_caught(self) -> None:
        document = self.altered()
        del document["entries"][2]
        with self.assertRaises(BrokenChain):
            verify_export(document)

    def test_truncation_verifies_alone_and_needs_an_outside_head(self) -> None:
        """The load-bearing case: a shortened journal is a valid journal.

        Dropping the tail and rewriting the header leaves a document whose every
        link holds. Nothing inside it knows how long it was meant to be, so only
        a head digest held outside the export detects the loss.
        """
        document = self.altered()
        del document["entries"][-2:]
        document["entry_count"] = len(document["entries"])
        document["head_digest"] = document["entries"][-1]["entry_digest"]

        self.assertNotEqual(verify_export(document), self.head)
        with self.assertRaises(TruncatedExport):
            verify_export(document, expected_head=self.head)

    def test_declared_head_must_match_the_replayed_head(self) -> None:
        document = self.altered()
        document["head_digest"] = "0" * 64
        with self.assertRaises(BrokenChain):
            verify_export(document)

    def test_declared_count_must_match_the_entries_carried(self) -> None:
        document = self.altered()
        document["entry_count"] = 99
        with self.assertRaises(RestoreRefused):
            verify_export(document)

    def test_an_entry_missing_fields_is_refused(self) -> None:
        document = self.altered()
        del document["entries"][0]["actor"]
        with self.assertRaises(RestoreRefused):
            verify_export(document)

    def test_a_foreign_document_is_refused(self) -> None:
        for document in ({"export_schema": "something-else"}, {"entries": []}, [], "text"):
            with self.assertRaises(RestoreRefused):
                verify_export(document)


class RestoreRoundTrip(unittest.TestCase):
    """Cases that write a store. Each pays for its own."""

    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.service = RecordService(self.root / "live")
        self.opened = [self.service]

    def tearDown(self) -> None:
        # Every store closes before the directory goes: Windows refuses to
        # remove a file an open SQLite connection still holds.
        for service in self.opened:
            service.close()
        self.tmp.cleanup()

    def fresh(self, name: str = "restored") -> RecordService:
        service = RecordService(self.root / name)
        self.opened.append(service)
        return service

    # -- positive ------------------------------------------------------------

    def test_export_then_restore_reaches_the_same_head(self) -> None:
        populate(self.service)
        head = self.service.head()
        document = export_document(self.service)
        target = self.fresh()
        self.assertEqual(restore(target, document), document["entry_count"])
        self.assertEqual(target.head(), head)
        self.assertEqual(target.entries(), self.service.entries())

    def test_round_trip_through_a_file_rebuilds_projections(self) -> None:
        populate(self.service)
        self.service.rebuild_projections()
        path = self.root / "backup" / "journal.json"
        document = write_export(self.service, path)
        self.assertTrue(path.is_file())
        target = self.fresh()
        restore_file(target, path, expected_head=document["head_digest"])
        self.assertEqual(target.head(), self.service.head())
        self.assertEqual(target.projection("subject-0"),
                         self.service.projection("subject-0"),
                         "a restore rebuilds projections from the journal it replayed")

    def test_empty_journal_round_trips(self) -> None:
        document = export_document(self.service)
        self.assertEqual(document["entry_count"], 0)
        self.assertEqual(restore(self.fresh(), document), 0)

    # -- defeating -----------------------------------------------------------

    def test_restore_into_a_live_journal_is_refused(self) -> None:
        populate(self.service)
        document = export_document(self.service)
        target = self.fresh()
        target.append("EVENT", "its-own", "principal:bdo", {"already": True})
        with self.assertRaises(RestoreRefused):
            restore(target, document)

    def test_truncated_export_is_refused_against_an_outside_head(self) -> None:
        populate(self.service)
        head = self.service.head()
        document = export_document(self.service)
        del document["entries"][-2:]
        document["entry_count"] = len(document["entries"])
        document["head_digest"] = document["entries"][-1]["entry_digest"]
        with self.assertRaises(TruncatedExport):
            restore(self.fresh(), document, expected_head=head)

    def test_a_broken_journal_is_never_exported(self) -> None:
        populate(self.service)
        self.service.db.execute(
            "UPDATE journal SET payload_json=? WHERE seq=2", ('{"tampered":true}',))
        self.service.db.commit()
        with self.assertRaises(ExportRefused):
            export_document(self.service)

    def test_unreadable_export_file_is_refused(self) -> None:
        with self.assertRaises(RestoreRefused):
            restore_file(self.fresh(), self.root / "nothing-here.json")


if __name__ == "__main__":
    unittest.main()
