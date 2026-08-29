#!/usr/bin/env python3
"""Run every repository-owned structural, oracle, and reference check.

Each check declares how it avoids relying on the thing it checks, and the run
emits one `Observation` per check against `contracts/observation.schema.json`.
Emitting records rather than prose is the point: a claim about what verification
found can then be checked against a record instead of trusted as a paragraph.

An observation settles nothing. `AGENTS.md`: a test may establish `BUILT`; it
may never claim `WITNESSED` or `RATIFIED`.

Checks are independent and run concurrently. Output is buffered and printed in
declared order so a parallel run reads exactly like a serial one.

Every check is timed on two clocks, wall and CPU, by `sovverify.clocks`. One
aggregate wall time could not tell a repository that grew from a machine that was
busy; per check, the pair can. The gate still keys on aggregate wall time and on
nothing else - `decisions/0050` owns that budget.

The table of what to run lives in `scripts/sovverify/checks.py`; this module owns
only how a run is executed, observed, and graded.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import argparse
import json
import sys
import time
import uuid

from sovverify import budget, clocks
from sovverify.checks import CHECKS, ROOT, Check


# Filtered after the glob rather than pruned at descent, so this set costs a walk it
# then discards. `worktrees` is here for the same reason it is in the other two walkers:
# an agent checkout under `.claude/worktrees/` is a copy of this repository and would
# enter a directory digest as though it were repository content. Latent today, because
# no check declares an observed address that contains one. `lineage` and `node_modules`
# are deliberately not added: the other two sets drop them from a document corpus and a
# lint population, and a check that digests attributed evidence should see it.
SKIP_PARTS = {".git", ".venv", "__pycache__", ".local", "worktrees"}
# The budget is declared in contracts/verification-budget.json, not here, so the
# numbers and the rule that a wall-clock reading never refuses live in one place
# a reader can open (decisions/0081). These names remain because callers and the
# structural drift tests use them; both are derived, never restated.
BUDGET_TABLE = budget.load()
BUDGET_GRADES = tuple(budget.grades(BUDGET_TABLE))
BUDGET_SECONDS = budget.slowest_band(BUDGET_TABLE)
# Starting every repository check at once became slower as the suite grew: the
# hosted runner spent its budget context-switching between 20+ Python processes.
# Keep enough independent work in flight to hide startup/I/O without allowing
# process count itself to become the critical path.
MAX_CHECK_WORKERS = 8
STANDING_NOTE = ("Standing note: self-tests establish BUILT evidence only. Nothing here is "
                 "accepted; acceptance is an act taken by a seat over a presented result "
                 "(contracts/acceptance-policy.json).")


def digest(address: str) -> str:
    """sha256 of a file, or of a sorted manifest of the files beneath a directory."""
    target = ROOT / address
    if target.is_file():
        return "sha256:" + sha256(target.read_bytes()).hexdigest()
    manifest = sha256()
    for path in sorted(target.rglob("*")) if target.is_dir() else []:
        if not path.is_file() or SKIP_PARTS & set(path.parts):
            continue
        manifest.update(path.relative_to(target).as_posix().encode("utf-8"))
        manifest.update(b"\0")
        manifest.update(sha256(path.read_bytes()).hexdigest().encode("ascii"))
        manifest.update(b"\n")
    return "sha256:" + manifest.hexdigest()


def observe(check: Check, run_id: str, reading: clocks.Reading, when: str) -> dict:
    """One Observation of one check, per contracts/observation.schema.json."""
    addresses = [address for address in check.observes if (ROOT / address).exists()]
    identity = sha256(f"{run_id}\0{check.name}".encode("utf-8")).hexdigest()[:32]
    return {
        "observation_id": f"observation_{identity}",
        "run_id": run_id,
        "observer_id": f"scripts/verify.py@{digest('scripts/verify.py').split(':', 1)[1][:16]}",
        "observer_relation": check.relation,
        "observed_state_addresses": addresses,
        "observed_state_digests": [digest(address) for address in addresses],
        "predicate_results": {
            "exit_code": reading.exit_code,
            "outcome": "PASS" if reading.exit_code == 0 else "FAIL",
            "elapsed_seconds": round(reading.wall, 3),
            "cpu_seconds": None if reading.cpu is None else round(reading.cpu, 3),
            "cpu_ratio": None if reading.ratio is None else round(reading.ratio, 3),
            "cpu_source": reading.cpu_source,
        },
        "observed_at": when,
        "subject": check.name,
    }


def grade(wall: float) -> str | None:
    """Name the band a wall time earns, or None past the slowest band.

    None no longer means the run failed. A wall-clock reading measures the host
    at that instant, not the repository, so past the slowest band the run earns
    no grade and records debt (`decisions/0081`).
    """
    return budget.grade(wall, BUDGET_TABLE)


def budget_line(wall: float) -> str:
    """State the grade a run earned, or the debt it owes, naming the next faster band."""
    return budget.wall_clock_line(wall, BUDGET_TABLE)


def run_check(check: Check) -> tuple[Check, clocks.Reading]:
    """Run one check on both clocks. Nothing about the command changes to be measured."""
    return check, clocks.run(check.command, check.cwd)


def confirm_alone(catastrophes: list[budget.Catastrophe],
                  results: list[tuple[Check, clocks.Reading]]) -> list[budget.Catastrophe]:
    """Re-read each suspected catastrophe with nothing else running.

    The suite runs its checks in a pool, so a per-check wall time carries
    whatever was scheduled beside it. That is tolerable for attributing debt and
    not for refusing a run, which is the most expensive thing this harness does.
    So the suspects are re-run one at a time, after every other check has
    finished, and the isolated reading is what decides.

    Only the suspects are re-run, so a passing run costs nothing extra.
    """
    if not catastrophes or not budget.confirms_alone(BUDGET_TABLE):
        return catastrophes
    by_name = {check.name: check for check, _ in results}
    confirmed = []
    for entry in catastrophes:
        check = by_name.get(entry.check)
        if check is None:
            # Unreachable today, and it must not fail open if it ever is. An
            # entry left with no isolated reading is discarded by `refusing`, so
            # a suspect nobody could re-read would silently stop refusing.
            # Standing on the reading we do have is the safe direction.
            confirmed.append(entry._replace(alone=entry.seconds))
            continue
        print(f"\n== re-reading {entry.check} alone ==", flush=True)
        reading = clocks.run(check.command, check.cwd)
        print(f"TIME: {entry.check} alone: {reading.report()}", flush=True)
        confirmed.append(entry._replace(alone=reading.wall))
    # A suspect that leaves here with no isolated reading is discarded by
    # `refusing`, so any future reason to skip a re-read - a cap on how many to
    # take, a timeout, an early return - would fail open and no case bounded by
    # a fixed number of suspects could see it. Standing on the reading there is
    # makes every such skip fail closed instead, whatever its shape.
    return [entry if entry.alone is not None else entry._replace(alone=entry.seconds)
            for entry in confirmed]


def cost_line(results: list[tuple[Check, clocks.Reading]]) -> str:
    """Sum both clocks over the checks, and say plainly when a CPU number is missing.

    The old report summed `perf_counter` per check and called the total "work",
    which was a second wall figure carrying the same contention as the first.
    """
    measured = [reading for _, reading in results if reading.measured]
    wall = f"{sum(reading.wall for _, reading in results):.3f}s of check wall"
    if not measured:
        # A summed 0.000s would read as a run that cost no compute at all.
        return f"{wall}, cpu unmeasured for all {len(results)} checks"
    line = f"{wall}, {sum(reading.cpu for reading in measured):.3f}s of check cpu"
    missing = len(results) - len(measured)
    return line if not missing else f"{line}; cpu unmeasured for {missing} of {len(results)}"


def summary(results: list[tuple[Check, clocks.Reading]], wall: float,
            failed: list[str]) -> list[str]:
    """The closing lines of a run, cost included whether or not the gate refused.

    A failing run is where the second clock earns its place: the question "did
    the repository grow or was the machine busy" is asked hardest by a run that
    just failed, and the old report answered it only on the passing path.
    """
    cost = f"{len(results)} checks in {wall:.3f}s wall; {cost_line(results)}"
    if failed:
        return [f"FAIL: {', '.join(failed)}", f"COST: {cost}"]
    return [f"PASS: {cost}", budget_line(wall), STANDING_NOTE]


def main(argv: list[str] | None = None, run_id: str | None = None,
         now: str | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--observe", type=Path, metavar="PATH",
                        help="write the run's Observation records to PATH as JSON")
    parser.add_argument("--json", action="store_true", dest="as_json",
                        help="print the Observation records instead of the human report")
    args = parser.parse_args(argv)

    run_id = run_id or f"run_{uuid.uuid4().hex}"
    when = now or datetime.now(timezone.utc).isoformat(timespec="seconds")

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=min(MAX_CHECK_WORKERS, len(CHECKS))) as pool:
        results = list(pool.map(run_check, CHECKS))
    wall = time.perf_counter() - started

    observations = [observe(check, run_id, reading, when) for check, reading in results]
    failed = [check.name for check, reading in results if reading.exit_code]

    if args.observe:
        args.observe.parent.mkdir(parents=True, exist_ok=True)
        args.observe.write_bytes(
            (json.dumps(observations, indent=2, sort_keys=True) + "\n").encode("utf-8"))

    if args.as_json:
        print(json.dumps(observations, indent=2, sort_keys=True))
        return 1 if failed else 0

    for check, reading in results:
        print(f"\n== {check.name} ==", flush=True)
        print(reading.output.rstrip("\n"), flush=True)
        print(f"TIME: {check.name}: {reading.report()}", flush=True)

    timings = [(check.name, reading.wall) for check, reading in results]
    debts, catastrophes = budget.judge(timings, BUDGET_TABLE)
    catastrophes = confirm_alone(catastrophes, results)
    # A catastrophe is a check that changed, so it joins the semantic failures.
    # Ordinary overruns never do: they are attributed below. A suspicion that did
    # not survive being re-read alone is neither, and says so in its own line -
    # and gets its ordinary debt back, because it is now refusing nothing.
    refusing = budget.refusing(catastrophes, BUDGET_TABLE)
    failed.extend(entry.line() for entry in refusing)
    for entry in catastrophes:
        if entry in refusing:
            continue
        # CROWDED is a claim about the isolated reading, not about whether the
        # entry refuses. With `blocks` off a confirmed catastrophe also lands
        # here, and labelling that one crowded would contradict its own sentence.
        label = "CROWDED" if not entry.confirmed() else "NOT BLOCKING"
        print(f"{label}: {entry.line()}", flush=True)
    debts = sorted(debts + budget.demoted(catastrophes, refusing, BUDGET_TABLE),
                   key=lambda entry: entry.seconds, reverse=True)
    for line in budget.baseline_drift(timings, BUDGET_TABLE):
        print(f"BASELINE: {line}", flush=True)
    print("")
    for line in summary(results, wall, failed):
        print(line)
    for line in budget.report(debts, budget_line(wall), BUDGET_TABLE):
        print(line)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
