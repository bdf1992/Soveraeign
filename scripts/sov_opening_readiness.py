#!/usr/bin/env python3
"""Rehearse root successor-opening judgement from repository evidence without opening it."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import argparse
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from conformance import commissioning  # noqa: E402
from sovsession import phase_context  # noqa: E402


FIXTURES = "conformance/fixtures/commissioning/qualification-cases.json"
REQUIRED_POLARITIES = frozenset({"positive", "defeating"})


def _has(path: Path, *needles: str) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    return all(needle in text for needle in needles)


def p15_predicates(root: Path = ROOT) -> list[str]:
    """The normative P15 predicate ids stated by SPEC.md, in source order."""
    text = (root / "SPEC.md").read_text(encoding="utf-8")
    if "## Phase 1.5 commissioning predicates" not in text:
        return []
    block = text.split("## Phase 1.5 commissioning predicates", 1)[1]
    block = re.split(r"^## ", block, maxsplit=1, flags=re.M)[0]
    return re.findall(r"^- `(P15-Q[1-4]\.\d+)`\s", block, flags=re.M)


def _set_path(record: object, dotted: str, value: object) -> None:
    """Apply one fixture mutation through dict keys and list indices."""
    parts = dotted.split(".")
    current = record
    for part in parts[:-1]:
        current = current[int(part)] if isinstance(current, list) else current[part]  # type: ignore[index]
    leaf = parts[-1]
    if isinstance(current, list):
        current[int(leaf)] = value
    else:
        current[leaf] = value  # type: ignore[index]


def commissioning_instrument(root: Path = ROOT) -> dict:
    """Prove every stated P15 predicate has a discriminating fixture pair."""
    fixture_path = root / FIXTURES
    if not fixture_path.is_file():
        return {"closed": False, "predicates_total": 0, "predicates_covered": 0,
                "open": [], "defects": ["qualification fixture corpus missing"]}
    document = json.loads(fixture_path.read_text(encoding="utf-8"))
    templates = document.get("templates") or {}
    cases = document.get("cases") or []
    stated = p15_predicates(root)
    stated_set = set(stated)
    coverage: dict[str, set[str]] = {}
    defects: list[str] = []

    if stated_set != commissioning.PREDICATES:
        missing = sorted(stated_set - commissioning.PREDICATES)
        extra = sorted(commissioning.PREDICATES - stated_set)
        if missing:
            defects.append("independent evaluator missing: " + ", ".join(missing))
        if extra:
            defects.append("evaluator names predicates absent from SPEC.md: " + ", ".join(extra))

    for case in cases:
        predicate = str(case.get("predicate") or "")
        polarity = case.get("polarity")
        case_id = str(case.get("case_id") or predicate or "unnamed")
        if predicate not in stated_set:
            defects.append(f"{case_id}: predicate absent from SPEC.md")
            continue
        if polarity not in REQUIRED_POLARITIES:
            defects.append(f"{case_id}: invalid polarity {polarity}")
            continue
        template = templates.get(predicate)
        if not isinstance(template, dict):
            defects.append(f"{case_id}: no observation template")
            continue
        observation = deepcopy(template)
        for dotted, value in (case.get("set") or {}).items():
            try:
                _set_path(observation, str(dotted), value)
            except (KeyError, IndexError, TypeError, ValueError):
                defects.append(f"{case_id}: mutation path {dotted} does not resolve")
                observation = {}
                break
        seen = commissioning.evaluate(predicate, observation)
        discriminates = (not seen) if polarity == "positive" else bool(seen)
        if not discriminates:
            defects.append(
                f"{case_id}: {polarity} case did not discriminate ({'; '.join(seen) or 'no defect'})")
            continue
        coverage.setdefault(predicate, set()).add(str(polarity))

    rows = []
    for predicate in stated:
        have = coverage.get(predicate, set())
        missing = sorted(REQUIRED_POLARITIES - have)
        rows.append({"predicate": predicate, "missing": missing})
    open_rows = [row for row in rows if row["missing"]]
    return {
        "closed": not defects and not open_rows and len(stated) == len(commissioning.PREDICATES),
        "predicates_total": len(stated),
        "predicates_covered": len(stated) - len(open_rows),
        "open": open_rows,
        "defects": defects,
    }


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

    instrument = commissioning_instrument(root)
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
        "p15_qualification_instrument": instrument["closed"],
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
    defects.extend("P15_INSTRUMENT: " + item for item in instrument["defects"])
    defects.extend(
        "P15_INSTRUMENT_OPEN: " + row["predicate"] + " missing " + "+".join(row["missing"])
        for row in instrument["open"]
    )

    future_custody = root / "contracts/custodies/phase-1-5.json"
    if future_custody.exists():
        defects.append("LIVE_PHASE_1_5_CUSTODY_EXISTS_BEFORE_OPENING")

    return {
        "state": "READY_TO_OPEN" if not defects else "NOT_READY",
        "phase": None,
        "next_gate": state.get("next_gate"),
        "checks": checks,
        "p15_instrument": instrument,
        "defects": defects,
        "authoritative": False,
        "note": "readiness is evidence for root judgement; this command cannot open a phase",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--instrument", action="store_true",
                        help="read only the prepared P15 positive/defeating fixture instrument")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args(argv)
    if args.instrument:
        report = commissioning_instrument(ROOT)
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print(f"P15 instrument: {report['predicates_covered']}/{report['predicates_total']} "
                  "normative predicates carry discriminating fixture pairs")
            for row in report["open"]:
                print(f"  OPEN {row['predicate']} missing {'+'.join(row['missing'])}")
            for defect in report["defects"]:
                print(f"  DEFECT {defect}")
            print("CLOSED: P15 instrument" if report["closed"] else "OPEN: P15 instrument")
        return 0 if report["closed"] else 1

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
