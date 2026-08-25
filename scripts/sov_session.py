#!/usr/bin/env python3
"""Live-session coordination across the worktrees of one repository.

Host plumbing, not a governed surface: it holds no standing and grants no
authority (`AGENTS.md`, Local orchestration harness). It exists because git
answers "what changed" and never "who is changing it right now", and on
2026-08-23 seven concurrent sessions in one working tree produced three lost
updates, a decision-number collision, and a blanket commit that swept four
sessions' uncommitted work into one branch.

Read commands (`list`, `who`, `brief`, `worktree list`) need no identity and
touch nothing. Write commands record an event; nothing here ever edits history.
This module owns only the shape of the command line; `sovsession.commands` owns
what each command does.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sovsession import commands  # noqa: E402
from sovsession import store  # noqa: E402

session_name = commands.session_name


def _common() -> argparse.ArgumentParser:
    """The options every subcommand accepts, before or after the subcommand.

    `register --name X` is the order people actually type, and argparse rejects
    it by default when the option lives only on the top-level parser. SUPPRESS
    keeps an unsupplied copy from overwriting one given on the other side.
    """
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--name", default=argparse.SUPPRESS,
                        help="override this session's registry name")
    shared.add_argument("--json", action="store_true", dest="as_json",
                        default=argparse.SUPPRESS, help="emit machine-readable output")
    return shared


def build_parser() -> argparse.ArgumentParser:
    """Assemble the command line."""
    shared = _common()
    parser = argparse.ArgumentParser(description="Live-session coordination.",
                                     parents=[shared])
    parser.set_defaults(name=None, as_json=False)
    subparsers = parser.add_subparsers(dest="command", required=True,
                                       parser_class=lambda **kw: argparse.ArgumentParser(
                                           parents=[shared], **kw))

    register = subparsers.add_parser("register", help="record this session as live")
    register.add_argument("--intent", help="what this session is building")
    register.set_defaults(handler=commands.cmd_register)

    principal = subparsers.add_parser("principal",
                                      help="name the principal this session speaks as")
    principal.set_defaults(handler=commands.cmd_principal)

    subparsers.add_parser(
        "heartbeat", help="refresh liveness").set_defaults(handler=commands.cmd_heartbeat)
    subparsers.add_parser("end", help="close this session").set_defaults(handler=commands.cmd_end)

    claim = subparsers.add_parser("claim", help="claim paths for writing")
    claim.add_argument("paths", nargs="*")
    claim.add_argument("--resource", action="append", metavar="NAME",
                       help="a non-file hold: port:8787, sqlite:.local/console/x.db")
    claim.add_argument("--intent", help="why")
    claim.add_argument("--force", action="store_true", help="take a held claim anyway")
    claim.set_defaults(handler=commands.cmd_claim)

    release = subparsers.add_parser("release", help="give up claims")
    release.add_argument("paths", nargs="+")
    release.set_defaults(handler=commands.cmd_release)

    who = subparsers.add_parser("who", help="name the live holders of a path")
    who.add_argument("path")
    who.set_defaults(handler=commands.cmd_who)

    subparsers.add_parser(
        "list", help="live sessions and claims").set_defaults(handler=commands.cmd_list)
    subparsers.add_parser(
        "brief", help="the starting-session briefing").set_defaults(handler=commands.cmd_brief)
    subparsers.add_parser(
        "contested",
        help="uncommitted paths another live session holds").set_defaults(
            handler=commands.cmd_contested)

    guard = subparsers.add_parser("guard", help="judge a pending write or command")
    guard.add_argument("--path", help="repository path about to be written")
    guard.add_argument("--command", help="shell command about to run")
    guard.set_defaults(handler=commands.cmd_guard)

    reserve = subparsers.add_parser("reserve-decision", help="take a decision number")
    reserve.add_argument("slug")
    reserve.set_defaults(handler=commands.cmd_reserve_decision)

    worktree = subparsers.add_parser("worktree", help="inventory or create worktrees")
    wt_sub = worktree.add_subparsers(dest="worktree_command", required=True)
    wt_new = wt_sub.add_parser("new", help="add a worktree from a usable base")
    wt_new.add_argument("name_arg", metavar="name")
    wt_new.add_argument("--base", help="ref to branch from (default: current HEAD)")
    wt_new.add_argument("--branch", help="branch name (default: feat/<name>)")
    wt_sub.add_parser("list", help="every worktree and its occupant")
    wt_prune = wt_sub.add_parser("prune", help="remove worktrees holding nothing")
    wt_prune.add_argument("--apply", action="store_true", help="actually remove them")
    worktree.set_defaults(handler=commands.cmd_worktree)

    subparsers.add_parser(
        "selfcheck", help="prove the logic offline").set_defaults(handler=commands.cmd_selfcheck)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Dispatch one command."""
    args = build_parser().parse_args(argv)
    try:
        return int(args.handler(args))
    except store.StoreError as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
