"""Grade a phase record, and refuse a phase that ends by redefinition.

The failure this module exists to catch is quiet and only visible later: a phase
whose definition narrows until the evidence on hand satisfies it, leaving a
record that says the exit was earned. Nothing in the record afterwards
distinguishes that from a phase that actually earned it.

Two rules do the work. The definition is pinned by digest, so a document that
moved after the phase opened is reported rather than silently re-read. And
acceptance is derived: a phase cannot read EARNED while any clause reads
anything else, however the acceptance field is written.

Grading settles nothing. Whether a clause was earned is evidence, and whether
the phase is accepted is the root seat's.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, NamedTuple
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovkernel.jsonschema import validate  # noqa: E402

SCHEMA = ROOT / "contracts" / "phase.schema.json"
COLLECTION = ROOT / "contracts" / "phases.json"

REFUSALS = {
    "UNPINNED_DEFINITION":
        "A definition document's digest no longer matches the file, so the exit a reader "
        "checks is not the exit the phase opened with.",
    "MISSING_DEFINITION_DOCUMENT":
        "A pinned definition document is absent from the repository.",
    "ORPHAN_EXIT_CLAUSE":
        "An unmet clause names no custody, or names one that does not exist. Carried forward "
        "is not a terminal.",
    "ACCEPTANCE_WITHOUT_CLAUSES":
        "The phase reads EARNED while a clause reads anything other than EARNED.",
    "TERMINAL_MISMATCH":
        "The terminal does not derive from execution_status and acceptance_status.",
    "SELF_SETTLED_PHASE":
        "The phase names no settling seat, or names one that is not a root seat.",
}

#: The only admissible pairings. A closed window with an unearned exit is
#: CLOSED_INCOMPLETE, which is a truthful terminal and not a failure grade.
TERMINALS = {
    ("OPEN", "NOT_EARNED"): "IN_FLIGHT",
    ("OPEN", "EARNED"): "IN_FLIGHT",
    ("OPEN", "CANCELLED"): "CANCELLED",
    ("CLOSED", "NOT_EARNED"): "CLOSED_INCOMPLETE",
    ("CLOSED", "EARNED"): "ACCEPTED",
    ("CLOSED", "CANCELLED"): "CANCELLED",
}


class Defect(NamedTuple):
    """One refusal, named by its code and the exact thing that produced it."""

    code: str
    detail: str


def collection() -> dict[str, Any]:
    return json.loads(COLLECTION.read_bytes().decode("utf-8"))


def phases() -> list[dict[str, Any]]:
    return list(collection()["phases"])


def by_id(phase_id: str) -> dict[str, Any] | None:
    for phase in phases():
        if phase["phase_id"] == phase_id:
            return phase
    return None


def terminal_for(execution: str, acceptance: str) -> str | None:
    """The derived terminal, or None for a pairing the contract does not admit."""
    return TERMINALS.get((execution, acceptance))


def _digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def grade(phase: dict[str, Any], custody_ids: set[str] | None = None) -> list[Defect]:
    """Grade one phase against the constraints the schema cannot express."""
    defects: list[Defect] = []

    for pinned in phase.get("definition") or []:
        path = ROOT / str(pinned.get("document"))
        if not path.is_file():
            defects.append(Defect(
                "MISSING_DEFINITION_DOCUMENT",
                f"{phase.get('phase_id')} pins {pinned.get('document')}, which is absent"))
            continue
        actual = _digest(path)
        if actual != pinned.get("digest"):
            defects.append(Defect(
                "UNPINNED_DEFINITION",
                f"{pinned.get('document')} now digests {actual}, pinned at "
                f"{pinned.get('digest')}; the exit a reader checks is not the exit the "
                "phase opened with"))

    verdicts = [str(clause.get("verdict")) for clause in phase.get("exit_clauses") or []]
    if phase.get("acceptance_status") == "EARNED" and any(v != "EARNED" for v in verdicts):
        unearned = [clause["clause_id"] for clause in phase["exit_clauses"]
                    if clause.get("verdict") != "EARNED"]
        defects.append(Defect(
            "ACCEPTANCE_WITHOUT_CLAUSES",
            f"{phase.get('phase_id')} reads EARNED while {', '.join(unearned)} does not"))

    known = custody_ids
    for clause in phase.get("exit_clauses") or []:
        held = clause.get("held_by")
        if clause.get("verdict") == "EARNED":
            continue
        if not held:
            defects.append(Defect(
                "ORPHAN_EXIT_CLAUSE",
                f"{clause.get('clause_id')} is unmet and names no custody"))
        elif known is not None and held not in known:
            defects.append(Defect(
                "ORPHAN_EXIT_CLAUSE",
                f"{clause.get('clause_id')} names {held}, which no custody declares"))

    derived = terminal_for(str(phase.get("execution_status")),
                           str(phase.get("acceptance_status")))
    declared = phase.get("terminal")
    if declared is not None and declared != derived:
        defects.append(Defect(
            "TERMINAL_MISMATCH",
            f"{phase.get('phase_id')} declares {declared}; "
            f"{phase.get('execution_status')} and {phase.get('acceptance_status')} derive "
            f"{derived}"))

    if phase.get("execution_status") == "CLOSED" and not phase.get("settled_by"):
        defects.append(Defect(
            "SELF_SETTLED_PHASE",
            f"{phase.get('phase_id')} is CLOSED and names no settling seat"))

    return defects


def grade_collection(records: list[dict[str, Any]] | None = None,
                     custody_ids: set[str] | None = None) -> list[Defect]:
    """Validate every phase against the schema, then against the semantic constraints."""
    records = phases() if records is None else records
    schema = json.loads(SCHEMA.read_bytes().decode("utf-8"))
    defects: list[Defect] = []
    for phase in records:
        for error in validate(phase, schema):
            defects.append(Defect("SCHEMA", f"{phase.get('phase_id')}: {error}"))
        defects.extend(grade(phase, custody_ids))
    return defects


def declared_refusals() -> dict[str, str]:
    """Every refusal code this module declares, with its meaning."""
    return dict(REFUSALS)
