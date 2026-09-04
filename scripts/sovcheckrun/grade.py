"""Grading one declared closure expression, and the debt list that carries the rest.

Kept apart from `scripts/sov_closure_checks.py` so the reader that reports stays
a CLI. The seam is the ordinary one: what a refusal means lives here with the
refusal, and how it is printed lives with the printing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from sovcheckrun import dispatch, resolve  # noqa: E402
from sovcustody import model as custody_model  # noqa: E402
from sovkernel.jsonschema import validate  # noqa: E402

DEBT_CONTRACT = "contracts/closure-checks.json"
DEBT_SCHEMA = "contracts/closure-checks.schema.json"
PHASES = "contracts/phases.json"

#: A phase clause states its reading as prose that names a command. The prose cannot
#: be split into arguments reliably, so only the target is graded here - which is
#: exactly the defect that occurred: a reading naming a module with no entry point.
COMMAND_IN_PROSE = re.compile(r"python (?:-m )?([A-Za-z0-9_./-]+)")

REFUSALS = {
    "CLOSURE_CHECK_UNPARSEABLE":
        "the expression is not a command line this reader can split",
    "CLOSURE_CHECK_COMPOUND":
        "the expression chains more than one command, so which stage closes the custody "
        "is undeclared",
    "CLOSURE_CHECK_NOT_PYTHON":
        "the expression names no python target this reader knows how to drive",
    "CLOSURE_CHECK_TARGET_MISSING":
        "the expression names a file or module that does not exist",
    "CLOSURE_CHECK_AMBIGUOUS":
        "the dotted module name matches more than one file, so the target is undeclared",
    "CLOSURE_CHECK_MUTE":
        "the target has no entry point, so running it exits 0 in silence",
    "CLOSURE_CHECK_REJECTED":
        "the target exists and refuses the declared arguments",
    "CLOSURE_CHECK_UNIMPORTABLE":
        "the target cannot be imported as declared",
    "CLOSURE_CHECK_UNSETTLEABLE":
        "the custody has neither a check nor a judgement seat, so nothing can close it",
}

DISPATCH_REFUSALS = {
    dispatch.REJECTED: "CLOSURE_CHECK_REJECTED",
    dispatch.UNIMPORTABLE: "CLOSURE_CHECK_UNIMPORTABLE",
}


def debt_contract(root: Path = ROOT) -> dict[str, Any]:
    return json.loads((root / DEBT_CONTRACT).read_bytes().decode("utf-8"))


def debt_schema_defects(root: Path = ROOT) -> list[str]:
    """Grade the debt contract against its schema.

    The list had none when it was written, and a wrong reason and a wrong
    provenance claim both survived a first reading because nothing read the
    prose beside the error text.
    """
    schema = json.loads((root / DEBT_SCHEMA).read_bytes().decode("utf-8"))
    return [str(problem) for problem in validate(debt_contract(root), schema)]


def _defect(code: str, custody_id: str, detail: str) -> dict[str, str]:
    return {"code": code, "custody": custody_id, "detail": detail}


def grade_check(custody: dict[str, Any], root: Path = ROOT) -> list[dict[str, str]]:
    """Grade one custody's declared closure route."""
    custody_id = str(custody.get("custody_id") or "unnamed custody")
    closure = custody.get("closure") or {}
    check = closure.get("check")

    if not check:
        if not closure.get("judgement_seat"):
            return [_defect("CLOSURE_CHECK_UNSETTLEABLE", custody_id,
                            f"{custody_id} declares neither a check nor a judgement seat")]
        return []
    if str(check.get("kind")) != "COMMAND":
        return []

    expression = str(check.get("expression") or "")
    target = resolve.resolve(root, expression)
    if target.refusal:
        return [_defect(target.refusal, custody_id,
                        f"{custody_id} closure check {expression!r}: {REFUSALS[target.refusal]}")]

    if target.mode == "path" and not resolve.has_entry_point(target.path):
        relative = target.path.relative_to(root).as_posix()
        return [_defect("CLOSURE_CHECK_MUTE", custody_id,
                        f"{custody_id} closure check {expression!r} resolves to {relative}, "
                        f"which {REFUSALS['CLOSURE_CHECK_MUTE']}")]

    code, message = dispatch.probe(root, target.mode, target.target, target.argv,
                                   target.environment)
    refusal = DISPATCH_REFUSALS.get(code)
    if refusal:
        return [_defect(refusal, custody_id,
                        f"{custody_id} closure check {expression!r}: {message or REFUSALS[refusal]}")]
    if code == dispatch.NO_PARSER and target.mode == "module":
        return [_defect("CLOSURE_CHECK_MUTE", custody_id,
                        f"{custody_id} closure check {expression!r} ran without reading an "
                        "argument, so the declared arguments were never accepted")]
    return []


def grade(records: list[dict[str, Any]] | None = None, root: Path = ROOT,
          entries: list[dict[str, Any]] | None = None,
          ) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Return (refusals, carried debt) over every custody in every collection.

    `entries` overrides the checked-in debt list. Only a test or the selfcheck
    passes it: the three refusals that guard the list cannot be driven from a
    contract that is, by construction, currently accurate.
    """
    rows = custody_model.custodies() if records is None else records
    debt_entries = debt_contract(root).get("debt", []) if entries is None else entries
    carried = {(entry["custody_id"], entry["expression"]): entry for entry in debt_entries}

    refusals: list[dict[str, str]] = []
    debt: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for custody in rows:
        custody_id = str(custody.get("custody_id") or "")
        check = (custody.get("closure") or {}).get("check") or {}
        expression = str(check.get("expression") or "")
        key = (custody_id, expression)
        found = grade_check(custody, root)
        if key in carried:
            seen.add(key)
            missing = [field for field in ("observed", "reason", "repair_seat", "repair")
                       if not str(carried[key].get(field) or "").strip()]
            if missing:
                refusals.append(_defect(
                    "CLOSURE_CHECK_DEBT_UNATTRIBUTED", custody_id,
                    f"{DEBT_CONTRACT} carries {custody_id} without {', '.join(missing)}; an "
                    "entry with no evidence and no seat that can repair it is an exemption, "
                    "not attributed debt"))
                continue
            if not found:
                refusals.append(_defect(
                    "CLOSURE_CHECK_DEBT_REPAIRED", custody_id,
                    f"{custody_id} is recorded in {DEBT_CONTRACT} as not dispatching, and it "
                    "now dispatches; delete the entry rather than leaving it as cover"))
            else:
                debt.extend(found)
            continue
        refusals.extend(found)

    for custody_id, expression in sorted(set(carried) - seen):
        refusals.append(_defect(
            "CLOSURE_CHECK_DEBT_UNKNOWN", custody_id,
            f"{DEBT_CONTRACT} carries {custody_id} with {expression!r}, which no collection "
            "declares"))
    return refusals, debt


def _kind_census(rows: list[dict[str, Any]]) -> dict[str, int]:
    """Every closure route by kind, so a kind this reader does not drive is visible."""
    census: dict[str, int] = {}
    for custody in rows:
        check = (custody.get("closure") or {}).get("check")
        kind = str(check.get("kind")) if check else "NONE (settled by a seat)"
        census[kind] = census.get(kind, 0) + 1
    return census


def _phase_readings(root: Path) -> list[tuple[str, str]]:
    """Every (clause, command target) a phase record names in prose."""
    document = json.loads((root / PHASES).read_bytes().decode("utf-8"))
    found: list[tuple[str, str]] = []
    for phase in document.get("phases", []):
        phase_id = str(phase.get("phase_id") or "?")
        for clause in phase.get("exit_clauses", []):
            where = f"{phase_id} {clause.get('clause_id') or '?'}"
            for target in COMMAND_IN_PROSE.findall(str(clause.get("reading") or "")):
                found.append((where, target))
    return found


def grade_phase_readings(root: Path = ROOT) -> list[dict[str, str]]:
    """Refuse a phase reading that names a command nobody can run.

    The custody collection is not the only place a closure command is written
    down. `contracts/phases.json` states each exit clause's reading in prose, and
    repairing P15-X4's custody left the phase record still naming the mute module
    it was repaired away from. One place was graded and the other was not, which
    is how a repaired defect went on reading as live.
    """
    defects: list[dict[str, str]] = []
    for where, target in _phase_readings(root):
        if not target.endswith(".py"):
            continue
        path = (root / target).resolve()
        if not path.is_file():
            defects.append(_defect("CLOSURE_CHECK_TARGET_MISSING", where,
                                   f"{where} reading names {target}, which does not exist"))
        elif not resolve.has_entry_point(path):
            defects.append(_defect("CLOSURE_CHECK_MUTE", where,
                                   f"{where} reading names {target}, which "
                                   f"{REFUSALS['CLOSURE_CHECK_MUTE']}"))
    return defects
