"""Grade a page against derived values, and keep the two kinds of failure apart.

A claim can have DRIFTED, which is a statement about the page and fails. It can be
UNANSWERABLE here, which is a statement about the environment and does not fail: a
shallow CI checkout cannot count commits, and calling the page wrong on that basis
is the error this whole check exists to catch. Or it matches.

Nothing here reads a repository, and that is now enforced by the signature rather
than described in this paragraph. `grade` once defaulted both its arguments: with
them omitted it read `CLAUDE.md` and ran every deriver, so the sentence above was
false and `cmd_check` was taking exactly that path. A witness measured it — the
same synthetic page graded safely returned all UNANSWERABLE and graded through
the default returned all DRIFTED against real counts. Both arguments are required
now. The repository-reading path is `claims.page_text` and `claims.derive_all`,
which is where the sources already lived.
"""

from __future__ import annotations

from typing import NamedTuple
import re

from sovsnapshot import claims

DRIFTED = "DRIFTED"
UNANSWERABLE = "UNANSWERABLE"


class Finding(NamedTuple):
    """One claim's outcome, and whether it is about the page or about here."""

    kind: str
    claim: str
    detail: str


def read_claim(text: str, claim: claims.Claim) -> list[int]:
    """Every number the page states for this claim, in page order.

    All of them, not the first. `re.search` stops at the first match, so a stale
    sentence appended below the true one passed silently, which is L-0001's own
    failure moved further down the page.
    """
    return [int(m.group(1)) for m in re.finditer(claim.pattern, text)]


def grade(text: str, derived: dict[str, int],
          reasons: dict[str, str] | None = None) -> list[Finding]:
    """Grade a page against values already derived. Both are required.

    A claim absent from `derived` is unanswerable here, not drift. `reasons` only
    supplies the wording for that finding: it is the sole optional argument left,
    and omitting it degrades a message rather than changing a verdict.
    """
    findings = []
    for claim in claims.CLAIMS:
        stated = read_claim(text, claim)
        if not stated:
            findings.append(Finding(DRIFTED, claim.name,
                                    "the page states no number, so nothing can be "
                                    "checked against the record"))
            continue
        if len(set(stated)) > 1:
            # Before consulting the derived values: two numbers on one page
            # contradict each other whether or not anything here can say which is
            # right.
            findings.append(Finding(DRIFTED, claim.name,
                                    "the page states it more than once and the "
                                    f"statements disagree: {sorted(set(stated))}"))
            continue
        if claim.name not in derived:
            findings.append(Finding(UNANSWERABLE, claim.name,
                                    (reasons or {}).get(claim.name, "not derivable here")))
            continue
        actual = derived[claim.name]
        if abs(actual - stated[0]) > claim.tolerance:
            findings.append(Finding(DRIFTED, claim.name,
                                    f"page says {stated[0]}, record holds {actual}"
                                    + (f" (tolerance {claim.tolerance})"
                                       if claim.tolerance else "")))
    return findings


def drift(findings: list[Finding]) -> list[Finding]:
    """Only the findings that fail. The rest are about this environment."""
    return [f for f in findings if f.kind == DRIFTED]
