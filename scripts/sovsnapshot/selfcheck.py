"""Prove the grader fails on a drifted page and passes on a truthful one.

A check whose own correctness is unchecked is the failure `sov_snapshot` exists to
name, and this module has had to earn that twice. A witness broke `grade` to
return an empty list and watched the check print PASS; later, on a tree where
nothing was derivable, every case was satisfied by both sides saying nothing and
the selfcheck reported success having exercised nothing at all.

So: `check` runs this first, every time, and this refuses rather than passing when
it derived nothing.
"""

from __future__ import annotations

from typing import NamedTuple

from sovsnapshot import claims
from sovsnapshot import grading

#: What a synthetic page states for a claim nothing could derive. Any integer is
#: indistinguishable from a real count by looking at the page - an empty `reports/`
#: legitimately derives 0 - so the safety does not come from the value. It comes
#: from `grading.grade` requiring a derived set, which is now its signature rather
#: than a convention observed at some call sites.
PLACEHOLDER = 0

#: The slots the synthetic page has prose for. Renaming a claim without renaming
#: its slot raised `KeyError` out of `page` - a traceback rather than a reported
#: failure, and invisible to a reference walk that reads attributes and calls
#: rather than dict keys. Checked in `run`, not at import: a library that raises at
#: import decides the exit code of everything that imports it, including the
#: reference walk that loads every module in this package, and a guard nothing can
#: run without dying is a guard no test can prove.
PAGE_SLOTS = ("verification checks", "declared operations", "service boundaries",
              "manifests", "agent definitions", "skills", "workflows", "commits",
              "decision records", "reports")


def slots_match_claims() -> str | None:
    """The mismatch, if the page has prose for a different set than is declared."""
    declared = {claim.name for claim in claims.CLAIMS}
    if set(PAGE_SLOTS) == declared:
        return None
    return (f"the synthetic page has prose for {sorted(PAGE_SLOTS)} and the declared "
            f"claims are {sorted(declared)}; the page addresses its slots by name")


class SyntheticPage(NamedTuple):
    """A page and the values it was asked to state."""

    text: str
    values: dict[str, int]


def page(**stated: int) -> SyntheticPage:
    """A synthetic page stating one number for every declared claim, always.

    Every claim, without exception. An earlier version omitted a sentence when one
    of the three claims sharing it was underivable, which silently discarded the
    other two: it returned "." and exercised nothing. A synthetic page that states
    fewer claims than it was asked to is how a selfcheck passes while testing
    nothing.
    """
    value = {name: stated.get(name, PLACEHOLDER) for name in PAGE_SLOTS}

    def slot(name: str) -> int:
        """A slot the declared claims no longer hold is reported, never raised."""
        return value.get(name, PLACEHOLDER)

    return SyntheticPage(
        f"runs {slot('verification checks')} checks ... "
        f"{slot('service boundaries')} service boundaries under services/, "
        f"{slot('declared operations')} declared operations "
        f"across {slot('manifests')} manifests. Harness: "
        f"{slot('agent definitions')} agent definitions, {slot('skills')} skills, "
        f"{slot('workflows')} workflows. "
        f"it now holds {slot('commits')} commits, "
        f"{slot('decision records')} decision records "
        f"and {slot('reports')} reports.",
        dict(stated))


def shift(stated: dict[str, int], by: int) -> dict[str, int]:
    """The same claims, every number moved, so no value can collide with a real one.

    The duplicate-detection case once used literals, and on a shallow clone the
    real commit count is 1, so the two statements agreed and the case failed for
    the wrong reason. Every claim shifts, including ones nothing derived: shifting
    only the derived ones left an underivable claim holding `PLACEHOLDER` on both
    sides, which is the same collision one layer down.
    """
    return {claim.name: stated.get(claim.name, PLACEHOLDER) + by
            for claim in claims.CLAIMS}


def run() -> int:
    """Grade the declared cases. Returns 0 when the grader is sound."""
    answered = claims.derive_all()
    derived = answered.values
    for name, missing in answered.reasons.items():
        print(f"NOT SELF-DERIVED: {name} - {missing}")

    truthful = page(**derived)
    total = len(claims.CLAIMS)
    derivable = len(derived)

    # One claim held back on purpose, so unanswerability is exercised wherever this
    # runs. The previous case asserted `all(kind == UNANSWERABLE)` over an empty
    # list on a full clone, which is vacuously true and identical to the truthful
    # case - it proved nothing on the machine people develop on.
    withheld = next(iter(derived), None)
    partial = {name: value for name, value in derived.items() if name != withheld}

    cases = {
        "a truthful page is not reported as drifted":
            len(grading.drift(grading.grade(truthful.text, derived))) == 0,
        "every derivable claim is reported when every number is wrong":
            len(grading.drift(grading.grade(
                page(**shift(derived, 500)).text, derived))) == derivable,
        "a historical count on the same page is not read as the current one":
            len(grading.drift(grading.grade(
                "Day two ... 26 commits, 17 decision records, 8 reports. "
                + truthful.text, derived))) == 0,
        "a second, disagreeing statement further down the page is reported":
            len(grading.drift(grading.grade(
                truthful.text + " " + page(**shift(derived, 7)).text, derived))) == total,
        "a page stating no numbers at all is reported":
            len(grading.drift(grading.grade("", derived))) > 0,
        "a claim held back from the derived values is unanswerable, not drift":
            withheld is None or [f.kind for f in grading.grade(truthful.text, partial)
                                 if f.claim == withheld] == [grading.UNANSWERABLE],
        "holding one claim back does not silence a real drift in the others":
            withheld is None or len(grading.drift(grading.grade(
                page(**shift(derived, 500)).text, partial))) == derivable - 1,
    }
    if "commits" in derived:
        within = page(**dict(derived, commits=derived["commits"] + 20))
        cases["a count inside its declared tolerance is not reported"] = not any(
            f.claim == "commits" for f in grading.drift(
                grading.grade(within.text, derived)))

    failures = [description for description, held in cases.items() if not held]
    mismatch = slots_match_claims()
    if mismatch:
        failures.append(f"the page cannot state every claim: {mismatch}")
    for claim in claims.CLAIMS:
        if claim.tolerance > claims.MAX_TOLERANCE:
            failures.append(f"{claim.name}: tolerance {claim.tolerance} exceeds the "
                            f"ceiling of {claims.MAX_TOLERANCE}")

    # A selfcheck that derived nothing satisfies every case with both sides saying
    # nothing, and reports PASS having exercised nothing - precisely the failure
    # its own docstring claims to prevent.
    if not derived:
        print("FAIL no claim could be derived here, so nothing was exercised and this "
              "selfcheck proves nothing")
        return 1
    if failures:
        for line in failures:
            print(f"FAIL {line}")
        return 1
    print(f"PASS: {derivable} of {total} claims exercised, {len(cases)} cases")
    return 0
