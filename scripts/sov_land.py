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
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sovkernel import authority  # noqa: E402
import sov_grant  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGET = "main"


def _git(*argv: str) -> str:
    """Run one git command in the repository root and return its stdout."""
    done = subprocess.run(["git", *argv], cwd=ROOT, capture_output=True, text=True)
    if done.returncode != 0:
        raise RuntimeError(f"git {' '.join(argv)} failed: {done.stderr.strip()}")
    return done.stdout


def current_branch() -> str:
    return _git("rev-parse", "--abbrev-ref", "HEAD").strip()


def dirty_paths() -> list[str]:
    """Every path git reports as changed, in porcelain order."""
    lines = [line for line in _git("status", "--porcelain").splitlines() if line.strip()]
    return [line[3:].strip().strip('"').split(" -> ")[-1] for line in lines]


def _run_check(name: str, argv: list[str]) -> str:
    """Run one repository check and reduce it to PASS or FAIL."""
    done = subprocess.run([sys.executable, *argv], cwd=ROOT, capture_output=True, text=True)
    return "PASS" if done.returncode == 0 else "FAIL"


def gather_checks(skip: bool) -> dict[str, str]:
    """Run the checks the grant names as preconditions."""
    if skip:
        return {}
    return {
        "lint": _run_check("lint", ["scripts/lint.py"]),
        "verify": _run_check("verify", ["scripts/verify.py"]),
    }


def _commit_span(target: str, branch: str) -> tuple[int, int]:
    """How many commits the branch is ahead of and behind the target."""
    counts = _git("rev-list", "--left-right", "--count", f"{target}...{branch}").split()
    return int(counts[1]), int(counts[0])


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


def _held_elsewhere(paths: list[str]) -> list[str]:
    """Of the paths being landed, the ones another live session is holding.

    `sov_session.py contested` already answers this and already excludes the
    asking session, so the gate asks it rather than re-deriving who is who.
    """
    done = subprocess.run([sys.executable, "scripts/sov_session.py", "contested", "--json"],
                          cwd=ROOT, capture_output=True, text=True)
    if done.returncode != 0:
        return [f"could not read contested paths: {done.stderr.strip()}"]
    try:
        contested = json.loads(done.stdout or "[]")
    except json.JSONDecodeError:
        return ["could not parse the contested-path report"]
    wanted = {authority._normalise(p) for p in paths}
    held = []
    for entry in contested:
        path = entry.get("path") if isinstance(entry, dict) else str(entry)
        if authority._normalise(path or "") in wanted:
            holder = entry.get("holder", "another session") if isinstance(entry, dict) else "?"
            held.append(f"{path}: held by {holder}")
    return held


def _report(request: dict, result: dict, branch: str, ahead: int, behind: int) -> None:
    print(f"branch {branch} -> {request['branch']}: {ahead} commit(s) would move, "
          f"{behind} behind")
    print(f"paths ({len(request['paths'])}):")
    for path in request["paths"]:
        print(f"  {path}")
    checks = request["evidence"]["checks"] or {}
    print("checks: " + (", ".join(f"{k}={v}" for k, v in sorted(checks.items())) or "none run"))
    observation = request["evidence"]["observation"]
    print("observation: " + (f"{observation.get('observer_id')} -> "
                             f"{observation.get('verdict')}" if observation else "none offered"))
    print(f"\n{result['verdict']}: {result['code'] or result['grant_id']}")
    print(f"  {result['detail']}")


def _evaluate(args: argparse.Namespace) -> tuple[dict, dict, str, int, int]:
    """Assemble and grade one landing, returning everything the caller reports."""
    branch = current_branch()
    paths = list(args.path) if args.path else dirty_paths()
    checks = gather_checks(args.skip_checks)
    request = build_request(args, paths, checks)
    result = authority.evaluate(sov_grant.load_grants(), request)
    ahead, behind = _commit_span(args.target, branch)
    return request, result, branch, ahead, behind


def cmd_plan(args: argparse.Namespace) -> int:
    """Grade the landing and change nothing."""
    request, result, branch, ahead, behind = _evaluate(args)
    _report(request, result, branch, ahead, behind)
    if not args.path:
        print("\nNo --path given, so the whole dirty tree was graded. `land` requires "
              "explicit paths.")
    held = _held_elsewhere(request["paths"])
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
    request, result, branch, ahead, behind = _evaluate(args)
    _report(request, result, branch, ahead, behind)
    held = _held_elsewhere(request["paths"])
    if held:
        print("\nREFUSED: paths held by another live session:")
        for line in held:
            print(f"  {line}")
        return 2
    if result["verdict"] != authority.PERMITTED:
        return 1
    if behind:
        print(f"\nREFUSED: branch is {behind} commit(s) behind {args.target}; rebase or "
              "update before merge (AGENTS.md, Branch and commit strategy).")
        return 2

    _git("add", "--", *request["paths"])
    _git("commit", "-m", args.message)
    _git("checkout", args.target)
    try:
        _git("merge", "--no-ff", branch, "-m", f"merge: {args.message}")
    finally:
        _git("checkout", branch)
    print(f"\nLANDED on {args.target} under {result['grant_id']}")
    return 0


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
    return {"plan": cmd_plan, "land": cmd_land}[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
