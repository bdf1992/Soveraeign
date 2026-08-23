#!/usr/bin/env python3
"""Capture the GitHub coordination surface as a local ticket export.

This is the only module in the repository permitted to reach GitHub. It captures and
refuses; it never decides standing, writes a label, or settles anything. Every other
check reads the export it writes and runs offline.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import argparse
import hashlib
import json
import shutil
import subprocess
import sys

ISSUE_FIELDS = "number,title,state,body,labels"
PULL_FIELDS = "number,title,state,headRefName,body,isDraft,updatedAt"
DEFAULT_LIMIT = 500


class RegistrarRefusal(RuntimeError):
    """The crossing could not be completed and must refuse visibly."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


def _run(command: list[str]) -> str:
    """Run one `gh` invocation, converting every failure into a declared refusal."""
    if shutil.which(command[0]) is None:
        raise RegistrarRefusal("REGISTRAR_UNAVAILABLE", f"{command[0]} is not on PATH")
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode:
        stderr = (result.stderr or "").strip()
        code = "REGISTRAR_UNAUTHENTICATED" if "auth" in stderr.lower() else "REGISTRAR_UNAVAILABLE"
        raise RegistrarRefusal(code, stderr or f"exit {result.returncode}")
    return result.stdout


def capture_branches(repo: str) -> list[dict[str, Any]]:
    """Capture the live branch names so a merged ref can be judged offline.

    Only the name is projected. A branch is a ref, and this crossing has no business
    reading the tree behind it.
    """
    names = _run(["gh", "api", "--paginate", f"repos/{repo}/branches", "--jq", ".[].name"])
    return [{"name": name} for name in sorted(filter(None, names.splitlines()))]


def capture(repo: str, limit: int) -> dict[str, Any]:
    """Capture issues, pull requests, and branch refs with exact provenance."""
    issues = json.loads(
        _run(["gh", "issue", "list", "--repo", repo, "--state", "all",
              "--limit", str(limit), "--json", ISSUE_FIELDS])
    )
    pulls = json.loads(
        _run(["gh", "pr", "list", "--repo", repo, "--state", "all",
              "--limit", str(limit), "--json", PULL_FIELDS])
    )
    if not issues:
        raise RegistrarRefusal("REGISTRAR_EMPTY", f"{repo} returned no issues")
    return {"issues": issues, "pulls": pulls, "branches": capture_branches(repo)}


def _digest(payload: Any) -> str:
    """Return a stable content digest for a captured payload."""
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def write_export(captured: dict[str, Any], repo: str, out: Path) -> dict[str, Any]:
    """Write the ticket export and its sibling capture receipt."""
    out.parent.mkdir(parents=True, exist_ok=True)
    issues = sorted(captured["issues"], key=lambda item: item["number"])
    out.write_text(json.dumps(issues, indent=2) + "\n", encoding="utf-8", newline="\n")
    receipt = {
        "registrar": "github-coordination/v1",
        "source_repository": repo,
        "captured_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "issue_count": len(issues),
        "pull_count": len(captured["pulls"]),
        "branch_count": len(captured.get("branches", [])),
        "export_path": out.name,
        "export_digest": _digest(issues),
        "effect_class": "RECORD_LOCAL",
        "authority": "none granted, none accepted",
        "note": "A captured board is an observation with a timestamp, not a record.",
    }
    receipt_path = out.with_name(out.stem + ".receipt.json")
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n")
    pulls_path = out.with_name(out.stem + ".pulls.json")
    pulls = sorted(captured["pulls"], key=lambda item: item["number"])
    pulls_path.write_text(json.dumps(pulls, indent=2) + "\n", encoding="utf-8", newline="\n")
    branches_path = out.with_name(out.stem + ".branches.json")
    branches = captured.get("branches", [])
    branches_path.write_text(json.dumps(branches, indent=2) + "\n", encoding="utf-8", newline="\n")
    return receipt


def main(argv: list[str] | None = None) -> int:
    """Capture the coordination surface for one repository."""
    parser = argparse.ArgumentParser(prog="github-registrar", description=__doc__)
    parser.add_argument("--repo", required=True, help="owner/name of the coordination repository")
    parser.add_argument("--out", required=True, type=Path, help="path for the ticket export")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    args = parser.parse_args(argv)
    try:
        captured = capture(args.repo, args.limit)
    except RegistrarRefusal as refusal:
        print(f"REFUSED [{refusal.code}]: {refusal.detail}", file=sys.stderr)
        return 1
    receipt = write_export(captured, args.repo, args.out)
    print(
        f"CAPTURED: {receipt['issue_count']} issues, {receipt['pull_count']} pull requests, "
        f"and {receipt['branch_count']} branches from {args.repo} at {receipt['captured_at']}"
    )
    print(f"  export  {args.out}")
    print(f"  digest  {receipt['export_digest']}")
    print("Capture is an observation. It grants no authority and settles nothing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
