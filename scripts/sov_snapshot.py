#!/usr/bin/env python3
"""Check the orientation snapshot in CLAUDE.md against the record it describes.

`LESSONS.md` L-0001: the snapshot claimed 26 commits and 17 decision records
while the record held 65 commits and records through 0027. It had drifted inside
one day. A snapshot that is stale is worse than none, because every launched
agent reads it as current and does not carry the interactive session's context to
correct it.

The check derives what it can derive exactly and cheaply and names what it does
not, so silence is never read as confirmation. A draft counted conformance cases
from `scenarios.json` and got 9 against the suite's own 20 - a check that derives
the wrong truth is worse than no check. The restraint cuts both ways, and
`sovsnapshot.claims._declared_operations` records where it cut the wrong way.

An unanswerable claim never fails. A shallow CI checkout cannot count commits, and
`verify.py` is the required command there, so reporting that as drift failed three
workflows against a page that was correct - twice, because the first repair
changed the message and not the exit code.

For eight of the ten claims the record is the commit at HEAD and the page is the
working tree. Bdo ruled that referent on acceptance packet A5, 2026-08-26:
`CLAUDE.md` is a committed artifact read out of a checkout, so its counts are
counts of committed state. Before the ruling every count globbed the tree, and one
untracked directory belonging to a sibling session turned this gate red for
everyone on the branch against an unmoved HEAD - while printing an instruction to
edit a file the landing loop's grant excludes, so no automated participant could
clear it. The same ruling left `verification checks` and `declared operations`
where they were, for the restraint in the paragraph above: both count something
the repository already computes, and re-reading it out of the commit would be the
second implementation rather than a change of referent. `claims.UNCHECKED` names
both, so which half a number belongs to is on the printed output.

Six modules, split at the 300-line budget as each repair round grew this one, and
split by what each owns rather than by where the line count fell.
`sovsnapshot/committed.py` owns every call that reaches git and answers what the
commit holds. `sovsnapshot/claims.py` declares what the page claims, names the
source for each, and holds the three deliberate working-tree reads: the page
itself, the check table, and the capability map projection.
`sovsnapshot/grading.py` grades a page against derived values and cannot reach a
repository, because both arguments are required. `sovsnapshot/shape.py` grades the
declared claim table itself, so that a claim added later cannot quietly go back to
globbing the tree and so that the two named exceptions cannot quietly become
three; what it does not establish is written into its own docstring rather than
left to be assumed. `sovsnapshot/selfcheck.py` proves the grader fires and does
not over-fire, consults that shape check, and refuses to report success having
exercised nothing. This module is the command line, the verdict, and the only
place the two halves meet.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sovsnapshot import claims  # noqa: E402
from sovsnapshot import grading  # noqa: E402
from sovsnapshot import selfcheck  # noqa: E402

#: The least of the page a run may check and still call itself a pass. A gate that
#: goes green having checked one claim in ten is reporting on the environment
#: rather than the page. A shallow CI checkout loses only `commits`, nine of ten,
#: and stays green. The boundary is `<`, so exactly half passes; both sides of it
#: are in `scripts/tests/test_sov_snapshot.py`, which they were not until an
#: independent witness pointed out this constant had no test of any kind.
MIN_CHECKABLE = 0.5


def cmd_selfcheck(_args: argparse.Namespace | None = None) -> int:
    """Prove the grader fires and does not over-fire."""
    return selfcheck.run()


def cmd_check(args: argparse.Namespace | None = None) -> int:
    """Grade the page, after proving the grader still works."""
    if cmd_selfcheck(args) != 0:
        print("\nREFUSED: the check itself is broken, so its verdict about the page "
              "means nothing. Nothing was graded.")
        return 1
    try:
        text = claims.page_text()
    except claims.Underivable as absent:
        print(f"\nREFUSED: {absent}. There is nothing to grade.")
        return 1
    answered = claims.derive_all()
    findings = grading.grade(text, answered.values, answered.reasons)
    for line in claims.UNCHECKED:
        print(f"NOT CHECKED: {line}")
    for finding in findings:
        if finding.kind == grading.UNANSWERABLE:
            # Not a failure. An unanswerable claim is a fact about this
            # environment, and failing on it reported a correct page as wrong in
            # the one place the gate is mandatory.
            print(f"NOT CHECKED HERE: {finding.claim} - {finding.detail}")
    drifted = grading.drift(findings)
    if drifted:
        for finding in drifted:
            print(f"FAIL {finding.claim}: {finding.detail}")
        print("\nThe snapshot is orientation for every launched agent and it disagrees "
              "with the record. Either correct CLAUDE.md, or land the sources the page "
              "already describes - eight of these ten counts are of committed state, "
              "which is Bdo's ruling on acceptance packet A5, and the NOT CHECKED lines "
              "above name the two that read the working tree instead. Never widen a "
              "tolerance.")
        return 1
    total = len(claims.CLAIMS)
    checked = total - len([f for f in findings if f.kind == grading.UNANSWERABLE])
    if checked < total * MIN_CHECKABLE:
        print(f"\nREFUSED: only {checked} of {total} claims could be checked here, which "
              "is not enough of the page to call this a pass. The verdict would be about "
              "this environment rather than about the snapshot.")
        return 1
    print(f"PASS: {checked} of {total} snapshot claim(s) match the record")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("check", help="grade the snapshot against the record")
    sub.add_parser("selfcheck", help="prove the check fires and does not over-fire")
    # argv=None must fall through to sys.argv, not to a default subcommand.
    # Defaulting here once swallowed `selfcheck` entirely and ran `check` instead.
    supplied = argv if argv is not None else sys.argv[1:]
    args = parser.parse_args(supplied or ["check"])
    return {"check": cmd_check, "selfcheck": cmd_selfcheck}[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
