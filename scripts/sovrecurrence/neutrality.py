"""Institution neutrality, read for P15-Q4.3 from the contracts that declare the primitives.

Neutrality is not the absence of the words Controller, Orchestrator, Worker and Witness.
Those roles are a commissioning instance and a contract may name one in its prose without
requiring it. What defeats neutrality is a declaration that *closes* a vocabulary to those
four, because then no other institution can compose the primitive at all. So the reading
is structural: an `enum` whose every value is a proving-role name is a closed vocabulary;
a mention in prose is not. An alternate institution then composes the same ten primitives
under role names the founder did not predict, and every binding must remain admissible.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json

PROVING_ROLES = frozenset({"CONTROLLER", "ORCHESTRATOR", "WORKER", "WITNESS"})
"""The four commissioning roles. A vocabulary closed to these cannot admit a Phase II
institution, which is the defeating condition `contracts/custodies/phase-1-5.json` states
for this clause."""

PRIMITIVES: dict[str, str] = {
    "identity": "contracts/principal.schema.json",
    "session": "contracts/source.schema.json",
    "authority": "contracts/authority-grant.schema.json",
    "work": "contracts/work-circuit.json",
    "custody": "contracts/custody.schema.json",
    "record_projection": "contracts/record-projection.schema.json",
    "observation": "contracts/observation.schema.json",
    "finding": "contracts/finding.schema.json",
    "settlement": "contracts/ticket-settlement.json",
    "discovery": "contracts/node-interface.schema.json",
}
"""The ten primitives `conformance/commissioning.py` requires, each with the contract that
declares it generically. The name on the left is the primitive; the path on the right is
where a participant reads what it is, and is checked to exist rather than assumed."""

ALTERNATE_INSTITUTION = {
    "institution": "institution:procurement",
    "roles": ("procurement-steward", "supplier-liaison", "audit-observer", "settlement-clerk"),
}
"""An institution the founder did not predict, drawn from the horizon document's own
examples. Its role names share nothing with the proving four; if the primitives compose
under it, they do not depend on the commissioning instance."""


def _closed_enums(node: Any, path: str) -> list[tuple[str, list[str]]]:
    """Every `enum` under `node` whose values are all proving-role names, with its path."""
    found: list[tuple[str, list[str]]] = []
    if isinstance(node, dict):
        values = node.get("enum")
        if isinstance(values, list) and values:
            if {str(value).upper() for value in values} <= PROVING_ROLES:
                found.append((path, [str(value) for value in values]))
        for key, value in node.items():
            found += _closed_enums(value, f"{path}/{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            found += _closed_enums(value, f"{path}[{index}]")
    return found


def read(root: Path) -> dict[str, Any]:
    """Resolve the ten primitives under `root` and compose them as an alternate institution.

    A primitive resolves when the contract that declares it is present and parses. It is
    closed when that contract shuts a vocabulary to the proving roles. The alternate
    institution composes when every primitive resolves and none is closed, because a role
    name it does not use cannot then be required of it.
    """
    resolved: dict[str, str] = {}
    unresolved: list[str] = []
    closed: list[str] = []
    for primitive, relative in sorted(PRIMITIVES.items()):
        path = root / relative
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            unresolved.append(f"{primitive} declared at {relative}, which is absent or unreadable")
            continue
        resolved[primitive] = relative
        for where, values in _closed_enums(document, ""):
            closed.append(f"{primitive} closes {relative}{where} to {values}")
    composes = not unresolved and not closed
    return {
        "generic_primitives": sorted(resolved),
        "primitive_addresses": resolved,
        "unresolved": unresolved,
        "closed_vocabularies": closed,
        "fixed_role_names_required": bool(closed),
        "alternate_institution": ALTERNATE_INSTITUTION["institution"],
        "alternate_roles": list(ALTERNATE_INSTITUTION["roles"]),
        "alternate_institution_composes": composes,
    }
