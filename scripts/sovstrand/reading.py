"""The git readings the stranded-work grade is built on.

Every measurement here reads git at the moment it runs. None of it consults a prior
report, a session record, or a branch's own claim about being finished, because each of
those was written by the participant that walked away.
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple
import subprocess

ROOT = Path(__file__).resolve().parents[2]
TRUNK_CANDIDATES = ("main", "origin/main")
EPHEMERAL_MARKERS = ("/temp/", "/tmp/", "scratchpad", "appdata/local/temp")

AT_RISK = "AT_RISK"
UNLANDED = "UNLANDED"
EXPOSED = "EXPOSED"


class Branch(NamedTuple):
    """One local branch measured against the trunk and against every remote."""

    name: str
    ahead: int
    unreachable: int
    upstream: str
    verdict: str


class Worktree(NamedTuple):
    """One checked-out worktree and where it lives."""

    path: str
    branch: str
    ephemeral: bool


def git(*args: str) -> str:
    """Run one read-only git command from the repository root and return its stdout."""
    result = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def trunk() -> str:
    """Name the trunk ref this checkout actually has, or an empty string if it has none."""
    for candidate in TRUNK_CANDIDATES:
        if git("rev-parse", "--verify", "--quiet", candidate):
            return candidate
    return ""


def _listing() -> list[tuple[str, str]]:
    """Every branch this checkout can see, as (name, upstream) pairs.

    Local heads first, then remote-tracking refs with no local head of the same name.
    A branch that was pushed and never checked out here has no `refs/heads/` entry, so
    reading only local heads reported it as nothing at all - on 2026-08-27 that hid
    eighteen branches carrying 88 commits, one of them with an open pull request.
    A remote-tracking ref whose local counterpart exists is skipped, because the local
    head already measures that work and counting both would double it.
    """
    pairs: list[tuple[str, str]] = []
    local: set[str] = set()
    for line in git("for-each-ref", "--format=%(refname:short)%09%(upstream:short)",
                    "refs/heads/").splitlines():
        name, _, upstream = line.partition("\t")
        if name:
            local.add(name)
            pairs.append((name, upstream))
    for name in git("for-each-ref", "--format=%(refname:short)", "refs/remotes/").splitlines():
        if not name or name.endswith("/HEAD") or name.split("/", 1)[-1] in local:
            continue
        # It is its own copy on the remote, which is what an upstream records.
        pairs.append((name, name))
    return pairs


def branches(against: str) -> list[Branch]:
    """Measure every branch this checkout can see against the trunk, newest divergence first."""
    found: list[Branch] = []
    for name, upstream in _listing():
        if name == against:
            continue
        count = git("rev-list", "--count", f"{against}..{name}")
        ahead = int(count) if count.isdigit() else 0
        if ahead == 0:
            continue
        unreachable = _unreachable(against, name)
        verdict = AT_RISK if unreachable else UNLANDED
        found.append(Branch(name, ahead, unreachable, upstream, verdict))
    return sorted(found, key=lambda item: (item.verdict != AT_RISK, -item.unreachable,
                                           -item.ahead))


def _unreachable(against: str, *refs: str) -> int:
    """Count commits beyond the trunk on these refs that no remote-tracking ref reaches.

    A configured upstream is not the question. A branch may carry commits pushed under
    a different name, and a branch with an upstream set may never have been pushed at
    all. What survives losing this directory is exactly what some remote ref already
    reaches, so that is what is measured.

    The trunk is excluded as well as the remotes. An unpushed trunk is its own concern
    and would otherwise be charged to every branch built on it.
    """
    count = git("rev-list", "--count", *refs, "--not", "--remotes", against)
    return int(count) if count.isdigit() else 0


def trunk_unpushed(against: str) -> int:
    """Count trunk commits that no remote-tracking ref reaches.

    Excluded from every branch's own count so it is not charged to each of them, which
    would make one hazard look like several. Reported on its own line instead, because
    an unpushed trunk is the same loss and would otherwise go unmentioned.
    """
    count = git("rev-list", "--count", against, "--not", "--remotes")
    return int(count) if count.isdigit() else 0


def distinct(found: list[Branch], verdict: str, against: str) -> int:
    """Count commits once across branches that share history, never once per branch."""
    names = [item.name for item in found if item.verdict == verdict]
    if not names:
        return 0
    if verdict == AT_RISK:
        return _unreachable(against, *names)
    count = git("rev-list", "--count", *names, "--not", against)
    return int(count) if count.isdigit() else 0


def worktrees() -> list[Worktree]:
    """List every worktree other than the primary one, flagging ephemeral locations."""
    listing = git("worktree", "list", "--porcelain")
    found: list[Worktree] = []
    path = ""
    branch = ""
    for line in listing.splitlines() + [""]:
        if line.startswith("worktree "):
            path = line[len("worktree "):]
        elif line.startswith("branch "):
            branch = line[len("branch "):].replace("refs/heads/", "")
        elif not line and path:
            if Path(path).resolve() != ROOT:
                lowered = path.replace("\\", "/").lower()
                ephemeral = any(marker in lowered for marker in EPHEMERAL_MARKERS)
                found.append(Worktree(path, branch or "(detached)", ephemeral))
            path = ""
            branch = ""
    return found
