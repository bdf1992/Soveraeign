#!/usr/bin/env python3
"""Plan the label surface: the catalogue itself, and the labels each issue wears.

Two diffs live here, and they are different questions. The catalogue diff asks whether
GitHub's label definitions match ``.github/labels.yml`` — the names, colours, and
descriptions. The issue diff asks whether each ticket wears the labels its metadata
projects, under ``contracts/ticket-label-projection.json``. A board can pass one and fail
the other, which is how a fully grey catalogue survived a clean drift report.

Nothing here reaches GitHub. Both diffs are computed from a registrar export and the
local declarations, so a fresh witness reproduces them offline.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
import json
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from sovticket.labels import load_projection, project  # noqa: E402

LABEL_LINE = re.compile(r'^- name: "(?P<name>[^"]+)"$')
COLOR_LINE = re.compile(r'^  color: "(?P<color>[0-9A-Fa-f]{6})"$')
DESC_LINE = re.compile(r'^  description: "(?P<description>[^"]*)"$')
RETIRE_LINE = re.compile(r'^- retire: "(?P<name>[^"]+)"$')
# GitHub rejects a longer label description with HTTP 422, so the catalogue refuses it
# here rather than discovering it mid-crossing with some labels already written.
DESCRIPTION_LIMIT = 100

__all__ = [
    "DESCRIPTION_LIMIT",
    "IssueLabelAction",
    "LabelAction",
    "live_labels",
    "load_projection",
    "plan_issue_labels",
    "plan_labels",
    "read_catalogue",
]


@dataclass(frozen=True)
class LabelAction:
    """One declared label mutation: create, edit, or delete."""

    verb: str
    name: str
    color: str = ""
    description: str = ""

    def describe(self) -> str:
        if self.verb == "delete":
            return f"delete   {self.name}"
        return f"{self.verb:8} {self.name:32} #{self.color}"


@dataclass(frozen=True)
class IssueLabelAction:
    """The label set one issue must gain and lose to match the projection."""

    number: int
    add: tuple[str, ...]
    remove: tuple[str, ...]

    def describe(self) -> str:
        gained = " ".join(f"+{name}" for name in self.add)
        lost = " ".join(f"-{name}" for name in self.remove)
        return f"labels   #{self.number:<4} {' '.join(filter(None, (gained, lost)))}"


def read_catalogue(root: Path) -> tuple[dict[str, tuple[str, str]], list[str]]:
    """Return the governed label catalogue and the retired names, in declaration order."""
    governed: dict[str, tuple[str, str]] = {}
    retired: list[str] = []
    name: str | None = None
    color: str | None = None
    for raw in (root / ".github" / "labels.yml").read_text(encoding="utf-8").splitlines():
        if match := LABEL_LINE.match(raw):
            name, color = match.group("name"), None
        elif match := COLOR_LINE.match(raw):
            color = match.group("color").upper()
        elif match := DESC_LINE.match(raw):
            if name is None or color is None:
                raise ValueError(f"description without a preceding name and colour: {raw}")
            description = match.group("description")
            if len(description) > DESCRIPTION_LIMIT:
                raise ValueError(
                    f"{name}: description is {len(description)} characters; GitHub rejects "
                    f"anything over {DESCRIPTION_LIMIT}"
                )
            governed[name] = (color, description)
            name = color = None
        elif match := RETIRE_LINE.match(raw):
            retired.append(match.group("name"))
    overlap = sorted(set(retired) & set(governed))
    if overlap:
        raise ValueError(f"label is both governed and retired: {overlap}")
    return governed, retired


def live_labels(path: Path) -> dict[str, tuple[str, str]]:
    """Read the live label catalogue captured beside a ticket export.

    The sibling ``.labels.json`` carries every label the repository defines, including
    the ones no issue wears. Reading only the labels seen on issues would report an
    unworn label as absent and plan a create that collides with what is already there.
    """
    sidecar = path.with_name(path.stem + ".labels.json")
    if not sidecar.exists():
        raise FileNotFoundError(
            f"{sidecar} is missing; re-run adapters/github/export.py to capture the label catalogue"
        )
    return {
        label["name"]: (label.get("color", "").upper(), label.get("description") or "")
        for label in json.loads(sidecar.read_text(encoding="utf-8"))
    }


def plan_labels(
    governed: dict[str, tuple[str, str]],
    retired: Iterable[str],
    live: dict[str, tuple[str, str]],
) -> list[LabelAction]:
    """Diff the declared catalogue against the live surface.

    Only labels the catalogue governs or retires are touched. A live label that is
    neither is left alone: deleting something nobody declared is not this tool's call.
    """
    actions: list[LabelAction] = []
    for name, (color, description) in governed.items():
        if name not in live:
            actions.append(LabelAction("create", name, color, description))
        elif live[name] != (color, description):
            actions.append(LabelAction("edit", name, color, description))
    for name in retired:
        if name in live:
            actions.append(LabelAction("delete", name))
    return actions


def plan_issue_labels(
    tickets: dict[int, dict[str, Any]],
    live: dict[int, list[str]],
    projection: dict[str, Any],
) -> tuple[list[IssueLabelAction], list[str]]:
    """Reconcile each issue's governed labels with what its metadata projects.

    Only labels under a governed prefix are touched, so a label outside the declared
    axes is left where it is rather than silently stripped. An issue carrying metadata
    the projection cannot map is skipped and reported: stripping its labels because a
    value was unrecognised would turn a gap in the projection into damage on the board.
    """
    actions: list[IssueLabelAction] = []
    unmapped_defects: list[str] = []
    prefixes = tuple(projection["unprojected_label_prefixes"])
    for number, metadata in sorted(tickets.items()):
        expected, unmapped = project(metadata, projection)
        if unmapped:
            unmapped_defects.append(f"#{number}: unmapped metadata {sorted(unmapped)}")
            continue
        governed = {name for name in live.get(number, []) if name.startswith(prefixes)}
        add, remove = sorted(expected - governed), sorted(governed - expected)
        if add or remove:
            actions.append(IssueLabelAction(number, tuple(add), tuple(remove)))
    return actions, unmapped_defects
