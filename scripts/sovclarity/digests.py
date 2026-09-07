"""Digests for clarity receipts: the artifact whole, and each basis by the address it names.

A basis may address a part of a file (`sovaddress`), so one queue entry in `STATUS.yaml`
no longer stales every receipt whose meaning it never touched.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import sovaddress

DIGEST_PREFIX = "sha256:"


def digest(path: Path) -> str:
    """`sha256:` over a file's exact bytes."""
    return DIGEST_PREFIX + sha256(path.read_bytes()).hexdigest()


def basis_digest(root: Path, source: str) -> str | None:
    """A basis digest by address, or None when the file is gone or the fragment does not resolve."""
    if not (root / sovaddress.split(source)[0]).is_file():
        return None
    try:
        return sovaddress.digest(root, source)
    except sovaddress.AddressError:
        return None
