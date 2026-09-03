"""Every refusal `contracts/phase-progress.json` declares, fired by a case.

A floor that cannot refuse is the defect this module exists to stop, so the
tests below drive the grader with mutated readings rather than asserting that
today's numbers are today's numbers. The one test that does read the live
repository asserts only the relation the contract states - reading at or above
floor, every gap declared - and not the value, so closing a gap does not fail it.
"""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import sov_f2_gate  # noqa: E402
import sov_phase_progress as progress  # noqa: E402


def contract() -> dict:
    return json.loads((ROOT / progress.CONTRACT).read_bytes().decode("utf-8"))


def reading() -> dict:
    return sov_f2_gate.read_gate()


def codes(defects: list[dict]) -> set[str]:
    return {defect["code"] for defect in defects}


class TheLiveReading(unittest.TestCase):
    """What the repository actually reads today, stated as a relation."""

    def test_the_reading_meets_its_floor_and_every_gap_is_declared(self):
        self.assertEqual([], progress.grade(reading(), contract()))

    def test_the_floor_is_reachable(self):
        report, declared = reading(), contract()
        self.assertLessEqual(declared["floor"]["total"], report["predicates_total"])

    def test_every_family_floor_names_a_family_the_gate_reads(self):
        report, declared = reading(), contract()
        self.assertEqual(set(declared["floor"]["by_family"]), set(report["by_family"]))


class Regression(unittest.TestCase):
    """A fall refuses, because a fall is attributable to the edit that caused it."""

    def test_a_total_below_the_floor_refuses(self):
        report = copy.deepcopy(reading())
        report["predicates_covered"] -= 1
        self.assertIn("PREDICATE_REGRESSION", codes(progress.grade(report, contract())))

    def test_a_family_below_its_floor_refuses_even_when_the_total_holds(self):
        report, declared = copy.deepcopy(reading()), contract()
        declared["floor"]["by_family"]["parity"] += 1
        defects = progress.grade(report, declared)
        self.assertIn("PREDICATE_REGRESSION", codes(defects))
        self.assertTrue(any("parity" in defect["detail"] for defect in defects))

    def test_the_total_holding_does_not_excuse_a_family_fall(self):
        """Coverage moving between families is not coverage staying still."""
        report, declared = copy.deepcopy(reading()), contract()
        declared["floor"]["by_family"]["transition"] += 2
        declared["floor"]["by_family"]["requirement"] -= 2
        self.assertIn("PREDICATE_REGRESSION", codes(progress.grade(report, declared)))


class UnknownAndUndeclared(unittest.TestCase):
    """An id the specification does not state is silently uncounted without this."""

    def test_an_orphan_declaration_refuses(self):
        report = copy.deepcopy(reading())
        report["orphan_declarations"] = ["PRED-I-99.9"]
        self.assertIn("UNKNOWN_PREDICATE", codes(progress.grade(report, contract())))

    def test_an_uncovered_predicate_nobody_excused_refuses(self):
        """Built synthetically: the live corpus covers PARITY-1, so the gap is planted."""
        report, declared = copy.deepcopy(reading()), contract()
        report["open"] = [row for row in report["open"] if row["id"] != "PARITY-1"]
        report["open"].append({"id": "PARITY-1", "family": "parity",
                               "missing": ["defeating", "positive"], "text": "discovery"})
        report["predicates_covered"] = report["predicates_total"] - len(report["open"])
        declared["uncovered_on_purpose"] = [
            entry for entry in declared["uncovered_on_purpose"]
            if entry["predicate"] != "PARITY-1"
        ]
        declared["floor"]["total"] = 0
        declared["floor"]["by_family"] = {}
        defects = progress.grade(report, declared)
        self.assertIn("UNDECLARED_UNCOVERED", codes(defects))
        self.assertTrue(any("PARITY-1" in defect["detail"] for defect in defects))

    def test_a_new_normative_predicate_cannot_arrive_uncounted(self):
        """SPEC.md gaining a predicate forces a decision about it, not silence."""
        report = copy.deepcopy(reading())
        report["open"].append({"id": "PRED-I-10.1", "family": "requirement",
                               "missing": ["defeating", "positive"], "text": "a new claim"})
        report["predicates_total"] += 1
        self.assertIn("UNDECLARED_UNCOVERED", codes(progress.grade(report, contract())))


class StaleExclusion(unittest.TestCase):
    """An exclusion that stopped being true keeps a closed gap looking open."""

    def test_excusing_a_predicate_that_is_now_covered_refuses(self):
        """Built synthetically: PARITY-1 is covered, so excusing it must read as stale."""
        report, declared = copy.deepcopy(reading()), contract()
        report["open"] = [row for row in report["open"] if row["id"] != "PARITY-1"]
        report["predicates_covered"] = report["predicates_total"] - len(report["open"])
        declared["uncovered_on_purpose"] = [
            entry for entry in declared["uncovered_on_purpose"]
            if entry["predicate"] != "PARITY-1"
        ] + [{"predicate": "PARITY-1", "why": "planted"}]
        defects = progress.grade(report, declared)
        self.assertIn("STALE_EXCLUSION", codes(defects))
        self.assertTrue(any("now covered" in defect["detail"] for defect in defects))

    def test_excusing_a_predicate_spec_does_not_state_refuses(self):
        report, declared = copy.deepcopy(reading()), contract()
        declared["uncovered_on_purpose"].append(
            {"predicate": "TRANS-imaginary", "why": "invented"})
        defects = progress.grade(report, declared)
        self.assertIn("STALE_EXCLUSION", codes(defects))
        self.assertTrue(any("does not state" in defect["detail"] for defect in defects))


class FloorAboveCeiling(unittest.TestCase):
    """A floor above the total would refuse every run forever."""

    def test_a_floor_above_the_total_refuses(self):
        report, declared = copy.deepcopy(reading()), contract()
        declared["floor"]["total"] = report["predicates_total"] + 1
        self.assertIn("FLOOR_ABOVE_CEILING", codes(progress.grade(report, declared)))


class TheStallDoesNotRefuse(unittest.TestCase):
    """decisions/0081: a reading nobody caused does not refuse whoever arrived next."""

    def test_the_contract_declares_the_stall_non_refusing(self):
        self.assertFalse(contract()["stall"]["refuses"])

    def test_a_stall_over_ceiling_adds_no_defect(self):
        declared = contract()
        declared["floor"]["set_at_commit"] = "0" * 40
        declared["stall"]["ceiling_commits"] = 0
        self.assertEqual([], progress.grade(reading(), declared))

    def test_an_unreachable_floor_commit_is_reported_not_raised(self):
        declared = contract()
        declared["floor"]["set_at_commit"] = "0" * 40
        drift = progress.stall(declared)
        self.assertFalse(drift["floor_commit_reachable"])
        self.assertIsNone(drift["commits_since_floor"])


class EveryDeclaredRefusalFires(unittest.TestCase):
    """The contract may not declare a refusal no case in this file reaches."""

    def test_the_declared_refusals_are_exactly_the_reachable_ones(self):
        declared = {refusal["code"] for refusal in contract()["refusals"]}
        reached = {"PREDICATE_REGRESSION", "UNKNOWN_PREDICATE", "UNDECLARED_UNCOVERED",
                   "STALE_EXCLUSION", "FLOOR_ABOVE_CEILING"}
        self.assertEqual(declared, reached)


class TheExclusionListIsHonest(unittest.TestCase):
    """Each excluded predicate is one SPEC.md states and the corpus does not cover."""

    def test_every_exclusion_names_a_predicate_spec_states(self):
        spec_text = sov_f2_gate._text(sov_f2_gate.SPEC)
        stated = {p["id"] for p in sov_f2_gate.normative_predicates(spec_text)}
        for entry in contract()["uncovered_on_purpose"]:
            self.assertIn(entry["predicate"], stated)

    def test_every_exclusion_carries_a_reason(self):
        for entry in contract()["uncovered_on_purpose"]:
            self.assertTrue(entry.get("why", "").strip(), entry["predicate"])

    def test_the_floor_plus_the_exclusions_account_for_every_predicate(self):
        report, declared = reading(), contract()
        self.assertEqual(declared["floor"]["total"] + len(declared["uncovered_on_purpose"]),
                         report["predicates_total"])


class TheCorpusDeclaresWhatItCovers(unittest.TestCase):
    """The join is the thing the floor rests on, so it is checked directly."""

    def test_every_control_declares_at_least_one_predicate(self):
        cases = json.loads(
            (ROOT / "conformance/oracle-controls.json").read_bytes().decode("utf-8"))
        undeclared = [case["id"] for case in cases if not case.get("predicates")]
        self.assertEqual([], undeclared)

    def test_no_control_declares_a_predicate_spec_does_not_state(self):
        spec_text = sov_f2_gate._text(sov_f2_gate.SPEC)
        stated = {p["id"] for p in sov_f2_gate.normative_predicates(spec_text)}
        cases = json.loads(
            (ROOT / "conformance/oracle-controls.json").read_bytes().decode("utf-8"))
        for case in cases:
            for predicate_id in case.get("predicates", []):
                self.assertIn(predicate_id, stated, f"{case['id']} declares {predicate_id}")

    def test_a_requirement_predicate_is_only_declared_by_its_own_requirement(self):
        """PRED-I-<n> belongs to PROD-I-<n>; a control may not claim its neighbour's."""
        cases = json.loads(
            (ROOT / "conformance/oracle-controls.json").read_bytes().decode("utf-8"))
        for case in cases:
            for predicate_id in case.get("predicates", []):
                if not predicate_id.startswith("PRED-I-"):
                    continue
                number = predicate_id.split("PRED-I-")[1].split(".")[0]
                self.assertEqual(f"PROD-I-{number}", case["requirement"],
                                 f"{case['id']} declares {predicate_id}")

    def test_both_polarities_exist_for_every_declared_predicate(self):
        """A predicate declared by only one polarity is not covered and must read so."""
        report = reading()
        cases = json.loads(
            (ROOT / "conformance/oracle-controls.json").read_bytes().decode("utf-8"))
        declared = sov_f2_gate.declared_coverage(cases)
        single = {name for name, polarities in declared.items() if len(polarities) < 2}
        self.assertEqual(single, {row["id"] for row in report["open"]} & single)


if __name__ == "__main__":
    unittest.main()
