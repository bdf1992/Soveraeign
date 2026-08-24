"""Prove the docket both admits a sound routing and refuses a broken one.

Every case has a defeating counterpart (`AGENTS.md`, Testing and verification). A
checker that only ever sees the checked-in file proves nothing about what it would
catch, and this one exists precisely to catch a claim that `STATUS.yaml` already
answers something when it does not.

The unit is a question, not a record. `decisions/0036` carries three questions
with different answers, and the v1 contract - which routed records - marked the
whole record as not reaching Bdo on the strength of the first one. The cases
below include that shape directly.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_docket  # noqa: E402

STANDING = json.loads((ROOT / "contracts" / "decision-standing.json").read_text("utf-8"))
ROUTING = json.loads((ROOT / "contracts" / "acceptance-routing.json").read_text("utf-8"))


class CheckedInState(unittest.TestCase):
    """The repository as it stands passes its own gate."""

    def test_the_checked_in_routing_has_no_defect(self) -> None:
        self.assertEqual(sov_docket.check(), 0)

    def test_every_open_record_carries_at_least_one_question(self) -> None:
        """An open record with no question is one nobody can say whose it is."""
        rows, unknown = sov_docket.graded()
        self.assertEqual(unknown, [], "a status line is missing from the crosswalk")
        bare = [row["id"] for row in rows if not row["settled"] and not row["questions"]]
        self.assertEqual(bare, [])

    def test_the_crosswalk_covers_every_status_line_in_use(self) -> None:
        in_use = {record["status_line"] for record in sov_docket.records()}
        self.assertEqual(in_use - set(STANDING["crosswalk"]), set())

    def test_every_crosswalk_target_is_a_declared_standing(self) -> None:
        targets = set(STANDING["crosswalk"].values())
        self.assertEqual(targets - set(STANDING["standings"]), set())

    def test_a_record_may_carry_questions_with_different_answers(self) -> None:
        """The whole reason the unit changed: 0036 splits, and the split survives."""
        questions = [entry for entry in sov_docket.open_questions()
                     if entry["record"] == "0036"]
        self.assertGreater(len(questions), 1)
        self.assertEqual({entry["reaches_owner"] for entry in questions}, {True, False})
        for entry in questions:
            self.assertEqual(entry["enumerated_from"], "record-section")


class Defeats(unittest.TestCase):
    """Each declared check, given exactly the input it exists to refuse."""

    def setUp(self) -> None:
        self.contract = json.loads(json.dumps(ROUTING))
        self.original = sov_docket.ROUTING

    def tearDown(self) -> None:
        sov_docket.ROUTING = self.original

    def _refuses(self, mutate) -> None:
        mutate(self.contract["questions"])
        with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            path = Path(tmp) / "routing.json"
            path.write_text(json.dumps(self.contract), encoding="utf-8")
            sov_docket.ROUTING = path
            self.assertEqual(sov_docket.check(), 1)

    def test_a_status_key_that_is_not_in_status_yaml_fails(self) -> None:
        """The defect this checker caught in its own author's first draft."""
        self._refuses(lambda q: q["0001-A"].__setitem__("already_recorded_as", "no_such_field"))

    def test_a_question_against_a_record_that_does_not_exist_fails(self) -> None:
        def mutate(questions: dict) -> None:
            questions["9999-A"] = dict(questions["0020-A"], record="9999")
        self._refuses(mutate)

    def test_reaching_the_owner_without_naming_a_category_fails(self) -> None:
        self._refuses(lambda q: q["0039-A"].__setitem__("categories", []))

    def test_naming_a_category_without_reaching_the_owner_fails(self) -> None:
        self._refuses(lambda q: q["0040-A"].__setitem__("categories", ["product_intent"]))

    def test_an_undeclared_owner_held_category_fails(self) -> None:
        self._refuses(lambda q: q["0039-A"].__setitem__("categories", ["vibes"]))

    def test_a_question_missing_its_reason_fails(self) -> None:
        """A routing with no reason is an assertion, and assertions are what this replaces."""
        self._refuses(lambda q: q["0020-A"].pop("reason"))

    def test_a_key_outside_the_declared_vocabulary_fails(self) -> None:
        self._refuses(lambda q: q["0020-A"].__setitem__("accepted_by", "Bdo"))

    def test_an_undeclared_enumeration_source_fails(self) -> None:
        self._refuses(lambda q: q["0020-A"].__setitem__("enumerated_from", "vibes"))

    def test_splitting_a_record_that_does_not_enumerate_its_questions_fails(self) -> None:
        """You cannot claim to have split what the record never separated."""
        def mutate(questions: dict) -> None:
            questions["0020-B"] = dict(questions["0020-A"], question="an invented second question")
        self._refuses(mutate)


class OwnerQuestionsSection(unittest.TestCase):
    """The rule that turns routing from inference into reading a list.

    Grandfathered below the threshold and required at or above it, the way
    `scripts/lint.py` names module-size debt rather than silently forgiving it.
    """

    def setUp(self) -> None:
        self.original = sov_docket.DECISIONS

    def tearDown(self) -> None:
        sov_docket.DECISIONS = self.original

    def _check_with(self, name: str, body: str) -> int:
        with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            staged = Path(tmp) / "decisions"
            staged.mkdir()
            for path in self.original.glob("0*.md"):
                (staged / path.name).write_text(path.read_text("utf-8"), encoding="utf-8")
            (staged / name).write_text(body, encoding="utf-8")
            sov_docket.DECISIONS = staged
            return sov_docket.check()

    def test_a_new_record_without_the_section_fails(self) -> None:
        body = "# 0043 · invented\n\nStatus: `PROPOSED · BDO HAS NOT RULED`\n\n## Decision\n\nx\n"
        self.assertEqual(self._check_with("0043-invented.md", body), 1)

    def test_a_new_record_with_the_section_passes_the_rule(self) -> None:
        """It still fails for being unrouted, which is a different defect and the right one."""
        body = ("# 0043 · invented\n\nStatus: `PROPOSED · BDO HAS NOT RULED`\n\n"
                "## Decision\n\nx\n\n## What still waits on Bdo\n\n- one question\n")
        with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            staged = Path(tmp) / "decisions"
            staged.mkdir()
            for path in self.original.glob("0*.md"):
                (staged / path.name).write_text(path.read_text("utf-8"), encoding="utf-8")
            (staged / "0043-invented.md").write_text(body, encoding="utf-8")
            sov_docket.DECISIONS = staged
            records = {r["id"]: r["enumerates"] for r in sov_docket.records()}
            self.assertTrue(records["0043"])

    def test_the_grandfathered_records_are_not_failed_by_the_rule(self) -> None:
        """Seventeen open records predate the rule and must not turn the gate red."""
        threshold = STANDING["owner_questions_section"]["required_from_record"]
        silent = [row["id"] for row in sov_docket.records()
                  if not row["enumerates"] and row["id"] < threshold]
        self.assertTrue(silent, "the rule is pointless if every old record already complies")
        self.assertEqual(sov_docket.check(), 0)


class Routing(unittest.TestCase):
    """What the routing says, held against the rules it claims to apply."""

    def test_no_entry_has_a_field_that_could_record_a_settlement(self) -> None:
        """decisions/0023 reserves acceptance to Bdo, so the file cannot express one.

        Structural rather than textual: an entry's reason may well mention that
        something was accepted, because saying so is the whole point of
        `already_recorded_as`. What must not exist is a field this file could
        write an acceptance into.
        """
        allowed = set(ROUTING["entry_keys"])
        forbidden = {"settled", "settled_by", "accepted", "accepted_by", "accepted_at",
                     "ratified", "ratified_by", "standing", "outcome", "owner_action"}
        self.assertEqual(allowed & forbidden, set())
        for qid, entry in ROUTING["questions"].items():
            self.assertEqual(set(entry) - allowed, set(), qid)

    def test_a_question_reaching_the_owner_names_an_owner_held_category(self) -> None:
        declared = set(STANDING["owner_held_categories"])
        for qid, entry in ROUTING["questions"].items():
            if entry["reaches_owner"]:
                self.assertTrue(set(entry["categories"]) <= declared, qid)
                self.assertTrue(entry["categories"], qid)


if __name__ == "__main__":
    unittest.main()
