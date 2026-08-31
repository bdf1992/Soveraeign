"""Closure-ready clarity checks over the small trusted reader set."""

from __future__ import annotations


def required_paths(contract: dict) -> list[str]:
    value = contract.get("zero_state", {}).get("required_current", [])
    if not isinstance(value, list) or not all(isinstance(path, str) for path in value):
        return []
    return value


def errors(
    contract: dict,
    states: dict[str, str],
    allowed: set[str],
    base_errors: list[str],
) -> list[str]:
    defects = list(base_errors)
    required = required_paths(contract)
    if not required:
        return defects + ["zero_state.required_current must be a non-empty path list"]
    if len(required) != len(set(required)):
        defects.append("zero_state.required_current must not contain duplicate paths")
    for path in required:
        if path not in allowed:
            defects.append(f"{path}: zero-state reader must be eligible current prose")
        elif states.get(path, "UNCHECKED") != "CURRENT":
            defects.append(
                f"{path}: zero-state reader is {states.get(path, 'UNCHECKED')}, expected CURRENT"
            )
    return defects


def report(
    contract: dict,
    states: dict[str, str],
    allowed: set[str],
    base_errors: list[str],
) -> int:
    defects = errors(contract, states, allowed, base_errors)
    for defect in defects:
        print(f"ZERO: {defect}")
    if defects:
        return 1
    required = required_paths(contract)
    print(f"PASS: clarity zero is ready ({len(required)}/{len(required)} required readers CURRENT)")
    unchecked = sum(state == "UNCHECKED" for state in states.values())
    if unchecked:
        print(f"INFO: {unchecked} non-critical eligible artifacts remain UNCHECKED; full gate is separate")
    return 0
