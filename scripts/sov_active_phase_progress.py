"""Grade the progress floor of an active successor phase by its exit custodies."""

from __future__ import annotations

from pathlib import Path
import argparse
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from sovcustody import circuit as custody_circuit  # noqa: E402


def status_phase(root: Path = ROOT) -> str:
    """Read the phase token STATUS projects; the phase registry still owns existence."""
    text = (root / "STATUS.yaml").read_text(encoding="utf-8")
    match = re.search(r"(?m)^phase:\s*(\S+)\s*$", text)
    return match.group(1) if match else ""


def phase_record(phase_id: str, root: Path = ROOT) -> dict | None:
    """Resolve one phase from the authoritative phase history."""
    document = json.loads((root / "contracts/phases.json").read_text(encoding="utf-8"))
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


def read_active_phase(root: Path = ROOT) -> dict:
    """Assemble the active phase's exit-custody reading, floors included.

    `root` reaches STATUS, the phase registry, and the progress contract.
    `sovcustody.model` reads the repository root it resolves for itself, so a
    scratch root re-points three of the four sources and not the custody
    collection.
    """
    from sovcustody import model as custody_model  # noqa: PLC0415

    contract = json.loads((root / "contracts/phase-progress.json").read_bytes().decode("utf-8"))
    phase_id = status_phase(root)
    profile = (contract.get("active_phase_profiles") or {}).get(phase_id)
    phase = phase_record(phase_id, root)
    records = custody_model.custodies(phase_id)
    by_id = {str(item.get("custody_id")): item for item in records}
    floors = (profile or {}).get("exit_custody_floors") or {}

    rows = []
    clauses = (phase or {}).get("exit_clauses") or []
    for clause in clauses:
        custody_id = str(clause.get("held_by") or "")
        if not custody_id:
            continue
        custody = by_id.get(custody_id)
        rows.append({
            "clause": str(clause.get("clause_id") or clause.get("id") or ""),
            "verdict": str(clause.get("verdict") or "OPEN"),
            "custody_id": custody_id,
            "floor": str(floors.get(custody_id) or ""),
            "stage": custody_stage(custody) if custody else "",
            "target_stage": str((custody or {}).get("target_stage") or ""),
            "members": len((custody or {}).get("members") or []),
        })
    return {
        "phase": phase_id,
        "historical_phase": str(contract.get("historical_phase") or ""),
        "rows": rows,
        "defects": grade_active_phase(phase_id, phase, profile, records),
    }


def render(reading: dict) -> str:
    """One line per exit clause: where its custody stands against its floor."""
    phase_id = reading["phase"]
    if not phase_id or phase_id == "NONE_ACTIVE":
        return "active phase: NONE_ACTIVE; no exit custody carries a live floor"
    if phase_id == reading["historical_phase"]:
        return f"active phase: {phase_id} is the historical phase; its floors are non-regression only"

    lines = [f"active phase: {phase_id}"]
    for row in reading["rows"]:
        stage = row["stage"] or "no stage"
        floor = row["floor"] or "NO FLOOR"
        held = "at floor" if custody_circuit.at_least(row["stage"], row["floor"]) else "BELOW FLOOR"
        if not row["floor"]:
            held = "UNTRACKED"
        if row["verdict"] == "EARNED":
            held = "earned"
        lines.append(
            f"  {row['clause']:<8} {row['custody_id']}"
            f"\n           {stage} against floor {floor} toward {row['target_stage']}"
            f" - {held}, {row['members']} member(s)")
    return "\n".join(lines)


def main() -> int:
    """Print the reading the exit custodies declare as their closure check."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", dest="as_json", action="store_true",
                        help="emit machine-readable output")
    args = parser.parse_args()

    reading = read_active_phase()
    if args.as_json:
        print(json.dumps(reading, indent=2))
    else:
        print(render(reading))
        print()
        for defect in reading["defects"]:
            print(f"DEFECT {defect['code']}: {defect['detail']}")
    if reading["defects"]:
        return 1
    if not args.as_json:
        print("PASS: every unearned exit clause has a custody at or above its recorded floor")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
