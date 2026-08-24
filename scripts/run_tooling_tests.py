#!/usr/bin/env python3
"""Run every repository tooling test module, partitioned across worker processes.

The root verifier already executes independent checks concurrently. The tooling
suite became the critical path because hundreds of otherwise independent test
modules were still executed serially inside one subprocess. This runner keeps
unittest as the test oracle, assigns each discovered module to exactly one
stable worker, and reports failure if any worker fails.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TEST_ROOT = ROOT / "scripts" / "tests"
# Four shards preserved the full suite but left one measured 2.392s critical
# path on hosted CI. Eight keeps the same deterministic partition contract while
# reducing the maximum modules per worker from eight to four on the current tree.
DEFAULT_WORKERS = 8


def test_modules() -> tuple[Path, ...]:
    """Return the complete deterministic tooling module population."""
    return tuple(sorted(TEST_ROOT.glob("test_*.py")))


def partition(modules: tuple[Path, ...], workers: int) -> tuple[tuple[Path, ...], ...]:
    """Round-robin the stable module list so every module is run exactly once."""
    if workers < 1:
        raise ValueError("workers must be positive")
    buckets: list[list[Path]] = [[] for _ in range(workers)]
    for index, module in enumerate(modules):
        buckets[index % workers].append(module)
    return tuple(tuple(bucket) for bucket in buckets if bucket)


def _run(bucket: tuple[Path, ...]) -> tuple[int, str]:
    names = [f"scripts.tests.{path.stem}" for path in bucket]
    result = subprocess.run(
        [sys.executable, "-m", "unittest", *names],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout + result.stderr


def main() -> int:
    modules = test_modules()
    if not modules:
        print("FAIL: no repository tooling test modules discovered")
        return 1
    requested = int(os.environ.get("SOV_TOOLING_TEST_WORKERS", DEFAULT_WORKERS))
    buckets = partition(modules, min(requested, len(modules)))
    with ThreadPoolExecutor(max_workers=len(buckets)) as pool:
        results = list(pool.map(_run, buckets))
    failed = False
    for index, ((code, output), bucket) in enumerate(zip(results, buckets), start=1):
        print(f"\n== tooling shard {index}/{len(buckets)}: {len(bucket)} modules ==")
        if output.rstrip():
            print(output.rstrip())
        if code:
            failed = True
    if failed:
        print(f"FAIL: repository tooling tests ({len(modules)} modules, {len(buckets)} shards)")
        return 1
    print(f"PASS: repository tooling tests ({len(modules)} modules, {len(buckets)} shards)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
