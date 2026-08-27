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
SETTLEMENT = json.loads((ROOT / "contracts" / "ticket-settlement.json").read_text("utf-8"))
ISSUE_SCHEMA = json.loads((ROOT / "contracts" / "issue-metadata.schema.json").read_text("utf-8"))
PR_TEMPLATE = (ROOT / ".github" / "pull_request_template.md").read_text("utf-8")


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


    def test_lowering_the_recruitment_ceiling_refuses_what_it_admitted(self):
        claim = case("C-009")
        self.assertEqual(sov_closure.judge(claim)["verdict"], sov_closure.PERMITTED)
        table = copy.deepcopy(CONTRACT)
        table["helper_policy"]["recruitment"]["per_concern_ceiling"] = 4
        verdict = sov_closure.judge(claim, table)
        self.assertEqual(verdict["refusal"], "RECRUITMENT_UNBOUNDED")


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

    def test_the_recruitment_ceiling_is_a_boundary_the_participant_may_reach(self):
        ceiling = CONTRACT["helper_policy"]["recruitment"]["per_concern_ceiling"]
        claim = case("C-112")
        self.assertEqual(sov_closure.judge(claim)["refusal"], "RECRUITMENT_UNBOUNDED")
        claim["helper"]["invocations"] = ceiling
        self.assertEqual(sov_closure.judge(claim)["verdict"], sov_closure.PERMITTED)

    def test_an_accepted_commitment_admits_a_spend_above_the_ceiling(self):
        claim = case("C-112")
        claim["helper"]["resource_commitment_accepted"] = True
        self.assertEqual(sov_closure.judge(claim)["verdict"], sov_closure.PERMITTED)

    def test_a_host_withheld_tool_asked_as_a_capability_is_admitted(self):
        claim = case("C-113")
        claim["seam"] = "DEPENDENCY_SEAM"
        claim["provision"] = "capability"
        claim["requested_from"] = "controller"
        self.assertEqual(sov_closure.judge(claim)["verdict"], sov_closure.PERMITTED)

    def test_a_tool_the_participant_simply_lacks_is_not_a_host_limit(self):
        claim = case("C-113")
        del claim["helper"]["blocked_by_host"]
        self.assertEqual(sov_closure.judge(claim)["verdict"], sov_closure.PERMITTED)

    def test_a_host_limited_participant_may_still_ask_the_owner_for_judgement(self):
        claim = case("C-113")
        claim["asks"] = "acceptance of the split Asset Service core"
        del claim["helper"]["capability_requested"]
        self.assertEqual(sov_closure.judge(claim)["verdict"], sov_closure.PERMITTED)

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


class SettlementPolicy(unittest.TestCase):
    """Settlement closes concerns; GitHub execution artifacts only carry them."""

    def test_only_satisfies_and_supersedes_are_terminal(self):
        terminal = {name for name, relation in SETTLEMENT["relations"].items()
                    if relation["terminal"]}
        self.assertEqual(terminal, {"satisfies", "supersedes"})
        self.assertFalse(SETTLEMENT["relations"]["advances"]["terminal"])

    def test_merge_and_green_are_not_terminal(self):
        terminal = SETTLEMENT["landed_terminal"]
        self.assertFalse(terminal["merge_is_terminal"])
        self.assertFalse(terminal["green_ci_is_terminal"])
        self.assertTrue(CONTRACT["present_or_land_terminal"]["merge_is_not_settlement"])

    def test_source_projection_reuses_existing_ticket_references(self):
        fields = set(ISSUE_SCHEMA["properties"])
        projected = set()
        for group in ("product_intent", "evidence", "governance", "coordination"):
            projected.update(SETTLEMENT["source_projection"][group]["ticket_fields"])
        self.assertLessEqual(projected, fields)
        self.assertTrue(SETTLEMENT["source_projection"]["no_duplicate_registry"])

    def test_pr_template_makes_advances_distinct_from_closes(self):
        self.assertIn("Relation: `advances` | `satisfies` | `supersedes`", PR_TEMPLATE)
        self.assertIn("`Closes #N` syntax only when Relation is `satisfies`", PR_TEMPLATE)

    def test_adoption_does_not_mint_retrofit_work(self):
        adoption = SETTLEMENT["adoption"]
        self.assertTrue(adoption["prospective"])
        self.assertTrue(adoption["historical_missing_source_is_not_a_defect_by_itself"])
        self.assertIn("Do not mint cleanup tickets", adoption["historical_rule"])


if __name__ == "__main__":
    unittest.main()
