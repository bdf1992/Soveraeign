"""Where verification's performance pressure sits, and what it may do.

The rule this module holds, from `decisions/0081`: a wall-clock reading is a
property of the host at the instant it was taken, not of the repository, so it
grades and records debt and never refuses. Pressure moves to per-check ceilings,
which attribute an overrun to the check that owns it rather than to whoever
touched the repository next.

One timing condition still blocks: a single check past
`catastrophic_check_seconds`. Wall accuses exactly as it does today: a check
whose wall reading stays at or under the ceiling raises no suspicion, whatever
its CPU reading is. Only once wall has accused can a measured CPU reading
(`scripts/sovverify/clocks.py`) acquit it, by coming in at or under the
ceiling itself; a check with no measured CPU reading still refuses on wall
alone. CPU never raises a suspicion wall did not already raise, because a
check that shards across processes can spend far more CPU than wall, and
grading the accusation on CPU would make the ceiling stricter for exactly the
checks parallelism was meant to help. A pooled reading past that ceiling is
only a suspected catastrophe when confirmation is enabled; refusal requires
the same check to cross the ceiling again when re-read alone. This keeps
genuine pathological regressions blocking without treating host contention as
proof of an implementation defect.

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
    """One check past the blocking ceiling.

    ``alone`` is the isolated re-reading, or ``None`` while the pooled overrun is
    only suspected. With confirmation enabled, only a confirmed isolated overrun
    refuses.
    """

    check: str
    seconds: float
    ceiling: float
    alone: float | None = None

    def confirmed(self) -> bool:
        """True when an isolated reading was taken and is also over the ceiling."""
        return self.alone is not None and self.alone > self.ceiling

    def line(self) -> str:
        first = (f"{self.check} took {self.seconds:.3f}s, past the {self.ceiling:.3f}s "
                 f"catastrophic ceiling")
        if self.alone is None:
            return first
        if self.confirmed():
            return f"{first}, and {self.alone:.3f}s when re-run alone"
        return f"{first}, but {self.alone:.3f}s when re-run alone: crowded, not confirmed"


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


def confirms_alone(table: dict[str, Any]) -> bool:
    """Whether a pooled catastrophic reading must be re-read alone to refuse."""
    return bool(table.get("catastrophic_confirm_alone", False))


def judge(timings: list[tuple[str, float]] | list[tuple[str, float, float | None, bool]],
          table: dict[str, Any]) -> tuple[list[Debt], list[Catastrophe]]:
    """Grade every check against its own ceiling.

    Each entry is ``(name, wall)`` or ``(name, wall, cpu, measured)``. Debt and
    every other purpose still grade on wall, exactly as `decisions/0081`
    settled: the aggregate wall grade, the per-check debt table, and the
    printed timings are unchanged. Only the catastrophic read changes: wall
    accuses exactly as it does today, and a measured CPU reading at or under
    the ceiling then acquits it. A check whose wall stays at or under the
    ceiling raises no suspicion regardless of its CPU reading, because a check
    that shards across processes can spend far more CPU than wall
    (`#148/C0027`, PR #151); a check with no measured CPU reading still
    refuses on wall alone, exactly as before.

    Returns debts and suspected catastrophes separately because they resolve
    differently. A check is never both on the first reading; a suspected
    catastrophe that clears confirmation can later be demoted back to debt.
    """
    blocking = float(table["catastrophic_check_seconds"])
    debts: list[Debt] = []
    catastrophes: list[Catastrophe] = []
    for entry in timings:
        name, wall = entry[0], entry[1]
        cpu = entry[2] if len(entry) > 2 else None
        measured = bool(entry[3]) if len(entry) > 3 else False
        if wall > blocking:
            catastrophic_reading = cpu if measured and cpu is not None else wall
            if catastrophic_reading > blocking:
                catastrophes.append(Catastrophe(name, catastrophic_reading, blocking))
                continue
        ceiling = ceiling_for(name, table)
        if wall > ceiling:
            debts.append(Debt(name, wall, ceiling))
    debts.sort(key=lambda entry: entry.seconds, reverse=True)
    catastrophes.sort(key=lambda entry: entry.seconds, reverse=True)
    return debts, catastrophes


def refusing(catastrophes: list[Catastrophe], table: dict[str, Any]) -> list[Catastrophe]:
    """Return the catastrophic readings that are allowed to refuse the run."""
    if not confirms_alone(table):
        return list(catastrophes)
    return [entry for entry in catastrophes if entry.confirmed()]


def demoted(catastrophes: list[Catastrophe], refused: list[Catastrophe],
            table: dict[str, Any]) -> list[Debt]:
    """Restore ordinary debt for pooled catastrophes that isolated confirmation clears."""
    cleared = [entry for entry in catastrophes if entry not in refused]
    return [Debt(entry.check, entry.seconds, ceiling_for(entry.check, table))
            for entry in cleared
            if entry.seconds > ceiling_for(entry.check, table)]


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
