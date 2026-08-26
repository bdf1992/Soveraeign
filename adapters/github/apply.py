#!/usr/bin/env python3
"""Execute admitted coordination writes against GitHub.

This is the only module in the repository permitted to *write* to GitHub, and it is
deliberately self-contained: the crossing that holds write authority should be readable
in one file without following an import into shared plumbing. Its sibling ``export.py``
holds the general board read crossing and neither calls the other.

Every write here is ``EXTERNAL_WORLD``. Labels still require explicit per-action owner
approval. Branch deletion additionally admits one narrow automatic authority basis:
GitHub reports that the same-repository pull request for that exact head SHA is merged,
the live branch ref still points at that exact SHA, the ref is not the repository default
branch, and no open pull request still uses it as its base. The crossing re-reads those
facts immediately before deleting the ref; an event payload or caller assertion alone is
never enough.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import argparse
import json
import shutil
import string
import subprocess
import sys

#: The write actions this crossing admits. An action kind absent from this table is
#: refused by name; the adapter never falls through to a generic GitHub call.
ADMITTED = ("LABEL_ADD", "LABEL_REMOVE", "LABEL_CREATE", "BRANCH_DELETE")
AUTOMATIC_BRANCH_AUTHORITY = "merged-pull-request-retirement"


class CrossingRefusal(RuntimeError):
    """The write crossing declined to act and must refuse visibly."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


def _now() -> str:
    """Return the current instant in the receipt's timestamp format."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _run(command: list[str]) -> tuple[int, str]:
    """Run one ``gh`` invocation, returning its exit code and combined output."""
    if shutil.which(command[0]) is None:
        raise CrossingRefusal("CROSSING_UNAVAILABLE", f"{command[0]} is not on PATH")
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    output = ((result.stdout or "") + (result.stderr or "")).strip()
    return result.returncode, output


def _json(command: list[str], reason: str) -> Any:
    """Run a read needed to prove an effect and decode its JSON or refuse."""
    code, output = _run(command)
    if code:
        raise CrossingRefusal("AUTHORITY_PROOF_UNAVAILABLE", f"{reason}: {output[:240]}")
    try:
        return json.loads(output)
    except json.JSONDecodeError as error:
        raise CrossingRefusal("AUTHORITY_PROOF_INVALID", f"{reason}: {error}") from error


def plan(action: dict[str, Any], repo: str) -> list[str]:
    """Return the exact command one admitted action would run."""
    kind = action["kind"]
    if kind not in ADMITTED:
        raise CrossingRefusal("ACTION_NOT_ADMITTED", f"{kind} is not a declared write action")
    target, argument = action["target"], action["argument"]
    if kind == "LABEL_CREATE":
        extra = action.get("extra") or {}
        if not extra.get("color"):
            raise CrossingRefusal(
                "MALFORMED_TARGET", f"{argument!r} carries no colour to create it with"
            )
        return [
            "gh", "label", "create", argument, "--repo", repo,
            "--color", extra["color"], "--description", extra.get("description", ""),
        ]
    if kind in ("LABEL_ADD", "LABEL_REMOVE"):
        number = target.lstrip("#")
        if not number.isdigit():
            raise CrossingRefusal("MALFORMED_TARGET", f"{target!r} is not an issue reference")
        flag = "--add-label" if kind == "LABEL_ADD" else "--remove-label"
        return ["gh", "issue", "edit", number, "--repo", repo, flag, argument]
    if argument.startswith(("refs/", "-")):
        raise CrossingRefusal("MALFORMED_TARGET", f"{argument!r} is not a plain branch name")
    return ["gh", "api", "-X", "DELETE", f"repos/{repo}/git/refs/heads/{argument}"]


def _automatic_branch_basis(action: dict[str, Any], repo: str) -> str:
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

    pull = _json(["gh", "api", f"repos/{repo}/pulls/{number}"], f"read PR #{number}")
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

    repository = _json(["gh", "api", f"repos/{repo}"], "read repository default branch")
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


def _authority(action: dict[str, Any], repo: str) -> str:
    """Resolve the authority basis for this attempt, refusing unknown automation claims."""
    basis = (action.get("extra") or {}).get("authority_basis")
    if basis is None:
        return "one owner approval, recorded per action; the adapter holds none"
    if basis == AUTOMATIC_BRANCH_AUTHORITY:
        return _automatic_branch_basis(action, repo)
    raise CrossingRefusal("AUTHORITY_BASIS_UNKNOWN", f"unrecognized authority basis {basis!r}")


def execute(action: dict[str, Any], repo: str, dry_run: bool) -> dict[str, Any]:
    """Attempt one action and return its receipt, whether it succeeded or failed."""
    receipt: dict[str, Any] = {
        "crossing": "github-coordination-write/v1",
        "action_id": action["id"],
        "kind": action["kind"],
        "target": action["target"],
        "argument": action["argument"],
        "effect_class": "EXTERNAL_WORLD",
        "attempted_at": _now(),
    }
    try:
        receipt["authority"] = _authority(action, repo)
        command = plan(action, repo)
    except CrossingRefusal as refusal:
        receipt.update(outcome="REFUSED", reason_code=refusal.code, detail=refusal.detail)
        return receipt
    receipt["command"] = " ".join(command)
    if dry_run:
        receipt.update(outcome="PLANNED", detail="dry run; nothing crossed the boundary")
        return receipt
    try:
        code, output = _run(command)
    except CrossingRefusal as refusal:
        receipt.update(outcome="REFUSED", reason_code=refusal.code, detail=refusal.detail)
        return receipt
    receipt["detail"] = output[:400]
    receipt["outcome"] = "APPLIED" if code == 0 else "FAILED"
    if code:
        receipt["reason_code"] = "CROSSING_REJECTED"
    return receipt


def apply_all(actions: list[dict[str, Any]], repo: str, dry_run: bool) -> list[dict[str, Any]]:
    """Execute an admitted action list in order, never stopping at the first failure."""
    if not actions:
        raise CrossingRefusal("NO_APPROVAL", "no approved or automatically proved actions were supplied")
    return [execute(action, repo, dry_run) for action in actions]


def main(argv: list[str] | None = None) -> int:
    """Apply an action list supplied as JSON."""
    parser = argparse.ArgumentParser(prog="github-write-crossing", description=__doc__)
    parser.add_argument("--repo", required=True, help="owner/name of the coordination repository")
    parser.add_argument("--actions", required=True, type=Path, help="admitted action list as JSON")
    parser.add_argument("--receipts", type=Path, help="path for the receipt list")
    parser.add_argument("--dry-run", action="store_true", help="print the exact commands only")
    args = parser.parse_args(argv)
    actions = json.loads(args.actions.read_text(encoding="utf-8"))
    try:
        receipts = apply_all(actions, args.repo, args.dry_run)
    except CrossingRefusal as refusal:
        print(f"REFUSED [{refusal.code}]: {refusal.detail}", file=sys.stderr)
        return 1
    for receipt in receipts:
        print(f"{receipt['outcome']:8} {receipt['kind']:14} {receipt['target']:8} {receipt['argument']}")
        if receipt["outcome"] in ("FAILED", "REFUSED"):
            print(f"         {receipt.get('reason_code', '')}: {receipt.get('detail', '')}")
    if args.receipts:
        args.receipts.parent.mkdir(parents=True, exist_ok=True)
        args.receipts.write_text(
            json.dumps(receipts, indent=2) + "\n", encoding="utf-8", newline="\n"
        )
        print(f"  receipts {args.receipts}")
    failed = sum(1 for receipt in receipts if receipt["outcome"] in ("FAILED", "REFUSED"))
    planned = sum(1 for receipt in receipts if receipt["outcome"] == "PLANNED")
    verb = "planned" if planned else "applied"
    print(
        f"{len(receipts) - failed} {verb}, {failed} refused or failed. "
        + ("Nothing crossed the boundary." if planned else "A receipt records an effect, not a standing.")
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
