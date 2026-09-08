"""Evaluate a request against the authority grants that might cover it.

`SPEC.md` declares the `AuthorityGrant` object and requires that an authority
check evaluate type, capability, scope, budget, time, and revocation at the
attempted transition (PROD-I-5). This module is that check, and nothing more:
it reads no files, writes no state, and grants nothing. A grant is data; the
caller loads it and the caller performs whatever the verdict permits.

Refusal codes are the ones `contracts/kernel-transitions.json` already declares.
No synonym is minted here: an out-of-scope path, an expired grant, an exhausted
budget, and a missing grant are all `AUTHORITY_REFUSED`, distinguished by the
detail sentence rather than by a second vocabulary.

Whether a request path is one the grant's scope reaches is `sovkernel.scope`,
split out on 2026-08-25 when five rounds of witness dissent had grown that
reasoning past the point where it was a detail of grant evaluation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sovkernel.scope import out_of_scope

PERMITTED = "PERMITTED"
REFUSED = "REFUSED"

AUTHORITY_REFUSED = "AUTHORITY_REFUSED"
MISSING_PRECONDITION = "MISSING_PRECONDITION"
OBSERVATION_MISSING = "OBSERVATION_MISSING"
OBSERVER_NOT_INDEPENDENT = "OBSERVER_NOT_INDEPENDENT"

#: Heavier classes contain lighter ones. A grant's ceiling admits every class at
#: or below its own index and refuses everything above it.
EFFECT_ORDER = ("RECORD_LOCAL", "RESOURCE_CONSUMPTION", "EXTERNAL_WORLD")

#: JUDGEMENT authority may be issued by the owner and by nobody else.
JUDGEMENT_ISSUER = "bdo"


class GrantError(ValueError):
    """A grant or request was malformed enough that no verdict is honest."""


def _instant(value: str, field: str) -> datetime:
    """Parse an ISO-8601 instant, accepting the trailing Z form."""
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise GrantError(f"{field} is not an ISO-8601 instant: {value!r}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _branch_refused(grant: dict, request: dict) -> str | None:
    """A grant that names branches reaches no others."""
    branches = grant["scope"].get("branches")
    branch = request.get("branch")
    if branches is None or branch is None:
        return None
    if branch not in branches:
        return f"branch {branch} is not among the branches the grant admits"
    return None


def _budget_exceeded(grant: dict, request: dict) -> str | None:
    """Compare declared spend against the grant's ceiling in its own unit."""
    budget = grant["budget"]
    ceiling = budget.get("ceiling")
    if ceiling is None:
        return None
    spend = request.get("spend")
    if not spend:
        return None
    if spend.get("unit") != budget.get("unit"):
        return (f"spend is measured in {spend.get('unit')!r} and the grant's budget in "
                f"{budget.get('unit')!r}; the two cannot be compared")
    amount = spend.get("amount")
    if not isinstance(amount, int):
        raise GrantError("spend.amount must be an integer")
    if amount > ceiling:
        return f"{amount} {budget['unit']} against a ceiling of {ceiling}"
    return None


def _grant_unavailable(grant: dict, request: dict, now: datetime) -> str | None:
    """Every reason this one grant cannot cover this one request, or None."""
    if grant.get("status") != "RATIFIED":
        return f"grant is at {grant.get('status')} standing and has not been ratified"
    if grant.get("actor_id") != request.get("actor_id"):
        return f"grant names actor {grant.get('actor_id')!r}"
    if request.get("capability") not in grant.get("capabilities", ()):
        return f"grant does not carry the capability {request.get('capability')!r}"
    if grant.get("authority_type") == "JUDGEMENT" and grant.get("issuer_id") != JUDGEMENT_ISSUER:
        return (f"JUDGEMENT authority issued by {grant.get('issuer_id')!r}; only "
                f"{JUDGEMENT_ISSUER} may issue it")
    if grant.get("revoked_at"):
        return f"grant was revoked at {grant['revoked_at']}"
    if now < _instant(grant["valid_from"], "valid_from"):
        return f"grant is not valid until {grant['valid_from']}"
    if now >= _instant(grant["valid_until"], "valid_until"):
        return f"grant expired at {grant['valid_until']}"
    ceiling = grant.get("effect_ceiling")
    declared = request.get("effect_class")
    if declared not in EFFECT_ORDER:
        raise GrantError(f"request declares an unknown effect class: {declared!r}")
    if EFFECT_ORDER.index(declared) > EFFECT_ORDER.index(ceiling):
        return f"request declares {declared} against an effect ceiling of {ceiling}"
    return (out_of_scope(grant, request)
            or _branch_refused(grant, request)
            or _budget_exceeded(grant, request))


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


def _norm(path: str) -> str:
    """One spelling of a repository path, so a comparison is not decided by punctuation."""
    cleaned = str(path).replace("\\", "/").strip()
    while cleaned.startswith("./"):
        cleaned = cleaned[2:]
    return cleaned.strip("/")


def _covers(landed: str, target: str) -> bool:
    """Whether a landed path is, or contains, the target file.

    Compared on whole segments. An unanchored suffix match reads `docs/release-notes.json`
    as covering `notes.json`, refusing a landing over a file it never touched.
    """
    landed, target = _norm(landed), _norm(target)
    if not landed or not target:
        return False
    return landed == target or target.startswith(landed + "/")


def independence_basis(request: dict) -> str:
    """How this request established that its observer stayed outside the change.

    `contributed_to_build` is a boolean the observer sets about itself, and a gate reading
    it alone grades a declaration where a measurement was available.

    An earlier form returned MEASURED when the observer's own id appeared inside one of the
    landed paths. That read entanglement as evidence of independence - the same relation
    the refusal below treats as disqualifying - and was unreachable by any observer not
    named after a file. It now reports MEASURED only when the request carried the
    observation's real path, which is what turns the inside-the-change reading into a
    measurement rather than an account.
    """
    if not (request.get("evidence") or {}).get("observation"):
        return "DECLARED_ONLY"
    return "MEASURED" if _norm(str(request.get("observation_path") or "")) else "DECLARED_ONLY"


def _observed_path(request: dict) -> str | None:
    """The landed path that is, or contains, the observation file itself.

    An observation written into the set of paths being landed is inside the change it is
    offered as the reading of. The path comes from the request, which the landing tool
    knows. It never comes from a field inside the observation:
    `contracts/observation.schema.json` sets additionalProperties false, so an
    `observation_file` key cannot legitimately be there and the refusal that read one
    could never fire.
    """
    written = _norm(str(request.get("observation_path") or ""))
    if not written:
        return None
    for path in (request.get("paths") or []):
        if _covers(str(path), written):
            return str(path)
    return None


def _observation_verdict(grant: dict, request: dict) -> tuple[str, str] | None:
    """Check the independent-observation precondition, if this capability sets one."""
    preconditions = _preconditions(grant, request)
    if not preconditions["requires_independent_observation"]:
        return None
    evidence = request.get("evidence") or {}
    observation = evidence.get("observation")
    if not observation:
        return (OBSERVATION_MISSING,
                "the grant requires an independent observation and the request carries none")

    observer = str(observation.get("observer_id") or "").strip()
    if not observer:
        return (OBSERVER_NOT_INDEPENDENT,
                "the observation names no observer, so nothing about its independence can "
                "be established, declared or measured")
    if observer == str(request.get("actor_id") or ""):
        return (OBSERVER_NOT_INDEPENDENT,
                f"observer {observer!r} is the actor exercising this grant; a build cannot "
                "witness itself")
    inside = _observed_path(request)
    if inside:
        return (OBSERVER_NOT_INDEPENDENT,
                f"the observation at {inside!r} is among the paths being landed, so it is "
                "inside the change it is offered as the reading of")
    if observation.get("contributed_to_build"):
        return (OBSERVER_NOT_INDEPENDENT,
                f"observer {observer!r} contributed to the build it "
                "is offered as the observation of")
    if observation.get("verdict") != "CONFIRMED":
        return (OBSERVATION_MISSING,
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


def _refused(code: str, detail: str, considered: list[dict]) -> dict[str, Any]:
    return {"verdict": REFUSED, "code": code, "detail": detail, "grant_id": None,
            "considered": considered}


def evaluate(grants: list[dict], request: dict) -> dict[str, Any]:
    """Grade one request against every grant that might cover it.

    Returns a verdict of PERMITTED with the covering `grant_id`, or REFUSED with
    one of the kernel's declared refusal codes and the sentence that earned it.
    When several grants could apply, the first that covers the request wins and
    the rest are reported under `considered` so a reader can see why they did
    not.
    """
    now = _instant(request["at"], "at")
    considered: list[dict] = []
    covering: dict | None = None
    for grant in grants:
        reason = _grant_unavailable(grant, request, now)
        if reason is None:
            covering = grant
            break
        considered.append({"grant_id": grant.get("grant_id"), "reason": reason})

    if covering is None:
        detail = "; ".join(f"{c['grant_id']}: {c['reason']}" for c in considered) \
            or "no grant was offered"
        return _refused(AUTHORITY_REFUSED, detail, considered)

    observation = _observation_verdict(covering, request)
    if observation is not None:
        return _refused(observation[0], observation[1], considered)

    unmet = _precondition_unmet(covering, request)
    if unmet is not None:
        return _refused(MISSING_PRECONDITION, unmet, considered)

    return {"verdict": PERMITTED, "code": None,
            "detail": f"covered by {covering['grant_id']}",
            "grant_id": covering["grant_id"], "considered": considered}
