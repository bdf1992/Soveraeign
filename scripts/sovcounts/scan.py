"""Find count claims in live prose, and the count-shaped sentences nothing declares.

Two outputs, and the second is the point. A check that reports only what it can
grade teaches a reader that what it stayed silent about was fine. This scanner
also returns every count-shaped sentence whose noun no population declares, so
coverage is visible as a list rather than inferred from a green result.

Prose is read from the working tree while populations are counted out of the
commit. That split is deliberate and matches `sovsnapshot`: someone correcting a
number is graded on the number they just wrote, not on the one that was committed
before they fixed it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

UNITS = {word: value for value, word in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen "
    "fourteen fifteen sixteen seventeen eighteen nineteen".split())}
TENS = {word: (index + 2) * 10 for index, word in enumerate(
    "twenty thirty forty fifty sixty seventy eighty ninety".split())}

_WORD_ALTERNATIVES = "|".join(
    sorted(list(TENS) + list(UNITS), key=len, reverse=True))
#: A hyphenated compound is one token here (`forty-nine`), because that is how the
#: repository writes it and a pattern that stopped at `forty` would grade the wrong
#: number against the right population.
NUMBER = rf"(?:\d{{1,5}}|(?:{_WORD_ALTERNATIVES})(?:-(?:{'|'.join(UNITS)}))?)"

#: A count-shaped sentence is a number followed by a plural common noun. The noun
#: pattern is deliberately loose: this half is looking for what nobody declared, and
#: a tight pattern would go short by exactly the shapes nobody thought to list.
CANDIDATE = re.compile(rf"\b({NUMBER})\s+((?:[a-z][a-z-]*\s+){{0,2}}?[a-z][a-z-]*s)\b")


@dataclass(frozen=True)
class Claim:
    """One number written into prose, and the population its wording names."""

    path: str
    line: int
    stated: int
    anchor: str
    population: str
    text: str


@dataclass(frozen=True)
class Candidate:
    """A count-shaped sentence no population declares. Reported, never failed."""

    path: str
    line: int
    stated: int
    noun: str
    text: str


def value_of(token: str) -> int | None:
    """The integer a number token states, or None when it states none."""
    token = token.lower()
    if token.isdigit():
        return int(token)
    if token in UNITS:
        return UNITS[token]
    if token in TENS:
        return TENS[token]
    if "-" in token:
        tens, _, units = token.partition("-")
        if tens in TENS and units in UNITS:
            return TENS[tens] + UNITS[units]
    return None


def live_files(paths: list[str], frozen: tuple[str, ...]) -> list[str]:
    """Committed prose that describes current state rather than recording history."""
    return [p for p in paths
            if p.endswith(".md") and not any(p.startswith(f) for f in frozen)]


def _anchors(populations) -> list[tuple[str, str, object, bool]]:
    """Every declared anchor, with whether that anchor is a scoped one.

    Specificity decides, and it decides in two directions. A longer anchor beats a
    shorter one, so `declared Record operations` is not read as `Record operations`.
    A scoped anchor beats an unscoped one of any length, because a population that
    declares where its bare wording is unambiguous knows something the general
    population does not: inside `services/gateway/`, `declared operations` means
    that manifest and cannot mean the repository's total.
    """
    listed = []
    for population in populations:
        for anchor in population.anchors:
            listed.append((anchor.lower(), anchor, population, False))
        for anchor in population.scoped_anchors:
            listed.append((anchor.lower(), anchor, population, True))
    return sorted(listed, key=lambda entry: (entry[3], len(entry[0])), reverse=True)


def scan(root: Path, files: list[str], populations, guard) -> tuple[list[Claim], list[Candidate]]:
    """Read every live file once, returning graded claims and uncovered candidates."""
    anchors = _anchors(populations)
    claims: list[Claim] = []
    candidates: list[Candidate] = []
    for relative in files:
        try:
            text = (root / relative).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            # A file the working tree does not hold, or holds as something other
            # than text, is not a claim about anything.
            continue
        for number, line in enumerate(text.splitlines(), 1):
            _read_line(relative, number, line, anchors, guard, claims, candidates)
    return claims, candidates


def _subset(before: str, guard: tuple[str, ...]) -> bool:
    """Whether the words before the number mark this as a count of a part.

    Only the last two words are consulted. A qualifier further back belongs to
    another clause, and reading the whole line would let any sentence containing
    `other` exempt every number in it.
    """
    tail = " ".join(before.lower().replace("`", " ").split()[-2:])
    return any(tail == word or tail.endswith(" " + word) or tail == word.split()[-1]
               for word in guard)


def _read_line(relative, number, line, anchors, guard, claims, candidates) -> None:
    lowered = line.lower()
    matched_spans: list[tuple[int, int]] = []
    for match in re.finditer(rf"\b({NUMBER})\s+", lowered):
        stated = value_of(match.group(1))
        if stated is None:
            continue
        tail = lowered[match.end():]
        best = None
        for lowered_anchor, anchor, population, scoped in anchors:
            if not tail.startswith(lowered_anchor):
                continue
            if not population.binds(relative, anchor):
                continue
            best = (lowered_anchor, anchor, population)
            break
        if best is None:
            continue
        lowered_anchor, anchor, population = best
        span = (match.start(), match.end() + len(lowered_anchor))
        matched_spans.append(span)
        if _subset(lowered[:match.start()], guard):
            # A count of a part, correctly stated. Reported as a candidate so the
            # sentence is still visible, never graded against the population total.
            candidates.append(
                Candidate(relative, number, stated, anchor + " (subset)", line.strip()))
            continue
        claims.append(Claim(relative, number, stated, anchor, population.id, line.strip()))
    for match in CANDIDATE.finditer(lowered):
        stated = value_of(match.group(1))
        if stated is None:
            continue
        if any(start <= match.start() < end for start, end in matched_spans):
            continue
        candidates.append(
            Candidate(relative, number, stated, match.group(2), line.strip()))
