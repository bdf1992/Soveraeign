"""Bounded JSON Schema (Draft 2020-12 subset) checker with no runtime dependency.

Supported keywords: type, enum, const, required, properties, additionalProperties
(boolean form), items, minItems, uniqueItems, minLength, minimum, maximum,
pattern, anyOf, oneOf, allOf, if/then/else, and local ``$ref`` into ``$defs``.
Unsupported keywords are ignored, so silence on one of them is not evidence of
validity; the subset covers the harness schedule declaration, the kernel event
envelope, and the issue metadata contract.
"""

from __future__ import annotations

from typing import Any, Callable
import json
import re


TYPE_CHECKS: dict[str, Callable[[Any], bool]] = {
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "null": lambda v: v is None,
}


def _resolve_ref(ref: str, root: dict) -> dict:
    if not ref.startswith("#/"):
        raise ValueError(f"only local refs are supported: {ref}")
    node: Any = root
    for part in ref[2:].split("/"):
        node = node[part]
    return node


def _check_type(value: Any, expected: Any, path: str) -> list[str]:
    names = expected if isinstance(expected, list) else [expected]
    if any(TYPE_CHECKS[name](value) for name in names):
        return []
    return [f"{path}: expected type {'|'.join(names)}"]


def _check_object(value: dict, schema: dict, root: dict, path: str) -> list[str]:
    defects = []
    properties = schema.get("properties", {})
    for name in schema.get("required", []):
        if name not in value:
            defects.append(f"{path}: missing required property '{name}'")
    if schema.get("additionalProperties") is False:
        for name in value:
            if name not in properties:
                defects.append(f"{path}: unexpected property '{name}'")
    for name, subschema in properties.items():
        if name in value:
            defects.extend(check(value[name], subschema, root, f"{path}.{name}"))
    return defects


def _check_array(value: list, schema: dict, root: dict, path: str) -> list[str]:
    defects = []
    if "minItems" in schema and len(value) < schema["minItems"]:
        defects.append(f"{path}: fewer than {schema['minItems']} items")
    if schema.get("uniqueItems"):
        seen = {json.dumps(item, sort_keys=True) for item in value}
        if len(seen) != len(value):
            defects.append(f"{path}: items are not unique")
    if "items" in schema:
        for index, item in enumerate(value):
            defects.extend(check(item, schema["items"], root, f"{path}[{index}]"))
    return defects


def _check_scalar(value: Any, schema: dict, path: str) -> list[str]:
    defects = []
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            defects.append(f"{path}: shorter than {schema['minLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            defects.append(f"{path}: does not match pattern {schema['pattern']}")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            defects.append(f"{path}: below minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            defects.append(f"{path}: above maximum {schema['maximum']}")
    return defects


def check(value: Any, schema: dict, root: dict | None = None, path: str = "$") -> list[str]:
    """Return the defects found; an empty list means the subset found nothing wrong."""
    root = schema if root is None else root
    if "$ref" in schema:
        return check(value, _resolve_ref(schema["$ref"], root), root, path)
    defects: list[str] = []
    if "type" in schema:
        defects.extend(_check_type(value, schema["type"], path))
        if defects:
            return defects
    if "enum" in schema and value not in schema["enum"]:
        defects.append(f"{path}: value not in enum {schema['enum']}")
    if "const" in schema and value != schema["const"]:
        defects.append(f"{path}: value is not the constant {schema['const']!r}")
    if isinstance(value, dict):
        defects.extend(_check_object(value, schema, root, path))
    elif isinstance(value, list):
        defects.extend(_check_array(value, schema, root, path))
    else:
        defects.extend(_check_scalar(value, schema, path))
    for subschema in schema.get("allOf", []):
        defects.extend(check(value, subschema, root, path))
    if "anyOf" in schema:
        branches = [check(value, sub, root, path) for sub in schema["anyOf"]]
        if all(branches):
            defects.append(f"{path}: matches no anyOf branch")
    if "oneOf" in schema:
        matched = sum(1 for sub in schema["oneOf"] if not check(value, sub, root, path))
        if matched != 1:
            defects.append(f"{path}: matches {matched} oneOf branches, expected exactly 1")
    if "if" in schema:
        taken = "then" if not check(value, schema["if"], root, path) else "else"
        if taken in schema:
            defects.extend(check(value, schema[taken], root, path))
    return defects


def validate(value: Any, schema: dict) -> None:
    """Raise ValueError listing every defect the subset detects."""
    defects = check(value, schema)
    if defects:
        raise ValueError("; ".join(defects))
