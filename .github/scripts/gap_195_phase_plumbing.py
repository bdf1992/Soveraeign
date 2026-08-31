from __future__ import annotations

from pathlib import Path
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SELF = ROOT / ".github" / "scripts" / "gap_195_phase_plumbing.py"
WORKFLOW = ROOT / ".github" / "workflows" / "gap-195-phase-plumbing.yml"


def run(*args: str, capture: bool = False) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, cwd=ROOT, text=True, capture_output=capture, check=False)
    if result.returncode:
        if capture:
            print(result.stdout)
            print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)
    return result


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise SystemExit(f"expected text absent in {path.relative_to(ROOT)}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


def assert_closed() -> None:
    status = (ROOT / "STATUS.yaml").read_text(encoding="utf-8")
    phases = json.loads((ROOT / "contracts/phases.json").read_text(encoding="utf-8"))
    if "phase: NONE_ACTIVE" not in status:
        raise SystemExit("refuse: successor already active")
    if len(phases.get("phases", [])) != 1:
        raise SystemExit("refuse: phase registry already contains a successor")


def patch_custody_model() -> None:
    path = ROOT / "scripts/sovcustody/model.py"
    old = 'COLLECTION = ROOT / "contracts" / "custodies.json"\nSEATS = ROOT / "contracts" / "seat-registry.json"\n'
    new = ('COLLECTION = ROOT / "contracts" / "custodies.json"\n'
           'COLLECTION_DIR = ROOT / "contracts" / "custodies"\n'
           'SEATS = ROOT / "contracts" / "seat-registry.json"\n')
    replace_once(path, old, new)
    old = '''def collection() -> dict[str, Any]:\n    return json.loads(COLLECTION.read_bytes().decode("utf-8"))\n\n\ndef custodies() -> list[dict[str, Any]]:\n    return list(collection()["custodies"])\n\n\ndef by_id(custody_id: str) -> dict[str, Any] | None:\n    for custody in custodies():\n        if custody["custody_id"] == custody_id:\n            return custody\n    return None\n'''
    new = '''def collection() -> dict[str, Any]:\n    """The historical legacy collection, retained for compatibility."""\n    return json.loads(COLLECTION.read_bytes().decode("utf-8"))\n\n\ndef collection_paths() -> tuple[Path, ...]:\n    """Every custody collection, with the historical Phase-I record first."""\n    paths: list[Path] = []\n    if COLLECTION.exists():\n        paths.append(COLLECTION)\n    if COLLECTION_DIR.exists():\n        paths.extend(sorted(path for path in COLLECTION_DIR.glob("*.json") if path.is_file()))\n    return tuple(paths)\n\n\ndef collections() -> list[dict[str, Any]]:\n    """Read every collection independently; filenames grant no authority."""\n    return [json.loads(path.read_bytes().decode("utf-8")) for path in collection_paths()]\n\n\ndef custodies(phase: str | None = None) -> list[dict[str, Any]]:\n    """Every custody across history, optionally restricted to one phase."""\n    records = [custody for document in collections() for custody in document.get("custodies", [])]\n    if phase is not None:\n        records = [custody for custody in records if custody.get("phase") == phase]\n    return records\n\n\ndef by_id(custody_id: str) -> dict[str, Any] | None:\n    for custody in custodies():\n        if custody["custody_id"] == custody_id:\n            return custody\n    return None\n'''
    replace_once(path, old, new)


def patch_custody_commands() -> None:
    path = ROOT / "scripts/sovcustody/commands.py"
    replace_once(path, '    records = modelmod.custodies()\n    if args.as_json:\n',
                 '    records = modelmod.custodies(getattr(args, "phase", None))\n    if args.as_json:\n')
    old = '''    records = modelmod.custodies()\n    if args.custody_id:\n'''
    new = '''    records = modelmod.custodies(getattr(args, "phase", None))\n    if args.custody_id:\n'''
    replace_once(path, old, new)
    old = '''    records = {custody["custody_id"]: custody for custody in modelmod.custodies()}\n    defects = phasemod.grade_collection(custody_ids=set(records))\n    rows = []\n    for phase in phasemod.phases():\n'''
    new = '''    requested_phase = getattr(args, "phase", None)\n    selected = modelmod.custodies(requested_phase) if requested_phase else modelmod.custodies()\n    records = {custody["custody_id"]: custody for custody in selected}\n    phases = [phase for phase in phasemod.phases()\n              if requested_phase is None or phase["phase_id"] == requested_phase]\n    if requested_phase and not phases:\n        print(f"REFUSED: no phase named {requested_phase}")\n        return 1\n    defects = phasemod.grade_collection(phases, custody_ids=set(records))\n    rows = []\n    for phase in phases:\n'''
    replace_once(path, old, new)


def patch_custody_cli() -> None:
    path = ROOT / "scripts/sov_custody.py"
    replace_once(path,
                 '    subparsers.add_parser("list", help="every custody and where it stands")\n',
                 '    listing = subparsers.add_parser("list", help="every custody and where it stands")\n'
                 '    listing.add_argument("--phase", help="show one phase custody collection")\n')
    replace_once(path,
                 '    estimate.add_argument("custody_id", nargs="?")\n    subparsers.add_parser("reconcile", help="phase exit clauses against custodies")\n',
                 '    estimate.add_argument("custody_id", nargs="?")\n'
                 '    estimate.add_argument("--phase", help="estimate only one phase collection")\n'
                 '    reconcile = subparsers.add_parser("reconcile", help="phase exit clauses against custodies")\n'
                 '    reconcile.add_argument("--phase", help="reconcile one phase only")\n')


def patch_progress_contract() -> None:
    path = ROOT / "contracts/phase-progress.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["version"] = "1.1.0"
    doc["historical_phase"] = "phase:i"
    doc["active_phase_profiles"] = doc.get("active_phase_profiles", {})
    doc["active_refusals"] = [
        {
            "code": "ACTIVE_PHASE_PROGRESS_UNINITIALIZED",
            "fires_when": "STATUS names an active successor phase and phase-progress has no initialized profile for it",
            "why_it_refuses": "an active campaign whose own progress unit is absent from the verifier repeats the Phase-I failure"
        },
        {
            "code": "MISSING_EXIT_CUSTODY",
            "fires_when": "an unearned exit clause points to a custody absent from that phase's live collection",
            "why_it_refuses": "an exit carried by nobody cannot stay on the critical path of work"
        },
        {
            "code": "EXIT_CUSTODY_UNTRACKED",
            "fires_when": "an active exit custody has no initialized stage floor, or a floor names something no active exit carries",
            "why_it_refuses": "the floor must account for exactly the work that owns the active exit"
        },
        {
            "code": "CUSTODY_STAGE_REGRESSION",
            "fires_when": "an active exit custody falls below the stage recorded in its phase-opening/progress floor",
            "why_it_refuses": "a regression is attributable to the change that moved the custody backwards and may not disappear into a board projection"
        }
    ]
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8", newline="\n")


def patch_phase_progress() -> None:
    path = ROOT / "scripts/sov_phase_progress.py"
    replace_once(path, 'import subprocess\n\nimport sov_f2_gate\n',
                 'import subprocess\nimport re\n\nimport sov_f2_gate\nfrom sovcustody import circuit as custody_circuit\n')
    anchor = '''def grade(report: dict, contract: dict) -> list[dict]:\n'''
    insert = '''def status_phase() -> str:\n    """The active phase named by STATUS, without treating STATUS as a phase registry."""\n    text = (ROOT / "STATUS.yaml").read_text(encoding="utf-8")\n    match = re.search(r"(?m)^phase:\\s*(\\S+)\\s*$", text)\n    return match.group(1) if match else ""\n\n\ndef phase_record(phase_id: str) -> dict | None:\n    document = json.loads((ROOT / "contracts/phases.json").read_text(encoding="utf-8"))\n    return next((phase for phase in document.get("phases", [])\n                 if phase.get("phase_id") == phase_id), None)\n\n\ndef custody_stage(custody: dict) -> str:\n    """The least-drawn member stage, matching the custody board's progress rule."""\n    stages = [str(member.get("stage") or "") for member in custody.get("members") or []]\n    stages = [stage for stage in stages if custody_circuit.ordinal(stage)]\n    if stages:\n        return min(stages, key=custody_circuit.ordinal)\n    return str(custody.get("entry_stage") or "")\n\n\ndef grade_active_phase(\n    phase_id: str, phase: dict | None, profile: dict | None, records: list[dict],\n) -> list[dict]:\n    """Refuse an active phase whose exit custody has no initialized monotonic floor."""\n    if profile is None:\n        return [{\n            "code": "ACTIVE_PHASE_PROGRESS_UNINITIALIZED",\n            "detail": f"{phase_id} is active but has no initialized phase-progress profile",\n        }]\n    if phase is None:\n        return [{\n            "code": "ACTIVE_PHASE_PROGRESS_UNINITIALIZED",\n            "detail": f"{phase_id} is active in STATUS but absent from contracts/phases.json",\n        }]\n\n    defects: list[dict] = []\n    by_id = {str(item.get("custody_id")): item for item in records\n             if item.get("phase") == phase_id}\n    required = {str(clause.get("held_by")) for clause in phase.get("exit_clauses", [])\n                if clause.get("verdict") != "EARNED" and clause.get("held_by")}\n    floors = profile.get("exit_custody_floors") or {}\n\n    for custody_id in sorted(required):\n        custody = by_id.get(custody_id)\n        if custody is None:\n            defects.append({\n                "code": "MISSING_EXIT_CUSTODY",\n                "detail": f"{phase_id} exit points to {custody_id}, absent from its custody collection",\n            })\n            continue\n        floor = floors.get(custody_id)\n        if not floor:\n            defects.append({\n                "code": "EXIT_CUSTODY_UNTRACKED",\n                "detail": f"{custody_id} owns an active exit but has no recorded progress floor",\n            })\n            continue\n        current = custody_stage(custody)\n        if not custody_circuit.at_least(current, str(floor)):\n            defects.append({\n                "code": "CUSTODY_STAGE_REGRESSION",\n                "detail": f"{custody_id} reads {current or 'no stage'} below floor {floor}",\n            })\n\n    for custody_id in sorted(set(floors) - required):\n        defects.append({\n            "code": "EXIT_CUSTODY_UNTRACKED",\n            "detail": f"progress floor names {custody_id}, which owns no unearned exit in {phase_id}",\n        })\n    return defects\n\n\n'''
    text = path.read_text(encoding="utf-8")
    if 'def grade_active_phase(' not in text:
        if anchor not in text:
            raise SystemExit("phase progress grade anchor absent")
        text = text.replace(anchor, insert + anchor, 1)
        path.write_text(text, encoding="utf-8", newline="\n")

    old = '''    defects = grade(report, contract)\n    drift = stall(contract)\n\n    covered, total = report["predicates_covered"], report["predicates_total"]\n'''
    new = '''    defects = grade(report, contract)\n    drift = stall(contract)\n    active = status_phase()\n    active_defects: list[dict] = []\n    if active and active != "NONE_ACTIVE" and active != contract.get("historical_phase"):\n        from sovcustody import model as custody_model\n        active_defects = grade_active_phase(\n            active, phase_record(active),\n            (contract.get("active_phase_profiles") or {}).get(active),\n            custody_model.custodies(active),\n        )\n    defects.extend(active_defects)\n\n    covered, total = report["predicates_covered"], report["predicates_total"]\n'''
    replace_once(path, old, new)
    old = '''    for defect in defects:\n        print(f"  {defect['code']}: {defect['detail']}")\n'''
    new = '''    if active == "NONE_ACTIVE":\n        print("  active    NONE_ACTIVE; historical non-regression remains enforced")\n    elif active and active != contract.get("historical_phase"):\n        profile = (contract.get("active_phase_profiles") or {}).get(active)\n        state = "initialized" if profile else "UNINITIALIZED"\n        print(f"  active    {active} progress profile {state}")\n    for defect in defects:\n        print(f"  {defect['code']}: {defect['detail']}")\n'''
    replace_once(path, old, new)
    old = '''    contract = _contract()\n    report = sov_f2_gate.read_gate()\n    covered = report["predicates_covered"]\n'''
    new = '''    contract = _contract()\n    active = status_phase()\n    if active not in ("", "NONE_ACTIVE", contract.get("historical_phase")):\n        print(f"REFUSED: raise-floor is the historical {contract.get('historical_phase')} reader; "\n              f"initialize {active} exit-custody floors in the phase opening/progress record")\n        return 1\n    report = sov_f2_gate.read_gate()\n    covered = report["predicates_covered"]\n'''
    replace_once(path, old, new)
    old = '''    print(json.dumps({\n        "reading": sov_f2_gate.read_gate()["predicates_covered"],\n        "floor": contract["floor"],\n        "stall": stall(contract),\n    }, indent=2, sort_keys=True))\n'''
    new = '''    active = status_phase()\n    print(json.dumps({\n        "historical_phase": contract.get("historical_phase"),\n        "reading": sov_f2_gate.read_gate()["predicates_covered"],\n        "floor": contract["floor"],\n        "stall": stall(contract),\n        "active_phase": active or None,\n        "active_profile": (contract.get("active_phase_profiles") or {}).get(active),\n    }, indent=2, sort_keys=True))\n'''
    replace_once(path, old, new)


def patch_verify_warrant() -> None:
    path = ROOT / "scripts/sovverify/checks.py"
    old = '''          "between them against a recorded floor, so the number that defines the phase is one "\n          "something refuses on; it never reads a prior gate report or any claim that coverage "\n          "was added. The F2 gate itself is deliberately not the check: registering it would "\n'''
    new = '''          "between them against the preserved Phase-I floor, and when STATUS names a later "\n          "active phase it also requires every unearned exit custody to have an initialized "\n          "stage floor and refuses regression below it. It never reads a stored board or prior "\n          "gate report. The F2 gate itself is deliberately not the check: registering it would "\n'''
    replace_once(path, old, new)
    old = '''          ("SPEC.md", "conformance/oracle-controls.json", "contracts/phase-progress.json",\n           "scripts/sov_f2_gate.py", "scripts/sov_phase_progress.py")),\n'''
    new = '''          ("SPEC.md", "STATUS.yaml", "contracts/phases.json",\n           "conformance/oracle-controls.json", "contracts/phase-progress.json",\n           "contracts/custodies.json", "contracts/custodies",\n           "scripts/sov_f2_gate.py", "scripts/sov_phase_progress.py", "scripts/sovcustody")),\n'''
    replace_once(path, old, new)


def apply() -> None:
    assert_closed()
    patch_custody_model()
    patch_custody_commands()
    patch_custody_cli()
    patch_progress_contract()
    patch_phase_progress()
    patch_verify_warrant()


def refresh_clarity() -> None:
    coverage = json.loads((ROOT / ".clarity/coverage.json").read_text(encoding="utf-8"))
    candidates = list(coverage.get("reviews", {}).keys())
    for _ in range(5):
        result = subprocess.run([sys.executable, "scripts/sov_clarity.py", "check"], cwd=ROOT,
                                text=True, capture_output=True, check=False)
        output = result.stdout + "\n" + result.stderr
        stale = []
        for line in output.splitlines():
            if "BASIS_STALE" not in line and "TEXT_STALE" not in line:
                continue
            for candidate in candidates:
                if candidate in line and candidate not in stale:
                    stale.append(candidate)
        if not stale:
            if result.returncode:
                print(output)
                raise SystemExit(result.returncode)
            return
        for candidate in stale:
            run(sys.executable, "scripts/sov_clarity.py", "record", candidate, "--changed")
    run(sys.executable, "scripts/sov_clarity.py", "check")


def refresh_snapshot() -> None:
    sys.path.insert(0, str((ROOT / "scripts").resolve()))
    from sovsnapshot import claims
    path = ROOT / "CLAUDE.md"
    text = path.read_text(encoding="utf-8")
    derived = claims.derive_all()
    for claim in claims.CLAIMS:
        value = derived.values[claim.name] + (1 if claim.name == "commits" else 0)
        match = re.search(claim.pattern, text)
        if not match:
            raise SystemExit(f"snapshot pattern absent for {claim.name}")
        start, end = match.span(1)
        text = text[:start] + str(value) + text[end:]
    path.write_text(text, encoding="utf-8", newline="\n")


def finalize() -> None:
    assert_closed()
    WORKFLOW.unlink()
    SELF.unlink()
    refresh_snapshot()
    refresh_clarity()
    run(sys.executable, "scripts/sov_docs.py", "build")


COMMANDS = {"apply": apply, "finalize": finalize}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        raise SystemExit("usage: gap_195_phase_plumbing.py apply|finalize")
    COMMANDS[sys.argv[1]]()
