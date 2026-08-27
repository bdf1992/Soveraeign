"""Defeating fixtures for the cold-start benchmark's own grading rules.

Every case here reproduces something that was live: a probe that could only ever report
MATCH, a scorer that credited a one-character answer, a gate that read as passed because
nothing measured it. A benchmark that grades a participant has to be graded itself.
"""

from __future__ import annotations

from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovcoldstart.grading import UNMEASURED, compare, judge, truth_for  # noqa: E402
from sovcoldstart.report import scorecard  # noqa: E402

CORPUS = json.loads((ROOT / "scripts" / "sovcoldstart" / "corpus.json").read_text("utf-8"))


def _row(tier: int, verdict: str, qid: str = "Q") -> dict[str, object]:
    return {"id": qid, "tier": tier, "verdict": verdict, "q": "?", "weight": 10,
            "severity_on_failure": "FATAL", "why": ""}


class GraderRefusesFuzzyCredit(unittest.TestCase):
    """A substring in either direction used to be worth full marks."""

    def test_an_answer_contained_in_the_truth_is_wrong(self):
        question = {"grade": "exact"}
        self.assertEqual(judge(question, "O", "OPEN,BUILT,WITNESSED,RATIFIED", None), "WRONG")

    def test_one_member_does_not_satisfy_a_set(self):
        question = {"grade": "set_eq"}
        truth = ["EXTERNAL_WORLD", "RECORD_LOCAL", "RESOURCE_CONSUMPTION"]
        self.assertEqual(judge(question, "RECORD_LOCAL", truth, None), "WRONG")

    def test_a_superset_is_wrong_too(self):
        question = {"grade": "set_eq"}
        truth = ["EXTERNAL_WORLD", "RECORD_LOCAL", "RESOURCE_CONSUMPTION"]
        given = "EXTERNAL_WORLD,RECORD_LOCAL,RESOURCE_CONSUMPTION,INVENTED_CLASS"
        self.assertEqual(judge(question, given, truth, None), "WRONG")

    def test_a_worded_answer_to_a_counted_question_is_wrong_not_a_crash(self):
        question = {"grade": "int_eq"}
        self.assertEqual(judge(question, "about seventy", 70, None), "WRONG")

    def test_arrow_and_comma_spellings_of_one_answer_agree(self):
        self.assertTrue(compare("OPEN -> BUILT", "OPEN,BUILT", "exact"))


class UnmeasuredIsNeverPassed(unittest.TestCase):
    """Breaking a probe was a way to pass, rather than a way to measure less."""

    def test_an_errored_probe_does_not_fall_back_to_the_answer_key(self):
        question = {"grade": "exact", "expected": "FOUNDING"}
        self.assertIs(truth_for(question, "ERROR", None), UNMEASURED)
        self.assertEqual(judge(question, "FOUNDING", UNMEASURED, None), "UNGRADED")

    def test_a_skipped_probe_does_not_fall_back_either(self):
        question = {"grade": "exact", "expected": "FOUNDING"}
        self.assertIs(truth_for(question, "SKIPPED", None), UNMEASURED)

    def test_a_contains_question_scores_against_the_named_token(self):
        question = {"grade": "contains", "expected": "PREAPPROVAL_REQUESTED"}
        truth = truth_for(question, "MATCH", ["PACKET_INCOMPLETE", "PREAPPROVAL_REQUESTED"])
        self.assertEqual(judge(question, "PREAPPROVAL_REQUESTED", truth, None), "RIGHT")

    def test_a_participant_cannot_certify_its_own_prose(self):
        question = {"grade": "manual", "expected": "no"}
        self.assertEqual(judge(question, "banana", "no", None), "UNGRADED")
        self.assertEqual(judge(question, "banana", "no", "RIGHT"), "RIGHT")


class ScorecardRefusesAnUnrunGate(unittest.TestCase):
    """Every one of these printed ADMISSIBLE before it was fixed."""

    def test_an_absent_tier_zero_is_not_a_clean_tier_zero(self):
        _, admissible = scorecard([_row(3, "RIGHT")], "verdict", "RIGHT", "t")
        self.assertFalse(admissible)

    def test_abstaining_does_not_shrink_the_denominator(self):
        rows = [_row(0, "RIGHT", "a"), _row(1, "RIGHT", "b")]
        rows += [_row(1, "ABSTAIN", f"c{n}") for n in range(31)]
        rows += [_row(2, "RIGHT", "d")]
        _, admissible = scorecard(rows, "verdict", "RIGHT", "t")
        self.assertFalse(admissible)

    def test_an_unmeasured_tier_zero_question_blocks_admissible(self):
        rows = [_row(0, "RIGHT", "a"), _row(0, "UNGRADED", "b"),
                _row(1, "RIGHT", "c"), _row(2, "RIGHT", "d")]
        card, admissible = scorecard(rows, "verdict", "RIGHT", "t")
        self.assertFalse(admissible)
        self.assertIn("TIER 0 UNMEASURED", card)

    def test_a_fully_measured_clean_run_is_admissible(self):
        rows = [_row(0, "RIGHT", "a"), _row(1, "RIGHT", "b"), _row(2, "RIGHT", "c")]
        card, admissible = scorecard(rows, "verdict", "RIGHT", "t")
        self.assertTrue(admissible)
        self.assertIn("ADMISSIBLE", card)


class CorpusShape(unittest.TestCase):
    """Rules the corpus has to keep for the scorecard above to mean anything."""

    def test_ids_are_unique(self):
        ids = [q["id"] for q in CORPUS["questions"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_question_carries_a_tier_and_a_reason(self):
        for question in CORPUS["questions"]:
            self.assertIn(question.get("tier"), (0, 1, 2, 3), question["id"])
            self.assertTrue(question.get("why"), f"{question['id']} has no stated reason")

    def test_no_probe_searches_for_its_own_expected_value(self):
        """A pattern equal to its answer can report a sentence vanishing, never a rule changing."""
        for question in CORPUS["questions"]:
            probe = question.get("probe") or {}
            if probe.get("kind") != "regex_first" or "group" in probe:
                continue
            target = question.get("probe_expected", question["expected"])
            self.assertNotEqual(probe.get("pattern"), target,
                                f"{question['id']} probes for the string it expects")

    def test_tier_zero_is_not_diluted_by_weight_zero_questions(self):
        for question in CORPUS["questions"]:
            if question["tier"] == 0:
                self.assertEqual(question["weight"], 10, question["id"])


if __name__ == "__main__":
    unittest.main()
