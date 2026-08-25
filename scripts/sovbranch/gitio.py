"""Read-only git primitives for the branch ledger, and the object-database merge probe.

Everything here answers a question; nothing here changes a ref, a working tree, or the
index. That split is the point. A branch manager that has to check a branch out in order
to say whether it merges will, sooner or later, check one out over someone's work, and
this repository has nineteen trees checked out at once.

`probe` is the reason the split holds. `git merge-tree --write-tree` performs the whole
recursive merge inside the object database and hands back either a tree or the list of
paths it could not reconcile, touching no tree on disk. `chain` then writes a throwaway
commit over that tree with `commit-tree`, so a sequence of merges can be simulated end to
end in the object database. The commits it writes are unreferenced and are collected by
the next `git gc`; no ref ever points at one.
"""

from __future__ import annotations

from pathlib import Path
import subprocess

FIELDS = ("refname:short", "objectname:short", "upstream:short", "upstream:track",
          "committerdate:unix", "contents:subject")
SEP = "\x1f"


def git(root: Path, args: list[str]) -> tuple[int, str, str]:
    """Run one git command in a tree and return its code, stdout, and stderr."""
    done = subprocess.run(["git", *args], cwd=str(root), capture_output=True,
                          text=True, check=False)
    return done.returncode, done.stdout.strip(), done.stderr.strip()


def out(root: Path, args: list[str], default: str = "") -> str:
    """Stdout of a git command, or `default` when it fails, for questions that may not apply."""
    code, stdout, _ = git(root, args)
    return stdout if code == 0 else default


def resolve(root: Path, ref: str) -> str | None:
    """The full object name of a ref, or None when the ref does not exist."""
    code, stdout, _ = git(root, ["rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"])
    return stdout or None if code == 0 else None


def default_base(root: Path) -> str:
    """The integration base: origin's default branch when known, else local main."""
    head = out(root, ["symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"])
    if head.startswith("refs/remotes/"):
        return head[len("refs/remotes/"):]
    return "origin/main" if resolve(root, "origin/main") else "main"


def refs(root: Path, pattern: str) -> list[dict[str, str]]:
    """Every ref under a pattern, with the fields the ledger reads."""
    fmt = SEP.join(f"%({field})" for field in FIELDS)
    code, stdout, _ = git(root, ["for-each-ref", f"--format={fmt}", pattern])
    if code != 0 or not stdout:
        return []
    records = []
    for line in stdout.splitlines():
        parts = line.split(SEP)
        if len(parts) != len(FIELDS):
            continue
        records.append(dict(zip(("name", "head", "upstream", "track", "when", "subject"), parts)))
    return records


def divergence(root: Path, base: str, ref: str) -> tuple[int, int]:
    """Commits `ref` holds that `base` lacks, and commits `base` holds that `ref` lacks."""
    code, stdout, _ = git(root, ["rev-list", "--left-right", "--count", f"{base}...{ref}"])
    if code != 0:
        return (0, 0)
    parts = stdout.split()
    return (int(parts[1]), int(parts[0])) if len(parts) == 2 else (0, 0)


def probe(root: Path, base: str, ref: str) -> tuple[bool, str | None, list[str]]:
    """Merge `ref` into `base` in the object database only.

    Returns whether it merged, the resulting tree when it did, and the conflicted paths
    when it did not. No working tree, index, or ref is read or written.
    """
    code, stdout, stderr = git(root, ["merge-tree", "--write-tree", "--name-only", base, ref])
    if code not in (0, 1):
        return False, None, [f"merge-tree failed: {stderr or stdout or 'unknown error'}"]
    lines = stdout.split("\n\n")[0].splitlines()
    if not lines:
        return False, None, [f"merge-tree could not merge {ref}: {stderr or stdout or 'no reason given'}"]
    tree, paths = lines[0].strip(), sorted(set(name for name in lines[1:] if name))
    return (True, tree, []) if code == 0 else (False, None, paths)


def chain(root: Path, tree: str, first: str, second: str) -> str | None:
    """Write an unreferenced commit over a probed tree, so the next probe sees this merge.

    The commit is written into the object database and pointed at by nothing, which is what
    lets a sequence be simulated without a branch, a checkout, or a reset to undo.
    """
    parents = []
    for parent in (first, second):
        name = resolve(root, parent)
        if name is None:
            return None
        parents.extend(["-p", name])
    code, stdout, _ = git(root, ["commit-tree", tree, *parents, "-m", "sov-branch merge probe"])
    return stdout.strip() if code == 0 else None
