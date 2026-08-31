"""Grade one custody, and the collection it belongs to.

`contracts/custody.schema.json` refuses a malformed record. Six things it cannot
see are refused here, and each has a fixture that defeats it:

- a custody whose closure names neither a machine check nor a settling seat can
  never close, which is the shape the epic tree accumulated and the reason
  twenty-one of its issues are unroutable;
- a custody held by the same seat that settles its closure accepts its own work;
- a target stage below the entry stage is a custody that is already finished and
  says otherwise;
- one member address held by two custodies means two participants each believe
  the other is carrying it;
- a dependency cycle is a set of initiatives each waiting on the next;
- a root that does not resolve is work with no product ground behind it.

Grading settles nothing. It decides whether the custody may be carried, never
whether the initiative is worth carrying; that is the root seat's.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, NamedTuple
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovcustody import circuit as circuitmod  # noqa: E402
from sovcustody import collections as collectionmod  # noqa: E402
from sovcustody import estimate as estimatemod  # noqa: E402
from sovcustody import roots as rootsmod  # noqa: E402
from sovkernel.jsonschema import validate  # noqa: E402

SCHEMA = ROOT / "contracts" / "custody.schema.json"
ESTIMATE_SCHEMA = ROOT / "contracts" / "estimate.schema.json"
COLLECTION = ROOT / "contracts" / "custodies.json"
COLLECTION_DIR = ROOT / "contracts" / "custodies"
SEATS = ROOT / "contracts" / "seat-registry.json"
PHASES = ROOT / "contracts" / "phases.json"

ESTIMATE_REF = "https://soveraeign.local/contracts/estimate.schema.json"

REFUSALS = {
    "CLOSED_PHASE_CUSTODY_LIVE":
        "A custody still belongs to a phase whose execution window is closed but names no terminal, so historical accountability still reads as current assignment.",
    "INVALID_CUSTODY_TERMINAL":
        "EXIT and DELIVERY custodies have different terminal vocabularies; using the wrong one changes whether an unmet obligation is being claimed as earned or settled.",
    "UNCLOSEABLE_CUSTODY":
        "The custody declares neither a machine check nor a seat that settles it, so "
        "nothing can ever close it.",
    "SELF_HELD_CUSTODY":
        "The seat holding the custody is also the seat settling its closure.",
    "TARGET_BELOW_ENTRY":
        "The declared target stage does not advance on the entry stage.",
    "MEMBER_IN_TWO_CUSTODIES":
        "One work address is claimed by two custodies, so neither holder is on the hook.",
    "CUSTODY_CYCLE":
        "A dependency cycle: each initiative waits on the next and none can start.",
    "UNRESOLVED_ROOT":
        "A declared root names a record that does not exist.",
    "FLAT_CUSTODY":
        "A delivery custody names neither the exit custody it serves nor an explicit reason "
        "for being outside the phase exit, or names both.",
    "UNKNOWN_EXIT_CUSTODY":
        "A delivery custody serves an exit custody that does not exist, or one that is not "
        "itself an EXIT custody.",
    "DUPLICATE_EXIT_CLAUSE":
        "Two exit custodies hold the same clause, so neither is the one accountable for it.",
}


def _closed_phase_ids() -> set[str]:
    """Phase ids whose operating window is already closed."""
    document = json.loads(PHASES.read_bytes().decode("utf-8"))
    return {
        str(phase.get("phase_id"))
        for phase in document.get("phases") or []
        if phase.get("execution_status") == "CLOSED"
    }


class Defect(NamedTuple):
    """One refusal, named by its code and the exact thing that produced it."""

    code: str
    detail: str


def _rewrite_refs(node: Any, mapping: dict[str, str]) -> Any:
    """Rewrite every `$ref` string through `mapping`, leaving everything else alone."""
    if isinstance(node, dict):
        return {
            key: (mapping.get(value, value) if key == "$ref" and isinstance(value, str)
                  else _rewrite_refs(value, mapping))
            for key, value in node.items()
        }
    if isinstance(node, list):
        return [_rewrite_refs(item, mapping) for item in node]
    return node


def schema() -> dict[str, Any]:
    """The custody schema with the estimate contract spliced in as a local definition.

    `sovkernel.jsonschema` resolves local pointers only, and the estimate is a
    separate contract because a ticket carries one too. Splicing at load keeps
    one source of truth rather than a second copy that drifts.
    """
    document = json.loads(SCHEMA.read_bytes().decode("utf-8"))
    estimate = json.loads(ESTIMATE_SCHEMA.read_bytes().decode("utf-8"))
    definitions = estimate.pop("$defs", {})
    for key in ("$schema", "$id"):
        estimate.pop(key, None)

    inner = {f"#/$defs/{name}": f"#/$defs/estimate_{name}" for name in definitions}
    document = _rewrite_refs(document, {ESTIMATE_REF: "#/$defs/estimate"})
    document["$defs"]["estimate"] = _rewrite_refs(estimate, inner)
    for name, definition in definitions.items():
        document["$defs"][f"estimate_{name}"] = _rewrite_refs(definition, inner)
    return document


def collection() -> dict[str, Any]:
    """The historical legacy collection, retained for compatibility."""
    return json.loads(COLLECTION.read_bytes().decode("utf-8"))


def collection_paths() -> tuple[Path, ...]:
    return collectionmod.paths(COLLECTION, COLLECTION_DIR)


def collections() -> list[dict[str, Any]]:
    return collectionmod.documents(COLLECTION, COLLECTION_DIR)


def custodies(phase: str | None = None) -> list[dict[str, Any]]:
    return collectionmod.records(COLLECTION, COLLECTION_DIR, phase)


def by_id(custody_id: str) -> dict[str, Any] | None:
    for custody in custodies():
        if custody["custody_id"] == custody_id:
            return custody
    return None


def _known_seats() -> set[str]:
    document = json.loads(SEATS.read_bytes().decode("utf-8"))
    return {str(seat.get("seat_id")) for seat in document.get("seats") or []}


def grade(custody: dict[str, Any], seats: set[str] | None = None) -> list[Defect]:
    """Grade one custody against the constraints the schema cannot express."""
    defects: list[Defect] = []
    closure = custody.get("closure") or {}
    check = closure.get("check")
    seat = closure.get("judgement_seat")
    terminal = custody.get("terminal")
    phase = custody.get("phase")

    if phase and phase in _closed_phase_ids() and not terminal:
        defects.append(Defect(
            "CLOSED_PHASE_CUSTODY_LIVE",
            f"{custody.get('custody_id')} belongs to closed {phase} and names no terminal",
        ))
    if terminal:
        outcome = terminal.get("outcome")
        allowed = {
            "EXIT": {"EARNED", "CLOSED_UNMET"},
            "DELIVERY": {"SETTLED", "RETIRED"},
        }.get(str(custody.get("custody_kind")), set())
        if outcome not in allowed:
            defects.append(Defect(
                "INVALID_CUSTODY_TERMINAL",
                f"{custody.get('custody_id')} is {custody.get('custody_kind')} but terminates {outcome}",
            ))

    if not check and not seat:
        defects.append(Defect(
            "UNCLOSEABLE_CUSTODY",
            f"{custody.get('custody_id')} declares no check and no settling seat",
        ))
    if seat and seat == custody.get("held_by"):
        defects.append(Defect(
            "SELF_HELD_CUSTODY",
            f"{custody.get('custody_id')} is held by {seat}, which also settles its closure",
        ))

    if custody.get("custody_kind") == "DELIVERY":
        serves = custody.get("serves_exit")
        outside = custody.get("outside_phase_exit")
        if bool(serves) == bool(outside):
            defects.append(Defect(
                "FLAT_CUSTODY",
                f"{custody.get('custody_id')} names "
                + ("both an exit custody and a reason for being outside the phase exit"
                   if serves else
                   "neither the exit custody it serves nor a reason for being outside it")))

    entry, target = custody.get("entry_stage", ""), custody.get("target_stage", "")
    if circuitmod.ordinal(target) < circuitmod.ordinal(entry):
        defects.append(Defect(
            "TARGET_BELOW_ENTRY",
            f"{custody.get('custody_id')} enters at {entry} and targets {target}",
        ))

    for root in custody.get("roots") or []:
        if not rootsmod.root_resolves(root):
            defects.append(Defect(
                "UNRESOLVED_ROOT",
                f"{custody.get('custody_id')} names {root.get('reference')}, which does "
                "not resolve",
            ))

    known = seats if seats is not None else _known_seats()
    for field in ("held_by",):
        value = custody.get(field)
        if value and value not in known:
            defects.append(Defect(
                "UNRESOLVED_ROOT",
                f"{custody.get('custody_id')} {field} names {value}, absent from the "
                "seat registry",
            ))

    required = estimatemod.required_at(entry, circuitmod.ordinal)
    defects.extend(
        Defect(code, f"{custody.get('custody_id')}: {detail}")
        for code, detail in estimatemod.grade(custody.get("estimate"), required, entry)
    )
    return defects


def grade_collection(records: list[dict[str, Any]] | None = None) -> list[Defect]:
    """Grade the whole set, including the constraints that only exist between custodies."""
    records = custodies() if records is None else records
    seats = _known_seats()
    defects: list[Defect] = []
    document = schema()

    for custody in records:
        for error in validate(custody, document):
            defects.append(Defect("SCHEMA", f"{custody.get('custody_id')}: {error}"))
        defects.extend(grade(custody, seats))

    exits = {custody["custody_id"] for custody in records
             if custody.get("custody_kind") == "EXIT"}
    for custody in records:
        serves = custody.get("serves_exit")
        if serves and serves not in exits:
            defects.append(Defect(
                "UNKNOWN_EXIT_CUSTODY",
                f"{custody['custody_id']} serves {serves}, which is not an EXIT custody here"))

    clauses: dict[str, list[str]] = {}
    for custody in records:
        clause = custody.get("exit_clause")
        if clause:
            clauses.setdefault(str(clause), []).append(custody["custody_id"])
    for clause, owners in sorted(clauses.items()):
        if len(owners) > 1:
            defects.append(Defect(
                "DUPLICATE_EXIT_CLAUSE",
                f"{clause} is held by {' and '.join(sorted(owners))}"))

    holders: dict[str, list[str]] = {}
    for custody in records:
        for member in custody.get("members") or []:
            holders.setdefault(str(member.get("address")), []).append(custody["custody_id"])
    for address, owners in sorted(holders.items()):
        if len(owners) > 1:
            defects.append(Defect(
                "MEMBER_IN_TWO_CUSTODIES",
                f"{address} is claimed by {' and '.join(sorted(owners))}",
            ))

    edges = {custody["custody_id"]: list(custody.get("depends_on") or []) for custody in records}
    for start in sorted(edges):
        seen, stack = set(), [start]
        while stack:
            here = stack.pop()
            for nxt in edges.get(here, []):
                if nxt == start:
                    defects.append(Defect(
                        "CUSTODY_CYCLE", f"{start} depends on itself through {here}"))
                    stack = []
                    break
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
    return defects
