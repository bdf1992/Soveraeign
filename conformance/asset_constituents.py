#!/usr/bin/env python3
"""Predicates for the constituent plane: parts, their content states, and the
observations and diffs that read them.

Held apart from `asset_objects.py`, which judges the whole-asset plane. The
split follows the objects: everything here is a statement about one constituent
or about the difference between two compositions, and nothing here imports
participant code.
"""

from __future__ import annotations

from typing import Any

from asset_shared import (INTRINSIC_REPRESENTATION, PLACEMENT_FIELDS, SOURCE_FIELDS,
                          index_by, records)


# ---- AssetPart and AssetPartVersion ----------------------------------------

def part_is_not_a_file(world: dict[str, Any]) -> list[str]:
    """A path, a filename and a locator are placement or observation, never identity."""
    defects = []
    for part in records(world, "parts"):
        for field in PLACEMENT_FIELDS + SOURCE_FIELDS:
            if field in part:
                defects.append(f"part {part.get('part_id')!r} carries {field!r} as identity")
    return defects


def part_role_is_type_governed(world: dict[str, Any]) -> list[str]:
    """`part_role` is the stable slot the asset's `AssetType` declares."""
    asset = world.get("asset") or {}
    types = index_by(records(world, "asset_types"), "asset_type_id")
    declared = types.get(asset.get("asset_type_id"))
    if declared is None:
        return []
    admitted = {role.get("part_role") for role in declared.get("spec", {}).get("part_roles", [])}
    return [f"part {part.get('part_id')!r} occupies undeclared role {part.get('part_role')!r}"
            for part in records(world, "parts") if part.get("part_role") not in admitted]


def part_version_carries_no_placement_or_source(world: dict[str, Any]) -> list[str]:
    """A content state says what it is, never where it sits or where it came from."""
    defects = []
    for state in records(world, "part_versions"):
        for field in PLACEMENT_FIELDS + SOURCE_FIELDS:
            if field in state or field in (state.get("representation") or {}):
                defects.append(
                    f"part version {state.get('part_version_id')!r} carries {field!r}")
    return defects


def representation_is_intrinsic(world: dict[str, Any]) -> list[str]:
    """A representation carries only what is true of the content itself."""
    defects = []
    for state in records(world, "part_versions"):
        extra = set(state.get("representation") or {}) - INTRINSIC_REPRESENTATION
        for field in sorted(extra):
            defects.append(
                f"part version {state.get('part_version_id')!r} representation carries {field!r}")
    return defects


def custody_is_a_reference(world: dict[str, Any]) -> list[str]:
    """A content state names an address, never a storage form."""
    defects = []
    for state in records(world, "part_versions"):
        if "payload_address" not in state or "content_digest" not in state:
            defects.append(
                f"part version {state.get('part_version_id')!r} has no custody reference")
        for field in ("chunks", "blob_path", "chunk_manifest"):
            if field in state:
                defects.append(
                    f"part version {state.get('part_version_id')!r} names storage form {field!r}")
    return defects


def a_shared_payload_is_not_a_shared_record(world: dict[str, Any]) -> list[str]:
    """Two content states may hold identical bytes and stay distinct records."""
    identifiers: set[str] = set()
    defects = []
    for state in records(world, "part_versions"):
        identifier = state.get("part_version_id")
        if identifier in identifiers:
            defects.append(f"part version {identifier!r} is declared more than once")
        identifiers.add(identifier)
    return defects


# ---- SourceObservation -----------------------------------------------------

def observations_are_not_constitutive(world: dict[str, Any]) -> list[str]:
    """Many observations may point at one content state, and none is required."""
    states = {state.get("part_version_id") for state in records(world, "part_versions")}
    return [f"observation {entry.get('observation_id')!r} names unknown part version "
            f"{entry.get('part_version_id')!r}"
            for entry in records(world, "source_observations")
            if entry.get("part_version_id") not in states]


# ---- AssetVersionDiff ------------------------------------------------------

def diff_is_decided_by_identity(world: dict[str, Any]) -> list[str]:
    """Every kind is decided by identity; an equal payload never establishes a move."""
    states = index_by(records(world, "part_versions"), "part_version_id")
    defects = []
    for change in (world.get("diff") or {}).get("changes", []):
        kind = change.get("kind")
        same_state = change.get("from_part_version_id") == change.get("to_part_version_id")
        same_place = change.get("from_placement") == change.get("to_placement")
        if kind == "MOVED" and not same_state:
            payloads = {states.get(change.get(side), {}).get("payload_address")
                        for side in ("from_part_version_id", "to_part_version_id")}
            reason = " on equal payload alone" if len(payloads) == 1 else ""
            defects.append(f"MOVED names two different content states{reason}")
        if kind == "MOVED" and same_place:
            defects.append("MOVED names an unchanged placement")
        if kind == "CHANGED" and same_state:
            defects.append("CHANGED names one content state")
        if kind == "CHANGED" and not same_place:
            defects.append("CHANGED names a changed placement")
    return defects


