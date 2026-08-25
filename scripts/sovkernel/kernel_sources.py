"""Resolve and address every raw source conditioning the Kernel closure."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any


def closure_source_addresses(manifest_sources: list[str],
                             paradigms: dict[str, Any]) -> list[str]:
    """Every authored or governing source whose bytes condition this closure."""
    addresses = set(manifest_sources)
    addresses.update({
        "contracts/kernel-paradigms.json",
        "contracts/kernel-transitions.json",
    })
    for definition in paradigms.get("paradigms", []):
        addresses.update(source for source in definition.get("sources", [])
                         if isinstance(source, str))
    return sorted(addresses)


def load_source_digests(root: Path, addresses: list[str]) -> tuple[
        list[dict[str, str]], list[str]]:
    """Address closure inputs by raw bytes without permitting path escape."""
    root = root.resolve()
    digests: list[dict[str, str]] = []
    defects: list[str] = []
    for address in sorted(set(addresses)):
        relative = Path(address)
        if relative.is_absolute() or ".." in relative.parts:
            defects.append(f"SOURCE_ADDRESS_INVALID: {address!r} is not repository-relative")
            continue
        path = (root / relative).resolve()
        if root not in path.parents or not path.is_file():
            defects.append(f"SOURCE_UNRESOLVED: {address!r} does not resolve to a file")
            continue
        digests.append({
            "address": relative.as_posix(),
            "digest": sha256(path.read_bytes()).hexdigest(),
        })
    return digests, defects
