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
import subprocess
import sys
import time
import uuid

from sovverify.checks import CHECKS, ROOT, Check


SKIP_PARTS = {".git", ".venv", "__pycache__", ".local"}
BUDGET_GRADES = (("PLATINUM", 3.0), ("GOLD", 6.0), ("SILVER", 15.0))
BUDGET_SECONDS = BUDGET_GRADES[-1][1]


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


def observe(check: Check, run_id: str, exit_code: int, elapsed: float, when: str) -> dict:
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
            "exit_code": exit_code,
            "outcome": "PASS" if exit_code == 0 else "FAIL",
            "elapsed_seconds": round(elapsed, 3),
        },
        "observed_at": when,
        "subject": check.name,
    }


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


def run_check(check: Check) -> tuple[Check, int, float, str]:
    started = time.perf_counter()
    result = subprocess.run(check.command, cwd=check.cwd, check=False,
                            capture_output=True, text=True)
    return check, result.returncode, time.perf_counter() - started, result.stdout + result.stderr


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
    with ThreadPoolExecutor(max_workers=len(CHECKS)) as pool:
        results = list(pool.map(run_check, CHECKS))
    wall = time.perf_counter() - started

    observations = [observe(check, run_id, code, elapsed, when)
                    for check, code, elapsed, _ in results]
    work = sum(elapsed for _, _, elapsed, _ in results)
    failed = [check.name for check, code, _, _ in results if code]

    if args.observe:
        args.observe.parent.mkdir(parents=True, exist_ok=True)
        args.observe.write_bytes(
            (json.dumps(observations, indent=2, sort_keys=True) + "\n").encode("utf-8"))

    if args.as_json:
        print(json.dumps(observations, indent=2, sort_keys=True))
        return 1 if failed else 0

    for check, _, elapsed, output in results:
        print(f"\n== {check.name} ==", flush=True)
        print(output.rstrip("\n"), flush=True)
        print(f"TIME: {check.name}: {elapsed:.3f}s", flush=True)

    if wall > BUDGET_SECONDS:
        failed.append(budget_line(wall))
    if failed:
        print(f"\nFAIL: {', '.join(failed)}")
        return 1
    print(f"\nPASS: {len(CHECKS)} checks in {wall:.3f}s wall, {work:.3f}s of work")
    print(budget_line(wall))
    print("Standing note: self-tests establish BUILT evidence only; no independent witness "
          "or owner ratification is implied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
