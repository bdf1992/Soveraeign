"""One record per branch: where it lives, who holds it, and whether it can land.

Git answers each of these separately and none of them together. `git branch -vv` knows
about upstreams but not worktrees, `git worktree list` knows about trees but not merge
state, and neither knows that a live session is presently editing one of them. The ledger
joins the three, because every decision a branch manager makes needs all three at once:
retiring a branch a session is sitting on loses work, and merging one nobody has probed
turns a clean tree into a conflicted one.

Reading is free and safe. The merge probe is the expensive part and is opt-in, since it
runs a full recursive merge per branch.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import subprocess

from sovbranch import gitio
from sovsession import store, worktrees

HELD = "HELD"
MERGED = "MERGED"
ORPHANED = "ORPHANED"
CONFLICTED = "CONFLICTED"
READY = "READY"
OPEN = "OPEN"

ORDER = (HELD, CONFLICTED, ORPHANED, READY, OPEN, MERGED)
"""Display order: what needs a decision first, what is safe to forget last."""

ALWAYS_PROTECTED = ("main", "master")
"""Never retirement candidates, whatever the ledger says about containment.

A trunk branch is contained in its own remote by definition, so the containment test
that makes every other merged branch disposable marks the trunk disposable too. It is
named rather than inferred because the consequence of getting it wrong is deleting the
branch every other measurement in this file is taken against.
"""


def _occupancy(root: Path) -> dict[str, dict[str, Any]]:
    """Worktree facts keyed by branch, from the session registry's own inventory.

    Delegated rather than reimplemented: `sovsession.worktrees` already owns what a
    worktree is and which session holds it, and a second answer to that question would be
    a second authority (`AGENTS.md`, Design System of Record).
    """
    try:
        entries = worktrees.inventory(root, store.store_dir(root))
    except Exception:
        return {}
    return {entry["branch"]: entry for entry in entries if entry.get("branch")}


def _pull_requests(root: Path) -> dict[str, dict[str, Any]]:
    """Open pull requests keyed by head branch, or nothing when `gh` cannot answer.

    An unattended run carries no `gh` and no credentials, so this degrades to silence
    rather than failing the ledger.
    """
    try:
        done = subprocess.run(
            ["gh", "pr", "list", "--state", "open", "--limit", "100", "--json",
             "number,title,headRefName,baseRefName,isDraft,mergeable"],
            cwd=str(root), capture_output=True, text=True, check=False, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return {}
    if done.returncode != 0:
        return {}
    try:
        return {pr["headRefName"]: pr for pr in json.loads(done.stdout or "[]")}
    except (ValueError, KeyError, TypeError):
        return {}


def _blank(name: str) -> dict[str, Any]:
    """An empty record for one branch name."""
    return {"name": name, "local": False, "remote": None, "gone": False, "head": None,
            "subject": "", "when": 0, "ahead": 0, "behind": 0, "worktree": None,
            "session": None, "dirty": None, "temp": False, "clean": None,
            "conflicts": [], "pr": None, "disposition": OPEN, "retirable": False,
            "protected": False, "remote_ahead": 0}


def _collect(root: Path) -> dict[str, dict[str, Any]]:
    """Every branch name known locally or on origin, with its refs joined."""
    records: dict[str, dict[str, Any]] = {}
    for ref in gitio.refs(root, "refs/heads/"):
        entry = records.setdefault(ref["name"], _blank(ref["name"]))
        entry.update(local=True, head=ref["head"], subject=ref["subject"],
                     when=int(ref["when"] or 0), gone="gone" in ref["track"])
        if ref["upstream"]:
            entry["remote"] = ref["upstream"]
    for ref in gitio.refs(root, "refs/remotes/origin/"):
        name, _, short = ref["name"].partition("/")
        if not short or short == "HEAD":
            continue
        entry = records.setdefault(short, _blank(short))
        entry["remote"] = ref["name"]
        if not entry["local"]:
            entry.update(head=ref["head"], subject=ref["subject"], when=int(ref["when"] or 0))
    return records


def _judge(entry: dict[str, Any]) -> None:
    """Set the disposition and whether the branch is safe to retire, in that precedence."""
    if entry["session"]:
        entry["disposition"] = HELD
    elif entry["ahead"] == 0:
        entry["disposition"] = MERGED
    elif entry["gone"]:
        entry["disposition"] = ORPHANED
    elif entry["clean"] is False:
        entry["disposition"] = CONFLICTED
    elif entry["clean"] is True:
        entry["disposition"] = READY
    else:
        entry["disposition"] = OPEN
    entry["retirable"] = bool(
        entry["disposition"] == MERGED and entry["local"] and not entry["protected"]
        and not entry["session"] and entry["dirty"] is not True
        and entry["remote_ahead"] == 0)


def build(root: Path, base: str, probe: bool = False, prs: bool = False,
          include: list[str] | None = None) -> list[dict[str, Any]]:
    """The ledger: every branch, positioned against `base`, ordered by what needs deciding."""
    occupied, requests = _occupancy(root), (_pull_requests(root) if prs else {})
    trunk = base.rpartition("/")[2]
    records = _collect(root)
    for name, entry in records.items():
        if include and name not in include:
            continue
        ref = name if entry["local"] else entry["remote"]
        entry["ahead"], entry["behind"] = gitio.divergence(root, base, ref)
        held = occupied.get(name)
        if held:
            entry.update(worktree=held["path"], session=held.get("session"),
                         dirty=held.get("dirty"), temp=held.get("temp", False))
        entry["pr"] = requests.get(name)
        entry["protected"] = name in ALWAYS_PROTECTED or ref == base or name == trunk
        if entry["local"] and entry["remote"]:
            entry["remote_ahead"] = gitio.divergence(root, name, entry["remote"])[0]
        if probe and entry["ahead"] > 0:
            clean, _, conflicts = gitio.probe(root, base, ref)
            entry["clean"], entry["conflicts"] = clean, conflicts
        _judge(entry)
    chosen = [entry for name, entry in records.items() if not include or name in include]
    return sorted(chosen, key=lambda e: (ORDER.index(e["disposition"]), -e["when"], e["name"]))
