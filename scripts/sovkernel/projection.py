"""Derive the SPEC.md transition contract table and check the kernel table against it.

`contracts/kernel-transitions.json` is authored, not generated: it carries lease,
observation, authority, settlement, and effect-class fields that `SPEC.md` states in
prose rather than in its transition table. Deriving the whole file from the table is
therefore impossible, and claiming to would be worse than not doing it.

What the table does state is checkable: which transitions exist and which refusal codes
each one names. This module derives exactly that much and reports where the authored
contract and the governing document disagree. A transition SPEC.md names and the kernel
does not know is a hole in the kernel; a refusal code the kernel invents is a refusal no
document authorises.

Nothing here settles anything. `SPEC.md` is authoritative; a disagreement is a defect in
the authored file until Bdo rules otherwise.
"""

from __future__ import annotations

from typing import Any
import re

TABLE_HEADER = "| Transition | Preconditions | Commit | Refusal |"
#: SPEC leaves several transitions an open reasoned refusal alongside any named code.
REASONED = "reasoned refusal"


def _codes(cell: str) -> list[str]:
    """Named refusal codes in a SPEC refusal cell, in declared order."""
    return re.findall(r"`([A-Z_]+)`", cell)


def _split_semicolons(cell: str) -> list[str]:
    """SPEC states preconditions as a semicolon-separated list."""
    return [part.strip() for part in cell.split(";") if part.strip()]


def derive(spec_text: str) -> dict[str, dict[str, Any]]:
    """Read the SPEC.md transition contract table into a mapping keyed by transition."""
    if TABLE_HEADER not in spec_text:
        raise ValueError("SPEC.md no longer contains the transition contract table")
    body = spec_text.split(TABLE_HEADER, 1)[1].splitlines()
    derived: dict[str, dict[str, Any]] = {}
    for line in body[1:]:
        if not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 4 or all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        name = re.match(r"`([a-z_]+)`", cells[0])
        if not name:
            continue
        derived[name.group(1)] = {
            "preconditions": _split_semicolons(cells[1]),
            "commit": cells[2].replace("`", ""),
            "refusals": _codes(cells[3]),
            "reasoned_refusal_admitted": REASONED in cells[3],
        }
    if not derived:
        raise ValueError("the SPEC.md transition table declares no transitions")
    return derived


def invariants(derived: dict[str, dict[str, Any]]) -> list[str]:
    """Defects the SPEC table must never carry, independent of what the kernel stores."""
    defects: list[str] = []
    if not derived:
        defects.append("the transition table declares no transitions")
    for name, transition in sorted(derived.items()):
        if not transition.get("preconditions"):
            defects.append(f"{name}: declares no precondition")
        if not transition.get("commit"):
            defects.append(f"{name}: declares no commit")
        if not transition["refusals"] and not transition["reasoned_refusal_admitted"]:
            defects.append(f"{name}: declares no refusal path")
        for code in transition["refusals"]:
            if code != code.upper():
                defects.append(f"{name}: refusal code {code} is not upper case")
    return defects


def conflicts(derived: dict[str, dict[str, Any]], stored: dict[str, Any]) -> list[str]:
    """Report where the authored kernel table contradicts SPEC.md on what SPEC states.

    Only the transition set and the named refusal codes are compared. The stored file's
    remaining fields have no counterpart in the SPEC table, so silence about them is
    accurate rather than lenient; the commit column is prose in SPEC and an outcome
    name in the kernel, and comparing the two would report drift that does not exist.
    """
    entries = {entry["transition"]: entry for entry in stored.get("transitions", [])}
    defects: list[str] = []
    for name in sorted(set(derived) - set(entries)):
        defects.append(f"{name}: SPEC.md declares it; the kernel table does not carry it")
    for name in sorted(set(entries) - set(derived)):
        defects.append(f"{name}: the kernel table carries it; SPEC.md does not declare it")
    for name in sorted(set(derived) & set(entries)):
        spec_codes = set(derived[name]["refusals"])
        kernel_codes = set(entries[name].get("refusals") or [])
        for code in sorted(spec_codes - kernel_codes):
            defects.append(f"{name}: SPEC.md names refusal {code}; the kernel table omits it")
        for code in sorted(kernel_codes - spec_codes):
            if derived[name]["reasoned_refusal_admitted"]:
                continue
            defects.append(f"{name}: the kernel table names refusal {code}; SPEC.md does not")
    return defects
