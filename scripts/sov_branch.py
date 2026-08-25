#!/usr/bin/env python3
"""Branch, worktree, and merge management for a repository with many trees checked out.

Host plumbing, not a governed surface: it holds no standing and grants no authority
(`AGENTS.md`, Local orchestration harness). It exists because this repository presently
has twenty-seven worktrees and thirty-seven branches on origin, several of them left
behind in the scratchpad of a session that has since ended, and git will answer a
question about any one of those facts but never about all three together.

Read commands (`ledger`, `plan`, `worktrees`) change nothing at all: the merge probe runs
inside the object database and never touches a working tree. `merge` builds its own
worktree and merges into that. `retire` deletes local branches and local worktrees, and
refuses by default until told to apply. Nothing here pushes, opens, or merges a pull
request; those are external-world effects and belong to Bdo.

This module owns only the shape of the command line; `sovbranch` owns what each command
does.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sovbranch import execute, gitio, ledger, mergeplan, render  # noqa: E402
from sovsession import store, worktrees  # noqa: E402


def _root() -> Path:
    """The repository this command is being run against."""
    return store.repo_root()


def _emit(payload: Any, as_json: bool, text: str) -> None:
    """Print machine output or human output, never both."""
    print(json.dumps(payload, indent=2, sort_keys=True) if as_json else text)


def _base(args: argparse.Namespace, root: Path) -> str:
    """The ref every position in this run is measured against."""
    return args.base or gitio.default_base(root)


def _candidates(root: Path, base: str, args: argparse.Namespace) -> list[dict[str, Any]]:
    """Branches eligible to merge: holding commits the base lacks, and held by nobody.

    A branch a live session is working in is excluded by default. Merging it would land
    the commits it has pushed while leaving the uncommitted half of that session's work
    behind, which reads afterwards as if the work were complete.
    """
    entries = ledger.build(root, base, probe=False, prs=False, include=args.branch or None)
    chosen = []
    for entry in entries:
        if entry["ahead"] == 0 or entry["name"] == base.split("/")[-1]:
            continue
        if entry["session"] and not args.include_held:
            continue
        chosen.append(entry)
    return chosen


def cmd_ledger(args: argparse.Namespace) -> int:
    """Every branch, where it lives, who holds it, and whether it can land."""
    root = _root()
    base = _base(args, root)
    entries = ledger.build(root, base, probe=args.probe, prs=args.prs,
                           include=args.branch or None)
    _emit(entries, args.as_json, render.ledger(entries, base))
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    """Prove a merge sequence in the object database without touching any tree."""
    root = _root()
    base = _base(args, root)
    record = mergeplan.build(root, base, _candidates(root, base, args),
                             how=args.order, retry=not args.no_retry)
    _emit(record, args.as_json, render.plan(record))
    return 0 if record["steps"] or not record["blocked"] else 1


def cmd_merge(args: argparse.Namespace) -> int:
    """Land a proved sequence in a fresh integration worktree, verifying as it goes."""
    root = _root()
    base = _base(args, root)
    record = mergeplan.build(root, base, _candidates(root, base, args),
                             how=args.order, retry=not args.no_retry)
    if not record["steps"]:
        _emit(record, args.as_json, render.plan(record))
        return 1
    if record["blocked"] and not args.skip_blocked:
        text = render.plan(record) + "\n\nrefusing: re-run with --skip-blocked to land the rest"
        _emit(record, args.as_json, text)
        return 1
    default_path = root.parent / f"{root.name.lower()}-integration"
    path = Path(args.path) if args.path else default_path
    result = execute.integrate(root, base, record["steps"], args.branch_name, path,
                               verify=not args.no_verify, keep_going=args.keep_going)
    _emit(result, args.as_json, render.integrate(result))
    return 1 if result["failed"] else 0


def cmd_retire(args: argparse.Namespace) -> int:
    """Delete local branches the base already contains, and the worktrees holding them."""
    root = _root()
    base = _base(args, root)
    entries = ledger.build(root, base, probe=False, prs=False, include=args.branch or None)
    actions = execute.retire(root, entries, dry_run=not args.apply)
    _emit(actions, args.as_json, render.retire(actions, dry_run=not args.apply))
    return 0


def cmd_worktrees(args: argparse.Namespace) -> int:
    """The worktree inventory the session registry keeps, positioned against the base."""
    root = _root()
    entries = worktrees.inventory(root, store.store_dir(), _base(args, root))
    _emit(entries, args.as_json, render.trees(entries))
    return 0


def _merge_options(parser: argparse.ArgumentParser) -> None:
    """The options that only apply once a plan is actually being landed."""
    parser.add_argument("--branch-name", default="integration/sov-branch",
                        help="name for the new integration branch")
    parser.add_argument("--path", help="where to create the integration worktree")
    parser.add_argument("--skip-blocked", action="store_true",
                        help="proceed even though some branches cannot land")
    parser.add_argument("--keep-going", action="store_true",
                        help="continue past a branch that fails instead of stopping")
    parser.add_argument("--no-verify", action="store_true",
                        help="skip scripts/verify.py after each merge")


def build_parser() -> argparse.ArgumentParser:
    """Assemble the command line."""
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--base", help="ref every position is measured against")
    shared.add_argument("--branch", action="append", default=[],
                        help="restrict to this branch; repeatable")
    shared.add_argument("--json", action="store_true", dest="as_json",
                        help="emit machine-readable output")
    parser = argparse.ArgumentParser(description="Branch, worktree, and merge management.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    table = subparsers.add_parser("ledger", parents=[shared], help="every branch, joined")
    table.add_argument("--probe", action="store_true",
                       help="also merge each branch in the object database to see if it lands")
    table.add_argument("--prs", action="store_true", help="enrich with open pull requests")
    table.set_defaults(handler=cmd_ledger)

    for name, handler, helptext in (
            ("plan", cmd_plan, "prove a merge sequence, change nothing"),
            ("merge", cmd_merge, "land a proved sequence in a fresh worktree")):
        sub = subparsers.add_parser(name, parents=[shared], help=helptext)
        sub.add_argument("--order", choices=mergeplan.ORDERS, default="oldest",
                         help="sequence branches by age, size, or as given")
        sub.add_argument("--no-retry", action="store_true",
                         help="do not retry a conflicted branch after the others land")
        sub.add_argument("--include-held", action="store_true",
                         help="include branches a live session is working in")
        sub.set_defaults(handler=handler)
        if name == "merge":
            _merge_options(sub)

    retire = subparsers.add_parser("retire", parents=[shared],
                                   help="delete local branches the base already contains")
    retire.add_argument("--apply", action="store_true",
                        help="carry it out instead of reporting")
    retire.set_defaults(handler=cmd_retire)

    trees = subparsers.add_parser("worktrees", parents=[shared], help="the worktree inventory")
    trees.set_defaults(handler=cmd_worktrees)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse and dispatch."""
    args = build_parser().parse_args(argv)
    try:
        return args.handler(args)
    except (ValueError, RuntimeError, store.StoreError) as failure:
        print(f"refused: {failure}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
