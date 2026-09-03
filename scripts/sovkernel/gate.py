"""Grade the independent-observation and precondition gate for one covering grant.

Split out of `authority.py` on 2026-09-02, alongside `sovkernel.admission`, when
the Cedar spike (`reports/2026-09-03-cedar-authority-equivalence.md`) found
these clauses were never sent to Cedar at all: `OBSERVATION_MISSING`,
`OBSERVER_NOT_INDEPENDENT`, and `MISSING_PRECONDITION` are not an authority
decision over the grant's own attributes - they ask whether the *evidence
attached to this request* satisfies what the grant already decided it would
require. A build cannot witness itself (`AGENTS.md`, "Closure ownership"), and
this module is where that fact is checked.

Nothing here reads a file or knows a repository root. It is asked only once a
grant already covers the request; a grant that does not cover the request
never reaches this module.
"""

from __future__ import annotations

from sovkernel import authority


def _preconditions(grant: dict, request: dict) -> dict:
    """Compose grant-wide and capability-specific preconditions for this request."""
    common = grant.get("preconditions") or {}
    specific = (grant.get("preconditions_by_capability") or {}).get(
        request.get("capability"), {}
    )
    checks = list(dict.fromkeys(
        [*common.get("required_checks", ()), *specific.get("required_checks", ())]
    ))
    return {
        "required_checks": checks,
        "requires_independent_observation": bool(
            common.get("requires_independent_observation")
            or specific.get("requires_independent_observation")
        ),
    }


def _observation_verdict(grant: dict, request: dict) -> tuple[str, str] | None:
    """Check the independent-observation precondition, if this capability sets one."""
    preconditions = _preconditions(grant, request)
    if not preconditions["requires_independent_observation"]:
        return None
    evidence = request.get("evidence") or {}
    observation = evidence.get("observation")
    if not observation:
        return (authority.OBSERVATION_MISSING,
                "the grant requires an independent observation and the request carries none")
    if observation.get("contributed_to_build"):
        return (authority.OBSERVER_NOT_INDEPENDENT,
                f"observer {observation.get('observer_id')!r} contributed to the build it "
                "is offered as the observation of")
    if observation.get("verdict") != "CONFIRMED":
        return (authority.OBSERVATION_MISSING,
                f"the observation reads {observation.get('verdict')!r}, not CONFIRMED")
    return None


def _precondition_unmet(grant: dict, request: dict) -> str | None:
    """A required check absent from the evidence is absent, never satisfied."""
    preconditions = _preconditions(grant, request)
    evidence = (request.get("evidence") or {}).get("checks") or {}
    for name in preconditions["required_checks"]:
        result = evidence.get(name)
        if result is None:
            return f"required check {name!r} is not present in the request's evidence"
        if result != "PASS":
            return f"required check {name!r} reads {result!r}"
    return None
