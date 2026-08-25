"""Typed, expiring, session-bound authority for the asset service.

A grant is live or it is nothing. Every grant carries an expiry, and `authorized`
refuses one that has expired, been revoked, or whose session has closed. An
issuer other than the recorded root may only issue what one of its own live
grants already covers - same capability, no wider scope, no later expiry - so
delegation attenuates and can never widen.

Before this module a grant row had `created_at` and no expiry, and the only
disqualifier was `revoked`, which made every grant ever issued a permanent
credential. A store written under that schema migrates with `expires_at = 0`, so
those grants read as expired rather than silently outliving the rule.

Defaults taken (`AGENTS.md`, Self-direction is not delegation): the root issuer
is whoever issues the first grant against an empty store, recorded once and
inspectable afterwards. That is a mechanism for making the first issuer visible,
not an answer to O3 (what bootstrap authority attests the first attestor), which
stays open.
"""

from __future__ import annotations

from typing import Any
import sqlite3

from soveraeign_asset_service.store import Store, new_id


DEFAULT_GRANT_TTL_SECONDS = 900.0
DEFAULT_SESSION_TTL_SECONDS = 3600.0

SCHEMA = """
CREATE TABLE IF NOT EXISTS grants(
  id TEXT PRIMARY KEY, actor TEXT NOT NULL, capability TEXT NOT NULL,
  scope TEXT NOT NULL, revoked INTEGER NOT NULL DEFAULT 0,
  created_at REAL NOT NULL, expires_at REAL NOT NULL DEFAULT 0,
  issuer TEXT NOT NULL DEFAULT '', session_id TEXT);
CREATE TABLE IF NOT EXISTS sessions(
  id TEXT PRIMARY KEY, participant TEXT NOT NULL, model_identity TEXT NOT NULL,
  started_at REAL NOT NULL, expires_at REAL NOT NULL, ended_at REAL);
CREATE TABLE IF NOT EXISTS authority_root(
  singleton INTEGER PRIMARY KEY CHECK(singleton = 1),
  issuer TEXT NOT NULL, established_at REAL NOT NULL);
"""

MIGRATIONS = (
    ("expires_at", "ALTER TABLE grants ADD COLUMN expires_at REAL NOT NULL DEFAULT 0"),
    ("issuer", "ALTER TABLE grants ADD COLUMN issuer TEXT NOT NULL DEFAULT ''"),
    ("session_id", "ALTER TABLE grants ADD COLUMN session_id TEXT"),
)


class AuthorityRefused(PermissionError):
    """An actor lacks a live grant for the capability and scope it attempted."""


class Authority:
    """Grants and sessions for one service root.

    Every refusal writes a receipt before it raises, so a refused attempt is as
    inspectable as a committed one.
    """

    def __init__(self, store: Store) -> None:
        self.store = store
        self.db = store.db
        self.now = store.now
        self._schema()

    def _schema(self) -> None:
        """Bring a store written before grants expired up to the current shape."""
        columns = {row["name"] for row in self.db.execute("PRAGMA table_info(grants)")}
        for column, statement in MIGRATIONS:
            if column not in columns:
                self.db.execute(statement)

    # -- sessions ---------------------------------------------------------

    def open_session(self, participant: str, model_identity: str,
                     ttl_seconds: float = DEFAULT_SESSION_TTL_SECONDS) -> str:
        """Start a bounded session for one participant and its model identity."""
        now = self.now()
        session = new_id("session")
        self.db.execute("INSERT INTO sessions VALUES(?,?,?,?,?,NULL)",
                        (session, participant, model_identity, now, now + ttl_seconds))
        self.store.receipt("COMMITTED", "session.open", "session", session, participant,
                           {"model_identity": model_identity, "expires_at": now + ttl_seconds})
        self.db.commit()
        return session

    def close_session(self, session_id: str, actor: str) -> str:
        """End a session. Every grant bound to it stops authorizing immediately."""
        if self.session(session_id) is None:
            raise KeyError(session_id)
        self.db.execute("UPDATE sessions SET ended_at=? WHERE id=? AND ended_at IS NULL",
                        (self.now(), session_id))
        bound = self.db.execute("SELECT COUNT(*) FROM grants WHERE session_id=?",
                                (session_id,)).fetchone()[0]
        receipt = self.store.receipt("COMMITTED", "session.close", "session", session_id,
                                     actor, {"grants_bound": bound})
        self.db.commit()
        return receipt

    def session(self, session_id: str) -> sqlite3.Row | None:
        """The session row, whether or not it is still live."""
        return self.db.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()

    def session_live(self, session_id: str) -> bool:
        """A session is live while it is unclosed and unexpired."""
        row = self.session(session_id)
        return bool(row and row["ended_at"] is None and row["expires_at"] > self.now())

    # -- grants -----------------------------------------------------------

    def root_issuer(self) -> str | None:
        """The issuer recorded as this store's uncovered origin, if one is recorded yet."""
        row = self.db.execute("SELECT issuer FROM authority_root WHERE singleton=1").fetchone()
        return row["issuer"] if row else None

    def grant(self, issuer: str, actor: str, capability: str, scope: str = "*",
              ttl_seconds: float = DEFAULT_GRANT_TTL_SECONDS,
              session_id: str | None = None) -> str:
        """Issue a live grant, attenuated to what the issuer already holds.

        A grant bound to a session never outlives that session. An issuer other
        than the recorded root is refused unless one of its own live grants
        covers the capability, the scope, and the requested expiry.
        """
        now = self.now()
        expires_at = now + ttl_seconds
        if session_id is not None:
            if not self.session_live(session_id):
                self._refuse(issuer, actor, capability, scope, "SESSION_NOT_LIVE")
            expires_at = min(expires_at, self.session(session_id)["expires_at"])
        root = self.root_issuer()
        if root is None:
            self.db.execute("INSERT INTO authority_root VALUES(1,?,?)", (issuer, now))
        elif issuer != root and self._covering(issuer, capability, scope, expires_at) is None:
            self._refuse(issuer, actor, capability, scope, "GRANT_NOT_COVERED")
        grant = new_id("grant")
        self.db.execute("INSERT INTO grants VALUES(?,?,?,?,0,?,?,?,?)",
                        (grant, actor, capability, scope, now, expires_at, issuer, session_id))
        self.store.receipt("COMMITTED", "authority.grant", "grant", grant, issuer,
                           {"actor": actor, "capability": capability, "scope": scope,
                            "expires_at": expires_at, "session_id": session_id})
        self.db.commit()
        return grant

    def revoke(self, grant_id: str, actor: str) -> str:
        """Revoke one grant ahead of its expiry."""
        if self.db.execute("SELECT 1 FROM grants WHERE id=?", (grant_id,)).fetchone() is None:
            raise KeyError(grant_id)
        self.db.execute("UPDATE grants SET revoked=1 WHERE id=?", (grant_id,))
        receipt = self.store.receipt("COUNTERED", "authority.revoke", "grant", grant_id,
                                     actor, {"grant_id": grant_id})
        self.db.commit()
        return receipt

    def _live_grants(self, actor: str, capability: str) -> list[sqlite3.Row]:
        """Unrevoked, unexpired grants held by an actor, whose session still stands."""
        rows = self.db.execute(
            "SELECT * FROM grants WHERE actor=? AND capability=? AND revoked=0 AND expires_at>?",
            (actor, capability, self.now()),
        ).fetchall()
        return [row for row in rows
                if row["session_id"] is None or self.session_live(row["session_id"])]

    def _covering(self, issuer: str, capability: str, scope: str,
                  expires_at: float) -> sqlite3.Row | None:
        """A live grant of the issuer's that fully covers what it is trying to issue."""
        for row in self._live_grants(issuer, capability):
            if row["scope"] not in (scope, "*"):
                continue
            if row["expires_at"] < expires_at:
                continue
            return row
        return None

    def _refuse(self, issuer: str, actor: str, capability: str, scope: str,
                reason: str) -> None:
        self.store.receipt("REFUSED", "authority.grant", "grant", "none", issuer,
                           {"actor": actor, "capability": capability, "scope": scope,
                            "reason": reason})
        self.db.commit()
        raise AuthorityRefused(f"{issuer} may not issue {capability} for {scope}: {reason}")

    # -- checks -----------------------------------------------------------

    def authorized(self, actor: str, capability: str, scope: str) -> bool:
        """Whether the actor holds a live grant covering this capability and scope."""
        return any(row["scope"] in (scope, "*")
                   for row in self._live_grants(actor, capability))

    def require(self, actor: str, capability: str, scope: str,
                subject_type: str, subject_id: str) -> None:
        """Refuse the transition, with a receipt, unless the actor is authorized."""
        if self.authorized(actor, capability, scope):
            return
        self.store.receipt("REFUSED", "authority.check", subject_type, subject_id,
                           actor, {"required": capability, "scope": scope})
        self.db.commit()
        raise AuthorityRefused(f"{actor} lacks {capability} for {scope}")

    def grants(self) -> list[dict[str, Any]]:
        """Every grant row, live or not, in issue order."""
        return [dict(row) for row in
                self.db.execute("SELECT * FROM grants ORDER BY created_at,id")]
