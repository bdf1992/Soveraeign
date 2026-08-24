"""Positive and defeating cases for the F2 milestone gate reader.

The reader's claim is that it enumerates every normative predicate ``SPEC.md``
states and credits coverage only where the conformance corpus declares it in
machine-readable form. These cases defeat that claim: a predicate the corpus
never names, a case that names a predicate ``SPEC.md`` does not contain, a case
crediting one polarity as if it were both, and a suite bound to a single
participant.

BUILT evidence only. A gate reader witnesses nothing; it reports a distance.
"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_f2_gate  # noqa: E402


SPEC_FIXTURE = """
## Transition contract

| Transition | Preconditions | Commit | Refusal |
| --- | --- | --- | --- |
| `capture_source` | readable bytes | create immutable `Source` | `UNREADABLE` |
| `admit` | predicates pass | add `ADMITTED` event | `ADMISSION_REFUSED` |

## Requirement predicates

### PROD-I-1 · Propose

- Every accepted proposal has actor, cost, and `RECORDED` standing.
- Missing fields defeat admission.

### PROD-I-2 · Remember

- A source rereads byte-identical by digest.

## Interface parity

Human and model bindings may present different projections, but they must:

- discover the same legal operations and required inputs;
- lack direct authoritative storage writes.

## Conformance boundary

Every normative predicate above requires a positive and a defeating fixture.
"""


class Enumeration(unittest.TestCase):
    """SPEC.md is the only source of the predicate list."""

    def test_every_family_is_enumerated_from_the_specification(self) -> None:
        predicates = sov_f2_gate.normative_predicates(SPEC_FIXTURE)
        ids = [predicate["id"] for predicate in predicates]
        self.assertEqual(
            ids,
            ["PRED-I-1.1", "PRED-I-1.2", "PRED-I-2.1",
             "TRANS-capture_source", "TRANS-admit",
             "PARITY-1", "PARITY-2"],
        )

    def test_a_wrapped_bullet_stays_one_predicate(self) -> None:
        block = "### PROD-I-9 · Bring your own model\n\n- one claim that\n  wraps a line.\n"
        predicates = sov_f2_gate.requirement_predicates("## Requirement predicates\n" + block)
        self.assertEqual(len(predicates), 1)
        self.assertEqual(predicates[0]["text"], "one claim that wraps a line.")

    def test_the_live_specification_states_predicates_in_all_three_families(self) -> None:
        """The reader must not silently return an empty gate if SPEC.md moves."""
        report = sov_f2_gate.read_gate()
        for family in sov_f2_gate.FAMILY_ORDER:
            self.assertGreater(report["by_family"][family]["total"], 0, family)


class Coverage(unittest.TestCase):
    """Coverage is credited only where a case declares it."""

    def test_a_declared_pair_covers_its_predicate(self) -> None:
        cases = [
            {"id": "A", "polarity": "positive", "predicates": ["PRED-I-1.1"]},
            {"id": "B", "polarity": "defeating", "predicates": ["PRED-I-1.1"]},
        ]
        self.assertEqual(sov_f2_gate.declared_coverage(cases),
                         {"PRED-I-1.1": {"positive", "defeating"}})

    def test_a_case_that_declares_nothing_covers_nothing(self) -> None:
        """Defeating: the corpus is not credited for coverage it never claimed."""
        cases = [{"id": "A", "requirement": "PROD-I-1", "polarity": "positive"}]
        self.assertEqual(sov_f2_gate.declared_coverage(cases), {})

    def test_one_polarity_alone_does_not_close_a_predicate(self) -> None:
        """Defeating: a positive fixture without its defeat leaves the predicate open."""
        cases = [{"id": "A", "polarity": "positive", "predicates": ["PRED-I-1.1"]}]
        coverage = sov_f2_gate.declared_coverage(cases)
        self.assertEqual(sorted(sov_f2_gate.REQUIRED_POLARITIES - coverage["PRED-I-1.1"]),
                         ["defeating"])

    def test_a_participant_polarity_case_never_counts_as_a_fixture(self) -> None:
        """Defeating: participant runs observe an implementation, they are not controls."""
        cases = [{"id": "A", "polarity": "participant", "predicates": ["PRED-I-1.1"]}]
        self.assertEqual(sov_f2_gate.declared_coverage(cases), {})

    def test_a_predicate_absent_from_the_specification_is_a_defect(self) -> None:
        """Defeating: a corpus citing a retired predicate must not read as coverage."""
        predicates = sov_f2_gate.normative_predicates(SPEC_FIXTURE)
        coverage = {"PRED-I-1.1": {"positive"}, "PRED-I-4.9": {"positive", "defeating"}}
        self.assertEqual(sov_f2_gate.unknown_declarations(predicates, coverage), ["PRED-I-4.9"])


class GateVerdict(unittest.TestCase):
    """The gate is closed only when both F2 exit criteria hold."""

    def test_the_live_gate_is_open_and_says_why(self) -> None:
        report = sov_f2_gate.read_gate()
        self.assertFalse(report["closed"])
        self.assertEqual(report["predicates_open"] + report["predicates_covered"],
                         report["predicates_total"])

    def test_a_single_bound_participant_cannot_close_the_gate(self) -> None:
        """Defeating: F2 needs the suite bound to more than one implementation."""
        self.assertGreaterEqual(sov_f2_gate.REQUIRED_PARTICIPANTS, 2)
        report = sov_f2_gate.read_gate()
        if len(report["bound_participants"]) < sov_f2_gate.REQUIRED_PARTICIPANTS:
            self.assertFalse(report["bound_participants_ok"])
            self.assertFalse(report["closed"])

    def test_the_ranking_puts_requirement_predicates_first(self) -> None:
        report = sov_f2_gate.read_gate()
        ordered = sov_f2_gate.rank(report, 0)
        families = [row["family"] for row in ordered]
        self.assertEqual(families, sorted(families,
                                          key=sov_f2_gate.FAMILY_ORDER.index))


if __name__ == "__main__":
    unittest.main()
