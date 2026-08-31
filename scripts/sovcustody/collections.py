"""Discover phase-scoped custody collections without assigning them authority."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json


def paths(legacy: Path, directory: Path) -> tuple[Path, ...]:
    """Historical collection first, then deterministic phase-scoped collections."""
    found: list[Path] = []
    if legacy.exists():
        found.append(legacy)
    if directory.exists():
        found.extend(sorted(path for path in directory.glob("*.json") if path.is_file()))
    return tuple(found)


def documents(legacy: Path, directory: Path) -> list[dict[str, Any]]:
    """Read each collection independently; a filename grants no phase standing."""
    return [json.loads(path.read_bytes().decode("utf-8")) for path in paths(legacy, directory)]


def records(legacy: Path, directory: Path, phase: str | None = None) -> list[dict[str, Any]]:
    """Flatten custody history, optionally restricting the reading to one phase."""
    rows = [row for document in documents(legacy, directory)
            for row in document.get("custodies", [])]
    if phase is not None:
        rows = [row for row in rows if row.get("phase") == phase]
    return rows
