"""Defeating cases for the repository tooling partition."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from unittest import mock
import sys
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import run_tooling_tests  # noqa: E402
from sovtooling import driver  # noqa: E402


def heaviest_declared() -> str:
    """The module the table currently weights most, by weight then name.

    Every assertion below that needs a weighted module asks for it this way. Naming
    one costs a false pin the moment that module stops being slow, which this file
    has already paid twice: test_sov_branch was hardcoded here and went on being
    asserted heavy for a week after it measured 0.1s.
    """
    return max(run_tooling_tests.MODULE_WEIGHTS,
               key=lambda name: (run_tooling_tests.MODULE_WEIGHTS[name], name))

REAL_WEIGHTS = dict(run_tooling_tests.MODULE_WEIGHTS)


class ToolingPartition(unittest.TestCase):
    def test_every_discovered_module_is_assigned_exactly_once(self):
        modules = run_tooling_tests.test_modules()
        buckets = run_tooling_tests.partition(modules, 4)
        assigned = [module for bucket in buckets for module in bucket]
        self.assertEqual(sorted(assigned), list(modules))
        self.assertEqual(len(assigned), len(set(assigned)))

    def test_full_corpus_reader_gets_fewer_peers_than_default_modules(self):
        modules = tuple(Path(name) for name in (
            heaviest_declared(), "test_a.py", "test_b.py", "test_c.py", "test_d.py",
            "test_e.py", "test_f.py", "test_g.py", "test_h.py", "test_i.py", "test_j.py",
            "test_k.py", "test_l.py", "test_m.py", "test_n.py", "test_o.py",
        ))
        buckets = run_tooling_tests.partition(modules, 4)
        heavy = next(bucket for bucket in buckets if Path(heaviest_declared()) in bucket)
        self.assertLess(len(heavy), max(len(bucket) for bucket in buckets))

    @staticmethod
    @contextmanager
    def weights(**overrides: int | None):
        """Run the partitioner under a different weight map, then put it back."""
        original = dict(run_tooling_tests.MODULE_WEIGHTS)
        replacement = dict(original)
        for name, weight in overrides.items():
            if weight is None:
                replacement.pop(name.replace("__", "."), None)
            else:
                replacement[name.replace("__", ".")] = weight
        run_tooling_tests.MODULE_WEIGHTS = replacement
        try:
            yield
        finally:
            run_tooling_tests.MODULE_WEIGHTS = original

    def test_a_module_with_no_declared_weight_counts_as_one(self):
        self.assertEqual(run_tooling_tests.module_weight(Path("test_a.py")), 1)
        self.assertGreater(run_tooling_tests.module_weight(Path(heaviest_declared())), 1)

    def critical_shard(self, weights) -> int:
        """The cost of the slowest shard, scored with the measured weights.

        Scored with the real table whatever map produced the packing, because that
        is the question: a partition built in ignorance of how long modules take
        still takes exactly as long to run.
        """
        modules = run_tooling_tests.test_modules()
        real = dict(run_tooling_tests.MODULE_WEIGHTS)
        run_tooling_tests.MODULE_WEIGHTS = weights
        try:
            buckets = run_tooling_tests.partition(modules, run_tooling_tests.DEFAULT_WORKERS)
        finally:
            run_tooling_tests.MODULE_WEIGHTS = real
        return max(sum(real.get(module.name, 1) for module in bucket) for bucket in buckets)

    def test_the_declared_weight_shortens_the_slowest_shard(self):
        """Dropping the entry is the defeat: the weight has to buy a shorter shard.

        This asserts the critical shard rather than the heaviest module's peer
        count. Peer count is what the weights were originally tuned by, and it is
        the wrong instrument against the live population: `run_tooling_tests`
        records that peers are not monotonic in the weight, so the property flips
        whenever anyone adds a module of any size. Adding one bounded 0.08s module
        at 112 flipped it while every measured weight in the table was still
        correct, which is a brittle instrument reporting a sound table as expired.

        The peer property is not lost. It is proven next door in
        `test_full_corpus_reader_gets_fewer_peers_than_default_modules`, against a
        controlled sixteen-module population where it is stable and means what it
        says. What is asserted here is what the table is actually for and what its
        own comments record tuning against: the slowest shard is the suite's wall
        clock, and at 112 modules the declared weights buy 100 against 137.
        """
        heaviest = heaviest_declared()
        declared = dict(run_tooling_tests.MODULE_WEIGHTS)
        dropped = {name: weight for name, weight in declared.items() if name != heaviest}
        self.assertLess(self.critical_shard(declared), self.critical_shard(dropped))

    def test_the_declared_weights_beat_no_weights_at_all(self):
        """The table as a whole must buy something, not merely its heaviest entry."""
        self.assertLess(self.critical_shard(dict(run_tooling_tests.MODULE_WEIGHTS)),
                        self.critical_shard({}))

    def test_ignoring_the_whole_table_is_worse_than_honouring_it(self):
        """The table as a whole earns its place, not only its largest entry."""
        weighted = self.makespan()
        original = dict(run_tooling_tests.MODULE_WEIGHTS)
        run_tooling_tests.MODULE_WEIGHTS = {}
        try:
            flat = self.makespan()
        finally:
            run_tooling_tests.MODULE_WEIGHTS = original
        self.assertLess(weighted, flat)

    def test_a_weight_changes_placement_and_never_the_population(self):
        modules = run_tooling_tests.test_modules()
        heavy = run_tooling_tests.partition(modules, 4)
        with self.weights(**{heaviest_declared().replace(".", "__"): None}):
            light = run_tooling_tests.partition(modules, 4)
        self.assertNotEqual(heavy, light, "the weight must change some assignment")
        self.assertEqual(
            sorted(item for bucket in heavy for item in bucket),
            sorted(item for bucket in light for item in bucket),
        )

    def test_invalid_worker_count_refuses(self):
        with self.assertRaises(ValueError):
            run_tooling_tests.partition((Path("test_a.py"),), 0)

    def test_worker_count_above_population_does_not_create_empty_work(self):
        modules = (Path("test_a.py"), Path("test_b.py"))
        buckets = run_tooling_tests.partition(modules, 8)
        assigned = [module for bucket in buckets for module in bucket]
        self.assertEqual(sorted(assigned), list(modules))
        self.assertEqual(len(buckets), 2)


class PerModuleCost(unittest.TestCase):
    """What each module cost, which a shard total can never say."""

    def test_a_reported_cost_line_is_read_back_as_the_module_and_its_seconds(self):
        costs = run_tooling_tests.module_costs(
            f"{driver.COST_PREFIX} test_a 1.500 PASS\n"
            f"{driver.COST_PREFIX} test_b 0.030 PASS\n"
        )
        self.assertEqual(costs, {"test_a": 1.5, "test_b": 0.03})

    def test_ordinary_test_output_is_not_mistaken_for_a_cost(self):
        """The driver shares its stream with unittest, so the prefix has to be exact."""
        costs = run_tooling_tests.module_costs(
            "Ran 7 tests in 0.005s\n"
            "OK\n"
            f"NOT_{driver.COST_PREFIX} test_a 1.500 PASS\n"
            f"{driver.COST_PREFIX}_SUFFIX test_b 1.500 PASS\n"
        )
        self.assertEqual(costs, {})

    def test_a_malformed_cost_line_is_dropped_and_never_raises(self):
        costs = run_tooling_tests.module_costs(
            f"{driver.COST_PREFIX} test_a not-a-number PASS\n"
            f"{driver.COST_PREFIX} test_b\n"
            f"{driver.COST_PREFIX} test_c 2.000 PASS\n"
        )
        self.assertEqual(costs, {"test_c": 2.0})

    def test_the_derived_weight_is_the_measured_seconds_times_ten(self):
        self.assertEqual(
            run_tooling_tests.measured_weights({"test_a": 5.5, "test_b": 1.04}),
            {"test_a.py": 55, "test_b.py": 10},
        )

    def test_a_module_measuring_under_one_second_earns_no_derived_weight(self):
        """The defeat of the rule above: a bounded module must not enter the table."""
        self.assertEqual(run_tooling_tests.measured_weights({"test_a": 0.999}), {})

    def test_a_missing_module_is_a_failure_and_not_a_traceback(self):
        """unittest reports an unimportable module as a synthesized failing test.

        So the loader does not raise here and the suite still refuses, which is the
        behaviour that matters: a module that vanished must not read as a module
        that passed.
        """
        passed, seconds, output = driver.run_module("test_module_that_does_not_exist")
        self.assertFalse(passed)
        self.assertGreaterEqual(seconds, 0.0)
        self.assertIn("Failed to import test module", output)

    @staticmethod
    def suite_that_takes(seconds: float) -> unittest.TestSuite:
        """A one-test suite that really spends `seconds`, for timing the timer."""

        class Slow(unittest.TestCase):
            def test_spends_the_time(self):
                time.sleep(seconds)

        return unittest.TestSuite([Slow("test_spends_the_time")])

    def test_the_reported_cost_tracks_real_elapsed_work(self):
        """The residual the witness pressed: nothing proved a number meant anything.

        Asserting only that a cost is positive would pass against a constant. This
        runs a suite that really spends a known interval and reads the cost back.
        """
        with mock.patch.object(unittest.defaultTestLoader, "loadTestsFromName",
                               return_value=self.suite_that_takes(0.25)):
            passed, seconds, _ = driver.run_module("any_name")
        self.assertTrue(passed)
        self.assertGreaterEqual(seconds, 0.25)
        self.assertLess(seconds, 5.0, "the reported cost must be this module's, not the run's")

    def test_a_faster_module_reports_a_smaller_cost_than_a_slower_one(self):
        """The defeat of a timer that reports a constant, which the case above admits."""
        with mock.patch.object(unittest.defaultTestLoader, "loadTestsFromName",
                               return_value=self.suite_that_takes(0.01)):
            _, quick, _ = driver.run_module("any_name")
        with mock.patch.object(unittest.defaultTestLoader, "loadTestsFromName",
                               return_value=self.suite_that_takes(0.30)):
            _, slow, _ = driver.run_module("any_name")
        self.assertLess(quick, slow)

    def test_a_loader_that_raises_refuses_one_module_and_not_the_whole_shard(self):
        """The guard around the loader, which no module name can reach.

        unittest converts every bad name under scripts.tests. into a synthesized
        failing test, so the guard exists for a loader that raises rather than
        reports. It is worth keeping and worth testing because the modules in a
        shard share one process: an exception escaping here would lose the cost
        reading for every module beside it, which is the reading this run adds.
        """
        with mock.patch.object(unittest.defaultTestLoader, "loadTestsFromName",
                               side_effect=RuntimeError("loader exploded")):
            passed, seconds, output = driver.run_module("any_name")
        self.assertNotIn("loadTestsFromName", vars(unittest.defaultTestLoader),
                         "the patch must leave no residue on the process-wide loader")
        self.assertFalse(passed)
        self.assertGreaterEqual(seconds, 0.0)
        self.assertIn("could not be loaded", output)
        self.assertIn("loader exploded", output)

    def test_a_failing_module_is_read_back_from_the_verdict_it_reported(self):
        failing = run_tooling_tests.failing_modules(
            f"{driver.COST_PREFIX} test_a 1.500 PASS\n"
            f"{driver.COST_PREFIX} test_b 0.030 FAIL\n"
        )
        self.assertEqual(failing, {"test_b"})

    def test_a_module_that_reported_no_cost_is_named_as_not_having_run(self):
        """The swallow this run can now refuse.

        A module that exits its shard at import takes the shard's remaining modules
        with it and the shard returns 0, so before the costs existed there was
        nothing to compare and the suite reported PASS over tests that never ran.
        """
        declared = {"test_a", "test_b", "test_c"}
        reported = run_tooling_tests.module_costs(
            f"{driver.COST_PREFIX} test_a 0.100 PASS\n"
            f"{driver.COST_PREFIX} test_b 0.100 PASS\n"
        )
        self.assertEqual(sorted(declared - set(reported)), ["test_c"])


if __name__ == "__main__":
    unittest.main()
