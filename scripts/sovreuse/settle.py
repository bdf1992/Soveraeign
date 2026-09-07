"""How the result settled, read for P15-Q3.1: after independent observation, against the
bytes that landed, with its temporary inventory gone and a receipt for the landing.

The landing receipt is the merge on the current first-parent line that first carried the
witnessed revision; the repository's record is git, and nothing committed records a
landing otherwise. Inventory is scoped to the result: leases on its custody, and branches
or worktrees still carrying its witnessed revision. What this host cannot see, it does not
report, and the reading says which stores it read.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any
import subprocess

from sovlease import store as lease_store
from sovsession import store as session_store

INDEPENDENT = "INDEPENDENT"
LANDED = "LANDED"
PRESENTED = "PRESENTED"


def git(repo: Path, *args: str) -> str | None:
    """Stdout of one git command under `repo`, or None when git refuses or is absent."""
    try:
        done = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                              text=True, encoding="utf-8", check=False, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def independent_observation(record: dict[str, Any] | None,
                            receipts: list[dict[str, Any]]) -> tuple[bool, str]:
    """True when the record supports `WITNESSED` and a receipt declares an independent observer.

    The relation is the receipt's own declaration, compared as a whole leading token so
    that `INDEPENDENTLY_UNCHECKED` is not read as independence (`CLAUDE.md`, trap T3).
    Whether the declaration is true is the next witness's question, not this reader's.
    """
    if record is None or record.get("standing_supported") != "WITNESSED":
        return False, "no witness record supports WITNESSED"
    independent = [r for r in receipts if r.get("exists")
                   and r.get("standing_supported") == "WITNESSED"
                   and r.get("observer_relation", "").split("_", 1)[0] == INDEPENDENT]
    if not independent:
        return False, "no receipt declares an independent observer supporting WITNESSED"
    return True, f"{len(independent)} independent receipt(s)"


def current_state(root: Path, receipts: list[dict[str, Any]],
                  result_address: str | None) -> dict[str, Any]:
    """The witnessed digests against the bytes now at each observed address.

    `covers_result` is whether any receipt observed the result's own address; a witness
    that digested everything but the program under observation settled nothing about it.
    """
    matching: set[str] = set()
    drifted: set[str] = set()
    missing: set[str] = set()
    covered = False
    for receipt in receipts:
        for address, digest in (receipt.get("observed") or {}).items():
            covered = covered or address == result_address
            path = root / address
            if not path.is_file():
                missing.add(address)
                continue
            now = "sha256:" + sha256(path.read_bytes()).hexdigest()
            (matching if now == digest else drifted).add(address)
    return {"matching": sorted(matching), "drifted": sorted(drifted),
            "missing": sorted(missing), "covers_result": covered}


def landing(repo: Path, revision: str | None) -> dict[str, Any]:
    """The commit that carried the witnessed revision onto the current first-parent line.

    That is the oldest merge on the line that descends from the revision, or the revision
    itself when it sits on the line directly. A revision the line does not carry has not
    landed here, whatever the member declares. The ancestry path is walked without
    `--first-parent`, which would drop the merge itself in git 2.43, and then intersected
    with the line.
    """
    if not revision or git(repo, "merge-base", "--is-ancestor", revision, "HEAD") is None:
        return {"commit": None, "subject": None}
    line = (git(repo, "rev-list", "--first-parent", "HEAD") or "").split()
    merges = (git(repo, "rev-list", "--merges", "--ancestry-path",
                  f"{revision}..HEAD") or "").split()
    carried = [merge for merge in merges if merge in set(line)]
    full = git(repo, "rev-parse", "--verify", f"{revision}^{{commit}}")
    commit = carried[-1] if carried else (full if full in line else None)
    if commit is None:
        return {"commit": None, "subject": None}
    return {"commit": commit, "subject": git(repo, "log", "-1", "--format=%s", commit)}


def derived_work_state(landed: dict[str, Any]) -> str:
    """What the history says the member's work state is."""
    return LANDED if landed.get("commit") else PRESENTED


def temporary_inventory(repo: Path, sessions_dir: Path | None, custody_id: str | None,
                        revision: str | None) -> list[str]:
    """What a settled run may not leave behind, scoped to this result.

    Leases are the custody's own, still held by a session that is not live. Branches and
    worktrees are those still carrying the witnessed revision other than the trunk and
    the line HEAD is on: work that landed and was not cleaned up, or never landed at all.
    A symbolic ref such as `origin/HEAD`, which git lists as the bare remote name, is not
    a branch and is skipped.
    """
    found: list[str] = []
    if sessions_dir is not None and sessions_dir.is_dir():
        live = {name for name, record in session_store.sessions(sessions_dir).items()
                if record.get("live")}
        leases = lease_store.leases(sessions_dir)
        found += [f"lease {lease_id}" for lease_id in lease_store.orphaned(sessions_dir, live)
                  if (leases[lease_id].get("concern") or {}).get("reference") == custody_id]
    if not revision:
        return found
    current = git(repo, "rev-parse", "--abbrev-ref", "HEAD") or ""
    keep = {"main", "origin/main", "origin/HEAD", current, f"origin/{current}"}
    listed = (git(repo, "branch", "-a", "--contains", revision,
                  "--format=%(refname:short)|%(symref)") or "").splitlines()
    branches = [line.split("|", 1)[0] for line in listed if line.endswith("|")]
    found += [f"branch {name}" for name in branches if name not in keep]
    for block in (git(repo, "worktree", "list", "--porcelain") or "").split("\n\n")[1:]:
        lines = block.splitlines()
        head = next((line.split(" ", 1)[1] for line in lines if line.startswith("HEAD ")), "")
        if head and git(repo, "merge-base", "--is-ancestor", revision, head) is not None:
            found.append(f"worktree {lines[0].split(' ', 1)[1]}")
    return found


def readings(root: Path, result: dict[str, Any], sessions_dir: Path | None) -> dict[str, Any]:
    """The P15-Q3.1 observation for one discovered result, with the facts behind it."""
    member = result.get("member") or {}
    receipts = result.get("receipts") or []
    revisions = [r.get("artifact_revision") for r in receipts if r.get("artifact_revision")]
    revision = revisions[-1] if revisions else None
    observed, why = independent_observation(result.get("record"), receipts)
    state = current_state(root, receipts, member.get("address"))
    landed = landing(root, revision)
    inventory = temporary_inventory(root, sessions_dir, result.get("custody_id"), revision)
    return {
        "observation": {
            "independent_observation_present": observed,
            "settled_against_current_state": (observed and state["covers_result"]
                                              and not state["drifted"] and not state["missing"]
                                              and landed["commit"] is not None),
            "temporary_inventory_remaining": inventory,
            "closure_receipt": landed["commit"],
        },
        "facts": {"independence": why, "state": state, "revision": revision,
                  "landing": landed, "work_state_declared": member.get("work_state"),
                  "work_state_derived": derived_work_state(landed)},
    }
