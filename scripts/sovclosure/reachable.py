"""What a refusal leaves reachable.

``contracts/closure-ownership.json`` names twelve ways a handoff is refused. A
refusal that says only why is a dead end: the participant that meets one has no
move left but to stop, or to ask the same thing again in a different shape. The
contract therefore declares, for every refusal code, the operations that clear
it, and this module reads that declaration.

Two things are owned here. ``operations_for`` annotates a code's declared
operations with whether the participant could take each one right now, given
the tools its invocation granted. ``table_defects`` grades the declaration
itself: a code with no operations, or with none the refused participant can
take alone, is a politer dead end and fails the build.
"""

from __future__ import annotations

from typing import Any

TABLE_KEY = "reachable_operations"


def _declared(table: dict) -> dict[str, list[dict]]:
    return table.get(TABLE_KEY) or {}


def _self_reachable(operation: dict) -> bool:
    """True when the refused participant can take this operation alone."""
    return not operation.get("needs_other_participant", False)


def _available(operation: dict, tools_available: list[str]) -> bool:
    """True when this invocation grants what the operation needs."""
    if not _self_reachable(operation):
        return False
    tool = operation.get("tool")
    return tool is None or tool in tools_available


def operations_for(table: dict, code: str,
                   tools_available: list[str] | None = None) -> list[dict[str, Any]]:
    """Return the operations that clear ``code``, annotated for this invocation.

    Each entry carries the declared ``operation``, ``tool`` and
    ``needs_other_participant``, plus ``available``: whether the refused
    participant holds what the operation needs. A missing ``tools_available``
    is read as an invocation that granted nothing, which is how the rest of the
    closure evaluator reads it.
    """
    granted = tools_available or []
    annotated: list[dict[str, Any]] = []
    for declared in _declared(table).get(code, []):
        entry = dict(declared)
        entry.setdefault("needs_other_participant", False)
        entry["available"] = _available(declared, granted)
        annotated.append(entry)
    return annotated


def table_defects(table: dict) -> list[str]:
    """Grade the declaration and return one line per defect.

    The invariant is that no refusal is a dead end: every declared code names
    at least one operation, and at least one of those is an operation the
    refused participant can take without another participant.
    """
    defects: list[str] = []
    refusals = table.get("refusals") or {}
    tools = table.get("tools") or []
    declared = _declared(table)

    for code in refusals:
        operations = declared.get(code)
        if operations is None:
            defects.append(f"{code}: declared in refusals with no reachable operations")
            continue
        if not operations:
            defects.append(f"{code}: reachable_operations is empty")
            continue
        for index, operation in enumerate(operations):
            if not (operation.get("operation") or "").strip():
                defects.append(f"{code}: operation {index} has no operation text")
            tool = operation.get("tool")
            if tool is not None and tool not in tools:
                defects.append(f"{code}: operation {index} names undeclared tool {tool!r}")
        if not any(_self_reachable(operation) for operation in operations):
            defects.append(f"{code}: every reachable operation needs another participant")

    for code in declared:
        if code not in refusals:
            defects.append(f"{code}: reachable_operations names a refusal the contract"
                           " does not declare")
    return defects


def state_of(operation: dict) -> str:
    """Name an annotated operation's state, as the availability corpus declares it.

    An operation that needs another participant and is also marked available is
    its own state rather than one of the three. Folding it into
    ``OTHER_PARTICIPANT`` would hide exactly the drift the corpus grades for: an
    annotation that stopped reading the flag would still render correctly and
    still pass.
    """
    if operation["needs_other_participant"]:
        return "OTHER_PARTICIPANT_BUT_AVAILABLE" if operation["available"] \
            else "OTHER_PARTICIPANT"
    return "AVAILABLE" if operation["available"] else "UNAVAILABLE"


def corpus_defects(live_table: dict, corpus: dict) -> list[str]:
    """Grade the declared reachable-operations corpus.

    ``table_cases`` grade the declaration through ``table_defects``.
    ``availability_cases`` grade the annotation through ``operations_for``,
    which is the separate question of whether an operation reads as reachable
    against the tools an invocation actually granted.
    """
    return (_table_case_defects(live_table, corpus)
            + _availability_case_defects(live_table, corpus))


def _table_case_defects(live_table: dict, corpus: dict) -> list[str]:
    defects: list[str] = []
    base = corpus["base"]
    for case in corpus["table_cases"]:
        table = live_table if case["target"] == "live" else {**base, **(case.get("patch") or {})}
        found = table_defects(table)
        if case["expect"] == "CLEAN":
            if found:
                defects.append(f"{case['case_id']}: expected CLEAN, got {found[0]}")
            continue
        wanted = case["defect_contains"]
        if not any(wanted in line for line in found):
            got = found[0] if found else "no defect at all"
            defects.append(f"{case['case_id']}: expected a defect containing {wanted!r},"
                           f" got {got}")
    return defects


def _availability_case_defects(live_table: dict, corpus: dict) -> list[str]:
    defects: list[str] = []
    base = corpus["availability_base"]
    for case in corpus["availability_cases"]:
        granted = case.get("tools_available")
        if case.get("target") == "live":
            defects.extend(_every_code_reachable(live_table, case, granted))
            continue
        found = [state_of(operation)
                 for operation in operations_for(base, case["code"], granted)]
        if found != case["expect"]:
            defects.append(f"{case['case_id']}: expected {case['expect']}, got {found}")
    return defects


def _every_code_reachable(table: dict, case: dict, granted: list[str] | None) -> list[str]:
    """Check that every declared refusal leaves one operation available to this tool set."""
    stranded = [code for code in table.get("refusals") or {}
                if not any(operation["available"]
                           for operation in operations_for(table, code, granted))]
    if not stranded:
        return []
    return [f"{case['case_id']}: {', '.join(sorted(stranded))} leaves nothing available to a"
            f" participant granted {', '.join(granted or [])}"]
