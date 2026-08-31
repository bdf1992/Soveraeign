from __future__ import annotations

from pathlib import Path
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SELF = ROOT / ".github" / "scripts" / "gap_195_context_projection.py"
WORKFLOW = ROOT / ".github" / "workflows" / "gap-195-context-projection.yml"


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


def assert_no_phase_opened() -> None:
    status = (ROOT / "STATUS.yaml").read_text(encoding="utf-8")
    phases = json.loads((ROOT / "contracts" / "phases.json").read_text(encoding="utf-8"))
    if "phase: NONE_ACTIVE" not in status:
        raise SystemExit("refuse: STATUS no longer says NONE_ACTIVE")
    if len(phases.get("phases", [])) != 1 or phases["phases"][0].get("phase_id") != "phase:i":
        raise SystemExit("refuse: successor phase already exists")


def patch_prd() -> None:
    path = ROOT / "PRD.md"
    old = "This profile exists **for Phase II**. Phase 1.5 commissions the ability to\n"
    new = ("Human-readable pre-opening rationale and boundary: "
           "`contracts/phase-1-5-phase-ii-horizon.md`. That record is prepared context, "
           "not phase standing.\n\n"
           "This profile exists **for Phase II**. Phase 1.5 commissions the ability to\n")
    replace_once(path, old, new)


def patch_record_cli() -> None:
    path = ROOT / "services" / "record" / "src" / "soveraeign_record_service" / "cli.py"
    old = '''def reconstruct(service: RecordService, _: argparse.Namespace) -> dict[str, Any]:\n'''
    new = '''def project_evidence(service: RecordService, args: argparse.Namespace) -> dict[str, Any]:\n    """Return a frozen, addressed RecordProjection for one recipient relation."""\n    return service.evidence_projection(\n        args.subject, args.recipient_principal, args.recipient_relation, args.purpose,\n        as_of_entry=args.as_of_entry, exclude_kinds=args.exclude_kind or (),\n    )\n\n\ndef reconstruct(service: RecordService, _: argparse.Namespace) -> dict[str, Any]:\n'''
    replace_once(path, old, new)
    old = '''        "read-projection": read_projection,\n        "drop-projections": lambda s, _: {"dropped": True, "authoritative": False},\n'''
    new = '''        "read-projection": read_projection,\n        "project-evidence": project_evidence,\n        "drop-projections": lambda s, _: {"dropped": True, "authoritative": False},\n'''
    replace_once(path, old, new)
    old = '''    projection = sub.add_parser("read-projection", help="read one derived projection row")\n    projection.add_argument("--subject", required=True)\n\n    sub.add_parser("drop-projections", help="delete every projection; the journal is untouched")\n'''
    new = '''    projection = sub.add_parser("read-projection", help="read one derived projection row")\n    projection.add_argument("--subject", required=True)\n\n    evidence = sub.add_parser(\n        "project-evidence", help="derive one scoped, frozen RecordProjection")\n    evidence.add_argument("--subject", action="append", required=True)\n    evidence.add_argument("--recipient-principal", required=True)\n    evidence.add_argument("--recipient-relation", required=True)\n    evidence.add_argument("--purpose", required=True)\n    evidence.add_argument("--as-of-entry")\n    evidence.add_argument("--exclude-kind", action="append",\n                          choices=("EVENT", "RECEIPT", "OBSERVATION", "COUNTER"))\n\n    sub.add_parser("drop-projections", help="delete every projection; the journal is untouched")\n'''
    replace_once(path, old, new)


def patch_record_manifest() -> None:
    path = ROOT / "services" / "record" / "contracts" / "service.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    if "record-projection" not in doc["owns"]:
        doc["owns"].append("record-projection")
    if not any(item["operation"] == "project-evidence" for item in doc["operations"]):
        doc["operations"].append({
            "operation": "project-evidence",
            "standing": "BUILT",
            "logical_endpoint": "sov://record/project-evidence",
            "subject": "record-projection",
            "crud": "READ",
            "preconditions": [
                "journal_readable", "subject_declared", "recipient_declared",
                "relation_declared", "purpose_declared"
            ],
            "commit": "DERIVED",
            "refusals": ["UNREADABLE", "DIGEST_MISMATCH", "MISSING_PRECONDITION"]
        })
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8", newline="\n")


def patch_capability_offices() -> None:
    path = ROOT / "contracts" / "capability-offices.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["cli_commands"]["record.project-evidence"] = (
        "python -m soveraeign_record_service.cli project-evidence")
    doc["assignments"]["record.project-evidence"] = {
        "office": "FRONT",
        "counter": "operator-desk",
        "required_authority": "read:journal",
        "effect_class": "RECORD_LOCAL",
        "actor_kinds": ["HUMAN", "MODEL"],
        "note": (
            "A RecordProjection is an authorized reading of common history for a named "
            "subject and recipient relation. The operation widens no authority: it derives "
            "addresses, digests, cutoff and omissions from the journal and returns "
            "authority_effect NONE."
        ),
    }
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8", newline="\n")


def patch_record_spec() -> None:
    path = ROOT / "services" / "record" / "SERVICE-SPEC.md"
    old = '''`service.json` `owns`: `journal-entry`, `terminal-receipt`, `counter-record`,\n`digest-chain`, `subject-projection`, `journal-export`.\n'''
    new = '''`service.json` `owns`: `journal-entry`, `terminal-receipt`, `counter-record`,\n`digest-chain`, `subject-projection`, `journal-export`, `record-projection`.\n'''
    replace_once(path, old, new)
    old = '''- **subject-projection** — `subject_projection`, a rebuildable index dropped\n  and rebuilt from the journal alone. `CHARTER.md` "Authoritative versus\n  derived": "A projection can never be promoted to the record."\n'''
    new = '''- **subject-projection** — `subject_projection`, a rebuildable index dropped\n  and rebuilt from the journal alone. `CHARTER.md` "Authoritative versus\n  derived": "A projection can never be promoted to the record."\n- **record-projection** — a bounded evidence reading matching\n  `contracts/record-projection.schema.json`: exact subjects, recipient relation,\n  purpose, verified cutoff, included Record addresses and digests, explicit\n  omissions, and `authority_effect: NONE`. The same journal/request/cutoff\n  rebuilds the same projection identity; it is not stored as authoritative history.\n'''
    replace_once(path, old, new)
    old = '''| `read-projection` | — (local) | `projection_built` | `DERIVED` | `MISSING_PRECONDITION` |\n'''
    new = '''| `read-projection` | — (local) | `projection_built` | `DERIVED` | `MISSING_PRECONDITION` |\n| `project-evidence` | — (local) | `journal_readable`, `subject_declared`, `recipient_declared`, `relation_declared`, `purpose_declared` | `DERIVED` | `UNREADABLE`, `DIGEST_MISMATCH`, `MISSING_PRECONDITION` |\n'''
    replace_once(path, old, new)


def apply() -> None:
    assert_no_phase_opened()
    patch_prd()
    patch_record_cli()
    patch_record_manifest()
    patch_capability_offices()
    patch_record_spec()


def refresh_clarity() -> None:
    coverage = json.loads((ROOT / ".clarity" / "coverage.json").read_text(encoding="utf-8"))
    candidates = list(coverage.get("reviews", {}).keys())
    for _ in range(5):
        result = subprocess.run(
            [sys.executable, "scripts/sov_clarity.py", "check"], cwd=ROOT,
            text=True, capture_output=True, check=False)
        output = result.stdout + "\n" + result.stderr
        stale: list[str] = []
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


def refresh() -> None:
    run(sys.executable, "scripts/sov_capability.py", "build")
    run(sys.executable, "scripts/sov_interface.py", "build")
    run(sys.executable, "scripts/sov_surface.py", "render")
    run(sys.executable, "scripts/sov_docs.py", "build")
    refresh_clarity()


def refresh_snapshot() -> None:
    sys.path.insert(0, str((ROOT / "scripts").resolve()))
    from sovsnapshot import claims

    path = ROOT / "CLAUDE.md"
    text = path.read_text(encoding="utf-8")
    derived = claims.derive_all()
    missing = [claim.name for claim in claims.CLAIMS if claim.name not in derived.values]
    if missing:
        raise SystemExit(f"cannot refresh snapshot; underivable claims: {missing}")
    for claim in claims.CLAIMS:
        value = derived.values[claim.name] + (1 if claim.name == "commits" else 0)
        match = re.search(claim.pattern, text)
        if not match:
            raise SystemExit(f"snapshot pattern absent for {claim.name}")
        start, end = match.span(1)
        text = text[:start] + str(value) + text[end:]
    path.write_text(text, encoding="utf-8", newline="\n")


def finalize() -> None:
    assert_no_phase_opened()
    WORKFLOW.unlink()
    SELF.unlink()
    refresh_snapshot()
    refresh_clarity()
    run(sys.executable, "scripts/sov_docs.py", "build")


COMMANDS = {"apply": apply, "refresh": refresh, "finalize": finalize}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        raise SystemExit("usage: gap_195_context_projection.py apply|refresh|finalize")
    COMMANDS[sys.argv[1]]()
