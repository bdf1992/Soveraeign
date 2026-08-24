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

    python scripts/sov_docket.py queue      the one merged list, and for whom
    python scripts/sov_docket.py unrouted   open records with no question routed at them
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
NL = chr(10)
_OWNER_SECTION = re.compile(r"^## What still waits on Bdo\s*$", re.M)
STATUS_LINE = re.compile(r"^Status:\s*`([^`]+)`", re.M)


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def records() -> list[dict[str, str]]:
    """Every decision record, with the status line it carries, in number order."""
    found = []
    for path in sorted(DECISIONS.glob("0*.md")):
        text = path.read_text(encoding="utf-8")
        match = STATUS_LINE.search(text)
        found.append({"id": path.stem[:4], "slug": path.stem[5:], "path": str(path),
                      "status_line": match.group(1) if match else "",
                      "enumerates": _OWNER_SECTION.search(text) is not None})
    return found


def graded() -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Each record joined to its standing and to the questions routed against it.

    The unit is a question, not a record. A record may carry several with
    different answers, so `questions` is a list and may be empty. A status line
    absent from the crosswalk is returned separately rather than guessed at.
    """
    standing = _read(STANDING)
    routed = _read(ROUTING)["questions"]
    rows, unknown = [], []
    for record in records():
        name = standing["crosswalk"].get(record["status_line"])
        if name is None:
            unknown.append(record)
            continue
        mine = [dict(entry, question_id=qid) for qid, entry in sorted(routed.items())
                if entry["record"] == record["id"]]
        rows.append({**record, "standing": name,
                     "settled": standing["standings"][name]["settled"], "questions": mine})
    return rows, unknown


def open_questions() -> list[dict[str, Any]]:
    """Every open question, from a decision record or from anywhere else.

    Bdo ruled on 2026-08-24 that he wants one merged list, so a question from a
    commit-range sweep sits beside one from a record and is counted once. A
    question carrying `same_as` is a second source reaching a question already
    here; it is kept so the agreement stays visible and excluded from counts.
    """
    rows, _ = graded()
    from_records = [dict(entry, slug=row["slug"]) for row in rows if not row["settled"]
                    for entry in row["questions"]]
    routed = _read(ROUTING)["questions"]
    elsewhere = [dict(entry, question_id=qid, slug=_short_source(entry))
                 for qid, entry in sorted(routed.items()) if entry.get("record") is None]
    return [entry for entry in from_records + elsewhere if not entry.get("same_as")]


def duplicates() -> list[dict[str, Any]]:
    """Questions two sources reached independently, kept rather than deleted."""
    routed = _read(ROUTING)["questions"]
    return [dict(entry, question_id=qid) for qid, entry in sorted(routed.items())
            if entry.get("same_as")]


def _short_source(entry: dict[str, Any]) -> str:
    source = (entry.get("source") or "").rsplit("/", 1)[-1].removesuffix(".md")
    return f"{source} {entry.get('source_item', '')}".strip()


def _open_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if not row["settled"]]


def _line(entry: dict[str, Any]) -> str:
    mark = "  [STATUS.yaml already answers this]" if entry.get("already_recorded_as") else ""
    return f"  {entry['question_id']}  {entry['question'][:58]:60}{mark}"


def queue() -> int:
    """Print every open question, split by who can settle it."""
    rows, unknown = graded()
    unsettled = _open_rows(rows)
    asked = open_questions()
    owner = [entry for entry in asked if entry["reaches_owner"]]
    below = [entry for entry in asked if not entry["reaches_owner"]]
    stale = [entry for entry in owner if entry.get("already_recorded_as")]
    real = [entry for entry in owner if not entry.get("already_recorded_as")]

    dupes = duplicates()
    print(f"{len(rows)} decision records, {len(unsettled)} standing PROPOSED. "
          f"One merged list: {len(asked)} open questions, {len(dupes)} of them reached twice "
          f"and counted once." + NL)
    print(f"== genuinely waiting on Bdo: {len(real)} ==")
    for entry in real:
        print(_line(entry))
        print(f"        {entry['reason']}")
        print(f"        -> {entry['action_if_confirmed']}")
    print(NL + f"== his answer is already in STATUS.yaml; the record's status line lags: "
          f"{len(stale)} ==")
    for entry in stale:
        print(_line(entry) + NL + f"        {entry['already_recorded_as']}")
    print(NL + f"== settleable below the owner: {len(below)} ==")
    for entry in below:
        print(_line(entry))
        print(f"        {entry['reason'][:96]}")
    contested = [entry for entry in asked if entry.get("contested_by")]
    if contested:
        print(NL + f"== routed, and someone has pushed back on the routing: {len(contested)} ==")
        for entry in contested:
            print(_line(entry))
            print(f"        {entry['contested_by'][:150]}")
    bare = [row for row in unsettled if not row["questions"]]
    if bare:
        print(NL + f"== open records with no question routed against them: {len(bare)} ==")
        for row in bare:
            print(f"  {row['id']}  {row['slug']}")
    if unknown:
        print(NL + f"== status line not in the crosswalk: {len(unknown)} ==")
        for row in unknown:
            print(f"  {row['id']}  {row['status_line']}")
    print(NL + "== counts, so nobody has to add them up ==")
    print(f"  {len(owner)} questions reach Bdo at all")
    print(f"  {len(stale)} of those he has already answered; the record's status line lags")
    print(f"  {len(real)} genuinely await a judgement from him")
    sources = sorted({entry.get("source") or "decisions/" for entry in asked})
    print(f"  merged from {len(sources)} sources: " + ", ".join(sources))
    enumerating = len([row for row in unsettled if row["enumerates"]])
    print(f"  {enumerating} of {len(unsettled)} open records state their own owner questions")
    headline = [entry for entry in asked if entry["enumerated_from"] == "headline"]
    print(NL + f"{len(headline)} of {len(asked)} questions come from a record that does not "
          f"enumerate its own; a further question such a record carries is not visible here.")
    print("Standing note: routing entries are claims with reasons, not settlements. "
          "Nothing here ratifies anything.")
    return 0


def unrouted() -> int:
    """List open records no question has been routed against."""
    rows, unknown = graded()
    bare = [row for row in _open_rows(rows) if not row["questions"]]
    for row in bare:
        print(f"{row['id']}  {row['slug']}  {row['status_line']}")
    for row in unknown:
        print(f"{row['id']}  {row['slug']}  UNKNOWN STATUS: {row['status_line']}")
    print(NL + f"{len(bare)} open records with no question, "
          f"{len(unknown)} with an undeclared status line")
    return 1 if (bare or unknown) else 0


def check() -> int:
    """The gate: the crosswalk is total, and every routed question is sound."""
    defects: list[str] = []
    standing = _read(STANDING)
    contract = _read(ROUTING)
    routed = contract["questions"]
    allowed = set(contract["entry_keys"])
    rows, unknown = graded()

    for row in unknown:
        defects.append(f"{row['id']}: status line not in the crosswalk: {row['status_line']!r}")

    known = {record["id"] for record in records()}
    categories = set(standing["owner_held_categories"])
    status_text = STATUS.read_text(encoding="utf-8")

    for qid, entry in sorted(routed.items()):
        if entry.get("record") is None:
            if not entry.get("source"):
                defects.append(f"{qid}: belongs to no record and names no source")
        elif entry["record"] not in known:
            defects.append(f"{qid}: names record {entry['record']!r}, which does not exist")
        if entry.get("same_as") and entry["same_as"] not in routed:
            defects.append(f"{qid}: same_as names {entry['same_as']!r}, which is not a question")
        for field in ("question", "enumerated_from", "reaches_owner", "categories",
                      "reason", "action_if_confirmed"):
            if field not in entry:
                defects.append(f"{qid}: has no {field}")
        if set(entry) - allowed:
            defects.append(f"{qid}: carries {sorted(set(entry) - allowed)} outside entry_keys")
        if entry.get("enumerated_from") not in ("record-section", "headline"):
            defects.append(f"{qid}: enumerated_from is {entry.get('enumerated_from')!r}")
        stray = set(entry.get("categories", [])) - categories
        if stray:
            defects.append(f"{qid}: undeclared owner-held category {sorted(stray)}")
        if entry.get("reaches_owner") and not entry.get("categories"):
            defects.append(f"{qid}: reaches the owner but names no category")
        if entry.get("categories") and not entry.get("reaches_owner"):
            defects.append(f"{qid}: names a category but does not reach the owner")
        recorded = entry.get("already_recorded_as")
        if recorded and recorded not in status_text:
            defects.append(f"{qid}: claims STATUS.yaml records {recorded!r}, and it does not")

    # A record that does not enumerate its own questions cannot have been split into
    # several here; claiming otherwise would assert a reading nobody did.
    for row in _open_rows(rows):
        headline = [entry for entry in row["questions"]
                    if entry["enumerated_from"] == "headline"]
        if len(row["questions"]) > 1 and headline:
            defects.append(f"{row['id']}: several questions, but {len(headline)} claim to come "
                           f"from a record that does not enumerate its own")

    # Reported, never failed. A gate that turns red because someone else wrote a
    # document is a gate that gets deleted rather than obeyed, and routing another
    # author's record means inventing their questions - the exact failure the rule
    # exists to end. scripts/lint.py names module debt the same way.
    rule = standing["owner_questions_section"]
    threshold = rule["required_from_record"]
    silent = [record["id"] for record in records()
              if record["id"] >= threshold and not record["enumerates"]]

    for defect in defects:
        print("DEFECT: " + defect)
    if defects:
        print(NL + f"FAIL: {len(defects)} defects in the acceptance routing")
        return 1
    for identifier in silent:
        print(f"DEBT: {identifier} carries no '{rule['heading']}' section, minted at or after "
              f"{threshold}. Reported, not failed: routing it here would mean inventing its "
              f"author's questions.")
    unsettled = _open_rows(rows)
    covered = len([row for row in unsettled if row["questions"]])
    asked = len(open_questions())
    print(f"PASS: {len(rows)} decision records, {len(unsettled)} open, {covered} with a routed "
          f"question; one merged list of {asked} open questions from "
          f"{len({e.get('source') or 'decisions/' for e in open_questions()})} sources")
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
