"""What a campaign plan says, and whether the machine agrees with it.

A plan names lanes: a session name, the worktree it belongs in, the ref that
worktree must be sitting on, and the orders it opens with. This module reads
one, and grades each lane against what is actually on disk and actually
running. It launches nothing.

Every refusal here is a precondition the launcher could not satisfy, checked
before a process exists. Starting a lane on the wrong branch is the failure
this file is for: a witness that quietly begins on `main` reports on the wrong
bytes, and nothing downstream can tell.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
import json
import re

NAME = re.compile(r"^[a-z0-9][a-z0-9-]{1,38}[a-z0-9]$")

PLAN_UNREADABLE = "PLAN_UNREADABLE"
PLAN_INVALID = "PLAN_INVALID"
LANE_NAME_INVALID = "LANE_NAME_INVALID"
LANE_DUPLICATED = "LANE_DUPLICATED"
WORKTREE_MISSING = "WORKTREE_MISSING"
REF_MISMATCH = "REF_MISMATCH"
ORDERS_MISSING = "ORDERS_MISSING"
READ_ONLY_LANE_ON_BRANCH = "READ_ONLY_LANE_ON_BRANCH"
LANE_OCCUPIED = "LANE_OCCUPIED"

MODES = {"write", "read-only"}
READY = "READY"


class PlanError(RuntimeError):
    """A plan that cannot be read or does not describe lanes."""

    def __init__(self, refusal: str, because: str) -> None:
        super().__init__(f"{refusal}: {because}")
        self.refusal = refusal
        self.because = because


def load(path: Path) -> dict[str, Any]:
    """Read a campaign plan, refusing anything that is not one."""
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as error:
        raise PlanError(PLAN_UNREADABLE, f"{path}: {error}") from error
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as error:
        raise PlanError(PLAN_INVALID, f"{path} is not JSON: {error}") from error
    if not isinstance(parsed, dict):
        raise PlanError(PLAN_INVALID, f"{path} is not a plan object")
    if not parsed.get("campaign"):
        raise PlanError(PLAN_INVALID, f"{path} names no campaign")
    sessions = parsed.get("sessions")
    if not isinstance(sessions, list) or not sessions:
        raise PlanError(PLAN_INVALID, f"{path} declares no sessions")
    return parsed


def lanes(plan: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalise every declared lane, filling the defaults the launcher needs."""
    out: list[dict[str, Any]] = []
    for index, raw in enumerate(plan.get("sessions") or []):
        if not isinstance(raw, dict):
            raise PlanError(PLAN_INVALID, f"session {index} is not an object")
        lane = {
            "name": str(raw.get("name") or "").strip(),
            "worktree": str(raw.get("worktree") or "").strip(),
            "expected_ref": str(raw.get("expected_ref") or "").strip(),
            "mode": str(raw.get("mode") or "write").strip(),
            "model": str(raw.get("model") or "").strip(),
            "agent": str(raw.get("agent") or "").strip(),
            "orders_file": str(raw.get("orders_file") or raw.get("prompt_file") or "").strip(),
            "orders": str(raw.get("orders") or raw.get("prompt") or "").strip(),
            "remote_control": bool(raw.get("remote_control", True)),
        }
        if lane["mode"] not in MODES:
            raise PlanError(PLAN_INVALID,
                            f"session {index} mode {lane['mode']!r} is not one of "
                            + ", ".join(sorted(MODES)))
        out.append(lane)
    return out


def _ref_matches(expected: str, branch: str, sha: str) -> bool:
    """A lane's ref may be named as a branch or as a commit prefix."""
    if expected == branch:
        return True
    return bool(sha) and len(expected) >= 7 and sha.startswith(expected)


def check(lane: dict[str, Any], observe: Callable[[str], dict[str, Any]],
          live: dict[str, dict[str, Any]], seen: set[str]) -> dict[str, Any]:
    """Grade one lane against disk and registry. `READY`, or a named refusal.

    `observe` answers what a worktree path currently is; `live` is the session
    registry keyed by name; `seen` accumulates names already graded in this
    plan, because two lanes sharing a name would each register over the other.
    """
    name = lane["name"]
    if not NAME.match(name):
        return _no(name, LANE_NAME_INVALID,
                   f"{name!r} is not a lane name: lowercase, digits and dashes, 3-40 chars")
    if name in seen:
        return _no(name, LANE_DUPLICATED, f"{name} is declared twice in this plan")
    seen.add(name)

    if not lane["worktree"]:
        return _no(name, WORKTREE_MISSING, f"{name} declares no worktree")
    tree = observe(lane["worktree"])
    if not tree.get("is_worktree"):
        return _no(name, WORKTREE_MISSING,
                   f"{name}: {lane['worktree']} is not a git working tree")

    branch, sha = str(tree.get("branch") or ""), str(tree.get("sha") or "")
    if not lane["expected_ref"]:
        return _no(name, REF_MISMATCH, f"{name} declares no expected_ref; a lane names its ref")
    if not _ref_matches(lane["expected_ref"], branch, sha):
        return _no(name, REF_MISMATCH,
                   f"{name} expects {lane['expected_ref']}, tree is on "
                   f"{branch or '(detached)'} @ {sha[:7] or '?'}")

    if lane["mode"] == "read-only" and branch:
        return _no(name, READ_ONLY_LANE_ON_BRANCH,
                   f"{name} is read-only but {lane['worktree']} is on branch {branch}; "
                   "check out a detached commit so nothing it does can land")

    if lane["orders_file"]:
        orders = Path(lane["orders_file"])
        if not orders.is_absolute():
            orders = Path(lane["worktree"]) / lane["orders_file"]
        if not orders.is_file():
            return _no(name, ORDERS_MISSING, f"{name}: no orders at {orders}")
    elif not lane["orders"]:
        return _no(name, ORDERS_MISSING,
                   f"{name} carries no orders; a lane launched without them waits "
                   "for a human to paste one, which is what this refuses")

    holder = live.get(name)
    if holder and holder.get("live"):
        return _no(name, LANE_OCCUPIED,
                   f"{name} is already live (pid {holder.get('pid')}) in "
                   f"{holder.get('tree')}; end it or choose another name")

    return {"lane": name, "verdict": READY, "branch": branch, "sha": sha}


def _no(lane: str, refusal: str, because: str) -> dict[str, Any]:
    """A refusal in the shape every caller reads.

    It carries `lane` for the same reason the `READY` verdict does: a caller
    rendering a mixed batch reads one key off every entry, and a refusal that
    omitted the name crashed `--partial` instead of reporting the refusal.
    """
    return {"lane": lane, "verdict": refusal, "refusal": refusal, "because": because}
