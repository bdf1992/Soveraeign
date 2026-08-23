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
    ("kernel transition contract", [sys.executable, "scripts/sov_kernel.py", "selfcheck"], ROOT),
    ("kernel participant parity", [sys.executable, "scripts/sov_kernel.py", "parity"], ROOT),
    ("ticket transition corpus", [sys.executable, "scripts/sov_ticket.py", "selfcheck"], ROOT),
    ("ticket coordination tests", [sys.executable, "-m", "unittest", "discover", "-s", "scripts/tests", "-v"], ROOT),
    (
        "Sov context profile",
        [sys.executable, "-m", "unittest", "discover", "-s", "bindings/sov/tests", "-v"],
        ROOT,
    ),
    ("Record Service reference tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], ROOT / "services" / "record"),
    ("Asset Service reference tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], ROOT / "services" / "asset"),
)

BUDGET_SECONDS = 3.0


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
        failed.append(f"verification budget ({total:.3f}s > {BUDGET_SECONDS:.3f}s)")
    if failed:
        print(f"\nFAIL: {', '.join(failed)}")
        return 1
    print(f"\nPASS: repository checks completed in {total:.3f}s")
    print("Standing note: self-tests establish BUILT evidence only; no independent witness or owner ratification is implied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
