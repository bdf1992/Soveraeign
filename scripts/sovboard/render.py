"""Render a surveyed batch as the surface a reviewer approves from.

The rendering carries the evidence next to the recommendation on purpose. A reviewer who
has to leave this surface to find out why an action is proposed is being asked to redo
the survey, which is the expensive half of the work.
"""

from __future__ import annotations

from sovboard.actions import Action, Batch

RULE_WIDTH = 96
WHY_WIDTH = 58


def _clip(text: str, width: int) -> str:
    """Trim one field to width, marking any trim so a reader never mistakes it for the whole."""
    flat = " ".join(text.split())
    return flat if len(flat) <= width else flat[: width - 1] + "…"


def _proposed_table(actions: list[Action]) -> list[str]:
    """Render the executable actions as an id-addressable table."""
    rows = [
        (action.identity, action.kind, action.target, _clip(action.argument, 22),
         _clip(action.evidence, WHY_WIDTH))
        for action in actions
    ]
    widths = [max(len(row[column]) for row in ([("ID", "ACTION", "TARGET", "ARGUMENT", "WHY")] + rows))
              for column in range(5)]
    lines = []
    header = ("ID", "ACTION", "TARGET", "ARGUMENT", "WHY")
    lines.append("  " + "  ".join(value.ljust(widths[index]) for index, value in enumerate(header)))
    lines.append("  " + "  ".join("-" * widths[index] for index in range(5)))
    for row in rows:
        lines.append("  " + "  ".join(value.ljust(widths[index]) for index, value in enumerate(row)))
    return lines


def _reported_blocks(actions: list[Action]) -> list[str]:
    """Render each report with the full evidence, rule, and recommended move."""
    lines = []
    for action in actions:
        argument = f" {action.argument}" if action.argument else ""
        lines.append(f"  {action.target}  {action.kind}{argument}")
        lines.append(f"       saw   {_clip(action.evidence, RULE_WIDTH)}")
        lines.append(f"       rule  {_clip(action.rule, RULE_WIDTH)}")
        lines.append(f"       do    {_clip(action.recommendation, RULE_WIDTH)}")
        lines.append("")
    return lines


def render(batch: Batch, batch_path: str) -> str:
    """Return the complete review surface for one batch."""
    lines = [
        f"BOARD REVIEW  {batch.repository}  captured {batch.captured_at}",
        f"  export {batch.export_digest}",
        f"  batch  {batch_path}",
        "",
    ]
    proposed, reported = batch.proposed, batch.reported
    if proposed:
        lines.append(f"PROPOSED ({len(proposed)}) — executable, reversible, awaiting your approval")
        lines.append("")
        lines.extend(_proposed_table(proposed))
        lines.append("")
        lines.append(
            f"  approve: python scripts/sov_board.py apply --batch {batch_path} --approve <id>[,<id>|all]"
        )
        lines.append("")
    else:
        lines.append("PROPOSED (0) — nothing executable is outstanding.")
        lines.append("")
    if reported:
        lines.append(
            f"REPORTED ({len(reported)}) — not executable; each needs authorship or your judgement"
        )
        lines.append("")
        lines.extend(_reported_blocks(reported))
    else:
        lines.append("REPORTED (0) — nothing is waiting on authorship or judgement.")
        lines.append("")
    lines.append(
        "A survey is an observation with recommendations attached. Nothing above has run, "
        "and approving an action settles no standing."
    )
    return "\n".join(lines)
