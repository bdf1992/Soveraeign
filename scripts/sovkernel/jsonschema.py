"""Bounded JSON Schema Draft 2020-12 subset validator with no runtime dependency.

The validator implements exactly the keyword set used by ``contracts/*.schema.json``
and reports an unsupported keyword as a defect rather than ignoring it. A validator
that silently skips a keyword it does not understand reports a passing result for an
unchecked constraint, which is the green-build-as-authority failure ``AGENTS.md``
refuses.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
import re

ANNOTATION_KEYWORDS = frozenset(
    {"$schema", "$id", "$comment", "title", "description", "default", "examples"}
)
SUPPORTED_KEYWORDS = frozenset(
    {
        "$defs",
        "$ref",
        "additionalProperties",
        "allOf",
        "anyOf",
        "const",
        "else",
        "enum",
        "format",
        "if",
        "items",
        "maxItems",
        "minItems",
        "minLength",
        "minProperties",
        "minimum",
        "oneOf",
        "pattern",
        "properties",
        "required",
        "then",
        "type",
        "uniqueItems",
    }
)
SUPPORTED_FORMATS = frozenset({"date-time"})
DIALECT = "https://json-schema.org/draft/2020-12/schema"
RFC3339_PROFILE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)


def _type_matches(instance: Any, name: str) -> bool:
    """Report whether ``instance`` satisfies one JSON Schema type name."""
    if name == "null":
        return instance is None
    if name == "boolean":
        return isinstance(instance, bool)
    if name == "integer":
        return isinstance(instance, int) and not isinstance(instance, bool)
    if name == "number":
        return isinstance(instance, (int, float)) and not isinstance(instance, bool)
    if name == "string":
        return isinstance(instance, str)
    if name == "array":
        return isinstance(instance, list)
    if name == "object":
        return isinstance(instance, dict)
    return False


def _is_date_time(value: str) -> bool:
    """Apply SOV-RFC3339-1 before asking datetime to validate calendar values."""
    if not RFC3339_PROFILE.fullmatch(value) or value.endswith("-00:00"):
        return False
    if not value.endswith("Z"):
        offset = value[-6:]
        if int(offset[1:3]) > 23 or int(offset[4:6]) > 59:
            return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _resolve(ref: str, root: dict[str, Any], path: str) -> tuple[Any, list[str]]:
    """Resolve a local JSON pointer reference, refusing every other reference form."""
    if not ref.startswith("#/"):
        return None, [f"{path}: unsupported non-local $ref {ref!r}"]
    node: Any = root
    for token in ref[2:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, dict) or token not in node:
            return None, [f"{path}: unresolvable $ref {ref!r}"]
        node = node[token]
    if not isinstance(node, dict):
        return None, [f"{path}: $ref {ref!r} does not resolve to a schema"]
    return node, []


def _check_object(instance: dict[str, Any], schema: dict[str, Any], root: Any, path: str) -> list[str]:
    """Apply the object keywords to a mapping instance."""
    defects: list[str] = []
    properties = schema.get("properties", {})
    for name in schema.get("required", []):
        if name not in instance:
            defects.append(f"{path}: missing required property {name!r}")
    if "minProperties" in schema and len(instance) < schema["minProperties"]:
        defects.append(f"{path}: fewer than {schema['minProperties']} properties")
    extra = schema.get("additionalProperties")
    for key, value in instance.items():
        child = f"{path}{key}" if path == "/" else f"{path}/{key}"
        if key in properties:
            defects.extend(validate(value, properties[key], root, child))
        elif extra is False:
            defects.append(f"{child}: additional property is not permitted")
        elif isinstance(extra, dict):
            defects.extend(validate(value, extra, root, child))
    return defects


def _check_array(instance: list[Any], schema: dict[str, Any], root: Any, path: str) -> list[str]:
    """Apply the array keywords to a sequence instance."""
    defects: list[str] = []
    if "minItems" in schema and len(instance) < schema["minItems"]:
        defects.append(f"{path}: fewer than {schema['minItems']} items")
    if "maxItems" in schema and len(instance) > schema["maxItems"]:
        defects.append(f"{path}: more than {schema['maxItems']} items")
    if schema.get("uniqueItems") and len(instance) != len({repr(item) for item in instance}):
        defects.append(f"{path}: items are not unique")
    if "items" in schema:
        for index, item in enumerate(instance):
            child = f"{path}{index}" if path == "/" else f"{path}/{index}"
            defects.extend(validate(item, schema["items"], root, child))
    return defects


def _check_scalar(instance: Any, schema: dict[str, Any], path: str) -> list[str]:
    """Apply the string and number keywords to a scalar instance."""
    defects: list[str] = []
    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            defects.append(f"{path}: shorter than {schema['minLength']} characters")
        pattern = schema.get("pattern")
        if pattern is not None and not re.search(pattern, instance):
            defects.append(f"{path}: {instance!r} does not match pattern {pattern!r}")
        if schema.get("format") == "date-time" and not _is_date_time(instance):
            defects.append(f"{path}: {instance!r} is not an RFC 3339 date-time")
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            defects.append(f"{path}: below minimum {schema['minimum']}")
    return defects


def _check_combinators(instance: Any, schema: dict[str, Any], root: Any, path: str) -> list[str]:
    """Apply allOf, anyOf, oneOf, and if/then/else."""
    defects: list[str] = []
    for sub in schema.get("allOf", []):
        defects.extend(validate(instance, sub, root, path))
    if "anyOf" in schema and all(validate(instance, sub, root, path) for sub in schema["anyOf"]):
        defects.append(f"{path}: matches no anyOf branch")
    if "oneOf" in schema:
        matched = sum(1 for sub in schema["oneOf"] if not validate(instance, sub, root, path))
        if matched != 1:
            defects.append(f"{path}: matches {matched} oneOf branches, expected exactly 1")
    if "if" in schema:
        branch = "then" if not validate(instance, schema["if"], root, path) else "else"
        if branch in schema:
            defects.extend(validate(instance, schema[branch], root, path))
    return defects


def validate(instance: Any, schema: Any, root: Any = None, path: str = "") -> list[str]:
    """Validate ``instance`` against ``schema`` and return every defect found.

    An empty list means the instance satisfies every supported constraint. It does not
    mean the instance is correct, admitted, witnessed, or authoritative.
    """
    if schema is True:
        return []
    if schema is False:
        return [f"{path or '/'}: schema refuses every instance"]
    if not isinstance(schema, dict):
        return [f"{path or '/'}: schema is not an object"]
    top_level = root is None or (root is schema and path in ("", "/"))
    if top_level and schema.get("$schema") != DIALECT:
        return [f"{path or '/'}: schema must declare dialect {DIALECT!r}"]
    root = schema if top_level else root
    path = path or "/"

    unsupported = set(schema) - SUPPORTED_KEYWORDS - ANNOTATION_KEYWORDS
    if unsupported:
        return [f"{path}: unsupported schema keyword(s) {sorted(unsupported)}"]
    declared_format = schema.get("format")
    if declared_format is not None and declared_format not in SUPPORTED_FORMATS:
        return [f"{path}: unsupported format {declared_format!r}"]

    if "$ref" in schema:
        target, errors = _resolve(schema["$ref"], root, path)
        if errors:
            return errors
        defects = validate(instance, target, root, path)
    else:
        defects = []

    if "type" in schema:
        names = schema["type"]
        names = [names] if isinstance(names, str) else names
        if not any(_type_matches(instance, name) for name in names):
            return [f"{path}: type is not one of {names}"]
    if "const" in schema and instance != schema["const"]:
        defects.append(f"{path}: {instance!r} is not the constant {schema['const']!r}")
    if "enum" in schema and instance not in schema["enum"]:
        defects.append(f"{path}: {instance!r} is not one of {schema['enum']}")

    defects.extend(_check_scalar(instance, schema, path))
    if isinstance(instance, dict):
        defects.extend(_check_object(instance, schema, root, path))
    if isinstance(instance, list):
        defects.extend(_check_array(instance, schema, root, path))
    defects.extend(_check_combinators(instance, schema, root, path))
    return defects
