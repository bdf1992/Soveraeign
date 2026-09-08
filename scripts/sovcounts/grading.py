"""Grade stated numbers against derived ones. Pure: it reaches no repository.

Both arguments are required and neither is a path, for the reason
`sovsnapshot/grading.py` gives: a grader that can reach the record can be tested
against the record it just read, which proves nothing. Everything here is decided
from values passed in.
"""

from __future__ import annotations

from dataclasses import dataclass

DRIFT = "DRIFT"
UNDERIVABLE = "UNDERIVABLE"
HISTORICAL = "HISTORICAL"
MATCH = "MATCH"


@dataclass(frozen=True)
class Finding:
    """One verdict about one stated number."""

    kind: str
    path: str
    line: int
    population: str
    stated: int
    actual: int | None
    anchor: str
    detail: str


def exempt(claim, exemptions) -> str | None:
    """The recorded reason this stated number is history, or None.

    Matched on path, anchor and the exact stated value rather than on a line
    number. Editing the sentence changes the value and the exemption stops
    applying, so an exemption cannot outlive the claim it was written for.
    """
    for entry in exemptions:
        if (entry.get("path") == claim.path
                and entry.get("anchor") == claim.anchor
                and entry.get("stated") == claim.stated):
            return entry.get("reason", "recorded as historical")
    return None


def grade(claims, values: dict[str, int], reasons: dict[str, str], exemptions) -> list[Finding]:
    """One finding per claim, in the order the claims were read."""
    findings = []
    for claim in claims:
        history = exempt(claim, exemptions)
        if history is not None:
            findings.append(Finding(HISTORICAL, claim.path, claim.line, claim.population,
                                    claim.stated, None, claim.anchor, history))
            continue
        if claim.population not in values:
            findings.append(Finding(UNDERIVABLE, claim.path, claim.line, claim.population,
                                    claim.stated, None, claim.anchor,
                                    reasons.get(claim.population, "no derivation answered")))
            continue
        actual = values[claim.population]
        kind = MATCH if actual == claim.stated else DRIFT
        findings.append(Finding(kind, claim.path, claim.line, claim.population,
                                claim.stated, actual, claim.anchor,
                                f"the record holds {actual}"))
    return findings


def drifted(findings) -> list[Finding]:
    """Only the findings that are a page disagreeing with the record."""
    return [f for f in findings if f.kind == DRIFT]
