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
CLOSED = {
    "lease_id": "lease:concern-example/thing",
    "concern": {"kind": "concern", "reference": "concern:example/thing"},
    "state": "COMPLETED",
    "holder": {
        "principal_id": "urn:soveraeign:principal:instance:session-a",
        "parent_lease": None,
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
            self.assertEqual("2026-09-08-lease-concern-example-thing.json", path.name)
            written = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual("receipt:example/thing", written["receipt_id"])

    def test_writes_nothing_outside_a_repository_tree(self) -> None:
        """A lease command run from an unrelated checkout must not create a stray tree."""
        with tempfile.TemporaryDirectory() as raw:
            self.assertIsNone(settlement.write(CLOSED, Path(raw)))
            self.assertEqual([], list(Path(raw).iterdir()))


if __name__ == "__main__":
    unittest.main()
