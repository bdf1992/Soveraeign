"""One derivation per rule in ``contracts/automation-health.json``.

Each function answers a single question - did this rule fire, and on what numbers -
and returns the sentence a reader sees, or None. The severity, the thresholds, and
whether a rule applies to a switched-off schedule all come from the table; only the
arithmetic lives here, so a rule added to the table with no derivation fails loudly
in ``health.judge`` rather than passing as a rule that never fires.

Nothing here reads a file, a clock, or the ledger. Every input arrives on ``Facts``.
"""

from __future__ import annotations

from sovschedule import cron
from sovschedule.facts import (
    FAILED, FAILURE_STATUSES, PASSED, REFUSED, Facts, measured, settled, statuses_of,
    utc,
)


def _target_missing(facts: Facts, _table: dict, _limits: dict) -> str | None:
    if facts.target_exists:
        return None
    detail = "the workflow or skill file this schedule targets is not in the tree"
    if facts.declaration_defect:
        return f"{detail}; the loader refuses it: {facts.declaration_defect}"
    return detail


def _declaration_refused(facts: Facts, _table: dict, _limits: dict) -> str | None:
    """Stands down where the target is absent; TARGET_MISSING carries the defect there."""
    if not facts.declaration_defect or not facts.target_exists:
        return None
    return f"the loader refuses this declaration: {facts.declaration_defect}"


def _enabled_never_run(facts: Facts, _table: dict, _limits: dict) -> str | None:
    if facts.runs:
        return None
    return "enabled, and the record holds no attempt at all - the tick is not reaching it"


def _last_run_failed(facts: Facts, _table: dict, _limits: dict) -> str | None:
    answered = settled(facts)
    if not answered or answered[-1] not in FAILURE_STATUSES:
        return None
    word = "failed" if answered[-1] == FAILED else "never reported"
    return f"the newest settled run {word}"


def _consecutive_failures(facts: Facts, _table: dict, limits: dict) -> str | None:
    threshold = limits["consecutive_failure_threshold"]
    answered = settled(facts)
    if len(answered) < threshold:
        return None
    tail = answered[-threshold:]
    if any(status not in FAILURE_STATUSES for status in tail):
        return None
    return f"the newest {threshold} settled runs all failed: {', '.join(tail)}"


def _runtime_regression(facts: Facts, _table: dict, limits: dict) -> str | None:
    runs = measured(facts)
    if len(runs) < 2:
        return None
    previous = runs[-2].duration_seconds
    newest = runs[-1].duration_seconds
    grew_by = newest - previous
    multiple = limits["regression_multiple"]
    floor = limits["regression_floor_seconds"]
    if previous < 0 or grew_by < floor or (previous > 0 and newest < previous * multiple):
        return None
    times = "an unmeasurable multiple of" if previous == 0 else f"{newest / previous:.1f} times"
    return (f"{newest:.0f}s against {previous:.0f}s the run before it - "
            f"{times}, {grew_by:.0f}s more")


def _refusal_loop(facts: Facts, _table: dict, limits: dict) -> str | None:
    threshold = limits["refusal_loop_threshold"]
    if len(facts.runs) < threshold:
        return None
    tail = facts.runs[-threshold:]
    statuses = statuses_of(facts)[-threshold:]
    if any(status != REFUSED for status in statuses):
        return None
    codes = {run.reason_code for run in tail}
    if len(codes) != 1:
        return None
    code = codes.pop()
    named = code or ("an unrecorded reason - the runner refusal wording no longer "
                     "matches what history.py parses")
    return f"the newest {threshold} attempts were all refused {named}"


def _overdue(facts: Facts, _table: dict, limits: dict) -> str | None:
    """Late by whole cadences, or last attempted before the scan window even opens.

    The cap is not a reason to stay quiet. A weekly expression yields one or two
    occurrences inside an eight-day window depending on which weekday today is, so a
    threshold of two would fire on one day in seven and stay silent on the other six,
    however long the schedule had been dead. A capped walk means the gap is longer than
    the window, which is already past the threshold for every cadence declared here.
    """
    if not facts.runs:
        return None
    threshold = limits["overdue_missed_occurrences"]
    try:
        spec = cron.parse(facts.cron_expression)
    except ValueError:
        return None  # DECLARATION_REFUSED already names an expression that will not parse
    last = facts.runs[-1].attempted_at.astimezone(facts.now.tzinfo)
    count, capped = cron.count_between(spec, last, facts.now, limits["scan_days"])
    if count < threshold and not capped:
        return None
    days = limits["scan_days"]
    if capped:
        return (f"the last attempt at {utc(last)} is older than the {days}-day scan "
                f"window; at least {count} cron occurrences have passed since")
    return f"{count} cron occurrences have passed since the last attempt at {utc(last)}"


def _empty_run(facts: Facts, _table: dict, _limits: dict) -> str | None:
    """A run that returned zero and left nothing behind.

    Every declaration prompt asks the executor for a completion report under reports/.
    A run that passes without writing one is the refusal loop quieter twin: it is
    alive, it spends budget, and it achieves nothing - and unlike a refusal, nothing
    else in the record calls it out.

    Reads PASSED runs rather than measured ones. Measured also requires an end time,
    and a witness found the difference reachable: a PASSED run with no recorded end
    read HEALTHY. Today one reader sets both together, but ``history.py`` is declared
    a replaceable seam, and a rule that depends on a coupling only the present source
    guarantees is exactly what that seam promises it does not.
    """
    passed = [run for run, status in zip(facts.runs, statuses_of(facts)) if status == PASSED]
    if not passed or passed[-1].produced_reports:
        return None
    return (f"run {passed[-1].run_id} returned zero and wrote no report under "
            "reports/, which is what its prompt asked for")


#: Rule name to the function that decides whether it fired. The severity, the
#: thresholds, and whether a rule applies to a disabled schedule all come from the
#: table; only the derivation lives here, so adding a rule to the table without a
#: derivation fails loudly rather than passing as a rule that never fires.
DERIVATIONS = {
    "TARGET_MISSING": _target_missing,
    "DECLARATION_REFUSED": _declaration_refused,
    "ENABLED_NEVER_RUN": _enabled_never_run,
    "LAST_RUN_FAILED": _last_run_failed,
    "CONSECUTIVE_FAILURES": _consecutive_failures,
    "RUNTIME_REGRESSION": _runtime_regression,
    "REFUSAL_LOOP": _refusal_loop,
    "OVERDUE": _overdue,
    "EMPTY_RUN": _empty_run,
}
