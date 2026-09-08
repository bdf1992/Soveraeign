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
    Check("carried cores", [sys.executable, "scripts/sov_vendor.py"], ROOT,
          "recomputes each copy's digest from the bytes on disk and reads the expected value "
          "out of the decision that carried it, so neither side can supply the other; it "
          "does not reimplement bdos's own artifact_digest, which answers a different "
          "question and belongs to bdos",
          (".claude/skills", "decisions/0103-carry-two-bdos-cores.md",
           "scripts/sov_vendor.py")),
    Check("carried core refusals fire",
          [sys.executable, "scripts/sov_vendor.py", "selfcheck"], ROOT,
          "builds a tree carrying a drifted copy, an unrecorded copy and a decision with no "
          "pin, and asserts each is refused while a faithful carry is not",
          ("scripts/sov_vendor.py",)),
    Check("harness claims", [sys.executable, "scripts/sov_harness.py"], ROOT,
          "reads the harness surface and the records that own its claims by separate paths - "
          "STATUS.yaml line by line so the eight legitimately doubled subjects are not "
          "collapsed, contracts/harness-hosts.json for the tool surface, and the tree itself "
          "for addresses - so no claim can supply the record that would support it; "
          ".claude/ is the surface every launched agent reads and was the only claim "
          "surface in this repository with no grader",
          (".claude", "services", "CLAUDE.md", "STATUS.yaml", "contracts/harness-hosts.json",
           "contracts/harness-claims.json", "scripts/sov_harness.py", "scripts/sovharness")),
    Check("communications claims", [sys.executable, "scripts/sov_comms.py"], ROOT,
          "reads the agent definitions for behavioural figures and asks each paragraph for "
          "something runnable that derives them, and grades every witnessed claim against "
          "scripts/sov_standing.py, which reads STATUS.yaml and the witness records by paths "
          "this grader never touches; Communications is the only surface a person reads and "
          "was the only claim surface here with no grader, which is how a breakdown of 379 of "
          "the owner's turns survived against no transcript corpus at all",
          (".claude/agents", "contracts/comms-claims.json", "scripts/sov_comms.py",
           "scripts/sovcomms", "STATUS.yaml")),
    Check("communications claim refusals fire",
          [sys.executable, "scripts/sov_comms.py", "selfcheck"], ROOT,
          "grades cases the module carries itself and never reads .claude/, so repairing the "
          "live surfaces cannot stop a refusal being proved; it also asserts that a recorded "
          "historical sentence clears only itself and that NOT_WITNESSED is read as denial",
          ("scripts/sov_comms.py", "scripts/sovcomms", "contracts/comms-claims.json")),
    Check("harness claim refusals fire",
          [sys.executable, "scripts/sov_harness.py", "selfcheck"], ROOT,
          "builds a tree carrying one unsupported claim of each kind and asserts the matching "
          "refusal fires, and a supported tree is not refused; a grader that cannot refuse "
          "passes every repository silently",
          ("scripts/sov_harness.py", "scripts/sovharness",
           "contracts/harness-claims.json", "contracts/harness-hosts.json")),
)
