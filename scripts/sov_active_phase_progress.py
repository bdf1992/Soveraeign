"""Grade the progress floor of an active successor phase by its exit custodies."""

from __future__ import annotations

from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from sovcustody import circuit as custody_circuit  # noqa: E402


def status_phase() -> str:
    """Read the phase token STATUS projects; the phase registry still owns existence."""
    text = (ROOT / "STATUS.yaml").read_text(encoding="utf-8")
    match = re.search(r"(?m)^phase:\s*(\S+)\s*$", text)
    return match.group(1) if match else ""


def phase_record(phase_id: str) -> dict | None:
    """Resolve one phase from the authoritative phase history."""
    document = json.loads((ROOT / "contracts/phases.json").read_text(encoding="utf-8"))
    return next((phase for phase in document.get("phases", [])
                 if phase.get("phase_id") == phase_id), None)


def custody_stage(custody: dict) -> str:
    """Return the least-drawn member stage, matching the custody board progress rule."""
    stages = [str(member.get("stage") or "") for member in custody.get("members") or []]
    stages = [stage for stage in stages if custody_circuit.ordinal(stage)]
    if stages:
        return min(stages, key=custody_circuit.ordinal)
    return str(custody.get("entry_stage") or "")


def grade_active_phase(
    phase_id: str, phase: dict | None, profile: dict | None, records: list[dict],
) -> list[dict]:
    """Refuse an active phase whose exit custody lacks an initialized monotonic floor."""
    if profile is None:
        return [{
            "code": "ACTIVE_PHASE_PROGRESS_UNINITIALIZED",
            "detail": f"{phase_id} is active but has no initialized phase-progress profile",
        }]
    if phase is None:
        return [{
            "code": "ACTIVE_PHASE_PROGRESS_UNINITIALIZED",
            "detail": f"{phase_id} is active in STATUS but absent from contracts/phases.json",
        }]

    defects: list[dict] = []
    by_id = {str(item.get("custody_id")): item for item in records
             if item.get("phase") == phase_id}
    required = {str(clause.get("held_by")) for clause in phase.get("exit_clauses", [])
                if clause.get("verdict") != "EARNED" and clause.get("held_by")}
    floors = profile.get("exit_custody_floors") or {}

    for custody_id in sorted(required):
        custody = by_id.get(custody_id)
        if custody is None:
            defects.append({
                "code": "MISSING_EXIT_CUSTODY",
                "detail": f"{phase_id} exit points to {custody_id}, absent from its custody collection",
            })
            continue
        floor = floors.get(custody_id)
        if not floor:
            defects.append({
                "code": "EXIT_CUSTODY_UNTRACKED",
                "detail": f"{custody_id} owns an active exit but has no recorded progress floor",
            })
            continue
        current = custody_stage(custody)
        if not custody_circuit.at_least(current, str(floor)):
            defects.append({
                "code": "CUSTODY_STAGE_REGRESSION",
                "detail": f"{custody_id} reads {current or 'no stage'} below floor {floor}",
            })

    for custody_id in sorted(set(floors) - required):
        defects.append({
            "code": "EXIT_CUSTODY_UNTRACKED",
            "detail": f"progress floor names {custody_id}, which owns no unearned exit in {phase_id}",
        })
    return defects
