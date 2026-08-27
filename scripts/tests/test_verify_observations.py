"""Cases for the observations the verification run emits.

`SPEC.md` says an observation must state how the observer avoids relying solely
on the executor's report. These cases prove every check declares that, that the
emitted records satisfy the contract, and that the run reports its own cost
honestly rather than hiding growth behind concurrency.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch
import json
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import verify  # noqa: E402
from sovschedule import jsonshape  # noqa: E402
from sovverify import clocks  # noqa: E402


SCHEMA = json.loads((verify.ROOT / "contracts" / "observation.schema.json")
                    .read_bytes().decode("utf-8"))


def _reading(exit_code=0, cpu=0.25, source=clocks.POSIX_SOURCE):
    """A constructed reading, so record shape is tested without spawning anything."""
    return clocks.Reading(exit_code, "", 0.5, cpu, source)


def _observation(check, exit_code=0, reading=None):
    return verify.observe(check, "run_test", reading or _reading(exit_code),
                          "2026-08-23T00:00:00+00:00")


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


class PersistedClocks(unittest.TestCase):
    """A per-check reading is only comparable against history if it is written down.

    `observe` is the record the run already emitted, so both clocks are carried in
    its `predicate_results` rather than in a second file with its own shape.
    """

    def test_a_record_carries_wall_cpu_ratio_and_how_cpu_was_taken(self):
        results = _observation(verify.CHECKS[0])["predicate_results"]
        self.assertEqual(results["elapsed_seconds"], 0.5)
        self.assertEqual(results["cpu_seconds"], 0.25)
        self.assertEqual(results["cpu_ratio"], 0.5)
        self.assertEqual(results["cpu_source"], clocks.POSIX_SOURCE)

    def test_the_clock_keys_are_typed_here_because_the_schema_does_not_type_them(self):
        """`predicate_results` is `additionalProperties: true` by design, so passing
        the contract says nothing about these four keys. Whoever adds a key owns its
        shape; that is this case. Widening the shared kernel schema to name one
        participant's predicates would be the wrong repair.
        """
        for reading in (_reading(), _reading(cpu=None, source=clocks.UNMEASURED + "x")):
            results = verify.observe(verify.CHECKS[0], "run_test", reading,
                                     "2026-08-23T00:00:00+00:00")["predicate_results"]
            with self.subTest(measured=reading.measured):
                self.assertIsInstance(results["elapsed_seconds"], float)
                self.assertIsInstance(results["cpu_source"], str)
                for key in ("cpu_seconds", "cpu_ratio"):
                    value = results[key]
                    self.assertTrue(value is None or isinstance(value, float), key)
                    self.assertEqual(value is None, not reading.measured)

    def test_an_unmeasured_cpu_is_recorded_as_null_and_never_as_the_wall_time(self):
        """The defeating case: a missing number must not read as a fast check."""
        unmeasured = _reading(cpu=None, source=clocks.UNMEASURED + "job-query-refused")
        results = _observation(verify.CHECKS[0], reading=unmeasured)["predicate_results"]
        self.assertIsNone(results["cpu_seconds"])
        self.assertIsNone(results["cpu_ratio"])
        self.assertNotEqual(results["cpu_seconds"], results["elapsed_seconds"])
        self.assertEqual(results["cpu_source"], "unmeasured:job-query-refused")

    def test_an_unmeasured_record_still_satisfies_the_contract(self):
        unmeasured = _reading(cpu=None, source=clocks.UNMEASURED + "no-per-child-accounting")
        record = _observation(verify.CHECKS[0], reading=unmeasured)
        self.assertEqual(jsonshape.check(record, SCHEMA, SCHEMA), [])

    def test_the_summary_reports_both_clocks_and_names_missing_ones(self):
        measured = [(check, _reading()) for check in verify.CHECKS[:2]]
        self.assertEqual(verify.cost_line(measured), "1.000s of check wall, 0.500s of check cpu")
        mixed = measured + [(verify.CHECKS[2], _reading(cpu=None, source=clocks.UNMEASURED + "x"))]
        self.assertIn("cpu unmeasured for 1 of 3", verify.cost_line(mixed))

    def test_a_failing_run_still_reports_both_clocks(self):
        """The defeating case for the old report, which stated cost only on PASS.

        A run that just failed is exactly the one whose operator needs to know
        whether the repository grew or the machine was busy.
        """
        results = [(check, _reading()) for check in verify.CHECKS[:2]]
        lines = verify.summary(results, 18.4, ["verification budget (18.400s > 15.000s)"])
        self.assertTrue(lines[0].startswith("FAIL: verification budget"))
        self.assertEqual(lines[1], "COST: 2 checks in 18.400s wall; "
                                   "1.000s of check wall, 0.500s of check cpu")

    def test_a_passing_run_keeps_its_grade_and_standing_note(self):
        results = [(check, _reading()) for check in verify.CHECKS[:2]]
        lines = verify.summary(results, 4.0, [])
        self.assertTrue(lines[0].startswith("PASS: 2 checks in 4.000s wall;"))
        self.assertEqual(lines[1], verify.budget_line(4.0))
        self.assertEqual(lines[2], verify.STANDING_NOTE)

    def test_a_run_with_no_cpu_at_all_prints_no_cpu_figure(self):
        """A summed 0.000s would read as a run that cost no compute."""
        none = [(check, _reading(cpu=None, source=clocks.UNMEASURED + "x"))
                for check in verify.CHECKS[:2]]
        self.assertEqual(verify.cost_line(none),
                         "1.000s of check wall, cpu unmeasured for all 2 checks")
        self.assertNotIn("0.000s of check cpu", verify.cost_line(none))

    def test_the_summary_never_calls_a_sum_of_wall_times_work(self):
        """What the old line did. Summed wall carries the same contention as wall."""
        self.assertNotIn("of work", verify.cost_line([(verify.CHECKS[0], _reading())]))


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


class DigestOverAnObservedAddress(unittest.TestCase):
    """`digest()` states the bytes an observation claims to cover.

    It is not a corpus walk. If a checkout of this repository ever sits under an
    observed address, the record would name bytes the digest never hashed and
    nothing would say so, which is why the prune is asserted here rather than
    left to the two walkers that own the same entry.
    """

    @staticmethod
    def _write(path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")

    def _tree(self, root: Path) -> None:
        """One observed address holding a file, and a copy of it inside a worktree."""
        self._write(root / "observed" / "real.txt", "evidence\n")
        self._write(root / "observed" / "worktrees" / "agent-x" / "real.txt", "evidence\n")
        self._write(root / "alone" / "real.txt", "evidence\n")

    def test_a_checkout_under_an_observed_address_is_not_hashed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._tree(root)
            with patch.object(verify, "ROOT", root):
                self.assertEqual(verify.digest("observed"), verify.digest("alone"))

    def test_without_the_prune_the_copy_enters_the_manifest(self) -> None:
        """The defeating case: drop the entry and the digest stops describing the address."""
        without = verify.SKIP_PARTS - {"worktrees"}
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._tree(root)
            with patch.object(verify, "ROOT", root):
                pruned = verify.digest("observed")
                with patch.object(verify, "SKIP_PARTS", without):
                    self.assertNotEqual(verify.digest("observed"), pruned)


if __name__ == "__main__":
    unittest.main()
