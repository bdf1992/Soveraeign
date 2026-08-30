"""Clarity coverage is a live repository claim, not a decorative percentage."""

from __future__ import annotations

import unittest

from scripts import sov_clarity


class ClarityCoverageTests(unittest.TestCase):
    def test_recorded_reviews_are_well_formed_and_current(self) -> None:
        contract = sov_clarity.load(sov_clarity.CONTRACT_PATH)
        record = sov_clarity.coverage(contract)

        self.assertEqual([], sov_clarity.registry_errors(contract, record))
        stale = {
            path: state
            for path, state in sov_clarity.state_map(contract, record).items()
            if state in {"TEXT_STALE", "BASIS_STALE"}
        }
        self.assertEqual({}, stale)

    def test_unchecked_files_do_not_fake_failure_or_coverage(self) -> None:
        contract = sov_clarity.load(sov_clarity.CONTRACT_PATH)
        record = {
            "schema": "soveraeign-clarity-coverage/v1",
            "skill": contract["skill"],
            "reviews": {},
        }

        self.assertEqual([], sov_clarity.registry_errors(contract, record))
        states = sov_clarity.state_map(contract, record)
        self.assertTrue(states)
        self.assertEqual({"UNCHECKED"}, set(states.values()))


if __name__ == "__main__":
    unittest.main()
