"""Where verification's performance pressure sits, and what it may do.

The rule this module holds, from `decisions/0081`: a wall-clock reading is a
property of the host at the instant it was taken, not of the repository, so it
grades and records debt and never refuses. Pressure moves to per-check ceilings,
which attribute an overrun to the check that owns it rather than to whoever
touched the repository next. One condition still blocks — a single check past
`catastrophic_check_seconds` — because no host load explains it.

`contracts/verification-budget.json` is the declaration; nothing here restates a
number it owns.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, NamedTuple
import json

ROOT = Path(__file__).resolve().parents[2]
TABLE_PATH = ROOT / "contracts" / "verification-budget.json"


class Debt(NamedTuple):
    """One check over its own ceiling. Recorded and attributed; never a refusal."""

    check: str
    seconds: float
    ceiling: float

    def line(self) -> str:
        return f"{self.check}: {self.seconds:.3f}s over its {self.ceiling:.3f}s ceiling"


class Catastrophe(NamedTuple):
    """One check past the blocking ceiling. The only timing condition that refuses."""

    check: str
    seconds: float
    ceiling: float

    def line(self) -> str:
        return (f"{self.check} took {self.seconds:.3f}s, past the {self.ceiling:.3f}s "
                f"catastrophic ceiling")


def load(path: Path | None = None) -> dict[str, Any]:
    """Read the declared budget table."""
    return json.loads((path or TABLE_PATH).read_bytes().decode("utf-8"))


def grades(table: dict[str, Any]) -> list[tuple[str, float]]:
    """Wall-clock bands, fastest first."""
    return [(name, float(ceiling)) for name, ceiling in table["wall_clock"]["grades"]]


def grade(wall: float, table: dict[str, Any]) -> str | None:
    """The band a wall time earns, or None past the slowest band.

    None no longer means failure. It means the run earned no grade and owes the
    debt `wall_clock_line` states.
    """
    for name, ceiling in grades(table):
        if wall <= ceiling:
            return name
    return None


def slowest_band(table: dict[str, Any]) -> float:
    """The ceiling of the slowest graded band."""
    return grades(table)[-1][1]


def wall_clock_line(wall: float, table: dict[str, Any]) -> str:
    """State the grade a run earned, or the debt it owes, naming the next faster band."""
    earned = grade(wall, table)
    if earned is None:
        return (f"DEBT: no wall-clock grade at {wall:.3f}s; "
                f"{grades(table)[-1][0]} needs {slowest_band(table):.3f}s or less")
    bands = grades(table)
    index = [name for name, _ in bands].index(earned)
    if index == 0:
        return f"GRADE: {earned} at {wall:.3f}s, the fastest band"
    faster, ceiling = bands[index - 1]
    return f"GRADE: {earned} at {wall:.3f}s; {faster} needs {ceiling:.3f}s or less"


def ceiling_for(check: str, table: dict[str, Any]) -> float:
    """The ceiling this check answers to: its own if named, else the default."""
    ceilings = table["check_ceilings"]
    return float(ceilings["named"].get(check, ceilings["default_seconds"]))


def judge(timings: list[tuple[str, float]],
          table: dict[str, Any]) -> tuple[list[Debt], list[Catastrophe]]:
    """Grade every check against its own ceiling.

    Returns debts and catastrophes separately because they resolve differently:
    debt is recorded and attributed, catastrophe refuses the run. A check is
    never both — past the catastrophic ceiling it is only a catastrophe, so one
    regression is not reported twice.
    """
    blocking = float(table["catastrophic_check_seconds"])
    debts: list[Debt] = []
    catastrophes: list[Catastrophe] = []
    for name, seconds in timings:
        if seconds > blocking:
            catastrophes.append(Catastrophe(name, seconds, blocking))
            continue
        ceiling = ceiling_for(name, table)
        if seconds > ceiling:
            debts.append(Debt(name, seconds, ceiling))
    debts.sort(key=lambda entry: entry.seconds, reverse=True)
    catastrophes.sort(key=lambda entry: entry.seconds, reverse=True)
    return debts, catastrophes


def report(debts: list[Debt], wall_line: str, table: dict[str, Any]) -> list[str]:
    """The lines a passing run prints about its own cost.

    Debt is stated with an owner and a number so a reader knows which check to
    open. A run with no debt says so, because silence would read the same as a
    run whose debt nobody computed.
    """
    lines = [wall_line]
    if not debts:
        lines.append(f"BUDGET: every check inside its ceiling "
                     f"(default {table['check_ceilings']['default_seconds']:.3f}s)")
        return lines
    total = sum(entry.seconds - entry.ceiling for entry in debts)
    lines.append(f"BUDGET DEBT: {len(debts)} check(s) over ceiling, {total:.3f}s above budget")
    lines.extend(f"  {entry.line()}" for entry in debts)
    lines.append("  Debt is attributed and does not refuse this run "
                 "(contracts/verification-budget.json).")
    return lines
