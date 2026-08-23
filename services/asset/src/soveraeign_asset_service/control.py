"""Authority checks and terminal receipt recording for the Asset Service."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from .storage import new_id, now


class AuthorityRefused(PermissionError):
    """Raised after a missing scoped capability has been receipted."""


class ControlLedger:
    """Own authority lookup and receipt persistence without domain behavior."""

    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def receipt(
        self,
        outcome: str,
        event: str,
        subject_type: str,
        subject_id: str,
        actor: str,
        payload: dict[str, Any],
    ) -> str:
        """Append an attributable transition receipt and return its address."""
        receipt_id = new_id("rcpt")
        self.db.execute(
            "INSERT INTO receipts VALUES(?,?,?,?,?,?,?,?)",
            (
                receipt_id,
                outcome,
                event,
                subject_type,
                subject_id,
                actor,
                json.dumps(payload, sort_keys=True),
                now(),
            ),
        )
        return receipt_id

    def grant(self, issuer: str, actor: str, capability: str, scope: str = "*") -> str:
        """Record a provisional reference grant and its receipt."""
        grant_id = new_id("grant")
        self.db.execute(
            "INSERT INTO grants VALUES(?,?,?,?,0,?)",
            (grant_id, actor, capability, scope, now()),
        )
        self.receipt(
            "COMMITTED",
            "authority.grant",
            "grant",
            grant_id,
            issuer,
            {"actor": actor, "capability": capability, "scope": scope},
        )
        self.db.commit()
        return grant_id

    def require(
        self,
        actor: str,
        capability: str,
        scope: str,
        subject_type: str,
        subject_id: str,
    ) -> None:
        """Require one live matching grant or append a refusal receipt."""
        authorized = self.db.execute(
            "SELECT 1 FROM grants WHERE actor=? AND capability=? AND revoked=0 "
            "AND scope IN (?, '*') LIMIT 1",
            (actor, capability, scope),
        ).fetchone()
        if authorized is not None:
            return
        self.receipt(
            "REFUSED",
            "authority.check",
            subject_type,
            subject_id,
            actor,
            {"required": capability, "scope": scope},
        )
        self.db.commit()
        raise AuthorityRefused(f"{actor} lacks {capability} for {scope}")
