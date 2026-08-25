"""Cases for the observations the verification run emits.

`SPEC.md` says an observation must state how the observer avoids relying solely
on the executor's report. These cases prove every check declares that, that the
emitted records satisfy the contract, and that the run reports its own cost
honestly rather than hiding growth behind concurrency.
"""

from __future__ import annotations

from pathlib import Path
import json
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import verify  # noqa: E402
from sovschedule import jsonshape  # noqa: E402


SCHEMA = json.loads((verify.ROOT / "contracts" / "observation.schema.json")
                    .read_bytes().decode("utf-8"))


def _observation(check, exit_code=0):
    return verify.observe(check, "run_test", exit_code, 0.5, "2026-08-23T00:00:00+00:00")


class DeclaredRelations(unittest.TestCase):
    def test_every_check_declares_how_it_stays_independent(self):
        for check in verify.CHECKS:
            with self.subTest(check=check.name):
                self.assertTrue(check.relation.strip(),
                                f"{check.name} declares no observer_relation")

    def test_a_check_that_is_not_independent_says_so(self):
        """The participant's own tests must not imply independence they lack."""
        own = next(c for c in verify.CHECKS if c.name == "Asset Service reference tests")
        self.assertIn("NOT independent", own.relation)

    def test_every_check_names_what_it_observes(self):
        for check in verify.CHECKS:
            with self.subTest(check=check.name):
                self.assertTrue(check.observes, f"{check.name} names no observed address")

    def test_every_declared_address_exists(self):
        for check in verify.CHECKS:
            for address in check.observes:
                with self.subTest(address=address):
                    self.assertTrue((verify.ROOT / address).exists(), address)


class ContractConformance(unittest.TestCase):
    def test_each_emitted_observation_satisfies_the_contract(self):
        for check in verify.CHECKS:
            with self.subTest(check=check.name):
                self.assertEqual(jsonshape.check(_observation(check), SCHEMA, SCHEMA), [])

    def test_a_failing_check_still_emits_a_valid_observation(self):
        """Refusal is first class: a failed check is recorded, not dropped."""
        record = _observation(verify.CHECKS[0], exit_code=1)
        self.assertEqual(jsonshape.check(record, SCHEMA, SCHEMA), [])
        self.assertEqual(record["predicate_results"]["outcome"], "FAIL")

    def test_addresses_and_digests_stay_positionally_aligned(self):
        for check in verify.CHECKS:
            record = _observation(check)
            with self.subTest(check=check.name):
                self.assertEqual(len(record["observed_state_addresses"]),
                                 len(record["observed_state_digests"]))

    def test_observation_id_is_stable_for_one_run_and_subject(self):
        check = verify.CHECKS[0]
        self.assertEqual(_observation(check)["observation_id"],
                         _observation(check)["observation_id"])

    def test_two_subjects_in_one_run_do_not_share_an_identity(self):
        first, second = verify.CHECKS[0], verify.CHECKS[1]
        self.assertNotEqual(_observation(first)["observation_id"],
                            _observation(second)["observation_id"])


class Digests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_a_file_digest_tracks_its_bytes(self):
        target = verify.ROOT / "SPEC.md"
        before = verify.digest("SPEC.md")
        self.assertTrue(before.startswith("sha256:"))
        self.assertEqual(before, verify.digest("SPEC.md"))
        self.assertNotEqual(before, verify.digest("PRD.md"))
        self.assertTrue(target.exists())

    def test_a_directory_digest_covers_the_files_beneath_it(self):
        self.assertTrue(verify.digest("conformance/tests").startswith("sha256:"))

    def test_a_directory_and_a_file_do_not_collide(self):
        self.assertNotEqual(verify.digest("conformance/tests"), verify.digest("SPEC.md"))


class BudgetReporting(unittest.TestCase):
    """The budget is graded, so the report says how fast the run was and not
    only whether it cleared the ceiling (`decisions/0050`)."""

    def test_the_bands_are_the_ones_the_record_declares(self):
        """Guards the same thing the bare 3.0 assertion did: the budget cannot be
        loosened quietly. It pins the bands from decisions/0050 rather than a
        single number, so widening any one of them trips here and has to be argued.
        """
        self.assertEqual(verify.BUDGET_GRADES,
                         (("PLATINUM", 3.0), ("GOLD", 6.0), ("SILVER", 15.0)))

    def test_the_budget_is_still_declared(self):
        self.assertEqual(verify.BUDGET_SECONDS, 15.0)

    def test_the_slowest_band_ceiling_is_the_budget(self):
        """The two cannot drift apart: the budget is derived from the bands."""
        self.assertEqual(verify.BUDGET_GRADES[-1][1], verify.BUDGET_SECONDS)

    def test_bands_run_fastest_first_with_no_repeated_ceiling(self):
        ceilings = [ceiling for _, ceiling in verify.BUDGET_GRADES]
        self.assertEqual(ceilings, sorted(ceilings))
        self.assertEqual(len(set(ceilings)), len(ceilings))

    def test_a_ceiling_belongs_to_its_own_band(self):
        for name, ceiling in verify.BUDGET_GRADES:
            with self.subTest(band=name):
                self.assertEqual(verify.grade(ceiling), name)

    def test_a_hair_over_a_ceiling_drops_to_the_next_band(self):
        self.assertEqual(verify.grade(3.001), "GOLD")
        self.assertEqual(verify.grade(6.001), "SILVER")

    def test_past_the_last_ceiling_there_is_no_band(self):
        """The defeating case. Grading must not turn the budget into advice:
        over the slowest ceiling nothing is earned and the run still fails."""
        self.assertIsNone(verify.grade(verify.BUDGET_SECONDS + 0.001))
        self.assertIn("verification budget", verify.budget_line(15.001))

    def test_a_graded_run_is_told_what_the_next_band_costs(self):
        self.assertIn("PLATINUM needs 3.000s", verify.budget_line(4.0))

    def test_the_fastest_band_is_not_told_to_go_faster(self):
        self.assertNotIn("needs", verify.budget_line(1.0))

    def test_checks_are_unique_by_name(self):
        names = [check.name for check in verify.CHECKS]
        self.assertEqual(len(names), len(set(names)))


if __name__ == "__main__":
    unittest.main()
