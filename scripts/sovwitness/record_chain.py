"""Recompute the Record Service journal chain without importing the participant.

The arithmetic here is a second implementation of the rule
``services/record/CHARTER.md`` states, written from the charter rather than
borrowed from the service. That duplication is the point: a witness that called
the participant's own digest function would confirm only that the function agrees
with itself.

One profile per branch, and an unrecognised profile returns
``UNKNOWN_DIGEST_PROFILE`` rather than falling back to a weaker one. A witness
that silently graded a v3 entry under v2 would report a chain intact while the
entry's identifier, origin and moment went unchecked.

Split out of ``scripts/witness_record.py`` when adding the v3 branch took that
module past the 300-line limit. The walk owns the observations; this owns the
digest.
"""

from __future__ import annotations

from typing import Any
import hashlib
import json

GENESIS = "0" * 64
LEGACY_DIGEST_PROFILE = "soveraeign-record-chain/v1"
DIGEST_PROFILE = "soveraeign-record-chain/v2"
BOUND_DIGEST_PROFILE = "soveraeign-record-chain/v3"

#: The chain rule as the charter states it: every entry carries the digest of the
#: entry before it, over these fields.
CHAIN_MATERIAL = ("prev_digest", "kind", "subject", "actor", "payload")
#: What record-chain/v3 binds on top of that: the entry's own identifier, where it
#: came from, and when. v2 left all three loose, so an entry could be relabelled or
#: repointed in place and this witness would still have called the chain intact.
BOUND_MATERIAL = CHAIN_MATERIAL + ("entry_id", "source_address", "recorded_at")


def recompute(previous: str, entry: dict[str, Any]) -> str:
    """Rebuild one link of the chain here, from the rule the charter states."""
    profile = entry.get("digest_profile", LEGACY_DIGEST_PROFILE)
    if profile == LEGACY_DIGEST_PROFILE:
        material = [previous] + [
            json.dumps(entry[field], sort_keys=True, separators=(",", ":"))
            if field == "payload" else str(entry[field])
            for field in CHAIN_MATERIAL[1:]
        ]
        encoded = "|".join(material).encode("utf-8")
    elif profile == DIGEST_PROFILE:
        encoded = json.dumps(
            [profile, previous, entry["kind"], entry["subject"], entry["actor"],
             entry["payload"]],
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    elif profile == BOUND_DIGEST_PROFILE:
        encoded = json.dumps(
            [profile, previous, entry["entry_id"], entry["kind"], entry["subject"],
             entry["actor"], entry["source_address"], float(entry["recorded_at"]),
             entry["payload"]],
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    else:
        return "UNKNOWN_DIGEST_PROFILE"
    return hashlib.sha256(encoded).hexdigest()


#: The byte form each profile's stored payload must have. Restated here, from the
#: charter, rather than imported: every profile binds the payload's parsed value,
#: so a check that verified digests alone would call a row clean whose bytes read
#: differently to a different reader. v1 escapes non-ASCII; v2 and v3 do not.
CANONICAL = {
    LEGACY_DIGEST_PROFILE: lambda payload: json.dumps(
        payload, sort_keys=True, separators=(",", ":")),
    DIGEST_PROFILE: lambda payload: json.dumps(
        payload, ensure_ascii=False, allow_nan=False, sort_keys=True,
        separators=(",", ":")),
    BOUND_DIGEST_PROFILE: lambda payload: json.dumps(
        payload, ensure_ascii=False, allow_nan=False, sort_keys=True,
        separators=(",", ":")),
}


def canonical_bytes_disagree(entry: dict[str, Any]) -> bool:
    """Whether this row's stored payload bytes are not its profile's encoding.

    Takes the raw column under `payload_json` when the caller has it. An entry
    read back through the service carries only the parsed value, in which case
    there is nothing here to check and the digest alone stands.
    """
    stored = entry.get("payload_json")
    if stored is None:
        return False
    encode = CANONICAL.get(entry.get("digest_profile", LEGACY_DIGEST_PROFILE))
    if encode is None:
        return True
    try:
        return stored != encode(entry["payload"])
    except (TypeError, ValueError):
        return True


def verify_chain(entries: list[dict[str, Any]]) -> list[str]:
    """Return the entry ids whose digest or whose payload bytes do not recompute."""
    previous, broken = GENESIS, []
    for entry in entries:
        if (entry["prev_digest"] != previous
                or entry["entry_digest"] != recompute(previous, entry)
                or canonical_bytes_disagree(entry)):
            broken.append(entry["entry_id"])
        previous = entry["entry_digest"]
    return broken


__all__ = [
    "BOUND_DIGEST_PROFILE", "BOUND_MATERIAL", "CANONICAL", "CHAIN_MATERIAL",
    "DIGEST_PROFILE", "GENESIS", "LEGACY_DIGEST_PROFILE",
    "canonical_bytes_disagree", "recompute", "verify_chain",
]
