"""Apply mutants to a source file, run the suite against each, and score.

The score is the fraction of mutants the suite detected. It is evidence about
the *tests*, not about the code: a low score means the suite asserts less than
it appears to, which is exactly the gap a passing build cannot show.

Mutation is destructive by construction - the mutant must be on disk for the
suite to import it - so every application is wrapped in restore-on-exit and the
original digest is checked afterwards. A run that cannot prove it restored the
tree refuses rather than reporting a score.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import hashlib
import subprocess
import sys

from . import operators

DEFAULT_COMMAND = (sys.executable, "-m", "unittest", "discover", "-s", "scripts/tests", "-q")
DEFAULT_TIMEOUT = 120


class RestoreFailure(RuntimeError):
    """The tree was not restored after a mutant; no score may be reported."""


@dataclass(frozen=True)
class Mutant:
    """One applied mutant and whether the suite detected it."""

    site: operators.Site
    killed: bool
    detail: str


@dataclass
class Score:
    """The outcome of scoring one file."""

    target: str
    command: tuple[str, ...]
    mutants: list[Mutant] = field(default_factory=list)
    skipped: int = 0

    @property
    def generated(self) -> int:
        return len(self.mutants)

    @property
    def killed(self) -> int:
        return sum(1 for m in self.mutants if m.killed)

    @property
    def survived(self) -> list[Mutant]:
        return [m for m in self.mutants if not m.killed]

    @property
    def percent(self) -> float:
        """Kill rate as a percentage; 100.0 when a file admits no mutants."""
        if not self.mutants:
            return 100.0
        return 100.0 * self.killed / self.generated


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _run(command: tuple[str, ...], cwd: Path, timeout: int) -> tuple[bool, str]:
    """Run the suite. Returns (detected, detail).

    A non-zero exit means the suite noticed the mutant. A timeout also counts as
    detected: the mutant changed behaviour observably, which is what is being
    measured, and treating it as survived would flatter the suite.
    """
    try:
        completed = subprocess.run(
            list(command), cwd=str(cwd), capture_output=True, timeout=timeout, check=False,
        )
    except subprocess.TimeoutExpired:
        return True, "suite timed out"
    if completed.returncode != 0:
        return True, f"suite exit {completed.returncode}"
    return False, "suite passed"


def score_file(
    path: Path,
    root: Path,
    command: tuple[str, ...] = DEFAULT_COMMAND,
    timeout: int = DEFAULT_TIMEOUT,
    limit: int | None = None,
) -> Score:
    """Score one file by applying each mutant in turn and running the suite."""
    original = path.read_bytes()
    before = _digest(original)
    source = original.decode("utf-8")
    found = operators.sites(source)
    selected = found if limit is None else found[:limit]
    score = Score(target=str(path), command=command, skipped=len(found) - len(selected))

    try:
        for site in selected:
            try:
                mutated = operators.mutate(source, site.index)
            except (IndexError, ValueError, SyntaxError) as exc:
                score.mutants.append(Mutant(site=site, killed=True, detail=f"unbuildable: {exc}"))
                continue
            path.write_bytes(mutated.encode("utf-8"))
            detected, detail = _run(command, root, timeout)
            score.mutants.append(Mutant(site=site, killed=detected, detail=detail))
    finally:
        path.write_bytes(original)

    if _digest(path.read_bytes()) != before:
        raise RestoreFailure(f"{path} was not restored to its original bytes")
    return score


def render(score: Score) -> str:
    """Human-readable report for one scored file."""
    lines = [
        f"target          : {score.target}",
        f"mutants         : {score.generated}" + (f" ({score.skipped} beyond limit)" if score.skipped else ""),
        f"killed          : {score.killed}",
        f"survived        : {len(score.survived)}",
        f"MUTATION SCORE  : {score.percent:.1f}%",
    ]
    if score.survived:
        lines.append("")
        lines.append("surviving mutants - each names a behaviour the suite does not assert:")
        for mutant in score.survived:
            lines.append(f"  {score.target}:{mutant.site.line}  {mutant.site.operator}  {mutant.site.description}")
    return "\n".join(lines)
