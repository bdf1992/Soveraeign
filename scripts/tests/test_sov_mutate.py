"""Checks for the mutation scorer.

The scorer is an instrument that makes claims about other suites, so it is held
to the standard it enforces: every positive case here has a defeating twin that
proves the check would notice its own absence. A scorer that only ever reported
high numbers would pass a suite of positive cases and be worthless.
"""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import sov_mutate  # noqa: E402
from sovmutate import harness, operators, plan  # noqa: E402

ROOT = SCRIPTS.parent


ASSERTED = '''
def classify(value):
    if value > 10:
        return "high"
    return "low"
'''

PINNING_SUITE = '''
import unittest
import subject


class Pinned(unittest.TestCase):
    def test_boundary(self):
        self.assertEqual(subject.classify(11), "high")
        self.assertEqual(subject.classify(10), "low")
'''

VACUOUS_SUITE = '''
import unittest
import subject


class Vacuous(unittest.TestCase):
    def test_it_runs(self):
        subject.classify(11)
'''


def _score(source: str, suite: str) -> harness.Score:
    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp)
        subject = workspace / "subject.py"
        subject.write_text(source, encoding="utf-8", newline="\n")
        (workspace / "test_subject.py").write_text(suite, encoding="utf-8", newline="\n")
        command = (sys.executable, "-m", "unittest", "discover", "-s", ".", "-q")
        return harness.score_file(subject, workspace, command=command)


class OperatorMechanics(unittest.TestCase):
    def test_one_call_mutates_exactly_one_site(self):
        source = "a = 1 < 2\nb = 3 < 4\n"
        found = operators.sites(source)
        self.assertEqual(len(found), 6)
        mutated = operators.mutate(source, 0)
        self.assertIn("1 <= 2", mutated)
        self.assertIn("3 < 4", mutated)

    def test_mutation_is_deterministic(self):
        source = "def f(x):\n    return x > 5\n"
        self.assertEqual(operators.mutate(source, 0), operators.mutate(source, 0))

    def test_site_order_is_stable_across_calls(self):
        source = "def f(x):\n    return x > 5 and x < 10\n"
        first = [(s.line, s.operator, s.description) for s in operators.sites(source)]
        second = [(s.line, s.operator, s.description) for s in operators.sites(source)]
        self.assertEqual(first, second)

    def test_an_index_naming_no_site_is_refused_not_silently_ignored(self):
        source = "x = 1 < 2\n"
        with self.assertRaises(IndexError):
            operators.mutate(source, 99)

    def test_source_with_no_mutable_site_yields_none(self):
        self.assertEqual(operators.sites("import os\n"), [])


class ScorerDiscriminates(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pinning = _score(ASSERTED, PINNING_SUITE)
        cls.vacuous = _score(ASSERTED, VACUOUS_SUITE)

    def test_a_pinning_suite_kills_the_boundary_mutants(self):
        killed = [m for m in self.pinning.mutants if m.killed and m.site.operator == "compare"]
        self.assertTrue(killed)

    def test_a_vacuous_suite_scores_lower_than_a_pinning_one(self):
        self.assertLess(self.vacuous.percent, self.pinning.percent)

    def test_a_vacuous_suite_never_reports_a_perfect_score(self):
        self.assertLess(self.vacuous.percent, 100.0)

    def test_survivors_carry_the_line_that_is_unasserted(self):
        self.assertTrue(self.vacuous.survived)
        for mutant in self.vacuous.survived:
            self.assertGreater(mutant.site.line, 0)


class TreeIsRestored(unittest.TestCase):
    def test_the_subject_is_byte_identical_after_scoring(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            subject = workspace / "subject.py"
            subject.write_text(ASSERTED, encoding="utf-8", newline="\n")
            (workspace / "test_subject.py").write_text(PINNING_SUITE, encoding="utf-8", newline="\n")
            before = subject.read_bytes()
            command = (sys.executable, "-m", "unittest", "discover", "-s", ".", "-q")
            harness.score_file(subject, workspace, command=command)
            self.assertEqual(subject.read_bytes(), before)

    def test_a_file_admitting_no_mutants_scores_one_hundred_without_running_anything(self):
        score = harness.Score(target="none", command=("true",))
        self.assertEqual(score.generated, 0)
        self.assertEqual(score.percent, 100.0)


class SuiteRouting(unittest.TestCase):
    def test_conformance_routes_to_its_own_suite(self):
        command, _cwd = sov_mutate.suite_for(ROOT / "conformance" / "run.py")
        self.assertIn("conformance/tests", command)
        self.assertNotIn("scripts/tests", command)

    def test_scripts_route_to_the_tooling_suite(self):
        command, _cwd = sov_mutate.suite_for(ROOT / "scripts" / "sov_ticket.py")
        self.assertIn("scripts/tests", command)

    def test_clarity_routes_to_its_focused_suite(self):
        for target in (
            ROOT / "scripts" / "sov_clarity.py",
            ROOT / "scripts" / "sovclarity" / "scope.py",
        ):
            command, cwd = sov_mutate.suite_for(target)
            self.assertEqual(cwd, ROOT)
            self.assertIn("scripts.tests.test_sov_clarity", command)

    def test_custody_lifecycle_routes_to_its_focused_suite(self):
        command, cwd = sov_mutate.suite_for(ROOT / "scripts" / "sovcustody" / "lifecycle.py")
        self.assertEqual(cwd, ROOT)
        self.assertIn("scripts.tests.test_sov_custody_lifecycle", command)
        self.assertNotIn("discover", command)

    def test_asset_service_runs_from_its_own_root(self):
        command, cwd = sov_mutate.suite_for(
            ROOT / "services" / "asset" / "src" / "soveraeign_asset_service" / "core.py"
        )
        self.assertEqual(cwd, ROOT / "services" / "asset")
        self.assertIn("tests", command)

    def test_registry_service_routes_to_its_horizontal_defeating_suite(self):
        command, cwd = sov_mutate.suite_for(
            ROOT / "services" / "registry" / "src" /
            "soveraeign_registry_service" / "core.py"
        )
        self.assertEqual(cwd, ROOT)
        self.assertIn("scripts.tests.test_registry_horizontal", command)

    def test_host_service_routes_to_its_participant_suite(self):
        command, cwd = sov_mutate.suite_for(
            ROOT / "services" / "host" / "src" /
            "soveraeign_host_service" / "core.py"
        )
        self.assertEqual(cwd, ROOT / "services" / "host")
        self.assertIn("tests", command)

    def test_host_adapter_routes_to_the_host_participant_suite(self):
        command, cwd = sov_mutate.suite_for(ROOT / "adapters" / "host" / "local_host_adapter.py")
        self.assertEqual(cwd, ROOT / "services" / "host")
        self.assertIn("tests", command)

    def test_an_unclaimed_file_is_refused_rather_than_scored_zero(self):
        self.assertIsNone(sov_mutate.suite_for(ROOT / "adapters" / "github" / "export.py"))

    def test_a_path_outside_the_repository_is_refused(self):
        self.assertIsNone(sov_mutate.suite_for(Path(tempfile.gettempdir()) / "elsewhere.py"))


class MutationPlanning(unittest.TestCase):
    def test_a_target_plan_names_source_lines_sites_and_focused_suite(self):
        target = ROOT / "scripts" / "sov_clarity.py"
        lines = set(range(1, len(target.read_text(encoding="utf-8").splitlines()) + 1))
        manifest = plan.target(ROOT, target, lines)
        self.assertEqual(manifest["path"], "scripts/sov_clarity.py")
        self.assertTrue(manifest["source_digest"].startswith("sha256:"))
        self.assertEqual(manifest["suite"]["cwd"], ".")
        self.assertIn("scripts.tests.test_sov_clarity", manifest["suite"]["command"])
        self.assertTrue(manifest["mutable_sites"])

    def test_an_unclaimed_target_is_refused_before_execution(self):
        target = ROOT / "adapters" / "github" / "export.py"
        if target.exists():
            with self.assertRaisesRegex(plan.PlanError, "no mutation suite owns"):
                plan.target(ROOT, target, {1})


class WholeRunBudget(unittest.TestCase):
    def paths(self, count: int) -> list[Path]:
        return [Path(f"target-{index:02d}.py") for index in range(count)]

    def test_a_small_diff_keeps_every_file_and_honours_the_per_file_cap(self):
        planned, omitted = sov_mutate._budgeted_targets(self.paths(3), 4, 30)
        self.assertEqual(planned, [(path, 4) for path in self.paths(3)])
        self.assertEqual(omitted, [])

    def test_a_large_diff_is_sampled_across_its_full_ordered_extent(self):
        planned, omitted = sov_mutate._budgeted_targets(self.paths(10), 40, 3)
        self.assertEqual([path for path, _limit in planned],
                         [Path("target-00.py"), Path("target-04.py"), Path("target-09.py")])
        self.assertEqual([limit for _path, limit in planned], [1, 1, 1])
        self.assertEqual(len(omitted), 7)

    def test_the_declared_total_can_never_be_exceeded(self):
        for files in range(1, 20):
            for budget in range(1, 20):
                planned, _omitted = sov_mutate._budgeted_targets(self.paths(files), 40, budget)
                self.assertLessEqual(sum(limit for _path, limit in planned), budget)

    def test_no_whole_run_cap_preserves_the_previous_behavior(self):
        planned, omitted = sov_mutate._budgeted_targets(self.paths(5), 7, None)
        self.assertEqual(planned, [(path, 7) for path in self.paths(5)])
        self.assertEqual(omitted, [])

    def test_a_zero_budget_is_refused_instead_of_reporting_an_empty_pass(self):
        with self.assertRaisesRegex(ValueError, "total-limit"):
            sov_mutate._budgeted_targets(self.paths(5), 40, 0)


if __name__ == "__main__":
    unittest.main()
