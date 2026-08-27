"""Five-field cron matching (minute hour day month weekday) in local time.

Supported per field: ``*``, ``N``, ``N-M``, ``*/S``, ``N-M/S``, and comma lists.
Weekday uses 0-6 with Sunday as 0; 7 is accepted as Sunday. No names, no ``L``
or ``?`` extensions. Matching is deterministic and clock-free: the caller
supplies every instant.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


FIELDS = (
    ("minute", 0, 59),
    ("hour", 0, 23),
    ("day", 1, 31),
    ("month", 1, 12),
    ("weekday", 0, 6),
)
MAX_SCAN_MINUTES = 8 * 24 * 60


@dataclass(frozen=True)
class CronSpec:
    """Parsed cron expression as value sets per field."""

    expression: str
    minutes: frozenset[int]
    hours: frozenset[int]
    days: frozenset[int]
    months: frozenset[int]
    weekdays: frozenset[int]


def _parse_field(name: str, text: str, low: int, high: int) -> frozenset[int]:
    values: set[int] = set()
    for part in text.split(","):
        step = 1
        base = part
        if "/" in part:
            base, step_text = part.split("/", 1)
            step = int(step_text)
            if step < 1:
                raise ValueError(f"{name}: step must be positive in '{part}'")
        if base == "*":
            start, end = low, high
        elif "-" in base:
            start_text, end_text = base.split("-", 1)
            start, end = int(start_text), int(end_text)
        else:
            start = int(base)
            end = high if "/" in part else start
        if name == "weekday":
            start, end = (0 if start == 7 else start), (0 if end == 7 else end)
        if start < low or end > high or start > end:
            raise ValueError(f"{name}: '{part}' outside {low}-{high}")
        values.update(range(start, end + 1, step))
    return frozenset(values)


def parse(expression: str) -> CronSpec:
    """Parse a five-field expression; raise ValueError on anything outside the subset."""
    parts = expression.split()
    if len(parts) != 5:
        raise ValueError(f"cron '{expression}': needs five fields, got {len(parts)}")
    try:
        sets = [
            _parse_field(name, part, low, high)
            for part, (name, low, high) in zip(parts, FIELDS)
        ]
    except ValueError as error:
        raise ValueError(f"cron '{expression}': {error}") from None
    return CronSpec(expression, *sets)


def matches(spec: CronSpec, moment: datetime) -> bool:
    """True when the minute containing ``moment`` satisfies the expression."""
    cron_weekday = (moment.weekday() + 1) % 7
    return (
        moment.minute in spec.minutes
        and moment.hour in spec.hours
        and moment.day in spec.days
        and moment.month in spec.months
        and cron_weekday in spec.weekdays
    )


def first_due(spec: CronSpec, after: datetime, until: datetime) -> datetime | None:
    """Earliest matching minute in (after, until], scanning at most eight days back."""
    cursor = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
    limit = until.replace(second=0, microsecond=0)
    floor = limit - timedelta(minutes=MAX_SCAN_MINUTES)
    if cursor < floor:
        cursor = floor
    while cursor <= limit:
        if matches(spec, cursor):
            return cursor
        cursor += timedelta(minutes=1)
    return None


def count_between(spec: CronSpec, after: datetime, until: datetime,
                  cap_days: int) -> tuple[int, bool]:
    """Whole cron occurrences in (after, until], and whether the scan hit its cap.

    Counted on UTC timestamps, while ``runner.is_due`` matches the same expression
    in the host's local time. For a daily, weekly, or n-hourly expression the two
    counts over one interval differ by at most one occurrence at a boundary, which
    is why ``overdue_missed_occurrences`` is two and not one.
    """
    cursor = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
    limit = until.replace(second=0, microsecond=0)
    floor = limit - timedelta(days=cap_days)
    capped = cursor < floor
    if capped:
        cursor = floor
    count = 0
    while cursor <= limit:
        if matches(spec, cursor):
            count += 1
        cursor += timedelta(minutes=1)
    return count, capped


def next_after(spec: CronSpec, after: datetime, cap_days: int) -> datetime | None:
    """The first minute after ``after`` the expression matches, or None inside the cap."""
    cursor = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
    limit = cursor + timedelta(days=cap_days)
    while cursor <= limit:
        if matches(spec, cursor):
            return cursor
        cursor += timedelta(minutes=1)
    return None
