#!/usr/bin/env python3
"""Grade `STATUS.yaml`'s status fields against the typed crosswalk that says what they mean.

`STATUS.yaml` writes three kinds of statement about a subject into one flat namespace: a
general status, an owner acceptance carried by a packet, and a reversible ruling the file's
own comment says "is not owner acceptance and does not claim to be". Where two are written
for one subject the key is duplicated, a YAML reader keeps the last, and the earlier claim
disappears without a word. `scripts/lint.py` has named those eight duplicates as debt and
declined to repair them, correctly: repairing means deciding how two kinds of claim about
one subject are represented, which is a governing choice.

`contracts/status-claims.json` records that choice as a crosswalk. It changes no prose. It
says, for each field and value the document already carries, which subject the claim is
about, which kind of claim it is, and where a ladder position is asserted, which one. Under
that typing the eight duplicates are not duplicates: they are one subject carrying two kinds
of claim, and neither erases the other.

This module owns reading the document and running the table. `scripts/sovstatus/refusals.py`
owns what counts as a wrong entry. `check` grades the live file in both directions - an
untyped field and a stale entry are both defects - and `selfcheck` proves every declared
refusal fires against a controlled case, alone, so the table cannot quietly stop refusing.

Scope, stated so it is not mistaken for more: this checks what STATUS.yaml *asserts*, never
whether the assertion holds. `scripts/sov_standing.py` is the check that a WITNESSED or
RATIFIED claim has a witness record behind it; this one is about representation.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from sovstatus.refusals import CHECKS, malformed

ROOT = Path(__file__).resolve().parent.parent
CONTRACT = ROOT / "contracts" / "status-claims.json"
STATUS = ROOT / "STATUS.yaml"
CORPUS = ROOT / "conformance" / "fixtures" / "status-claims" / "cases.json"

FIELD = re.compile(r"^([a-z0-9_]+_status):\s*(\S+)\s*$")
# Deliberately far looser than FIELD, and anchored on a real `_status` suffix. Three
# drafts of this pattern were each taught the shapes the previous witness reported;
# this one takes any key ending in `_status` however it is written - quoted, hyphenated,
# dotted, in a list item, in a flow mapping, in any case, at any indent, with or without
# a space before the colon. Requiring something before the underscore stops it firing on
# a bare `status:` key, which is not a status field and which no entry could ever match.
LOOSE = re.compile(r"^[\s\-{\[,]*[\"']?[A-Za-z0-9][A-Za-z0-9_.\-/]*_[Ss][Tt][Aa][Tt][Uu][Ss][\"']?\s*:")


def load_contract(path: Path = CONTRACT) -> dict:
    """The declared crosswalk and the vocabulary it is written in."""
    return json.loads(path.read_text(encoding="utf-8"))


def read_fields(text: str) -> list[tuple[str, str]]:
    """Every column-zero `*_status` field and its value, in document order.

    Read line by line rather than through a YAML parser on purpose: a parser collapses the
    duplicated keys before this check can see them, which is the defect being typed.
    """
    matches = (FIELD.match(line) for line in text.splitlines())
    return [(m.group(1), m.group(2)) for m in matches if m]


def unreadable_lines(text: str) -> list[str]:
    """Lines naming a status field the strict reader cannot parse.

    Without this the reader silently defines its own scope: a field it cannot parse would
    be invisible and would earn no `FIELD_UNTYPED`. The detector is deliberately looser
    than the reader, so the gap between them is a refusal rather than a blind spot.
    """
    return [line for line in text.splitlines() if LOOSE.match(line) and not FIELD.match(line)]


def grade(fields: list[tuple[str, str]], entries: list[dict], contract: dict,
          text: str = "") -> list[str]:
    """Every refusal the field set and crosswalk earn together, in declared order.

    A malformed entry short-circuits the rest: the checks below index into fields it does
    not have, and a traceback is a worse answer than a refusal.
    """
    defects = [f"FIELD_UNREADABLE: {line.strip()!r} names a status field this reader cannot "
               "parse; it would otherwise be invisible"
               for line in unreadable_lines(text)]
    shape = malformed(fields, entries, contract)
    if shape:
        return defects + shape
    return defects + [d for check in CHECKS for d in check(fields, entries, contract)]


def selfcheck(corpus_path: Path = CORPUS, contract: dict | None = None) -> list[str]:
    """Prove each declared refusal fires on its case, alone, and the positive case earns none."""
    contract = contract or load_contract()
    cases = json.loads(corpus_path.read_text(encoding="utf-8"))["cases"]
    declared = set(contract["refusals"])
    exercised: set[str] = set()
    defects: list[str] = []
    for case in cases:
        text = "\n".join(case["status_lines"])
        codes = {d.split(":", 1)[0]
                 for d in grade(read_fields(text), case["crosswalk"], contract, text)}
        expected = case["expect"]
        if expected is None:
            if codes:
                defects.append(f"{case['id']}: expected no refusal and earned {sorted(codes)}")
        elif codes != {expected}:
            defects.append(f"{case['id']}: expected exactly {expected} and earned "
                           f"{sorted(codes) or 'none'}; a case firing for a second reason "
                           "does not prove the one it names")
        else:
            exercised.add(expected)
    # A positive case over an empty document and an empty crosswalk satisfies every rule
    # and proves nothing; a second witness showed that such a corpus still passes.
    if not any(c["expect"] is None and c["crosswalk"] and c["status_lines"] for c in cases):
        defects.append("no positive case types a real entry; an empty one proves nothing")
    defects += [f"{code} is declared and no case proves it fires"
                for code in sorted(declared - exercised)]
    defects += [f"{code} fires and the contract does not declare it"
                for code in sorted(exercised - declared)]
    return defects


def _cmd_check(_args: argparse.Namespace) -> int:
    contract = load_contract()
    text = STATUS.read_text(encoding="utf-8")
    defects = grade(read_fields(text), contract["crosswalk"], contract, text)
    if defects:
        print("status claims: DEFECTS")
        for defect in defects:
            print(f"  {defect}")
        return 1
    entries = contract["crosswalk"]
    print(f"status claims: {len(entries)} typed against "
          f"{len({e['subject'] for e in entries})} subjects, no defects")
    return 0


def _cmd_selfcheck(_args: argparse.Namespace) -> int:
    defects = selfcheck()
    if defects:
        print("status-claims selfcheck: DEFECTS")
        for defect in defects:
            print(f"  {defect}")
        return 1
    print(f"status-claims selfcheck: {len(load_contract()['refusals'])} refusals each fire")
    return 0


def _cmd_show(args: argparse.Namespace) -> int:
    entries = load_contract()["crosswalk"]
    wanted = [e for e in entries if args.subject in (None, e["subject"])]
    if not wanted:
        print(f"no subject {args.subject!r}; try one of "
              f"{', '.join(sorted({e['subject'] for e in entries})[:6])} ...")
        return 1
    for subject in sorted({e["subject"] for e in wanted}):
        print(subject)
        for entry in [e for e in wanted if e["subject"] == subject]:
            print(f"  {entry['claim_kind']:<16} {entry['detail']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check", help="grade STATUS.yaml against the crosswalk")
    check.set_defaults(func=_cmd_check)
    self_ = subparsers.add_parser("selfcheck", help="prove every declared refusal fires")
    self_.set_defaults(func=_cmd_selfcheck)
    show = subparsers.add_parser("show", help="read the typed claims for a subject")
    show.add_argument("subject", nargs="?", default=None)
    show.set_defaults(func=_cmd_show)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
