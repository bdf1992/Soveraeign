"""The two operations that change something: land a plan, and retire what has landed.

Both are deliberately narrow. Integration happens in a worktree this module creates for
the purpose, never in a tree anyone is working in, so a merge that goes wrong is thrown
away by deleting a directory rather than reset out of someone's session. Retirement
deletes local branches and local worktrees only.

Neither reaches GitHub. Pushing a branch and merging a pull request are external-world
effects that need Bdo's instruction (`AGENTS.md`, Repository protections), so `integrate`
prints the push command it would have run and stops there.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import subprocess
import sys

from sovbranch import gitio

VERIFY_TIMEOUT = 900.0


def _verify(path: Path) -> dict[str, Any]:
    """Run the repository's required verification command inside the integration tree."""
    try:
        done = subprocess.run([sys.executable, "scripts/verify.py"], cwd=str(path),
                              capture_output=True, text=True, check=False,
                              timeout=VERIFY_TIMEOUT)
    except subprocess.TimeoutExpired:
        return {"ran": True, "passed": False, "tail": "verify.py exceeded its timeout"}
    tail = "\n".join((done.stdout or done.stderr).strip().splitlines()[-12:])
    return {"ran": True, "passed": done.returncode == 0, "tail": tail}


def integrate(root: Path, base: str, steps: list[dict[str, Any]], branch: str, path: Path,
              verify: bool = True, keep_going: bool = False) -> dict[str, Any]:
    """Merge a proved sequence into a fresh integration worktree, one branch at a time.

    Stops at the first branch that conflicts or fails verification unless told to keep
    going, and never removes the tree afterwards: the failure is the evidence, and it is
    only inspectable while it is still on disk.
    """
    if gitio.resolve(root, branch) is not None:
        raise ValueError(f"branch {branch!r} already exists; pick another name")
    if path.exists():
        raise ValueError(f"{path} already exists; pick another path")
    code, out, err = gitio.git(root, ["worktree", "add", "-b", branch, str(path), base])
    if code != 0:
        raise RuntimeError(f"could not create the integration worktree: {err or out}")
    record: dict[str, Any] = {"branch": branch, "path": str(path).replace("\\", "/"),
                              "base": base, "merged": [], "failed": None, "verify": None}
    for step in steps:
        outcome = _merge_one(root, path, step, verify)
        if outcome["ok"]:
            record["merged"].append(outcome)
            continue
        record["failed"] = outcome
        if not keep_going:
            break
    record["verify"] = _verify(path) if verify and record["failed"] is None else record["verify"]
    record["push"] = f"git -C {record['path']} push -u origin {branch}"
    return record


def _merge_one(root: Path, path: Path, step: dict[str, Any], verify: bool) -> dict[str, Any]:
    """Merge one branch into the integration tree and, when asked, verify the result."""
    ref = step["ref"]
    message = f"Merge {ref} into the integration branch"
    code, out, err = gitio.git(path, ["merge", "--no-ff", "--no-edit", "-m", message, ref])
    if code != 0:
        gitio.git(path, ["merge", "--abort"])
        return {"ok": False, "name": step["name"], "ref": ref, "reason": "conflict",
                "detail": (err or out).splitlines()[-6:]}
    result = {"ok": True, "name": step["name"], "ref": ref,
              "head": gitio.out(path, ["rev-parse", "--short", "HEAD"])}
    if verify:
        checked = _verify(path)
        result["verify"] = checked
        if not checked["passed"]:
            return {"ok": False, "name": step["name"], "ref": ref, "reason": "verify",
                    "detail": checked["tail"].splitlines()[-6:], "head": result["head"]}
    return result


def retire(root: Path, entries: list[dict[str, Any]], dry_run: bool = True) -> list[dict[str, Any]]:
    """Delete local branches whose commits the base already holds, and their worktrees.

    `git branch -d` is tried first so git applies its own containment check. It measures
    containment against HEAD, not against the base this ledger was built for, so when it
    refuses a branch the ledger proved is contained the forced delete is used instead and
    the record says which of the two ran.
    """
    actions = []
    for entry in entries:
        if not entry.get("retirable"):
            continue
        action = {"name": entry["name"], "worktree": entry.get("worktree"),
                  "removed_worktree": False, "deleted": False, "forced": False}
        if dry_run:
            actions.append(action)
            continue
        if entry.get("worktree"):
            code, _, _ = gitio.git(root, ["worktree", "remove", entry["worktree"]])
            action["removed_worktree"] = code == 0
            if code != 0:
                action["error"] = "worktree still in use; branch left alone"
                actions.append(action)
                continue
        code, _, err = gitio.git(root, ["branch", "-d", entry["name"]])
        if code != 0 and entry.get("ahead") == 0:
            code, _, err = gitio.git(root, ["branch", "-D", entry["name"]])
            action["forced"] = code == 0
        action["deleted"] = code == 0
        if code != 0:
            action["error"] = err
        actions.append(action)
    if not dry_run and actions:
        gitio.git(root, ["worktree", "prune"])
    return actions
