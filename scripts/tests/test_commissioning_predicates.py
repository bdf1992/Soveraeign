"""Prove the P15-Q commissioning predicates join the custody root vocabulary.

Phase I closed `CLOSED_INCOMPLETE`; its first exit clause read that the gate
credited predicate-level identifiers while the join between the control
vocabulary and the predicate vocabulary was never made. `SPEC.md` writes the
twelve `P15-Q*` commissioning predicates literally, in backticks, under
"## Phase 1.5 commissioning predicates" - unlike the Phase-I families, which
`scripts/sov_f2_gate.py` synthesises from prose. This module proves the
deriver reads them correctly, that the Phase-I denominator does not move, and
that a PREDICATE custody root naming one of them resolves.
"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_f2_gate as gatemod  # noqa: E402
from sovcustody import roots as rootsmod  # noqa: E402

SPEC_TEXT = (ROOT / "SPEC.md").read_bytes().decode("utf-8")

#: The twelve identifiers SPEC.md states literally under the commissioning heading.
EXPECTED_IDS = {
    "P15-Q1.1", "P15-Q1.2", "P15-Q1.3",
    "P15-Q2.1", "P15-Q2.2", "P15-Q2.3", "P15-Q2.4",
    "P15-Q3.1", "P15-Q3.2",
    "P15-Q4.1", "P15-Q4.2", "P15-Q4.3",
}


class CommissioningPredicates(unittest.TestCase):
    def test_derives_exactly_twelve_identifiers(self) -> None:
        predicates = gatemod.commissioning_predicates(SPEC_TEXT)
        self.assertEqual(len(predicates), 12)

    def test_derived_ids_match_spec_literally(self) -> None:
        predicates = gatemod.commissioning_predicates(SPEC_TEXT)
        self.assertEqual({row["id"] for row in predicates}, EXPECTED_IDS)

    def test_normative_predicates_still_returns_forty_four(self) -> None:
        self.assertEqual(len(gatemod.normative_predicates(SPEC_TEXT)), 44)

    def test_normative_predicates_contains_no_p15_id(self) -> None:
        ids = {row["id"] for row in gatemod.normative_predicates(SPEC_TEXT)}
        self.assertFalse(any(pid.startswith("P15-Q") for pid in ids))


class PredicateRootResolution(unittest.TestCase):
    def test_a_commissioning_predicate_root_resolves(self) -> None:
        root = {"root_kind": "PREDICATE", "reference": "P15-Q1.1"}
        self.assertTrue(rootsmod.root_resolves(root))

    def test_an_unknown_predicate_root_does_not_resolve(self) -> None:
        root = {"root_kind": "PREDICATE", "reference": "P15-Q9.9"}
        self.assertFalse(rootsmod.root_resolves(root))


if __name__ == "__main__":
    unittest.main()
