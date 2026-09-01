#!/usr/bin/env python3
"""Repository candidate freeze and landing gate.

The current compatibility path (`plan` / `land`) still grades a mutable working
tree and commits it immediately before merge. The candidate path is the target
model: `freeze` commits reconciled construction first, qualification observes
that immutable commit, and `land-candidate` merges the exact frozen SHA without
rewriting it.

Nothing here ratifies anything. Repository effects still require the ratified
standing grant and the evidence preconditions declared for the capability used.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sovkernel import authority  # noqa: E402
from sovland import candidates  # noqa: E402
from sovland import isolation  # noqa: E402
from sovland import ledger  # noqa: E402
from sovland import preflight  # noqa: E402
from sovland import repo  # noqa: E402
from sovland import tree  # noqa: E402
import sov_grant  # noqa: E402

ROOT = repo.ROOT
DEFAULT_TARGET = "main"


def build_request(args: argparse.Namespace, paths: list[str], checks: dict[str, str]) -> dict:
    """Assemble the legacy mutable-tree landing request."""
    observation = None
    if args.observation:
        source = Path(args.observation)
        if not source.is_absolute():
            source = ROOT / source
        observation = json.loads(source.read_text(encoding="utf-8"))
    return {
        "request_schema": "soveraeign-authority-request/v1",
        "actor_id": args.actor,
        "capability": "repository.land",
        "effect_class": "RESOURCE_CONSUMPTION",
        "at": datetime.now(timezone.utc).isoformat(),
        "branch": args.target,
        "paths": paths,
        "spend": {"unit": "agent_invocations", "amount": args.spend},
        "evidence": {"checks": checks, "observation": observation},
    }


def _report(request: dict, result: dict, branch: str, ahead: int, behind: int,
            staged: list, carried: list, reading: dict | None = None) -> None:
    print(f"branch {branch} -> {request['branch']}: {ahead} commit(s) would move, "
          f"{behind} behind")
    print(f"graded paths ({len(request['paths'])}): "
          f"{len(staged)} staged now, {len(carried)} already carried by the merge")
    for path in request["paths"]:
        print(f"  {'+' if path in set(staged) else ' '} {path}")
    checks = request["evidence"]["checks"] or {}
    print("checks: " + (", ".join(f"{k}={v}" for k, v in sorted(checks.items())) or "none run"))
    observation = request["evidence"]["observation"]
    print("observation: " + (f"{observation.get('observer_id')} -> "
                             f"{observation.get('verdict')}" if observation else "none offered"))
    for line in isolation.describe(reading) if reading else []:
        print(line)
    print(f"\n{result['verdict']}: {result['code'] or result['grant_id']}")
    print(f"  {result['detail']}")


def _evaluate(args: argparse.Namespace):
    """Assemble and grade the legacy mutable-tree landing."""
    branch = repo.current_branch()
    staged = [tree.repo_relative(p) for p in (args.path if args.path else repo.dirty_paths())]
    carried = [tree.repo_relative(p) for p in repo.carried_paths(args.target, branch)]
    graded_as = tree.fingerprint(staged)
    graded_blobs = {q: repo.worktree_blob(q) for q in staged}
    checks, reading = tree.gather_checks(args.skip_checks, set(staged) | set(carried))
    by_checks = tree.drifted(graded_as, tree.fingerprint(staged))
    request = build_request(args, sorted(set(staged) | set(carried)), checks)
    result = authority.evaluate(sov_grant.load_grants(), request)
    ahead, behind = repo._commit_span(args.target, branch)
    return (request, result, branch, ahead, behind, staged, carried, graded_as,
            graded_blobs, by_checks, reading)


def _carried_note(result: dict, carried: list) -> None:
    detail = result.get("detail") or ""
    if not any(path and path in detail for path in carried):
        return
    print("\nThat path is carried by the merge, not staged by this landing. Branch from "
          "the target and replay only the admissible commits, or present the excluded part "
          "separately for acceptance.")


def cmd_plan(args: argparse.Namespace) -> int:
    """Grade the legacy mutable-tree landing and change nothing."""
    (request, result, branch, ahead, behind, staged, carried, _graded_as,
     _graded_blobs, _by_checks, reading) = _evaluate(args)
    _report(request, result, branch, ahead, behind, staged, carried, reading)
    if result["verdict"] != authority.PERMITTED:
        _carried_note(result, carried)
    for path in tree.directory_paths(staged):
        print(f"\nNote: {path} is a directory; `land` refuses it because staging it "
              "would commit every file beneath it.")
    if not args.path:
        print("\nNo --path given, so the whole dirty tree was graded. `land` requires "
              "explicit paths.")
    held = tree._held_elsewhere(staged)
    if held:
        print("\nHeld by another live session in this shared tree:")
        for line in held:
            print(f"  {line}")
    print(ledger.record(ROOT, request, result, branch,
                        ledger.LANDED if result["verdict"] == authority.PERMITTED
                        else ledger.REFUSED_AUTHORITY, dry=True, reading=reading))
    return 0 if result["verdict"] == authority.PERMITTED else 1


def cmd_freeze(args: argparse.Namespace) -> int:
    """Commit reconciled construction and emit the exact frozen candidate record."""
    try:
        candidate, result, reading = candidates.freeze(args, sov_grant.load_grants())
    except candidates.CandidateRefused as refusal:
        print(f"REFUSED: {refusal}")
        return 2
    print(f"FROZEN {candidate['candidate_commit']} on {candidate['base_commit']}")
    print(f"tree {candidate['candidate_tree']}")
    print(f"candidate {candidate['candidate_file']}")
    for line in isolation.describe(reading) if reading else []:
        print(line)
    print(f"PERMITTED: {result['grant_id']}")
    return 0


def cmd_land_candidate(args: argparse.Namespace) -> int:
    """Land a frozen candidate without creating or rewriting the candidate commit."""
    try:
        candidate, result, merge_commit = candidates.land(args, sov_grant.load_grants())
    except (candidates.CandidateRefused, OSError, json.JSONDecodeError) as refusal:
        print(f"REFUSED: {refusal}")
        return 2
    print(f"LANDED candidate {candidate['candidate_commit']} on {candidate['target']}")
    print(f"settlement {merge_commit}")
    print(f"PERMITTED: {result['grant_id']}")
    return 0


def cmd_land(args: argparse.Namespace) -> int:
    """Compatibility landing: grade a mutable tree, commit it, and merge it."""
    outcome, code, facts = _land(args)
    if facts is not None:
        request, result, branch, merge_commit, detail, reading = facts
        print(ledger.record(ROOT, request, result, branch, outcome,
                            merge_commit=merge_commit, refusal_detail=detail,
                            reading=reading))
    return code


def _land(args: argparse.Namespace):
    if not args.path:
        print("REFUSED: land requires explicit --path arguments; this tree is shared and a "
              "blanket stage would land another participant's work under this evidence.")
        return ledger.REFUSED_PREFLIGHT, 2, None
    (request, result, branch, _ahead, behind, staged, carried, graded_as,
     graded_blobs, by_checks, reading) = _evaluate(args)
    _report(request, result, branch, _ahead, behind, staged, carried, reading)
    facts = (request, result, branch, None, None, reading)
    if result["verdict"] != authority.PERMITTED:
        _carried_note(result, carried)
        return ledger.REFUSED_AUTHORITY, 1, facts
    detail = preflight.refusal(args, staged, behind, graded_as, by_checks)
    if detail is not None:
        return (ledger.REFUSED_PREFLIGHT, 2,
                (request, result, branch, None, detail, reading))
    repo._git("add", "--", *staged)
    wrong = tree.staged_wrong(staged, graded_blobs)
    if wrong:
        repo._git("reset", "--", *staged)
        print("\nREFUSED: what git staged is not what was graded:")
        for path in wrong:
            print(f"  {path}")
        return (ledger.REFUSED_PREFLIGHT, 2,
                (request, result, branch, None,
                 "staged content that is not what was graded; the index was reset", reading))
    repo._git("commit", "-m", args.message)
    repo._git("checkout", args.target)
    try:
        repo._git("merge", "--no-ff", branch, "-m", f"merge: {args.message}")
    finally:
        repo._git("checkout", branch)
    print(f"\nLANDED on {args.target} under {result['grant_id']}")
    return (ledger.LANDED, 0,
            (request, result, branch, repo.head_commit(args.target), None, reading))


def _common(cmd: argparse.ArgumentParser, *, paths: bool = False,
            observation: bool = False) -> None:
    if paths:
        cmd.add_argument("--path", action="append", default=[],
                         help="a repository path this concern changed; repeatable")
    if observation:
        cmd.add_argument("--observation", required=True,
                         help="path to the witness observation JSON")
    else:
        cmd.add_argument("--observation", help=argparse.SUPPRESS)
    cmd.add_argument("--message", default="chore: land a witnessed change")
    cmd.add_argument("--actor", default="sov")
    cmd.add_argument("--target", default=DEFAULT_TARGET)
    cmd.add_argument("--spend", type=int, default=0)
    cmd.add_argument("--skip-checks", action="store_true")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command")

    plan = sub.add_parser("plan", help="grade the compatibility landing and change nothing")
    _common(plan, paths=True)
    land = sub.add_parser("land", help="compatibility path: grade, commit, then merge")
    _common(land, paths=True)

    freeze = sub.add_parser("freeze", help="commit reconciled construction as a frozen candidate")
    _common(freeze, paths=True)
    freeze.add_argument("--concern", help="concern id carried by the candidate record")
    freeze.add_argument("--output", help="candidate JSON path; defaults under .local/candidates")

    exact = sub.add_parser("land-candidate", help="merge an exact frozen candidate")
    _common(exact, observation=True)
    exact.add_argument("--candidate", required=True, help="frozen candidate JSON path")

    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 2
    try:
        return {
            "plan": cmd_plan,
            "freeze": cmd_freeze,
            "land": cmd_land,
            "land-candidate": cmd_land_candidate,
        }[args.command](args)
    except repo.LandingRefused as refusal:
        print(f"REFUSED: {refusal}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
