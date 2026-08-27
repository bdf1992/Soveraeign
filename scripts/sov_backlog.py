"""Measure every branch that never reached the trunk, so a disposition can be judged.

86 commits sit on branches that were built, sometimes tested, and then left. Deciding
what to do with one needs three facts that are expensive to gather by hand and cheap to
compute: how much of it the trunk already contains, whether it still merges, and what it
touches. Gathering them by hand is what has not happened.

Every measurement here reads git directly and writes nothing. Merge trials use
``git merge-tree``, which resolves in memory and touches no index, no worktree and no
branch, so this is safe to run in a tree other sessions are working in.

Three facts per branch:

* ``already_on_trunk`` - commits whose patch the trunk already carries under a different
  hash, from ``git cherry``. A branch that is entirely this is finished work that landed
  by another route, and deleting it loses nothing.
* ``conflicts`` - paths a merge into the trunk cannot resolve on its own. Zero means the
  merge is mechanical; a number means someone must choose.
* ``touches`` - the files the branch changes relative to the trunk, which is what says
  whether two branches are about to fight.

It recommends nothing. Disposition is judgement, and this is the evidence under it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TRUNK_CANDIDATES = ("main", "origin/main")
CONFLICT_STAGES = ("1", "2", "3")


def git(*args: str) -> str:
    """Run one read-only git command and return stdout, empty on any failure."""
    result = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else ""


def git_allowing_failure(*args: str) -> tuple[int, str]:
    """Run a command whose non-zero exit is information rather than an error."""
    result = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False)
    return result.returncode, result.stdout


def trunk() -> str:
    """Name the trunk ref this checkout has, or an empty string if it has none."""
    for candidate in TRUNK_CANDIDATES:
        if git("rev-parse", "--verify", "--quiet", candidate):
            return candidate
    return ""


def candidates() -> list[str]:
    """Every branch this checkout can see: local heads, then remotes with no local head.

    Reading only ``refs/heads/`` made a branch that was pushed and never checked out
    here invisible to the survey whose whole purpose is finding unlanded work. On
    2026-08-27 that was eighteen branches carrying 88 commits, including one with an
    open pull request. A remote-tracking branch whose local counterpart exists is
    skipped, because the local head already measures that work and would otherwise be
    counted twice.
    """
    heads = [n for n in
             git("for-each-ref", "--format=%(refname:short)", "refs/heads/").splitlines() if n]
    local = set(heads)
    remotes = []
    for name in git("for-each-ref", "--format=%(refname:short)", "refs/remotes/").splitlines():
        if not name or name.endswith("/HEAD"):
            continue
        # "origin/feat/x" names the same work as a local "feat/x"; keep only the orphan.
        if name.split("/", 1)[-1] in local:
            continue
        remotes.append(name)
    return heads + remotes


def unlanded(against: str) -> list[str]:
    """List branches carrying at least one commit the trunk does not have."""
    names = []
    for name in candidates():
        if name == against:
            continue
        count = git("rev-list", "--count", f"{against}..{name}")
        if count.isdigit() and int(count) > 0:
            names.append(name)
    return names


def equivalence(against: str, name: str, ahead: int) -> tuple[int, int]:
    """Split a branch's commits into those the trunk already carries and those it does not.

    ``git cherry`` compares patches rather than hashes, so a commit that landed through a
    rebase, a squash or a cherry-pick is recognised as present. That is the difference
    between a branch that is abandoned and one whose work is simply already home.

    What it does with an equivalent commit varies: some versions mark it ``-`` and some
    omit it. Only the ``+`` lines are relied on here, and the landed count is the
    remainder against the raw commit count, which is true under either behaviour.
    """
    outstanding = len([line for line in git("cherry", against, name).splitlines()
                       if line.startswith("+")])
    return max(ahead - outstanding, 0), outstanding


def conflicts(against: str, name: str) -> list[str]:
    """Return the paths a merge into the trunk cannot resolve, resolving only in memory."""
    code, output = git_allowing_failure("merge-tree", "--write-tree", against, name)
    if code == 0:
        return []
    found = []
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) != 2:
            continue
        fields = parts[0].split(" ")
        if len(fields) == 3 and fields[2] in CONFLICT_STAGES and parts[1] not in found:
            found.append(parts[1])
    return found


def touches(against: str, name: str) -> list[str]:
    """List the files the branch changes relative to the trunk."""
    return [line for line in git("diff", "--name-only", f"{against}...{name}").splitlines()
            if line]


def measure(against: str, name: str) -> dict[str, Any]:
    """Gather every fact about one branch that a disposition needs."""
    raw = git("rev-list", "--count", f"{against}..{name}")
    ahead = int(raw) if raw.isdigit() else 0
    present, outstanding = equivalence(against, name, ahead)
    conflicted = conflicts(against, name)
    changed = touches(against, name)
    upstream = git("for-each-ref", "--format=%(upstream:short)", f"refs/heads/{name}")
    if not upstream and name.count("/") and git("rev-parse", "--verify", "--quiet",
                                                f"refs/remotes/{name}"):
        # The branch is itself a remote-tracking ref; it is its own copy on the remote.
        upstream = name
    unpushed = git("rev-list", "--count", name, "--not", "--remotes", against)
    return {
        "branch": name,
        "ahead": ahead,
        "already_on_trunk": present,
        "outstanding": outstanding,
        "conflicts": conflicted,
        "conflict_count": len(conflicted),
        "touches": changed,
        "touch_count": len(changed),
        "upstream": upstream,
        "unpushed": int(unpushed) if unpushed.isdigit() else 0,
        "last_commit": git("log", "-1", "--format=%ai", name),
        "last_subject": git("log", "-1", "--format=%s", name),
        "subjects": git("log", "--format=%s", f"{against}..{name}").splitlines()[:12],
    }


def overlaps(rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Name every file two or more unlanded branches both change.

    Two branches touching one file is the cheapest early warning that landing them in
    either order will cost a conflict the second time.
    """
    owners: dict[str, list[str]] = {}
    for row in rows:
        for path in row["touches"]:
            owners.setdefault(path, []).append(row["branch"])
    return {path: names for path, names in sorted(owners.items()) if len(names) > 1}


def survey() -> dict[str, Any]:
    """Measure every unlanded branch and return the whole reading."""
    against = trunk()
    if not against:
        return {"trunk": "", "branches": [], "shared_files": {},
                "note": "no trunk ref is present in this checkout; nothing can be measured"}
    rows = [measure(against, name) for name in unlanded(against)]
    rows.sort(key=lambda row: (-row["outstanding"], row["branch"]))
    return {"trunk": against, "branches": rows, "shared_files": overlaps(rows)}


def render(reading: dict[str, Any]) -> str:
    """Render the reading as a table a person can act on."""
    if not reading["trunk"]:
        return reading["note"]
    rows = reading["branches"]
    lines = [f"Trunk: {reading['trunk']}. {len(rows)} branch(es) carry unlanded commits.", ""]
    lines.append(f"{'branch':<42} {'out':>4} {'done':>5} {'confl':>6} {'files':>6}  last")
    for row in rows:
        lines.append(f"{row['branch']:<42} {row['outstanding']:>4} "
                     f"{row['already_on_trunk']:>5} {row['conflict_count']:>6} "
                     f"{row['touch_count']:>6}  {row['last_commit'][:10]}")
    lines.append("")
    lines.append("out = commits the trunk does not carry. done = commits already on the "
                 "trunk under another hash.")
    lines.append("confl = paths a merge cannot resolve on its own. files = files changed "
                 "against the trunk.")
    settled = [row for row in rows if row["outstanding"] == 0]
    if settled:
        lines.append("")
        lines.append(f"{len(settled)} branch(es) carry nothing the trunk lacks: "
                     + ", ".join(row["branch"] for row in settled))
    shared = reading["shared_files"]
    if shared:
        lines.append("")
        lines.append(f"{len(shared)} file(s) are changed by more than one branch. "
                     "Landing order will matter for these:")
        for path, names in list(shared.items())[:12]:
            lines.append(f"  {path}  <- {', '.join(names)}")
        if len(shared) > 12:
            lines.append(f"  and {len(shared) - 12} more")
    lines.append("")
    lines.append("This measures. It recommends nothing; disposition is judgement.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Print the survey as a table or as JSON."""
    parser = argparse.ArgumentParser(prog="sov_backlog", description="Measure unlanded work.")
    parser.add_argument("--json", action="store_true", help="emit the reading as JSON")
    parsed = parser.parse_args(argv)
    reading = survey()
    print(json.dumps(reading, indent=2) if parsed.json else render(reading))
    return 0


if __name__ == "__main__":
    sys.exit(main())
