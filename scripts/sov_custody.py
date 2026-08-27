#!/usr/bin/env python3
"""Custody: who is on the hook for an initiative, and how far it has been drawn.

Phase I was defined as nine requirements and worked as one undivided surface,
which is why four hundred commits produced no reading of its own progress. A
custody is the missing layer between the requirement and the commit: one named
initiative, one seat carrying it, a declared stage it must reach, and a closure
condition somebody can run.

    list        every custody, where it stands, what it targets
    board       one custody as a board across the circuit stages
    circuit     the five stages, their admission predicates and their defeats
    estimate    estimated cost against measured actual, and the registry grade
    reconcile   phase exit clauses against the custodies that hold them
    phase       phase terminals, pinned definitions, and their defects
    orphans     declared work no custody holds
    selfcheck   prove every declared refusal fires against a fixture

Nothing here settles anything. A custody grants no authority and changes no
standing, and a stage a participant drew is a build claim like any other.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sovcustody import commands  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", dest="as_json", action="store_true",
                        help="emit machine-readable output")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="every custody and where it stands")
    board = subparsers.add_parser("board", help="one custody as a board")
    board.add_argument("custody_id")
    board.add_argument("--no-derived", action="store_true",
                       help="skip the worklist join and read the custody alone")
    subparsers.add_parser("circuit", help="the five stages and their defeats")
    estimate = subparsers.add_parser("estimate", help="estimated against measured cost")
    estimate.add_argument("custody_id", nargs="?")
    subparsers.add_parser("reconcile", help="phase exit clauses against custodies")
    subparsers.add_parser("phase", help="phase terminals and their pinned definitions")
    orphans = subparsers.add_parser("orphans", help="declared work no custody holds")
    orphans.add_argument("--kind", choices=["SEAM", "ITEM"])
    subparsers.add_parser("selfcheck", help="prove every declared refusal fires")

    args = parser.parse_args()
    handlers = {
        "list": commands.command_list,
        "board": commands.command_board,
        "circuit": commands.command_circuit,
        "estimate": commands.command_estimate,
        "reconcile": commands.command_reconcile,
        "phase": commands.command_phase,
        "orphans": commands.command_orphans,
        "selfcheck": commands.command_selfcheck,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
