"""Two clocks for one subprocess: wall time, and the CPU the tree it waits for spent.

One aggregate wall time cannot say whether a slow verification run means the
repository grew or the machine was busy. Wall time answers how long the operator
waited; CPU time answers how much CPU the machine spent on this check. A check
whose wall rose while its CPU held was waiting, which is the reading the old
single number could not give.

What CPU time is not is a stable measure of the work a check asks for. Measured
on a 32-core host, saturating it inflated a fixed-work child's wall by 2.19x and
its own CPU by 2.12x: competing for cores, cache and turbo headroom buys real
cycles for identical bytes. The CPU-bound checks are where that bites hardest,
and they are exactly the ones a compute figure would otherwise describe best.
Read a rise in CPU as either more work or more competition, never as proof of the
first. `decisions/0071` carries the measurements and proposes nothing in force.

Both numbers are taken from the observing side. The command, its argv, its
working directory and its pipes are what `subprocess` would have used anyway, so
nothing here perturbs the thing it measures, and nothing here reads a check's own
claim about its cost.

The CPU number covers the process tree a check waits for. Measuring only the
direct child would understate the most expensive check in the suite:
`scripts/run_tooling_tests.py` spends nearly all its time in four grandchildren,
and a direct-child reading of it on Windows was 0.031s against 0.203s for the
tree. A descendant the check does not wait for is a different matter: on Windows
the job still holds it, so a reading is refused as unmeasured when the job has
not gone quiet shortly after the check returned; on POSIX `wait4` simply never
sees it and the reading is short by that much. Every check in the current table
waits for its children.

Resolution differs by platform and the printed three decimals do not: Windows job
accounting quantizes to 15.625ms, so a check reading 0.047s spent somewhere
between two and four quanta. Aggregates are sound; a single small per-check
figure is coarse.

- Windows: the child is assigned to a fresh job object and the job's
  `TotalUserTime + TotalKernelTime` is read after it exits. Job accounting counts
  processes that have already terminated, so descendants are included. Nothing
  here touches `Popen._handle`; the handle is opened by pid, which is public.
- POSIX: `os.wait4` returns the exact rusage of one child, which on Linux carries
  the usage of descendants that child waited for. Per-child attribution is what
  `resource.getrusage(RUSAGE_CHILDREN)` cannot give while checks run in parallel,
  because that call is cumulative and process-wide.

When a path cannot produce a number, `cpu` is `None` and `cpu_source` names why.
Wall time is never substituted for it.
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple
import locale
import os
import selectors
import subprocess
import sys
import time


#: How the CPU number was obtained. A reading whose source starts with UNMEASURED
#: carries no CPU number at all, which is the only honest degraded state.
WINDOWS_SOURCE = "windows-job-accounting"
POSIX_SOURCE = "posix-wait4-rusage"
UNMEASURED = "unmeasured:"

_ENCODING = locale.getpreferredencoding(False)


class Reading(NamedTuple):
    """What one command cost: how long the operator waited, what the machine spent."""

    exit_code: int
    output: str
    wall: float
    cpu: float | None
    cpu_source: str

    @property
    def measured(self) -> bool:
        """True when a real CPU number was obtained for this command."""
        return self.cpu is not None

    @property
    def ratio(self) -> float | None:
        """CPU seconds per wall second, or None when CPU was not measured."""
        if self.cpu is None or self.wall <= 0:
            return None
        return self.cpu / self.wall

    def report(self) -> str:
        """Both clocks in one line. An unmeasured CPU says so; wall never stands in."""
        if self.cpu is None:
            reason = self.cpu_source.removeprefix(UNMEASURED)
            return f"{self.wall:.3f}s wall, cpu unmeasured ({reason})"
        if self.ratio is None:
            # A zero wall leaves no ratio to state. Printing the pair still beats
            # raising out of the report after every check has already run.
            return f"{self.wall:.3f}s wall, {self.cpu:.3f}s cpu"
        return f"{self.wall:.3f}s wall, {self.cpu:.3f}s cpu ({self.ratio:.2f}x)"


def _text(raw: bytes) -> str:
    """Decode child output the way subprocess text mode would, and never raise."""
    decoded = raw.decode(_ENCODING, errors="replace")
    return decoded.replace("\r\n", "\n").replace("\r", "\n")


def run(command: list[str], cwd: Path) -> Reading:
    """Run one command to completion and time it on both clocks."""
    if sys.platform == "win32":
        return _run_windows(command, cwd)
    if hasattr(os, "wait4"):
        return _run_posix(command, cwd)
    return run_unmeasured(command, cwd, "no-per-child-accounting")


def run_unmeasured(command: list[str], cwd: Path, reason: str) -> Reading:
    """Run a command with wall time only, naming why CPU could not be taken."""
    started = time.perf_counter()
    result = subprocess.run(command, cwd=cwd, check=False, capture_output=True)
    wall = time.perf_counter() - started
    return Reading(result.returncode, _text(result.stdout) + _text(result.stderr),
                   wall, None, UNMEASURED + reason)


def _run_posix(command: list[str], cwd: Path) -> Reading:
    """Read both pipes, then collect the child's own rusage with os.wait4."""
    started = time.perf_counter()
    # bufsize=0 is load-bearing: it makes each pipe a raw FileIO, so reading the
    # file descriptor directly cannot strand bytes in a BufferedReader nobody drains.
    # The context manager is what closes both pipes on every path, including the
    # interrupt that ends a verification run early; subprocess.run uses it for that.
    with subprocess.Popen(command, cwd=cwd, bufsize=0,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
        try:
            output = _drain(process)
            _, status, usage = os.wait4(process.pid, 0)
        except BaseException:
            # What subprocess.run does on the same failure: never leave a child
            # running and unreaped because the observer gave up on it.
            process.kill()
            process.wait()
            raise
        # Recording the code here is what stops Popen calling waitpid on a pid
        # os.wait4 already collected. Without it the interpreter reaps twice.
        process.returncode = os.waitstatus_to_exitcode(status)
        wall = time.perf_counter() - started
    return Reading(process.returncode, output, wall,
                   usage.ru_utime + usage.ru_stime, POSIX_SOURCE)


def _drain(process: subprocess.Popen) -> str:
    """Read stdout and stderr to EOF without letting communicate() reap the child.

    Both pipes are read at once for the reason `subprocess.communicate` does it:
    blocking on one while the other fills its buffer deadlocks. EOF arrives when
    every writer closes, which is the same condition `subprocess.run` waits on.
    """
    streams = (process.stdout, process.stderr)
    order = [stream.fileno() for stream in streams]
    chunks: dict[int, list[bytes]] = {fileno: [] for fileno in order}
    with selectors.DefaultSelector() as selector:
        for stream in streams:
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ)
        while selector.get_map():
            for key, _ in selector.select():
                data = os.read(key.fd, 65536)
                if data:
                    chunks[key.fd].append(data)
                else:
                    selector.unregister(key.fileobj)
    return "".join(_text(b"".join(chunks[fileno])) for fileno in order)


if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    #: JobObjectBasicAccountingInformation, and the access AssignProcessToJobObject
    #: requires on the process handle (PROCESS_TERMINATE | PROCESS_SET_QUOTA).
    _ACCOUNTING_CLASS = 1
    _ASSIGN_ACCESS = 0x0001 | 0x0100
    _HUNDRED_NANOSECONDS = 1e7

    class _Accounting(ctypes.Structure):
        """JOBOBJECT_BASIC_ACCOUNTING_INFORMATION; times are 100-nanosecond units."""

        _fields_ = (
            ("TotalUserTime", ctypes.c_longlong),
            ("TotalKernelTime", ctypes.c_longlong),
            ("ThisPeriodTotalUserTime", ctypes.c_longlong),
            ("ThisPeriodTotalKernelTime", ctypes.c_longlong),
            ("TotalPageFaultCount", wintypes.DWORD),
            ("TotalProcesses", wintypes.DWORD),
            ("ActiveProcesses", wintypes.DWORD),
            ("TotalTerminatedProcesses", wintypes.DWORD),
        )

    _KERNEL32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _KERNEL32.CreateJobObjectW.restype = wintypes.HANDLE
    _KERNEL32.CreateJobObjectW.argtypes = (ctypes.c_void_p, wintypes.LPCWSTR)
    _KERNEL32.OpenProcess.restype = wintypes.HANDLE
    _KERNEL32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    _KERNEL32.AssignProcessToJobObject.restype = wintypes.BOOL
    _KERNEL32.AssignProcessToJobObject.argtypes = (wintypes.HANDLE, wintypes.HANDLE)
    _KERNEL32.QueryInformationJobObject.restype = wintypes.BOOL
    _KERNEL32.QueryInformationJobObject.argtypes = (
        wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p)
    _KERNEL32.CloseHandle.argtypes = (wintypes.HANDLE,)


def _run_windows(command: list[str], cwd: Path) -> Reading:
    """Account the child's whole tree by putting it in a job object of its own."""
    job = _KERNEL32.CreateJobObjectW(None, None)
    handle = 0
    try:
        started = time.perf_counter()
        process = subprocess.Popen(command, cwd=cwd,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # The handle is opened by pid rather than taken from Popen._handle: pid is
        # public API, and Popen keeps its own handle open, so the kernel cannot
        # recycle the pid underneath this call even after the child exits.
        handle = _KERNEL32.OpenProcess(_ASSIGN_ACCESS, False, process.pid) if job else 0
        assigned = bool(handle) and bool(_KERNEL32.AssignProcessToJobObject(job, handle))
        out, err = process.communicate()
        wall = time.perf_counter() - started
        cpu, source = _job_cpu(job) if assigned else (None, _refusal(job, handle))
    finally:
        for open_handle in (handle, job):
            if open_handle:
                _KERNEL32.CloseHandle(open_handle)
    return Reading(process.returncode, _text(out) + _text(err), wall, cpu, source)


def _job_cpu(job: int, settle: float = 0.1) -> tuple[float | None, str]:
    """Kernel plus user time for every process the job ever held, terminated included.

    A job can still report an active process for a few milliseconds after the
    check returned, because disassociating a terminated process from its job is
    not instantaneous; under a saturated host that lag grew far enough to refuse
    ordinary checks. So poll it out, and treat only what does not settle as a
    descendant the check never waited for. `settle` is spent after the wall clock
    has stopped, so it cannot enter the measurement.
    """
    deadline = time.perf_counter() + settle
    while True:
        accounting = _Accounting()
        queried = _KERNEL32.QueryInformationJobObject(
            job, _ACCOUNTING_CLASS, ctypes.byref(accounting), ctypes.sizeof(accounting),
            None)
        if not queried:
            return None, UNMEASURED + "job-query-refused"
        if not accounting.TotalProcesses:
            # An empty job accounts for 0.000s, which would read as an instant check.
            # If the assignment never actually took, say nothing was measured.
            return None, UNMEASURED + "job-held-no-process"
        if not accounting.ActiveProcesses:
            total = accounting.TotalUserTime + accounting.TotalKernelTime
            return total / _HUNDRED_NANOSECONDS, WINDOWS_SOURCE
        if time.perf_counter() >= deadline:
            # Something the check started outlived it. The total is real but
            # partial, and a partial total reads exactly like a cheap check:
            # measured at 0.062s against the 0.422s its tree went on to spend.
            return None, UNMEASURED + "job-tree-still-running"
        time.sleep(0.002)


def _refusal(job: int, handle: int) -> str:
    """Name which step of the Windows path declined, so a zero is never invented.

    The assignment case carries its Win32 error, because that is the one whose
    cause is not obvious from the name: 5 is the already-exited process.
    """
    if not job:
        return UNMEASURED + "job-object-unavailable"
    if not handle:
        return UNMEASURED + "process-handle-unavailable"
    return UNMEASURED + f"job-assignment-refused-win32-{ctypes.get_last_error()}"
