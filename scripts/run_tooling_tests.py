#!/usr/bin/env python3
"""Run every repository tooling test module, partitioned across worker processes.

The root verifier already executes independent checks concurrently. The tooling
suite became the critical path because hundreds of otherwise independent test
modules were still executed serially inside one subprocess. This runner keeps
unittest as the test oracle, assigns each discovered module to exactly one
stable worker, and reports failure if any worker fails.

It also reports what each module cost. A shard total cannot name the module that
grew, so a suite reported only in aggregate can indict nobody but whoever pushed
last: on 2026-09-07 a change measuring one second against a fifteen-second suite
took the refusal for a ceiling the trunk was already sitting against. The weights
below were each set by a hand campaign that measured every module alone and then
kept only prose. `--weights` regenerates them from a real run instead.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import argparse
import os
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sovtooling.driver import COST_PREFIX  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TEST_ROOT = ROOT / "scripts" / "tests"
# The root verifier already runs every independent check concurrently. Four
# tooling workers provide useful module-level concurrency without the hosted
# runner contention observed when this nested pool was widened to five or eight.
DEFAULT_WORKERS = 4
# The table below was set by hand campaigns that measured every module alone and then
# kept only prose; three of them each found the previous table inverted, because a
# suite reported only in aggregate cannot say which module moved. That measurement is
# now taken on every run: `python scripts/run_tooling_tests.py --weights` prints the
# table this run measures. Regenerating is deliberate, not automatic — the derived
# values are seconds times ten, and packing is not monotonic in the weight, so a new
# table has to be checked against test_run_tooling_tests before it is pasted in.
# Most tooling modules exercise bounded fixtures. test_sov_docs deliberately renders
# the complete published corpus several times and is an order-of-magnitude different
# unit of work. Hosted observations showed that giving it ordinary module weight left
# its shard on the critical path even after pre-descent pruning. Weight it as roughly
# ten bounded modules so the existing four-worker pool nearly isolates that corpus
# reader without adding a process or dropping evidence.
# test_sov_branch is the same shape of exception for a different reason: every case
# builds a throwaway git repository and drives real git subprocesses, so it measured
# 4.1s against roughly 0.08s for a bounded module. Left at ordinary weight it packs
# beside the other slow readers whenever the module population changes, and the shard
# it lands in becomes the whole suite's critical path. Weighted here it stays with one
# peer instead of four. The weight is a scheduling hint; it changes no check and no
# budget, which decisions/0050 owns.
# test_verify_clocks measures real subprocesses, so it deliberately sleeps and burns
# CPU. Measured at 0.64s on Windows and 0.28s on Linux against roughly 0.05s for a
# bounded module, and at ordinary weight it added 0.75s to whichever shard drew it.
# test_sov_branch was 4 against a two-entry table and no longer bought what it was
# chosen for once a third heavy module arrived: measured over the merged set, 4
# gave its shard 18 peers where dropping the entry gave 15. The property only
# holds from 8 upward. 10 puts it level with the other multi-second reader and
# leaves margin. Note for whoever tunes this next: peers are not monotonic in the
# weight across the whole range - weight 1 packs late and lands at 15, weight 2
# at 20 - so a weight has to be measured rather than reasoned about.
#
# Remeasured 2026-08-31 at 97 modules after the commissioning-contract test was
# added. The 89-module weights had expired: docs at 20 and branch at 18 no longer
# bought shorter shards, and clocks at 7 over-weighted a much smaller Linux cost.
# Holding the other two measured weights constant, 24 gives test_sov_docs 15 peers
# instead of 32 unweighted, 32 gives test_sov_branch 8 instead of 30, and 3 gives
# test_verify_clocks 36 instead of 38. The resulting synthetic loads are
# 39/38/38/38. These remain scheduling hints, never evidence or budget changes.
#
# Remeasured 2026-09-07 at 111 modules on Linux, every module alone, after the
# discovery-and-reuse suite arrived and the hosted tooling check crossed the 30s
# catastrophic ceiling (31.2s and 36.8s alone on two runners at ea01dcc). The 97-module
# table had inverted: test_sov_docs measured 1.4s and test_sov_branch 1.2s, so weights of
# 24 and 32 isolated two modules that no longer needed it, while test_sov_fresh at 5.1s,
# test_sov_strand at 3.6s, test_sov_reuse at 3.0s, test_sov_backlog at 2.5s and
# test_sov_ci_subject at 2.3s all packed at ordinary weight into one shard, which
# measured 18.6s against 4.5s, 10.4s and 5.3s for the other three. Weights below are
# the measured seconds times ten for every module at or above one second; a bounded
# module measures 0.05s to 0.1s. Resulting synthetic loads 100/100/100/99 and measured
# shards 12.1s, 9.6s, 11.0s and 9.8s, a 12.6s wall against 18.9s before. Still
# scheduling hints, never evidence or budget.
MODULE_WEIGHTS = {
    "test_sov_fresh.py": 51, "test_sov_strand.py": 36, "test_sov_reuse.py": 30,
    "test_sov_backlog.py": 25, "test_sov_ci_subject.py": 23,
    "test_repository_candidate_effects.py": 18, "test_automation_control.py": 17,
    "test_automation_health.py": 16, "test_lint.py": 15, "test_sov_docs.py": 14,
    "test_sov_surface.py": 12, "test_sov_branch.py": 12, "test_sov_snapshot.py": 11,
    "test_sov_land.py": 11, "test_sov_facets.py": 10, "test_verify_clocks.py": 3,
}


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
    names = [path.stem for path in bucket]
    result = subprocess.run(
        [sys.executable, "-m", "scripts.sovtooling.driver", *names],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout + result.stderr


def module_costs(output: str) -> dict[str, float]:
    """Read the per-module wall costs the driver reported, keyed by module stem."""
    costs: dict[str, float] = {}
    for line in output.splitlines():
        if not line.startswith(COST_PREFIX + " "):
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        try:
            costs[parts[1]] = float(parts[2])
        except ValueError:
            continue
    return costs


def measured_weights(costs: dict[str, float]) -> dict[str, int]:
    """Derive the scheduling table from measurement: seconds times ten, at or above 1s.

    This is the same rule each hand campaign applied and then discarded. Deriving it
    means a stale table is a run away from repair rather than a campaign away.
    """
    return {
        f"{name}.py": round(seconds * 10)
        for name, seconds in sorted(costs.items(), key=lambda item: (-item[1], item[0]))
        if seconds >= 1.0
    }


def report_costs(costs: dict[str, float], shards: int, threshold: float = 1.0) -> None:
    """Print what each module cost, so an overrun names the module that owns it."""
    if not costs:
        return
    ranked = sorted(costs.items(), key=lambda item: (-item[1], item[0]))
    named = [item for item in ranked if item[1] >= threshold]
    rest = [item for item in ranked if item[1] < threshold]
    print(f"\n== tooling cost: {len(costs)} modules, {shards} shards ==")
    for name, seconds in named:
        print(f"  {seconds:7.3f}s  {name}")
    if rest:
        total = sum(seconds for _, seconds in rest)
        print(f"  {total:7.3f}s  ({len(rest)} module(s) under {threshold:.3f}s)")
    print(f"  {sum(costs.values()):7.3f}s  TOTAL module cost across {shards} shards")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the repository tooling test suite.")
    parser.add_argument(
        "--weights",
        action="store_true",
        help="print the MODULE_WEIGHTS table this run measures, instead of the shard log",
    )
    args = parser.parse_args(argv)
    modules = test_modules()
    if not modules:
        print("FAIL: no repository tooling test modules discovered")
        return 1
    requested = int(os.environ.get("SOV_TOOLING_TEST_WORKERS", DEFAULT_WORKERS))
    buckets = partition(modules, min(requested, len(modules)))
    with ThreadPoolExecutor(max_workers=len(buckets)) as pool:
        results = list(pool.map(_run, buckets))
    failed = False
    costs: dict[str, float] = {}
    shard_log: list[str] = []
    for index, ((code, output), bucket) in enumerate(zip(results, buckets), start=1):
        costs.update(module_costs(output))
        names = ", ".join(path.stem for path in bucket)
        shard_log.append(f"\n== tooling shard {index}/{len(buckets)}: {names} ==")
        body = "\n".join(
            line for line in output.rstrip().splitlines() if not line.startswith(COST_PREFIX + " ")
        )
        if body.strip():
            shard_log.append(body)
        if code:
            failed = True
    if args.weights:
        for name, weight in measured_weights(costs).items():
            print(f'    "{name}": {weight},')
        return 1 if failed else 0
    for line in shard_log:
        print(line)
    report_costs(costs, len(buckets))
    if failed:
        print(f"FAIL: repository tooling tests ({len(modules)} modules, {len(buckets)} shards)")
        return 1
    print(f"PASS: repository tooling tests ({len(modules)} modules, {len(buckets)} shards)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
