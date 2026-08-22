#!/usr/bin/env python3
"""Run all repository-owned structural, oracle, and reference checks."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


CHECKS = (
    ("bootstrap and locked evidence", [sys.executable, "scripts/verify_bootstrap.py"], ROOT),
    ("conformance oracle controls", [sys.executable, "conformance/run.py"], ROOT),
    ("conformance oracle tests", [sys.executable, "-m", "unittest", "discover", "-s", "conformance/tests", "-v"], ROOT),
    ("Asset Service reference tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], ROOT / "services" / "asset"),
)


def main() -> int:
    failed = []
    for name, command, cwd in CHECKS:
        print(f"\n== {name} ==", flush=True)
        result = subprocess.run(command, cwd=cwd, check=False)
        if result.returncode:
            failed.append(name)
    if failed:
        print(f"\nFAIL: {', '.join(failed)}")
        return 1
    print("\nPASS: repository checks completed")
    print("Standing note: self-tests establish BUILT evidence only; no independent witness or owner ratification is implied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
