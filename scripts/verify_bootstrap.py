#!/usr/bin/env python3
"""Dependency-free structural and source-integrity check for the bootstrap."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import json
import sys


ROOT = Path(__file__).resolve().parents[1]

REQUIRED = (
    "README.md",
    "SYSTEM.md",
    "CLASSIFICATION.md",
    "CONTRACT.md",
    "PRD.md",
    "SPEC.md",
    "AI-NATIVE.md",
    "services/asset/CHARTER.md",
    "services/proofing/CHARTER.md",
    "ROADMAP.md",
    "STATUS.yaml",
    "AGENTS.md",
    "OPEN-SEAMS.md",
    "NAMING.md",
    "AGENT-BOOTSTRAP-PROMPT.md",
    "contracts/service-manifest.schema.json",
    "contracts/operation-plan.schema.json",
    "contracts/receipt.schema.json",
    "contracts/participant-observation.schema.json",
    "services/README.md",
    "services/asset/contracts/service.json",
    "services/proofing/contracts/service.json",
    "decisions/0001-founding-boundary.md",
    "decisions/0002-naming-process.md",
    "decisions/0003-evidence-boundary.md",
    "decisions/0007-asset-service-boundary.md",
    "decisions/0008-classification-contract.md",
    "decisions/0009-phase-i-logical-spec.md",
    "decisions/0010-proofing-service-boundary.md",
)


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def verify_required() -> int:
    count = 0
    for relative in REQUIRED:
        path = ROOT / relative
        if not path.is_file() or path.stat().st_size == 0:
            fail(f"missing or empty required file: {relative}")
        count += 1
    return count


def verify_selected_name() -> int:
    status = (ROOT / "STATUS.yaml").read_text(encoding="utf-8")
    for line in ("product_name: Soveraeign", "repository_name: Soveraeign"):
        if line not in status:
            fail(f"owner-selected naming state changed: expected {line!r}")
    return 2


def verify_sources() -> int:
    lock = ROOT / "lineage" / "SOURCES.lock"
    if not lock.is_file():
        print("SKIP: historical evidence archive is not present in this checkout")
        return 0
    count = 0
    for number, raw in enumerate(lock.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            expected, relative = line.split("  ", 1)
        except ValueError:
            fail(f"malformed source lock line {number}")
        path = ROOT / relative
        if not path.is_file():
            fail(f"locked source missing: {relative}")
        actual = sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            fail(f"source digest mismatch: {relative}")
        count += 1
    if count == 0:
        fail("source lock contains no entries")
    return count


def verify_scenarios() -> int:
    paths = sorted((ROOT / "conformance" / "founding-scenarios").glob("*.yaml"))
    if len(paths) < 7:
        fail("expected at least seven founding scenarios")
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for marker in ("id:", "given:", "when:", "then:", "defeating:"):
            if marker not in text:
                fail(f"{path.relative_to(ROOT)} lacks {marker}")
    return len(paths)


def verify_conformance_controls() -> int:
    cases = ROOT / "conformance" / "oracle-controls.json"
    scenarios = ROOT / "conformance" / "scenarios.json"
    runner = ROOT / "conformance" / "run.py"
    if not cases.is_file() or not scenarios.is_file() or not runner.is_file():
        fail("executable conformance controls are missing")
    text = cases.read_text(encoding="utf-8")
    for requirement in (f"PROD-I-{number}" for number in range(1, 9)):
        if text.count(f'"requirement": "{requirement}"') < 2:
            fail(f"{requirement} lacks positive and defeating controls")
    return 16


def verify_json_documents() -> int:
    paths = sorted(ROOT.glob("contracts/*.json"))
    paths.extend(sorted(ROOT.glob("services/*/contracts/*.json")))
    paths.extend((ROOT / "conformance" / "oracle-controls.json",
                  ROOT / "conformance" / "scenarios.json"))
    for path in paths:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            fail(f"invalid JSON document {path.relative_to(ROOT)}: {error}")
    for service in ("asset", "proofing"):
        manifest = json.loads((ROOT / "services" / service / "contracts" / "service.json").read_text(encoding="utf-8"))
        for field in ("service_id", "standing", "owns", "operations", "uses_kernel_contracts", "forbids"):
            if not manifest.get(field):
                fail(f"{service} service manifest lacks {field}")
    return len(paths)


def main() -> int:
    checks = (verify_required() + verify_selected_name() + verify_sources()
              + verify_scenarios() + verify_conformance_controls()
              + verify_json_documents())
    print(f"PASS: bootstrap structure and evidence integrity ({checks} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
