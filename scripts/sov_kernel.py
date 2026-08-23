#!/usr/bin/env python3
"""Project and check the kernel transition contract against `SPEC.md`.

`SPEC.md` fixes fourteen legal transitions in prose. Prose cannot be checked, so
this derives a machine-readable projection of that table into
`contracts/kernel-transitions.json`.

The projection is never authoritative. `SPEC.md` is. `selfcheck` re-derives the
table from `SPEC.md` and refuses when the projection disagrees, so editing one
without the other breaks the gate instead of the reader. Every read is local.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import argparse
import json
import re


ROOT = Path(__file__).resolve().parents[1]
PROJECTION = ROOT / "contracts" / "kernel-transitions.json"
TABLE_ID = "soveraeign-kernel-transitions/v1"

TABLE_HEADER = "| Transition | Preconditions | Commit | Refusal |"
# SPEC leaves three transitions an open reasoned refusal alongside any named code.
REASONED = "reasoned refusal"


def _read(path: Path) -> str:
    """Read repository text as UTF-8 without newline translation."""
    return path.read_bytes().decode("utf-8")


def _codes(cell: str) -> list[str]:
    """Named refusal codes in a SPEC refusal cell, in declared order."""
    return re.findall(r"`([A-Z_]+)`", cell)


def _split_semicolons(cell: str) -> list[str]:
    """SPEC states preconditions as a semicolon-separated list."""
    return [part.strip() for part in cell.split(";") if part.strip()]


def derive(spec_text: str) -> dict:
    """Build the projection from the SPEC.md transition contract table."""
    if TABLE_HEADER not in spec_text:
        raise SystemExit("FAIL: SPEC.md no longer contains the transition contract table")
    body = spec_text.split(TABLE_HEADER, 1)[1].splitlines()
    transitions: dict[str, dict] = {}
    order: list[str] = []
    for line in body[1:]:
        if not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 4 or all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        name = re.match(r"`([a-z_]+)`", cells[0])
        if not name:
            continue
        transitions[name.group(1)] = {
            "preconditions": _split_semicolons(cells[1]),
            "commit": cells[2].replace("`", ""),
            "refusal_codes": _codes(cells[3]),
            "reasoned_refusal_admitted": REASONED in cells[3],
        }
        order.append(name.group(1))

    every_code = sorted({code for t in transitions.values() for code in t["refusal_codes"]})
    return {
        "table_id": TABLE_ID,
        "governed_by": ["SPEC.md"],
        "note": ("Projection of the SPEC.md transition contract table. SPEC.md is "
                 "authoritative; this file is rebuildable and holds no standing. "
                 "scripts/sov_kernel.py selfcheck refuses when the two disagree."),
        "source_digest": sha256((ROOT / "SPEC.md").read_bytes()).hexdigest()[:16],
        "order": order,
        "refusal_codes": every_code,
        "transitions": transitions,
    }


def invariants(table: dict) -> list[str]:
    """Defects the projection must never carry, independent of SPEC drift."""
    defects = []
    transitions = table.get("transitions", {})
    if not transitions:
        defects.append("projection declares no transitions")
    for name, transition in sorted(transitions.items()):
        if not transition.get("preconditions"):
            defects.append(f"{name}: declares no precondition")
        if not transition.get("commit"):
            defects.append(f"{name}: declares no commit")
        if not transition["refusal_codes"] and not transition["reasoned_refusal_admitted"]:
            defects.append(f"{name}: declares no refusal path")
        for code in transition["refusal_codes"]:
            if code != code.upper():
                defects.append(f"{name}: refusal code {code} is not upper case")
    return defects


def compare(derived: dict, stored: dict) -> list[str]:
    """Differences between the live SPEC.md derivation and the stored projection."""
    defects = []
    if stored.get("table_id") != derived["table_id"]:
        defects.append(f"table_id drifted: stored {stored.get('table_id')!r}")
    if stored.get("source_digest") != derived["source_digest"]:
        defects.append(
            f"SPEC.md moved: projection records {stored.get('source_digest')}, "
            f"SPEC.md is now {derived['source_digest']} — rerun `sov_kernel.py sync`")
    live, kept = derived["transitions"], stored.get("transitions", {})
    for name in sorted(set(live) - set(kept)):
        defects.append(f"{name}: in SPEC.md, absent from the projection")
    for name in sorted(set(kept) - set(live)):
        defects.append(f"{name}: in the projection, absent from SPEC.md")
    for name in sorted(set(live) & set(kept)):
        for field in ("preconditions", "commit", "refusal_codes", "reasoned_refusal_admitted"):
            if live[name][field] != kept[name].get(field):
                defects.append(f"{name}.{field}: projection disagrees with SPEC.md")
    return defects


def command_sync(_: argparse.Namespace) -> int:
    table = derive(_read(ROOT / "SPEC.md"))
    defects = invariants(table)
    if defects:
        for defect in defects:
            print(f"FAIL: {defect}")
        return 1
    PROJECTION.write_bytes(
        (json.dumps(table, indent=2, sort_keys=False, ensure_ascii=False) + "\n").encode("utf-8"))
    print(f"PASS: projected {len(table['transitions'])} transitions "
          f"and {len(table['refusal_codes'])} refusal codes from SPEC.md")
    return 0


def command_selfcheck(_: argparse.Namespace) -> int:
    if not PROJECTION.exists():
        print(f"FAIL: {PROJECTION.relative_to(ROOT)} is absent; run `sov_kernel.py sync`")
        return 1
    derived = derive(_read(ROOT / "SPEC.md"))
    stored = json.loads(_read(PROJECTION))
    defects = invariants(stored) + compare(derived, stored)
    if defects:
        for defect in defects:
            print(f"FAIL: {defect}")
        return 1
    reasoned = sum(1 for t in stored["transitions"].values() if t["reasoned_refusal_admitted"])
    print(f"PASS: {len(stored['transitions'])} kernel transitions match SPEC.md "
          f"({len(stored['refusal_codes'])} named refusal codes, "
          f"{reasoned} admitting an open reasoned refusal)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("sync", help="rebuild the projection from SPEC.md").set_defaults(
        run=command_sync)
    sub.add_parser("selfcheck", help="refuse when the projection and SPEC.md disagree"
                   ).set_defaults(run=command_selfcheck)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.run(args)


if __name__ == "__main__":
    raise SystemExit(main())
