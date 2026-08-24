"""Payload custody and the receipt ledger for the asset service.

Two storage concerns the asset lifecycle depends on but does not own: immutable
payload bytes in a local content-addressed store, and the receipt table every
transition writes to. `core.py` reaches both through this object, so the
lifecycle module carries no storage mechanics.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any, Callable
import json
import sqlite3
import time
import uuid


SCHEMA = """
CREATE TABLE IF NOT EXISTS receipts(
  id TEXT PRIMARY KEY, outcome TEXT NOT NULL, event TEXT NOT NULL,
  subject_type TEXT NOT NULL, subject_id TEXT NOT NULL,
  actor TEXT NOT NULL, payload_json TEXT NOT NULL, created_at REAL NOT NULL);
"""


def new_id(prefix: str) -> str:
    """An opaque identifier carrying its object kind as a readable prefix."""
    return f"{prefix}_{uuid.uuid4().hex}"


class Store:
    """One service root: its SQLite connection, payload custody, and receipts.

    The clock is injectable because expiry and receipt ordering are observable in
    tests and in receipts (`AGENTS.md`, Python style: keep timestamps injectable).
    """

    def __init__(self, root: str | Path, clock: Callable[[], float] = time.time) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.blobs = self.root / "blobs" / "sha256"
        self.blobs.mkdir(parents=True, exist_ok=True)
        self.now = clock
        self.db = sqlite3.connect(self.root / "asset-service.sqlite3")
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA foreign_keys=ON")

    def apply_schema(self, *scripts: str) -> None:
        """Create every component's tables in one statement and land them in one commit.

        Each component owns its own DDL text; running them separately cost a
        parse and an fsync apiece, which the test suites pay on every
        construction. The service applies them together instead.
        """
        combined = SCHEMA
        for script in scripts:
            combined += script
        self.db.executescript(combined)
        self.db.commit()

    def close(self) -> None:
        """Close the underlying connection."""
        self.db.close()

    def receipt(self, outcome: str, event: str, subject_type: str, subject_id: str,
                actor: str, payload: dict[str, Any]) -> str:
        """Write one receipt row and return its identifier. The caller commits."""
        receipt = new_id("rcpt")
        self.db.execute(
            "INSERT INTO receipts VALUES(?,?,?,?,?,?,?,?)",
            (receipt, outcome, event, subject_type, subject_id, actor,
             json.dumps(payload, sort_keys=True), self.now()),
        )
        return receipt

    def store_blob(self, data: bytes) -> tuple[str, Path]:
        """Put bytes in the content-addressed store; refuse if that address holds other bytes."""
        digest = sha256(data).hexdigest()
        path = self.blobs / digest[:2] / digest
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_bytes(data)
        elif path.read_bytes() != data:
            raise RuntimeError("digest collision or corrupt blob")
        return digest, path

    def receipts(self) -> list[dict[str, Any]]:
        """Every receipt in write order."""
        return [dict(row) for row in
                self.db.execute("SELECT * FROM receipts ORDER BY created_at,id")]
