#!/usr/bin/env python3
"""Re-prove the facts that authorize a coordination write, immediately before it crosses.

``apply.py`` builds and runs the command. This module answers the separate question of
whether the world still looks the way the action claims it does. Both proofs here read
live state through ``gh`` rather than trusting the action's own payload: an event, a
survey, or a caller assertion describes a moment that has already passed, and the only
fact that authorizes a write is the one that holds when the write happens.

The two proofs are:

* ``automatic_branch_basis`` - a merged same-repository pull request whose head ref still
  points at the merged SHA, is not the default branch, and bases no open pull request.
* ``body_write_basis`` - the replacement body validates against
  ``contracts/issue-metadata.schema.json``, and the body as it stands now has been
  recorded so the write is reversible by writing it back.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
import hashlib
import json
import string
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
BODIES_BEFORE = ROOT / ".local" / "registrar" / "bodies-before"
AUTOMATIC_BRANCH_AUTHORITY = "merged-pull-request-retirement"


class CrossingRefusal(RuntimeError):
    """The write crossing declined to act and must refuse visibly."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


def _json(run: Callable[[list[str]], tuple[int, str]], command: list[str], reason: str) -> Any:
    """Run a read needed to prove an effect and decode its JSON or refuse."""
    code, output = run(command)
    if code:
        raise CrossingRefusal("AUTHORITY_PROOF_UNAVAILABLE", f"{reason}: {output[:240]}")
    try:
        return json.loads(output)
    except json.JSONDecodeError as error:
        raise CrossingRefusal("AUTHORITY_PROOF_INVALID", f"{reason}: {error}") from error


def automatic_branch_basis(action: dict[str, Any], repo: str,
                            run: Callable[[list[str]], tuple[int, str]]) -> str:
    """Re-prove the exact merged PR and unchanged ref before automatic retirement."""
    if action.get("kind") != "BRANCH_DELETE":
        raise CrossingRefusal(
            "AUTOMATION_NOT_ADMITTED", "automatic authority admits BRANCH_DELETE only"
        )
    extra = action.get("extra") or {}
    number = str(extra.get("pr_number", ""))
    head_sha = str(extra.get("head_sha", ""))
    base_ref = str(extra.get("base_ref", ""))
    branch = str(action.get("argument", ""))
    if not number.isdigit() or not base_ref:
        raise CrossingRefusal("AUTOMATION_PROOF_MALFORMED", "PR number and base ref are required")
    if len(head_sha) != 40 or any(char not in string.hexdigits for char in head_sha):
        raise CrossingRefusal("AUTOMATION_PROOF_MALFORMED", "head SHA must be a 40-digit hex SHA")

    pull = _json(run, ["gh", "api", f"repos/{repo}/pulls/{number}"], f"read PR #{number}")
    observed = {
        "merged": bool(pull.get("merged")),
        "branch": ((pull.get("head") or {}).get("ref")),
        "head_sha": ((pull.get("head") or {}).get("sha")),
        "head_repo": (((pull.get("head") or {}).get("repo") or {}).get("full_name")),
        "base_ref": ((pull.get("base") or {}).get("ref")),
    }
    expected = {
        "merged": True,
        "branch": branch,
        "head_sha": head_sha,
        "head_repo": repo,
        "base_ref": base_ref,
    }
    if observed != expected:
        raise CrossingRefusal(
            "AUTOMATION_PROOF_MISMATCH",
            f"PR #{number} no longer proves this retirement: {observed!r}",
        )

    repository = _json(run, ["gh", "api", f"repos/{repo}"], "read repository default branch")
    default_branch = repository.get("default_branch")
    if not isinstance(default_branch, str) or not default_branch:
        raise CrossingRefusal(
            "AUTHORITY_PROOF_INVALID", "repository returned no usable default branch"
        )
    if branch == default_branch:
        raise CrossingRefusal(
            "PROTECTED_BRANCH",
            f"{branch} is the repository default branch and is never automatically retired",
        )

    live_ref = _json(
        run,
        ["gh", "api", f"repos/{repo}/git/ref/heads/{branch}"],
        f"read live ref refs/heads/{branch}",
    )
    live_name = live_ref.get("ref")
    live_sha = (live_ref.get("object") or {}).get("sha")
    if live_name != f"refs/heads/{branch}" or live_sha != head_sha:
        raise CrossingRefusal(
            "BRANCH_HEAD_MOVED",
            f"refs/heads/{branch} no longer points at merged head {head_sha}; "
            f"observed {live_name!r} at {live_sha!r}",
        )

    children = _json(
        run,
        ["gh", "pr", "list", "--repo", repo, "--state", "open", "--base", branch,
         "--json", "number"],
        f"check whether {branch} is still a stack base",
    )
    if children:
        numbers = ", ".join(f"#{item['number']}" for item in children)
        raise CrossingRefusal(
            "STACK_BASE_LIVE",
            f"{branch} still bases open pull request(s) {numbers}; retarget them before retirement",
        )
    return (
        f"owner-directed automatic retirement; live PR #{number}, default-branch, "
        "head-ref, and stack proofs revalidated"
    )


def _block_validates(number: int, body: str) -> None:
    """Refuse a replacement body whose ticket block the contract does not admit.

    Proved by running the repository's own reader over a one-issue export rather than
    by re-implementing the parser here. A body write is the one coordination verb that
    authors the record every label is a projection of, so it is the one verb that could
    manufacture a ticket the schema refuses.
    """
    export = [{"number": number, "title": "", "state": "OPEN", "body": body, "labels": []}]
    with tempfile.TemporaryDirectory() as scratch:
        path = Path(scratch) / "one-issue-export.json"
        path.write_text(json.dumps(export), encoding="utf-8", newline="\n")
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "sov_ticket.py"),
             "validate", "--export", str(path)],
            capture_output=True, text=True, check=False, cwd=str(ROOT),
        )
    if result.returncode:
        detail = ((result.stdout or "") + (result.stderr or "")).strip()
        raise CrossingRefusal("BODY_BLOCK_REFUSED", f"#{number}: {detail[:300]}")


def body_write_basis(action: dict[str, Any], repo: str,
                     run: Callable[[list[str]], tuple[int, str]]) -> tuple[str, dict[str, str]]:
    """Validate the replacement body and record the one it replaces.

    Returns the authority basis and the snapshot facts for the receipt. Recording the
    prior body is what makes ``reversible_by`` true: a label is restored from the
    catalogue, and a body can only be restored from a copy of itself.
    """
    if action.get("kind") != "BODY_SET":
        raise CrossingRefusal("BODY_PROOF_NOT_ADMITTED", "body authority admits BODY_SET only")
    number = str(action.get("target", "")).lstrip("#")
    if not number.isdigit():
        raise CrossingRefusal("MALFORMED_TARGET", f"{action.get('target')!r} is not an issue")
    source = Path(str(action.get("argument", "")))
    if not source.is_file():
        raise CrossingRefusal("BODY_SOURCE_MISSING", f"{source} is not a readable body file")
    replacement = source.read_text(encoding="utf-8")
    if not replacement.strip():
        raise CrossingRefusal("BODY_SOURCE_EMPTY", f"{source} is empty; a body is never blanked")
    _block_validates(int(number), replacement)

    live = _json(
        run,
        ["gh", "issue", "view", number, "--repo", repo, "--json", "body"],
        f"read the body of #{number} before replacing it",
    )
    prior = live.get("body")
    if not isinstance(prior, str):
        raise CrossingRefusal("AUTHORITY_PROOF_INVALID", f"#{number} returned no readable body")
    BODIES_BEFORE.mkdir(parents=True, exist_ok=True)
    snapshot = BODIES_BEFORE / f"body-{number}.md"
    snapshot.write_text(prior, encoding="utf-8", newline="\n")
    return (
        "owner-directed body write under coordination.issue_metadata set_body "
        "(decisions/0067); block validated and prior body recorded",
        {
            "prior_body_snapshot": str(snapshot.relative_to(ROOT).as_posix()),
            "prior_body_digest": "sha256:" + hashlib.sha256(prior.encode("utf-8")).hexdigest(),
            "replacement_digest": "sha256:"
            + hashlib.sha256(replacement.encode("utf-8")).hexdigest(),
        },
    )
