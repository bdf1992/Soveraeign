#!/usr/bin/env python3
"""Read what a verification run observed, and compare two runs against each other.

`scripts/verify.py --observe` emits one record per check against
`contracts/observation.schema.json`, and CI retains those records per commit. Until
this module, nothing read them: `scripts/sovland/isolation.py` attributes a run, but
only one it just executed itself, so a retained record was kept and never opened.

What two retained records make answerable is the question `verify.py` asks in its own
docstring and cannot answer from one aggregate wall time: did the repository grow, or
was the machine busy. Each record carries the addresses its check read, the digests of
those bytes, and both clocks. So:

    a check whose observed digests changed   -> the repository changed under it
    identical digests, CPU up materially     -> the same bytes cost more work
    identical digests, wall up, CPU flat     -> the host was busy, not the repository

Those are readings, not verdicts. This module settles nothing, ratifies nothing, and
grades no run as acceptable; `AGENTS.md` reserves that for a seat, and a record read
here establishes at most what the record says.

The limit, found by running this against two real runs rather than reasoned about
afterwards: content movement is only visible at the addresses a check *declares* it
reads. Appending a byte to `AGENTS.md` failed two checks in a comparison that
reported no content change at all, because neither check names that file in its
`observes` tuple. `scripts/sovland/isolation.py` states the same weakness about its
own attribution - "attribution is only as good as each `Check.observes` tuple, and
nothing anywhere grades a tuple against what its check actually reads" - and this
module inherits it exactly. So a check that changed outcome with no content change
reported means the reader could not see why, never that no reason exists.

Refusals are named rather than guessed at: a file that is not one run of observations
is refused instead of being summarised into something plausible.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import sys

#: Keys every record must carry before this module will read a file as a run.
REQUIRED = ("subject", "run_id", "observed_state_addresses", "observed_state_digests",
            "predicate_results")
#: A cost change smaller than this in absolute terms is noise on any host.
MATERIAL_SECONDS = 0.5
#: A cost change must also be this multiple to be read as a change rather than jitter.
MATERIAL_RATIO = 1.5


class Refusal(Exception):
    """A named refusal. The reason code is the message's first token."""


def load(path: Path) -> list[dict[str, Any]]:
    """One run of observation records, or a named refusal.

    A file that is not a run refuses rather than being summarised. Reading a
    half-understood file into a confident paragraph is the failure this whole
    concern exists against.
    """
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
            raise Refusal(f"NOT_A_RUN {path} record {index} is {type(row).__name__}")
        missing = [key for key in REQUIRED if key not in row]
        if missing:
            raise Refusal(f"NOT_A_RUN {path} record {index} lacks {', '.join(missing)}")
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
    """How a cost changed: "slower", "faster", or "" for jitter and no reading.

    Direction is carried rather than dropped. An earlier version compared absolute
    difference, so a check that ran in a third of the time was reported as having
    waited longer - a wrong reading printed confidently, which is the failure this
    whole line of work exists against. Found by running it, not by rereading it.
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
    addresses = row.get("observed_state_addresses") or []
    digests = row.get("observed_state_digests") or []
    return sorted(zip(addresses, digests))


def summarise(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """One run reduced to what a reader wants first: what failed, and what it read."""
    failed = [row for row in rows if outcome(row) != "PASS"]
    walls = [(row["subject"], clock(row, "elapsed_seconds") or 0.0) for row in rows]
    return {
        "run_id": rows[0]["run_id"],
        "observed_at": rows[0].get("observed_at"),
        "checks": len(rows),
        "failed": [{"subject": row["subject"],
                    "exit_code": (row.get("predicate_results") or {}).get("exit_code"),
                    "addresses": row.get("observed_state_addresses") or []}
                   for row in failed],
        "slowest": sorted(walls, key=lambda pair: pair[1], reverse=True)[:5],
        "unmeasured_cpu": sorted(row["subject"] for row in rows
                                 if clock(row, "cpu_seconds") is None),
    }


def compare(before: list[dict[str, Any]], after: list[dict[str, Any]]) -> dict[str, Any]:
    """Two runs read against each other, per check.

    Every difference is attributed to what the records themselves carry: content
    when the observed digests moved, work when identical bytes cost materially more
    CPU, and waiting when the wall grew while the CPU did not. A check whose content
    moved is not also read as slower - the repository changed under it, and that is
    the reading that explains the rest.
    """
    if before[0]["run_id"] == after[0]["run_id"]:
        raise Refusal(f"SAME_RUN both files hold run {before[0]['run_id']}")
    was = {row["subject"]: row for row in before}
    now = {row["subject"]: row for row in after}
    changed, work, waiting, flipped = [], [], [], []
    for subject in sorted(set(was) & set(now)):
        old, new = was[subject], now[subject]
        if outcome(old) != outcome(new):
            flipped.append({"subject": subject, "was": outcome(old), "now": outcome(new)})
        if content(old) != content(new):
            changed.append(subject)
            continue
        cpu = moved(clock(old, "cpu_seconds"), clock(new, "cpu_seconds"))
        wall = moved(clock(old, "elapsed_seconds"), clock(new, "elapsed_seconds"))
        if cpu:
            work.append({"subject": subject, "direction": cpu,
                         "was": clock(old, "cpu_seconds"), "now": clock(new, "cpu_seconds")})
        elif wall:
            waiting.append({"subject": subject, "direction": wall,
                            "was": clock(old, "elapsed_seconds"),
                            "now": clock(new, "elapsed_seconds")})
    return {
        "before": before[0]["run_id"],
        "after": after[0]["run_id"],
        "outcome_changed": flipped,
        "content_changed": changed,
        "cost_changed_same_content": work,
        "waited_longer_same_work": waiting,
        "checks_added": sorted(set(now) - set(was)),
        "checks_removed": sorted(set(was) - set(now)),
    }


def read_lines(found: dict[str, Any]) -> list[str]:
    """The human report for one run."""
    lines = [f"run {found['run_id']} at {found['observed_at']}: {found['checks']} checks, "
             f"{len(found['failed'])} failing"]
    for entry in found["failed"]:
        lines.append(f"  FAIL {entry['subject']} (exit {entry['exit_code']}) "
                     f"read {', '.join(entry['addresses']) or 'nothing on disk'}")
    for subject, seconds in found["slowest"]:
        lines.append(f"  {seconds:7.3f}s {subject}")
    if found["unmeasured_cpu"]:
        lines.append(f"  no CPU clock on this host for {len(found['unmeasured_cpu'])} check(s); "
                     "their cost is wall time only")
    return lines


def compare_lines(found: dict[str, Any]) -> list[str]:
    """The human report for two runs, in the order a reader needs it."""
    lines = [f"{found['before']} -> {found['after']}"]
    for entry in found["outcome_changed"]:
        lines.append(f"  {entry['was']} -> {entry['now']}: {entry['subject']}")
    for subject in found["content_changed"]:
        lines.append(f"  content moved: {subject} read different bytes")
    for entry in found["cost_changed_same_content"]:
        turn = "more" if entry["direction"] == "slower" else "less"
        lines.append(f"  same bytes cost {turn} work: {subject_cost(entry)}")
    for entry in found["waited_longer_same_work"]:
        if entry["direction"] == "slower":
            lines.append(f"  waited longer for the same work: {subject_cost(entry)} "
                         "- a reading about the host, not the repository")
        else:
            lines.append(f"  same work came back sooner: {subject_cost(entry)} "
                         "- a reading about the host, not the repository")
    for subject in found["checks_added"]:
        lines.append(f"  added since: {subject}")
    for subject in found["checks_removed"]:
        lines.append(f"  gone since: {subject}")
    if len(lines) == 1:
        lines.append("  no check changed outcome, content or cost between these runs")
    return lines


def subject_cost(entry: dict[str, Any]) -> str:
    """One check's cost change, both numbers kept so the reader can judge it."""
    return f"{entry['subject']} {entry['was']:.3f}s -> {entry['now']:.3f}s"


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
