"""Cases for the reader over retained verification records.

`scripts/sov_observations.py` is the first thing in the repository that opens a
record `verify.py --observe` wrote. Five independent witnesses named the same
residual on the change that started retaining them - nothing read the artifacts -
so these cases hold the reader to saying only what a record carries.

The case that matters most is `test_a_check_that_got_faster_is_not_read_as_slower`.
The first version of `moved` compared absolute difference, so a check that ran in a
third of the time printed "waited longer for the same work". That was found by
running the reader against two real runs, not by rereading it, and a confidently
wrong reading is the exact failure this whole line of work exists against.
"""

from __future__ import annotations

from contextlib import redirect_stdout
from pathlib import Path
import io
import json
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import sov_observations as reader  # noqa: E402


def record(subject="a check", run="run_one", outcome="PASS", wall=1.0, cpu=1.0,
           addresses=("AGENTS.md",), digests=("sha256:aa",)):
    """One observation record shaped like the ones `verify.py` emits."""
    return {
        "observation_id": f"observation_{subject}",
        "run_id": run,
        "observer_id": "scripts/verify.py@test",
        "observer_relation": "constructed for this case",
        "observed_state_addresses": list(addresses),
        "observed_state_digests": list(digests),
        "predicate_results": {"outcome": outcome, "exit_code": 0 if outcome == "PASS" else 1,
                              "elapsed_seconds": wall, "cpu_seconds": cpu},
        "observed_at": "2026-09-08T00:00:00+00:00",
        "subject": subject,
    }


def written(rows):
    """`rows` on disk, for the cases that go through `load`."""
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(rows, handle)
    handle.close()
    return Path(handle.name)


class LoadRefusesWhatIsNotOneRun(unittest.TestCase):
    """A file half-understood and summarised anyway is the failure to avoid."""

    def refusal(self, payload):
        with self.assertRaises(reader.Refusal) as caught:
            reader.load(written(payload))
        return str(caught.exception).split(" ", 1)[0]

    def test_a_run_of_records_loads(self):
        rows = reader.load(written([record()]))
        self.assertEqual(["a check"], [row["subject"] for row in rows])

    def test_a_mapping_is_not_a_run(self):
        self.assertEqual("NOT_A_RUN", self.refusal({"subject": "a check"}))

    def test_an_empty_file_is_refused_rather_than_read_as_a_clean_run(self):
        self.assertEqual("EMPTY_RUN", self.refusal([]))

    def test_a_record_missing_a_required_key_is_refused(self):
        for key in reader.REQUIRED:
            broken = record()
            del broken[key]
            with self.subTest(missing=key):
                self.assertEqual("NOT_A_RUN", self.refusal([broken]))

    def test_two_runs_in_one_file_are_refused(self):
        self.assertEqual("MIXED_RUNS",
                         self.refusal([record(run="run_one"), record(run="run_two")]))

    def test_a_file_that_is_not_json_is_refused(self):
        handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        handle.write("not json")
        handle.close()
        with self.assertRaises(reader.Refusal) as caught:
            reader.load(Path(handle.name))
        self.assertTrue(str(caught.exception).startswith("UNREADABLE"))

    def test_a_path_that_does_not_exist_is_refused(self):
        with self.assertRaises(reader.Refusal) as caught:
            reader.load(Path("no/such/observations.json"))
        self.assertTrue(str(caught.exception).startswith("UNREADABLE"))


class CostIsReadWithItsDirection(unittest.TestCase):
    def test_a_check_that_got_faster_is_not_read_as_slower(self):
        """The defeating case for the bug two real runs surfaced."""
        self.assertEqual("faster", reader.moved(3.0, 0.5))
        self.assertEqual("slower", reader.moved(0.5, 3.0))

    def test_a_small_change_is_jitter_on_any_host(self):
        self.assertEqual("", reader.moved(1.0, 1.2))

    def test_a_large_absolute_change_that_is_a_small_ratio_is_not_a_reading(self):
        self.assertEqual("", reader.moved(100.0, 120.0))

    def test_an_unmeasured_clock_yields_no_reading_rather_than_a_guess(self):
        self.assertEqual("", reader.moved(None, 3.0))
        self.assertEqual("", reader.moved(3.0, None))


class CompareAttributesWhatTheRecordsCarry(unittest.TestCase):
    def test_two_readings_of_one_run_are_refused(self):
        rows = [record(run="run_one")]
        with self.assertRaises(reader.Refusal) as caught:
            reader.compare(rows, rows)
        self.assertTrue(str(caught.exception).startswith("SAME_RUN"))

    def test_an_outcome_change_is_named_with_both_sides(self):
        found = reader.compare([record(run="a")], [record(run="b", outcome="FAIL")])
        self.assertEqual([{"subject": "a check", "was": "PASS", "now": "FAIL"}],
                         found["outcome_changed"])

    def test_changed_digests_read_as_the_repository_moving(self):
        found = reader.compare([record(run="a")],
                               [record(run="b", digests=("sha256:bb",))])
        self.assertEqual(["a check"], found["content_changed"])

    def test_content_that_moved_is_not_also_read_as_a_cost_change(self):
        """The repository changing under a check explains its cost; reporting both
        would invite a reader to treat one cause as two."""
        found = reader.compare([record(run="a", cpu=1.0, wall=1.0)],
                               [record(run="b", cpu=9.0, wall=9.0, digests=("sha256:bb",))])
        self.assertEqual(["a check"], found["content_changed"])
        self.assertEqual([], found["cost_changed_same_content"])
        self.assertEqual([], found["waited_longer_same_work"])

    def test_identical_bytes_costing_more_cpu_read_as_more_work(self):
        found = reader.compare([record(run="a", cpu=1.0, wall=1.0)],
                               [record(run="b", cpu=9.0, wall=9.0)])
        self.assertEqual(["a check"], [e["subject"] for e in found["cost_changed_same_content"]])
        self.assertEqual("slower", found["cost_changed_same_content"][0]["direction"])

    def test_identical_bytes_and_cpu_with_a_longer_wall_read_as_the_host(self):
        found = reader.compare([record(run="a", cpu=1.0, wall=1.0)],
                               [record(run="b", cpu=1.0, wall=9.0)])
        self.assertEqual([], found["cost_changed_same_content"])
        self.assertEqual(["a check"], [e["subject"] for e in found["waited_longer_same_work"]])

    def test_checks_added_and_removed_are_named(self):
        found = reader.compare([record(run="a", subject="was here")],
                               [record(run="b", subject="is here")])
        self.assertEqual(["is here"], found["checks_added"])
        self.assertEqual(["was here"], found["checks_removed"])

    def test_two_identical_runs_report_nothing_changed(self):
        lines = reader.compare_lines(reader.compare([record(run="a")], [record(run="b")]))
        self.assertEqual(2, len(lines))
        self.assertIn("no check changed", lines[1])


class SummaryNamesWhatFailedAndWhatItRead(unittest.TestCase):
    def test_a_failing_check_is_named_with_the_addresses_it_declared(self):
        found = reader.summarise([record(), record(subject="broken", outcome="FAIL")])
        self.assertEqual(2, found["checks"])
        self.assertEqual(["broken"], [entry["subject"] for entry in found["failed"]])
        self.assertEqual(["AGENTS.md"], found["failed"][0]["addresses"])

    def test_a_host_with_no_cpu_clock_is_reported_rather_than_read_as_free(self):
        found = reader.summarise([record(cpu=None)])
        self.assertEqual(["a check"], found["unmeasured_cpu"])
        self.assertIn("wall time only", "\n".join(reader.read_lines(found)))


class TheCommandLineSurface(unittest.TestCase):
    """Stdout is captured: these cases run inside `verify.py`, where a report
    printed by a passing test is noise a reader has to learn to ignore."""

    def run_it(self, argv):
        spoken = io.StringIO()
        with redirect_stdout(spoken):
            code = reader.main(argv)
        return code, spoken.getvalue()

    def test_a_refused_file_exits_two_and_says_nothing_on_stdout(self):
        code, spoken = self.run_it(["read", "no/such/file.json"])
        self.assertEqual(2, code)
        self.assertEqual("", spoken)

    def test_reading_a_run_exits_zero_and_prints_the_record_as_json(self):
        code, spoken = self.run_it(["--json", "read", str(written([record()]))])
        self.assertEqual(0, code)
        self.assertEqual("run_one", json.loads(spoken)["run_id"])

    def test_comparing_two_runs_exits_zero_and_names_both(self):
        before, after = written([record(run="a")]), written([record(run="b")])
        code, spoken = self.run_it(["compare", str(before), str(after)])
        self.assertEqual(0, code)
        self.assertIn("a -> b", spoken)


if __name__ == "__main__":
    unittest.main()
