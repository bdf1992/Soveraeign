#!/usr/bin/env python3
"""Read the F2 milestone gate, exactly as ``SPEC.md`` states it.

``ROADMAP.md`` F2 exits when "every normative predicate has at least one
positive and one defeating fixture" and "the suite can be bound to more than
one implementation". ``SPEC.md`` Conformance boundary says the same thing in
the normative voice. Neither sentence is checked anywhere: the oracle measures
coverage per *requirement* (nine of them), while ``SPEC.md`` writes its
predicates one granularity below that, and adds a transition contract and an
interface-parity list that are normative too.

This module enumerates every normative predicate in ``SPEC.md``, reads which
ones the conformance corpus declares it covers, and reports the difference. It
settles nothing and edits nothing: it reads the specification and the corpus
and prints the distance between them, so an unattended loop has a stop
condition it cannot argue with.

Every read is local. Nothing here reaches the coordination surface.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import json
import re


ROOT = Path(__file__).resolve().parents[1]

SPEC = "SPEC.md"
CASES = "conformance/oracle-controls.json"
OBSERVATIONS = "conformance/observations"

PREDICATES_HEADING = "## Requirement predicates"
TRANSITIONS_HEADING = "## Transition contract"
PARITY_HEADING = "## Interface parity"

#: Both polarities SPEC.md requires of every normative predicate.
REQUIRED_POLARITIES = frozenset({"positive", "defeating"})

#: F2 also requires the suite to bind to more than one implementation.
REQUIRED_PARTICIPANTS = 2

#: Families are ranked so the loop closes the requirement predicates first.
FAMILY_ORDER = ("requirement", "transition", "parity")


def _text(relative: str) -> str:
    """Read repository text as UTF-8 without newline translation."""
    return (ROOT / relative).read_bytes().decode("utf-8")


def _section(text: str, heading: str) -> str:
    """The body of one ``##`` section, up to the next ``##`` heading."""
    if heading not in text:
        return ""
    body = text.split(heading, 1)[1]
    parts = re.split(r"^## ", body, maxsplit=1, flags=re.M)
    return parts[0]


def _bullets(block: str) -> list[str]:
    """Top-level ``- `` bullets in a block, rejoining their wrapped lines."""
    bullets: list[str] = []
    for line in block.splitlines():
        if line.startswith("- "):
            bullets.append(line[2:].strip())
        elif line.startswith("  ") and bullets and line.strip():
            bullets[-1] = bullets[-1] + " " + line.strip()
    return bullets


def requirement_predicates(spec_text: str) -> list[dict[str, str]]:
    """One entry per bullet under ``## Requirement predicates``.

    SPEC.md writes these one granularity below PROD-I-<n>: the requirement is
    the heading, and each bullet is a separately defeatable claim.
    """
    block = _section(spec_text, PREDICATES_HEADING)
    predicates: list[dict[str, str]] = []
    for match in re.finditer(r"^### (PROD-I-\d+)[^\n]*\n(.*?)(?=^### |\Z)", block, re.M | re.S):
        requirement = match.group(1)
        number = requirement.rsplit("-", 1)[1]
        for index, bullet in enumerate(_bullets(match.group(2)), start=1):
            predicates.append({
                "id": f"PRED-I-{number}.{index}",
                "family": "requirement",
                "requirement": requirement,
                "text": bullet,
            })
    return predicates


def transition_predicates(spec_text: str) -> list[dict[str, str]]:
    """One entry per row of the ``## Transition contract`` table.

    Each row states a precondition, a commit, and a refusal. The commit path is
    the positive fixture and the refusal path is the defeating one, so a row is
    a normative predicate in the sense the Conformance boundary means.
    """
    block = _section(spec_text, TRANSITIONS_HEADING)
    predicates: list[dict[str, str]] = []
    for line in block.splitlines():
        match = re.match(r"^\|\s*`([a-z_]+)`\s*\|(.+?)\|(.+?)\|(.+?)\|\s*$", line)
        if not match:
            continue
        name, pre, commit, refusal = (part.strip() for part in match.groups())
        predicates.append({
            "id": f"TRANS-{name}",
            "family": "transition",
            "requirement": "SPEC transition contract",
            "text": f"{name}: {pre} -> {commit}; refuses {refusal}",
        })
    return predicates


def parity_predicates(spec_text: str) -> list[dict[str, str]]:
    """One entry per bullet under ``## Interface parity``."""
    block = _section(spec_text, PARITY_HEADING)
    predicates: list[dict[str, str]] = []
    for index, bullet in enumerate(_bullets(block), start=1):
        predicates.append({
            "id": f"PARITY-{index}",
            "family": "parity",
            "requirement": "SPEC interface parity",
            "text": bullet.rstrip(";."),
        })
    return predicates


def normative_predicates(spec_text: str) -> list[dict[str, str]]:
    """Every normative predicate SPEC.md states above its Conformance boundary."""
    return (requirement_predicates(spec_text)
            + transition_predicates(spec_text)
            + parity_predicates(spec_text))


def declared_coverage(cases: list[dict]) -> dict[str, set[str]]:
    """Predicate id -> the polarities the corpus declares it covers.

    A case declares its predicates in an optional ``predicates`` array. A case
    without one covers nothing at this granularity: the corpus is not credited
    for coverage it has not claimed in machine-readable form.
    """
    coverage: dict[str, set[str]] = {}
    for case in cases:
        polarity = case.get("polarity")
        if polarity not in REQUIRED_POLARITIES:
            continue
        for predicate_id in case.get("predicates") or []:
            coverage.setdefault(str(predicate_id), set()).add(polarity)
    return coverage


def bound_participants() -> list[str]:
    """Distinct participants that have supplied a participant observation set."""
    directory = ROOT / OBSERVATIONS
    if not directory.is_dir():
        return []
    participants: set[str] = set()
    for path in sorted(directory.glob("*-observation.json")):
        try:
            document = json.loads(path.read_bytes().decode("utf-8"))
        except (ValueError, OSError):
            continue
        entries = document if isinstance(document, list) else [document]
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            name = entry.get("participant_id") or entry.get("participant")
            participants.add(str(name) if name else path.name.split("-observation")[0])
    return sorted(participants)


def unknown_declarations(predicates: list[dict[str, str]],
                         coverage: dict[str, set[str]]) -> list[str]:
    """Predicate ids the corpus claims that ``SPEC.md`` does not state.

    A case that cites a predicate the specification no longer contains is a
    defect in the corpus, not silent coverage.
    """
    known = {predicate["id"] for predicate in predicates}
    return sorted(predicate_id for predicate_id in coverage if predicate_id not in known)


def read_gate() -> dict:
    """The whole F2 gate as one report: covered, missing, participants, verdict."""
    spec_text = _text(SPEC)
    predicates = normative_predicates(spec_text)
    cases = json.loads(_text(CASES))
    coverage = declared_coverage(cases)
    participants = bound_participants()

    rows = []
    for predicate in predicates:
        have = coverage.get(predicate["id"], set())
        rows.append({
            **predicate,
            "positive": "positive" in have,
            "defeating": "defeating" in have,
            "missing": sorted(REQUIRED_POLARITIES - have),
        })

    open_rows = [row for row in rows if row["missing"]]
    orphans = unknown_declarations(predicates, coverage)
    participants_ok = len(participants) >= REQUIRED_PARTICIPANTS
    closed = not open_rows and not orphans and participants_ok

    return {
        "gate": "F2",
        "criterion": "every normative predicate has a positive and a defeating fixture; "
                     "the suite binds to more than one implementation",
        "closed": closed,
        "predicates_total": len(rows),
        "predicates_covered": len(rows) - len(open_rows),
        "predicates_open": len(open_rows),
        "by_family": {
            family: {
                "total": sum(1 for row in rows if row["family"] == family),
                "open": sum(1 for row in rows if row["family"] == family and row["missing"]),
            }
            for family in FAMILY_ORDER
        },
        "bound_participants": participants,
        "bound_participants_ok": participants_ok,
        "corpus_cases": len(cases),
        "orphan_declarations": orphans,
        "open": open_rows,
    }


def rank(report: dict, limit: int) -> list[dict]:
    """The next predicates to close, requirement family first, then SPEC order."""
    order = {family: index for index, family in enumerate(FAMILY_ORDER)}
    ordered = sorted(report["open"], key=lambda row: order.get(row["family"], 99))
    return ordered[:limit] if limit > 0 else ordered


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true", dest="as_json",
                        help="emit the whole gate report as JSON")
    parser.add_argument("--next", type=int, default=0, metavar="N",
                        help="print only the next N predicates to close")
    args = parser.parse_args()

    report = read_gate()

    if args.as_json:
        if args.next:
            report = {**report, "open": rank(report, args.next)}
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["closed"] else 1

    print(f"F2 gate: {report['predicates_covered']}/{report['predicates_total']} "
          f"normative predicates carry both fixtures")
    for family in FAMILY_ORDER:
        counts = report["by_family"][family]
        covered = counts["total"] - counts["open"]
        print(f"  {family:12} {covered:3}/{counts['total']:<3} covered")
    names = ", ".join(report["bound_participants"]) or "none"
    print(f"  participants  {len(report['bound_participants'])}/{REQUIRED_PARTICIPANTS} bound ({names})")
    for predicate_id in report["orphan_declarations"]:
        print(f"  ORPHAN  {predicate_id} is declared by the corpus but absent from SPEC.md")
    for row in rank(report, args.next):
        missing = "+".join(row["missing"])
        print(f"  OPEN    {row['id']:22} missing {missing:20} {row['text'][:60]}")
    print(f"{'CLOSED' if report['closed'] else 'OPEN'}: F2 milestone gate")
    print("Standing note: this reads the gate; closing it is evidence, and ratifying it is Bdo's.")
    return 0 if report["closed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
