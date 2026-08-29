#!/usr/bin/env python3
"""The landing gate: the one place an admitted BUILT change becomes durable on main.

Every workflow in this repository ends with an uncommitted working tree until a
landing operation carries it to the target. This gate assembles a request from
the real tree, grades it through `scripts/sov_grant.py`'s evaluator against
`contracts/standing-grants.json`, and either performs the commit and merge or
refuses with the kernel's own refusal code and the sentence that earned it.

`plan` changes nothing and is the default: it prints the verdict, the paths, and
how many commits a merge would actually move. `land` performs it. Neither ever
stages the whole tree - paths are named explicitly, because sessions in this
repository share one working directory and a blanket stage would land another
participant's work under this one's evidence.

Nothing here witnesses or ratifies anything. Under
`decisions/0098-milestone-witnessing.md`, ordinary landing requires the standing
grant's expected Blue checks and may leave the result at `BUILT`. Independent
witness is separately queued over named milestone targets when a later
transition consumes it.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sovkernel import authority  # noqa: E402
from sovland import repo  # noqa: E402
from sovland import tree  # noqa: E402
import sov_grant  # noqa: E402

DEFAULT_TARGET = "main"


def build_request(args: argparse.Namespace, paths: list[str], checks: dict[str, str]) -> dict:
    """Assemble the landing request the evaluator will grade.

    `--observation` remains accepted because another grant or an explicitly
    witness-gated landing may require it. The current ordinary landing grant
    does not treat an observation as a precondition for BUILT landing.
    """
    observation = None
    if args.observation:
        observation = json.loads(Path(args.observation).read_text(encoding="utf-8"))
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
            staged: list, carried: list) -> None:
    print(f"branch {branch} -> {request['branch']}: {ahead} commit(s) would move, "
          f"{behind} behind")
    print(f"graded paths ({len(request['paths'])}): "
          f"{len(staged)} staged now, {len(carried)} already carried by the merge")
    for path in request["paths"]:
        mark = "+" if path in set(staged) else " "
        print(f"  {mark} {path}")
    checks = request["evidence"]["checks"] or {}
    print("checks: " + (", ".join(f"{k}={v}" for k, v in sorted(checks.items())) or "none run"))
    observation = request["evidence"]["observation"]
    print("observation: " + (f"{observation.get('observer_id')} -> "
                             f"{observation.get('verdict')}" if observation else "none offered"))
    print(f"\n{result['verdict']}: {result['code'] or result['grant_id']}")
    print(f"  {result['detail']}")


def _evaluate(
    args: argparse.Namespace,
) -> tuple[dict, dict, str, int, int, list, list, dict, dict, list]:
    """Assemble and grade one landing, returning everything the caller reports.

    Ten positional values is past what a tuple should carry, and every round of
    this concern added one. A witness named it on 2026-08-25; it is recorded as a
    residual rather than repaired here, because restructuring the carrier at the
    end of a witnessed concern would change what was observed.
    """
    branch = repo.current_branch()
    staged = [tree.repo_relative(p) for p in (args.path if args.path else repo.dirty_paths())]
    carried = [tree.repo_relative(p) for p in repo.carried_paths(args.target, branch)]
    graded_as = tree.fingerprint(staged)
    graded_blobs = {q: repo.worktree_blob(q) for q in staged}
    checks = tree.gather_checks(args.skip_checks)
    by_checks = tree.drifted(graded_as, tree.fingerprint(staged))
    request = build_request(args, sorted(set(staged) | set(carried)), checks)
    result = authority.evaluate(sov_grant.load_grants(), request)
    ahead, behind = repo._commit_span(args.target, branch)
    return (request, result, branch, ahead, behind, staged, carried, graded_as,
            graded_blobs, by_checks)


def _carried_note(result: dict, carried: list) -> None:
    """When the refusal is about a path the merge carries, say what the way out is."""
    detail = result.get("detail") or ""
    offending = [p for p in carried if p and p in detail]
    if not offending:
        return
    print("\n"
          "That path is carried by the merge, not staged by this landing, so no "
          "change to --path will clear it. The branch has committed something the "
          "grant excludes and cannot reach the target as it stands. Branch from the "
          "target and replay only the admissible commits, or present the excluded "
          "part separately for acceptance.")


def cmd_plan(args: argparse.Namespace) -> int:
    """Grade the landing and change nothing."""
    (request, result, branch, ahead, behind, staged, carried, graded_as,
     graded_blobs, by_checks) = _evaluate(args)
    _report(request, result, branch, ahead, behind, staged, carried)
    if result["verdict"] != authority.PERMITTED:
        _carried_note(result, carried)
    for path in tree.directory_paths(staged):
        print(f"\nNote: {path} is a directory; `land` refuses it, because staging it "
              "would commit every file beneath it.")
    if not args.path:
        print("\nNo --path given, so the whole dirty tree was graded. `land` requires "
              "explicit paths.")
    held = tree._held_elsewhere(staged)
    if held:
        print("\nHeld by another live session in this shared tree:")
        for line in held:
            print(f"  {line}")
    return 0 if result["verdict"] == authority.PERMITTED else 1


def cmd_land(args: argparse.Namespace) -> int:
    """Grade the landing and, if permitted, commit the named paths and merge."""
    if not args.path:
        print("REFUSED: land requires explicit --path arguments; this tree is shared and a "
              "blanket stage would land another participant's work under this evidence.")
        return 2
    (request, result, branch, ahead, behind, staged, carried, graded_as,
     graded_blobs, by_checks) = _evaluate(args)
    _report(request, result, branch, ahead, behind, staged, carried)
    if result["verdict"] != authority.PERMITTED:
        _carried_note(result, carried)
        return 1
    directories = tree.directory_paths(staged)
    if directories:
        print("\nREFUSED: these name directories, and staging one commits every file "
              "beneath it, including files this landing never enumerated and files "
              "another session may hold:")
        for path in directories:
            print(f"  {path}")
        print("Name the files. A landing that cannot enumerate what it stages cannot "
              "honestly carry the evidence it presents.")
        return 2
    held = tree._held_elsewhere(staged)
    if held:
        print("\nREFUSED: paths held by another live session:")
        for line in held:
            print(f"  {line}")
        return 2
    if behind:
        print(f"\nREFUSED: branch is {behind} commit(s) behind {args.target}; rebase or "
              "update before merge (AGENTS.md, Branch and commit strategy).")
        return 2

    absent = tree.absent_paths(graded_as)
    if absent:
        print("\nREFUSED: these do not exist, so nothing was graded for them and "
              "`git add` would fail rather than refuse:")
        for path in absent:
            print(f"  {path}")
        return 2
    moved = tree.drifted(graded_as, tree.fingerprint(staged))
    if by_checks:
        print("\nREFUSED: running verify and lint modified these paths, so the "
              "checks changed the thing they were checking:")
        for path in by_checks:
            print(f"  {path}")
        return 2
    if moved:
        print("\nREFUSED: these changed between grading and staging, so the evidence "
              "this landing carries describes content it would not commit:")
        for path in moved:
            print(f"  {path}")
        print("Re-run the gate. Several sessions share this working directory, and "
              "`git add` stages the bytes on disk now, not the bytes that were graded.")
        return 2

    repo._git("add", "--", *staged)
    wrong = tree.staged_wrong(staged, graded_blobs)
    if wrong:
        repo._git("reset", "--", *staged)
        print("\nREFUSED: what git staged is not what was graded, so the commit would "
              "not contain the content this landing carries evidence for:")
        for path in wrong:
            print(f"  {path}")
        print("The index has been reset and nothing was committed. Re-run the gate.")
        return 2
    repo._git("commit", "-m", args.message)
    repo._git("checkout", args.target)
    try:
        repo._git("merge", "--no-ff", branch, "-m", f"merge: {args.message}")
    finally:
        repo._git("checkout", branch)
    print(f"\nLANDED BUILT on {args.target} under {result['grant_id']}")
    print("Standing note: this landing does not establish WITNESSED evidence.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command")

    for name, help_text in (("plan", "grade the landing and change nothing"),
                            ("land", "grade the landing, then commit and merge")):
        cmd = sub.add_parser(name, help=help_text)
        cmd.add_argument("--path", action="append", default=[],
                         help="a repository path this concern changed; repeatable")
        cmd.add_argument("--observation", help="optional observation evidence when the covering grant requires one")
        cmd.add_argument("--message", default="chore: land a built change",
                         help="commit message for the landing")
        cmd.add_argument("--actor", default="sov", help="the actor exercising the grant")
        cmd.add_argument("--target", default=DEFAULT_TARGET, help="the branch to land on")
        cmd.add_argument("--spend", type=int, default=0,
                         help="agent invocations this concern consumed")
        cmd.add_argument("--skip-checks", action="store_true",
                         help="do not run verify and lint; the gate then refuses on the "
                              "missing precondition, which is the point when rehearsing")

    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 2
    try:
        return {"plan": cmd_plan, "land": cmd_land}[args.command](args)
    except repo.LandingRefused as refusal:
        print(f"REFUSED: {refusal}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
