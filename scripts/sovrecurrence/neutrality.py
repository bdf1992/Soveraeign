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

PRIMITIVES: dict[str, tuple[str, str]] = {
    "identity": ("contracts/principal.schema.json", "principal"),
    "session": ("services/console/contracts/operator-session.schema.json", "session"),
    "authority": ("contracts/authority-grant.schema.json", "authority"),
    "work": ("contracts/work-circuit.json", "work"),
    "custody": ("contracts/custody.schema.json", "custody"),
    "record_projection": ("contracts/record-projection.schema.json", "recordprojection"),
    "observation": ("contracts/observation.schema.json", "observation"),
    "finding": ("contracts/finding.schema.json", "finding"),
    "settlement": ("contracts/ticket-settlement.json", "settlement"),
    "discovery": ("contracts/node-interface.schema.json", "discovery"),
}
"""The ten primitives `conformance/commissioning.py` requires: the contract claimed to
declare each, and the term that contract is expected to declare it under.

The second half of each pair exists because the pairing is the weakest thing this reader
does, and three independent witnesses each attacked it. It is an **asserted mapping**, not
a measured one. What is measured is narrow and stated: that the path parses, and that the
named term appears in the contract's structure - an identifier, a title, a definition, or
a property key, never prose. What is asserted is that the term is the repository's name for
the primitive. `identity` is paired with `principal` because Principal is what this
repository calls the identity of an actor; a reader who disagrees should say so, and that
is the point of writing the pairing down instead of hiding it inside a substring match.

Two pairings do not hold and are reported rather than forced. `settlement` is bound to a
policy file that declares no schema structure at all, so nothing in it can be read as a
declaration. `discovery` is bound to the Node Interface, which is what discovery produces
and never declares discovery itself; no contract in this repository does. An earlier
revision searched the whole JSON dump instead, which passed `session` against a note about
this host's live sessions and `authority` against the sentence "it grants no authority" -
49 of 78 contracts. Loosening the check until the count reads ten is the defect two
witnesses already caught here under a different name."""


ALTERNATE_INSTITUTION = {
    "institution": "institution:procurement",
    "roles": ("procurement-steward", "supplier-liaison", "audit-observer", "settlement-clerk"),
}
"""An institution the founder did not predict, drawn from the horizon document's own
examples. Its role names share nothing with the proving four; if the primitives compose
under it, they do not depend on the commissioning instance."""


def _alternate_tokens() -> set[str]:
    """The alternate institution's role names, normalised the way a vocabulary would spell them."""
    tokens = set()
    for role in ALTERNATE_INSTITUTION["roles"]:
        upper = role.upper()
        tokens |= {upper, upper.replace("-", "_"), upper.replace("-", "")}
    return tokens


def _closes(values: list[Any]) -> bool:
    """True when this vocabulary admits a proving role and admits no alternate one.

    An earlier revision asked whether *every* value was a proving-role name. That reads a
    vocabulary of exactly the four as closed and one of the four plus any fifth name as
    open, which is the wrong question: what matters is whether an institution the founder
    did not predict can fill the field. `["worker", "orchestrator", "controller", "owner"]`
    admits no `procurement-steward` and is closed against it, though it is not four-of-four.
    An independent witness found that gap with exactly that example.

    Two of the four are required, not one, and that is a judgement worth stating. `WORKER`
    alone is also an actor *kind*: `["HUMAN", "MODEL", "WORKER", "SYSTEM"]` in
    `contracts/principal.schema.json` is a taxonomy of what sort of thing acts, not a
    roster of the commissioning institution, and a procurement steward is a `HUMAN` or a
    `MODEL` in it. Reading that as closed would report institution-neutrality defeated by a
    vocabulary that has nothing to do with institutions. Two or more of the specific four
    is the point at which a field is naming the proving roles rather than overlapping one
    word with them. What would defeat this rule: a real vocabulary that closes against an
    alternate institution using exactly one proving-role name and no other.
    """
    spelled = {str(value).upper().replace("-", "_") for value in values}
    return len(spelled & PROVING_ROLES) >= 2 and not (spelled & _alternate_tokens())


def _closed_enums(node: Any, path: str) -> list[tuple[str, list[str]]]:
    """Every closed vocabulary under `node`, with its path.

    Known gap, stated rather than hidden: a JSON Schema `const`, a `pattern` regex, and a
    required-property closure can each pin a field to one role, and none is read here. A
    `const` cannot be read at all under the two-role rule above, since a vocabulary of one
    can never hold two. An earlier revision scanned `const` anyway; a unit test proved the
    branch unreachable, so it is gone rather than left looking like coverage. What this
    reader measures is enum closure in the ten bound contracts, and nothing wider.
    """
    found: list[tuple[str, list[str]]] = []
    if isinstance(node, dict):
        values = node.get("enum")
        if isinstance(values, list) and values and _closes(values):
            found.append((path, [str(value) for value in values]))
        for key, value in node.items():
            found += _closed_enums(value, f"{path}/{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            found += _closed_enums(value, f"{path}[{index}]")
    return found


def _structural_names(document: Any) -> set[str]:
    """The names a contract declares structurally: identifiers, titles, definitions, keys.

    Prose is excluded on purpose. An earlier revision searched the whole JSON dump, so
    `session` matched the word "sessions" in a note about this host and `authority` matched
    the sentence "it grants no authority" - 49 of 78 contracts satisfied `authority` that
    way. A third independent witness showed that both bindings the previous commit claimed
    to defeat still passed, and that appending one sentence to a `description` flipped the
    whole reading. A declaration is a structural fact, so only structure is read.
    """
    names: set[str] = set()

    def walk(node: Any, in_defs: bool) -> None:
        if isinstance(node, dict):
            for field in ("$id", "title", "name"):
                value = node.get(field)
                if isinstance(value, str):
                    names.add(value)
            for key, value in node.items():
                if key in ("$defs", "definitions", "properties", "patternProperties"):
                    if isinstance(value, dict):
                        names.update(value)
                    walk(value, True)
                elif key not in ("description", "note", "$comment", "warrant", "enum"):
                    walk(value, in_defs)
        elif isinstance(node, list):
            for value in node:
                walk(value, in_defs)

    walk(document, False)
    return {str(name).lower().replace("_", "").replace("-", "").replace(" ", "")
            for name in names}


def _declares(document: Any, primitive: str) -> bool:
    """True when the contract declares the primitive structurally, not merely mentions it."""
    wanted = primitive.replace("_", "")
    return any(wanted in name for name in _structural_names(document))


def _closed_elsewhere(root: Path, bound: set[str]) -> list[str]:
    """Closed vocabularies outside the ten bound paths, reported not graded.

    Grading follows the primitives, so a role vocabulary closed in an unrelated contract
    does not defeat them. That line is drawn at file boundaries, and a third witness showed
    where it leaks: `contracts/ticket-settlement.json` names
    `contracts/issue-metadata.schema.json` in its own `governed_by`, and two of the
    closures live there, so the `settlement` primitive is governed by a contract that shuts
    `requested_by` to the proving roles. A closure reached through a bound primitive's own
    `governed_by` is marked as such below rather than lost in the list.
    """
    governed: set[str] = set()
    for relative in sorted(bound):
        try:
            document = json.loads((root / relative).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for reference in document.get("governed_by") or []:
            if isinstance(reference, str):
                governed.add(reference)
    found: list[str] = []
    for path in sorted((root / "contracts").rglob("*.json")):
        relative = str(path.relative_to(root)).replace("\\", "/")
        if relative in bound:
            continue
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        reached = " (reached through a bound primitive's governed_by)" if relative in governed \
            else ""
        for where, values in _closed_enums(document, ""):
            found.append(f"{relative}{where} admits {values} and no alternate role{reached}")
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
    for primitive, (relative, term) in sorted(PRIMITIVES.items()):
        path = root / relative
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            unresolved.append(f"{primitive} declared at {relative}, which is absent or unreadable")
            continue
        if not _declares(document, term):
            unresolved.append(f"{primitive} is paired with {relative} as `{term}`, which that "
                              "contract does not declare structurally, so the pairing asserts "
                              "a declaration the contract does not make")
            continue
        resolved[primitive] = relative
        for where, values in _closed_enums(document, ""):
            closed.append(f"{primitive} closes {relative}{where} to {values}")
    composes = not unresolved and not closed
    return {
        "closed_elsewhere": _closed_elsewhere(
            root, {relative for relative, _ in PRIMITIVES.values()}),
        "generic_primitives": sorted(resolved),
        "primitive_addresses": resolved,
        "unresolved": unresolved,
        "closed_vocabularies": closed,
        "fixed_role_names_required": bool(closed),
        "alternate_institution": ALTERNATE_INSTITUTION["institution"],
        "alternate_roles": list(ALTERNATE_INSTITUTION["roles"]),
        "alternate_institution_composes": composes,
    }
