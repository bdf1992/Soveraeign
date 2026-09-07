"""Grade the progress floor of an active successor phase by its exit custodies.

Running this module prints that grading. It did not until 2026-09-07: it held only
functions, so `python scripts/sov_active_phase_progress.py` exited 0 and printed
nothing while CLAUDE.md and decisions/0102 both told a fresh participant to run it.
Seven witness passes recorded the silence -- three of them as "pass-1 residual
reproduced" -- and none could refuse it, because a module with no entry point has
no behaviour to defeat. That is the discoverability defect the active phase's own
P15-X1 names, standing in the instrument meant to report it.
"""

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


def report(phase_id: str, phase: dict | None, profile: dict | None,
           records: list[dict]) -> list[str]:
    """The reading a fresh participant gets: every exit, its custody, and what carries it."""
    if not phase_id or phase_id.upper() == "NONE_ACTIVE":
        return ["no active successor phase; historical non-regression is graded by "
                "scripts/sov_phase_progress.py"]
    lines = [f"{phase_id} - {phase.get('title') or '(untitled)'}" if phase else phase_id]
    if phase is None:
        return lines + [f"{phase_id} is active in STATUS but absent from contracts/phases.json"]

    by_id = {str(item.get("custody_id")): item for item in records}
    floors = (profile or {}).get("exit_custody_floors") or {}
    clauses = phase.get("exit_clauses") or []
    lines.append(f"{len(clauses)} exit clause(s); "
                 f"{sum(1 for c in clauses if c.get('verdict') == 'EARNED')} earned")
    lines.append("")
    empty: list[str] = []
    for clause in clauses:
        held = str(clause.get("held_by") or "")
        custody = by_id.get(held)
        members = (custody or {}).get("members") or []
        stage = custody_stage(custody) if custody else ""
        short = held.rsplit("/", 1)[-1] if held else "(no custody)"
        carried = f"{len(members)} member(s)" if members else "NO MEMBER"
        if not members:
            empty.append(f"{clause.get('clause_id')} ({short})")
        lines.append(f"  {str(clause.get('clause_id')):8} {short:24} "
                     f"{stage or '-':20} floor {str(floors.get(held) or '-'):20} "
                     f"{carried:12} {clause.get('verdict') or ''}")
    if empty:
        lines += ["", f"{len(empty)} exit clause(s) carry no member, so nothing in the tree "
                      "advances them:", "  " + ", ".join(empty),
                  "  Reported, not refused: an exit may legitimately wait on the ones before "
                  "it, and a root acceptance act has no member by construction."]
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Grade the active phase by its exit custodies.")
    parser.add_argument("--json", action="store_true", help="emit the defects as JSON")
    args = parser.parse_args(argv)
    phase_id = status_phase()
    phase = phase_record(phase_id) if phase_id else None
    contract = json.loads((ROOT / "contracts/phase-progress.json").read_text(encoding="utf-8"))
    profile = (contract.get("active_phase_profiles") or {}).get(phase_id)
    from sovcustody import model as custody_model
    records = list(custody_model.custodies(phase_id)) if phase_id else []
    defects = ([] if not phase_id or phase_id.upper() == "NONE_ACTIVE"
               else grade_active_phase(phase_id, phase, profile, records))
    if args.json:
        print(json.dumps({"phase": phase_id, "defects": defects}, indent=2))
        return 1 if defects else 0
    for line in report(phase_id, phase, profile, records):
        print(line)
    for defect in defects:
        print(f"  {defect['code']}: {defect['detail']}")
    if defects:
        print(f"FAIL: {len(defects)} active phase-progress defect(s)")
        return 1
    print("PASS: no exit custody reads below the floor its phase opened against")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
