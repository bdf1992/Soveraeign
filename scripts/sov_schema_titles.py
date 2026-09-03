#!/usr/bin/env python3
"""Schema titles cite their decision; they do not restate its standing.

A schema title used to carry both: `"Soveraeign Authority Grant (PROPOSED,
decisions/0061)"`. The decision record is the one producer of a decision's
standing (`contracts/decision-standing.json`), so a word like PROPOSED sitting
inside a title is a second, uncoordinated copy of that fact - one that goes
stale the moment the record moves and nobody remembers to edit every title that
quoted it. `decisions/0061` itself is `OWNER-DIRECTED` today; the title that
used to cite it still said PROPOSED.

The fix keeps the citation, which is a pointer and cannot go stale by itself,
and drops the word. This module is the check that holds the fix in place: it
reads every `contracts/*.json` file's top-level `title`, and for each one

  - refuses a title that still asserts a standing word, cited decision or not;
  - for a title that cites `decisions/NNNN`, confirms the citation names a
    decision record that exists and whose status line
    `contracts/decision-standing.json` actually crosswalks, so a broken or
    unrecognised citation is reported rather than silently accepted.

It reads decision records and the crosswalk contract directly from disk; it
never reads a schema's own claim about being current, and it settles nothing
about whether a decision is right - only whether a title still claims to know.

    python scripts/sov_schema_titles.py check     the gate
    python scripts/sov_schema_titles.py list       every cited title, graded
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"
DECISIONS = ROOT / "decisions"
STANDING_PATH = CONTRACTS / "decision-standing.json"

CITATION_RE = re.compile(r"decisions/(\d{4})")
STATUS_LINE_RE = re.compile(r"^Status:\s*`([^`]+)`", re.M)
NL = chr(10)


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def forbidden_standing_words(standing: dict[str, Any]) -> tuple[str, ...]:
    """Every spelling of a decision standing a title must never carry.

    Built from the crosswalk's own canonical names rather than a second,
    hand-kept list, so a standing added to the contract is guarded here for
    free. Each name is offered in its record spelling (underscores) and its
    prose spelling (hyphens), since decision status lines use the latter
    (`OWNER-DIRECTED`) and a title that quoted one could use either.
    """
    words: set[str] = set()
    for name in standing["standings"]:
        words.add(name)
        words.add(name.replace("_", "-"))
    return tuple(sorted(words))


def _word_pattern(word: str) -> re.Pattern[str]:
    # A standing word is only ever written whole, in caps; match it as a
    # token so "RULED-BELOW" cannot be mistaken for a substring of prose.
    return re.compile(r"(?<![A-Z0-9_-])" + re.escape(word) + r"(?![A-Z0-9_-])")


def schema_titles(contracts_dir: Path = CONTRACTS) -> list[dict[str, Any]]:
    """Every `contracts/*.json` file that declares a top-level `title`, in name order."""
    found = []
    for path in sorted(contracts_dir.glob("*.json")):
        try:
            document = _read(path)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if not isinstance(document, dict):
            continue
        title = document.get("title")
        if not isinstance(title, str):
            continue
        found.append({"path": path, "name": path.name, "title": title})
    return found


def decision_status_line(decision_id: str, decisions_dir: Path = DECISIONS) -> str | None:
    """The `Status:` line the decision record with this four-digit id carries, or None."""
    matches = sorted(decisions_dir.glob(f"{decision_id}-*.md"))
    if not matches:
        return None
    text = matches[0].read_text(encoding="utf-8")
    match = STATUS_LINE_RE.search(text)
    return match.group(1) if match else None


def title_defects(entry: dict[str, Any], standing: dict[str, Any],
                   forbidden: tuple[str, ...], decisions_dir: Path = DECISIONS) -> list[str]:
    """Every defect one schema title carries: a bare standing word, or a citation
    that does not resolve to a decision record the crosswalk recognises."""
    defects = []
    title = entry["title"]
    carried = [word for word in forbidden if _word_pattern(word).search(title)]
    if carried:
        defects.append(
            f"{entry['name']}: title still asserts standing {carried} - the decision record "
            f"is the one producer of standing, not the title ({title!r})")
    for decision_id in CITATION_RE.findall(title):
        status_line = decision_status_line(decision_id, decisions_dir)
        if status_line is None:
            defects.append(f"{entry['name']}: cites decisions/{decision_id}, which does not exist")
            continue
        if status_line not in standing["crosswalk"]:
            defects.append(
                f"{entry['name']}: decisions/{decision_id} carries status "
                f"{status_line!r}, which is not in the decision-standing crosswalk")
    return defects


def graded(contracts_dir: Path = CONTRACTS, decisions_dir: Path = DECISIONS,
           standing_path: Path = STANDING_PATH) -> list[dict[str, Any]]:
    """Every schema title, joined to the decisions it cites and their current standing."""
    standing = _read(standing_path)
    rows = []
    for entry in schema_titles(contracts_dir):
        citations = []
        for decision_id in CITATION_RE.findall(entry["title"]):
            status_line = decision_status_line(decision_id, decisions_dir)
            name = standing["crosswalk"].get(status_line) if status_line else None
            citations.append({"decision": decision_id, "status_line": status_line,
                              "standing": name})
        rows.append({**entry, "citations": citations})
    return rows


def list_titles() -> int:
    """Print every schema title with the decisions it cites and their standing."""
    for row in graded():
        cites = ", ".join(
            f"decisions/{c['decision']} -> {c['standing'] or 'UNKNOWN'}" for c in row["citations"]
        ) or "no decision cited"
        print(f"{row['name']:40} {row['title']}")
        print(f"  {cites}")
    return 0


def check_tree(contracts_dir: Path = CONTRACTS, decisions_dir: Path = DECISIONS,
               standing_path: Path = STANDING_PATH) -> int:
    """The gate against an arbitrary tree: no title asserts a standing word, and every
    citation resolves. Parameterised so a test can grade a throwaway fixture tree
    instead of mutating the checked-in one."""
    standing = _read(standing_path)
    forbidden = forbidden_standing_words(standing)
    defects: list[str] = []
    titles = schema_titles(contracts_dir)
    for entry in titles:
        defects.extend(title_defects(entry, standing, forbidden, decisions_dir))

    for defect in defects:
        print("DEFECT: " + defect)
    if defects:
        print(NL + f"FAIL: {len(defects)} defects across {len(titles)} schema titles")
        return 1
    cited = len([e for e in titles if CITATION_RE.search(e["title"])])
    print(f"PASS: {len(titles)} schema titles, {cited} citing a decision, "
          "none asserting a standing word")
    print("Standing note: this grades whether a title still claims a standing. It settles "
          "no decision and grades none of them as right.")
    return 0


def check() -> int:
    """The gate: no title asserts a standing word, and every citation resolves."""
    return check_tree()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sov-schema-titles", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check", help="the gate: no standing word, every citation resolves")
    sub.add_parser("list", help="every schema title, joined to its cited decisions' standing")
    args = parser.parse_args(argv)
    return {"check": check, "list": list_titles}[args.command]()


if __name__ == "__main__":
    sys.exit(main())
