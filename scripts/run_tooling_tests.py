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
# The root verifier already runs every independent check concurrently. Four
# tooling workers provide useful module-level concurrency without the hosted
# runner contention observed when this nested pool was widened to five or eight.
DEFAULT_WORKERS = 4
# Most tooling modules exercise bounded fixtures. test_sov_docs deliberately renders
# the complete published corpus several times and is an order-of-magnitude different
# unit of work. Hosted observations showed that giving it ordinary module weight left
# its shard on the critical path even after pre-descent pruning. Weight it as roughly
# ten bounded modules so the existing four-worker pool nearly isolates that corpus
# reader without adding a process or dropping evidence.
# test_verify_clocks measures real subprocesses, so it deliberately sleeps and burns
# CPU. Measured at 0.54s against roughly 0.05s for a bounded module, and it added
# 0.75s to whichever shard drew it while carrying ordinary weight.
MODULE_WEIGHTS = {"test_sov_docs.py": 10, "test_verify_clocks.py": 7}


def test_modules() -> tuple[Path, ...]:
    """Return the complete deterministic tooling module population."""
    return tuple(sorted(TEST_ROOT.glob("test_*.py")))


def module_weight(module: Path) -> int:
    return MODULE_WEIGHTS.get(module.name, 1)


def partition(modules: tuple[Path, ...], workers: int) -> tuple[tuple[Path, ...], ...]:
    """Assign every module once using stable longest-weight-first balancing."""
    if workers < 1:
        raise ValueError("workers must be positive")
    count = min(workers, len(modules))
    if not count:
        return ()
    buckets: list[list[Path]] = [[] for _ in range(count)]
    loads = [0] * count
    ordered = sorted(modules, key=lambda module: (-module_weight(module), module.as_posix()))
    for module in ordered:
        index = min(range(count), key=lambda item: (loads[item], item))
        buckets[index].append(module)
        loads[index] += module_weight(module)
    return tuple(tuple(sorted(bucket)) for bucket in buckets)


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
        names = ", ".join(path.stem for path in bucket)
        print(f"\n== tooling shard {index}/{len(buckets)}: {names} ==")
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
