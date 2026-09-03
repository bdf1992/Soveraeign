"""Decide whether one grant's own attributes admit a request at all.

Split out of `authority.py` on 2026-09-02, alongside `sovkernel.gate`, when the
Cedar spike (`reports/2026-09-03-cedar-authority-equivalence.md`) tiered the
authority corpus along exactly this line: status, actor, capability, JUDGEMENT
issuer, revocation, `valid_from`/`valid_until`, effect ceiling, branch, and
budget are the 14 `CEDAR`-tier clauses an off-the-shelf policy engine already
expresses; everything a request path selects is `sovkernel.scope`, unchanged;
and the observation verdict and precondition gate are `sovkernel.gate`.

Nothing here reads a file or knows a repository root. A grant is data; the
caller loads it and the caller performs whatever the verdict permits. This
module imports `sovkernel.authority` for its shared constants and helpers
rather than redefining them, so `GrantError`, the refusal codes, `EFFECT_ORDER`,
and `JUDGEMENT_ISSUER` stay importable from one place.
"""

from __future__ import annotations

from datetime import datetime

from sovkernel import authority
from sovkernel.scope import out_of_scope


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
        raise authority.GrantError("spend.amount must be an integer")
    if amount > ceiling:
        return f"{amount} {budget['unit']} against a ceiling of {ceiling}"
    return None


def unavailable(grant: dict, request: dict, now: datetime) -> str | None:
    """Every reason this one grant's own admission clauses refuse this request, or None.

    Checks status, actor, capability, JUDGEMENT issuer, revocation, the
    validity window, and the effect ceiling before deferring to path scope,
    branch, and budget, in that order - the same order `authority.evaluate`
    checked them in before this module existed.
    """
    if grant.get("status") != "RATIFIED":
        return f"grant is at {grant.get('status')} standing and has not been ratified"
    if grant.get("actor_id") != request.get("actor_id"):
        return f"grant names actor {grant.get('actor_id')!r}"
    if request.get("capability") not in grant.get("capabilities", ()):
        return f"grant does not carry the capability {request.get('capability')!r}"
    if (grant.get("authority_type") == "JUDGEMENT"
            and grant.get("issuer_id") != authority.JUDGEMENT_ISSUER):
        return (f"JUDGEMENT authority issued by {grant.get('issuer_id')!r}; only "
                f"{authority.JUDGEMENT_ISSUER} may issue it")
    if grant.get("revoked_at"):
        return f"grant was revoked at {grant['revoked_at']}"
    if now < authority._instant(grant["valid_from"], "valid_from"):
        return f"grant is not valid until {grant['valid_from']}"
    if now >= authority._instant(grant["valid_until"], "valid_until"):
        return f"grant expired at {grant['valid_until']}"
    ceiling = grant.get("effect_ceiling")
    declared = request.get("effect_class")
    if declared not in authority.EFFECT_ORDER:
        raise authority.GrantError(f"request declares an unknown effect class: {declared!r}")
    if authority.EFFECT_ORDER.index(declared) > authority.EFFECT_ORDER.index(ceiling):
        return f"request declares {declared} against an effect ceiling of {ceiling}"
    return (out_of_scope(grant, request)
            or _branch_refused(grant, request)
            or _budget_exceeded(grant, request))
