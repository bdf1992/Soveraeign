"""Whether uncommitted working-tree content has a second copy, and how to give it one.

`sov_strand.py` graded branches. It counted uncommitted paths and printed the number
underneath the verdict, but the verdict never read it, so the check could print
`PASS: no commit exists only in this directory` while a hundred files existed only in
this directory and were protected by nothing.

That gap was not theoretical. On 2026-08-27 `acceptance/A11.json`, a finished
acceptance packet, was destroyed in this shared working tree with no copy anywhere.
It had never been a commit, so no branch reading could see it, before or after.

Containment here is a property of content, not of commits: working-tree bytes are
contained when the identical blob is reachable from some ref in this repository. That
is the truthful predicate rather than a conservative one -- a file whose exact content
already sits in a reachable tree is recoverable, whoever put it there -- and it is
cheap, because the answer is one reachable-object listing.

`capture` gives exposed content a holder without touching a branch, the shared index,
or any sibling session's work. It stages by explicit path into a throwaway index, so
it is never the blanket stage this repository refuses in a shared tree.
"""

from __future__ import annotations

from pathlib import Path
import os
import subprocess
import tempfile

RESCUE_PREFIX = "refs/rescue"


def _git(root: Path, *args: str, env: dict[str, str] | None = None, stdin: str = "") -> str:
    """Run one git command from `root` and return stdout, or an empty string on failure."""
    result = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=False,
        env=env, input=stdin or None)
    if result.returncode != 0:
        return ""
    return result.stdout


def exposed_paths(root: Path) -> list[str]:
    """Return every uncommitted path whose content no ref in this repository holds.

    Untracked and modified paths are read from git rather than from a directory walk, so
    everything `.gitignore` excludes is excluded here too. A path that has since been
    deleted is skipped: there is nothing left to contain.
    """
    changed = uncommitted_paths(root)
    if not changed:
        return []
    reachable = _reachable_blobs(root)
    exposed = []
    for path in changed:
        if not (root / path).is_file():
            continue
        blob = _git(root, "hash-object", "--", path).strip()
        if blob and blob not in reachable:
            exposed.append(path)
    return exposed


def uncommitted_paths(root: Path) -> list[str]:
    """Return every untracked-but-not-ignored and every modified path, sorted."""
    others = _git(root, "ls-files", "--others", "--exclude-standard").splitlines()
    modified = _git(root, "diff", "--name-only").splitlines()
    return sorted({line for line in (*others, *modified) if line.strip()})


def _reachable_blobs(root: Path) -> set[str]:
    """Return every object id reachable from any ref, including the rescue refs.

    `--all` covers `refs/heads`, `refs/remotes`, `refs/tags` and anything written under
    `refs/rescue`, so a capture taken by this module counts as containment on the next
    reading without the check needing to know it was the one that took it.
    """
    listing = _git(root, "rev-list", "--objects", "--all")
    return {line.split(" ", 1)[0] for line in listing.splitlines() if line.strip()}


def capture(root: Path, paths: list[str], ref: str, message: str) -> str:
    """Write `paths` into the object database and anchor them under `ref`.

    Returns the new commit id, or an empty string when there was nothing to capture or
    git refused. The commit belongs to no branch: it exists so the content survives
    garbage collection, and it makes no claim about the work.

    A second capture onto the same ref merges rather than replaces. Replacing looked
    correct and was not: the first run of this command dropped six paths the previous
    capture held, because the tree it wrote contained only what was exposed at that
    moment. A rescue that can un-rescue is not one. Where both trees carry a path, the
    newer bytes win, and the previous capture becomes this commit's parent so the chain
    stays readable.
    """
    rows = []
    for path in paths:
        if not (root / path).is_file():
            continue
        blob = _git(root, "hash-object", "-w", "--", path).strip()
        if blob:
            rows.append((blob, path))
    if not rows:
        return ""

    handle, index = tempfile.mkstemp(prefix="sov-rescue-", suffix=".index")
    os.close(handle)
    os.unlink(index)
    parent = _git(root, "rev-parse", "--verify", "--quiet", ref).strip()
    env = dict(os.environ, GIT_INDEX_FILE=index)
    try:
        if parent:
            _git(root, "read-tree", parent, env=env)
        args = ["update-index", "--add"]
        for blob, path in rows:
            args += ["--cacheinfo", f"100644,{blob},{path}"]
        _git(root, *args, env=env)
        tree = _git(root, "write-tree", env=env).strip()
    finally:
        Path(index).unlink(missing_ok=True)
    if not tree:
        return ""

    parents = ["-p", parent] if parent else []
    commit = _git(root, "commit-tree", tree, *parents, stdin=message).strip()
    if not commit:
        return ""
    _git(root, "update-ref", ref, commit)
    return commit


def verify(root: Path, commit: str) -> tuple[int, list[str]]:
    """Re-read every file the capture claims to hold and compare it to the live tree.

    The capture is taken from a tree several sessions write at once, so a file can change
    between being hashed and being checked. Returns the count that matched and the paths
    that did not, and never repairs the difference: a drifted path is a reading about how
    fast this tree moves, and hiding it would make the capture look cleaner than it is.
    """
    listing = _git(root, "ls-tree", "-r", commit)
    matched, drifted = 0, []
    for line in listing.splitlines():
        if "\t" not in line:
            continue
        meta, path = line.split("\t", 1)
        blob = meta.split()[2]
        live = root / path
        if not live.is_file():
            drifted.append(path)
            continue
        stored = subprocess.run(
            ["git", "cat-file", "blob", blob], cwd=root, capture_output=True, check=False)
        if stored.stdout == live.read_bytes():
            matched += 1
        else:
            drifted.append(path)
    return matched, drifted
