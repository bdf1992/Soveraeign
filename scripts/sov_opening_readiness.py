#!/usr/bin/env python3
"""Rehearse successor opening from repository evidence without opening anything."""

from __future__ import annotations

from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sovsession import phase_context  # noqa: E402


def _has(path: Path, *needles: str) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    return all(needle in text for needle in needles)


def assess(root: Path = ROOT) -> dict:
    """Return a non-authoritative reading of whether the prepared opening is startable."""
    state = phase_context.collect(root)
    defects = list(state.get("defects") or [])
    active = state.get("active")
    if active is not None:
        return {"state": "ACTIVE_PHASE", "phase": active.get("phase_id"),
                "defects": defects, "authoritative": False}

    if state.get("status_phase") != "NONE_ACTIVE":
        defects.append("STATUS_NOT_NONE_ACTIVE")
    if state.get("next_gate") != "SUCCESSOR_PHASE_OPENING":
        defects.append("NEXT_GATE_NOT_SUCCESSOR_OPENING")

    phases_path = root / "contracts/phases.json"
    phases = json.loads(phases_path.read_text(encoding="utf-8")) if phases_path.is_file() else {}
    if any(item.get("phase_id") == "phase:1-5" for item in phases.get("phases", [])):
        defects.append("PHASE_1_5_ALREADY_RECORDED")

    checks = {
        "human_horizon": _has(root / "contracts/phase-1-5-phase-ii-horizon.md",
                              "PREPARED · HUMAN-READABLE · NO PHASE STANDING",
                              "Phase 1.5", "Phase II", "Agency learns. Record remembers."),
        "prd_profile": _has(root / "PRD.md", "Prepared Phase 1.5 qualification profile",
                            "P15-Q1", "P15-Q2", "P15-Q3", "P15-Q4",
                            "prepared successor profile, not an active phase"),
        "spec_predicates": _has(root / "SPEC.md", "Phase 1.5 commissioning predicates",
                                "P15-Q1", "P15-Q2", "P15-Q3", "P15-Q4",
                                "RecordProjection", "Finding"),
        "record_projection_contract": (root / "contracts/record-projection.schema.json").is_file(),
        "finding_contract": (root / "contracts/finding.schema.json").is_file(),
        "phase_custody_reader": (root / "scripts/sovcustody/collections.py").is_file(),
        "phase_progress_reader": (root / "scripts/sov_active_phase_progress.py").is_file(),
    }
    service_path = root / "services/record/contracts/service.json"
    if service_path.is_file():
        service = json.loads(service_path.read_text(encoding="utf-8"))
        checks["record_project_evidence"] = any(
            item.get("operation") == "project-evidence" and item.get("standing") == "BUILT"
            for item in service.get("operations", []))
    else:
        checks["record_project_evidence"] = False

    progress_path = root / "contracts/phase-progress.json"
    if progress_path.is_file():
        progress = json.loads(progress_path.read_text(encoding="utf-8"))
        codes = {item.get("code") for item in progress.get("active_refusals", [])}
        checks["opening_progress_refusal"] = "ACTIVE_PHASE_PROGRESS_UNINITIALIZED" in codes
    else:
        checks["opening_progress_refusal"] = False

    for name, passed in checks.items():
        if not passed:
            defects.append("MISSING_" + name.upper())

    future_custody = root / "contracts/custodies/phase-1-5.json"
    if future_custody.exists():
        defects.append("LIVE_PHASE_1_5_CUSTODY_EXISTS_BEFORE_OPENING")

    return {
        "state": "READY_TO_OPEN" if not defects else "NOT_READY",
        "phase": None,
        "next_gate": state.get("next_gate"),
        "checks": checks,
        "defects": defects,
        "authoritative": False,
        "note": "readiness is evidence for root judgement; this command cannot open a phase",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args(argv)
    report = assess(ROOT)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"{report['state']}: non-authoritative opening rehearsal")
        for name, passed in (report.get("checks") or {}).items():
            print(f"  {'PASS' if passed else 'FAIL'} {name}")
        for defect in report.get("defects") or []:
            print(f"  {defect}")
        print("  " + report.get("note", ""))
    if report.get("defects"):
        return 1
    if args.require_ready and report.get("state") != "READY_TO_OPEN":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
