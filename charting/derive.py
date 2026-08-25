"""Derive the experimental charting graph from existing governing sources.

The derivation is intentionally narrow. It extracts only structure that is
explicitly declared by governing sources, provisional bindings, or marked
experimental sidecars. It does not infer capabilities, authority, standing,
or workflow eligibility from prose.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any

from .model import ChartingError
from .skill_contracts import derive_experimental_skill_contracts


_SKILL_LINE = re.compile(r"^- `(?P<label>[^`]+) Skill` — (?P<description>.+)$")
_WORKFLOW_ROW = re.compile(
    r"^\| \*\*(?P<label>[^*]+)\*\* \| (?P<purpose>[^|]+) \| (?P<artifact>[^|]+) \|$"
)
_STANCE_LINE = re.compile(r"^- `(?P<label>LEFT|RIGHT|BLUE|RED)` — (?P<description>.+)$")
_FRONTMATTER_NAME = re.compile(r"^name:\s*(?P<name>[^\s]+)\s*$", re.MULTILINE)


def derive_repository_graph(repo_root: Path) -> dict[str, Any]:
    """Derive one experimental graph from the current repository artifact."""

    root = repo_root.resolve()
    sdlc_path = root / "SDLC.md"
    binding_readme = root / ".claude" / "README.md"
    skills_root = root / ".claude" / "skills"
    experiments_root = root / "charting" / "experiments"

    sdlc = _read_required(sdlc_path)
    _read_required(binding_readme)

    points: list[dict[str, Any]] = []
    crossings: list[dict[str, Any]] = []
    source_files = [sdlc_path, binding_readme]

    canonical_skills = _derive_skills(sdlc)
    points.extend(canonical_skills.values())
    points.extend(_derive_workflows(sdlc))
    points.extend(_derive_stances(sdlc))
    points.append(
        {
            "id": "binding:claude-code",
            "kind": "binding",
            "label": "Claude Harness Binding",
            "source": ".claude/README.md",
            "attributes": {"standing": "provisional"},
        }
    )

    implementation_points, implementation_crossings, implementation_sources = (
        _derive_binding_implementations(root, skills_root, canonical_skills)
    )
    points.extend(implementation_points)
    crossings.extend(implementation_crossings)
    source_files.extend(implementation_sources)

    contract_points, contract_crossings, contract_sources, contract_omissions = (
        derive_experimental_skill_contracts(root, experiments_root, canonical_skills)
    )
    points.extend(contract_points)
    crossings.extend(contract_crossings)
    source_files.extend(contract_sources)

    return {
        "contract_id": "soveraeign-sdlc-derived-charting-experiment",
        "source_revision": _source_revision(root, source_files),
        "source_files": [
            str(path.relative_to(root)).replace("\\", "/") for path in sorted(source_files)
        ],
        "omissions": contract_omissions,
        "points": points,
        "crossings": crossings,
        "paradigms": _paradigms(),
    }


def _paradigms() -> list[dict[str, Any]]:
    return [
        {
            "id": "skill-forest",
            "traverse": ["provides", "realizes", "requires", "binds"],
            "omissions": [
                "only explicitly declared Skill requirements and capabilities are included",
                "authority grants and live capability receipts are unresolved",
            ],
        },
        {
            "id": "operator-navigation",
            "traverse": ["provides", "realizes", "requires", "binds", "blocks"],
            "omissions": [
                "no operator position is resolved by this static derivation",
                "capability declarations are not runtime availability",
                "live authority and capability receipts require Registry/Broker/Authority dependencies",
            ],
        },
    ]


def _derive_skills(sdlc: str) -> dict[str, dict[str, Any]]:
    axis: str | None = None
    skills: dict[str, dict[str, Any]] = {}
    for line in sdlc.splitlines():
        if line.startswith("**Tier skills**"):
            axis = "tier"
            continue
        if line.startswith("**Domain skills**"):
            axis = "domain"
            continue
        if line.startswith("## Workflow templates"):
            axis = None
        match = _SKILL_LINE.match(line)
        if not match or axis is None:
            continue
        label = match.group("label").strip()
        point_id = f"skill:{_slug(label)}"
        if point_id in skills:
            raise ChartingError(f"duplicate derived skill: {point_id}")
        skills[point_id] = {
            "id": point_id,
            "kind": "skill",
            "label": f"{label} Skill",
            "source": "SDLC.md",
            "attributes": {
                "axis": axis,
                "description": match.group("description").strip(),
            },
        }
    if not skills:
        raise ChartingError("SDLC.md yielded no declared skills")
    return skills


def _derive_workflows(sdlc: str) -> list[dict[str, Any]]:
    in_section = False
    workflows: list[dict[str, Any]] = []
    for line in sdlc.splitlines():
        if line.startswith("## Workflow templates"):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if not in_section:
            continue
        match = _WORKFLOW_ROW.match(line)
        if match is None:
            continue
        label = match.group("label").strip()
        workflows.append(
            {
                "id": f"workflow:{_slug(label)}",
                "kind": "workflow",
                "label": label,
                "source": "SDLC.md",
                "attributes": {
                    "purpose": match.group("purpose").strip(),
                    "terminal_artifact": match.group("artifact").strip(),
                },
            }
        )
    if not workflows:
        raise ChartingError("SDLC.md yielded no workflow templates")
    return workflows


def _derive_stances(sdlc: str) -> list[dict[str, Any]]:
    stances: list[dict[str, Any]] = []
    seen: set[str] = set()
    for line in sdlc.splitlines():
        match = _STANCE_LINE.match(line)
        if match is None:
            continue
        label = match.group("label")
        point_id = f"stance:{label.lower()}"
        if point_id in seen:
            continue
        seen.add(point_id)
        stances.append(
            {
                "id": point_id,
                "kind": "stance",
                "label": label,
                "source": "SDLC.md",
                "attributes": {"description": match.group("description").strip()},
            }
        )
    if len(stances) != 4:
        raise ChartingError("SDLC.md must yield LEFT, RIGHT, BLUE, and RED stances")
    return stances


def _derive_binding_implementations(
    root: Path,
    skills_root: Path,
    canonical_skills: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[Path]]:
    if not skills_root.is_dir():
        raise ChartingError("provisional Claude skill binding directory is missing")

    points: list[dict[str, Any]] = []
    crossings: list[dict[str, Any]] = []
    sources: list[Path] = []
    # This chart models the SDLC loop, whose tiers SDLC.md declares and whose host
    # bindings are the `sdlc-*` skills. A `sov-<domain>` skill is domain know-how,
    # not a tier binding: it has no canonical SDLC skill to implement, so it is
    # outside this chart rather than a defect in it. Charting every skill here would
    # assert a correspondence nobody claimed. An `sdlc-*` skill whose frontmatter
    # disagrees with its directory still fails, which is the case worth keeping.
    for directory in sorted(path for path in skills_root.iterdir() if path.is_dir()):
        if not directory.name.startswith("sdlc-"):
            continue
        skill_path = directory / "SKILL.md"
        text = _read_required(skill_path)
        sources.append(skill_path)
        match = _FRONTMATTER_NAME.search(text)
        if match is None:
            raise ChartingError(f"missing skill frontmatter name: {skill_path.relative_to(root)}")
        binding_name = match.group("name")
        if binding_name != directory.name:
            raise ChartingError(f"binding skill identity mismatch: {skill_path.relative_to(root)}")

        canonical_id = f"skill:{binding_name.removeprefix('sdlc-')}"
        if canonical_id not in canonical_skills:
            raise ChartingError(f"binding skill has no declared SDLC skill: {binding_name}")

        relative = str(skill_path.relative_to(root)).replace("\\", "/")
        implementation_id = f"implementation:claude:{binding_name}"
        points.append(
            {
                "id": implementation_id,
                "kind": "implementation",
                "label": binding_name,
                "source": relative,
                "attributes": {"binding": "binding:claude-code"},
            }
        )
        crossings.extend(
            [
                {
                    "id": f"binding-provides:{binding_name}",
                    "kind": "provides",
                    "source": "binding:claude-code",
                    "target": implementation_id,
                    "provenance": ".claude/README.md",
                    "constraints": {},
                },
                {
                    "id": f"implementation-realizes:{binding_name}",
                    "kind": "realizes",
                    "source": implementation_id,
                    "target": canonical_id,
                    "provenance": relative,
                    "constraints": {"semantic_authority": False},
                },
            ]
        )
    return points, crossings, sources


def _source_revision(root: Path, paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(set(paths)):
        relative = str(path.relative_to(root)).replace("\\", "/")
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


def _read_required(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ChartingError(f"cannot read governing source: {path}") from exc


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    print(json.dumps(derive_repository_graph(root), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
