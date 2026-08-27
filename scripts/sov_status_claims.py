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

This module makes the crosswalk fire. `check` grades the live file against it in both
directions - an untyped field and a stale entry are both defects. `selfcheck` proves every
declared refusal fires against a controlled case, so the table cannot quietly stop refusing.

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

ROOT = Path(__file__).resolve().parent.parent
CONTRACT = ROOT / "contracts" / "status-claims.json"
STATUS = ROOT / "STATUS.yaml"
CORPUS = ROOT / "conformance" / "fixtures" / "status-claims" / "cases.json"

FIELD = re.compile(r"^([a-z0-9_]+_status):\s*(\S+)\s*$")
ACCEPTANCE_VALUE = re.compile(r"^OWNER_ACCEPTED_A\d")


def load_contract(path: Path = CONTRACT) -> dict:
    """The declared crosswalk and the vocabulary it is written in."""
    return json.loads(path.read_text(encoding="utf-8"))


def read_fields(text: str) -> list[tuple[str, str]]:
    """Every column-zero `*_status` field and its value, in document order.

    Read line by line rather than through a YAML parser on purpose: a parser collapses the
    duplicated keys before this check can see them, which is the defect being typed.
    """
    return [(m.group(1), m.group(2)) for m in (FIELD.match(line) for line in text.splitlines()) if m]


def token_asserts(value: str, standing: str) -> bool:
    """Whether `value` carries `standing` as a whole token that is not denied.

    `NOT_WITNESSED` contains the token `WITNESSED` and asserts the opposite (CLAUDE.md T3),
    so a token preceded by `NOT` is a denial rather than a claim.
    """
    tokens = value.upper().split("_")
    return any(
        token == standing and (index == 0 or tokens[index - 1] != "NOT")
        for index, token in enumerate(tokens)
    )


def _untyped(fields: list[tuple[str, str]], entries: list[dict], _c: dict) -> list[str]:
    declared = {(e["field"], e["value"]) for e in entries}
    return [f"FIELD_UNTYPED: STATUS.yaml carries {f}: {v} and the crosswalk does not type it"
            for f, v in fields if (f, v) not in declared]


def _unmatched(fields: list[tuple[str, str]], entries: list[dict], _c: dict) -> list[str]:
    present = set(fields)
    return [f"ENTRY_UNMATCHED: the crosswalk types {e['field']}: {e['value']} "
            "and STATUS.yaml does not carry it"
            for e in entries if (e["field"], e["value"]) not in present]


def _collision(_f: list[tuple[str, str]], entries: list[dict], _c: dict) -> list[str]:
    seen: dict[tuple[str, str], int] = {}
    for entry in entries:
        key = (entry["subject"], entry["claim_kind"])
        seen[key] = seen.get(key, 0) + 1
    return [f"CLAIM_KIND_COLLISION: subject {subject} carries {count} {kind} claims; "
            "one subject holds at most one claim of a kind"
            for (subject, kind), count in sorted(seen.items()) if count > 1]


def _not_in_ladder(_f: list[tuple[str, str]], entries: list[dict], contract: dict) -> list[str]:
    ladder = contract["artifact_standing_ladder"]
    return [f"STANDING_NOT_IN_LADDER: {e['field']} declares standing {e['artifact_standing']!r}, "
            f"which is not one of {', '.join(ladder)}"
            for e in entries
            if e["artifact_standing"] is not None and e["artifact_standing"] not in ladder]


def _token_absent(_f: list[tuple[str, str]], entries: list[dict], _c: dict) -> list[str]:
    defects = []
    for entry in entries:
        if entry["standing_source"] != "TOKEN":
            continue
        standing = entry["artifact_standing"]
        if standing is None:
            defects.append(f"STANDING_TOKEN_ABSENT: {entry['field']} declares a TOKEN source "
                           "and no standing to find")
        elif not token_asserts(entry["value"], standing):
            defects.append(f"STANDING_TOKEN_ABSENT: {entry['field']} declares standing "
                           f"{standing} from a token, and {entry['value']} does not assert it")
    return defects


def _leading_untyped(_f: list[tuple[str, str]], entries: list[dict], contract: dict) -> list[str]:
    ladder = set(contract["artifact_standing_ladder"])
    return [f"LEADING_TOKEN_UNTYPED: {e['field']} begins with the ladder word "
            f"{e['value'].split('_')[0]} and declares source {e['standing_source']}"
            for e in entries
            if e["value"].upper().split("_")[0] in ladder and e["standing_source"] != "TOKEN"]


def _ruling_as_acceptance(_f: list[tuple[str, str]], entries: list[dict], _c: dict) -> list[str]:
    defects = []
    for entry in entries:
        value, kind = entry["value"], entry["claim_kind"]
        if value.startswith("RULED_") and kind == "OWNER_ACCEPTANCE":
            defects.append(f"RULING_TYPED_AS_ACCEPTANCE: {entry['field']} carries a RULED_ "
                           "value typed as owner acceptance")
        elif ACCEPTANCE_VALUE.match(value) and kind == "RULING":
            defects.append(f"RULING_TYPED_AS_ACCEPTANCE: {entry['field']} carries an accepted "
                           "packet value typed as a reversible ruling")
    return defects


CHECKS = (_untyped, _unmatched, _collision, _not_in_ladder,
          _token_absent, _leading_untyped, _ruling_as_acceptance)


def grade(fields: list[tuple[str, str]], entries: list[dict], contract: dict) -> list[str]:
    """Every refusal the field set and crosswalk earn together, in declared order."""
    return [defect for check in CHECKS for defect in check(fields, entries, contract)]


def selfcheck(corpus_path: Path = CORPUS, contract: dict | None = None) -> list[str]:
    """Prove each declared refusal fires on its case and the positive case earns none."""
    contract = contract or load_contract()
    cases = json.loads(corpus_path.read_text(encoding="utf-8"))["cases"]
    declared = set(contract["refusals"])
    exercised: set[str] = set()
    defects: list[str] = []
    for case in cases:
        fields = read_fields("\n".join(case["status_lines"]))
        codes = {d.split(":", 1)[0] for d in grade(fields, case["crosswalk"], contract)}
        expected = case["expect"]
        if expected is None:
            if codes:
                defects.append(f"{case['id']}: expected no refusal and earned {sorted(codes)}")
        elif expected not in codes:
            defects.append(f"{case['id']}: expected {expected} and earned {sorted(codes) or 'none'}")
        else:
            exercised.add(expected)
    for code in sorted(declared - exercised):
        defects.append(f"{code} is declared and no case proves it fires")
    for code in sorted(exercised - declared):
        defects.append(f"{code} fires and the contract does not declare it")
    return defects


def _cmd_check(_args: argparse.Namespace) -> int:
    contract = load_contract()
    defects = grade(read_fields(STATUS.read_text(encoding="utf-8")), contract["crosswalk"], contract)
    if defects:
        print("status claims: DEFECTS")
        for defect in defects:
            print(f"  {defect}")
        return 1
    entries = contract["crosswalk"]
    subjects = {e["subject"] for e in entries}
    print(f"status claims: {len(entries)} typed against {len(subjects)} subjects, no defects")
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
            standing = entry["artifact_standing"] or "-"
            print(f"  {entry['claim_kind']:<16} {standing:<9} {entry['detail']}")
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
