"""Canonical JSON and SHA-256 digests for kernel records.

A digest is the kernel's only notion of "exact pre-state": a caller declares the
digest it observed, and the kernel compares it with the digest of what it holds
now. The encoding is canonical so two bindings computing the digest of the same
logical state agree byte for byte.
"""

from __future__ import annotations

from hashlib import sha256
from typing import Any
import json


def canonical_json(value: Any) -> str:
    """Serialize ``value`` deterministically: sorted keys, no whitespace, ASCII only."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest_of(value: Any) -> str:
    """Return ``sha256:<hex>`` over the canonical JSON of ``value``."""
    return "sha256:" + sha256(canonical_json(value).encode("utf-8")).hexdigest()
