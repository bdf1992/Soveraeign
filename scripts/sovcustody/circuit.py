"""Judge one stage advance on the work circuit.

The circuit in `contracts/work-circuit.json` is the second axis of a ticket:
not what standing a claim about it holds, but how far the thing itself has been
drawn. A point becomes a closed vertical, verticals compose into a surface, the
surface explodes into addressable endpoints, and the endpoints acquire identity,
authority and receipts until the whole thing can be addressed as a node.

Each stage's admission predicate is the previous stage's evidence, which is why
skipping is refused rather than merely discouraged: a HORIZONTAL_SURFACE claimed
straight from a ROOT_POINT has no verticals to compose, and the claim is about
nothing.

Judging an advance settles nothing. It decides whether the claim is admissible,
never whether the work is good, and the participant that drew the stage may not
be the one that settles it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, NamedTuple
import json

ROOT = Path(__file__).resolve().parents[2]
CIRCUIT = ROOT / "contracts" / "work-circuit.json"

#: Emissions a closed path may end on. A REPORT does not close a path: the
#: participant that produced it is also its only evidence (GROUND-010).
CLOSING_EMISSIONS = frozenset({"CHECK", "RECEIPT", "OBSERVATION"})


class Defect(NamedTuple):
    """One refusal, named by its code and the exact thing that produced it."""

    code: str
    detail: str


def _circuit() -> dict[str, Any]:
    return json.loads(CIRCUIT.read_bytes().decode("utf-8"))


def stages() -> list[dict[str, Any]]:
    """The declared stages in circuit order."""
    return sorted(_circuit()["stages"], key=lambda stage: stage["ordinal"])


def stage_names() -> list[str]:
    return [stage["stage"] for stage in stages()]


def ordinal(stage: str) -> int:
    """The stage's position, or 0 for a name the circuit does not declare."""
    for declared in stages():
        if declared["stage"] == stage:
            return int(declared["ordinal"])
    return 0


def at_least(stage: str, floor: str) -> bool:
    """True when `stage` sits at or above `floor` on the circuit."""
    return ordinal(stage) >= ordinal(floor) > 0


def _root_point(evidence: dict[str, Any]) -> list[Defect]:
    subject = evidence.get("subject")
    roots = evidence.get("roots") or []
    defects: list[Defect] = []
    if not subject:
        defects.append(Defect("ROOTLESS_POINT", "the ticket names no subject address"))
    resolving = [root for root in roots if root.get("resolves") is not False]
    if not resolving:
        defects.append(Defect(
            "ROOTLESS_POINT",
            "no root resolves; work with no product ground behind it can only be "
            "prioritised on opinion",
        ))
    return defects


def _vertical_slice(evidence: dict[str, Any]) -> list[Defect]:
    path = evidence.get("path") or []
    if not path:
        return [Defect("OPEN_PATH", "the slice names no path of layers")]
    final = path[-1]
    emits = str(final.get("emits") or "").upper()
    if emits not in CLOSING_EMISSIONS:
        return [Defect(
            "OPEN_PATH",
            f"the path ends at {final.get('layer', 'an unnamed layer')} emitting "
            f"{emits or 'nothing'}; a path closes on a check, a receipt or an observation",
        )]
    return []


def _horizontal_surface(evidence: dict[str, Any], required: set[str]) -> list[Defect]:
    composes = evidence.get("composes") or []
    defects: list[Defect] = []
    if len(composes) < 2:
        defects.append(Defect(
            "SURFACE_OVER_OPEN_PATHS",
            f"a surface composes at least two verticals; {len(composes)} supplied",
        ))
    for vertical in composes:
        stage = str(vertical.get("stage") or "")
        if not at_least(stage, "VERTICAL_SLICE"):
            defects.append(Defect(
                "SURFACE_OVER_OPEN_PATHS",
                f"{vertical.get('address', 'a vertical')} sits at {stage or 'no stage'}; "
                "composing over an open path hides which half failed",
            ))
    supplied = {
        str(dimension.get("dimension_id"))
        for dimension in (evidence.get("estimate") or {}).get("dimensions") or []
    }
    for missing in sorted(required - supplied):
        defects.append(Defect(
            "MISSING_EXTENT",
            f"no estimate on {missing}, which this stage requires",
        ))
    return defects


def _exploded_surface(evidence: dict[str, Any]) -> list[Defect]:
    declared_fields = ("subject", "verb", "endpoint", "preconditions", "commit", "refusals")
    defects: list[Defect] = []
    operations = evidence.get("operations") or []
    if not operations:
        defects.append(Defect("ADVERTISED_NOT_ENFORCED", "the surface declares no operations"))
    for operation in operations:
        missing = [field for field in declared_fields if not operation.get(field)]
        if missing:
            defects.append(Defect(
                "ADVERTISED_NOT_ENFORCED",
                f"{operation.get('operation', 'an operation')} declares no "
                f"{', '.join(missing)}",
            ))
    advertised = {str(name) for name in evidence.get("discovers") or []}
    enforced = {str(name) for name in evidence.get("enforces") or []}
    for name in sorted(advertised - enforced):
        defects.append(Defect(
            "ADVERTISED_NOT_ENFORCED",
            f"{name} is advertised with an authority the endpoint does not check",
        ))
    for name in sorted(enforced - advertised):
        defects.append(Defect(
            "ADVERTISED_NOT_ENFORCED",
            f"{name} is reachable and absent from discovery",
        ))
    return defects


def _capable_node(evidence: dict[str, Any]) -> list[Defect]:
    defects: list[Defect] = []
    identity = evidence.get("identity") or {}
    if not identity.get("admitted"):
        defects.append(Defect(
            "SELF_WITNESSED_NODE",
            "the node identity is inferred rather than admitted through a transition",
        ))
    for operation in evidence.get("operations") or []:
        if not operation.get("checks_authority"):
            defects.append(Defect(
                "SELF_WITNESSED_NODE",
                f"{operation.get('operation', 'an operation')} checks no typed grant",
            ))
        if not operation.get("emits_receipt"):
            defects.append(Defect(
                "SELF_WITNESSED_NODE",
                f"{operation.get('operation', 'an operation')} leaves no receipt",
            ))
    observation = evidence.get("observation") or {}
    if not observation.get("observer"):
        defects.append(Defect("SELF_WITNESSED_NODE", "no independent observation exists"))
    elif observation.get("build_relation"):
        defects.append(Defect(
            "SELF_WITNESSED_NODE",
            f"{observation['observer']} has a build relation to the node it observed; "
            "a node that witnesses itself closed its circuit with itself at both ends",
        ))
    return defects


def judge_advance(from_stage: str, to_stage: str, evidence: dict[str, Any],
                  required_dimensions: set[str] | None = None) -> list[Defect]:
    """Grade one advance. An empty list admits it; anything else refuses by name."""
    names = stage_names()
    if to_stage not in names:
        return [Defect("UNKNOWN_STAGE", f"{to_stage} is not a stage this circuit declares")]
    if from_stage and from_stage not in names:
        return [Defect("UNKNOWN_STAGE", f"{from_stage} is not a stage this circuit declares")]

    start = ordinal(from_stage) if from_stage else 0
    target = ordinal(to_stage)
    if target <= start:
        return [Defect(
            "SKIPPED_STAGE",
            f"{to_stage} does not advance on {from_stage}; falling back is recorded, "
            "not judged here",
        )]
    if target - start > 1:
        return [Defect(
            "SKIPPED_STAGE",
            f"{from_stage} to {to_stage} skips "
            f"{', '.join(names[start:target - 1])}; each stage admission predicate is the "
            "previous stage evidence",
        )]

    if to_stage == "ROOT_POINT":
        return _root_point(evidence)
    if to_stage == "VERTICAL_SLICE":
        return _vertical_slice(evidence)
    if to_stage == "HORIZONTAL_SURFACE":
        return _horizontal_surface(evidence, required_dimensions or set())
    if to_stage == "EXPLODED_SURFACE":
        return _exploded_surface(evidence)
    return _capable_node(evidence)


def declared_refusals() -> dict[str, str]:
    """Every refusal code the circuit declares, with its meaning."""
    return dict(_circuit()["refusals"])
