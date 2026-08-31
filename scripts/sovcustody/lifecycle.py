"""Read and grade the composed work lifecycle declared by concern admission.

This module does not create a second work model. It reads the composition already
owned by custody, leases, closure, landing and settlement and makes the joins
visible in one place.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "contracts" / "concern-admission.json"

REQUIRED_ROLES = {"CONCERN", "CUSTODY", "LEASE", "CLOSURE", "LANDING", "SETTLEMENT", "QUEUE"}
REQUIRED_STEPS = {"ADMIT", "TAKE", "WORK", "INTEGRATE", "RECONCILE", "RELEASE_ATTENTION"}
POTENTIAL_STATES = {"CURRENT", "PARTIAL", "CHARTED"}


def read(path: Path = CONTRACT) -> dict[str, Any]:
    """Return the declared work lifecycle."""
    document = json.loads(path.read_text(encoding="utf-8"))
    return dict(document.get("work_lifecycle") or {})


def defects(lifecycle: dict[str, Any] | None = None) -> list[str]:
    """Return structural defects in the lifecycle composition."""
    lifecycle = lifecycle or read()
    problems: list[str] = []
    roles = lifecycle.get("roles") or {}
    missing_roles = sorted(REQUIRED_ROLES - set(roles))
    if missing_roles:
        problems.append("missing roles: " + ", ".join(missing_roles))

    for role, spec in roles.items():
        owner = str((spec or {}).get("owned_by") or "")
        if not owner:
            problems.append(f"{role}: owned_by is missing")
        elif owner != "derived projection" and not (ROOT / owner).exists():
            problems.append(f"{role}: owner does not resolve: {owner}")
        if not str((spec or {}).get("means") or ""):
            problems.append(f"{role}: means is missing")

    flow = lifecycle.get("flow") or []
    steps = {str(item.get("step")) for item in flow}
    missing_steps = sorted(REQUIRED_STEPS - steps)
    if missing_steps:
        problems.append("missing flow steps: " + ", ".join(missing_steps))
    for item in flow:
        for field in ("from", "to"):
            value = item.get(field)
            if value not in roles:
                problems.append(f"{item.get('step')}: {field} names unknown role {value}")

    wake = lifecycle.get("wake_policy") or {}
    if set(wake.get("absorb_when") or []) != {"same_service", "same_effect_class", "same_authority"}:
        problems.append("wake_policy: absorb_when drifted from closure ownership")
    if not wake.get("separate_rule") or not wake.get("close_rule"):
        problems.append("wake_policy: separate_rule and close_rule are required")

    queue = lifecycle.get("queue_projection") or {}
    if queue.get("owns_work") is not False:
        problems.append("queue_projection: queue must not own work")
    if queue.get("selection_is_authority") is not False:
        problems.append("queue_projection: selection must not grant authority")

    potentials = lifecycle.get("potential_extensions") or []
    ids: set[str] = set()
    for potential in potentials:
        identity = str(potential.get("id") or "")
        if not identity:
            problems.append("potential extension has no id")
        elif identity in ids:
            problems.append(f"duplicate potential extension: {identity}")
        ids.add(identity)
        state = potential.get("status")
        if state not in POTENTIAL_STATES:
            problems.append(f"{identity or 'potential'}: unknown status {state}")
        if not potential.get("potential"):
            problems.append(f"{identity or 'potential'}: potential is missing")
    return problems


def render(lifecycle: dict[str, Any] | None = None) -> str:
    """Render the lifecycle and its charted extensions for a terminal reader."""
    lifecycle = lifecycle or read()
    lines = ["WORK LIFECYCLE", "", str(lifecycle.get("principle") or ""), "", "roles"]
    for role, spec in (lifecycle.get("roles") or {}).items():
        lines.append(f"  {role:<12} {spec['means']}")
        lines.append(f"               owner: {spec['owned_by']}")
    lines.extend(["", "flow"])
    for item in lifecycle.get("flow") or []:
        lines.append(f"  {item['step']:<18} {item['from']} -> {item['to']}")
        lines.append(f"                     {item['means']}")
    wake = lifecycle.get("wake_policy") or {}
    lines.extend(["", "reconciliation wake", f"  {wake.get('means', '')}",
                  "  absorb when: " + ", ".join(wake.get("absorb_when") or []),
                  f"  distinct: {wake.get('separate_rule', '')}",
                  f"  closure:  {wake.get('close_rule', '')}"])
    lines.extend(["", "potential"])
    for item in lifecycle.get("potential_extensions") or []:
        lines.append(f"  {item['status']:<8} {item['id']:<28} {item['potential']}")
    return "\n".join(lines)
