"""Pattern loading, hashing, and structural checks for Environment."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any
import json

from .errors import EnvironmentRefused


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: object) -> str:
    return "sha256:" + sha256(canonical(value)).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise EnvironmentRefused("DOCUMENT_NOT_OBJECT")
    return value


def validate_pattern(pattern: dict[str, Any]) -> list[str]:
    defects: list[str] = []
    if pattern.get("schema") != "soveraeign-environment-pattern/v1":
        defects.append("PATTERN_SCHEMA_UNSUPPORTED")
    definitions = pattern.get("environment_definitions") or []
    ids = [str(item.get("id") or "") for item in definitions]
    if not ids or any(not item for item in ids):
        defects.append("ENVIRONMENT_DEFINITION_ID_REQUIRED")
    if len(ids) != len(set(ids)):
        defects.append("ENVIRONMENT_DEFINITION_DUPLICATE")
    env_ids = set(ids)
    for item in definitions:
        if item.get("multiplicity") not in {"ONE", "MANY"}:
            defects.append(f"ENVIRONMENT_MULTIPLICITY_INVALID:{item.get('id')}")
        if item.get("acceptance") not in {"NONE", "EXPLICIT"}:
            defects.append(f"ENVIRONMENT_ACCEPTANCE_INVALID:{item.get('id')}")

    trunks = pattern.get("trunk_definitions") or []
    trunk_ids: set[str] = set()
    for trunk in trunks:
        trunk_id = str(trunk.get("id") or "")
        if not trunk_id:
            defects.append("TRUNK_ID_REQUIRED")
        elif trunk_id in trunk_ids:
            defects.append(f"TRUNK_DUPLICATE:{trunk_id}")
        trunk_ids.add(trunk_id)
        for crossing in trunk.get("crossings") or []:
            source = crossing.get("from")
            target = crossing.get("to")
            if source not in env_ids or target not in env_ids:
                defects.append(f"CROSSING_ENVIRONMENT_UNKNOWN:{trunk_id}:{source}->{target}")
            if source == target:
                defects.append(f"CROSSING_SELF_LOOP:{trunk_id}:{source}")
            if crossing.get("serialization") not in {"NONE", "INTEGRATION"}:
                defects.append(
                    f"CROSSING_SERIALIZATION_INVALID:{trunk_id}:{source}->{target}"
                )
            if not isinstance(crossing.get("evidence") or [], list):
                defects.append(f"CROSSING_EVIDENCE_INVALID:{trunk_id}:{source}->{target}")
    if not trunks:
        defects.append("TRUNK_DEFINITION_REQUIRED")

    for name, selector in (pattern.get("selectors") or {}).items():
        if selector.get("kind") != "ACCEPTED_HISTORY":
            defects.append(f"SELECTOR_KIND_UNSUPPORTED:{name}")
        if not isinstance(selector.get("offset"), int) or selector.get("offset") < 0:
            defects.append(f"SELECTOR_OFFSET_INVALID:{name}")
        if selector.get("environment") not in env_ids:
            defects.append(f"SELECTOR_ENVIRONMENT_UNKNOWN:{name}")
    return defects
