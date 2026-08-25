"""Experimental derivation of explicit Skill Requirement and Capability declarations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .model import ChartingError


_EFFECT_CLASSES = {"RECORD_LOCAL", "RESOURCE_CONSUMPTION", "EXTERNAL_WORLD"}


def derive_experimental_skill_contracts(
    root: Path,
    experiments_root: Path,
    canonical_skills: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[Path], list[str]]:
    """Derive only explicitly declared experimental competence relations."""

    if not experiments_root.exists():
        return [], [], [], []

    requirements: dict[str, dict[str, Any]] = {}
    capabilities: dict[str, dict[str, Any]] = {}
    crossings: list[dict[str, Any]] = []
    sources: list[Path] = []
    omissions: list[str] = []

    for path in sorted(experiments_root.glob("*.skill.json")):
        relative = str(path.relative_to(root)).replace("\\", "/")
        declaration = _read_json_object(path)
        sources.append(path)
        _validate_envelope(declaration, relative)
        omissions.extend(_declared_omissions(declaration, relative))

        skill_slug = _required_text(declaration, "skill", relative)
        skill_id = f"skill:{skill_slug}"
        if skill_id not in canonical_skills:
            raise ChartingError(f"experimental contract references unknown Skill: {skill_id}")

        raw_requirements = declaration.get("requirements")
        if not isinstance(raw_requirements, list) or not raw_requirements:
            raise ChartingError(f"experimental Skill contract has no requirements: {relative}")

        seen_requirement_ids: set[str] = set()
        for raw in raw_requirements:
            requirement_point, capability_point, requirement_crossings = _derive_requirement(
                raw,
                skill_slug=skill_slug,
                skill_id=skill_id,
                source=relative,
                seen_requirement_ids=seen_requirement_ids,
            )
            governing_reference = requirement_point["attributes"]["governing_source"]
            sources.append(_resolve_governing_source(root, governing_reference, relative))

            requirement_id = requirement_point["id"]
            if requirement_id in requirements:
                raise ChartingError(f"duplicate Requirement point: {requirement_id}")
            requirements[requirement_id] = requirement_point

            capability_id = capability_point["id"]
            existing = capabilities.get(capability_id)
            if existing is not None and existing["attributes"] != capability_point["attributes"]:
                raise ChartingError(f"conflicting Capability declaration: {capability_id}")
            capabilities.setdefault(capability_id, capability_point)
            crossings.extend(requirement_crossings)

    points = list(requirements.values()) + list(capabilities.values())
    return points, crossings, sources, omissions


def _validate_envelope(declaration: dict[str, Any], source: str) -> None:
    if declaration.get("format") != "0.1-experimental":
        raise ChartingError(f"unsupported experimental Skill format: {source}")
    if declaration.get("kind") != "skill-competence-contract":
        raise ChartingError(f"invalid experimental Skill contract kind: {source}")
    if declaration.get("source_owner") != "SDLC.md":
        raise ChartingError(f"experimental Skill contract must name SDLC.md owner: {source}")
    if declaration.get("standing") != "PROPOSAL":
        raise ChartingError(f"experimental Skill contract must remain PROPOSAL: {source}")
    if declaration.get("coverage") != "partial":
        raise ChartingError(f"experimental Skill contract must declare partial coverage: {source}")


def _declared_omissions(declaration: dict[str, Any], source: str) -> list[str]:
    raw = declaration.get("omissions")
    if not isinstance(raw, list) or not raw:
        raise ChartingError(f"partial experimental Skill contract must declare omissions: {source}")
    omissions: list[str] = []
    for item in raw:
        if not isinstance(item, str) or not item.strip():
            raise ChartingError(f"experimental Skill omission must be non-empty text: {source}")
        omissions.append(f"{source}: {item.strip()}")
    return omissions


def _derive_requirement(
    raw: Any,
    *,
    skill_slug: str,
    skill_id: str,
    source: str,
    seen_requirement_ids: set[str],
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    if not isinstance(raw, dict):
        raise ChartingError(f"experimental Skill requirement must be an object: {source}")

    requirement_slug = _required_text(raw, "id", source)
    if requirement_slug in seen_requirement_ids:
        raise ChartingError(f"duplicate Skill requirement {requirement_slug}: {source}")
    seen_requirement_ids.add(requirement_slug)

    description = _required_text(raw, "description", source)
    governing_source = _required_text(raw, "governing_source", source)
    capability = raw.get("capability")
    if not isinstance(capability, dict):
        raise ChartingError(f"Skill requirement has no capability selector: {source}")

    capability_name = _required_text(capability, "id", source)
    effect_class = _required_text(capability, "effect_class", source)
    if effect_class not in _EFFECT_CLASSES:
        raise ChartingError(f"undeclared effect class {effect_class}: {source}")

    requirement_id = f"requirement:{skill_slug}:{requirement_slug}"
    capability_id = f"capability:{capability_name}"
    requirement_point = {
        "id": requirement_id,
        "kind": "requirement",
        "label": description,
        "source": source,
        "attributes": {
            "governing_source": governing_source,
            "source_owner": "SDLC.md",
            "standing": "PROPOSAL",
            "coverage": "partial",
        },
    }
    capability_point = {
        "id": capability_id,
        "kind": "capability",
        "label": capability_name,
        "source": source,
        "attributes": {
            "effect_class": effect_class,
            "declaration_only": True,
            "live_availability": False,
        },
    }
    crossings = [
        {
            "id": f"skill-requires:{skill_slug}:{requirement_slug}",
            "kind": "requires",
            "source": skill_id,
            "target": requirement_id,
            "provenance": source,
            "constraints": {"governing_source": governing_source},
        },
        {
            "id": f"requirement-binds:{skill_slug}:{requirement_slug}",
            "kind": "binds",
            "source": requirement_id,
            "target": capability_id,
            "provenance": source,
            "constraints": {
                "effect_class": effect_class,
                "live_receipt_required": True,
            },
        },
    ]
    return requirement_point, capability_point, crossings


def _resolve_governing_source(root: Path, reference: str, declaration_source: str) -> Path:
    """Resolve a governing document reference without allowing path escape."""

    document, _, _anchor = reference.partition("#")
    if not document:
        raise ChartingError(f"governing source must name a document: {declaration_source}")

    relative = Path(document)
    if relative.is_absolute() or ".." in relative.parts:
        raise ChartingError(f"governing source escapes repository: {reference}")

    repository_root = root.resolve()
    resolved = (repository_root / relative).resolve()
    if not resolved.is_relative_to(repository_root) or not resolved.is_file():
        raise ChartingError(f"governing source does not resolve inside repository: {reference}")
    return resolved


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ChartingError(f"cannot read experimental Skill declaration: {path}") from exc
    if not isinstance(value, dict):
        raise ChartingError(f"JSON declaration must be an object: {path}")
    return value


def _required_text(value: dict[str, Any], field: str, source: str) -> str:
    result = value.get(field)
    if not isinstance(result, str) or not result.strip():
        raise ChartingError(f"{field} must be non-empty text: {source}")
    return result.strip()
