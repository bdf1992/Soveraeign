"""Derive the visible label set from ticket metadata and detect drift against it.

``CONTRIBUTING.md`` makes labels a projection of the issue metadata rather than a
second authority. This module makes that mechanically true: it derives the expected
label set from the metadata, and reports any live label the metadata does not imply as
drift rather than accepting it as fact.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import re

LABEL_LINE = re.compile(r'^- name:\s*"(?P<name>[^"]+)"\s*$')
LABEL_FIELD = re.compile(r'^(?P<key>color|description):\s*"(?P<value>[^"]*)"\s*$')


@dataclass(frozen=True)
class Drift:
    """The difference between the projected label set and the live label set."""

    issue: str
    missing: tuple[str, ...]
    unexpected: tuple[str, ...]
    unmapped: tuple[str, ...]

    @property
    def clean(self) -> bool:
        """Report whether the live labels match the projection exactly."""
        return not (self.missing or self.unexpected or self.unmapped)

    def render(self) -> str:
        """Return one human-readable line describing the drift."""
        parts = []
        if self.unmapped:
            parts.append(f"unmapped metadata {', '.join(self.unmapped)}")
        if self.missing:
            parts.append(f"missing {', '.join(self.missing)}")
        if self.unexpected:
            parts.append(f"unexpected {', '.join(self.unexpected)}")
        return f"{self.issue}: " + ("; ".join(parts) if parts else "labels match the projection")


def load_projection(root: Path) -> dict[str, Any]:
    """Load the declared label projection contract."""
    path = root / "contracts" / "ticket-label-projection.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_catalogue_entries(root: Path) -> list[dict[str, str]]:
    """Read the declared label catalogue as name, colour, and description entries.

    The colour and description are what a label has to be created with, so a caller that
    only knows a name can report a missing label but cannot propose creating one.
    """
    path = root / ".github" / "labels.yml"
    entries: list[dict[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        match = LABEL_LINE.match(stripped)
        if match:
            entries.append({"name": match.group("name"), "color": "", "description": ""})
            continue
        if not entries:
            continue
        field = LABEL_FIELD.match(stripped)
        if field and not entries[-1][field.group("key")]:
            entries[-1][field.group("key")] = field.group("value")
    return entries


def load_catalogue(root: Path) -> set[str]:
    """Read the canonical label names declared in ``.github/labels.yml``."""
    return {entry["name"] for entry in load_catalogue_entries(root)}


def project(metadata: dict[str, Any], projection: dict[str, Any]) -> tuple[set[str], list[str]]:
    """Return the label set implied by ``metadata`` and any unmapped metadata values."""
    labels: set[str] = set()
    unmapped: list[str] = []
    kind = metadata.get("kind")
    if kind in projection["kind_to_type"]:
        labels.add(projection["kind_to_type"][kind])
    elif kind is not None:
        unmapped.append(f"kind={kind}")
    if kind in projection["kind_to_scope"]:
        labels.add(projection["kind_to_scope"][kind])

    village = metadata.get("village")
    if kind not in projection["kinds_without_village_label"]:
        if village in projection["village_to_label"]:
            labels.add(projection["village_to_label"][village])
        elif village is not None:
            unmapped.append(f"village={village}")

    horizon = metadata.get("horizon")
    if horizon in projection["horizon_to_label"]:
        labels.add(projection["horizon_to_label"][horizon])
    elif horizon is not None:
        unmapped.append(f"horizon={horizon}")

    effect = metadata.get("effect_class", projection["default_effect_class"])
    if effect in projection["effect_to_label"]:
        label = projection["effect_to_label"][effect]
        if label:
            labels.add(label)
    elif effect is not None:
        unmapped.append(f"effect_class={effect}")

    standing = metadata.get("standing")
    if standing in projection["standing_to_label"]:
        label = projection["standing_to_label"][standing]
        if label:
            labels.add(label)
    elif standing is not None:
        unmapped.append(f"standing={standing}")
    witness = projection["standing_to_witness_label"].get(standing)
    if witness:
        labels.add(witness)
    return labels, unmapped


def compare(issue: str, metadata: dict[str, Any], live: list[str], projection: dict[str, Any]) -> Drift:
    """Compare a live label set against the projection, ignoring labels outside its axes."""
    expected, unmapped = project(metadata, projection)
    prefixes = tuple(projection["unprojected_label_prefixes"])
    governed = {name for name in live if name.startswith(prefixes)}
    return Drift(
        issue=issue,
        missing=tuple(sorted(expected - governed)),
        unexpected=tuple(sorted(governed - expected)),
        unmapped=tuple(unmapped),
    )
