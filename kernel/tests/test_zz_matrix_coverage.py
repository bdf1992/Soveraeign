"""Runs last: fail while a declared case is unexercised or a transition lacks its pair."""

from __future__ import annotations

import unittest

from support import COVERED, EXPECTED  # support puts kernel/src on sys.path

from soveraeign_kernel import KERNEL_TRANSITIONS, reasons  # noqa: E402


class MatrixCoverage(unittest.TestCase):
    def test_every_declared_case_was_exercised(self) -> None:
        missing = sorted(set(EXPECTED) - set(COVERED))
        self.assertEqual(missing, [], f"declared but unexercised: {missing}")

    def test_every_realized_transition_has_both_polarities(self) -> None:
        seen: dict[str, set[str]] = {name: set() for name in KERNEL_TRANSITIONS}
        for case_id in COVERED:
            case = EXPECTED[case_id]
            seen[case["transition"]].add(case["polarity"])
        gaps = sorted(name for name, polarities in seen.items()
                      if polarities != {"positive", "defeating"})
        self.assertEqual(gaps, [], f"transitions without a positive and defeating case: {gaps}")

    def test_every_declared_reason_code_has_a_case(self) -> None:
        declared = {case["expected"]["reason_code"] for case in EXPECTED.values()}
        unexercised = sorted(reasons.ALL - declared)
        self.assertEqual(unexercised, [], f"reason codes with no declared case: {unexercised}")
