"""Unit tests for the ticket coordination contract mechanics.

The semantic cases live in ``conformance/fixtures/tickets/transition-cases.json`` and
run through ``scripts/sov_ticket.py selfcheck``. These tests cover local mechanics,
edge cases, and the structural properties that keep the declared contracts and the
implementation from drifting apart. The two readers of the metadata block are tested
in ``test_ticket_readers.py``.
"""

from __future__ import annotations

from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovticket import queue as queuemod  # noqa: E402
from sovticket import transitions as transmod  # noqa: E402
from sovkernel.jsonschema import validate  # noqa: E402


class JsonSchemaTests(unittest.TestCase):
    """The bounded validator refuses what it cannot check rather than passing it."""

    def test_unsupported_keyword_is_a_defect(self) -> None:
        self.assertTrue(validate("abc", {"maxLength": 2}))

    def test_unsupported_format_is_a_defect(self) -> None:
        self.assertTrue(validate("x", {"type": "string", "format": "email"}))

    def test_boolean_is_not_an_integer(self) -> None:
        self.assertTrue(validate(True, {"type": "integer"}))

    def test_one_of_requires_exactly_one_branch(self) -> None:
        schema = {"oneOf": [{"type": "string"}, {"type": "string", "minLength": 1}]}
        self.assertTrue(validate("x", schema))

    def test_unique_items_and_min_items(self) -> None:
        schema = {"type": "array", "items": {"type": "string"}, "uniqueItems": True, "minItems": 2}
        self.assertTrue(validate(["a", "a"], schema))
        self.assertFalse(validate(["a", "b"], schema))

    def test_additional_properties_false(self) -> None:
        schema = {"type": "object", "properties": {"a": {"type": "string"}}, "additionalProperties": False}
        self.assertTrue(validate({"a": "x", "b": "y"}, schema))

    def test_local_ref_resolves_and_remote_ref_is_refused(self) -> None:
        root = {"$defs": {"n": {"type": "integer"}}, "$ref": "#/$defs/n"}
        self.assertFalse(validate(3, root))
        self.assertTrue(validate(3, {"$ref": "https://example.invalid/schema.json"}))

    def test_date_time_format(self) -> None:
        schema = {"type": "string", "format": "date-time"}
        self.assertFalse(validate("2026-08-23T03:25:13Z", schema))
        self.assertTrue(validate("yesterday", schema))


class TransitionTableTests(unittest.TestCase):
    """The declared table and the fixture corpus stay aligned."""

    def setUp(self) -> None:
        self.table = transmod.load_table(ROOT)
        path = ROOT / "conformance" / "fixtures" / "tickets" / "transition-cases.json"
        self.cases = json.loads(path.read_text(encoding="utf-8"))["cases"]

    def test_every_declared_refusal_code_is_exercised(self) -> None:
        expected = {case["expect"] for case in self.cases}
        declared = set(self.table["refusal_codes"]) | {"MALFORMED_REQUEST"}
        unexercised = declared - expected
        self.assertEqual(unexercised, set(), f"refusal codes with no defeating case: {sorted(unexercised)}")

    def test_every_case_expectation_is_a_declared_code(self) -> None:
        declared = set(self.table["refusal_codes"]) | {"ALLOWED", "MALFORMED_REQUEST"}
        for case in self.cases:
            self.assertIn(case["expect"], declared, case["case_id"])

    def test_every_transition_names_its_required_evidence(self) -> None:
        for entry in self.table["transitions"]:
            with self.subTest(transition=f"{entry['from']}->{entry['to']}"):
                self.assertTrue(entry.get("requires_evidence"), "a transition must name its evidence")
                self.assertTrue(entry.get("actor_kinds"), "a transition must name its actor kinds")

    def test_ratification_is_reserved_to_a_human_owner(self) -> None:
        entry = next(e for e in self.table["transitions"] if e["to"] == "RATIFIED")
        self.assertEqual(entry["actor_kinds"], ["HUMAN"])
        self.assertTrue(entry["requires_owner"])

    def test_witness_requires_a_distinct_actor_and_settled_purple(self) -> None:
        entry = next(
            e for e in self.table["transitions"]
            if e["to"] == "WITNESSED" and e["from"] == "BUILT_SELF_TESTED_NOT_WITNESSED"
        )
        self.assertTrue(entry["requires_distinct_actor"])
        self.assertTrue(entry["requires_purple"])


class QueueTests(unittest.TestCase):
    """The queue is a deterministic, rebuildable projection."""

    def setUp(self) -> None:
        self.policy = queuemod.load_policy(ROOT)

    def _ticket(self, number: int, **metadata: object) -> queuemod.Ticket:
        base = {"kind": "bit", "village": "ground-and-evidence", "horizon": "NOW", "standing": "OPEN"}
        base.update(metadata)
        return queuemod.Ticket(number=number, title=f"t{number}", state="OPEN", metadata=base)

    def test_unsatisfied_dependency_blocks_and_credits_the_blocker(self) -> None:
        entries = queuemod.build(
            [self._ticket(1), self._ticket(2, requires=["#1"])], self.policy
        )
        by_ref = {entry.issue: entry for entry in entries}
        self.assertTrue(by_ref["#2"].blocked)
        self.assertEqual(by_ref["#2"].blocked_by, ("#1",))
        self.assertEqual(by_ref["#1"].unblocks, ("#2",))

    def test_built_dependency_unblocks_its_dependents(self) -> None:
        entries = queuemod.build(
            [
                self._ticket(1, standing="BUILT_SELF_TESTED_NOT_WITNESSED"),
                self._ticket(2, requires=["#1"]),
            ],
            self.policy,
        )
        self.assertFalse({e.issue: e for e in entries}["#2"].blocked)

    def test_closed_dependency_unblocks_and_is_omitted(self) -> None:
        closed = queuemod.Ticket(number=1, title="t1", state="CLOSED", metadata={"standing": "OPEN"})
        entries = queuemod.build([closed, self._ticket(2, requires=["#1"])], self.policy)
        self.assertEqual([entry.issue for entry in entries], ["#2"])
        self.assertFalse(entries[0].blocked)

    def test_a_story_is_told_not_taken(self) -> None:
        story = self._ticket(
            60, kind="story", leans_on=["#1"], asks=[{"of": "#1", "adjustment": "exist"}]
        )
        entries = queuemod.build([self._ticket(1), story], self.policy)
        self.assertEqual([entry.issue for entry in entries], ["#1"])
        self.assertEqual(entries[0].unblocks, ())

    def test_dependency_outside_the_ticket_set_blocks(self) -> None:
        entries = queuemod.build([self._ticket(2, requires=["#99"])], self.policy)
        self.assertTrue(entries[0].blocked)

    def test_unblocked_work_sorts_ahead_of_blocked_work(self) -> None:
        entries = queuemod.build(
            [self._ticket(1, requires=["#99"]), self._ticket(2)], self.policy
        )
        self.assertEqual([entry.issue for entry in entries], ["#2", "#1"])

    def test_ordering_is_deterministic(self) -> None:
        tickets = [self._ticket(n) for n in (5, 3, 9, 1)]
        first = [entry.issue for entry in queuemod.build(tickets, self.policy)]
        second = [entry.issue for entry in queuemod.build(list(reversed(tickets)), self.policy)]
        self.assertEqual(first, second)

    def test_next_action_is_declared_for_every_standing(self) -> None:
        for standing in self.policy["standing_rank"]:
            self.assertIn(standing, self.policy["next_action"], standing)


if __name__ == "__main__":
    unittest.main()
