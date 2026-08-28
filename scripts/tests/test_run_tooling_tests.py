"""Defeating cases for the repository tooling partition."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import run_tooling_tests  # noqa: E402


class ToolingPartition(unittest.TestCase):
    def test_every_discovered_module_is_assigned_exactly_once(self):
        modules = run_tooling_tests.test_modules()
        buckets = run_tooling_tests.partition(modules, 4)
        assigned = [module for bucket in buckets for module in bucket]
        self.assertEqual(sorted(assigned), list(modules))
        self.assertEqual(len(assigned), len(set(assigned)))

    def test_full_corpus_reader_gets_fewer_peers_than_default_modules(self):
        modules = tuple(Path(name) for name in (
            "test_sov_docs.py", "test_a.py", "test_b.py", "test_c.py", "test_d.py",
            "test_e.py", "test_f.py", "test_g.py", "test_h.py", "test_i.py", "test_j.py",
            "test_k.py", "test_l.py", "test_m.py", "test_n.py", "test_o.py",
        ))
        buckets = run_tooling_tests.partition(modules, 4)
        docs_bucket = next(bucket for bucket in buckets if Path("test_sov_docs.py") in bucket)
        self.assertLess(len(docs_bucket), max(len(bucket) for bucket in buckets))

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

    def peers(self, module: str) -> int:
        """How many modules share this module's shard of the real corpus."""
        modules = run_tooling_tests.test_modules()
        buckets = run_tooling_tests.partition(modules, run_tooling_tests.DEFAULT_WORKERS)
        return len(next(
            bucket for bucket in buckets
            if any(item.name == module for item in bucket)
        ))

    def test_a_module_with_no_declared_weight_counts_as_one(self):
        self.assertEqual(run_tooling_tests.module_weight(Path("test_a.py")), 1)
        self.assertGreater(run_tooling_tests.module_weight(Path("test_sov_branch.py")), 1)

    def test_the_declared_weight_buys_the_git_driving_module_fewer_peers(self):
        """Dropping the entry is the defeat: the weight has to change the packing.

        Asserting only that the two slow readers land in different shards proves
        nothing — longest-weight-first separates the first two modules whenever
        there are at least two workers, whatever their weights are. What the
        declared value buys is a shorter shard, so that is what is asserted.
        """
        weighted = self.peers("test_sov_branch.py")
        with self.weights(test_sov_branch__py=None):
            unweighted = self.peers("test_sov_branch.py")
        self.assertLess(weighted, unweighted)

    def test_a_weight_changes_placement_and_never_the_population(self):
        modules = run_tooling_tests.test_modules()
        heavy = run_tooling_tests.partition(modules, 4)
        with self.weights(test_sov_branch__py=None):
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


if __name__ == "__main__":
    unittest.main()
