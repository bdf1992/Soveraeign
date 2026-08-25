"""Payload custody and the receipt ledger for the asset service.

Two storage concerns the asset lifecycle depends on but does not own: immutable
payload bytes in a local content-addressed store, and the receipt table every
transition writes to. `core.py` reaches both through this object, so the
lifecycle module carries no storage mechanics.
"""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable


SCHEMA = """
CREATE TABLE IF NOT EXISTS receipts(
  id TEXT PRIMARY KEY, outcome TEXT NOT NULL, event TEXT NOT NULL,
  subject_type TEXT NOT NULL, subject_id TEXT NOT NULL,
  actor TEXT NOT NULL, payload_json TEXT NOT NULL, created_at REAL NOT NULL);
"""


class PayloadIntegrityError(RuntimeError):
    """Addressed bytes no longer match their recorded identity."""


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
            raise PayloadIntegrityError("digest collision or corrupt blob")
        return digest, path

    def store_addressed_blob(self, data: bytes) -> tuple[str, str]:
        """Store bytes and return a portable CAS address plus digest."""
        digest, _ = self.store_blob(data)
        return f"cas:sha256:{digest}", f"sha256:{digest}"

    def verified_address(self, address: str, digest: str) -> bytes:
        """Resolve a local CAS address only when it agrees with its digest."""
        if not isinstance(digest, str) or not digest.startswith("sha256:"):
            raise PayloadIntegrityError("unsupported payload digest")
        hex_digest = digest.removeprefix("sha256:")
        if (
            len(hex_digest) != 64
            or any(character not in "0123456789abcdef" for character in hex_digest)
            or address != f"cas:{digest}"
        ):
            raise PayloadIntegrityError("payload address and digest disagree")
        path = self.blobs / hex_digest[:2] / hex_digest
        if not path.is_file():
            raise PayloadIntegrityError(f"missing addressed payload {address}")
        data = path.read_bytes()
        if sha256(data).hexdigest() != hex_digest:
            raise PayloadIntegrityError(f"addressed payload changed {address}")
        return data

    def verified_version(self, version_id: str) -> tuple[sqlite3.Row, bytes]:
        """Resolve an exact version and refuse bytes that no longer match it."""
        version = self.db.execute(
            "SELECT * FROM versions WHERE id=?", (version_id,)
        ).fetchone()
        if version is None:
            raise KeyError(version_id)
        expected_path = self.blobs / version["digest"][:2] / version["digest"]
        if Path(version["blob_path"]) != expected_path or not expected_path.is_file():
            raise PayloadIntegrityError(f"missing or displaced payload for {version_id}")
        data = expected_path.read_bytes()
        if sha256(data).hexdigest() != version["digest"] or len(data) != version["size"]:
            raise PayloadIntegrityError(f"payload identity changed for {version_id}")
        return version, data

    def receipts(self) -> list[dict[str, Any]]:
        """Every receipt in write order."""
        return [dict(row) for row in
                self.db.execute("SELECT * FROM receipts ORDER BY created_at,id")]
