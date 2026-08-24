"""The owner's queue, rebuilt from the records rather than written out by hand.

`decisions/0023-acceptance-not-approval.md` requires every acceptance request to
arrive as an evidence-backed packet. `decisions/0033-close-the-founding-docket.md`
Ruling 1 says a question is settled at the lowest tier that can produce evidence
defeating the alternatives, and only owner-held intent, naming, external
commitment, irreversible effect, and the acceptance standing itself reach Bdo.

Neither had a reader. `reports/2026-08-23-ratification-docket.md` is a hand-written
snapshot that was stale within hours, because a docket assembled by hand rots the
moment a record is minted. This builds the same thing as a projection over
`decisions/`, `contracts/decision-standing.json` and
`contracts/acceptance-routing.json`, so it is current whenever it is run.

It settles nothing. Every routing entry is a claim with a reason, and Bdo may
reject any of them.

    python scripts/sov_docket.py queue      what is genuinely open, and for whom
    python scripts/sov_docket.py unrouted   proposals no routing entry covers
    python scripts/sov_docket.py check      the gate: crosswalk total, routing sound
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
DECISIONS = ROOT / "decisions"
STANDING = ROOT / "contracts" / "decision-standing.json"
ROUTING = ROOT / "contracts" / "acceptance-routing.json"
STATUS = ROOT / "STATUS.yaml"
STATUS_LINE = re.compile(r"^Status:\s*`([^`]+)`", re.M)


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def records() -> list[dict[str, str]]:
    """Every decision record, with the status line it carries, in number order."""
    found = []
    for path in sorted(DECISIONS.glob("0*.md")):
        match = STATUS_LINE.search(path.read_text(encoding="utf-8"))
        found.append({"id": path.stem[:4], "slug": path.stem[5:], "path": str(path),
                      "status_line": match.group(1) if match else ""})
    return found


def graded() -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Each record joined to its standing and its routing entry.

    A status line absent from the crosswalk is returned separately rather than
    guessed at: this contract cannot decide what a phrasing nobody declared means.
    """
    standing = _read(STANDING)
    routing = _read(ROUTING)["routing"]
    rows, unknown = [], []
    for record in records():
        name = standing["crosswalk"].get(record["status_line"])
        if name is None:
            unknown.append(record)
            continue
        rows.append({**record, "standing": name,
                     "settled": standing["standings"][name]["settled"],
                     "routing": routing.get(record["id"])})
    return rows, unknown


def _open_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if not row["settled"]]


def _line(row: dict[str, Any]) -> str:
    entry = row["routing"] or {}
    recorded = entry.get("already_recorded_as")
    mark = "  [STATUS.yaml already answers this]" if recorded else ""
    return f"  {row['id']}  {row['slug'][:44]:46}{mark}"


def queue() -> int:
    """Print what is open, split by who can settle it."""
    rows, unknown = graded()
    unsettled = _open_rows(rows)
    routed = [row for row in unsettled if row["routing"]]
    owner = [row for row in routed if row["routing"]["reaches_owner"]]
    below = [row for row in routed if not row["routing"]["reaches_owner"]]
    stale = [row for row in owner if row["routing"].get("already_recorded_as")]
    real = [row for row in owner if not row["routing"].get("already_recorded_as")]

    print(f"{len(rows)} decision records, {len(unsettled)} standing PROPOSED\n")
    print(f"== genuinely waiting on Bdo: {len(real)} ==")
    for row in real:
        print(_line(row))
        print(f"        {row['routing']['reason']}")
        print(f"        -> {row['routing']['action_if_confirmed']}")
    print(f"\n== his answer is already in STATUS.yaml; the record's status line lags: "
          f"{len(stale)} ==")
    for row in stale:
        print(_line(row) + f"\n        {row['routing']['already_recorded_as']}")
    print(f"\n== settleable below the owner: {len(below)} ==")
    for row in below:
        print(_line(row))
        print(f"        {row['routing']['reason'][:96]}")
    contested = [row for row in routed if row["routing"].get("contested_by")]
    if contested:
        print(f"\n== routed, and someone has pushed back on the routing: {len(contested)} ==")
        for row in contested:
            print(_line(row))
            print(f"        {row['routing']['contested_by'][:150]}")
    unrouted = [row for row in unsettled if not row["routing"]]
    if unrouted:
        print(f"\n== unrouted, so nobody can say whose they are: {len(unrouted)} ==")
        for row in unrouted:
            print(_line(row))
    if unknown:
        print(f"\n== status line not in the crosswalk: {len(unknown)} ==")
        for row in unknown:
            print(f"  {row['id']}  {row['status_line']}")
    print("\nStanding note: routing entries are claims with reasons, not settlements. "
          "Nothing here ratifies anything.")
    return 0


def unrouted() -> int:
    """List proposals no routing entry covers."""
    rows, unknown = graded()
    missing = [row for row in _open_rows(rows) if not row["routing"]]
    for row in missing:
        print(f"{row['id']}  {row['slug']}  {row['status_line']}")
    for row in unknown:
        print(f"{row['id']}  {row['slug']}  UNKNOWN STATUS: {row['status_line']}")
    print(f"\n{len(missing)} unrouted, {len(unknown)} with an undeclared status line")
    return 1 if (missing or unknown) else 0


def check() -> int:
    """The gate: the crosswalk is total, and every routing entry is sound."""
    defects: list[str] = []
    standing = _read(STANDING)
    routing = _read(ROUTING)["routing"]
    rows, unknown = graded()

    for row in unknown:
        defects.append(f"{row['id']}: status line not in the crosswalk: {row['status_line']!r}")

    known = {record["id"] for record in records()}
    for identifier in sorted(set(routing) - known):
        defects.append(f"routing names {identifier}, which is not a decision record")

    categories = set(standing["owner_held_categories"])
    status_text = STATUS.read_text(encoding="utf-8")
    for identifier, entry in sorted(routing.items()):
        for field in ("reaches_owner", "categories", "reason", "action_if_confirmed"):
            if field not in entry:
                defects.append(f"{identifier}: routing entry has no {field}")
        stray = set(entry.get("categories", [])) - categories
        if stray:
            defects.append(f"{identifier}: undeclared owner-held category {sorted(stray)}")
        if entry.get("reaches_owner") and not entry.get("categories"):
            defects.append(f"{identifier}: reaches the owner but names no category")
        if entry.get("categories") and not entry.get("reaches_owner"):
            defects.append(f"{identifier}: names a category but does not reach the owner")
        recorded = entry.get("already_recorded_as")
        if recorded and recorded not in status_text:
            defects.append(f"{identifier}: claims STATUS.yaml records {recorded!r}, and it does not")

    for defect in defects:
        print("DEFECT: " + defect)
    if defects:
        print(f"\nFAIL: {len(defects)} defects in the acceptance routing")
        return 1
    unsettled = _open_rows(rows)
    covered = len([row for row in unsettled if row["routing"]])
    print(f"PASS: {len(rows)} decision records, {len(unsettled)} open, {covered} routed, "
          f"{len(unsettled) - covered} unrouted")
    print("Standing note: routing is a declared claim about who settles what. "
          "It grades no decision as right and settles none of them.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sov-docket", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("queue", help="what is open, and for whom")
    sub.add_parser("unrouted", help="proposals no routing entry covers")
    sub.add_parser("check", help="the gate: crosswalk total, routing sound")
    args = parser.parse_args(argv)
    return {"queue": queue, "unrouted": unrouted, "check": check}[args.command]()


if __name__ == "__main__":
    sys.exit(main())
