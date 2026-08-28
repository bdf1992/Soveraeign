"""Separation rules for a three-tier run.

`SDLC.md` fixes the loop in prose: three tiers, grants that narrow downward,
reports that never settle themselves, and a verification dyad whose two hands
are never held by one operator. Prose cannot refuse a run. These rules read a
run record and name every disagreement, so a loop that quietly widened its own
grant fails here instead of succeeding silently.

Every function is pure. Nothing here reads a clock, a network, or a model.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json

TABLE = Path(__file__).resolve().parents[2] / "contracts" / "tier-bindings.json"


def load_table(root: Path | None = None) -> dict[str, Any]:
    """Read the declared tier-binding table."""
    path = TABLE if root is None else root / "contracts" / "tier-bindings.json"
    return json.loads(path.read_bytes().decode("utf-8"))


def check_depth(run: dict[str, Any], table: dict[str, Any]) -> list[str]:
    """The chain is exactly the declared tiers, in the declared order.

    `SDLC.md` fixes tier depth at three: a deeper chain adds crossings and
    receipts without adding a new kind of accountability, and a shallower one
    drops a settlement hand.
    """
    declared = table["tier_order"]
    observed = [step.get("tier") for step in run.get("chain", [])]
    if observed != declared:
        return [f"TIER_DEPTH_REFUSED: chain is {observed}, declared order is {declared}"]
    return []


def check_grants_narrow(run: dict[str, Any], table: dict[str, Any]) -> list[str]:
    """Each tier holds only its declared verbs, over a strictly narrower scope.

    `SDLC.md`: grants flow downward and narrow at every step. What narrows is the
    authority scope, not the verb set - a worker executes, which its orchestrator
    does not do itself. So two things are checked: a tier never claims a verb the
    table withheld from it, and its scope is strictly inside its parent's.
    """
    defects: list[str] = []
    parent_scope = ""
    parent_tier = ""
    for step in run.get("chain", []):
        tier = step.get("tier", "")
        held = set(step.get("capabilities", []))
        declared = set(table["tiers"].get(tier, {}).get("capabilities", []))
        for extra in sorted(held - declared):
            defects.append(f"GRANT_NOT_NARROWED: {tier} claims {extra}, "
                           f"which contracts/tier-bindings.json does not grant it")
        for withheld in sorted(held & set(table["tiers"].get(tier, {}).get("may_not", []))):
            defects.append(f"GRANT_NOT_NARROWED: {tier} claims {withheld}, "
                           f"which the table forbids it")
        scope = step.get("scope", "")
        if parent_scope:
            if not scope.startswith(parent_scope + "/"):
                defects.append(f"GRANT_NOT_NARROWED: {tier} scope {scope!r} is not "
                               f"strictly inside {parent_tier} scope {parent_scope!r}")
        parent_scope, parent_tier = scope, tier
    return defects


def check_no_self_settlement(run: dict[str, Any], _: dict[str, Any]) -> list[str]:
    """The actor that produced a report is not the actor that settled it."""
    report = run.get("report") or {}
    settlement = run.get("settlement") or {}
    producer, settler = report.get("produced_by"), settlement.get("settled_by")
    if producer and settler and producer == settler:
        return [f"SELF_SETTLEMENT_REFUSED: {producer} settled the report it produced"]
    return []


def check_no_self_witness(run: dict[str, Any], table: dict[str, Any]) -> list[str]:
    """The binding that produced an output is not the binding that observed it.

    `SDLC.md`: no operator holds both hands of a dyad. An observation by the
    producing binding is an executor self-report wearing an observer's name.
    """
    observation = run.get("observation") or {}
    observer = observation.get("observer_binding_id")
    observed = observation.get("observed_binding_id")
    if observer and observed and observer == observed:
        return [f"SELF_WITNESS_REFUSED: binding {observer} observed its own output"]
    declared = table.get("observation", {}).get("observer_binding_id")
    if observer and declared and observer != declared:
        return [f"SELF_WITNESS_REFUSED: observer {observer} is not the declared "
                f"observer binding {declared}"]
    return []


_EFFECT_ORDER = ("RECORD_LOCAL", "RESOURCE_CONSUMPTION", "EXTERNAL_WORLD")


def check_effect_ceiling(run: dict[str, Any], table: dict[str, Any]) -> list[str]:
    """No tier exceeds its declared ceiling, and Phase I refuses external effects."""
    defects: list[str] = []
    refused = set(table.get("phase_refused_effect_classes", []))
    for step in run.get("chain", []):
        tier, effect = step.get("tier", ""), step.get("effect_class")
        if effect is None:
            continue
        if effect in refused:
            defects.append(f"EFFECT_CLASS_REFUSED: {tier} declared {effect}, "
                           "which this phase refuses")
            continue
        ceiling = table["tiers"].get(tier, {}).get("max_effect_class")
        if effect not in _EFFECT_ORDER:
            defects.append(f"EFFECT_CLASS_REFUSED: {tier} declared unknown class {effect}")
        elif ceiling and _EFFECT_ORDER.index(effect) > _EFFECT_ORDER.index(ceiling):
            defects.append(f"EFFECT_CLASS_REFUSED: {tier} declared {effect} above "
                           f"its ceiling {ceiling}")
    return defects


def check_bindings_declared(run: dict[str, Any], table: dict[str, Any]) -> list[str]:
    """Every tier runs on the binding the table declares for it."""
    defects: list[str] = []
    for step in run.get("chain", []):
        tier, binding = step.get("tier", ""), step.get("binding_id")
        declared = table["tiers"].get(tier, {}).get("binding_id")
        if binding and declared and binding != declared:
            defects.append(f"BINDING_UNDECLARED: {tier} ran on {binding}, "
                           f"the table declares {declared}")
    return defects


def check_provenance(run: dict[str, Any], table: dict[str, Any]) -> list[str]:
    """Every model invocation records each declared provenance field.

    `PRD.md` PROD-I-9 requires each run to record binding, adapter, provider,
    model, version, runtime, host, input projection, omissions, data boundary,
    usage, and cost. A missing field is not a cosmetic gap: it is a run that
    cannot be reconstructed or attributed.
    """
    defects: list[str] = []
    required = table["provenance_fields"]
    for index, invocation in enumerate(run.get("invocations", [])):
        for field in required:
            if invocation.get(field) in (None, "", [], {}):
                defects.append(f"PROVENANCE_INCOMPLETE: invocation {index} omits {field}")
    return defects


CHECKS = (check_depth, check_grants_narrow, check_no_self_settlement, check_no_self_witness,
          check_effect_ceiling, check_bindings_declared, check_provenance)


def audit(run: dict[str, Any], table: dict[str, Any]) -> list[str]:
    """Every separation defect in one run record, in declared check order."""
    defects: list[str] = []
    for check in CHECKS:
        defects.extend(check(run, table))
    return defects
