"""Named byte profiles for the Record Service journal chain, and what each one covers.

A chain profile decides which columns of a journal row are bound into the entry
digest. A column that is not bound is recorded but not protected: it can be
rewritten in place and every verification in the repository will still pass. That
distinction was implicit for two profiles and cost the journal its identifiers -
under `record-chain/v2` two entries could exchange `entry_id` values and the chain
verified clean, so any receipt citing an identifier could be repointed at other
content without trace.

``COVERAGE`` states the boundary per profile and
``services/record/tests/test_digest_coverage.py`` proves it column by column, in
both directions: every column named must break the chain when altered, and every
column not named must be shown to survive alteration. A profile whose declaration
drifts from its behaviour fails that test rather than passing quietly.

Profiles are immutable once defined. Correcting what a profile covers means adding
the next profile, never editing an existing one, because an edited profile
silently invalidates every entry already written under it.
"""

from __future__ import annotations

from typing import Any
import hashlib
import json


LEGACY_DIGEST_PROFILE = "soveraeign-record-chain/v1"
DIGEST_PROFILE = "soveraeign-record-chain/v2"
BOUND_DIGEST_PROFILE = "soveraeign-record-chain/v3"

#: The profile new entries are written under. The three names above are the
#: vocabulary; this is the one currently in use.
CURRENT_PROFILE = BOUND_DIGEST_PROFILE

#: Journal columns whose alteration each profile's verification detects.
#:
#: Read a set as the exact tamper-evidence the profile offers. Two columns need
#: their wording stated exactly, because an independent witness proved the earlier
#: phrasing wrong in both directions:
#:
#: `payload_json` is bound by its *parsed value*, not by its stored bytes. On its
#: own that left byte-different, value-identical JSON undetected - and duplicate
#: key injection with it, where two readers of one committed row disagree about
#: its content and the chain endorses both. `RecordService.reconstruct` therefore
#: also requires the stored bytes to be the canonical encoding of that value, so
#: the column is covered against both. `canonical_for` is that encoding.
#:
#: `seq` is absent from every profile and stays absent. It is a local
#: autoincrement carrying no meaning across a restore into another database, so
#: binding it would make a faithful restore verify as tampered. Its *value* is
#: genuinely unprotected - renumbering that preserves order is undetected and
#: hides nothing. Its *order* is protected, by the `prev_digest` link rather than
#: by any digest: every reordering breaks the chain. That is why one column can
#: be both absent here and impossible to reorder unnoticed.
COVERAGE: dict[str, frozenset[str]] = {
    LEGACY_DIGEST_PROFILE: frozenset({
        "kind", "subject", "actor", "payload_json", "prev_digest", "entry_digest",
        "digest_profile",
    }),
    DIGEST_PROFILE: frozenset({
        "kind", "subject", "actor", "payload_json", "prev_digest", "entry_digest",
        "digest_profile",
    }),
    BOUND_DIGEST_PROFILE: frozenset({
        "kind", "subject", "actor", "payload_json", "prev_digest", "entry_digest",
        "digest_profile", "entry_id", "source_address", "recorded_at",
    }),
}

#: Every column the journal table holds, so a coverage claim can be graded against
#: the whole row rather than against the columns somebody remembered to list.
JOURNAL_COLUMNS: frozenset[str] = frozenset({
    "seq", "entry_id", "kind", "subject", "actor", "source_address", "payload_json",
    "recorded_at", "prev_digest", "entry_digest", "digest_profile",
})


def canonical_for(profile: str):
    """The exact encoding a profile's stored `payload_json` bytes must have.

    The digest binds the parsed value, so this is what closes the gap between the
    value the chain protects and the bytes a reader actually reads.
    """
    if profile == LEGACY_DIGEST_PROFILE:
        return legacy_canonical
    if profile in (DIGEST_PROFILE, BOUND_DIGEST_PROFILE):
        return canonical
    raise ValueError(f"unknown record digest profile {profile!r}")


def uncovered(profile: str) -> frozenset[str]:
    """Columns this profile records but does not protect. Empty is not the goal.

    A caller that displays a journal entry as tamper-evident uses this to say which
    of its own fields that claim does not reach.
    """
    if profile not in COVERAGE:
        raise ValueError(f"unknown record digest profile {profile!r}")
    return JOURNAL_COLUMNS - COVERAGE[profile]


def refuse_non_finite(payload: Any) -> None:
    """Raise if the payload carries NaN or Infinity, whatever profile is writing.

    `legacy_canonical` permits both, and has to keep permitting them: v1 rows
    already exist carrying them, and a profile edited in place stops verifying its
    own history. The refusal therefore belongs at admission, where it stops a new
    row joining them without touching the profile obliged to accept the old ones.
    Before profile selection moved to the store this was a side effect of always
    encoding with `canonical`, which meant a store writing v1 would have quietly
    regained the divergence.
    """
    json.dumps(payload, allow_nan=False)


def canonical(payload: Any) -> str:
    """The v2 compact JSON payload form; explicit, UTF-8 capable, and finite."""
    return json.dumps(
        payload, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    )


def legacy_canonical(payload: Any) -> str:
    """The exact Python JSON form persisted by record-chain/v1."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def legacy_digest(previous: str, kind: str, subject: str, actor: str, payload: Any) -> str:
    material = "|".join((previous, kind, subject, actor, legacy_canonical(payload)))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def digest(previous: str, kind: str, subject: str, actor: str, payload: Any) -> str:
    """Hash an unambiguous, domain-separated record-chain/v2 entry."""
    material = json.dumps(
        [DIGEST_PROFILE, previous, kind, subject, actor, payload],
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def bound_digest(previous: str, kind: str, subject: str, actor: str, payload: Any, *,
                 entry_id: str, source_address: str | None, recorded_at: float) -> str:
    """Hash a record-chain/v3 entry, binding the identifier, origin and moment.

    The three fields v2 left loose are bound here. ``recorded_at`` enters as its
    exact float so a change below microsecond resolution is still detected; an
    append-preserving journal corrects a timestamp with a counter-record, never by
    editing the row, so binding it costs nothing a restore needs.
    """
    material = json.dumps(
        [BOUND_DIGEST_PROFILE, previous, entry_id, kind, subject, actor,
         source_address, float(recorded_at), payload],
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def digest_for_profile(
    profile: str, previous: str, kind: str, subject: str, actor: str, payload: Any,
    *, entry_id: str | None = None, source_address: str | None = None,
    recorded_at: float | None = None,
) -> str:
    """Dispatch to the named profile, refusing one it does not implement.

    The keyword arguments are required by ``record-chain/v3`` and ignored by the
    two profiles that never bound them. A v3 verification called without them
    raises rather than silently falling back to a weaker digest.
    """
    if profile == BOUND_DIGEST_PROFILE:
        if entry_id is None or recorded_at is None:
            raise ValueError(
                f"{BOUND_DIGEST_PROFILE} binds entry_id and recorded_at; "
                "verifying without them would grade the entry under a weaker profile"
            )
        return bound_digest(previous, kind, subject, actor, payload, entry_id=entry_id,
                            source_address=source_address, recorded_at=recorded_at)
    if profile == DIGEST_PROFILE:
        return digest(previous, kind, subject, actor, payload)
    if profile == LEGACY_DIGEST_PROFILE:
        return legacy_digest(previous, kind, subject, actor, payload)
    raise ValueError(f"unknown record digest profile {profile!r}")
