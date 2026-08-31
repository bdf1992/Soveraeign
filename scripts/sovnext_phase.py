"""Phase-authority reading for the non-authoritative next-work projection."""

from __future__ import annotations

from pathlib import Path

from sovcustody import collections as custody_collections
from sovsession import phase_context


def position(root: Path) -> tuple[dict, list[dict]]:
    """Current phase authority plus only that active phase's custody records."""
    state = phase_context.collect(root)
    active = state.get("active")
    if active is None or state.get("defects"):
        return state, []
    phase_id = str(active.get("phase_id"))
    records = custody_collections.records(
        root / "contracts" / "custodies.json", root / "contracts" / "custodies", phase_id)
    return state, records
