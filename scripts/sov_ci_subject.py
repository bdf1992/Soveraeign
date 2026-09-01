#!/usr/bin/env python3
"""Emit a machine-readable receipt for the repository bytes a CI job actually ran.

`candidate` proves HEAD is the exact candidate commit, the declared target base
is already contained by that candidate, and the base..candidate construction
range is linear. `integration` proves HEAD is a two-parent composition whose
parents are exactly the declared base then candidate. The command derives
commit/tree identity from Git; workflow names and GitHub event prose are inputs
to compare, never the observation itself.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "repository-ci-evidence.json"


class SubjectRefused(RuntimeError):
    """The checkout does not have the repository identity the caller declared."""


def _git(*args: str, root: Path = ROOT) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, check=False, capture_output=True, text=True
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise SubjectRefused(detail)
    return result.stdout.strip()


def _tree(commit: str, root: Path = ROOT) -> str:
    return _git("show", "-s", "--format=%T", commit, root=root)


def load_contract(path: Path = CONTRACT) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def candidate_receipt(base: str, candidate: str, root: Path = ROOT) -> dict[str, Any]:
    head = _git("rev-parse", "HEAD", root=root)
    if head != candidate:
        raise SubjectRefused(f"CANDIDATE_HEAD_MISMATCH: expected {candidate}, observed {head}")

    merge_base = _git("merge-base", base, candidate, root=root)
    if merge_base != base:
        raise SubjectRefused(
            "CANDIDATE_BASE_NOT_RECONCILED: "
            f"target base {base} is not an ancestor of candidate {candidate}; "
            f"merge-base is {merge_base}"
        )

    merge_commits = [
        value for value in _git(
            "rev-list", "--min-parents=2", f"{base}..{candidate}", root=root
        ).splitlines() if value
    ]
    if merge_commits:
        raise SubjectRefused(
            "CANDIDATE_HISTORY_NONLINEAR: base..candidate contains merge commit(s): "
            + ", ".join(merge_commits)
        )

    candidate_tree = _tree(candidate, root)
    construction_commits = int(_git("rev-list", "--count", f"{base}..{candidate}", root=root))
    return {
        "receipt_schema": "soveraeign-repository-ci-subject/v1",
        "evidence_kind": "CANDIDATE",
        "notation": "CI(C)",
        "base_commit": base,
        "candidate_commit": candidate,
        "candidate_tree": candidate_tree,
        "observed_commit": head,
        "observed_tree": candidate_tree,
        "base_is_ancestor": True,
        "construction_history": "LINEAR",
        "construction_commits": construction_commits,
    }


def integration_receipt(base: str, candidate: str, root: Path = ROOT) -> dict[str, Any]:
    head = _git("rev-parse", "HEAD", root=root)
    parents = _git("show", "-s", "--format=%P", head, root=root).split()
    expected = [base, candidate]
    if parents != expected:
        raise SubjectRefused(
            "INTEGRATION_PARENT_MISMATCH: "
            f"expected base,candidate {expected}, observed {parents} at {head}"
        )
    candidate_merge_base = _git("merge-base", base, candidate, root=root)
    return {
        "receipt_schema": "soveraeign-repository-ci-subject/v1",
        "evidence_kind": "INTEGRATION",
        "notation": "CI(B,C)",
        "base_commit": base,
        "candidate_commit": candidate,
        "candidate_tree": _tree(candidate, root),
        "integration_commit": head,
        "integration_tree": _tree(head, root),
        "observed_parents": parents,
        "candidate_contains_current_base": candidate_merge_base == base,
        "candidate_merge_base": candidate_merge_base,
    }


def _write(receipt: dict[str, Any], output: str | None) -> None:
    rendered = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("candidate", "integration"):
        command = sub.add_parser(name)
        command.add_argument("--base", required=True, help="declared current target-base commit")
        command.add_argument("--candidate", required=True, help="declared candidate commit")
        command.add_argument("--output", help="write the receipt to this path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        load_contract()
        receipt = (
            candidate_receipt(args.base, args.candidate)
            if args.command == "candidate"
            else integration_receipt(args.base, args.candidate)
        )
    except (OSError, ValueError, SubjectRefused) as refusal:
        print(f"REFUSED: {refusal}")
        return 2
    _write(receipt, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
