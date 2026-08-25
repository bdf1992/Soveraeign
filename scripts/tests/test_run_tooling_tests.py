"""Defeating cases for the repository tooling partition."""

from __future__ import annotations

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
