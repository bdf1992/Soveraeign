"""Cases for the kernel transition projection.

Every check has a positive case and a case proving the required refusal. The
projection is derived from `SPEC.md`; these cases prove it cannot silently
disagree with the document that governs it.
"""

from __future__ import annotations

from pathlib import Path
import json
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import sov_kernel  # noqa: E402


SPEC = """## Transition contract

| Transition | Preconditions | Commit | Refusal |
| --- | --- | --- | --- |
| `capture_source` | readable bytes; address available | create immutable `Source` | `UNREADABLE` or `DIGEST_MISMATCH` |
| `cross` | declared source, authority, destination | destination record and receipt | reasoned refusal |

Trailing prose.
"""


class Derivation(unittest.TestCase):
    def test_transitions_derive_in_declared_order(self):
        table = sov_kernel.derive(SPEC)
        self.assertEqual(table["order"], ["capture_source", "cross"])

    def test_preconditions_split_on_semicolons(self):
        table = sov_kernel.derive(SPEC)
        self.assertEqual(table["transitions"]["capture_source"]["preconditions"],
                         ["readable bytes", "address available"])

    def test_named_refusal_codes_are_captured_in_order(self):
        table = sov_kernel.derive(SPEC)
        self.assertEqual(table["transitions"]["capture_source"]["refusal_codes"],
                         ["UNREADABLE", "DIGEST_MISMATCH"])

    def test_an_open_reasoned_refusal_is_recorded_as_such(self):
        table = sov_kernel.derive(SPEC)
        cross = table["transitions"]["cross"]
        self.assertEqual(cross["refusal_codes"], [])
        self.assertTrue(cross["reasoned_refusal_admitted"])

    def test_a_spec_without_the_table_refuses_rather_than_deriving_nothing(self):
        with self.assertRaises(SystemExit):
            sov_kernel.derive("# Spec\n\nNo transition table here.\n")


class Invariants(unittest.TestCase):
    def _table(self, **transition):
        base = {"preconditions": ["a precondition"], "commit": "a commit",
                "refusal_codes": ["A_CODE"], "reasoned_refusal_admitted": False}
        base.update(transition)
        return {"transitions": {"t": base}}

    def test_a_complete_transition_carries_no_defect(self):
        self.assertEqual(sov_kernel.invariants(self._table()), [])

    def test_a_transition_with_no_precondition_is_a_defect(self):
        self.assertIn("no precondition", " ".join(sov_kernel.invariants(
            self._table(preconditions=[]))))

    def test_a_transition_with_no_commit_is_a_defect(self):
        self.assertIn("no commit", " ".join(sov_kernel.invariants(self._table(commit=""))))

    def test_a_transition_with_no_refusal_path_at_all_is_a_defect(self):
        """A transition that cannot refuse is a transition that cannot gate."""
        defects = sov_kernel.invariants(
            self._table(refusal_codes=[], reasoned_refusal_admitted=False))
        self.assertIn("no refusal path", " ".join(defects))

    def test_an_open_reasoned_refusal_satisfies_the_refusal_path(self):
        self.assertEqual(sov_kernel.invariants(
            self._table(refusal_codes=[], reasoned_refusal_admitted=True)), [])

    def test_a_lower_case_refusal_code_is_a_defect(self):
        self.assertIn("not upper case", " ".join(sov_kernel.invariants(
            self._table(refusal_codes=["stale_state"]))))

    def test_an_empty_projection_is_a_defect(self):
        self.assertIn("no transitions", " ".join(sov_kernel.invariants({"transitions": {}})))


class Drift(unittest.TestCase):
    def setUp(self):
        self.derived = sov_kernel.derive(SPEC)
        self.stored = json.loads(json.dumps(self.derived))

    def test_an_identical_projection_reports_no_drift(self):
        self.assertEqual(sov_kernel.compare(self.derived, self.stored), [])

    def test_a_transition_added_to_spec_is_reported_missing(self):
        del self.stored["transitions"]["cross"]
        self.assertIn("absent from the projection",
                      " ".join(sov_kernel.compare(self.derived, self.stored)))

    def test_a_transition_only_in_the_projection_is_reported(self):
        self.stored["transitions"]["invented"] = self.stored["transitions"]["cross"]
        self.assertIn("absent from SPEC.md",
                      " ".join(sov_kernel.compare(self.derived, self.stored)))

    def test_a_changed_refusal_code_is_reported(self):
        self.stored["transitions"]["capture_source"]["refusal_codes"] = ["RENAMED"]
        self.assertIn("refusal_codes", " ".join(sov_kernel.compare(self.derived, self.stored)))

    def test_a_changed_precondition_is_reported(self):
        self.stored["transitions"]["capture_source"]["preconditions"] = ["something else"]
        self.assertIn("preconditions", " ".join(sov_kernel.compare(self.derived, self.stored)))

    def test_a_moved_spec_digest_is_reported_with_the_repair(self):
        self.stored["source_digest"] = "0000000000000000"
        defects = " ".join(sov_kernel.compare(self.derived, self.stored))
        self.assertIn("SPEC.md moved", defects)
        self.assertIn("sync", defects)

    def test_a_drifted_table_id_is_reported(self):
        self.stored["table_id"] = "something-else/v1"
        self.assertIn("table_id drifted",
                      " ".join(sov_kernel.compare(self.derived, self.stored)))


class AgainstTheRepository(unittest.TestCase):
    """The checked-in projection must match the checked-in SPEC.md."""

    def test_selfcheck_passes_on_the_repository_as_committed(self):
        self.assertEqual(sov_kernel.command_selfcheck(None), 0)

    def test_every_spec_transition_is_projected(self):
        spec = (sov_kernel.ROOT / "SPEC.md").read_bytes().decode("utf-8")
        derived = sov_kernel.derive(spec)
        stored = json.loads(sov_kernel.PROJECTION.read_bytes().decode("utf-8"))
        self.assertEqual(sorted(derived["transitions"]), sorted(stored["transitions"]))

    def test_no_transition_lacks_a_refusal_path(self):
        stored = json.loads(sov_kernel.PROJECTION.read_bytes().decode("utf-8"))
        self.assertEqual(sov_kernel.invariants(stored), [])


if __name__ == "__main__":
    unittest.main()
