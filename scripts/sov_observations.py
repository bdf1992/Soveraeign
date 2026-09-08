#!/usr/bin/env python3
"""Read what a verification run observed, and read two runs against each other.

`scripts/verify.py --observe` emits one record per check against
`contracts/observation.schema.json`, and CI retains those records per commit. Until
this module nothing opened them: `scripts/sovland/isolation.py` attributes a run, but
only one it just executed itself, so a retained record was kept and never read.

What two records make answerable is narrower than it first looks, and the narrowing
is the point. Each record carries the addresses its check read, the digests of those
bytes, and both clocks. So:

    the observed digests moved      the repository changed under that check
    the digests held and cost moved the same bytes cost differently this run
    a clock the host could not take no cost reading is offered at all

That second row used to read "the same bytes cost more work", with a third blaming a
longer wall on the host. Both were wrong, and a witness proved it from this
repository's own measurements: `scripts/sovverify/clocks.py` says to read a rise in
CPU as "either more work or more competition, never as proof of the first", and
`decisions/0071` measured 2.12x CPU from saturation alone - above the ratio below, so
contention produced eight confident "more work" readings on unmoved bytes. This
module reports the pair and names the cause it cannot determine.

Limits, and this list is what has been found rather than a proof that nothing else
is here - the wording matters, because a list that called itself complete is the
finding that produced two of the repairs in this file:

  - content movement is visible only at the addresses a check *declares*. Appending
    a byte to `AGENTS.md`, which no check names, failed two checks while this reader
    reported no change at all. `isolation.py` states the same weakness about its own
    attribution. An outcome that moved with nothing reported behind it is named as
    such in the output rather than left to read as nothing having happened;
  - a directory address digests a manifest that skips `SKIP_PARTS`, so movement
    under those paths is invisible here as it is to `verify.py`;
  - shape is checked against the contract; provenance is not, so a well-formed
    record this repository never produced reads as one.

This module settles nothing and ratifies nothing. A record read here establishes at
most what the record says.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parent.parent
CONTRACT = ROOT / "contracts" / "observation.schema.json"
#: `subject` is optional in the contract and required here, because it is the key two
#: runs are compared on. Named separately so this reader never claims the contract
#: demanded something it does not.
COMPARED_ON = "subject"
#: A cost change under this many seconds is below what any host resolves. Measured,
#: not guessed: across two runs of one unchanged tree the largest absolute move among
#: every sub-second check was 0.082s. An earlier 0.5s floor was ten times that and
#: hid real change - 43 of 55 checks run under 0.25s of CPU, so a threefold
#: regression could not reach it.
MATERIAL_SECONDS = 0.10
#: And it must also be this multiple. Largest ratio across that same unchanged pair
#: was 1.35.
MATERIAL_RATIO = 1.5


class Refusal(Exception):
    """A named refusal. The reason code is the message's first token."""


def required() -> tuple[str, ...]:
    """The keys `contracts/observation.schema.json` requires, read from the contract.

    Read rather than restated, so this cannot drift from the shape it checks. An
    earlier version listed five keys of its own: it invented one requirement the
    contract does not make and omitted four it does.
    """
    try:
        schema = json.loads(CONTRACT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as problem:
        raise Refusal(f"NO_CONTRACT {CONTRACT}: {problem}") from problem
    return tuple(schema.get("required", ()))


def load(path: Path) -> list[dict[str, Any]]:
    """One run of observation records, or a named refusal.

    A file that is not a run refuses rather than being summarised. Reading a
    half-understood file into a confident paragraph is the failure this whole line
    of work exists against.
    """
    keys = required()
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as problem:
        raise Refusal(f"UNREADABLE {path}: {problem}") from problem
    if not isinstance(rows, list):
        raise Refusal(f"NOT_A_RUN {path} holds {type(rows).__name__}, not a list of records")
    if not rows:
        raise Refusal(f"EMPTY_RUN {path} holds no records")
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise Refusal(f"NOT_A_RUN {path} record {index} is {type(row).__name__}, not a record")
        missing = [key for key in keys if key not in row]
        if missing:
            raise Refusal(f"NOT_A_RUN {path} record {index} lacks {', '.join(missing)}")
        if COMPARED_ON not in row:
            raise Refusal(f"NO_SUBJECT {path} record {index} names no subject to compare on")
        if len(row["observed_state_addresses"]) != len(row["observed_state_digests"]):
            raise Refusal(f"MISALIGNED {path} record {index} has "
                          f"{len(row['observed_state_addresses'])} addresses and "
                          f"{len(row['observed_state_digests'])} digests")
    runs = {row["run_id"] for row in rows}
    if len(runs) > 1:
        raise Refusal(f"MIXED_RUNS {path} holds {len(runs)} run ids; a run is one reading")
    return rows


def outcome(row: dict[str, Any]) -> str:
    """What one record says its check concluded."""
    return str((row.get("predicate_results") or {}).get("outcome", "UNKNOWN"))


def clock(row: dict[str, Any], key: str) -> float | None:
    """One clock off a record, or None where the host could not measure it."""
    value = (row.get("predicate_results") or {}).get(key)
    return None if value is None else float(value)


def moved(before: float | None, after: float | None) -> str:
    """How a cost changed: "slower", "faster", or "" for jitter or no reading.

    Direction is carried rather than dropped. An earlier version compared absolute
    difference, so a check that ran in a third of the time was reported as having
    waited longer - a wrong reading printed confidently, found by running this
    against two real runs rather than by rereading it.
    """
    if before is None or after is None:
        return ""
    if abs(after - before) < MATERIAL_SECONDS:
        return ""
    slow, fast = max(after, before), min(after, before)
    if fast > 0 and slow / fast < MATERIAL_RATIO:
        return ""
    return "slower" if after > before else "faster"


def content(row: dict[str, Any]) -> list[tuple[str, str]]:
    """What one check read, as address/digest pairs it can be compared on."""
    return sorted(zip(row["observed_state_addresses"], row["observed_state_digests"]))


def cost(subject: str, old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any] | None:
    """One check's cost across two runs, with the cause left undetermined."""
    wall = moved(clock(old, "elapsed_seconds"), clock(new, "elapsed_seconds"))
    cpu = moved(clock(old, "cpu_seconds"), clock(new, "cpu_seconds"))
    if not wall and not cpu:
        return None
    measured = clock(old, "cpu_seconds") is not None and clock(new, "cpu_seconds") is not None
    return {"subject": subject, "direction": wall or cpu, "measured": measured,
            "wall": [clock(old, "elapsed_seconds"), clock(new, "elapsed_seconds")],
            "cpu": [clock(old, "cpu_seconds"), clock(new, "cpu_seconds")],
            "cpu_source": [(old.get("predicate_results") or {}).get("cpu_source"),
                           (new.get("predicate_results") or {}).get("cpu_source")]}


def summarise(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """One run reduced to what a reader wants first: what failed, and what it read."""
    failed = [row for row in rows if outcome(row) != "PASS"]
    walls = [(row["subject"], clock(row, "elapsed_seconds") or 0.0) for row in rows]
    return {
        "run_id": rows[0]["run_id"],
        "observer_id": rows[0]["observer_id"],
        "observed_at": rows[0]["observed_at"],
        "checks": len(rows),
        "failed": [{"subject": row["subject"],
                    "exit_code": (row.get("predicate_results") or {}).get("exit_code"),
                    "addresses": row["observed_state_addresses"]} for row in failed],
        "slowest": sorted(walls, key=lambda pair: pair[1], reverse=True)[:5],
        "unmeasured_cpu": sorted(row["subject"] for row in rows
                                 if clock(row, "cpu_seconds") is None),
    }


def compare(before: list[dict[str, Any]], after: list[dict[str, Any]]) -> dict[str, Any]:
    """Two runs read against each other, per check.

    A check whose content moved is not also reported as a cost change: the repository
    changing under it accounts for its cost, and reporting both invites a reader to
    count one cause twice. A check whose outcome moved with neither reported is
    carried in `unexplained`, because this reader failing to see a reason is not the
    same fact as there being none.
    """
    if before[0]["run_id"] == after[0]["run_id"]:
        raise Refusal(f"SAME_RUN both files hold run {before[0]['run_id']}")
    was = {row["subject"]: row for row in before}
    now = {row["subject"]: row for row in after}
    changed, costs, flipped = [], [], []
    for subject in sorted(set(was) & set(now)):
        old, new = was[subject], now[subject]
        if outcome(old) != outcome(new):
            flipped.append({"subject": subject, "was": outcome(old), "now": outcome(new)})
        if content(old) != content(new):
            changed.append(subject)
            continue
        reading = cost(subject, old, new)
        if reading:
            costs.append(reading)
    accounted = set(changed) | {entry["subject"] for entry in costs}
    return {
        "before": before[0]["run_id"],
        "after": after[0]["run_id"],
        "outcome_changed": flipped,
        "content_changed": changed,
        "cost_changed": costs,
        "unexplained": [entry["subject"] for entry in flipped
                        if entry["subject"] not in accounted],
        "checks_added": sorted(set(now) - set(was)),
        "checks_removed": sorted(set(was) - set(now)),
    }


def read_lines(found: dict[str, Any]) -> list[str]:
    """The human report for one run."""
    lines = [f"run {found['run_id']} at {found['observed_at']}, observed by "
             f"{found['observer_id']}: {found['checks']} checks, {len(found['failed'])} failing"]
    for entry in found["failed"]:
        lines.append(f"  FAIL {entry['subject']} (exit {entry['exit_code']}) "
                     f"read {', '.join(entry['addresses']) or 'nothing on disk'}")
    for subject, seconds in found["slowest"]:
        lines.append(f"  {seconds:7.3f}s {subject}")
    if found["unmeasured_cpu"]:
        lines.append(f"  no CPU clock on this host for {len(found['unmeasured_cpu'])} check(s); "
                     "their cost is wall time only")
    return lines


def _pair(values: list[float | None]) -> str:
    """Two clock readings, or a plain statement that one of them is absent."""
    if values[0] is None or values[1] is None:
        return "not measured"
    return f"{values[0]:.3f}s -> {values[1]:.3f}s"


def compare_lines(found: dict[str, Any]) -> list[str]:
    """The human report for two runs, in the order a reader needs it."""
    lines = [f"{found['before']} -> {found['after']}"]
    for entry in found["outcome_changed"]:
        lines.append(f"  {entry['was']} -> {entry['now']}: {entry['subject']}")
    for subject in found["content_changed"]:
        lines.append(f"  content moved: {subject} read different bytes")
    for entry in found["cost_changed"]:
        lines.append(f"  cost moved {entry['direction']}: {entry['subject']} "
                     f"wall {_pair(entry['wall'])}, cpu {_pair(entry['cpu'])}")
        if not entry["measured"]:
            lines.append(f"      no CPU reading on one side ({entry['cpu_source'][0]} then "
                         f"{entry['cpu_source'][1]}); the wall alone attributes nothing")
    if any(entry["measured"] for entry in found["cost_changed"]):
        lines.append("  a rise in CPU is more work or more competition, and nothing here tells "
                     "them apart (scripts/sovverify/clocks.py, decisions/0071)")
    for subject in found["unexplained"]:
        lines.append(f"  {subject} changed outcome and this reader cannot see why: content "
                     "moves only where a check declares what it reads")
    for subject in found["checks_added"]:
        lines.append(f"  added since: {subject}")
    for subject in found["checks_removed"]:
        lines.append(f"  gone since: {subject}")
    if len(lines) == 1:
        lines.append("  no check changed outcome, content or cost between these runs")
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true", dest="as_json",
                        help="print the reading as JSON instead of the human report")
    commands = parser.add_subparsers(dest="command", required=True)
    one = commands.add_parser("read", help="summarise one retained run")
    one.add_argument("path", type=Path)
    two = commands.add_parser("compare", help="read two retained runs against each other")
    two.add_argument("before", type=Path)
    two.add_argument("after", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "read":
            found = summarise(load(args.path))
            lines = read_lines(found)
        else:
            found = compare(load(args.before), load(args.after))
            lines = compare_lines(found)
    except Refusal as refusal:
        print(f"REFUSED: {refusal}", file=sys.stderr)
        return 2
    print(json.dumps(found, indent=2, sort_keys=True) if args.as_json else "\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
