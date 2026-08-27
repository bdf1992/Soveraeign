"""What a run and a schedule read as, before any rule looks at them.

The vocabulary is declared in ``contracts/automation-health.json`` under
``run_status``; this module applies it. Nothing here decides whether a schedule is
healthy - ``rules.py`` derives the findings and ``health.py`` grades them.

A REPORTED event is the executor own self-report. Mapping it to PASSED is a
statement about what the record says, never an observation that the run did what
it said (AGENTS.md, Evidence and standing).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sovschedule.history import Run

REFUSED = "REFUSED"
PASSED = "PASSED"
FAILED = "FAILED"
RUNNING = "RUNNING"
INCOMPLETE = "INCOMPLETE"
FAILURE_STATUSES = (FAILED, INCOMPLETE)
#: Runs whose wall time is a measurement of how long the work takes. A run that failed
#: fast is not one: using it as the baseline reports the next ordinary run as drift,
#: which is how a column earns being ignored.
MEASURED_STATUSES = (PASSED,)
#: A run that answered. Asserted against contracts/automation-health.json run_status.settled
#: in scripts/tests/test_automation_health.py, so the table and this module cannot drift.
SETTLED_STATUSES = (PASSED, FAILED, INCOMPLETE)

UNOBSERVED = "UNOBSERVED"
HEALTHY = "HEALTHY"


def utc(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class Finding:
    """One rule that fired, with the numbers it fired on."""

    rule: str
    severity: str
    detail: str


@dataclass(frozen=True)
class Facts:
    """What one schedule's rules are judged against. No file is read from here."""

    name: str
    enabled: bool
    target_exists: bool
    cron_expression: str
    timeout_seconds: int
    now: datetime
    runs: tuple[Run, ...]
    #: Why scripts/sovschedule/declaration.py refused this file, or None. The health read
    #: loads each declaration on its own so one refused file still leaves the others readable.
    declaration_defect: str | None = None


@dataclass(frozen=True)
class Reading:
    """The judged state of one schedule."""

    name: str
    reading: str
    findings: tuple[Finding, ...]
    statuses: tuple[str, ...]

    @property
    def refuses(self) -> bool:
        return self.reading == "UNHEALTHY"


def run_status(run: Run, timeout_seconds: int, now: datetime) -> str:
    """Map one ledger-recorded run onto the table's run_status vocabulary."""
    if run.attempt_outcome == REFUSED:
        return REFUSED
    if run.report_outcome == "FAILED":
        return FAILED
    if run.report_outcome is not None:
        return PASSED
    return RUNNING if run.age_seconds(now) < timeout_seconds else INCOMPLETE


def statuses_of(facts: Facts) -> list[str]:
    return [run_status(run, facts.timeout_seconds, facts.now) for run in facts.runs]


def settled(facts: Facts) -> list[str]:
    """Statuses of runs that answered, newest last. A refusal invoked nothing."""
    return [status for status in statuses_of(facts) if status in SETTLED_STATUSES]


def consecutive_run_failures(facts: Facts) -> int:
    """How many settled runs, counting back from the newest, failed without a pass.

    Reported as a number on every row because Bdo asked to see it, and used by no
    rule: CONSECUTIVE_FAILURES reads the same settled list against its own threshold.
    """
    count = 0
    for status in reversed(settled(facts)):
        if status not in FAILURE_STATUSES:
            break
        count += 1
    return count


def measured(facts: Facts) -> list[Run]:
    """Passing runs carrying both timestamps, newest last. Only these have a runtime."""
    pairs = zip(facts.runs, statuses_of(facts))
    return [run for run, status in pairs
            if status in MEASURED_STATUSES and run.duration_seconds is not None]
