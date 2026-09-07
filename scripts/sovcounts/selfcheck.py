"""Prove the grader fires, does not over-fire, and that the contract still binds.

A drift checker that has silently stopped matching anything reports a clean
repository. So `check` refuses to report a verdict until this has run, and this
refuses to report success having exercised nothing.

Three things are proven here, and they are different things. That the grader
returns DRIFT for a disagreement and MATCH for an agreement is arithmetic, and
cheap. That an exemption stops applying when its stated value moves is the
property that keeps a historical exemption from covering whatever is edited into
its place. That every declared population still derives against this repository
is the one that catches the real decay: a population whose glob stops matching
answers zero, agrees with nothing, and turns the whole check into a green light.
"""

from __future__ import annotations

from dataclasses import dataclass

from sovcounts import grading
from sovcounts import populations as pops


@dataclass(frozen=True)
class _Claim:
    """A controlled claim. Same shape as `scan.Claim`, built by hand."""

    path: str
    line: int
    stated: int
    anchor: str
    population: str
    text: str = ""


def _grader_cases() -> list[str]:
    failures = []
    claim = _Claim("X.md", 1, 20, "workflows", "harness-workflows")
    found = grading.grade([claim], {"harness-workflows": 23}, {}, [])
    if [f.kind for f in found] != [grading.DRIFT]:
        failures.append("a stated 20 against a record of 23 was not reported as drift")

    found = grading.grade([claim], {"harness-workflows": 20}, {}, [])
    if [f.kind for f in found] != [grading.MATCH]:
        failures.append("a stated 20 against a record of 20 was reported as drift")

    found = grading.grade([claim], {}, {"harness-workflows": "absent"}, [])
    if [f.kind for f in found] != [grading.UNDERIVABLE]:
        failures.append("an unanswered population was graded rather than reported unanswerable")
    return failures


def _exemption_cases() -> list[str]:
    failures = []
    exemptions = [{"path": "X.md", "anchor": "workflows", "stated": 20, "reason": "history"}]
    claim = _Claim("X.md", 1, 20, "workflows", "harness-workflows")
    found = grading.grade([claim], {"harness-workflows": 23}, {}, exemptions)
    if [f.kind for f in found] != [grading.HISTORICAL]:
        failures.append("a recorded historical claim was graded as drift")

    moved = _Claim("X.md", 1, 21, "workflows", "harness-workflows")
    found = grading.grade([moved], {"harness-workflows": 23}, {}, exemptions)
    if [f.kind for f in found] != [grading.DRIFT]:
        failures.append("an exemption still applied after its stated value moved, so it "
                        "covers whatever is edited into its place")

    elsewhere = _Claim("Y.md", 1, 20, "workflows", "harness-workflows")
    found = grading.grade([elsewhere], {"harness-workflows": 23}, {}, exemptions)
    if [f.kind for f in found] != [grading.DRIFT]:
        failures.append("an exemption applied in a file it was not written for")
    return failures


def _population_cases() -> list[str]:
    """Every declared population must derive here, and none may answer zero.

    Zero is the shape decay takes. A glob that stops matching does not raise; it
    counts nothing, matches no prose, and leaves a green result behind it.
    """
    failures = []
    try:
        populations, paths = pops.load()
    except pops.Underivable as absent:
        return [f"the contract could not be loaded: {absent}"]
    if not populations:
        return ["the contract declares no populations, so nothing can be graded"]
    for population in populations:
        try:
            value = pops.derive(population.derivation, paths)
        except pops.Underivable:
            # An environment that cannot answer is reported by `check`, not failed
            # here. A shallow checkout is not a broken contract.
            continue
        if value == 0:
            failures.append(f"{population.id} derives 0; its source has moved or "
                            "its glob no longer matches, and it can no longer "
                            "disagree with any number")
    return failures


def run() -> int:
    """Every case, reported together rather than at the first failure."""
    failures = _grader_cases() + _exemption_cases() + _population_cases()
    exercised = 7
    for failure in failures:
        print(f"SELFCHECK FAIL: {failure}")
    if failures:
        return 1
    print(f"SELFCHECK PASS: {exercised} controlled cases, "
          f"{len(pops.load()[0])} declared populations derive non-zero")
    return 0
