"""Project the ticket set into a prioritized, takeable work queue.

The queue is a projection under ``AGENTS.md``, State and execution: it is derived
entirely from the ticket metadata and the declared policy, it is rebuildable, and it
holds no state of its own. Position in the queue is not priority authority and grants
no right to act; it reports what the declared ordering makes takeable next.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json


@dataclass(frozen=True)
class Entry:
    """One ticket's position and takeability in the projected queue."""

    issue: str
    number: int
    title: str
    kind: str
    village: str
    horizon: str
    standing: str
    blocked_by: tuple[str, ...] = ()
    unblocks: tuple[str, ...] = ()
    next_action: str = ""

    @property
    def blocked(self) -> bool:
        """Report whether an unsatisfied dependency prevents taking this ticket."""
        return bool(self.blocked_by)

    def as_dict(self) -> dict[str, Any]:
        """Return the entry as a plain mapping for JSON output."""
        return {
            "issue": self.issue,
            "number": self.number,
            "title": self.title,
            "kind": self.kind,
            "village": self.village,
            "horizon": self.horizon,
            "standing": self.standing,
            "blocked": self.blocked,
            "blocked_by": list(self.blocked_by),
            "unblocks": list(self.unblocks),
            "next_action": self.next_action,
        }


@dataclass
class Ticket:
    """A parsed ticket paired with the issue surface it came from."""

    number: int
    title: str
    state: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def ref(self) -> str:
        """Return the issue reference form used inside ticket metadata."""
        return f"#{self.number}"


def load_policy(root: Path) -> dict[str, Any]:
    """Load the declared queue ordering policy."""
    path = root / "contracts" / "ticket-queue-policy.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _satisfied(standing: str | None, state: str, policy: dict[str, Any]) -> bool:
    """Report whether a dependency ticket has advanced far enough to unblock its dependents."""
    if state.upper() == "CLOSED":
        return True
    order = policy["standing_order"]
    threshold = policy["dependency_satisfied_at_or_beyond"]
    if standing not in order:
        return False
    return order.index(standing) >= order.index(threshold)


def build(tickets: list[Ticket], policy: dict[str, Any]) -> list[Entry]:
    """Return the ordered queue projection for the open tickets in ``tickets``."""
    by_ref = {ticket.ref: ticket for ticket in tickets}
    unblocks: dict[str, list[str]] = {ticket.ref: [] for ticket in tickets}
    blocked_by: dict[str, list[str]] = {}
    for ticket in tickets:
        blockers = []
        for required in ticket.metadata.get("requires") or []:
            dependency = by_ref.get(required)
            if dependency is None:
                blockers.append(f"{required} (not in the ticket set)")
                continue
            if not _satisfied(dependency.metadata.get("standing"), dependency.state, policy):
                blockers.append(required)
                unblocks.setdefault(required, []).append(ticket.ref)
        blocked_by[ticket.ref] = blockers

    entries = []
    for ticket in tickets:
        if ticket.state.upper() == "CLOSED":
            continue
        standing = str(ticket.metadata.get("standing") or "OPEN")
        entries.append(
            Entry(
                issue=ticket.ref,
                number=ticket.number,
                title=ticket.title,
                kind=str(ticket.metadata.get("kind") or "unknown"),
                village=str(ticket.metadata.get("village") or "unassigned"),
                horizon=str(ticket.metadata.get("horizon") or "NOW"),
                standing=standing,
                blocked_by=tuple(blocked_by[ticket.ref]),
                unblocks=tuple(sorted(unblocks.get(ticket.ref, []))),
                next_action=policy["next_action"].get(standing, "no declared next action"),
            )
        )
    return sorted(entries, key=lambda entry: _sort_key(entry, policy))


def _sort_key(entry: Entry, policy: dict[str, Any]) -> tuple[Any, ...]:
    """Return the declared ordering key for one entry."""
    available = {
        "blocked": int(entry.blocked),
        "horizon_rank": policy["horizon_rank"].get(entry.horizon, 99),
        "unblocks_count_desc": -len(entry.unblocks),
        "standing_rank": policy["standing_rank"].get(entry.standing, 99),
        "kind_rank": policy["kind_rank"].get(entry.kind, 99),
        "issue_number": entry.number,
    }
    return tuple(available[name] for name in policy["order_by"])


def render(entries: list[Entry], limit: int | None = None) -> str:
    """Render the queue as a fixed-width table for a report or a terminal."""
    shown = entries[:limit] if limit else entries
    header = f"{'#':>4}  {'ISSUE':>6}  {'STANDING':<32}  {'HZN':<5}  {'BLK':<3}  TITLE"
    lines = [header, "-" * len(header)]
    for rank, entry in enumerate(shown, 1):
        flag = "yes" if entry.blocked else "-"
        lines.append(
            f"{rank:>4}  {entry.issue:>6}  {entry.standing:<32}  "
            f"{entry.horizon[:5]:<5}  {flag:<3}  {entry.title[:56]}"
        )
    takeable = sum(1 for entry in entries if not entry.blocked)
    lines.append("")
    lines.append(f"{takeable} takeable of {len(entries)} open tickets; projection only, grants nothing.")
    return "\n".join(lines)
