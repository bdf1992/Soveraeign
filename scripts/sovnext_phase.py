"""Phase-authority and custody projection for the non-authoritative next-work reader."""

from __future__ import annotations

from pathlib import Path
import re

from sovcustody import collections as custody_collections
from sovsession import phase_context


def position(root: Path) -> tuple[dict, list[dict]]:
    """Current phase authority plus only that active phase's custody records."""
    state = phase_context.collect(root)
    active = state.get("active")
    if active is None or state.get("defects"):
        return state, []
    phase_id = str(active.get("phase_id"))
    records = custody_collections.records(
        root / "contracts" / "custodies.json", root / "contracts" / "custodies", phase_id)
    return state, records


def prepared_horizons(root: Path) -> list[str]:
    """Prepared human-readable successor horizons; never phase standing."""
    contracts = root / "contracts"
    if not contracts.is_dir():
        return []
    return [path.relative_to(root).as_posix()
            for path in sorted(contracts.glob("phase-*-horizon.md")) if path.is_file()]


def active_custody_members(custodies: list[dict], ready: list[dict[str, str]]) -> list[dict]:
    """Work already drawn under active-phase custody, without promoting it."""
    ready_by_number = {row["number"]: row for row in ready}
    rows = []
    for custody in custodies:
        if custody.get("terminal"):
            continue
        custody_id = str(custody.get("custody_id") or "")
        for member in custody.get("members") or []:
            if member.get("work_state") == "RETIRED":
                continue
            row = {
                "custody_id": custody_id,
                "address": str(member.get("address") or ""),
                "member_kind": member.get("member_kind"),
                "stage": member.get("stage"),
                "standing": member.get("standing"),
                "work_state": member.get("work_state"),
                "epic_reachable": False,
            }
            match = re.search(r"(?:issue:)?#(\d+)$", row["address"])
            if match and match.group(1) in ready_by_number:
                row["epic_reachable"] = True
                row["ticket"] = ready_by_number[match.group(1)]
            rows.append(row)
    return rows


def render_precedence(active_phase: dict | None, custodies: list[dict],
                      members: list[dict], horizons: list[str]) -> list[str]:
    """Render the authority-first portion of next-work output."""
    lines: list[str] = []
    if active_phase is not None:
        lines.append("== active phase custody ==")
        if custodies:
            for custody in custodies:
                terminal = custody.get("terminal")
                state = terminal.get("outcome") if isinstance(terminal, dict) else "OPEN"
                lines.append(
                    f"  {custody.get('custody_id')}  {state}: {custody.get('initiative', '')}")
        else:
            lines.append("  none — active phase has no phase-scoped custody; this is opening debt")
        lines.extend(["", "== active phase work =="])
        if members:
            for member in members:
                marker = "epic-reachable" if member.get("epic_reachable") else "drawn"
                lines.append(f"  {member['address']} [{member.get('work_state')}] {marker}")
                lines.append(f"      custody {member['custody_id']}")
        else:
            lines.append("  none drawn under active phase custody")
    else:
        lines.append("== prepared successor context ==")
        if horizons:
            lines.extend(f"  {horizon}  (context only; no standing)" for horizon in horizons)
        else:
            lines.append("  none")
    lines.extend(["", "== roadmap forecast (non-authoritative) =="])
    return lines


__all__ = ["position", "prepared_horizons", "active_custody_members", "render_precedence"]
