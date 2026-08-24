#!/usr/bin/env python3
"""Run all repository-owned structural, oracle, and reference checks."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]


CHECKS = (
    ("repository hygiene", [sys.executable, "scripts/lint.py"], ROOT),
    ("recorded traps still hold", [sys.executable, "scripts/sov_traps.py"], ROOT),
    ("standing claims carry a witness", [sys.executable, "scripts/sov_standing.py"], ROOT),
    ("bootstrap and locked evidence", [sys.executable, "scripts/verify_bootstrap.py"], ROOT),
    ("conformance oracle controls", [sys.executable, "conformance/run.py"], ROOT),
    ("conformance oracle tests", [sys.executable, "-m", "unittest", "discover", "-s", "conformance/tests", "-v"], ROOT),
    ("semantic cold-start task", [sys.executable, "scripts/sov_witness.py", "semantic"], ROOT),
    ("specification traceability", [sys.executable, "scripts/sov_spec.py", "trace"], ROOT),
    ("kernel transition contract", [sys.executable, "scripts/sov_kernel.py", "selfcheck"], ROOT),
    ("kernel participant parity", [sys.executable, "scripts/sov_kernel.py", "parity"], ROOT),
    ("ticket transition corpus", [sys.executable, "scripts/sov_ticket.py", "selfcheck"], ROOT),
    ("owner queue", [sys.executable, "scripts/sov_accept.py", "audit"], ROOT),
    ("ticket coordination tests", [sys.executable, "-m", "unittest", "discover", "-s", "scripts/tests", "-v"], ROOT),
    (
        "Sov context profile",
        [sys.executable, "-m", "unittest", "discover", "-s", "bindings/sov/tests", "-v"],
        ROOT,
    ),
    ("Record Service reference tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], ROOT / "services" / "record"),
    ("Asset Service reference tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], ROOT / "services" / "asset"),
)

BUDGET_GRADES = (("PLATINUM", 3.0), ("GOLD", 6.0), ("SILVER", 15.0))
BUDGET_SECONDS = BUDGET_GRADES[-1][1]


def grade(wall: float) -> str | None:
    """Name the band a wall time earns, or None when it exceeds the budget.

    Bands run fastest first, each ceiling is inclusive, and the slowest ceiling
    is the budget - so every graded run is a passing run.
    """
    for name, ceiling in BUDGET_GRADES:
        if wall <= ceiling:
            return name
    return None


def budget_line(wall: float) -> str:
    """State the grade a run earned, naming the next faster band if there is one."""
    earned = grade(wall)
    if earned is None:
        return f"verification budget ({wall:.3f}s > {BUDGET_SECONDS:.3f}s)"
    index = [name for name, _ in BUDGET_GRADES].index(earned)
    if index == 0:
        return f"GRADE: {earned} at {wall:.3f}s, the fastest band"
    faster, ceiling = BUDGET_GRADES[index - 1]
    return f"GRADE: {earned} at {wall:.3f}s; {faster} needs {ceiling:.3f}s or less"


def main() -> int:
    failed = []
    started = time.perf_counter()
    for name, command, cwd in CHECKS:
        print(f"\n== {name} ==", flush=True)
        check_started = time.perf_counter()
        result = subprocess.run(command, cwd=cwd, check=False)
        elapsed = time.perf_counter() - check_started
        print(f"TIME: {name}: {elapsed:.3f}s", flush=True)
        if result.returncode:
            failed.append(name)
    total = time.perf_counter() - started
    if total > BUDGET_SECONDS:
        failed.append(budget_line(total))
    if failed:
        print(f"\nFAIL: {', '.join(failed)}")
        return 1
    print(f"\nPASS: repository checks completed in {total:.3f}s")
    print(budget_line(total))
    print("Standing note: self-tests establish BUILT evidence only. Nothing here is "
          "accepted; acceptance is an act taken by a seat over a presented result "
          "(contracts/acceptance-policy.json).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
