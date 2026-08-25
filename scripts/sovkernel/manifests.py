"""Read every service manifest and judge it against the kernel and its own declarations.

The manifest owns what an operation is: the record it acts on, the append-preserving CRUD verb
it realizes, its logical endpoint, the preconditions it checks, what a commit produces, and every
refusal it may return. ``contracts/capability-offices.json`` owns where the operation is answered
and what authority it needs; nothing here duplicates that table.

Every check derives its expectation from a governing source read at check time - the kernel
transition table for refusal vocabulary and transition ids, ``PRD.md`` for requirement ids, and
the manifest's own ``service_id`` for endpoint addresses. A manifest is never asked whether it
is correct.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterator

from sovkernel.jsonschema import validate

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "contracts" / "service-manifest.schema.json"
KERNEL_PATH = ROOT / "contracts" / "kernel-transitions.json"
PRD_PATH = ROOT / "PRD.md"

STANDING_ORDER = ("PROPOSED", "BUILT", "WITNESSED", "RATIFIED")

#: What a satisfied operation may commit, per CRUD verb. A READ writes no authoritative record;
#: a REBUILD recomputes a projection only; a COUNTER adds a counter-record and erases nothing.
COMMIT_BY_CRUD = {
    "CREATE": {"COMMITTED", "RECORDED", "EFFECTIVE"},
    "SUPERSEDE": {"COMMITTED", "RECORDED", "EFFECTIVE"},
    "COUNTER": {"COUNTERED"},
    "READ": {"DERIVED"},
    "REBUILD": {"REBUILT"},
}


def manifest_paths() -> list[Path]:
    """Every service manifest on disk, in service order."""
    return sorted((ROOT / "services").glob("*/contracts/service.json"))


def kernel_refusals() -> set[str]:
    """The refusal vocabulary the kernel transition table declares."""
    table = json.loads(KERNEL_PATH.read_text(encoding="utf-8"))
    return {code for row in table["transitions"] for code in row["refusals"]}


def kernel_transition_ids() -> set[str]:
    """Every transition id the kernel table declares."""
    table = json.loads(KERNEL_PATH.read_text(encoding="utf-8"))
    return {row["transition"] for row in table["transitions"]}


def prd_requirements() -> set[str]:
    """Requirement ids PRD.md actually carries, read from its bytes rather than assumed."""
    return set(re.findall(r"PROD-I-[1-9]", PRD_PATH.read_text(encoding="utf-8")))


def load(path: Path) -> dict[str, Any]:
    """Parse one manifest."""
    return json.loads(path.read_text(encoding="utf-8"))


def _schema_defects(manifest: dict[str, Any]) -> Iterator[str]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    for defect in validate(manifest, schema, schema, "/"):
        yield f"schema: {defect}"


def _endpoint_defects(manifest: dict[str, Any]) -> Iterator[str]:
    service_id = manifest.get("service_id", "")
    seen: set[str] = set()
    for entry in manifest.get("operations", []):
        operation = entry.get("operation", "")
        expected = f"sov://{service_id}/{operation}"
        declared = entry.get("logical_endpoint")
        if declared != expected:
            yield f"{operation}: logical endpoint is {declared!r}, expected {expected!r}"
        if declared in seen:
            yield f"{operation}: logical endpoint {declared!r} is declared twice"
        seen.add(declared)


def _subject_defects(manifest: dict[str, Any]) -> Iterator[str]:
    owns = set(manifest.get("owns", []))
    for entry in manifest.get("operations", []):
        operation = entry.get("operation")
        subject = entry.get("subject")
        if subject not in owns:
            yield f"{operation}: subject {subject!r} is not a record this service owns"
        also = entry.get("also_reads")
        if also is None:
            continue
        if entry.get("crud") != "READ":
            yield f"{operation}: only a READ may declare also_reads"
        for extra in also:
            if extra not in owns:
                yield f"{operation}: also_reads {extra!r} is not a record this service owns"
            if extra == subject:
                yield f"{operation}: also_reads repeats its own subject {extra!r}"


def _refusal_defects(manifest: dict[str, Any], kernel: set[str]) -> Iterator[str]:
    local = manifest.get("local_refusals", {})
    for code, mapped in sorted(local.items()):
        if code in kernel:
            yield f"local_refusals: {code} is already a kernel refusal and must not be remapped"
        if mapped not in kernel:
            yield f"local_refusals: {code} maps to {mapped!r}, which the kernel does not declare"
    used: set[str] = set()
    for entry in manifest.get("operations", []):
        for code in entry.get("refusals", []):
            used.add(code)
            if code not in kernel and code not in local:
                yield (f"{entry.get('operation')}: refusal {code} is neither a kernel refusal nor "
                       f"declared in local_refusals")
    for code in sorted(set(local) - used):
        yield f"local_refusals: {code} is declared but no operation returns it"


def _shape_defects(manifest: dict[str, Any], transitions: set[str],
                   requirements: set[str]) -> Iterator[str]:
    service_standing = manifest.get("standing", "PROPOSED")
    for entry in manifest.get("operations", []):
        operation = entry.get("operation")
        crud = entry.get("crud")
        commit = entry.get("commit")
        allowed = COMMIT_BY_CRUD.get(crud, set())
        if commit not in allowed:
            yield (f"{operation}: a {crud} operation may not commit {commit}; "
                   f"expected one of {sorted(allowed)}")
        standing = entry.get("standing", "PROPOSED")
        if STANDING_ORDER.index(standing) > STANDING_ORDER.index(service_standing):
            yield (f"{operation}: standing {standing} is ahead of the service's own "
                   f"{service_standing}")
        transition = entry.get("kernel_transition")
        if transition is not None and transition not in transitions:
            yield f"{operation}: kernel_transition {transition!r} is not in the kernel table"
        requirement = entry.get("requirement")
        if requirement is not None and requirement not in requirements:
            yield f"{operation}: requirement {requirement} does not appear in PRD.md"


def _crud_defects(manifest: dict[str, Any]) -> Iterator[str]:
    """A written record no operation can read back is a hole in the surface, not a design."""
    written: dict[str, set[str]] = {}
    readable: set[str] = set()
    for entry in manifest.get("operations", []):
        subject = entry.get("subject")
        crud = entry.get("crud")
        if crud == "READ":
            readable.add(subject)
            readable.update(entry.get("also_reads", []))
        elif crud in ("CREATE", "SUPERSEDE", "COUNTER"):
            written.setdefault(subject, set()).add(entry.get("operation"))
    for subject in sorted(set(written) - readable):
        yield (f"{subject}: written by {sorted(written[subject])} but no operation reads it back")


def defects(manifest: dict[str, Any], kernel: set[str], transitions: set[str],
            requirements: set[str]) -> list[str]:
    """Every defect in one manifest, in a stable order."""
    found = list(_schema_defects(manifest))
    if found:
        return found
    found.extend(_endpoint_defects(manifest))
    found.extend(_subject_defects(manifest))
    found.extend(_refusal_defects(manifest, kernel))
    found.extend(_shape_defects(manifest, transitions, requirements))
    found.extend(_crud_defects(manifest))
    return found


def check_all() -> tuple[int, list[str]]:
    """Judge every manifest on disk. Returns the operation count and every defect found."""
    kernel = kernel_refusals()
    transitions = kernel_transition_ids()
    requirements = prd_requirements()
    total = 0
    findings: list[str] = []
    for path in manifest_paths():
        manifest = load(path)
        total += len(manifest.get("operations", []))
        for defect in defects(manifest, kernel, transitions, requirements):
            findings.append(f"{path.relative_to(ROOT).as_posix()}: {defect}")
    return total, findings


def crud_coverage() -> list[dict[str, Any]]:
    """Per service, which append-preserving CRUD verbs its declared operations cover."""
    rows: list[dict[str, Any]] = []
    for path in manifest_paths():
        manifest = load(path)
        verbs: dict[str, list[str]] = {}
        built = 0
        for entry in manifest["operations"]:
            verbs.setdefault(entry["crud"], []).append(entry["operation"])
            if entry["standing"] != "PROPOSED":
                built += 1
        rows.append({
            "service_id": manifest["service_id"],
            "standing": manifest["standing"],
            "operations": len(manifest["operations"]),
            "built": built,
            "verbs": {verb: sorted(names) for verb, names in sorted(verbs.items())},
            "subjects": sorted(manifest["owns"]),
        })
    return rows


def endpoints() -> list[dict[str, Any]]:
    """Every declared logical endpoint across every service."""
    rows: list[dict[str, Any]] = []
    for path in manifest_paths():
        manifest = load(path)
        for entry in manifest["operations"]:
            rows.append({
                "logical_endpoint": entry["logical_endpoint"],
                "service_id": manifest["service_id"],
                "operation": entry["operation"],
                "crud": entry["crud"],
                "subject": entry["subject"],
                "standing": entry["standing"],
                "commit": entry["commit"],
                "requirement": entry.get("requirement"),
                "refusals": entry["refusals"],
            })
    rows.sort(key=lambda row: row["logical_endpoint"])
    return rows
