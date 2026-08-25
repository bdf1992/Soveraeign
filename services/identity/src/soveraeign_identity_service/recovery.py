"""Sealed recovery secrets: the one root-recovery mechanism this stack can carry.

A challenge (`challenges.py`) is short-lived and delivered on demand. That is
exactly what recovery cannot be: at the moment you need it, the channel you
would deliver over is the thing you lost. So a recovery secret is the inverse —
delivered once at enrollment, held outside the node by the human, redeemable
whenever. It has no expiry, and that is deliberate rather than an oversight of
ID-12: an expiring recovery secret expires precisely when it is not being
watched. What replaces expiry as the bound is single use, a finite set, and
revocation of the whole set at once.

Everything else is the same discipline as challenges: the secret is generated
here, returned exactly once, and never stored — only its digest is held and only
its digest is emitted, so a journal or a leaked log cannot redeem anything.

What this module deliberately does **not** do is decide that recovery secrets
are how the root recovers. `decisions/0048` ID-11 is Bdo's, and the paper's
physical custody is the whole question. This provides the mechanism any answer
of this shape would need, and one report the system owes regardless of the
answer: `unenrolled` names every principal that has no recovery at all, so the
gap is visible rather than discovered at the worst moment.

For the root the stakes differ in kind. The root has no controller, so nobody
can re-enroll it: if the root never enrolls, there is no recovery, and no
process can supply one afterwards.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Iterable
import hashlib
import hmac
import secrets

DEFAULT_SET_SIZE = 10

NOT_ENROLLED = "NOT_ENROLLED"
SECRET_UNKNOWN = "SECRET_UNKNOWN"
SECRET_SPENT = "SECRET_SPENT"
SET_REVOKED = "SET_REVOKED"
ALREADY_ENROLLED = "ALREADY_ENROLLED"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _stamp(moment: datetime) -> str:
    return moment.isoformat().replace("+00:00", "Z")


def digest_of(secret: str) -> str:
    """The only form of a recovery secret that may be recorded."""
    return "sha256:" + hashlib.sha256(secret.encode("utf-8")).hexdigest()


@dataclass
class RecoverySet:
    """One principal's enrolled recovery secrets, held as digests only."""

    principal_id: str
    enrolled_at: str
    live_digests: list[str] = field(default_factory=list)
    spent_digests: list[str] = field(default_factory=list)
    revoked_at: str | None = None

    @property
    def remaining(self) -> int:
        return 0 if self.revoked_at else len(self.live_digests)


class Recovery:
    """Enroll, redeem, and revoke sealed recovery secrets, recording every attempt."""

    def __init__(self, clock: Callable[[], datetime] | None = None,
                 secret_source: Callable[[], str] | None = None) -> None:
        self._clock = clock or _utc_now
        self._secrets = secret_source or (lambda: secrets.token_urlsafe(24))
        self._sets: dict[str, RecoverySet] = {}
        self._records: list[dict[str, Any]] = []

    @property
    def records(self) -> list[dict[str, Any]]:
        """Every attempt, in order, for the caller to journal."""
        return list(self._records)

    def _record(self, operation: str, outcome: str, principal_id: str,
                reason_code: str | None = None, **detail: Any) -> dict[str, Any]:
        entry = {"operation": operation, "outcome": outcome, "principal_id": principal_id,
                 "reason_code": reason_code, "occurred_at": _stamp(self._clock()), **detail}
        self._records.append(entry)
        return entry

    # -- transitions ---------------------------------------------------------

    def enroll(self, principal_id: str, *, count: int = DEFAULT_SET_SIZE
               ) -> tuple[dict[str, Any], list[str]]:
        """Generate a set of recovery secrets, returning them exactly once.

        Refuses to overwrite a live set: replacing recovery silently is how
        recovery is lost. Revoke first, deliberately, then enroll again.
        """
        existing = self._sets.get(principal_id)
        if existing is not None and existing.revoked_at is None:
            return self._record("enroll", "REFUSED", principal_id, ALREADY_ENROLLED,
                                remaining=existing.remaining), []
        issued = [self._secrets() for _ in range(count)]
        self._sets[principal_id] = RecoverySet(
            principal_id=principal_id, enrolled_at=_stamp(self._clock()),
            live_digests=[digest_of(secret) for secret in issued])
        return self._record("enroll", "COMMITTED", principal_id, count=count,
                            digests=[digest_of(secret) for secret in issued]), issued

    def redeem(self, principal_id: str, secret: str) -> dict[str, Any]:
        """Spend one recovery secret. Constant-time, single-use, receipted."""
        found = self._sets.get(principal_id)
        if found is None:
            return self._record("redeem", "REFUSED", principal_id, NOT_ENROLLED)
        if found.revoked_at is not None:
            return self._record("redeem", "REFUSED", principal_id, SET_REVOKED)
        presented = digest_of(secret)
        for known in list(found.live_digests):
            if hmac.compare_digest(known, presented):
                found.live_digests.remove(known)
                found.spent_digests.append(known)
                return self._record("redeem", "COMMITTED", principal_id,
                                    digest=known, remaining=found.remaining,
                                    exhausted=found.remaining == 0)
        for known in found.spent_digests:
            if hmac.compare_digest(known, presented):
                return self._record("redeem", "REFUSED", principal_id, SECRET_SPENT,
                                    digest=known)
        return self._record("redeem", "REFUSED", principal_id, SECRET_UNKNOWN)

    def revoke(self, principal_id: str, *, revoked_by: str, reason: str) -> dict[str, Any]:
        """Retire a whole set at once. Individual secrets are never revoked alone."""
        found = self._sets.get(principal_id)
        if found is None:
            return self._record("revoke", "REFUSED", principal_id, NOT_ENROLLED)
        if found.revoked_at is not None:
            return self._record("revoke", "REFUSED", principal_id, SET_REVOKED)
        found.revoked_at = _stamp(self._clock())
        found.live_digests.clear()
        return self._record("revoke", "COMMITTED", principal_id, revoked_by=revoked_by,
                            reason=reason)

    # -- reading -------------------------------------------------------------

    def status(self, principal_id: str) -> dict[str, Any]:
        found = self._sets.get(principal_id)
        if found is None:
            return {"principal_id": principal_id, "enrolled": False, "remaining": 0,
                    "revoked": False}
        return {"principal_id": principal_id, "enrolled": found.revoked_at is None,
                "remaining": found.remaining, "revoked": found.revoked_at is not None,
                "enrolled_at": found.enrolled_at}

    def unenrolled(self, principals: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        """Name every principal with no live recovery, root first.

        This is the report the system owes whatever Bdo rules at ID-11. A root
        with no recovery enrolled is not an error the system can fix — nobody is
        above it to re-enroll — so the only honest handling is to say so, loudly
        and continuously, rather than discover it at the worst moment.
        """
        gaps = []
        for principal in principals:
            principal_id = principal.get("principal_id", "")
            state = self.status(principal_id)
            if state["enrolled"] and state["remaining"] > 0:
                continue
            is_root = principal.get("controller") is None
            gaps.append({
                "principal_id": principal_id, "is_root": is_root,
                "remaining": state["remaining"], "revoked": state["revoked"],
                "consequence": ("no recovery exists and none can be supplied: the root "
                                "has no controller to re-enroll it")
                if is_root else "recoverable by its controller re-enrolling it",
            })
        gaps.sort(key=lambda gap: (not gap["is_root"], gap["principal_id"]))
        return gaps
