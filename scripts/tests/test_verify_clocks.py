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
budgeted at roughly half a second inside a gate that grades the aggregate wall
time as debt and refuses only a single check past thirty seconds
(`decisions/0081`).
"""

from __future__ import annotations

from pathlib import Path
import ast
import os
import subprocess
import sys
import unittest
import unittest.mock

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


# Sized to the platform's clock, not to a round number. Windows job accounting
# quantizes to 15.625ms, so the burn has to clear several quanta to be readable;
# POSIX rusage is finer and its interpreter is slower per iteration, so the same
# count would cost this module three times as much on the runner that gates merges.
ITERATIONS = 3000000 if sys.platform == "win32" else 800000
BURN = reporting("x = 0\nfor i in range(%d):\n    x += i\n" % ITERATIONS)
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
    """Four children, measured once in setUpClass and asserted against many times."""

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
        """Two independent clocks on one process, so contention moves both alike.

        The bound is tight enough to defeat substitution: a run that reported the
        sleeper's wall time here would miss its self-report by the whole sleep.
        """
        for name, reading in (("sleeper", self.sleeper), ("burner", self.burner)):
            with self.subTest(child=name):
                self.assertLessEqual(abs(reading.cpu - self_reported(reading)), 0.12)

    def test_a_waiting_check_spends_wall_without_spending_cpu(self):
        """The defeating case for substitution: these two numbers cannot be one."""
        self.assertGreaterEqual(self.sleeper.wall, 0.15)
        self.assertLess(self.sleeper.cpu, self.sleeper.wall * 0.6)
        self.assertLess(self.sleeper.ratio, 0.6)

    def test_a_cpu_bound_check_spends_more_cpu_than_a_waiting_one(self):
        """Absolute CPU, not the ratio: an oversubscribed runner moves wall, not work.

        Ordered, not scaled by a factor. Windows job accounting quantizes to
        15.625 ms and both children carry one interpreter startup, so a `* 2`
        margin here was under two quanta wide and failed about one run in eight
        at 0.09375 against 0.09375. Substitution still fails the comparison: the
        waiting child's wall is the larger of the two.
        """
        self.assertGreater(self.burner.cpu, self.sleeper.cpu)

    def test_cpu_covers_work_the_check_did_in_a_grandchild(self):
        """`scripts/run_tooling_tests.py` spends nearly all its time in grandchildren.

        Take the parent's own CPU off the observed total. What is left has to be
        most of what the grandchild said it spent. A per-process measurement would
        leave nothing there, which is what makes this the defeating case.
        """
        parent, grandchild = cpu_reports(self.nested)
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

    def test_a_zero_wall_reading_still_reports_instead_of_raising(self):
        """A guard that only guards `.ratio` leaves `.report()` to raise, and
        `verify.py` calls it for every check after all of them have already run."""
        line = clocks.Reading(0, "", 0.0, 0.125, clocks.WINDOWS_SOURCE).report()
        self.assertEqual(line, "0.000s wall, 0.125s cpu")

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
            cpu, source = clocks._job_cpu(job, settle=0.0)
        finally:
            clocks._KERNEL32.CloseHandle(job)
        self.assertIsNone(cpu)
        self.assertEqual(source, "unmeasured:job-held-no-process")

    @unittest.skipUnless(sys.platform == "win32", "the Windows accounting call")
    def test_a_job_still_holding_a_live_process_reports_no_measurement(self):
        """A check can return while something it started keeps running.

        The job's total is then real but partial, and a partial total reads as a
        cheap check. Measured: a child that spawned a burner and exited accounted
        for 0.062s against the 0.422s its tree went on to spend.

        `settle=0` because this process is genuinely alive; the settle window
        exists for the millisecond of lag after a real check has already ended.
        """
        job = clocks._KERNEL32.CreateJobObjectW(None, None)
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        handle = clocks._KERNEL32.OpenProcess(clocks._ASSIGN_ACCESS, False, child.pid)
        try:
            self.assertTrue(clocks._KERNEL32.AssignProcessToJobObject(job, handle))
            cpu, source = clocks._job_cpu(job, settle=0.0)
        finally:
            child.kill()
            child.communicate()
            for open_handle in (handle, job):
                clocks._KERNEL32.CloseHandle(open_handle)
        self.assertIsNone(cpu)
        self.assertEqual(source, "unmeasured:job-tree-still-running")

    @unittest.skipUnless(sys.platform == "win32", "the Windows refusal table")
    def test_every_windows_refusal_labels_itself_unmeasured(self):
        for job, handle in ((0, 0), (1, 0), (1, 1)):
            with self.subTest(job=job, handle=handle):
                self.assertTrue(clocks._refusal(job, handle).startswith(clocks.UNMEASURED))

    @unittest.skipUnless(sys.platform == "win32", "the Windows assignment call")
    def test_an_assignment_refusal_carries_the_win32_error_that_caused_it(self):
        """`use_last_error` earns its place only if something reads the error."""
        self.assertRegex(clocks._refusal(1, 1),
                         r"^unmeasured:job-assignment-refused-win32-\d+$")


class Hygiene(unittest.TestCase):
    """What the observer leaves behind, on the ordinary path and on the interrupted one."""

    def open_descriptors(self):
        return len(os.listdir("/proc/self/fd"))

    @unittest.skipUnless(os.path.isdir("/proc/self/fd"), "descriptor count needs /proc")
    def test_the_posix_path_closes_its_pipes_when_the_read_is_interrupted(self):
        """Ctrl-C during a run interrupts eight of these at once. A pipe left open
        per check is what `subprocess.run` avoids by holding Popen as a context
        manager, and what this path avoided only on the path that did not raise."""
        before = self.open_descriptors()
        with unittest.mock.patch.object(clocks, "_drain", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                measure(SLEEP)
        self.assertEqual(self.open_descriptors(), before)

    @unittest.skipUnless(os.path.isdir("/proc/self/fd"), "descriptor count needs /proc")
    def test_an_ordinary_run_closes_its_pipes_too(self):
        before = self.open_descriptors()
        measure(ECHO)
        self.assertEqual(self.open_descriptors(), before)

    def test_output_larger_than_one_read_survives_the_drain(self):
        """The drain reads 64 KiB at a time; a check that writes more must not lose
        the remainder, and both streams must still arrive whole."""
        chatty = ("import sys\n"
                  "sys.stdout.write('o' * 200000)\n"
                  "sys.stderr.write('e' * 200000)\n")
        reading = measure(chatty)
        self.assertEqual(reading.output.count("o"), 200000)
        self.assertEqual(reading.output.count("e"), 200000)


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
