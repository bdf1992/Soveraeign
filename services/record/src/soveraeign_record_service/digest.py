"""Named byte profiles for the Record Service journal chain."""

from __future__ import annotations

from typing import Any
import hashlib
import json


LEGACY_DIGEST_PROFILE = "soveraeign-record-chain/v1"
DIGEST_PROFILE = "soveraeign-record-chain/v2"


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


def digest_for_profile(
    profile: str, previous: str, kind: str, subject: str, actor: str, payload: Any
) -> str:
    if profile == DIGEST_PROFILE:
        return digest(previous, kind, subject, actor, payload)
    if profile == LEGACY_DIGEST_PROFILE:
        return legacy_digest(previous, kind, subject, actor, payload)
    raise ValueError(f"unknown record digest profile {profile!r}")
