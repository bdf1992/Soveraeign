"""One clock, named on every timestamp it writes.

Split out of ``report.py`` at the module ceiling. The seam is real: everything here is
about what time it is and how to say so, and nothing here reads a declaration.

``runner.is_due`` matches cron in the host local time, so a read taken in UTC answers
"when is it next due" hours - sometimes a day - wrong on any host that is not on UTC.
Every stamp therefore carries its own offset rather than assuming a reader knows which
clock produced it.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


def host_offset() -> timedelta:
    """The host current offset from UTC, which is the clock the runner fires in."""
    return datetime.now(timezone.utc).astimezone().utcoffset() or timedelta(0)


def stamp(moment: datetime | None) -> str:
    """One timestamp, in whatever clock it carries, with that clock named on it."""
    if moment is None:
        return "-"
    offset = moment.utcoffset() or timedelta(0)
    if not offset:
        return moment.strftime("%Y-%m-%dT%H:%M:%SZ")
    total = int(offset.total_seconds()) // 60
    sign = "+" if total >= 0 else "-"
    return (moment.strftime("%Y-%m-%dT%H:%M:%S")
            + f"{sign}{abs(total) // 60:02d}:{abs(total) % 60:02d}")


def parse_stamp(text: str) -> datetime:
    """Read back a stamp this module wrote, in UTC or in an offset clock."""
    return datetime.fromisoformat(text)
