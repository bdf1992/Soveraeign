"""Read current campaign state without becoming another phase authority.

`STATUS.yaml` says what is active now; `contracts/phases.json` preserves the
phase records. A fresh session needs both readings together, but this module is
only a reconciler: disagreement is a defect to surface, never a choice this
reader is allowed to settle.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any
import json


def _digest(path: Path) -> str:
    return "sha256:" + sha256(path.read_bytes()).hexdigest()


def _status_value(text: str, key: str) -> str:
    prefix = key + ":"
    for line in text.splitlines():
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return ""


def collect(root: Path) -> dict[str, Any]:
    """Reconcile the current STATUS reading with the append-preserving phase record."""
    status_path = root / "STATUS.yaml"
    phases_path = root / "contracts" / "phases.json"
    status_text = status_path.read_text(encoding="utf-8")
    phases = json.loads(phases_path.read_text(encoding="utf-8"))
    status_phase = _status_value(status_text, "phase")
    next_gate = _status_value(status_text, "next_gate")
    records = list(phases.get("phases", []))
    opened = [item for item in records if item.get("execution_status") == "OPEN"]
    defects: list[str] = []

    if len(opened) > 1:
        defects.append("PHASE_REGISTRY_MULTIPLE_OPEN")
    if status_phase == "NONE_ACTIVE":
        if opened:
            defects.append("STATUS_NONE_ACTIVE_WITH_OPEN_PHASE")
        active = None
    else:
        matches = [item for item in opened if item.get("phase_id") == status_phase]
        active = matches[0] if len(matches) == 1 else None
        if not status_phase:
            defects.append("STATUS_PHASE_MISSING")
        elif not matches:
            defects.append("STATUS_PHASE_NOT_OPEN_IN_REGISTRY")
        elif len(matches) > 1:
            defects.append("STATUS_PHASE_DUPLICATE")

    closed = [item for item in records if item.get("execution_status") == "CLOSED"]
    latest = closed[-1] if closed else None
    return {
        "status_phase": status_phase,
        "next_gate": next_gate,
        "active": active,
        "latest_terminal": latest,
        "defects": defects,
        "sources": [
            {"path": "STATUS.yaml", "digest": _digest(status_path)},
            {"path": "contracts/phases.json", "digest": _digest(phases_path)},
        ],
    }


def render(data: dict[str, Any]) -> list[str]:
    """Render a compact phase reading for SessionStart."""
    if data["defects"]:
        return ["phase state CONFLICT: " + ", ".join(data["defects"])]
    active = data.get("active")
    if active is None:
        lines = [f"phase: {data.get('status_phase') or 'UNKNOWN'}"
                 + (f"; next gate: {data['next_gate']}" if data.get("next_gate") else "")]
        latest = data.get("latest_terminal")
        if latest:
            lines.append(
                f"latest terminal: {latest.get('phase_id')} — {latest.get('terminal', 'UNKNOWN')}")
    else:
        lines = [
            f"phase: {active.get('phase_id')} — {active.get('title')} "
            f"({active.get('execution_status')})"
        ]
        if data.get("next_gate"):
            lines.append(f"next gate: {data['next_gate']}")
        clauses = active.get("exit_clauses") or []
        if clauses:
            lines.append("exit: " + "; ".join(
                f"{item.get('clause_id')}: {item.get('text')}" for item in clauses))
    sources = data.get("sources") or []
    if sources:
        lines.append("phase authority: " + " + ".join(
            f"{item['path']}@{item['digest'][7:19]}" for item in sources))
    return lines


__all__ = ["collect", "render"]
