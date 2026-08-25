#!/usr/bin/env python3
"""Plan the relationship surface: containment edges and the rendered relations block.

Containment is the only edge GitHub holds natively, and it comes from ``child_issues``
on the epic and ``village_issue`` on each bit or stub. The dependency DAG — ``requires``,
``parent_bits``, ``leans_on``, ``asks``, ``holds`` — stays in the metadata and is only
rendered, because forcing it into a single-parent tree would lose edges
(``CONTRIBUTING.md``, Issue coordination contract).

The label surface is planned next door in ``catalogue.py``. Nothing here reaches GitHub:
every action is derived from a registrar export, so a fresh witness reproduces the plan
offline, and an action no declaration derives is a refusal rather than an improvisation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from sovticket.yamlblock import TicketBlockError, load_ticket  # noqa: E402

BLOCK_BEGIN = "<!-- sov:relations:begin -->"
BLOCK_END = "<!-- sov:relations:end -->"
BLOCK_NOTE = (
    "_Rendered from this issue's metadata block by `adapters/github/apply.py`. The "
    "metadata block is authoritative; this section only makes it readable._"
)
HEADINGS = {
    "requires": "Requires — this cannot advance until each is satisfied",
    "closes_bits": "Closes bits — the obligations this surface discharges",
    "leans_on": "Leans on — back-office supports the crossing needs",
    "asks": "Asks — adjustments this crossing wants of the substrate",
    "holds": "Holds — the ticket this unblock request releases",
}


@dataclass(frozen=True)
class RelationAction:
    """One containment edge: ``child`` becomes a native sub-issue of ``parent``."""

    parent: int
    child: int

    def describe(self) -> str:
        return f"contain  #{self.child:<4} under #{self.parent}"


@dataclass
class BodyAction:
    """A rewritten issue body carrying a regenerated relations block."""

    number: int
    body: str
    edges: dict[str, list[int]] = field(default_factory=dict)

    def describe(self) -> str:
        parts = ", ".join(f"{key}={len(value)}" for key, value in sorted(self.edges.items()))
        return f"body     #{self.number:<4} {parts or 'no edges'}"


def _ref(value: Any) -> int | None:
    """Parse a ``#123`` issue reference into its number, or None if it is not one."""
    if isinstance(value, str) and (match := re.fullmatch(r"#([1-9][0-9]*)", value.strip())):
        return int(match.group(1))
    return None


def _refs(values: Any) -> list[int]:
    """Parse a list of issue references, dropping anything that is not one."""
    if not isinstance(values, list):
        return []
    return [number for number in (_ref(value) for value in values) if number is not None]


def containment_edges(
    tickets: dict[int, dict[str, Any]],
    held: dict[int, int] | None = None,
) -> list[RelationAction]:
    """Derive the containment tree: epic -> village -> bit or implementation stub.

    ``village_issue`` is the containment edge for a bit or a stub, not ``parent``: the
    schema lets a bit name the epic as its parent while its village issue is the node
    that must contain it (``.claude/epic/README.md``). The epic contains its villages
    through its own ``child_issues``. GitHub allows one parent per issue, so an issue
    already placed by the epic is never placed again by a village.

    ``held`` is the containment graph the surface already holds, captured by the export.
    An edge that is already in place is dropped, so the plan reports what would actually
    change rather than what the tree would look like from nothing.
    """
    edges: list[RelationAction] = []
    placed: set[int] = set()
    standing = held or {}

    def place(parent: int, child: int) -> None:
        if child == parent or child in placed:
            return
        placed.add(child)
        if standing.get(child) != parent:
            edges.append(RelationAction(parent, child))

    for number, metadata in sorted(tickets.items()):
        if metadata.get("kind") == "epic-of-epics":
            for child in _refs(metadata.get("child_issues")):
                place(number, child)
    for number, metadata in sorted(tickets.items()):
        if parent := _ref(metadata.get("village_issue")):
            place(parent, number)
    return edges


def held_parents(path: Path) -> dict[int, int]:
    """Read the containment graph the surface already holds out of a registrar export."""
    export = json.loads(path.read_text(encoding="utf-8"))
    return {
        int(issue["number"]): int(issue["parent"])
        for issue in export
        if issue.get("parent") is not None
    }


def render_block(metadata: dict[str, Any], titles: dict[int, str]) -> tuple[str, dict[str, list[int]]]:
    """Render the relations section for one issue, and report the edges it carries.

    ``requires`` and ``parent_bits`` are the dependency DAG and stay out of GitHub's
    single-parent tree (``CONTRIBUTING.md``). Rendering them as plain links keeps the
    metadata authoritative while making the edges visible and back-linked. No closing
    keyword is used: a stub cannot close its bit by itself.
    """
    edges: dict[str, list[int]] = {}
    for key, source in (
        ("requires", metadata.get("requires")),
        ("closes_bits", metadata.get("parent_bits")),
        ("leans_on", metadata.get("leans_on")),
    ):
        if found := _refs(source):
            edges[key] = found
    if held := _ref(metadata.get("held")):
        edges["holds"] = [held]
    asks = [
        (_ref(ask.get("of")), str(ask.get("adjustment", "")))
        for ask in (metadata.get("asks") or [])
        if isinstance(ask, dict) and _ref(ask.get("of"))
    ]
    if asks:
        edges["asks"] = [ref for ref, _ in asks]

    lines = [BLOCK_BEGIN, "", "### Relations", ""]
    for key, heading in HEADINGS.items():
        if key not in edges:
            continue
        lines.extend([f"**{heading}**", ""])
        if key == "asks":
            for ref, adjustment in asks:
                lines.append(f"- #{ref} — {adjustment}")
        else:
            for ref in edges[key]:
                title = titles.get(ref, "")
                lines.append(f"- #{ref}" + (f" — {title}" if title else ""))
        lines.append("")
    if not edges:
        lines.extend(["_No dependency edges declared._", ""])
    lines.extend([BLOCK_NOTE, "", BLOCK_END])
    return "\n".join(lines), edges


def apply_block(body: str, block: str) -> str:
    """Insert or replace the delimited block, leaving every other byte of the body alone."""
    start = body.find(BLOCK_BEGIN)
    end = body.find(BLOCK_END)
    if start != -1 and end > start:
        return body[:start] + block + body[end + len(BLOCK_END):]
    return body.rstrip("\n") + "\n\n" + block + "\n"


def plan_bodies(
    tickets: dict[int, dict[str, Any]],
    bodies: dict[int, str],
    titles: dict[int, str],
) -> list[BodyAction]:
    """Return one action per issue whose rendered relations block differs from its body."""
    actions: list[BodyAction] = []
    for number, metadata in sorted(tickets.items()):
        current = bodies.get(number, "")
        block, edges = render_block(metadata, titles)
        if not edges and BLOCK_BEGIN not in current:
            continue  # An issue with no declared edges gets no block rather than an empty one.
        updated = apply_block(current, block)
        if updated != current:
            actions.append(BodyAction(number, updated, edges))
    return actions


def load_export(path: Path) -> tuple[dict[int, dict], dict[int, str], dict[int, str], list[str]]:
    """Split a registrar export into metadata, bodies, titles, and parse defects.

    An issue whose body carries no ticket block is reported, never guessed at. It keeps
    its body and title so the planner can still name it in another issue's edges, but it
    contributes no edges of its own.
    """
    export = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(export, list):
        raise ValueError(f"{path} is not a ticket export array")
    metadata: dict[int, dict] = {}
    bodies: dict[int, str] = {}
    titles: dict[int, str] = {}
    defects: list[str] = []
    for issue in sorted(export, key=lambda item: item["number"]):
        number = int(issue["number"])
        bodies[number] = issue.get("body") or ""
        titles[number] = issue.get("title") or ""
        try:
            metadata[number] = load_ticket(bodies[number])
        except TicketBlockError as error:
            defects.append(f"#{number}: {error}")
    return metadata, bodies, titles, defects
