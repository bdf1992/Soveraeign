"""A closed lease leaves a committed record; a live one leaves nothing."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sovlease import settlement  # noqa: E402

# Shaped as scripts/sovlease/store.py actually reconstructs a lease, read from a real
# closed lease rather than assumed: concern, closure and grant are nested objects and the
# definition hangs off the holder. A first version of this fixture guessed flat names and
# every one of those fields serialised as null.


def _seed_held_lease(commands, store_dir) -> None:
    """Put one HELD lease in a fixture store, shaped as the evaluator will accept it."""
    held = json.loads(json.dumps(CLOSED))
    held["state"] = "HELD"
    held.pop("closure_evidence")
    commands.store.append(store_dir, commands.store.LEASES_LOG,
                          {"event": "take", "lease_id": CLOSED["lease_id"], "lease": held})


def _close_body() -> str:
    """cmd_close's own source, so an assertion cannot match cmd_take earlier in the file."""
    source = (Path(__file__).resolve().parents[1] / "sovlease" / "commands.py").read_text(
        encoding="utf-8")
    start = source.index("def cmd_close(")
    return source[start:source.index("\ndef ", start)]


CLOSED = {
    "lease_id": "lease:concern-example/thing",
    "concern": {"kind": "concern", "reference": "concern:example/thing"},
    "state": "COMPLETED",
    "holder": {
        "principal_id": "urn:soveraeign:principal:instance:session-a",
        "parent_lease": None,
        "relation": "PARENT",
        "controller_principal": None,
        "definition": {"definition_id": "example/definition", "provenance": "USER_AUTHORED"},
    },
    "closure": {
        "condition": "the check passes on the trunk and fails at the broken revision",
        "defeating_evidence": "the check passes at the broken revision",
    },
    "grant": {"grant_id": None, "effect_ceiling": "RECORD_LOCAL"},
    "closure_evidence": {
        "receipt_id": "receipt:example/thing",
        "standing_reached": "BUILT",
        "evidence_addresses": ["a@1 path/one.py", "b@2 path/two.md"],
        "witnessed_by": None,
    },
}


class SettlementRecord(unittest.TestCase):
    def test_carries_every_field_the_closure_established(self) -> None:
        entry = settlement.record(CLOSED, now=datetime(2026, 9, 8, 15, tzinfo=timezone.utc))
        self.assertEqual("soveraeign-lease-settlement/v1", entry["record_schema"])
        self.assertEqual("receipt:example/thing", entry["receipt_id"])
        self.assertEqual("BUILT", entry["standing_reached"])
        self.assertEqual(["a@1 path/one.py", "b@2 path/two.md"], entry["evidence_addresses"])
        self.assertEqual("2026-09-08T15:00:00Z", entry["closed_at"])

    def test_no_field_the_lease_carries_serialises_as_null(self) -> None:
        """The defect a first version shipped: guessed field names read as absent terms."""
        entry = settlement.record(CLOSED)
        for field in ("concern", "concern_kind", "held_by", "definition",
                      "closure_condition", "defeating_condition", "effect_ceiling"):
            self.assertIsNotNone(entry[field], f"{field} read as null from a lease that has it")

    def test_claims_no_standing_the_closure_did_not_reach(self) -> None:
        """The record states the standing the evaluator admitted and invents none."""
        entry = settlement.record(CLOSED)
        self.assertEqual("BUILT", entry["standing_reached"])
        self.assertIsNone(entry["witnessed_by"])

    def test_writes_one_file_under_reports(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "reports").mkdir()
            path = settlement.write(CLOSED, root,
                                    now=datetime(2026, 9, 8, tzinfo=timezone.utc))
            self.assertIsNotNone(path)
            assert path is not None
            self.assertTrue(path.name.startswith("2026-09-08-lease-concern-example-thing-"),
                            f"unexpected stem: {path.name}")
            written = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual("receipt:example/thing", written["receipt_id"])

    def test_refuses_to_overwrite_a_different_settlement(self) -> None:
        """Found by closing a COMPLETED lease again: the first record was destroyed.

        A closure is a governed claim carrying a receipt and evidence addresses. The
        first version replaced one settlement's claim with another's silently, which is
        the erasure AGENTS.md forbids of a retraction.
        """
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "reports").mkdir()
            settlement.write(CLOSED, root, now=datetime(2026, 9, 8, tzinfo=timezone.utc))
            amended = json.loads(json.dumps(CLOSED))
            amended["closure_evidence"]["receipt_id"] = "receipt:example/second"
            with self.assertRaises(settlement.SettlementRefused) as refusal:
                settlement.write(amended, root, now=datetime(2026, 9, 8, tzinfo=timezone.utc))
            self.assertIn("receipt:example/thing", str(refusal.exception))
            standing = json.loads(next(
                (root / settlement.SETTLEMENTS).glob("*.json")).read_text(encoding="utf-8"))
            self.assertEqual("receipt:example/thing", standing["receipt_id"])

    def test_re_running_the_same_closure_is_idempotent(self) -> None:
        """A close retried after a partial failure must not be refused as an amendment."""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "reports").mkdir()
            first = settlement.write(CLOSED, root,
                                     now=datetime(2026, 9, 8, 9, tzinfo=timezone.utc))
            second = settlement.write(CLOSED, root,
                                      now=datetime(2026, 9, 8, 17, tzinfo=timezone.utc))
            self.assertEqual(first, second)
            written = json.loads(Path(str(second)).read_text(encoding="utf-8"))
            self.assertEqual("2026-09-08T09:00:00Z", written["closed_at"])

    def test_writes_nothing_outside_a_repository_tree(self) -> None:
        """A lease command run from an unrelated checkout must not create a stray tree."""
        with tempfile.TemporaryDirectory() as raw:
            self.assertIsNone(settlement.write(CLOSED, Path(raw)))
            self.assertEqual([], list(Path(raw).iterdir()))


    def test_a_record_for_another_lease_does_not_block_this_one(self) -> None:
        """The first anti-amendment repair globbed `*-{slug}.json` and matched other leases.

        `lease:concern-b-lease-concern-a` ends with `-lease-concern-a`, so recording it
        left `lease:concern-a` permanently unclosable behind a refusal that named the
        wrong record. The glob is anchored to the date shape and the record's own
        lease_id is compared.
        """
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "reports").mkdir()
            longer = json.loads(json.dumps(CLOSED))
            longer["lease_id"] = "lease:concern-b-lease-concern-a"
            settlement.write(longer, root, now=datetime(2026, 9, 9, tzinfo=timezone.utc))
            shorter = json.loads(json.dumps(CLOSED))
            shorter["lease_id"] = "lease:concern-a"
            written = settlement.write(shorter, root,
                                       now=datetime(2026, 9, 9, tzinfo=timezone.utc))
            self.assertIsNotNone(written)
            self.assertEqual(2, len(list((root / settlement.SETTLEMENTS).glob("*.json"))))

    def test_two_leases_that_slug_alike_keep_separate_records(self) -> None:
        """`lease:concern-a` and `lease:concern/a` both slug to `lease-concern-a`.

        The filename then matches exactly and the anchored glob cannot separate them.
        Only comparing the record's own lease_id does. This case exists so that removing
        that comparison fails a test rather than silently merging two settlements.
        """
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "reports").mkdir()
            first = json.loads(json.dumps(CLOSED))
            first["lease_id"] = "lease:concern-a"
            second = json.loads(json.dumps(CLOSED))
            second["lease_id"] = "lease:concern/a"
            second["closure_evidence"]["receipt_id"] = "receipt:example/other"
            settlement.write(first, root, now=datetime(2026, 9, 9, tzinfo=timezone.utc))
            written = settlement.write(second, root,
                                       now=datetime(2026, 9, 9, tzinfo=timezone.utc))
            self.assertIsNotNone(written)
            records = sorted((root / settlement.SETTLEMENTS).glob("*.json"))
            self.assertEqual(2, len(records),
                             "a second lease whose id slugs alike must not adopt the first "
                             "lease's record")
            self.assertEqual({"lease:concern-a", "lease:concern/a"},
                             {json.loads(r.read_text(encoding="utf-8"))["lease_id"]
                              for r in records})

    def test_a_record_whose_identifier_disagrees_is_not_adopted(self) -> None:
        """The filename is a guess; the identifier inside the record is the check.

        A file carrying this lease's exact name but another lease's `lease_id` - copied,
        hand-edited, or produced by a future naming change - must not be adopted as this
        lease's settlement.
        """
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "reports").mkdir()
            written = settlement.write(CLOSED, root,
                                       now=datetime(2026, 9, 9, tzinfo=timezone.utc))
            assert written is not None
            impostor = json.loads(written.read_text(encoding="utf-8"))
            impostor["lease_id"] = "lease:concern-somebody/else"
            impostor["receipt_id"] = "receipt:somebody/else"
            written.write_text(json.dumps(impostor, indent=2) + "\n", encoding="utf-8")
            again = settlement.write(CLOSED, root,
                                     now=datetime(2026, 9, 9, tzinfo=timezone.utc))
            self.assertIsNotNone(again)
            self.assertEqual(CLOSED["lease_id"],
                             json.loads(Path(str(again)).read_text(encoding="utf-8"))["lease_id"])

    def test_a_second_claim_on_a_later_day_is_refused(self) -> None:
        """The stem carried the date, so the next day admitted a second, higher claim."""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "reports").mkdir()
            settlement.write(CLOSED, root, now=datetime(2026, 9, 8, 23, 59, tzinfo=timezone.utc))
            amended = json.loads(json.dumps(CLOSED))
            amended["closure_evidence"]["receipt_id"] = "receipt:example/second"
            amended["closure_evidence"]["standing_reached"] = "RATIFIED"
            with self.assertRaises(settlement.SettlementRefused):
                settlement.write(amended, root,
                                 now=datetime(2026, 9, 9, 0, 1, tzinfo=timezone.utc))
            self.assertEqual(1, len(list((root / settlement.SETTLEMENTS).glob("*.json"))))

    def test_an_unreadable_record_refuses_rather_than_raising(self) -> None:
        """A corrupt record raised JSONDecodeError with absolute paths in the traceback."""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "reports").mkdir()
            written = settlement.write(CLOSED, root,
                                       now=datetime(2026, 9, 9, tzinfo=timezone.utc))
            assert written is not None
            written.write_text("{ not json", encoding="utf-8")
            with self.assertRaises(settlement.SettlementRefused) as refusal:
                settlement.write(CLOSED, root, now=datetime(2026, 9, 9, tzinfo=timezone.utc))
            self.assertNotIn(str(root), str(refusal.exception))

    def test_the_unwritable_refusal_carries_no_absolute_path(self) -> None:
        """The refusal reported whatever path the OSError named, which can be absolute."""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "reports").mkdir()
            original = settlement.write

            def explode(lease, where, now=None):
                raise OSError(28, "No space left on device", str(where / "settlements"))

            settlement.write = explode
            try:
                path, defect = settlement.record_closure(CLOSED, root)
            finally:
                settlement.write = original
            self.assertIsNone(path)
            assert defect is not None
            self.assertEqual("SETTLEMENT_UNWRITABLE", defect["code"])
            self.assertNotIn(str(root), defect["message"])


class ClosureOrdering(unittest.TestCase):
    """The committed record is written before the closure reaches the log."""

    def test_the_source_order_holds(self) -> None:
        """Scoped to cmd_close: cmd_take appends to the same log earlier in the file."""
        body = _close_body()
        self.assertLess(body.index("settlement.record_closure(candidate"),
                        body.index("store.append(directory, store.LEASES_LOG"))

    def test_the_record_lands_under_the_root_and_not_the_working_directory(self) -> None:
        """Found by closing from a subdirectory: cmd_close used the process CWD.

        The first repair was checked by two greps over the source. A mutation of equal
        line count reinstated the defect exactly while unittest, lint and verify all
        stayed green, so the fatal defect's repair carried no defeating fixture. This
        drives cmd_close with a root that is deliberately not the working directory and
        asserts where the record actually lands.
        """
        import argparse
        import os

        from sovlease import commands
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "tree"
            (root / "reports").mkdir(parents=True)
            store_dir = root / "store"
            store_dir.mkdir()
            elsewhere = Path(raw) / "elsewhere"
            elsewhere.mkdir()
            _seed_held_lease(commands, store_dir)

            original_context = commands._context
            commands._context = lambda name=None: (root, store_dir, "session-test")
            here = os.getcwd()
            try:
                os.chdir(elsewhere)
                code = commands.cmd_close(argparse.Namespace(
                    name=None, as_json=True, lease=CLOSED["lease_id"], receipt="receipt:x",
                    evidence=["a.py"], standing="BUILT", witnessed_by=None))
            finally:
                os.chdir(here)
                commands._context = original_context

            self.assertEqual(0, code)
            self.assertEqual(1, len(list((root / settlement.SETTLEMENTS).glob("*.json"))),
                             "the record must land under the root, not the working directory")
            self.assertEqual([], list(elsewhere.rglob("*.json")),
                             "nothing may be written beside the working directory")

    def test_a_refused_record_stops_the_close(self) -> None:
        """A mutation keeping the source order and dropping the refusal passed every case.

        The order assertion above cannot see that, so this drives the behaviour against a
        fixture store: when record_closure reports a defect, cmd_close returns non-zero
        and appends nothing. Deleting the `return 1` in cmd_close fails here.
        """
        import argparse

        from sovlease import commands
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "reports").mkdir()
            store_dir = root / "store"
            store_dir.mkdir()
            _seed_held_lease(commands, store_dir)

            original_context = commands._context
            original_record = settlement.record_closure
            commands._context = lambda name=None: (root, store_dir, "session-test")
            settlement.record_closure = lambda lease, where: (
                None, {"code": "SETTLEMENT_UNWRITABLE", "message": "injected"})
            try:
                code = commands.cmd_close(argparse.Namespace(
                    name=None, as_json=True, lease=CLOSED["lease_id"], receipt="receipt:x",
                    evidence=["a.py"], standing="BUILT", witnessed_by=None))
            finally:
                commands._context = original_context
                settlement.record_closure = original_record

            self.assertEqual(1, code, "a refused record must refuse the close")
            events = [entry.get("event") for entry
                      in commands.store.read(store_dir, commands.store.LEASES_LOG)]
        self.assertNotIn("close", events, "the closure was appended despite a refused record")


if __name__ == "__main__":
    unittest.main()
