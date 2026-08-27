"""Derive the board for one custody, and render it.

A board is not stored. It is computed from the custody, the circuit, and the
live tree, for the same reason the worklist derives its half: a stored board
goes stale silently, and the staleness is invisible precisely when the board
looks busiest. Recomputation is what makes a column empty.

The columns are the circuit stages. A member sits in the column it has reached,
and the distance from the rightmost occupied column to the custody's declared
target is the only progress reading this repository can honestly produce.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovcustody import circuit as circuitmod  # noqa: E402
from sovcustody import estimate as estimatemod  # noqa: E402


def derived_items() -> list[dict[str, Any]]:
    """Derived work items from the worklist, or an empty list if it cannot run.

    The worklist is a sibling projection and may legitimately be absent from a
    partial checkout. An empty list is reported as empty rather than as zero
    outstanding work; the caller prints which of the two it got.
    """
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "sov_worklist.py"), "derive", "--json"],
        capture_output=True, text=True, check=False, cwd=ROOT,
    )
    if result.returncode:
        return []
    try:
        return json.loads(result.stdout)
    except ValueError:
        return []


def _dotted(address: str) -> str:
    """`sov://console/grant` and `services/console` both reduce toward `console.grant`.

    The worklist addresses an operation as a URI and a custody names it the way
    the service manifest does. Without this the join silently returns nothing,
    which reads on a board as no outstanding work rather than as no match.
    """
    trimmed = address.removeprefix("sov://").removeprefix("services/")
    return trimmed.replace("/", ".").strip(".")


def attached(custody: dict[str, Any], items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Derived items whose subject falls inside one of this custody's members."""
    addresses = [str(member.get("address")) for member in custody.get("members") or []]
    matched: list[dict[str, Any]] = []
    for item in items:
        subject = (item.get("subject") or {})
        raw = str(subject.get("address") or "")
        dotted = _dotted(raw)
        service = str(subject.get("service_id") or "")
        for address in addresses:
            member = _dotted(address)
            if (raw.startswith(address) or dotted == member
                    or dotted.startswith(f"{member}.")
                    or (service and member == service)):
                matched.append({**item, "attached_to": address})
                break
    return matched


def build(custody: dict[str, Any], with_derived: bool = True) -> dict[str, Any]:
    """The whole board for one custody as one record."""
    names = circuitmod.stage_names()
    columns: dict[str, list[dict[str, Any]]] = {name: [] for name in names}
    for member in custody.get("members") or []:
        stage = str(member.get("stage") or "")
        columns.setdefault(stage, []).append(member)

    # `names` is already in circuit order, so the first occupied column is the
    # least-drawn member and the last is the frontier. Progress is read from the
    # least-drawn one: a custody is only as far along as its laggard, because the
    # target applies to the whole initiative rather than to its best member.
    occupied = [name for name in names if columns.get(name)]
    reached = occupied[0] if occupied else None
    frontier = occupied[-1] if occupied else None
    target = str(custody.get("target_stage") or "")

    derived = attached(custody, derived_items()) if with_derived else []
    entry = str(custody.get("entry_stage") or "")
    required = estimatemod.required_at(entry, circuitmod.ordinal)

    return {
        "custody_id": custody.get("custody_id"),
        "custody_kind": custody.get("custody_kind"),
        "serves_exit": custody.get("serves_exit"),
        "outside_phase_exit": custody.get("outside_phase_exit"),
        "exit_clause": custody.get("exit_clause"),
        "initiative": custody.get("initiative"),
        "held_by": custody.get("held_by"),
        "entry_stage": entry,
        "target_stage": target,
        "lowest_member_stage": reached,
        "highest_member_stage": frontier,
        "stages_to_target": max(
            0, circuitmod.ordinal(target) - circuitmod.ordinal(reached or entry)),
        "columns": columns,
        "derived_items": derived,
        "closure": custody.get("closure"),
        "required_dimensions": sorted(required),
        "variance": estimatemod.variance(custody.get("estimate")),
        "depends_on": custody.get("depends_on") or [],
    }


def render(board: dict[str, Any]) -> str:
    """The board as text, with the evidence a reader needs to disagree with it."""
    lines: list[str] = []
    lines.append(f"{board['custody_id']}   held by {board['held_by']}")
    lines.append(f"  {board['initiative']}")
    lines.append("")
    lines.append(f"  circuit  entry {board['entry_stage']} -> target {board['target_stage']}"
                 f"   ({board['stages_to_target']} stage(s) to go from the least-drawn member)")
    if board["depends_on"]:
        lines.append(f"  waits on {', '.join(board['depends_on'])}")
    lines.append("")

    for name in circuitmod.stage_names():
        members = board["columns"].get(name) or []
        marker = "<" if name == board["target_stage"] else " "
        lines.append(f"  {marker} {name:<20} {len(members):>2}")
        for member in members:
            observed = member.get("stage_observed_by")
            witness = f"  observed by {observed}" if observed else "  [build claim]"
            lines.append(f"      {member.get('member_kind'):<10} {member.get('address')}{witness}")
            note = member.get("note")
            if note:
                lines.append(f"                 {note}")
    lines.append("")

    if board["derived_items"]:
        lines.append(f"  derived work attached: {len(board['derived_items'])}")
        for item in board["derived_items"][:8]:
            lines.append(f"      {item.get('kind', ''):<10} "
                         f"{(item.get('subject') or {}).get('address', '')}")
        if len(board["derived_items"]) > 8:
            lines.append(f"      ... {len(board['derived_items']) - 8} more")
        lines.append("")

    closure = board.get("closure") or {}
    check = closure.get("check") or {}
    lines.append("  closes when")
    if check:
        lines.append(f"      {check.get('kind')}  {check.get('expression')}")
    if closure.get("judgement_seat"):
        lines.append(f"      settled by {closure['judgement_seat']}")
    lines.append(f"  defeated by  {closure.get('defeated_by', '-')}")
    lines.append("")

    if board["variance"]:
        lines.append("  estimate")
        for row in board["variance"]:
            actual = "-" if row["actual"] is None else row["actual"]
            lines.append(f"      {row['dimension_id']:<22} "
                         f"{row['low']:>8} .. {row['high']:<10} actual {actual:<10} "
                         f"{row['verdict']}")
    missing = set(board["required_dimensions"]) - {
        row["dimension_id"] for row in board["variance"]}
    if missing:
        lines.append(f"  MISSING_REQUIRED_DIMENSION: {', '.join(sorted(missing))}")
    return "\n".join(lines)


def summary(custodies: list[dict[str, Any]]) -> str:
    """The set as a hierarchy: each exit custody, then the delivery work beneath it.

    Printed as a tree rather than a flat list because a flat list is the shape the
    first draft of the custody set took, and mixing an exit obligation with a
    coordination cleanup as peers is what that draft got wrong.
    """
    width = max([len(str(record.get("custody_id"))) for record in custodies] + [7]) + 2
    lines = [f"{len(custodies)} custodies "
             f"({sum(1 for r in custodies if r.get('custody_kind') == 'EXIT')} exit, "
             f"{sum(1 for r in custodies if r.get('custody_kind') == 'DELIVERY')} delivery)",
             ""]
    lines.append(f"  {'custody':<{width}} {'entry':<19} {'target':<19} {'to go':>5}  members")

    def row(record: dict[str, Any], indent: str) -> str:
        board = build(record, with_derived=False)
        label = indent + str(board["custody_id"])
        return (f"  {label:<{width}} {board['entry_stage']:<19} "
                f"{board['target_stage']:<19} {board['stages_to_target']:>5}  "
                f"{sum(len(column) for column in board['columns'].values())}")

    for record in [r for r in custodies if r.get("custody_kind") == "EXIT"]:
        lines.append(row(record, ""))
        for child in custodies:
            if child.get("serves_exit") == record["custody_id"]:
                lines.append(row(child, "  "))
    outside = [r for r in custodies if r.get("outside_phase_exit")]
    if outside:
        lines.append("")
        lines.append("  explicitly outside the phase exit")
        for record in outside:
            lines.append(row(record, "  "))
    return "\n".join(lines)
