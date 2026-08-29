"""The guards between the grant saying yes and git being touched.

One owned responsibility: everything that must hold after authority is granted
and before a single byte is staged. The grant decides whether this landing is
permitted; these decide whether it can be performed honestly against the tree as
it stands right now.

Each guard prints the refusal a reader has to act on and returns a short detail
the landing ledger records, so a refusal that only ever appeared on a terminal
now also accumulates. The messages are moved here unchanged; every one of them
was earned by a defect and rewording them would lose what they teach.

The order matters and is not alphabetical. A directory is refused before a held
path, because staging a directory sweeps in files this landing never enumerated
and the reader must fix that first.
"""

from __future__ import annotations

from typing import Any
import argparse

from sovland import tree


def refusal(args: argparse.Namespace, staged: list[str], behind: int,
            graded_as: dict[str, Any], by_checks: list[str]) -> str | None:
    """Print the first guard that refuses and return its ledger detail, else None."""
    directories = tree.directory_paths(staged)
    if directories:
        print("\n"
              "REFUSED: these name directories, and staging one commits every file "
              "beneath it, including files this landing never enumerated and files "
              "another session may hold:")
        for path in directories:
            print(f"  {path}")
        print("Name the files. A landing that cannot enumerate what it stages cannot "
              "honestly carry the evidence it presents.")
        return "named a directory, which would stage every file beneath it"

    held = tree._held_elsewhere(staged)
    if held:
        print("\nREFUSED: paths held by another live session:")
        for line in held:
            print(f"  {line}")
        return "named a path held by another live session"

    if behind:
        print(f"\nREFUSED: branch is {behind} commit(s) behind {args.target}; rebase or "
              "update before merge (AGENTS.md, Branch and commit strategy).")
        return "is behind the target and must rebase before merging"

    # A deleted path that git still tracks is not absent: `git add` on it exits 0
    # and stages the removal, which is what landing a deletion means.
    absent = tree.absent_paths(graded_as)
    if absent:
        print("\nREFUSED: these do not exist, so nothing was graded for them and "
              "`git add` would fail rather than refuse:")
        for path in absent:
            print(f"  {path}")
        return "named a path that does not exist, so nothing was graded for it"

    if by_checks:
        print("\nREFUSED: running verify and lint modified these paths, so the "
              "checks changed the thing they were checking:")
        for path in by_checks:
            print(f"  {path}")
        return "ran checks that modified the paths being checked"

    moved = tree.drifted(graded_as, tree.fingerprint(staged))
    if moved:
        print("\nREFUSED: these changed between grading and staging, so the evidence "
              "this landing carries describes content it would not commit:")
        for path in moved:
            print(f"  {path}")
        print("Re-run the gate. Several sessions share this working directory, and "
              "`git add` stages the bytes on disk now, not the bytes that were graded.")
        return "graded content that drifted before it could be staged"

    return None


__all__ = ["refusal"]
