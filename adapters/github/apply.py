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
import subprocess
import sys

# ``adapters/`` is not an importable package, so the sibling proof module is reached the
# way ``plan.py`` reaches ``scripts/``: by path, before the import. Without this the
# crossing only imports when some other module happens to have put this directory on the
# path first, which is how it looked working while failing in isolation.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from proofs import (  # noqa: E402
    AUTOMATIC_BRANCH_AUTHORITY,
    CrossingRefusal,
    automatic_branch_basis,
    body_write_basis,
)

#: The write actions this crossing admits. An action kind absent from this table is
#: refused by name; the adapter never falls through to a generic GitHub call.
ADMITTED = (
    "LABEL_ADD", "LABEL_REMOVE", "LABEL_CREATE", "BRANCH_DELETE", "BODY_SET", "COMMENT_ADD",
)
BODY_WRITE_AUTHORITY = "owner-directed-body-write"


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
    if kind in ("BODY_SET", "COMMENT_ADD"):
        number = target.lstrip("#")
        if not number.isdigit():
            raise CrossingRefusal("MALFORMED_TARGET", f"{target!r} is not an issue reference")
        if not Path(argument).is_file():
            raise CrossingRefusal("BODY_SOURCE_MISSING", f"{argument} is not a readable file")
        # --body-file, never --body: ticket text carries backticks, braces, and newlines that
        # an argv round-trip through a shell would mangle silently.
        if kind == "COMMENT_ADD":
            # A comment appends; it never replaces the body, and the scope carries no verb
            # that removes one, so this is the one admitted write with no inverse.
            return ["gh", "issue", "comment", number, "--repo", repo, "--body-file", argument]
        return ["gh", "issue", "edit", number, "--repo", repo, "--body-file", argument]
    if argument.startswith(("refs/", "-")):
        raise CrossingRefusal("MALFORMED_TARGET", f"{argument!r} is not a plain branch name")
    return ["gh", "api", "-X", "DELETE", f"repos/{repo}/git/refs/heads/{argument}"]


def _authority(action: dict[str, Any], repo: str) -> tuple[str, dict[str, str]]:
    """Resolve the authority basis for this attempt, refusing unknown claims.

    Returns the basis and any extra facts the proof produced for the receipt.
    """
    basis = (action.get("extra") or {}).get("authority_basis")
    if basis is None:
        if action.get("kind") == "BODY_SET":
            raise CrossingRefusal(
                "AUTHORITY_BASIS_UNKNOWN",
                "a body write names its basis; it is never one of the unproved approvals",
            )
        return "one owner approval, recorded per action; the adapter holds none", {}
    if basis == AUTOMATIC_BRANCH_AUTHORITY:
        return automatic_branch_basis(action, repo, _run), {}
    if basis == BODY_WRITE_AUTHORITY:
        return body_write_basis(action, repo, _run)
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
        receipt["authority"], proved = _authority(action, repo)
        receipt.update(proved)
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
