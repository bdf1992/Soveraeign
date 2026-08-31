#!/usr/bin/env python3
"""Reconcile every signpost that claims to say what happens next.

Five documents name the next action in five vocabularies. This reads all of
them, resolves the ``ROADMAP.md`` name crosswalk, grades the four-lane shape
that roadmap declares, and prints one answer with
every alias it travels under. It settles nothing: where the declared gate and
the reachable work name different jobs, that disagreement is reported rather
than resolved, because choosing between them is judgement and judgement is
owner-held. Blocked edge is not blocked frontier: a declared gate stops one
transition, and the reachable work printed here stays reachable regardless
(``AGENTS.md``, Authority).

Every read is local. Nothing here reaches the coordination surface.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import argparse
import json
import re

import roadmap_lanes
import sovnext_phase
from sovsession import phase_context


ROOT = Path(__file__).resolve().parents[1]

CROSSWALK_HEADER = "| Phase | Epic ticket | Governing debt or objective | Drawn as |"


def _text(relative: str) -> str:
    """Read repository text as UTF-8 without newline translation."""
    return (ROOT / relative).read_bytes().decode("utf-8")


phase_position = sovnext_phase.position


def declared_gate(status_text: str) -> str | None:
    """The gate STATUS.yaml currently declares."""
    match = re.search(r"^next_gate:\s*(\S+)\s*$", status_text, re.M)
    return match.group(1) if match else None


def roadmap_phases(roadmap_text: str) -> dict[str, str]:
    """Phase id -> heading text, from the ROADMAP section headings.

    Both ladders are accepted: `F0`-`F6` from the archived roadmap and `P0`-`P9`
    from the current one, at heading level two or three, with or without the
    backticks the newer document uses. Multi-digit, matching ``roadmap_document``:
    reading one digit here and many there made a `P10` unreadable to this reader
    and readable to that one, so the unreadable-token refusal fired on a token
    that was correctly written.
    """
    phases = {}
    for match in re.finditer(r"^#{2,3} `?([FP]\d+)`?\s*·\s*(.+?)\s*$", roadmap_text, re.M):
        phases[match.group(1)] = match.group(2)
    return phases


def crosswalk(roadmap_text: str) -> list[dict[str, str]]:
    """Rows of the ROADMAP name crosswalk, the only place identity is asserted."""
    text = roadmap_text
    if CROSSWALK_HEADER not in text:
        return []
    body = text.split(CROSSWALK_HEADER, 1)[1].splitlines()
    rows = []
    for line in body[1:]:
        if not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 4 or all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        phase = re.search(r"`([FP]\d+)`", cells[0])
        ticket = re.search(r"`#(\d+)`", cells[1])
        rows.append({
            "phase": phase.group(1) if phase else "",
            "phase_label": cells[0],
            "ticket": ticket.group(1) if ticket else "",
            "debt": cells[2],
            "drawn": cells[3],
        })
    return rows


def epic_ready(issues: dict) -> list[dict[str, str]]:
    """Open tickets whose every requirement is satisfied, from the local projection."""
    settled = {"WITNESSED", "RATIFIED", "DEMOTED"}
    actionable = {"bit", "implementation-stub", "story"}
    ready = []
    for number, issue in issues.items():
        metadata = issue.get("metadata") or {}
        if issue.get("state") != "OPEN" or metadata.get("standing") in settled:
            continue
        if metadata.get("kind") not in actionable:
            continue
        blockers = []
        for requirement in (metadata.get("requires") or []):
            other = issues.get(requirement.lstrip("#")) or {}
            if (other.get("metadata") or {}).get("standing") not in settled:
                blockers.append(requirement)
        if not blockers:
            ready.append({"number": number, "title": issue.get("title", ""),
                          "standing": metadata.get("standing", "?"),
                          "horizon": metadata.get("horizon", "?")})
    return sorted(ready, key=lambda row: int(row["number"]))


def stale_views(root: Path) -> list[tuple[str, list[str]]]:
    """Diagram views whose recorded source_digest no longer matches its source."""
    stale = []
    for view in sorted((root / "diagrams").glob("*.md")):
        if view.name == "README.md":
            continue
        text = view.read_bytes().decode("utf-8")
        header = re.search(r"^source\s+(.*?)^source_digest\s+(.*?)^reader", text, re.S | re.M)
        if not header:
            continue
        sources = [s.strip() for s in re.split(r"·", header.group(1)) if s.strip()]
        digests = [d.strip() for d in re.split(r"·", header.group(2)) if d.strip()]
        drifted = []
        for source, recorded in zip(sources, digests):
            path = root / source
            if not path.exists():
                drifted.append(f"{source} (missing)")
            elif sha256(path.read_bytes()).hexdigest()[:16] != recorded:
                drifted.append(source)
        if drifted:
            stale.append((view.name, drifted))
    return stale


def closed_unsettled(issues: dict) -> list[str]:
    """Issues closed on the coordination surface without a settled standing.

    Closing a ticket is a coordination act; settling its standing is a
    governance act. When they disagree the tree says a job is finished and
    unfinished at once, so it is reported rather than resolved here.
    """
    settled = {"WITNESSED", "RATIFIED", "DEMOTED"}
    return sorted(
        (f"#{number} {issue.get('title', '')[:52]} "
         f"(closed, standing {(issue.get('metadata') or {}).get('standing')})"
         for number, issue in issues.items()
         if issue.get("state") == "CLOSED"
         and (issue.get("metadata") or {}).get("standing") not in settled),
        key=lambda line: int(line.split()[0].lstrip("#")))


def resolve(rows: list[dict[str, str]], ready: list[dict[str, str]],
            phases: dict[str, str], roadmap_text: str, root: Path = ROOT,
            issues: dict | None = None, graded_roadmap: bool = False) -> list[str]:
    """Defects: a crosswalk row that no longer resolves, a lane a phase dropped,
    or a signpost conflict."""
    defects = []
    ready_numbers = {row["number"] for row in ready}
    for row in rows:
        if row["phase"] and row["phase"] not in phases:
            defects.append(f"crosswalk names phase {row['phase']}, absent from ROADMAP.md")
        if not row["phase"] and re.search(r"\b[FP]\d+\b", row["phase_label"]):
            # The cell names a phase and this reader cannot read it. Skipping such
            # a row let one mutation pass both this check and the lane grader at
            # once, because both resolve a phase through the same backticks.
            defects.append(
                f"crosswalk row {row['phase_label']} names a phase this reader cannot "
                "resolve; a phase token must be backticked")
        if not row["ticket"]:
            defects.append(f"crosswalk row {row['phase_label']} names no epic ticket")
        if issues is not None and row["ticket"]:
            ticket = issues.get(row["ticket"])
            if ticket is None:
                defects.append(
                    f"crosswalk row {row['phase'] or row['phase_label']} names #{row['ticket']}, "
                    "which is absent from the epic projection")
            elif ticket.get("state") == "CLOSED":
                defects.append(
                    f"crosswalk row {row['phase'] or row['phase_label']} names #{row['ticket']}, "
                    "which is closed; the row asserts an identity against dead work")
        drawn = re.search(r"`?(diagrams/[\w.-]+)`?", row["drawn"])
        if drawn and not (root / drawn.group(1)).exists():
            defects.append(f"crosswalk row {row['phase']} draws to missing {drawn.group(1)}")
    if "split `core.py`" not in roadmap_text:
        defects.append("crosswalk no longer names the ENGINEERING.md module debt")
    # The lane shape is graded for presence only. Whether a Now item can really be
    # finished with what exists is judgement over evidence, which no parser settles.
    defects.extend(str(defect) for defect in
                   roadmap_lanes.grade(roadmap_text, must_carry_phases=graded_roadmap))
    # An empty frontier is deliberately not a defect. Every open ticket being
    # held is a legitimate state, and a gate that fails on it teaches operators
    # to clear the alarm unread. It is reported under "reachable work" instead.
    del ready_numbers
    return defects


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--strict", action="store_true",
                        help="exit non-zero when a crosswalk row fails to resolve")
    parser.add_argument("--json", action="store_true", help="emit the survey as JSON")
    args = parser.parse_args(argv)

    roadmap_text = _text("ROADMAP.md")
    projection = ROOT / ".claude" / "epic" / "tree.json"
    issues = (json.loads(projection.read_bytes().decode("utf-8")).get("issues", {})
              if projection.exists() else {})

    gate = declared_gate(_text("STATUS.yaml"))
    phase_state, active_custodies = phase_position(ROOT)
    active_phase = phase_state.get("active")
    phases = roadmap_phases(roadmap_text)
    rows = crosswalk(roadmap_text)
    ready = epic_ready(issues)
    stale = stale_views(ROOT)
    unsettled = closed_unsettled(issues)
    defects = resolve(rows, ready, phases, roadmap_text, issues=issues,
                      graded_roadmap=True)

    by_ticket = {row["ticket"]: row for row in rows}
    conflict = None
    if active_phase is None and gate and ready:
        gate_phase = gate.split("_", 1)[0]
        reachable_phases = {by_ticket[r["number"]]["phase"] for r in ready
                            if r["number"] in by_ticket}
        if reachable_phases and gate_phase not in reachable_phases:
            conflict = (f"STATUS.yaml declares {gate}, but reachable work sits at "
                        f"{', '.join(sorted(p for p in reachable_phases if p))}")

    if args.json:
        print(json.dumps({"phase": phase_state, "active_phase_custodies": active_custodies,
                          "declared_gate": gate, "crosswalk": rows, "ready": ready,
                          "stale_views": [{"view": v, "drifted": d} for v, d in stale],
                          "closed_unsettled": unsettled,
                          "conflict": conflict, "defects": defects},
                         indent=2, sort_keys=True))
        return 1 if args.strict and defects else 0

    print("== phase authority ==")
    for line in phase_context.render(phase_state):
        print(f"  {line}")
    if active_phase is not None:
        print("\n== active phase custody ==")
        if active_custodies:
            for custody in active_custodies:
                print(f"  {custody.get('custody_id')}  {custody.get('terminal', custody.get('standing', '?'))}")
        else:
            print("  none — active phase has no phase-scoped custody; this is opening debt")

    print("\n== roadmap reachable work ==")
    for row in ready or []:
        alias = by_ticket.get(row["number"])
        print(f"  #{row['number']} [{row['horizon']}] {row['title']}")
        if alias:
            print(f"      phase   {alias['phase_label']}")
            print(f"      debt    {alias['debt']}")
            print(f"      drawn   {alias['drawn']}")
        else:
            print("      (no crosswalk row; this job travels under one name)")
    if not ready:
        print("  none — every open ticket is held. This is a state, not a defect.")

    print(f"\n== declared gate ==\n  STATUS.yaml  {gate or 'absent'}")
    if conflict:
        print(f"  DISAGREE: {conflict}")
        print("  Both lanes may be legitimate. Choosing between them is owner judgement.")

    if unsettled:
        print("\n== closed without a settled standing ==")
        for line in unsettled:
            print(f"  {line}")
        print("  Closing is a coordination act; settling standing is a governance act.")

    if stale:
        print("\n== stale views ==")
        for view, drifted in stale:
            print(f"  {view:30} drifted against {', '.join(drifted)}")

    if defects:
        print("\n== defects ==")
        for defect in defects:
            print(f"  {defect}")

    if defects:
        print(f"\nFAIL: {len(defects)} signpost defect(s)")
        return 1 if args.strict else 0
    if conflict:
        print("\nPASS: crosswalk and lanes resolve. A declared-gate disagreement "
              "stands; that is owner judgement, not a defect.")
        return 0
    print("\nPASS: every crosswalk row resolves, every phase carries its four "
          "lanes, and no signpost disagrees")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
