#!/usr/bin/env python3
"""The landing gate: the one place a witnessed change becomes a commit on main.

Every workflow in this repository ends with an uncommitted working tree and a
queue pointed at the owner. This is the step that was missing. It assembles a
landing request from the real tree, grades it through
`scripts/sov_grant.py`'s evaluator against `contracts/standing-grants.json`, and
either performs the commit and the merge or refuses with the kernel's own
refusal code and the sentence that earned it.

`plan` changes nothing and is the default: it prints the verdict, the paths, and
how many commits a merge would actually move. `land` performs it. Neither ever
stages the whole tree - paths are named explicitly, because sessions in this
repository share one working directory and a blanket stage would land another
participant's work under this one's evidence.

Nothing here ratifies anything. A landed commit is `BUILT` plus an independent
observation; standing still moves only by Bdo's acceptance.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sovkernel import authority  # noqa: E402
from sovland import ledger  # noqa: E402
from sovland import preflight  # noqa: E402
from sovland import repo  # noqa: E402
from sovland import tree  # noqa: E402
import sov_grant  # noqa: E402

#: The repository root, taken from the module that already resolves it, so the
#: ledger is written beside the tree this landing actually grades.
ROOT = repo.ROOT

DEFAULT_TARGET = "main"


def build_request(args: argparse.Namespace, paths: list[str], checks: dict[str, str]) -> dict:
    """Assemble the landing request the evaluator will grade."""
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
    # The graded set is everything that reaches the target: what this landing is
    # about to stage, plus every path the merge already carries. Grading only the
    # first is what let an excluded path onto main without ever being asked about.
    # Taken before the checks, which are what make the window twelve seconds long.
    graded_as = tree.fingerprint(staged)
    graded_blobs = {q: repo.worktree_blob(q) for q in staged}
    checks = tree.gather_checks(args.skip_checks)
    # A third reading, so drift caused by the checks themselves is named as
    # that rather than blamed on another session. verify.py contains
    # generated-artifact checks; the day one regenerates a file in the
    # landing set, every landing refuses and the reason should be findable.
    by_checks = tree.drifted(graded_as, tree.fingerprint(staged))
    request = build_request(args, sorted(set(staged) | set(carried)), checks)
    result = authority.evaluate(sov_grant.load_grants(), request)
    ahead, behind = repo._commit_span(args.target, branch)
    return (request, result, branch, ahead, behind, staged, carried, graded_as,
            graded_blobs, by_checks)


def _carried_note(result: dict, carried: list) -> None:
    """When the refusal is about a path the merge carries, say what the way out is.

    A branch that has ever committed an excluded path can never land, because the
    carried set is permanent. That is fail-closed and correct, and it is a dead
    end unless the escape is stated where the refusal is read.
    """
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
        print(f"\n"
      f"Note: {path} is a directory; `land` refuses it, because staging it "
              "would commit every file beneath it.")
    if not args.path:
        print("\nNo --path given, so the whole dirty tree was graded. `land` requires "
              "explicit paths.")
    held = tree._held_elsewhere(staged)
    if held:
        print("\nHeld by another live session in this shared tree:")
        for line in held:
            print(f"  {line}")
    # The reading a real landing would append, shown before a merge is spent on
    # it. `plan` changes nothing, so this writes nothing and says so.
    print(ledger.record(ROOT, request, result, branch,
                        ledger.LANDED if result["verdict"] == authority.PERMITTED
                        else ledger.REFUSED_AUTHORITY, dry=True))
    return 0 if result["verdict"] == authority.PERMITTED else 1


def cmd_land(args: argparse.Namespace) -> int:
    """Grade the landing, perform it if permitted, and append what it decided.

    The append is the whole reason this wrapper exists. `_land` returns the exit
    code and the terminal facts; this records them and then returns. A landing
    that printed its verdict and forgot it is what let 598 commits accumulate
    against a three-record ledger.

    `_record` never raises and never changes the exit code, so the ledger cannot
    turn a permitted landing into a refused one.
    """
    outcome, code, facts = _land(args)
    if facts is not None:
        request, result, branch, merge_commit, detail = facts
        print(ledger.record(ROOT, request, result, branch, outcome,
                            merge_commit=merge_commit, refusal_detail=detail))
    return code


def _land(args: argparse.Namespace):
    """Grade the landing and, if permitted, commit the named paths and merge.

    Returns `(outcome, exit_code, facts)`. `facts` is None only when the landing
    was refused before a request existed to record.
    """
    if not args.path:
        print("REFUSED: land requires explicit --path arguments; this tree is shared and a "
              "blanket stage would land another participant's work under this evidence.")
        return ledger.REFUSED_PREFLIGHT, 2, None
    (request, result, branch, ahead, behind, staged, carried, graded_as,
     graded_blobs, by_checks) = _evaluate(args)
    _report(request, result, branch, ahead, behind, staged, carried)
    # Authority first. A contested path used to be reported before the verdict,
    # so a landing the grant never covered came back as "held by another live
    # session" and the caller went to negotiate a collision instead of learning
    # they were not permitted. A refusal that names the wrong reason sends the
    # reader to fix the wrong thing.
    facts = (request, result, branch, None, None)
    if result["verdict"] != authority.PERMITTED:
        _carried_note(result, carried)
        return ledger.REFUSED_AUTHORITY, 1, facts
    detail = preflight.refusal(args, staged, behind, graded_as, by_checks)
    if detail is not None:
        return (ledger.REFUSED_PREFLIGHT, 2,
                (request, result, branch, None, detail))

    # Stage only what --path named. A carried path is already committed, and
    # adding one would sweep in whatever happens to be dirty there.
    repo._git("add", "--", *staged)
    wrong = tree.staged_wrong(staged, graded_blobs)
    if wrong:
        repo._git("reset", "--", *staged)
        print("\n"
      "REFUSED: what git staged is not what was graded, so the commit would "
              "not contain the content this landing carries evidence for:")
        for path in wrong:
            print(f"  {path}")
        print("The index has been reset and nothing was committed. Re-run the gate.")
        return (ledger.REFUSED_PREFLIGHT, 2,
                (request, result, branch, None,
                 "staged content that is not what was graded; the index was reset"))
    repo._git("commit", "-m", args.message)
    repo._git("checkout", args.target)
    try:
        repo._git("merge", "--no-ff", branch, "-m", f"merge: {args.message}")
    finally:
        repo._git("checkout", branch)
    print(f"\nLANDED on {args.target} under {result['grant_id']}")
    return (ledger.LANDED, 0,
            (request, result, branch, repo.head_commit(args.target), None))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command")

    for name, help_text in (("plan", "grade the landing and change nothing"),
                            ("land", "grade the landing, then commit and merge")):
        cmd = sub.add_parser(name, help=help_text)
        cmd.add_argument("--path", action="append", default=[],
                         help="a repository path this concern changed; repeatable")
        cmd.add_argument("--observation", help="path to the witness observation JSON")
        cmd.add_argument("--message", default="chore: land a witnessed change",
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
