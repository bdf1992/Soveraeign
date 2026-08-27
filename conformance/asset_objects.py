#!/usr/bin/env python3
"""Predicates for the `SPEC.md` asset objects, judged against a declared world.

One function per normative invariant. Each takes a world - a plain dict of the
records `SPEC.md` defines - and returns the defects it can see. No function
imports participant code, reads a participant verdict, or touches a filesystem,
so a participant cannot report itself passing and an invariant can be graded
before any implementation carries the objects at all.

The world is the shape `SPEC.md` states: an asset, its declared types, its
constituent parts, their content states, the whole-asset versions that place
them, and any source observations. A key omitted is unknown rather than
satisfied, which is the same reading `conformance/fixtures/kernel` uses.

`decisions/0077` owns the rulings these predicates realize.
"""

from __future__ import annotations

from typing import Any, Callable

from asset_constituents import (a_shared_payload_is_not_a_shared_record,
                                custody_is_a_reference, diff_is_decided_by_identity,
                                observations_are_not_constitutive, part_is_not_a_file,
                                part_role_is_type_governed,
                                part_version_carries_no_placement_or_source,
                                representation_is_intrinsic)
from asset_shared import PAYLOAD_FIELDS, index_by, records


# ---- Asset -----------------------------------------------------------------

def asset_holds_no_payload(world: dict[str, Any]) -> list[str]:
    """An asset is a governed identity, not bytes."""
    asset = world.get("asset") or {}
    return [f"asset carries payload field {field!r}"
            for field in PAYLOAD_FIELDS if field in asset]


def asset_type_is_declared(world: dict[str, Any]) -> list[str]:
    """An `asset_type_id` naming no declared `AssetType` is refused."""
    asset = world.get("asset") or {}
    declared = {entry.get("asset_type_id") for entry in records(world, "asset_types")}
    named = asset.get("asset_type_id")
    if named is None:
        return ["asset declares no asset_type_id"]
    return [] if named in declared else [f"asset_type_id {named!r} is not declared"]


def descriptions_target_a_governed_subject(world: dict[str, Any]) -> list[str]:
    """A description names an asset or a version, never a payload or a placement."""
    governed = {(world.get("asset") or {}).get("asset_id")}
    governed |= {version.get("version_id") for version in records(world, "versions")}
    defects = []
    for description in records(world, "descriptions"):
        subject = description.get("subject_id")
        if subject not in governed:
            defects.append(f"description targets {subject!r}, which is not a governed subject")
    return defects


# ---- AssetType -------------------------------------------------------------

def type_is_declared_once(world: dict[str, Any]) -> list[str]:
    """Redeclaring an `asset_type_id` is refused `STALE_STATE`."""
    seen: set[str] = set()
    defects = []
    for entry in records(world, "asset_types"):
        identifier = entry.get("asset_type_id")
        if identifier in seen:
            defects.append(f"asset_type_id {identifier!r} is declared more than once")
        seen.add(identifier)
    return defects


def media_type_is_not_authority(world: dict[str, Any]) -> list[str]:
    """A media type, suffix or magic reading never stands in for a declared type."""
    asset = world.get("asset") or {}
    named = asset.get("asset_type_id")
    declared = {entry.get("asset_type_id") for entry in records(world, "asset_types")}
    if named in declared:
        return []
    observed = {version.get("representation", {}).get("media_type")
                for version in records(world, "part_versions")}
    if named in observed:
        return [f"asset_type_id {named!r} is an observed media type standing in for a type"]
    return []


def required_roles_are_carried(world: dict[str, Any]) -> list[str]:
    """A version is judged against its asset's type when it is recorded."""
    asset = world.get("asset") or {}
    types = index_by(records(world, "asset_types"), "asset_type_id")
    declared = types.get(asset.get("asset_type_id"))
    if declared is None:
        return []
    required = {role.get("part_role") for role in declared.get("spec", {}).get("part_roles", [])
                if role.get("required")}
    parts = index_by(records(world, "parts"), "part_id")
    defects = []
    for version in records(world, "versions"):
        carried = {parts.get(entry.get("part_id"), {}).get("part_role")
                   for entry in version.get("entries", [])}
        for role in sorted(required - carried):
            defects.append(f"version {version.get('version_id')!r} omits required role {role!r}")
    return defects


# ---- AssetVersion ----------------------------------------------------------

def version_reaches_payload_through_parts(world: dict[str, Any]) -> list[str]:
    """No transition may assume a single payload; a version holds entries, not bytes."""
    defects = []
    for version in records(world, "versions"):
        for field in PAYLOAD_FIELDS:
            if field in version and field != "content_digest":
                defects.append(
                    f"version {version.get('version_id')!r} carries payload field {field!r}")
        if not isinstance(version.get("entries"), list):
            defects.append(f"version {version.get('version_id')!r} carries no entry set")
    return defects


def entries_resolve(world: dict[str, Any]) -> list[str]:
    """Every entry names a part of this asset and a content state of that part."""
    asset_id = (world.get("asset") or {}).get("asset_id")
    parts = index_by(records(world, "parts"), "part_id")
    part_versions = index_by(records(world, "part_versions"), "part_version_id")
    defects = []
    for version in records(world, "versions"):
        for entry in version.get("entries", []):
            part = parts.get(entry.get("part_id"))
            if part is None:
                defects.append(f"entry names unknown part {entry.get('part_id')!r}")
                continue
            if part.get("asset_id") != asset_id:
                defects.append(f"entry names part {part.get('part_id')!r} of another asset")
            state = part_versions.get(entry.get("part_version_id"))
            if state is None:
                defects.append(
                    f"entry names unknown part version {entry.get('part_version_id')!r}")
            elif state.get("part_id") != entry.get("part_id"):
                defects.append(
                    f"entry pairs part {entry.get('part_id')!r} with a state of another part")
    return defects


def placement_lives_on_the_entry(world: dict[str, Any]) -> list[str]:
    """Where a constituent sits is a fact about a composition, not a content state."""
    defects = []
    for version in records(world, "versions"):
        for entry in version.get("entries", []):
            if "placement" not in entry:
                defects.append(f"entry for part {entry.get('part_id')!r} declares no placement")
    return defects


def lineage_and_derivation_are_orthogonal(world: dict[str, Any]) -> list[str]:
    """The two are never collapsed into one exclusive value."""
    defects = []
    for version in records(world, "versions"):
        if "role" in version:
            defects.append(
                f"version {version.get('version_id')!r} stores an exclusive role; lineage and "
                "derivation are read off predecessor_version_id and derivation")
    return defects


def digest_covers_the_entry_set(world: dict[str, Any]) -> list[str]:
    """Equal entry sets carry equal content digests; different sets do not."""
    by_entries: dict[str, set[str]] = {}
    for version in records(world, "versions"):
        key = repr(sorted(
            (entry.get("part_id"), entry.get("part_version_id"),
             (entry.get("placement") or {}).get("logical_path"))
            for entry in version.get("entries", [])))
        by_entries.setdefault(key, set()).add(version.get("content_digest"))
    defects = [f"one entry set carries {len(digests)} content digests"
               for digests in by_entries.values() if len(digests) > 1]
    seen: dict[str, str] = {}
    for key, digests in by_entries.items():
        for digest in digests:
            if digest in seen and seen[digest] != key:
                defects.append(f"content digest {digest!r} covers two different entry sets")
            seen[digest] = key
    return defects


#: Every invariant a case may assert, by the id the corpus uses.
PREDICATES: dict[str, Callable[[dict[str, Any]], list[str]]] = {
    "asset-holds-no-payload": asset_holds_no_payload,
    "asset-type-is-declared": asset_type_is_declared,
    "descriptions-target-a-governed-subject": descriptions_target_a_governed_subject,
    "type-is-declared-once": type_is_declared_once,
    "media-type-is-not-authority": media_type_is_not_authority,
    "required-roles-are-carried": required_roles_are_carried,
    "version-reaches-payload-through-parts": version_reaches_payload_through_parts,
    "entries-resolve": entries_resolve,
    "placement-lives-on-the-entry": placement_lives_on_the_entry,
    "lineage-and-derivation-are-orthogonal": lineage_and_derivation_are_orthogonal,
    "digest-covers-the-entry-set": digest_covers_the_entry_set,
    "part-is-not-a-file": part_is_not_a_file,
    "part-role-is-type-governed": part_role_is_type_governed,
    "part-version-carries-no-placement-or-source": part_version_carries_no_placement_or_source,
    "representation-is-intrinsic": representation_is_intrinsic,
    "custody-is-a-reference": custody_is_a_reference,
    "a-shared-payload-is-not-a-shared-record": a_shared_payload_is_not_a_shared_record,
    "observations-are-not-constitutive": observations_are_not_constitutive,
    "diff-is-decided-by-identity": diff_is_decided_by_identity,
}
