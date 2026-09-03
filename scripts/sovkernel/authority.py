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
reasoning past the point where it was a detail of grant evaluation. Whether one
grant's own attributes admit a request at all is `sovkernel.admission`, and
whether the evidence attached to the request satisfies what a covering grant
requires is `sovkernel.gate`, both split out on 2026-09-02 along the line the
Cedar spike drew: `admission` is every clause an off-the-shelf policy engine
already expressed, `gate` is the two clauses that are not an authority decision
over the grant at all (`reports/2026-09-03-cedar-authority-equivalence.md`).
`evaluate` still reads as one function, calling each module in the same order
it always checked these clauses in.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

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


# Imported here, after the constants and `_instant` both modules read, rather
# than at module top: `admission` and `gate` each import this module back for
# those symbols, and the constants must already exist on it when they do.
from sovkernel import admission  # noqa: E402
from sovkernel import gate  # noqa: E402


def _grant_unavailable(grant: dict, request: dict, now: datetime) -> str | None:
    """`scripts/sov_grant.py` reads this name directly (`cmd_list`'s liveness probe).

    Kept as a thin forward to `admission.unavailable` rather than moved outright
    so that caller does not have to import a second module for one call. A
    function rather than a module-level alias, so it resolves `admission`'s
    attribute at call time - after both modules have finished importing,
    whichever one a caller happened to import first.
    """
    return admission.unavailable(grant, request, now)


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
        reason = admission.unavailable(grant, request, now)
        if reason is None:
            covering = grant
            break
        considered.append({"grant_id": grant.get("grant_id"), "reason": reason})

    if covering is None:
        detail = "; ".join(f"{c['grant_id']}: {c['reason']}" for c in considered) \
            or "no grant was offered"
        return _refused(AUTHORITY_REFUSED, detail, considered)

    observation = gate._observation_verdict(covering, request)
    if observation is not None:
        return _refused(observation[0], observation[1], considered)

    unmet = gate._precondition_unmet(covering, request)
    if unmet is not None:
        return _refused(MISSING_PRECONDITION, unmet, considered)

    return {"verdict": PERMITTED, "code": None,
            "detail": f"covered by {covering['grant_id']}",
            "grant_id": covering["grant_id"], "considered": considered}
