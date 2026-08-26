"""Grade work that has been left lying around, and fail when any of it exists only here.

Nobody in this repository notices stranded work. A branch that was built, tested and
then never merged reads exactly like a branch someone is still using, and a branch that
was never pushed reads like both -- right up until the disk it lives on is the only copy.
Bdo has been the sole detector of this, by hand, and said plainly that he cannot be.

The check reads git directly at the moment it runs. It never consults a prior report, a
session record, or a branch's own claim about being finished, because every one of those
is written by the participant that walked away.

Two classes, deliberately graded differently:

* ``AT_RISK`` - commits not on the trunk and no upstream anywhere. Losing this directory
  loses the work outright. This is the only condition that fails the check.
* ``UNLANDED`` - commits not on the trunk, but a remote copy exists. Untidy, recoverable,
  reported and never fatal, because mid-flight work is the normal state of a branch.

A worktree parked under a temporary or scratchpad directory is reported alongside them:
the session that opened it is usually gone, and its path will not survive a reboot.
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TRUNK_CANDIDATES = ("main", "origin/main")
EPHEMERAL_MARKERS = ("/temp/", "/tmp/", "scratchpad", "appdata/local/temp")

AT_RISK = "AT_RISK"
UNLANDED = "UNLANDED"


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


def branches(against: str) -> list[Branch]:
    """Measure every local branch against the trunk, newest divergence first."""
    listing = git("for-each-ref", "--format=%(refname:short)%09%(upstream:short)",
                  "refs/heads/")
    found: list[Branch] = []
    for line in listing.splitlines():
        name, _, upstream = line.partition("\t")
        if not name or name == against:
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


def uncommitted() -> int:
    """Count paths with uncommitted changes in the primary working tree."""
    status = git("status", "--porcelain")
    return len([line for line in status.splitlines() if line.strip()])


def brief() -> str:
    """Return a short session-start reading, or an empty string when nothing is at risk.

    Session start is already crowded. This speaks only when something would be lost, and
    keeps the untidy-but-recoverable count to one line underneath it.
    """
    against = trunk()
    if not against:
        return ""
    found = branches(against)
    at_risk = [item for item in found if item.verdict == AT_RISK]
    unlanded = [item for item in found if item.verdict == UNLANDED]
    behind = trunk_unpushed(against)
    if not at_risk and not behind:
        return ""
    risked = distinct(found, AT_RISK, against) + behind
    named = ", ".join(f"{item.name} ({item.unreachable})" for item in at_risk[:4])
    if len(at_risk) > 4:
        named += f", and {len(at_risk) - 4} more"
    lines = [
        f"Stranded work: {risked} distinct commit(s) exist only on this disk, reachable "
        f"from no remote ({len(at_risk)} branch(es)"
        + (f", plus {behind} on {against}" if behind else "") + ").",
    ]
    if named:
        lines.append(f"  {named}")
    if unlanded:
        carried = distinct(found, UNLANDED, against)
        lines.append(f"  Separately, {carried} distinct commit(s) on {len(unlanded)} "
                     "branch(es) are pushed but not merged.")
    lines.append("  python scripts/sov_strand.py for the full reading.")
    return "\n".join(lines)


def report(against: str, found: list[Branch], trees: list[Worktree], dirty: int) -> int:
    """Print the graded reading and return the process exit code."""
    at_risk = [item for item in found if item.verdict == AT_RISK]
    unlanded = [item for item in found if item.verdict == UNLANDED]
    stranded = distinct(found, AT_RISK, against) + distinct(found, UNLANDED, against)
    ephemeral = [tree for tree in trees if tree.ephemeral]

    behind = trunk_unpushed(against)
    print(f"Trunk: {against}. {stranded} distinct commit(s) on {len(found)} branch(es) are "
          "not on it.")
    if behind:
        print()
        print(f"AT RISK - the trunk itself: {behind} commit(s) on {against} reach no remote.")
    if at_risk:
        print()
        print(f"AT RISK - no copy anywhere but this directory ({len(at_risk)} branch(es)):")
        for item in at_risk:
            print(f"  {item.unreachable:>4} unpushed, {item.ahead:>3} beyond trunk  "
                  f"{item.name}")
    if unlanded:
        print()
        print(f"UNLANDED - pushed, not merged ({len(unlanded)} branch(es)):")
        for item in unlanded:
            print(f"  {item.ahead:>4} commit(s)  {item.name}  -> {item.upstream}")
    if trees:
        print()
        print(f"WORKTREES - {len(trees)} open, {len(ephemeral)} in a temporary location:")
        for tree in trees:
            mark = "  [temporary]" if tree.ephemeral else ""
            print(f"  {tree.branch:<40} {tree.path}{mark}")
    if dirty:
        print()
        print(f"UNCOMMITTED - {dirty} path(s) changed in this working tree.")

    print()
    if at_risk or behind:
        risked = distinct(found, AT_RISK, against) + behind
        print(f"FAIL: {risked} distinct commit(s) across {len(at_risk)} branch(es) and the "
              f"trunk exist only in this directory. Push them, merge them, or delete them "
              "deliberately.")
        return 1
    print(f"PASS: no commit exists only in this directory. {stranded} distinct commit(s) "
          "await landing.")
    return 0


def main() -> int:
    """Grade the working area and return an exit code."""
    against = trunk()
    if not against:
        print("PASS: no trunk ref is present in this checkout, so nothing can be graded "
              "against one. This is not evidence that no work is stranded.")
        return 0
    return report(against, branches(against), worktrees(), uncommitted())


if __name__ == "__main__":
    sys.exit(main())
