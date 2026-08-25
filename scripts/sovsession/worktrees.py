"""Worktree inventory and creation, with a base ref that is actually usable.

The host's own worktree tool branches from `origin/<default>` by default. In
this repository that is presently 69 commits behind the branch every session is
working on and is missing whole modules, so a worktree cut from it cannot build.
`create` therefore defaults to the current HEAD and says which ref it used.

The other half is hygiene. Worktrees created under a session's scratchpad
directory outlive the session that made them and are invisible once its
transcript is gone; `inventory` marks them, and `prune` offers to remove the
ones that hold nothing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import subprocess

from sovsession import store

TEMP_MARKERS = ("/temp/", "/tmp/", "\temp\\", "/appdata/local/temp/")


def _git(root: Path, args: list[str]) -> tuple[int, str, str]:
    """Run a git command in a tree and return code, stdout, stderr."""
    result = subprocess.run(["git", *args], cwd=str(root),
                            capture_output=True, text=True, check=False)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def _porcelain(root: Path) -> list[dict[str, Any]]:
    """Parse `git worktree list --porcelain` into records."""
    code, out, err = _git(root, ["worktree", "list", "--porcelain"])
    if code != 0:
        raise store.StoreError(f"git worktree list failed: {err}")
    records, current = [], {}
    for line in out.splitlines():
        if not line.strip():
            if current:
                records.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        if key == "worktree":
            current = {"path": value.replace("\\", "/")}
        elif key == "branch":
            current["branch"] = value.replace("refs/heads/", "")
        elif key == "detached":
            current["branch"] = None
        elif key == "HEAD":
            current["head"] = value[:8]
    if current:
        records.append(current)
    return records


def _counts(root: Path, ref: str, base: str = "main") -> tuple[int, int]:
    """Commits `ref` has that `base` lacks, and the reverse."""
    code, out, _ = _git(root, ["rev-list", "--left-right", "--count", f"{base}...{ref}"])
    if code != 0:
        return (0, 0)
    parts = out.split()
    if len(parts) != 2:
        return (0, 0)
    return (int(parts[1]), int(parts[0]))


def inventory(root: Path, directory: Path, base: str = "main") -> list[dict[str, Any]]:
    """Every worktree, with its occupant, its position, and whether it is disposable.

    `base` is what each tree's position is measured against. It defaults to the local
    trunk, which in a repository whose local `main` trails origin reports every tree as
    further ahead than it is; a caller that knows the real integration base passes it.
    """
    live = {record.get("tree"): record for record in store.sessions(directory).values()
            if record.get("live")}
    results = []
    for record in _porcelain(root):
        path = record["path"]
        entry = dict(record)
        entry["exists"] = Path(path).is_dir()
        entry["temp"] = any(marker in path.lower() for marker in TEMP_MARKERS)
        occupant = live.get(path)
        entry["session"] = occupant.get("session") if occupant else None
        entry["dirty"] = None
        entry["ahead"], entry["behind"] = (0, 0)
        if entry["exists"]:
            code, out, _ = _git(Path(path), ["status", "--porcelain"])
            entry["dirty"] = bool(out) if code == 0 else None
            ref = record.get("branch") or record.get("head") or "HEAD"
            entry["ahead"], entry["behind"] = _counts(root, ref, base)
        entry["disposable"] = bool(
            entry["temp"] and not entry["session"] and entry["dirty"] is False
            and entry["ahead"] == 0)
        results.append(entry)
    return results


def create(root: Path, name: str, base: str | None = None,
           branch: str | None = None, parent: Path | None = None) -> dict[str, Any]:
    """Add a worktree beside the repository, branching from a ref that builds.

    Defaults to the current HEAD rather than `origin/main`, because a base that
    predates the work in flight is not a clean start, it is a broken one.
    """
    code, head_ref, _ = _git(root, ["rev-parse", "--abbrev-ref", "HEAD"])
    base = base or (head_ref if code == 0 and head_ref != "HEAD" else "HEAD")
    branch = branch or f"feat/{name}"
    parent = parent or root.parent
    path = parent / f"{root.name.lower()}-{name}" if parent == root.parent else parent / name
    if path.exists():
        raise store.StoreError(f"{path} already exists; pick another name")
    code, out, err = _git(root, ["worktree", "add", "-b", branch, str(path), base])
    if code != 0:
        raise store.StoreError(f"git worktree add failed: {err or out}")
    return {"path": str(path).replace("\\", "/"), "branch": branch, "base": base}


def prune(root: Path, directory: Path, dry_run: bool = True) -> list[dict[str, Any]]:
    """Remove worktrees that hold nothing: no occupant, no commits, no changes."""
    removed = []
    for entry in inventory(root, directory):
        if not entry["disposable"]:
            continue
        action = dict(entry)
        if dry_run:
            action["removed"] = False
        else:
            code, _, err = _git(root, ["worktree", "remove", entry["path"]])
            action["removed"] = code == 0
            if code != 0:
                action["error"] = err
        removed.append(action)
    if not dry_run:
        _git(root, ["worktree", "prune"])
    return removed
