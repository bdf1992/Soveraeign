"""Where verification's performance pressure sits, and what it may do.

The rule this module holds, from `decisions/0081`: a wall-clock reading is a
property of the host at the instant it was taken, not of the repository, so it
grades and records debt and never refuses. Pressure moves to per-check ceilings,
which attribute an overrun to the check that owns it rather than to whoever
touched the repository next. One condition still blocks — a single check past
its catastrophic ceiling — because a check that has changed is a defect.

That ceiling used to be one absolute number, and an absolute number decays: it
was set far above the slowest check of the day, the suite grew, and it began
refusing runs for growing rather than for regressing. It is now derived from
each check's own measured baseline, so the comparison it makes stays the one it
claims to make. A refusal is also confirmed by re-running the check alone, since
a reading taken while forty-seven other checks share the pool is not a clean
measurement of anything.

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
    """One check past its blocking ceiling. The only timing condition that refuses.

    ``alone`` is the isolated re-reading, taken with nothing else running, or
    ``None`` while the catastrophe is still only suspected. A suspicion is not a
    refusal: the run refuses on the isolated reading, because that is the one
    measuring the check rather than the pool it shared.
    """

    check: str
    seconds: float
    ceiling: float
    alone: float | None = None

    def confirmed(self) -> bool:
        """True when an isolated reading was taken and it is also over the ceiling."""
        return self.alone is not None and self.alone > self.ceiling

    def line(self) -> str:
        first = (f"{self.check} took {self.seconds:.3f}s, past its {self.ceiling:.3f}s "
                 f"catastrophic ceiling")
        if self.alone is None:
            return first
        if self.confirmed():
            return f"{first}, and {self.alone:.3f}s when re-run alone"
        return f"{first}, but {self.alone:.3f}s when re-run alone: crowded, not changed"


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


def baseline_for(check: str, table: dict[str, Any]) -> float | None:
    """The check's measured baseline, or None when it was too fast to have one."""
    baseline = table["catastrophic"]["baselines"].get(check)
    return None if baseline is None else float(baseline)


def catastrophic_for(check: str, table: dict[str, Any]) -> float:
    """The ceiling past which this check refuses the run.

    Derived from what the check is measured to cost, so a suite that grows moves
    its own ceiling when the baseline is next taken, while a check that triples
    against a current baseline still refuses. A check too fast to carry a
    baseline answers to the unbaselined ceiling: it has no measured cost to
    multiply, and it is not thereby exempt.
    """
    catastrophic = table["catastrophic"]
    floor = float(catastrophic["floor_seconds"])
    baseline = baseline_for(check, table)
    if baseline is None:
        return max(floor, float(catastrophic["unbaselined_seconds"]))
    # Rounded to the precision the report prints. Sub-millisecond precision on a
    # ceiling is not a real distinction, and carrying it makes a declared fixture
    # value read as wrong against a float that differs in the twelfth decimal.
    return max(floor, round(baseline * float(catastrophic["factor"]), 3))


def confirms_alone(table: dict[str, Any]) -> bool:
    """Whether a suspected catastrophe must be re-read alone before it refuses."""
    return bool(table["catastrophic"].get("confirm_alone"))


def judge(timings: list[tuple[str, float]],
          table: dict[str, Any]) -> tuple[list[Debt], list[Catastrophe]]:
    """Grade every check against its own ceiling.

    Returns debts and catastrophes separately because they resolve differently:
    debt is recorded and attributed, catastrophe refuses the run. A check is
    never both — past its catastrophic ceiling it is only a catastrophe, so one
    regression is not reported twice.

    Catastrophes come back unconfirmed, carrying no isolated reading. Whether
    they refuse is decided after that reading is taken, by ``refusing``.
    """
    debts: list[Debt] = []
    catastrophes: list[Catastrophe] = []
    for name, seconds in timings:
        if seconds > catastrophic_for(name, table):
            catastrophes.append(Catastrophe(name, seconds, catastrophic_for(name, table)))
            continue
        ceiling = ceiling_for(name, table)
        if seconds > ceiling:
            debts.append(Debt(name, seconds, ceiling))
    debts.sort(key=lambda entry: entry.seconds, reverse=True)
    catastrophes.sort(key=lambda entry: entry.seconds, reverse=True)
    return debts, catastrophes


def refusing(catastrophes: list[Catastrophe], table: dict[str, Any]) -> list[Catastrophe]:
    """The catastrophes that actually refuse the run.

    With confirmation on, only those whose isolated re-reading was also over.
    With it off, all of them: a table that declares no confirmation step is
    taking the crowded reading at face value, which is its own choice to make.

    ``blocks`` is read here rather than described: a declared switch that
    switches nothing is worse than no switch, because a reader takes it for the
    rule.
    """
    if not table["catastrophic"].get("blocks", True):
        return []
    if not confirms_alone(table):
        return list(catastrophes)
    return [entry for entry in catastrophes if entry.confirmed()]


def demoted(catastrophes: list[Catastrophe], refused: list[Catastrophe],
            table: dict[str, Any]) -> list[Debt]:
    """Debt for suspects the isolated reading cleared.

    ``judge`` skips debt for a catastrophe so one regression is not reported
    twice. That reasoning held while every catastrophe refused. One that clears
    refuses nothing, so without this its overrun would vanish from the accounting
    entirely — the slowest check in the run owing nothing on the one path where
    it was slowest.
    """
    cleared = [entry for entry in catastrophes if entry not in refused]
    return [Debt(entry.check, entry.seconds, ceiling_for(entry.check, table))
            for entry in cleared
            if entry.seconds > ceiling_for(entry.check, table)]


def baseline_drift(timings: list[tuple[str, float]], table: dict[str, Any]) -> list[str]:
    """Checks whose reading has parted company with their recorded baseline.

    Read in both directions, for two different reasons.

    Under: a baseline is what every derived ceiling is computed from, so one set
    too high raises a ceiling and nothing else notices. Nothing here refuses —
    the run cannot tell an inflated baseline from a check that genuinely got
    faster — but a number nobody would defend stops being invisible.

    Over: the cliff catches a check that triples, and the thing worth knowing is
    that a check costs materially more than it did. That is a continuous
    comparison, not a cliff, and it is the reading that would name a regression
    on the run it lands rather than two doublings later.

    What this cannot see is stated in the contract and bears repeating: a
    baseline inflated just far enough to admit a reading it should have refused
    sits inside the band this is silent on. Visibility is not a guard.
    """
    drift = table["catastrophic"]["baseline_drift"]
    under = float(drift["under_factor"])
    over = float(drift["over_factor"])
    floor = float(drift["floor_seconds"])
    lines = []
    for name, seconds in timings:
        baseline = baseline_for(name, table)
        if baseline is None or seconds <= 0:
            continue
        # The same reason the cliff has a floor and 28 checks carry no baseline:
        # a ratio taken on a fifth of a second is scheduling noise, and a report
        # that cries wolf on a loaded run teaches a reader to skim it.
        if baseline < floor:
            continue
        if baseline > seconds * under:
            lines.append(f"{name}: measured {seconds:.3f}s against a {baseline:.3f}s "
                         f"baseline, which derives its {catastrophic_for(name, table):.3f}s "
                         f"ceiling; the baseline may be stale or too high")
        elif seconds > baseline * over:
            lines.append(f"{name}: measured {seconds:.3f}s against a {baseline:.3f}s "
                         f"baseline, {seconds / baseline:.2f}x; it costs materially more "
                         f"than when the baseline was taken")
    return lines


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
