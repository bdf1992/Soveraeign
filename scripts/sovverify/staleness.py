"""Checks that grade whether a written page still matches the record it describes.

A different kind of evidence from the rest of the table, and the seam is the same
one `participants.py` was split on: not arithmetic, but what a reader learns from
the result. These four settle nothing about whether a contract validates or a
participant works. They settle whether prose that a reader - most often a launched
agent, which does not carry the interactive session's context to correct it - will
take as current is still true of the repository.

`LESSONS.md` L-0001 is why the group exists: the orientation snapshot claimed 26
commits and 17 decision records against a record holding 65 and 27, having drifted
inside one day. `counted populations` is the generalisation of that check past the
one page it was written for, and it was built because that check was green while
eight numbers elsewhere had drifted, four of them in governing documents.
`recorded traps` inverts the same idea: it fails when a recorded hazard stops
being true, so a warning cannot outlive what it warns about.

Split out of `checks.py` at the 300-line module ceiling.
"""

from __future__ import annotations

import sys

from sovverify.shape import ROOT, Check

STALENESS_CHECKS = (
    Check("orientation snapshot", [sys.executable, "scripts/sov_snapshot.py", "check"],
          ROOT,
          "re-derives every number at the moment of the check - git ls-tree for the "
          "counted directories and git rev-list for the history, both of the commit at "
          "HEAD, and the working tree for the two counts the repository already "
          "computes, the check table and the capability projection - and never reads "
          "the page's own claim about being current; the page is orientation for every "
          "launched agent, which does not carry the interactive session's context to "
          "correct it (LESSONS.md L-0001). Reading the commit for the counted "
          "directories is Bdo's ruling on acceptance packet A5, and it is what stops "
          "another session's untracked file from reporting a correct page as drifted; "
          "the same ruling left the other two where they were, and the run prints which "
          "half each number belongs to",
          # The derivation moved into scripts/sovsnapshot/ and this tuple did not
          # follow it, so the emitted observation digested neither the code that
          # produces the verdict nor the check table one of the claims counts.
          ("CLAUDE.md", "scripts/sov_snapshot.py", "scripts/sovsnapshot",
           "scripts/sovverify/checks.py")),
    Check("counted populations", [sys.executable, "scripts/sov_counts.py", "check"], ROOT,
          "derives each declared population at check time - the committed file list for the "
          "counted directories, the manifests and projections the repository already "
          "computes for the rest - and searches prose for the wording claiming each, so a "
          "number is graded wherever written rather than only where a pattern was authored; "
          "it reads no page's claim to be current. The generalisation of `orientation "
          "snapshot`, built because that check was green while eight numbers elsewhere had "
          "drifted, four in governing documents. Every run prints the count-shaped "
          "sentences no population declares, so coverage is a list rather than silence",
          ("contracts/counted-populations.json", "scripts/sov_counts.py",
           "scripts/sovcounts", "scripts/sovverify/checks.py")),
    Check("counted population refusals fire",
          [sys.executable, "scripts/sov_counts.py", "selfcheck"], ROOT,
          "grades the grader against controlled values it is handed rather than against the "
          "repository, and separately proves every population still derives non-zero - a "
          "glob that has stopped matching does not raise, it counts nothing, agrees with "
          "every number, and leaves a green result behind it",
          ("scripts/sovcounts", "contracts/counted-populations.json")),
    Check("recorded traps still hold", [sys.executable, "scripts/sov_traps.py"], ROOT,
          "re-derives every recorded trap from the repository at check time, so a trap that "
          "has stopped being true fails here instead of going stale in prose",
          ("CLAUDE.md", "scripts/sov_traps.py")),
)
