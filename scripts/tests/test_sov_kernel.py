"""Cases for the SPEC.md transition projection and the drift check over it.

`contracts/kernel-transitions.json` is authored, not generated, so nothing but a
check stops an edit to one file from widening or narrowing what the other
admits. Every case here has a positive form and a form proving the required
defect is reported.

Judging one transition request against that table is a different concern,
covered by the declared corpus in
`conformance/fixtures/kernel/transition-cases.json` and run by
`scripts/sov_kernel.py selfcheck`.
"""

from __future__ import annotations

from pathlib import Path
import json
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sovkernel import projection  # noqa: E402
from sovkernel import transitions as kernel  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]

SPEC = """## Transition contract

| Transition | Preconditions | Commit | Refusal |
| --- | --- | --- | --- |
| `capture_source` | readable bytes; address available | create immutable `Source` | `UNREADABLE` or `DIGEST_MISMATCH` |
| `cross` | declared source, authority, destination | destination record and receipt | reasoned refusal |

Trailing prose.
"""


def authored(*rows: dict) -> dict:
    """A kernel table in the shape contracts/kernel-transitions.json uses."""
    return {"transitions": list(rows)}


class Derivation(unittest.TestCase):
    def test_transitions_derive_in_declared_order(self):
        self.assertEqual(list(projection.derive(SPEC)), ["capture_source", "cross"])

    def test_preconditions_split_on_semicolons(self):
        table = projection.derive(SPEC)
        self.assertEqual(table["capture_source"]["preconditions"],
                         ["readable bytes", "address available"])

    def test_named_refusal_codes_are_captured_in_order(self):
        table = projection.derive(SPEC)
        self.assertEqual(table["capture_source"]["refusals"],
                         ["UNREADABLE", "DIGEST_MISMATCH"])

    def test_an_open_reasoned_refusal_is_recorded_as_such(self):
        cross = projection.derive(SPEC)["cross"]
        self.assertEqual(cross["refusals"], [])
        self.assertTrue(cross["reasoned_refusal_admitted"])

    def test_a_spec_without_the_table_refuses_rather_than_deriving_nothing(self):
        with self.assertRaises(ValueError):
            projection.derive("# Spec\n\nNo transition table here.\n")

    def test_a_table_header_with_no_rows_refuses_rather_than_reporting_agreement(self):
        """Deriving zero transitions would make every authored row look like drift."""
        with self.assertRaises(ValueError):
            projection.derive("## Transition contract\n\n"
                              "| Transition | Preconditions | Commit | Refusal |\n"
                              "| --- | --- | --- | --- |\n\nProse.\n")


class Invariants(unittest.TestCase):
    def _derived(self, **transition):
        base = {"preconditions": ["a precondition"], "commit": "a commit",
                "refusals": ["A_CODE"], "reasoned_refusal_admitted": False}
        base.update(transition)
        return {"t": base}

    def test_a_complete_transition_carries_no_defect(self):
        self.assertEqual(projection.invariants(self._derived()), [])

    def test_a_transition_with_no_precondition_is_a_defect(self):
        self.assertIn("no precondition",
                      " ".join(projection.invariants(self._derived(preconditions=[]))))

    def test_a_transition_with_no_commit_is_a_defect(self):
        self.assertIn("no commit",
                      " ".join(projection.invariants(self._derived(commit=""))))

    def test_a_transition_with_no_refusal_path_at_all_is_a_defect(self):
        """A transition that cannot refuse is a transition that cannot gate."""
        defects = projection.invariants(
            self._derived(refusals=[], reasoned_refusal_admitted=False))
        self.assertIn("no refusal path", " ".join(defects))

    def test_an_open_reasoned_refusal_satisfies_the_refusal_path(self):
        self.assertEqual(projection.invariants(
            self._derived(refusals=[], reasoned_refusal_admitted=True)), [])

    def test_a_lower_case_refusal_code_is_a_defect(self):
        self.assertIn("not upper case", " ".join(projection.invariants(
            self._derived(refusals=["stale_state"]))))


class Drift(unittest.TestCase):
    def setUp(self):
        self.derived = projection.derive(SPEC)
        self.compiled = authored(
            {"transition": "capture_source", "preconditions": ["source_address"],
             "commit": "COMMITTED", "refusals": ["UNREADABLE", "DIGEST_MISMATCH"]},
            {"transition": "cross", "preconditions": ["source"], "commit": "COMMITTED",
             "refusals": []},
        )

    def test_an_agreeing_contract_reports_no_drift(self):
        self.assertEqual(projection.conflicts(self.derived, self.compiled), [])

    def test_a_normalised_precondition_is_not_drift(self):
        """The authored table states field names on purpose; SPEC states prose."""
        self.compiled["transitions"][0]["preconditions"] = ["something", "entirely", "other"]
        self.assertEqual(projection.conflicts(self.derived, self.compiled), [])

    def test_a_transition_missing_from_the_contract_is_reported(self):
        self.compiled["transitions"] = self.compiled["transitions"][:1]
        self.assertIn("the kernel table does not carry it",
                      " ".join(projection.conflicts(self.derived, self.compiled)))

    def test_a_transition_only_in_the_contract_is_reported(self):
        self.compiled["transitions"].append(
            {"transition": "invented", "commit": "COMMITTED", "refusals": []})
        self.assertIn("SPEC.md does not declare it",
                      " ".join(projection.conflicts(self.derived, self.compiled)))

    def test_a_refusal_code_dropped_from_the_contract_is_reported(self):
        """The direction that matters: the kernel would accept what SPEC refuses."""
        self.compiled["transitions"][0]["refusals"] = ["UNREADABLE"]
        self.assertIn("SPEC.md names refusal DIGEST_MISMATCH; the kernel table omits it",
                      " ".join(projection.conflicts(self.derived, self.compiled)))

    def test_an_extra_code_on_a_closed_spec_row_is_reported(self):
        self.compiled["transitions"][0]["refusals"].append("INVENTED")
        self.assertIn("the kernel table names refusal INVENTED; SPEC.md does not",
                      " ".join(projection.conflicts(self.derived, self.compiled)))

    def test_an_extra_code_under_an_open_reasoned_refusal_is_admitted(self):
        """Naming a specific code for an open reasoned refusal is what SPEC invites."""
        self.compiled["transitions"][1]["refusals"] = ["AUTHORITY_REFUSED"]
        self.assertEqual(projection.conflicts(self.derived, self.compiled), [])


class AgainstTheRepository(unittest.TestCase):
    """The checked-in contract must agree with the checked-in SPEC.md."""

    def test_the_repository_carries_no_drift(self):
        spec = (ROOT / "SPEC.md").read_bytes().decode("utf-8")
        derived = projection.derive(spec)
        self.assertEqual(projection.invariants(derived), [])
        self.assertEqual(projection.conflicts(derived, kernel.load_table(ROOT)), [])

    def test_every_authored_transition_declares_a_refusal_path(self):
        table = kernel.load_table(ROOT)
        without = [row["transition"] for row in table["transitions"]
                   if not row.get("refusals")]
        self.assertEqual(without, [], "a transition that cannot refuse cannot gate")

    def test_the_authored_contract_is_valid_json_with_a_transition_list(self):
        raw = json.loads((ROOT / "contracts" / "kernel-transitions.json")
                         .read_bytes().decode("utf-8"))
        self.assertIsInstance(raw["transitions"], list)
        self.assertTrue(raw["transitions"])


if __name__ == "__main__":
    unittest.main()
