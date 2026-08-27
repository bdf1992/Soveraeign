"""Cases for the two clocks a verification check is measured on.

The claim under test is that the CPU number is a second measurement and not the
wall number wearing a different label. Each child here reports its own
`time.process_time()`, so the observed number is graded against a figure the
child computed for itself rather than against a threshold tuned to one machine.
That is also what makes these cases load-independent: both figures describe the
same process, so a busy host moves them together.

The defeating cases are the ones that matter. A run that printed wall time under
a CPU heading, or a zero where no measurement was taken, would read as a fast
check and be worse than reporting nothing at all.

These cases spawn real children, so they are kept small on purpose: the module is
budgeted at roughly half a second inside a gate that fails past fifteen
(`decisions/0050`).
"""

from __future__ import annotations

from pathlib import Path
import ast
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sovverify import clocks  # noqa: E402


ROOT = Path(__file__).resolve().parents[2]


def reporting(body: str) -> str:
    """Child source that runs `body` and then states its own CPU time.

    chr(10) rather than an escape keeps the child's source readable inside this
    module's source, where a doubled backslash would be the only other option.
    """
    return ("import subprocess, sys, time\n" + body
            + "sys.stdout.write('CPU=' + str(time.process_time()) + chr(10))\n")


BURN = reporting("x = 0\nfor i in range(2000000):\n    x += i\n")
SLEEP = reporting("time.sleep(0.15)\n")
NESTED = reporting("subprocess.run([sys.executable, '-c', " + repr(BURN) + "])\n")
ECHO = ("import os, sys\n"
        "sys.stdout.write(repr(sys.argv[1:]) + chr(10) + os.getcwd() + chr(10))\n"
        "sys.stderr.write('on stderr' + chr(10))\n"
        "sys.exit(3)\n")


def measure(code: str, *extra: str) -> clocks.Reading:
    return clocks.run([sys.executable, "-c", code, *extra], ROOT)


def cpu_reports(reading: clocks.Reading) -> list[float]:
    """Every CPU figure a process in the measured tree stated about itself, ascending.

    `time.process_time` excludes children, so a parent that only spawns and waits
    states a small number and the process doing the work states a large one.
    """
    return sorted(float(line.removeprefix("CPU="))
                  for line in reading.output.splitlines() if line.startswith("CPU="))


def self_reported(reading: clocks.Reading) -> float:
    """Sum every CPU figure the measured process tree stated about itself."""
    return sum(cpu_reports(reading))


class Measured(unittest.TestCase):
    """Five children, measured once, asserted against many times."""

    @classmethod
    def setUpClass(cls):
        cls.echo = measure(ECHO, "alpha", "beta")
        cls.sleeper = measure(SLEEP)
        cls.burner = measure(BURN)
        cls.nested = measure(NESTED)

    def test_the_host_uses_the_measurement_path_it_declares(self):
        """If a platform path stops working this fails loudly instead of degrading."""
        expected = clocks.WINDOWS_SOURCE if sys.platform == "win32" else clocks.POSIX_SOURCE
        for reading in (self.echo, self.sleeper, self.burner, self.nested):
            self.assertEqual(reading.cpu_source, expected)
            self.assertTrue(reading.measured)

    def test_the_observed_cpu_matches_what_the_child_measured_of_itself(self):
        """Two independent clocks on one process, so contention moves both alike."""
        for name, reading in (("sleeper", self.sleeper), ("burner", self.burner)):
            with self.subTest(child=name):
                stated = self_reported(reading)
                self.assertGreaterEqual(reading.cpu, stated - 0.05)
                self.assertLessEqual(reading.cpu, stated + 0.25)

    def test_a_waiting_check_spends_wall_without_spending_cpu(self):
        """The defeating case for substitution: these two numbers cannot be one."""
        self.assertGreaterEqual(self.sleeper.wall, 0.15)
        self.assertLess(self.sleeper.cpu, self.sleeper.wall * 0.6)
        self.assertLess(self.sleeper.ratio, 0.6)

    def test_a_cpu_bound_check_spends_more_cpu_than_a_waiting_one(self):
        """Absolute CPU, not the ratio: an oversubscribed runner moves wall, not work."""
        self.assertGreater(self.burner.cpu, self.sleeper.cpu * 2)

    def test_cpu_covers_work_the_check_did_in_a_grandchild(self):
        """`scripts/run_tooling_tests.py` spends nearly all its time in grandchildren.

        Take the parent's own CPU off the observed total. What is left has to be
        most of what the grandchild said it spent. A per-process measurement would
        leave nothing there, which is what makes this the defeating case.
        """
        parent, grandchild = cpu_reports(self.nested)
        self.assertGreater(grandchild, parent)
        self.assertGreaterEqual(self.nested.cpu - parent, grandchild * 0.7)
        self.assertGreaterEqual(self.nested.cpu, (parent + grandchild) * 0.8)

    def test_argv_and_working_directory_reach_the_child_unaltered(self):
        """The harness must not perturb what it measures: no shim, no rewritten argv."""
        argv, cwd = self.echo.output.splitlines()[:2]
        self.assertEqual(ast.literal_eval(argv), ["alpha", "beta"])
        self.assertEqual(Path(cwd).resolve(), ROOT.resolve())

    def test_both_streams_are_captured_and_the_exit_code_is_the_child_s(self):
        self.assertEqual(self.echo.exit_code, 3)
        self.assertIn("on stderr", self.echo.output)

    def test_captured_output_carries_no_carriage_returns(self):
        """Universal-newline translation, which text mode used to do for this."""
        self.assertNotIn("\r", self.echo.output)


class Degraded(unittest.TestCase):
    """What a reading says when no CPU number could be taken."""

    def unmeasured(self, reason="job-query-refused", wall=1.25):
        return clocks.Reading(0, "", wall, None, clocks.UNMEASURED + reason)

    def test_an_unmeasured_reading_offers_no_ratio(self):
        self.assertIsNone(self.unmeasured().ratio)
        self.assertFalse(self.unmeasured().measured)

    def test_an_unmeasured_report_says_so_and_never_prints_wall_as_cpu(self):
        line = self.unmeasured().report()
        self.assertIn("cpu unmeasured (job-query-refused)", line)
        self.assertNotIn("1.250s cpu", line)

    def test_a_measured_report_states_both_clocks_and_the_ratio(self):
        line = clocks.Reading(0, "", 2.0, 1.0, clocks.POSIX_SOURCE).report()
        self.assertEqual(line, "2.000s wall, 1.000s cpu (0.50x)")

    def test_a_zero_wall_reading_offers_no_ratio_rather_than_dividing(self):
        self.assertIsNone(clocks.Reading(0, "", 0.0, 0.0, clocks.POSIX_SOURCE).ratio)

    def test_measured_is_exactly_whether_a_cpu_number_exists(self):
        for source in (clocks.WINDOWS_SOURCE, clocks.POSIX_SOURCE):
            self.assertTrue(clocks.Reading(0, "", 1.0, 0.1, source).measured)
        self.assertFalse(self.unmeasured().measured)

    def test_running_unmeasured_still_runs_the_command_and_admits_no_cpu(self):
        reading = clocks.run_unmeasured([sys.executable, "-c", "print(7)"], ROOT, "no-clock")
        self.assertEqual(reading.exit_code, 0)
        self.assertIn("7", reading.output)
        self.assertIsNone(reading.cpu)
        self.assertEqual(reading.cpu_source, "unmeasured:no-clock")

    @unittest.skipUnless(sys.platform == "win32", "the Windows accounting call")
    def test_an_empty_job_reports_no_measurement_rather_than_zero(self):
        """The sharpest version of the hazard: real accounting, no process in it.

        A job that never held the child accounts for 0.000s, which would print as
        an instant check. Measured separately: assigning an already-exited process
        fails with ERROR_ACCESS_DENIED, so this is the second guard, not the first.
        """
        job = clocks._KERNEL32.CreateJobObjectW(None, None)
        try:
            cpu, source = clocks._job_cpu(job)
        finally:
            clocks._KERNEL32.CloseHandle(job)
        self.assertIsNone(cpu)
        self.assertEqual(source, "unmeasured:job-held-no-process")

    @unittest.skipUnless(sys.platform == "win32", "the Windows refusal table")
    def test_every_windows_refusal_labels_itself_unmeasured(self):
        for job, handle in ((0, 0), (1, 0), (1, 1)):
            with self.subTest(job=job, handle=handle):
                self.assertTrue(clocks._refusal(job, handle).startswith(clocks.UNMEASURED))


class Provenance(unittest.TestCase):
    def test_the_windows_path_never_reaches_into_a_popen_private(self):
        """The process handle is opened by pid, which is public API. Held by a case
        so the choice cannot be quietly reversed to `Popen._handle`."""
        tree = ast.parse(Path(clocks.__file__).read_bytes().decode("utf-8"))
        attributes = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        self.assertNotIn("_handle", attributes)

    def test_the_two_measured_sources_are_distinct_and_not_refusals(self):
        self.assertNotEqual(clocks.WINDOWS_SOURCE, clocks.POSIX_SOURCE)
        for source in (clocks.WINDOWS_SOURCE, clocks.POSIX_SOURCE):
            self.assertFalse(source.startswith(clocks.UNMEASURED))


if __name__ == "__main__":
    unittest.main()
