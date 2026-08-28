"""Tests for attributing a verify failure to the change, the tree, or the host.

The dangerous direction here is only one: this must never turn a failure the
landing caused into a reading it can ignore. Most of these cases exist to hold
that line, and the ones that matter most are the ones asserting a refusal.

The permissive direction is the ruling being implemented: a landing must not be
refused because another session has unpushed work or because the host was loaded
enough to trip a ceiling. Those become recorded readings, never silence.
"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovland import isolation  # noqa: E402


def observation(subject, outcome, addresses):
    return {"subject": subject,
            "observed_state_addresses": list(addresses),
            "predicate_results": {"outcome": outcome}}


class Attribution(unittest.TestCase):

    def test_a_failing_check_the_landing_touched_refuses(self):
        """The line that must hold. A defect in the change is still a refusal."""
        rows = [observation("repository tooling tests", "FAIL",
                            ["scripts/tests", "scripts/run_tooling_tests.py"])]
        got = isolation.attribute(rows, 1, {"scripts/tests/test_landing_ledger.py"})
        self.assertEqual(got["verify"], "FAIL")
        self.assertEqual(got["attribution"], isolation.CHANGE)
        self.assertEqual(got["change_scoped"][0]["touched"],
                         ["scripts/tests/test_landing_ledger.py"])

    def test_a_failing_check_the_landing_never_touched_is_a_reading(self):
        """Another session's stale docs page is not this landing's defect."""
        rows = [observation("documentation reader", "FAIL",
                            ["docs/documentation.html", "scripts/sovdocs"])]
        got = isolation.attribute(rows, 1, {"scripts/sovland/ledger.py"})
        self.assertEqual(got["verify"], "PASS")
        self.assertEqual(got["attribution"], isolation.GLOBAL)
        self.assertEqual(len(got["readings"]), 1)

    def test_a_nonzero_run_with_every_check_passing_is_the_host(self):
        """A timing ceiling trips at the summary, not in any check. That is the machine."""
        rows = [observation("repository tooling tests", "PASS", ["scripts/tests"])]
        got = isolation.attribute(rows, 1, {"contracts/phases.json"})
        self.assertEqual(got["verify"], "PASS")
        self.assertEqual(got["attribution"], isolation.HOST)

    def test_one_touched_check_refuses_even_beside_many_untouched_ones(self):
        """A real defect is not diluted by however much unrelated noise is present."""
        rows = [observation("documentation reader", "FAIL", ["docs/documentation.html"]),
                observation("orientation snapshot", "FAIL", ["CLAUDE.md"]),
                observation("repository tooling tests", "FAIL", ["scripts/tests"])]
        got = isolation.attribute(rows, 1, {"scripts/tests/test_x.py"})
        self.assertEqual(got["verify"], "FAIL")
        self.assertEqual(got["attribution"], isolation.CHANGE)
        self.assertEqual(len(got["readings"]), 2)

    def test_a_passing_run_is_never_reattributed(self):
        rows = [observation("anything", "PASS", ["docs"])]
        got = isolation.attribute(rows, 0, set())
        self.assertEqual(got["verify"], "PASS")
        self.assertIsNone(got["attribution"])

    def test_readings_are_kept_not_dropped(self):
        """Nothing this stops blocking on may become invisible."""
        rows = [observation("strand", "FAIL", ["scripts/sov_strand.py"])]
        got = isolation.attribute(rows, 1, {"scripts/sovland/ledger.py"})
        self.assertEqual(got["readings"][0]["check"], "strand")
        self.assertIn("scripts/sov_strand.py", got["readings"][0]["addresses"])
        self.assertTrue(any("strand" in line for line in isolation.describe(got)))


class PathMatching(unittest.TestCase):

    def test_a_directory_address_covers_files_beneath_it(self):
        got = isolation.attribute(
            [observation("c", "FAIL", ["scripts/tests"])], 1, {"scripts/tests/a/b.py"})
        self.assertEqual(got["attribution"], isolation.CHANGE)

    def test_a_prefix_that_is_not_a_path_boundary_does_not_match(self):
        """`scripts/test` must not claim `scripts/tests/x.py`. A near-miss that
        matched would attribute an unrelated failure to the change and refuse it."""
        got = isolation.attribute(
            [observation("c", "FAIL", ["scripts/test"])], 1, {"scripts/tests/x.py"})
        self.assertEqual(got["attribution"], isolation.GLOBAL)

    def test_windows_separators_compare_equal_to_posix(self):
        """`verify.py` emits `docs\\surface.html` on this host and the grant speaks posix."""
        got = isolation.attribute(
            [observation("c", "FAIL", ["docs\\surface.html"])], 1, {"docs/surface.html"})
        self.assertEqual(got["attribution"], isolation.CHANGE)

    def test_an_exact_file_address_matches_itself(self):
        got = isolation.attribute(
            [observation("c", "FAIL", ["CLAUDE.md"])], 1, {"CLAUDE.md"})
        self.assertEqual(got["attribution"], isolation.CHANGE)


class FailsStrict(unittest.TestCase):
    """When attribution cannot be made, the gate must get stricter, never looser."""

    def test_no_observations_and_a_nonzero_exit_is_still_not_a_refusal_but_is_named(self):
        """Zero observations means verify never reported; HOST is the honest label,
        and `describe` says so out loud rather than printing a bare PASS."""
        got = isolation.attribute([], 1, {"scripts/x.py"})
        self.assertEqual(got["attribution"], isolation.HOST)
        self.assertTrue(any("ceiling on this host" in line
                            for line in isolation.describe(got)))

    def test_an_empty_path_set_attributes_nothing_to_the_change(self):
        """With no paths there is nothing to intersect; a failure cannot be blamed
        on the change, and the reading still survives."""
        got = isolation.attribute(
            [observation("c", "FAIL", ["scripts/tests"])], 1, set())
        self.assertEqual(got["attribution"], isolation.GLOBAL)
        self.assertEqual(len(got["readings"]), 1)


if __name__ == "__main__":
    unittest.main()
