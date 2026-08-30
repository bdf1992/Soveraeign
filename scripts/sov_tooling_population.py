#!/usr/bin/env python3
"""Grade the tooling runner's discovered population from outside that population."""

from __future__ import annotations

from pathlib import Path
import os
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_tooling_tests  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / "scripts" / "tests"


def listed(where: Path) -> list[str]:
    """List test modules independently of the runner's glob implementation."""
    return sorted(
        name for name in os.listdir(where)
        if name.startswith("test_") and name.endswith(".py")
    )


def discovered() -> list[str]:
    """Return the population the tooling runner says it will execute."""
    return sorted(path.name for path in run_tooling_tests.test_modules())


def compare(expected: list[str], actual: list[str]) -> list[str]:
    """Name every population disagreement in both directions."""
    defects: list[str] = []
    for missing in sorted(set(expected) - set(actual)):
        defects.append(f"{missing} is in scripts/tests and the runner did not discover it")
    for extra in sorted(set(actual) - set(expected)):
        defects.append(f"the runner discovered {extra}, which is not in scripts/tests")
    if not expected and not actual:
        defects.append("scripts/tests holds no test modules at all")
    return defects


def selfcheck() -> list[str]:
    """Prove the comparison can distinguish agreement from disagreement."""
    failures: list[str] = []
    both = ["test_a.py", "test_b.py"]
    if compare(both, both):
        failures.append("identical populations were reported as disagreeing")
    if not any(
        "test_b.py" in line and "did not discover" in line
        for line in compare(both, ["test_a.py"])
    ):
        failures.append("a missing module was not detected")
    if not any(
        "test_c.py" in line and "not in scripts/tests" in line
        for line in compare(both, both + ["test_c.py"])
    ):
        failures.append("an invented module was not detected")
    if not compare([], []):
        failures.append("two empty populations were reported as agreement")
    return failures


def main() -> int:
    failures = selfcheck()
    if failures:
        for failure in failures:
            print(f"  {failure}")
        print("FAIL: tooling population comparison cannot prove it distinguishes defects")
        return 1

    defects = compare(listed(TESTS), discovered())
    if defects:
        for defect in defects:
            print(f"  {defect}")
        print("FAIL: tooling runner population disagrees with scripts/tests")
        return 1

    print(f"PASS: tooling population ({len(listed(TESTS))} modules; independent listing agrees)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
