#!/usr/bin/env python3
"""Field vocabularies and world readers the asset predicates share.

The constants say which fields belong to which plane, so a predicate names a
plane rather than restating a field list. `SPEC.md` owns the planes.
"""

from __future__ import annotations

from typing import Any

#: Fields that describe where a constituent sits, which never belong to a
#: content state or to an identity.
PLACEMENT_FIELDS = ("logical_path", "path", "filename")

#: Fields that describe where something was observed, which are never identity.
SOURCE_FIELDS = ("source_id", "locator", "source_address", "original_path")

#: Everything a representation may carry. Intrinsic to the content, nothing else.
INTRINSIC_REPRESENTATION = frozenset(
    {"media_type", "format", "encoding", "dimensions", "declared_properties"})

#: A payload is reached, never held, by a governed identity.
PAYLOAD_FIELDS = ("payload_address", "content_digest", "blob_path", "chunks", "size")


def records(world: dict[str, Any], key: str) -> list[dict[str, Any]]:
    """The records a world declares under one key. An absent key declares none."""
    value = world.get(key)
    return value if isinstance(value, list) else []


def index_by(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    """Index records by one field, skipping any record that omits it."""
    return {row[key]: row for row in rows if key in row}
