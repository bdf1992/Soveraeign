"""Judge the declared board fixture corpus offline.

The corpus lives here rather than inside ``sov_board.py`` so it has one implementation
and two callers: the ``selfcheck`` subcommand, for running it by hand, and a unit test,
so ``scripts/verify.py`` proves it without paying for a thirteenth subprocess. Process
startup is most of what the verification budget spends, and the budget is tight.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from sovboard.actions import load_batch, select
from sovboard.survey import build


def load(root: Path) -> dict[str, Any]:
    """Load the declared corpus of survey and approval cases."""
    path = root / "conformance" / "fixtures" / "board" / "survey-cases.json"
    return json.loads(path.read_text(encoding="utf-8"))


def failures(root: Path, cases: dict[str, Any] | None = None) -> list[str]:
    """Return one message per case whose declared expectation was not met."""
    cases = cases if cases is not None else load(root)
    found: list[str] = []
    for case in cases["cases"]:
        batch = build(root, case["capture"])
        observed = sorted(f"{a.kind}:{a.target}:{a.argument}" for a in batch.actions)
        expected = sorted(case["expect_actions"])
        if observed != expected:
            found.append(f"{case['case_id']}: expected {expected}, observed {observed}")
    for case in cases["approval_cases"]:
        _, refusals = select(load_batch(case["batch"]), case["approve"])
        wanted = case.get("refuses")
        if wanted and not any(wanted in refusal for refusal in refusals):
            found.append(f"{case['case_id']}: expected a refusal naming {wanted!r}, observed {refusals}")
        if not wanted and refusals:
            found.append(f"{case['case_id']}: expected no refusal, observed {refusals}")
    return found


def tally(cases: dict[str, Any]) -> tuple[int, int]:
    """Return the total case count and how many of them are defeating."""
    total = len(cases["cases"]) + len(cases["approval_cases"])
    defeating = sum(1 for case in cases["cases"] if case.get("defeating"))
    defeating += sum(1 for case in cases["approval_cases"] if case.get("refuses"))
    return total, defeating
