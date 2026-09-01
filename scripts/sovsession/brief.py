"""The briefing a starting session reads before it touches anything.

A message reaches only the sessions that already exist. On 2026-08-23 a freeze
announced to five sessions was broken by three more that started afterwards and
had never heard of it. A briefing printed at SessionStart is the only channel
that reaches a session which does not exist yet, so this is where the standing
facts about the other occupants of this repository belong.

Cheap by construction: it lands in every session's context, so it is capped and
says nothing when there is nothing to say.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import subprocess

from sovsession import claims, concerns, guard, phase_context, principals, store

NEWLINE = chr(10)

MAX_PATHS = 8
MAX_PEERS = 10


def branch_of(tree: Path) -> str:
    """The branch checked out in a tree, or a short detached head."""
    result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=str(tree),
                            capture_output=True, text=True, check=False)
    name = result.stdout.strip()
    return name if name and name != "HEAD" else "(detached)"


def _position(root: Path, branch: str) -> str:
    """How this branch stands against main, in one clause."""
    result = subprocess.run(
        ["git", "rev-list", "--left-right", "--count", f"main...{branch}"],
        cwd=str(root), capture_output=True, text=True, check=False)
    parts = result.stdout.split()
    if result.returncode != 0 or len(parts) != 2:
        return ""
    behind, ahead = int(parts[0]), int(parts[1])
    if not ahead and not behind:
        return "level with main"
    return f"{ahead} ahead of main, {behind} behind"


def collect(root: Path, directory: Path, session: str, tree: str) -> dict[str, Any]:
    """Gather everything the briefing reports, as data."""
    sessions = store.sessions(directory)
    own = sessions.get(session, {})
    live = [record for record in sessions.values()
            if record.get("live") and record.get("session") != session]
    holders = claims.held(directory)
    foreign = {path: [h for h in owners if h.get("session") != session]
               for path, owners in holders.items()}
    foreign = {path: owners for path, owners in foreign.items() if owners}
    branch = branch_of(Path(tree))
    return {
        "session": session,
        "intent": own.get("intent", ""),
        "concern": own.get("concern") or concerns.resolve(None, session)[0],
        "concern_binding_source": own.get("concern_binding_source", "SESSION_FALLBACK"),
        "source_session": own.get("source_session", ""),
        "source_refs": own.get("source_refs", []),
        "queue_refs": own.get("queue_refs", []),
        "skills": concerns.available_skills(root),
        "concern_routes": concerns.routes(directory),
        "tree": tree,
        "branch": branch,
        "position": _position(root, branch),
        "shared_tree": guard.tree_peers(directory, session, tree),
        "peers": sorted(live, key=lambda item: str(item.get("session", ""))),
        "held": foreign,
        "next_decision": claims.next_decision_number(root, directory),
        "principal": principals.resolve(root, session),
        "phase": phase_context.collect(root),
    }


def _discovery(lines: list[str]) -> None:
    """Point a participant from presence into the node's existing discovery path.

    The session registry owns presence and collision avoidance, not product capability.
    The next question therefore crosses to the derived Node Interface rather than
    growing another operation list here. Governance stays behind the operation that
    needs it: discover first, then read the owning contract for the thing being changed.
    """
    lines.append("  discover what this node exposes: python scripts/sov_interface.py show")
    lines.append("  then load the owning contract for the operation or constraint you touch")


def _work_context(lines: list[str], data: dict[str, Any]) -> None:
    """Show attribution/routing without confusing it with authority."""
    concern = data.get("concern") or "concern:session/" + str(data.get("session") or "unbound")
    binding = data.get("concern_binding_source") or "SESSION_FALLBACK"
    lines.append(f"  concern: {concern} ({binding}; attribution/routing only)")
    if data.get("source_session"):
        lines.append(f"  source session: {data['source_session']}")
    if data.get("queue_refs"):
        lines.append("  available queues: " + ", ".join(data["queue_refs"][:6]))
    if data.get("source_refs"):
        lines.append("  sources: " + ", ".join(data["source_refs"][:6]))
    lines.append(f"  discoverable skills: {len(data.get('skills') or [])} under .claude/skills/")


def _phase(lines: list[str], data: dict[str, Any]) -> None:
    """Show the reconciled phase reading without turning the briefing into authority."""
    for line in phase_context.render(data):
        lines.append("  " + line)


def render(data: dict[str, Any]) -> str:
    """Render the briefing for a human or a model reading it as context."""
    peers = data["peers"]
    identity = principals.render(data["principal"])
    if not peers and not data["held"]:
        lines = [f"Session registry: you are the only live session. "
                 f"{data['branch']}, {data['position']}.", f"  {identity}"]
        lines.append(f"  intent: {data['intent'] or '(not registered)'}")
        _work_context(lines, data)
        _phase(lines, data["phase"])
        _discovery(lines)
        return NEWLINE.join(lines)
    lines = [f"Session registry - {len(peers)} other live session"
             f"{'' if len(peers) == 1 else 's'} in this repository."]
    lines.append(f"  you: {data['session']} in {data['tree']} "
                 f"on {data['branch']}, {data['position']}")
    lines.append(f"  {identity}")
    lines.append(f"  intent: {data['intent'] or '(not registered)'}")
    _work_context(lines, data)
    _phase(lines, data["phase"])
    if data["shared_tree"]:
        shared = data["shared_tree"]
        names = ", ".join(str(p.get("session")) for p in shared)
        verb = "shares" if len(shared) == 1 else "share"
        lines.append(f"  WARNING: {names} {verb} this exact working tree. "
                     f"Blanket staging (git add -A, git commit -a) is refused here; "
                     f"stage explicit paths, or take your own worktree.")
    for peer in peers[:MAX_PEERS]:
        lines.append(f"  {peer.get('session')}: {peer.get('tree', '?')} "
                     f"on {peer.get('branch', '?')}")
    if data["held"]:
        lines.append(f"  paths held by other live sessions "
                     f"({len(data['held'])} total, showing {MAX_PATHS}):")
        for path in sorted(data["held"])[:MAX_PATHS]:
            owners = ", ".join(str(o.get("session")) for o in data["held"][path])
            lines.append(f"    {path} - {owners}")
    lines.append(f"  next free decision number: {data['next_decision']:04d} "
                 f"(reserve it: python scripts/sov_session.py reserve-decision <slug>)")
    lines.append("  who holds a path: python scripts/sov_session.py who <path>")
    _discovery(lines)
    return "\n".join(lines)

def render_console(data: dict[str, Any]) -> str:
    """Detailed local work projection: concern, sources, queues, skills, crossings."""
    lines = [render(data), "", "Work console (projection; grants no authority)"]
    lines.append("  concern: " + str(data.get("concern") or ""))
    lines.append("  source session: " + str(data.get("source_session") or "(none)"))
    lines.append("  sources: " + (", ".join(data.get("source_refs") or []) or "(none)"))
    lines.append("  queues: " + (", ".join(data.get("queue_refs") or []) or "(none)"))
    lines.append("  skills: " + (", ".join(data.get("skills") or []) or "(none)"))
    concern = data.get("concern")
    related = [route for route in data.get("concern_routes") or []
               if concern in (route.get("source_concern"), route.get("destination_concern"))]
    lines.append(f"  concern routes: {len(related)}")
    for route in related[-8:]:
        lines.append("    " + str(route.get("route_id")) + ": "
                     + str(route.get("source_concern")) + " -> "
                     + str(route.get("destination_concern")) + " ["
                     + str(route.get("disposition")) + "]")
    lines.append("  route cross-concern work: python scripts/sov_session.py route --to <concern> --source <address>")
    return "\n".join(lines)
