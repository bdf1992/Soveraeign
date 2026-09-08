"""The checks that grade the harness surface against the records owning its claims.

Split out of `checks.py` on the same pressure and the same kind of seam that put
the participant checks in `participants.py`: `.claude/` is a surface this
repository owns but does not implement, read by launched agents that carry none
of the interactive session's context, and what it asserts is graded against
records held somewhere else entirely.
"""

from __future__ import annotations

import sys

from sovverify.shape import ROOT, Check

HARNESS_CHECKS = (
    Check("harness claims", [sys.executable, "scripts/sov_harness.py"], ROOT,
          "reads the harness surface and the records that own its claims by separate paths - "
          "STATUS.yaml line by line so the eight legitimately doubled subjects are not "
          "collapsed, contracts/harness-hosts.json for the tool surface, and the tree itself "
          "for addresses - so no claim can supply the record that would support it; "
          ".claude/ is the surface every launched agent reads and was the only claim "
          "surface in this repository with no grader",
          (".claude", "services", "CLAUDE.md", "STATUS.yaml", "contracts/harness-hosts.json",
           "contracts/harness-claims.json", "scripts/sov_harness.py", "scripts/sovharness")),
    Check("harness claim refusals fire",
          [sys.executable, "scripts/sov_harness.py", "selfcheck"], ROOT,
          "builds a tree carrying one unsupported claim of each kind and asserts the matching "
          "refusal fires, and a supported tree is not refused; a grader that cannot refuse "
          "passes every repository silently",
          ("scripts/sov_harness.py", "scripts/sovharness",
           "contracts/harness-claims.json", "contracts/harness-hosts.json")),
)
