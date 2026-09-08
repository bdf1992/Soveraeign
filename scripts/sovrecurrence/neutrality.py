"""Institution neutrality, read for P15-Q4.3 from the contracts that declare the primitives.

Neutrality is not the absence of the words Controller, Orchestrator, Worker and Witness.
Those roles are a commissioning instance and a contract may name one in its prose without
requiring it. What defeats neutrality is a declaration that *closes* a vocabulary to those
four, because then no other institution can compose the primitive at all. So the reading
is structural: an `enum` whose every value is a proving-role name is a closed vocabulary;
a mention in prose is not. An alternate institution then composes the same ten primitives
under role names the founder did not predict, and every binding must remain admissible.

Two properties are read here and they are not equally strong, so they are named apart.
Resolution asks whether the contract a primitive is paired with is present and carries the
primitive's term in its declared identity or its declared structure. That is close to a
presence check, because a contract in this repository is normally named after the thing it
declares, and it is stated as such rather than dressed up. Closure is the property that
actually grades neutrality: it reads enum vocabularies, in the bound contracts and in the
contracts those bound contracts name as their own `governed_by`, and it can fail on facts
no wording change reaches.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from sovrecurrence.declaration import declares

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
does, and every witness so far has attacked it. It is an **asserted mapping**, not a
measured one, and no mechanical rule can supply it: that `contracts/principal.schema.json`
is this repository's identity primitive is a fact about what the repository calls things,
held by whoever names them. Writing the term down puts the assertion where a reader can
challenge one line of it instead of arguing with a substring match.

What is measured is narrow and stated: the path parses, and the term appears in the
contract's *declared identity* (`$id`, or a root-level `_id` or `_schema` value) or among
the names it declares (`$defs`, `definitions`, `properties`, `patternProperties` keys).
Prose is not read at all - not descriptions, not notes, and not titles. An earlier revision
searched the whole JSON dump, which passed `session` against a note about this host's live
sessions and `authority` against the sentence "it grants no authority", 49 of 78 contracts.
The revision after it stopped reading descriptions but kept reading `title`, which is free
prose in a structural field: `work` resolved only because the title of `contracts/work-
circuit.json` is a sentence containing the word, and `settlement` failed only because
`contracts/ticket-settlement.json` has no title at all. A fourth witness flipped both
verdicts with one-string edits that changed no structure. Both files declare their own
identity - `soveraeign-work-circuit/v1` and `soveraeign-ticket-settlement/v1` - and that is
what is read now.

One pairing does not hold and is reported rather than forced. `discovery` is bound to the
Node Interface, which is what discovery produces and never declares discovery itself; no
contract in this repository declares it, under this rule or the two stricter halves of the
last one. Loosening the check until the count reads ten is the defect three witnesses have
already caught here under three different names."""


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
    reader measures is enum closure in the bound contracts and in the contracts they name
    as governing them, and nothing wider.
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


def _governing_index(root: Path, bound: dict[str, str]) -> dict[str, set[str]]:
    """Which primitives name which other contract as their own `governed_by`.

    One hop, not a closure: a primitive's governance is what its contract says governs it,
    and following that recursively would eventually reach every contract in the repository
    and grade the whole tree under whichever primitive got there first.
    """
    index: dict[str, set[str]] = {}
    for primitive, relative in sorted(bound.items()):
        try:
            document = json.loads((root / relative).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for reference in document.get("governed_by") or []:
            if isinstance(reference, str) and reference not in bound.values():
                index.setdefault(reference, set()).add(primitive)
    return index


def _closures_beyond(root: Path, bound: dict[str, str]) -> tuple[list[str], list[str],
                                                                 list[str], list[str]]:
    """Closed vocabularies outside the ten bound paths, split into graded and reported.

    A closure in a contract a bound primitive names as `governed_by` is that primitive's
    own: `contracts/ticket-settlement.json` declares
    `contracts/issue-metadata.schema.json` as governing it, and that schema shuts
    `requested_by` to the proving roles, so the `settlement` primitive as governed does
    require a proving-role name. A third witness found the leak and this reader disclosed
    it without letting it change the verdict, which was the wrong half to fix: the custody's
    stated defeating condition is "a primitive that only works when the participant is named
    Controller, Orchestrator, Worker, or Witness", and that is what this is. It is graded.

    A closure in a contract no bound primitive names is still only reported. Grading follows
    the primitives, and an unrelated contract's role vocabulary defeats none of them.

    The addresses on each side are returned alongside the sentences. A sixth witness showed
    why: the test that pinned this split parsed the sentences to recover the path, so whether
    it could fail depended on whether the closure sat under `/properties` or `/definitions`.
    A test should not have to reparse prose to find out what the reader decided.

    The scan is `contracts/**` plus every `.json` a bound primitive actually names, so a
    primitive governed by a contract under `services/` is graded rather than silently missed.
    A fifth witness found that gap while it was still vacuous, which is the cheapest time.

    What this does not follow is an instance to its schema. `settlement` names
    `contracts/product-canon.json`, and the closed vocabulary lives in
    `contracts/product-canon.schema.json`, which that instance does not name; the link is a
    filename convention and not a declaration, so it is reported and not graded.
    """
    governed = _governing_index(root, bound)
    graded: list[str] = []
    reported: list[str] = []
    graded_at: set[str] = set()
    reported_at: set[str] = set()
    scanned = {str(path.relative_to(root)).replace("\\", "/")
               for path in (root / "contracts").rglob("*.json")}
    scanned |= {name for name in governed if name.endswith(".json")}
    for relative in sorted(scanned):
        path = root / relative
        if relative in bound.values() or not path.is_file():
            continue
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        owners = sorted(governed.get(relative) or ())
        for where, values in _closed_enums(document, ""):
            if owners:
                graded.append(f"{', '.join(owners)} is governed by {relative}, which closes "
                              f"{where} to {values} and admits no alternate role")
                graded_at.add(relative)
            else:
                reported.append(f"{relative}{where} admits {values} and no alternate role")
                reported_at.add(relative)
    return graded, reported, sorted(graded_at), sorted(reported_at)


def read(root: Path) -> dict[str, Any]:
    """Resolve the ten primitives under `root` and compose them as an alternate institution.

    A primitive resolves when the contract that declares it is present, parses, and declares
    the paired term. It is closed when that contract, or a contract it names as governing
    it, shuts a vocabulary to the proving roles. The alternate institution composes when
    every primitive resolves and none is closed, because a role name it does not use cannot
    then be required of it.
    """
    bound = {primitive: relative for primitive, (relative, _) in PRIMITIVES.items()}
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
        if not declares(document, term):
            unresolved.append(f"{primitive} is paired with {relative} as `{term}`, which that "
                              "contract does not declare structurally, so the pairing asserts "
                              "a declaration the contract does not make")
            continue
        resolved[primitive] = relative
        for where, values in _closed_enums(document, ""):
            closed.append(f"{primitive} closes {relative}{where} to {values}")
    graded, reported, graded_at, reported_at = _closures_beyond(root, bound)
    closed += graded
    composes = not unresolved and not closed
    return {
        "closed_elsewhere": reported,
        "governed_closure_addresses": graded_at,
        "reported_closure_addresses": reported_at,
        "generic_primitives": sorted(resolved),
        "primitive_addresses": resolved,
        "unresolved": unresolved,
        "closed_vocabularies": closed,
        "fixed_role_names_required": bool(closed),
        "alternate_institution": ALTERNATE_INSTITUTION["institution"],
        "alternate_roles": list(ALTERNATE_INSTITUTION["roles"]),
        "alternate_institution_composes": composes,
    }
