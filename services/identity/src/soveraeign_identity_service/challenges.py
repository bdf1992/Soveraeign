"""Challenge lifecycle: the passwordless verification mechanism (decisions/0048).

A challenge is the magic-link pattern expressed in primitives the system already
has. It is a lease: minted against one principal and one declared channel, fenced
by a token, expiring on a clock, presentable exactly once. Presenting a live
token inside its window is what upgrades an identity claim from `UNVERIFIED` to
`VERIFIED`; the presentation receipt is that claim's `verification_basis`
(ID-12, ID-13). Recovery is not a separate door: a lost credential is a fresh
challenge to the declared channel (ID-14).

Two properties are structural rather than promised:

- **The token never enters the record.** Only its digest is held, and only its
  digest is emitted. A journal, a receipt, or a leaked log therefore cannot
  replay a challenge (`AGENTS.md`, Secrets and local boundaries). The token
  exists in one place: the return of `mint`, which the caller hands to the
  channel and does not keep.
- **Nothing here is storage.** The clock and the token source are injected, and
  the in-memory map is a projection of the records this module emits. Whether
  identity is a service or a kernel registry is open (`decisions/0048`,
  judgement 3); this lifecycle is written so that ruling moves the file and
  changes no semantics.

Verification is not authority. A `VERIFIED` claim still grants nothing; every
consequential transition checks a live typed grant (ID-8, C3).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable
import hashlib
import hmac
import secrets

# Channel kinds the node itself controls. `external` is refused while
# `no_external_effects_in_phase_i` stands (O7); admitting it later changes this
# tuple and nothing else about the mechanism.
LOCAL_CHANNEL_KINDS = ("console-session", "local-file", "os-account")
EXTERNAL_CHANNEL_KIND = "external"

MINTED, PRESENTED, SPENT = "MINTED", "PRESENTED", "SPENT"

# Refusal reason codes. Proposed alongside decisions/0048; O10 owns whether
# SPEC.md adopts them.
CHANNEL_UNDECLARED = "CHANNEL_UNDECLARED"
CHANNEL_REFUSED = "CHANNEL_REFUSED"
PRINCIPAL_REVOKED = "PRINCIPAL_REVOKED"
TOKEN_UNKNOWN = "TOKEN_UNKNOWN"
CHALLENGE_EXPIRED = "CHALLENGE_EXPIRED"
CHALLENGE_SPENT = "CHALLENGE_SPENT"
PRINCIPAL_MISMATCH = "PRINCIPAL_MISMATCH"

DEFAULT_TTL_SECONDS = 600


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _stamp(moment: datetime) -> str:
    return moment.isoformat().replace("+00:00", "Z")


def _parse(stamp: str) -> datetime:
    """Read a stamp back. Expiry compares moments, never strings: an ISO-8601 stamp
    carrying microseconds sorts before the same second without them, so a string
    comparison would read a live challenge as expired."""
    return datetime.fromisoformat(stamp.replace("Z", "+00:00"))


def digest_of(token: str) -> str:
    """The only form of a token that may be recorded."""
    return "sha256:" + hashlib.sha256(token.encode("utf-8")).hexdigest()


@dataclass
class Challenge:
    """One minted challenge. Holds a token digest, never a token."""

    challenge_id: str
    principal_id: str
    channel_kind: str
    channel_reference: str
    token_digest: str
    minted_at: str
    expires_at: str
    state: str = MINTED
    presented_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Challenges:
    """Mint, deliver, and present challenges, emitting one record per attempt."""

    def __init__(self, clock: Callable[[], datetime] | None = None,
                 tokens: Callable[[], str] | None = None,
                 ids: Callable[[], str] | None = None) -> None:
        self._clock = clock or _utc_now
        self._tokens = tokens or (lambda: secrets.token_urlsafe(32))
        self._ids = ids or (lambda: f"challenge:{secrets.token_hex(8)}")
        self._challenges: dict[str, Challenge] = {}
        self._by_digest: dict[str, str] = {}
        self._records: list[dict[str, Any]] = []

    # -- reading -------------------------------------------------------------

    @property
    def records(self) -> list[dict[str, Any]]:
        """Every attempt, in order, for the caller to journal."""
        return list(self._records)

    def challenge(self, challenge_id: str) -> Challenge | None:
        return self._challenges.get(challenge_id)

    def _record(self, operation: str, outcome: str, challenge_id: str | None,
                principal_id: str, reason_code: str | None = None,
                **detail: Any) -> dict[str, Any]:
        entry = {"operation": operation, "outcome": outcome, "challenge_id": challenge_id,
                 "principal_id": principal_id, "reason_code": reason_code,
                 "occurred_at": _stamp(self._clock()), **detail}
        self._records.append(entry)
        return entry

    # -- transitions ---------------------------------------------------------

    def mint(self, principal: dict[str, Any], *, ttl_seconds: int = DEFAULT_TTL_SECONDS
             ) -> tuple[dict[str, Any], str | None]:
        """Mint a challenge for a principal's declared channel.

        Returns the record and the token. The token is returned exactly once and
        never stored; hand it to the channel and drop it. A refusal returns a
        record and ``None``.
        """
        principal_id = principal.get("principal_id", "")
        channel = principal.get("verification_channel")
        if principal.get("revoked") is not None:
            return self._record("mint", "REFUSED", None, principal_id,
                                PRINCIPAL_REVOKED), None
        if not channel:
            return self._record("mint", "REFUSED", None, principal_id,
                                CHANNEL_UNDECLARED), None
        kind = channel.get("kind")
        if kind == EXTERNAL_CHANNEL_KIND or kind not in LOCAL_CHANNEL_KINDS:
            return self._record("mint", "REFUSED", None, principal_id, CHANNEL_REFUSED,
                                channel_kind=kind), None
        now = self._clock()
        token = self._tokens()
        record = Challenge(
            challenge_id=self._ids(), principal_id=principal_id, channel_kind=kind,
            channel_reference=channel.get("reference", ""), token_digest=digest_of(token),
            minted_at=_stamp(now), expires_at=_stamp(now + timedelta(seconds=ttl_seconds)))
        self._challenges[record.challenge_id] = record
        self._by_digest[record.token_digest] = record.challenge_id
        return self._record("mint", "COMMITTED", record.challenge_id, principal_id,
                            channel_kind=kind, token_digest=record.token_digest,
                            expires_at=record.expires_at), token

    def deliver(self, challenge_id: str) -> dict[str, Any]:
        """Record the crossing that hands a token to its channel.

        Phase I channels are node-local, so the crossing is `RECORD_LOCAL` and
        this module performs no external effect. The delivery itself is the
        caller's: this records that it was owed and to which channel.
        """
        found = self._challenges.get(challenge_id)
        if found is None:
            return self._record("deliver", "REFUSED", challenge_id, "", TOKEN_UNKNOWN)
        return self._record("deliver", "COMMITTED", challenge_id, found.principal_id,
                            channel_kind=found.channel_kind,
                            channel_reference=found.channel_reference,
                            effect_class="RECORD_LOCAL")

    def present(self, token: str, principal: dict[str, Any]) -> dict[str, Any]:
        """Present a token once, inside its window, by the principal it was minted to.

        The lookup is by digest and the comparison is constant-time, so neither a
        stored value nor the time taken distinguishes a wrong token from a
        near-miss. The principal is required rather than inferred: a token names
        who it verifies, and a presenter who is not that principal is refused
        rather than quietly verified as its owner.
        """
        presented = digest_of(token)
        challenge_id = None
        for known_digest, known_id in self._by_digest.items():
            if hmac.compare_digest(known_digest, presented):
                challenge_id = known_id
                break
        if challenge_id is None:
            return self._record("present", "REFUSED", None, "", TOKEN_UNKNOWN)
        found = self._challenges[challenge_id]
        if found.state != MINTED:
            return self._record("present", "REFUSED", challenge_id, found.principal_id,
                                CHALLENGE_SPENT, state=found.state)
        now = self._clock()
        if now > _parse(found.expires_at):
            found.state = SPENT
            return self._record("present", "REFUSED", challenge_id, found.principal_id,
                                CHALLENGE_EXPIRED, expires_at=found.expires_at)
        if principal.get("principal_id") != found.principal_id:
            found.state = SPENT
            return self._record("present", "REFUSED", challenge_id, found.principal_id,
                                PRINCIPAL_MISMATCH,
                                presented_by=principal.get("principal_id"))
        if principal.get("revoked") is not None:
            found.state = SPENT
            return self._record("present", "REFUSED", challenge_id, found.principal_id,
                                PRINCIPAL_REVOKED)
        found.state, found.presented_at = PRESENTED, _stamp(now)
        return self._record("present", "COMMITTED", challenge_id, found.principal_id,
                            token_digest=found.token_digest, verifies=found.principal_id)

    def verification_basis(self, challenge_id: str) -> str | None:
        """The reference a `VERIFIED` claim carries, once the challenge was presented."""
        found = self._challenges.get(challenge_id)
        if found is None or found.state != PRESENTED:
            return None
        return f"urn:soveraeign:challenge:{challenge_id}"
