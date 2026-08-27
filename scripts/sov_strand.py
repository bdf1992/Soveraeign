"""Grade work that has been left lying around, and fail when any of it exists only here.

Nobody in this repository notices stranded work. A branch that was built, tested and
then never merged reads exactly like a branch someone is still using, and a branch that
was never pushed reads like both -- right up until the disk it lives on is the only copy.
Bdo has been the sole detector of this, by hand, and said plainly that he cannot be.

The check reads git directly at the moment it runs. It never consults a prior report, a
session record, or a branch's own claim about being finished, because every one of those
is written by the participant that walked away.

Two classes, deliberately graded differently:

* ``AT_RISK`` - commits not on the trunk and no upstream anywhere. Losing this directory
  loses the work outright. This is the only condition that fails the check.
* ``UNLANDED`` - commits not on the trunk, but a remote copy exists. Untidy, recoverable,
  reported and never fatal, because mid-flight work is the normal state of a branch.
* ``EXPOSED`` - uncommitted working-tree content no ref in this repository holds. It was
  never a commit, so no branch reading can see it. This fails the check too.

The third class was added after `acceptance/A11.json`, a finished acceptance packet, was
destroyed in this shared tree on 2026-08-27 with no copy anywhere. The check had graded
that tree `PASS` throughout, because it counted uncommitted paths and printed the number
below the verdict without ever reading it. Counting is not grading.

A worktree parked under a temporary or scratchpad directory is reported alongside them:
the session that opened it is usually gone, and its path will not survive a reboot.
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple
import argparse
import subprocess
import sys

_HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_HERE / "scripts"))

from sovstrand import containment, reading  # noqa: E402
from sovstrand.reading import (  # noqa: E402
    AT_RISK,
    EPHEMERAL_MARKERS,
    EXPOSED,
    TRUNK_CANDIDATES,
    UNLANDED,
    Branch,
    Worktree,
    branches,
    distinct,
    git,
    trunk,
    trunk_unpushed,
    worktrees,
)


def uncommitted() -> list[str]:
    """Return every untracked-but-not-ignored and modified path in this working tree."""
    return containment.uncommitted_paths(reading.ROOT)


def exposed() -> list[str]:
    """Return the uncommitted paths whose exact content no ref in this repository holds.

    This is the reading the check was missing. A path here is one power cut, one bad
    `git clean`, or one sibling session's overwrite away from being gone outright, and
    unlike a stranded commit it leaves nothing behind to notice it by.
    """
    return containment.exposed_paths(reading.ROOT)


def brief() -> str:
    """Return a short session-start reading, or an empty string when nothing is at risk.

    Session start is already crowded. This speaks only when something would be lost, and
    keeps the untidy-but-recoverable count to one line underneath it.
    """
    against = trunk()
    if not against:
        return ""
    found = branches(against)
    at_risk = [item for item in found if item.verdict == AT_RISK]
    unlanded = [item for item in found if item.verdict == UNLANDED]
    behind = trunk_unpushed(against)
    bare = exposed()
    if not at_risk and not behind and not bare:
        return ""
    risked = distinct(found, AT_RISK, against) + behind
    named = ", ".join(f"{item.name} ({item.unreachable})" for item in at_risk[:4])
    if len(at_risk) > 4:
        named += f", and {len(at_risk) - 4} more"
    lines = []
    if at_risk or behind:
        lines.append(
            f"Stranded work: {risked} distinct commit(s) exist only on this disk, reachable "
            f"from no remote ({len(at_risk)} branch(es)"
            + (f", plus {behind} on {against}" if behind else "") + ").")
    if named:
        lines.append(f"  {named}")
    if unlanded:
        carried = distinct(found, UNLANDED, against)
        lines.append(f"  Separately, {carried} distinct commit(s) on {len(unlanded)} "
                     "branch(es) are pushed but not merged.")
    if bare:
        shown = ", ".join(bare[:3]) + (f", and {len(bare) - 3} more" if len(bare) > 3 else "")
        lines.append(f"  Exposed: {len(bare)} uncommitted file(s) held by no ref at all "
                     f"({shown}). Contain them: python scripts/sov_strand.py contain.")
    lines.append("  python scripts/sov_strand.py for the full reading.")
    return "\n".join(lines)


def report(against: str, found: list[Branch], trees: list[Worktree],
           dirty: list[str], bare: list[str]) -> int:
    """Print the graded reading and return the process exit code."""
    at_risk = [item for item in found if item.verdict == AT_RISK]
    unlanded = [item for item in found if item.verdict == UNLANDED]
    stranded = distinct(found, AT_RISK, against) + distinct(found, UNLANDED, against)
    ephemeral = [tree for tree in trees if tree.ephemeral]

    behind = trunk_unpushed(against)
    print(f"Trunk: {against}. {stranded} distinct commit(s) on {len(found)} branch(es) are "
          "not on it.")
    if behind:
        print()
        print(f"AT RISK - the trunk itself: {behind} commit(s) on {against} reach no remote.")
    if at_risk:
        print()
        print(f"AT RISK - no copy anywhere but this directory ({len(at_risk)} branch(es)):")
        for item in at_risk:
            print(f"  {item.unreachable:>4} unpushed, {item.ahead:>3} beyond trunk  "
                  f"{item.name}")
    if unlanded:
        print()
        print(f"UNLANDED - pushed, not merged ({len(unlanded)} branch(es)):")
        for item in unlanded:
            print(f"  {item.ahead:>4} commit(s)  {item.name}  -> {item.upstream}")
    if trees:
        print()
        print(f"WORKTREES - {len(trees)} open, {len(ephemeral)} in a temporary location:")
        for tree in trees:
            mark = "  [temporary]" if tree.ephemeral else ""
            print(f"  {tree.branch:<40} {tree.path}{mark}")
    if dirty:
        print()
        held = len(dirty) - len(bare)
        print(f"UNCOMMITTED - {len(dirty)} path(s) changed in this working tree, "
              f"{held} of them held by some ref.")
    if bare:
        print()
        print(f"EXPOSED - {len(bare)} uncommitted file(s) no ref holds at all:")
        for path in bare[:20]:
            print(f"  {path}")
        if len(bare) > 20:
            print(f"  and {len(bare) - 20} more")

    print()
    failures = []
    if at_risk or behind:
        risked = distinct(found, AT_RISK, against) + behind
        failures.append(
            f"{risked} distinct commit(s) across {len(at_risk)} branch(es) and the trunk "
            "exist only in this directory. Push them, merge them, or delete them "
            "deliberately.")
    if bare:
        failures.append(
            f"{len(bare)} uncommitted file(s) exist only in this working tree and no ref "
            "holds them. Commit them, or run python scripts/sov_strand.py contain.")
    if failures:
        for line in failures:
            print(f"FAIL: {line}")
        return 1
    print(f"PASS: no commit and no uncommitted file exists only in this directory. "
          f"{stranded} distinct commit(s) await landing.")
    return 0


def contain(ref: str = "") -> int:
    """Give every exposed uncommitted file a holder, then re-read what the holder holds.

    This writes into the object database and one ref under `refs/rescue`. It touches no
    branch, no remote and not the shared index, so it is safe in a tree several sessions
    are writing at once - which is the tree it exists for.
    """
    bare = exposed()
    if not bare:
        print("Nothing to contain: every uncommitted file is already held by some ref.")
        return 0
    day = git("log", "-1", "--format=%cd", "--date=short").strip() or "undated"
    target = ref or f"{containment.RESCUE_PREFIX}/uncommitted-{day}"
    message = (
        "rescue: uncommitted files this working tree was not protecting\n\n"
        f"{len(bare)} file(s) held by no ref, captured by explicit path. Parentless"
        " and on no branch: this makes the content survive garbage collection and"
        " claims nothing about the work itself.\n")
    commit = containment.capture(reading.ROOT, bare, target, message)
    if not commit:
        print("FAIL: the capture produced no commit. Nothing was contained.")
        return 1
    matched, drifted = containment.verify(reading.ROOT, commit)
    print(f"Contained {matched} file(s) under {target} -> {commit[:12]}")
    if drifted:
        print(f"  {len(drifted)} file(s) changed between capture and check; this tree is "
              "written by more than one participant:")
        for path in drifted[:10]:
            print(f"    {path}")
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    """Grade the working area, or contain what it is not protecting, and return an exit code."""
    parser = argparse.ArgumentParser(description="Grade work left lying around.")
    parser.add_argument(
        "command", nargs="?", default="report", choices=("report", "contain"),
        help="report grades and changes nothing; contain anchors exposed files under a ref")
    parser.add_argument("--ref", default="", help="override the rescue ref contain writes")
    args = parser.parse_args(argv)

    if args.command == "contain":
        return contain(args.ref)

    against = trunk()
    if not against:
        print("PASS: no trunk ref is present in this checkout, so nothing can be graded "
              "against one. This is not evidence that no work is stranded.")
        return 0
    return report(against, branches(against), worktrees(), uncommitted(), exposed())


if __name__ == "__main__":
    sys.exit(main())
