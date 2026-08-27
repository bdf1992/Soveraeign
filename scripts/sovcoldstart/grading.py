"""How an answer is compared to a truth, and what counts as having been measured.

Split from the CLI so that the rules a score depends on sit in one readable place. Every
generosity in here was an exploit before it was removed: a substring match in either
direction, a fallback to the checked-in answer key when a probe failed, and a verdict the
participant supplied about its own prose.
"""

from __future__ import annotations

from typing import Any
import json

__all__ = ["UNMEASURED", "compare", "judge", "truth_for"]


def _norm(value: Any) -> Any:
    """Sorted token list, so a comma-joined answer and a JSON list compare as one thing.

    Normalised the same way `_flat` normalises, because the two disagreeing meant `exact`
    forgave a trailing period and `set_eq` refused it: `OPEN, BUILT.` was graded WRONG
    against `OPEN,BUILT`, and `OPEN -> BUILT` too. Nineteen questions are `set_eq`, nine of
    them tier 0, and a good answer refused is as bad a measurement as a bad one accepted.
    """
    if isinstance(value, (list, tuple)):
        items = [_flat(v) for v in value]
    else:
        items = [part for part in _flat(value).split(",") if part]
    return sorted(part for part in items if part)


def _flat(value: Any) -> str:
    """Case, spacing and arrow-versus-comma are not knowledge; strip them before comparing."""
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    text = text.replace("->", ",").replace("→", ",")
    text = " ".join(text.split()).strip().rstrip(".").upper()
    return ",".join(part.strip() for part in text.split(",") if part.strip())


def compare(expected: Any, actual: Any, grade: str, tol: int = 0) -> bool:
    """True when `actual` satisfies `expected` under the named grader."""
    if grade == "int_eq":
        return int(actual) == int(expected)
    if grade == "int_tol":
        return abs(int(actual) - int(expected)) <= int(tol)
    if grade == "set_eq":
        return _norm(expected) == _norm(actual)
    if grade == "contains":
        if isinstance(actual, (list, tuple)):
            return _flat(expected) in [_flat(v) for v in actual]
        return _flat(expected) in _flat(actual)
    return _flat(expected) == _flat(actual)


UNMEASURED = object()


def truth_for(question: dict[str, Any], status: str, actual: Any) -> Any:
    """What a participant answer is scored against, or UNMEASURED when nothing measured it.

    For a direct-value grader the probe wins, so a stale `expected` never marks a correct
    answer wrong. For `contains` it cannot: there the corpus `expected` is one member of
    what the probe returns - A09 expects `PREAPPROVAL_REQUESTED` while the probe returns
    all fourteen refusal codes - and scoring a one-token answer against the whole list
    fails every right answer.

    An errored or skipped probe returns UNMEASURED rather than falling back to the corpus.
    That fallback was an exploit: breaking a probe silently re-pointed its question at the
    answer key checked into this repository, so replacing every tier 0 probe with a pattern
    that cannot match, and answering from `corpus.json`, produced ADMISSIBLE and exit 0.
    `--fast` and `--offline` reached the same result without breaking anything.

    DRIFT is UNMEASURED for the same reason, found by a second witness: a `contains`
    question whose probe disagreed with the corpus was still scored against the corpus, so
    the run measured the key stale and then graded against it anyway. Nine of the 49 tier 0
    questions are `contains`-graded, and a stale one there teaches a wrong rule with the
    weight of a failed gate behind it.
    """
    if status in ("SKIPPED", "ERROR"):
        return UNMEASURED
    if question.get("grade") == "contains" or status == "MANUAL":
        return UNMEASURED if status == "DRIFT" else question["expected"]
    return actual


def judge(question: dict[str, Any], given: Any, truth: Any, owner_verdict: str | None) -> str:
    """Score one participant answer. Fuzzy string credit is refused on purpose.

    An earlier version accepted an answer whenever the truth was a substring of it OR the
    answer was a substring of the truth. The second direction meant the bare word `wrong`
    scored RIGHT on three of the ten defeating cases, and a single enum name scored RIGHT
    on every `set_eq` question. A grader that generous measures nothing.

    A question graded `manual` is not scored here at all. It returns UNGRADED unless the
    caller passes a verdict from a file the participant did not write, because a prose
    answer to a behavioural case is exactly the thing a string comparison cannot judge.

    An earlier version of this docstring said the verdict comes from the answer file. It
    does not, and it never should: 41 answers of `banana banana banana`, each carrying its
    own `owner_verdict: RIGHT`, scored tier 0 at 100%. `scoring.load_verdicts` is where the
    verdict comes from. The sentence describing the hole outlived the hole by a day and a
    witness caught it.
    """
    if truth is UNMEASURED:
        return "UNGRADED"
    if given is None:
        return "MISSING"
    if str(given).strip().upper().startswith("UNKNOWN"):
        return "ABSTAIN"
    if question.get("grade") == "manual":
        return owner_verdict if owner_verdict in ("RIGHT", "WRONG") else "UNGRADED"
    grade = question.get("grade", "exact")
    try:
        if grade == "contains":
            return "RIGHT" if answered(truth, given) else "WRONG"
        return "RIGHT" if compare(truth, given, grade, question.get("tol", 0)) else "WRONG"
    except (TypeError, ValueError):
        return "WRONG"


def answered(expected: Any, given: Any) -> bool:
    """Whether a participant actually gave this answer, for a `contains`-graded question.

    `contains` means two different things. Against a probe it means "expected is one member
    of the set the probe returned", which is right: A09 expects one refusal code and the
    probe returns all fourteen. Against a participant it means the participant named the
    term, and it took two witnesses to get that rule to hold.

    The first version scored RIGHT whenever the term appeared anywhere in the answer, so one
    339-character blob of prose took three tier 0 questions. The second let the answer be a
    comma-separated list, which changed the haystack from prose to commas and raised the
    yield: 886 tokens harvested from AGENTS.md and CLAUDE.md alone scored RIGHT on four tier
    0 questions, and a list of the 21 expected values scored 18 of 21.

    So the answer is the term. Not a list containing it, not prose containing it. That is
    what `verbs._shape` has told the participant all along: "one exact term or identifier".
    """
    want = _flat(expected)
    return bool(want) and _flat(given) == want
