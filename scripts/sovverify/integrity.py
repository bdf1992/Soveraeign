"""Checks that grade the verification machinery from outside the tooling suite."""

from __future__ import annotations

import sys

from sovverify.shape import ROOT, Check


INTEGRITY_CHECKS = (
    Check(
        "tooling population integrity",
        [sys.executable, "scripts/sov_tooling_population.py"],
        ROOT,
        "lists scripts/tests independently of the tooling runner and self-checks the comparison before trusting agreement, so narrowing the runner's discovery cannot remove the guard that detects it",
        ("scripts/tests", "scripts/run_tooling_tests.py", "scripts/sov_tooling_population.py"),
    ),
    Check(
        "tooling verdict integrity",
        [sys.executable, "scripts/sov_tooling_verdict.py"],
        ROOT,
        "runs the tooling runner against miniature trees with known pass/fail outcomes and separately binds the named repository check to the real runner, so discarded shard failures or a repointed check cannot report green merely by silencing in-suite guards",
        (
            "scripts/run_tooling_tests.py",
            "scripts/sov_tooling_verdict.py",
            "scripts/sovverify/checks.py",
        ),
    ),
)
