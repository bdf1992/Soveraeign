"""Grade one schedule, and the node, against the declared health table.

``contracts/automation-health.json`` owns which rules exist, what each fires on,
what severity it carries, whether it applies to a switched-off schedule, and which
reading refuses. This module applies it; ``rules.py`` holds the arithmetic and
``facts.py`` the run vocabulary. ``conformance/fixtures/automation-health/cases.json``
defeats all three: every rule carries a case that proves it fires and a case that
proves it stays quiet.

Nothing here holds standing and nothing here changes a schedule. A reading is a
report about records.
"""

from __future__ import annotations

from pathlib import Path
import json

from sovschedule.facts import (
    FAILED, FAILURE_STATUSES, HEALTHY, INCOMPLETE, MEASURED_STATUSES, PASSED, REFUSED,
    RUNNING, SETTLED_STATUSES, UNOBSERVED, Facts, Finding, Reading,
    consecutive_run_failures as consecutive_failures, run_status, settled, statuses_of,
)
from sovschedule.rules import DERIVATIONS

ROOT = Path(__file__).resolve().parents[2]
TABLE_PATH = ROOT / "contracts" / "automation-health.json"

__all__ = [
    "DERIVATIONS", "FAILED", "FAILURE_STATUSES", "Facts", "Finding", "HEALTHY",
    "INCOMPLETE", "MEASURED_STATUSES", "PASSED", "REFUSED", "RUNNING", "Reading",
    "SETTLED_STATUSES", "UNOBSERVED", "UnderivedRule", "consecutive_failures", "judge",
    "load", "reading_of", "run_status", "statuses_of", "worst",
]


class UnderivedRule(KeyError):
    """The table declares a rule no derivation in ``rules.py`` can evaluate."""


def load(path: Path = TABLE_PATH) -> dict:
    """Read the declared table. The rules live there, not here."""
    return json.loads(path.read_text(encoding="utf-8"))


def judge(facts: Facts, table: dict) -> Reading:
    """Apply every declared rule to one schedule and derive its reading."""
    limits = table["thresholds"]
    findings = []
    for rule, declared in table["rules"].items():
        if rule not in DERIVATIONS:
            raise UnderivedRule(
                f"contracts/automation-health.json declares rule {rule} and "
                "scripts/sovschedule/rules.py has no derivation for it")
        if not facts.enabled and not declared["applies_to_disabled"]:
            continue
        detail = DERIVATIONS[rule](facts, table, limits)
        if detail is not None:
            findings.append(Finding(rule, declared["severity"], detail))
    return Reading(facts.name, reading_of(findings, bool(settled(facts)), table),
                   tuple(findings), tuple(statuses_of(facts)))


def reading_of(findings: list[Finding], has_history: bool, table: dict) -> str:
    """Worst severity that fired; UNOBSERVED when nothing fired and nothing settled.

    ``has_history`` asks whether a run ever answered, not whether the ledger holds a
    line about this schedule. Two identical TREE_DIRTY refusals is the likeliest real
    state on a tree nine sessions share, and it would otherwise read HEALTHY over a
    schedule that has never once executed.
    """
    fired = [finding.severity for finding in findings]
    for reading in table["readings"]["order"]:
        if reading in fired:
            return reading
    return HEALTHY if has_history else UNOBSERVED


def worst(readings: list[str], table: dict) -> str:
    """The node's reading: the worst of its schedules', or UNOBSERVED over none."""
    if not readings:
        return UNOBSERVED
    for reading in table["readings"]["order"]:
        if reading in readings:
            return reading
    return HEALTHY
