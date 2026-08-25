"""Prove the closure-ownership table refuses what it declares it refuses.

``scripts/sov_closure.py selfcheck`` grades the declared corpus in
``conformance/fixtures/closure/handoff-cases.json``. This module proves the
half the corpus cannot: that the evaluator reads the contract as data rather
than restating it, that the declared order is the order refusals arrive in,
and that the boundaries the corpus states at one point hold on both sides.

Passing establishes ``BUILT`` for the table and its evaluator. It witnesses
nothing: no participant here carried a concern, and the table grants nothing.
"""

from __future__ import annotations

from pathlib import Path
import copy
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_closure  # noqa: E402

CONTRACT = json.loads((ROOT / "contracts" / "closure-ownership.json").read_text("utf-8"))
CORPUS = json.loads(
    (ROOT / "conformance" / "fixtures" / "closure" / "handoff-cases.json").read_text("utf-8"))


def case(case_id: str) -> dict:
    """Return a deep copy of one declared case's claim, ready to mutate."""
    for entry in CORPUS["cases"]:
        if entry["case_id"].startswith(case_id):
            return copy.deepcopy(entry["claim"])
    raise KeyError(case_id)


class DeclaredCorpus(unittest.TestCase):
    def test_every_case_is_judged_as_declared(self):
        self.assertEqual(sov_closure.selfcheck(), [])

    def test_every_refusal_code_has_a_rule(self):
        self.assertEqual(set(CONTRACT["refusals"]), set(sov_closure.RULES))

    def test_evaluation_order_covers_every_refusal_exactly_once(self):
        order = CONTRACT["evaluation_order"]
        self.assertEqual(len(order), len(set(order)))
        self.assertEqual(set(order), set(CONTRACT["refusals"]))


class ContractIsData(unittest.TestCase):
    """The evaluator must read the table, not a copy of it kept in code."""

    def test_a_new_routine_decision_is_refused_without_touching_the_evaluator(self):
        table = copy.deepcopy(CONTRACT)
        table["routine_decisions"].append("choosing which log level to use")
        claim = case("C-001")
        claim["asks"] = "choosing which log level to use"
        verdict = sov_closure.judge(claim, table)
        self.assertEqual(verdict["refusal"], "ROUTINE_DECISION")

    def test_raising_the_wip_ceiling_admits_what_it_refused(self):
        claim = case("C-101")
        self.assertEqual(sov_closure.judge(claim)["refusal"], "WIP_EXCEEDED")
        table = copy.deepcopy(CONTRACT)
        table["wip_policy"]["max_unlanded_concerns_per_participant"] = 2
        self.assertEqual(sov_closure.judge(claim, table)["verdict"], sov_closure.PERMITTED)

    def test_the_declared_order_decides_which_refusal_is_reported(self):
        claim = case("C-101")
        claim["seam"] = None
        self.assertEqual(sov_closure.judge(claim)["refusal"], "WIP_EXCEEDED")
        table = copy.deepcopy(CONTRACT)
        order = table["evaluation_order"]
        order.remove("SEAM_UNDECLARED")
        order.insert(0, "SEAM_UNDECLARED")
        self.assertEqual(sov_closure.judge(claim, table)["refusal"], "SEAM_UNDECLARED")


class Boundaries(unittest.TestCase):
    """Each rule is stated at one point in the corpus; prove the other side."""

    def test_absorption_needs_all_three_predicates(self):
        for crossed in CONTRACT["absorption_test"]["predicates"]:
            claim = case("C-102")
            claim["follow_on"][crossed] = False
            with self.subTest(crossed=crossed):
                self.assertEqual(sov_closure.judge(claim)["verdict"], sov_closure.PERMITTED)

    def test_a_reading_helper_may_be_offered_as_the_observation(self):
        claim = case("C-103")
        claim["helper"]["role"] = "reading"
        self.assertEqual(sov_closure.judge(claim)["verdict"], sov_closure.PERMITTED)

    def test_a_recruited_helper_closes_the_second_reading_gap(self):
        claim = case("C-110")
        claim["helper"] = {"recruited": True, "role": "editing", "offered_as_witness": False}
        self.assertEqual(sov_closure.judge(claim)["verdict"], sov_closure.PERMITTED)

    def test_a_participant_without_the_recruit_tool_is_not_refused_for_not_recruiting(self):
        claim = case("C-110")
        claim["tools_available"] = [t for t in claim["tools_available"] if t != "recruit_helper"]
        self.assertEqual(sov_closure.judge(claim)["verdict"], sov_closure.PERMITTED)

    def test_every_required_step_is_checked_not_only_the_first(self):
        for step in CONTRACT["loop"]:
            if not step["required"]:
                continue
            claim = case("C-001")
            claim["loop_steps_taken"] = [s for s in claim["loop_steps_taken"]
                                         if s != step["step"]]
            with self.subTest(step=step["step"]):
                verdict = sov_closure.judge(claim)
                self.assertEqual(verdict["refusal"], "LOOP_INCOMPLETE")
                self.assertIn(step["step"], verdict["because"])

    def test_judgement_is_refused_at_every_tier_that_is_not_the_owner(self):
        for tier in ("worker", "orchestrator", "controller"):
            claim = case("C-107")
            claim["requested_from"] = tier
            with self.subTest(tier=tier):
                self.assertEqual(sov_closure.judge(claim)["refusal"], "JUDGEMENT_NOT_OWNER")


class SeamTable(unittest.TestCase):
    def test_every_seam_can_be_asked_of_a_tier_that_can_serve_its_provision(self):
        for name, seam in CONTRACT["admissible_seams"].items():
            self.assertTrue(seam["provisions"], name)
            self.assertTrue(seam["requested_from"], name)
            if "judgement" in seam["provisions"]:
                self.assertIn("owner", seam["requested_from"], name)

    def test_each_seam_admits_at_least_one_shaped_handoff(self):
        for name, seam in CONTRACT["admissible_seams"].items():
            claim = case("C-001")
            claim["seam"] = name
            claim["provision"] = seam["provisions"][0]
            claim["requested_from"] = (
                "owner" if seam["provisions"][0] == "judgement" else seam["requested_from"][0])
            with self.subTest(seam=name):
                self.assertEqual(sov_closure.judge(claim)["verdict"], sov_closure.PERMITTED)


if __name__ == "__main__":
    unittest.main()
