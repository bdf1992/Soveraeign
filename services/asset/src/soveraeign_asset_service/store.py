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

from soveraeign_asset_service.operational import OperationalJournal, mirror_receipt


SCHEMA = """
CREATE TABLE IF NOT EXISTS receipts(
  id TEXT PRIMARY KEY, outcome TEXT NOT NULL, event TEXT NOT NULL,
  subject_type TEXT NOT NULL, subject_id TEXT NOT NULL,
  actor TEXT NOT NULL, payload_json TEXT NOT NULL, created_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS operational_outbox(
  receipt_id TEXT PRIMARY KEY REFERENCES receipts(id),
  record_entry_id TEXT, delivered_at REAL);
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

    def __init__(self, root: str | Path, clock: Callable[[], float] = time.time,
                 operational_record: OperationalJournal | None = None) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.blobs = self.root / "blobs" / "sha256"
        self.blobs.mkdir(parents=True, exist_ok=True)
        self.now = clock
        self.operational_record = operational_record
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
        self._try_flush_operational_history()

    def close(self) -> None:
        """Best-effort the outbox once more, then close the underlying connection."""
        self._try_flush_operational_history()
        self.db.close()

    def receipt(self, outcome: str, event: str, subject_type: str, subject_id: str,
                actor: str, payload: dict[str, Any]) -> str:
        """Commit one local terminal receipt and its Record outbox intent together.

        Asset state changes made immediately before this call share this SQLite
        transaction. Record delivery happens only after that transaction commits,
        so the operational journal never gets ahead of the local terminal receipt.
        A failed Record delivery leaves a durable outbox row for replay instead of
        rolling back or misreporting already-committed Asset state.
        """
        receipt = new_id("rcpt")
        created_at = self.now()
        self.db.execute(
            "INSERT INTO receipts VALUES(?,?,?,?,?,?,?,?)",
            (receipt, outcome, event, subject_type, subject_id, actor,
             json.dumps(payload, sort_keys=True), created_at),
        )
        self.db.execute(
            "INSERT INTO operational_outbox(receipt_id,record_entry_id,delivered_at) "
            "VALUES(?,NULL,NULL)", (receipt,))
        self.db.commit()
        self._try_flush_operational_history()
        return receipt

    def pending_operational_history(self) -> list[str]:
        """Local terminal receipts not yet confirmed in the bound Record journal."""
        return [row["receipt_id"] for row in self.db.execute(
            "SELECT receipt_id FROM operational_outbox WHERE record_entry_id IS NULL "
            "ORDER BY rowid")]

    def flush_operational_history(self) -> int:
        """Replay the durable outbox into Record, idempotently, when the port is bound."""
        if self.operational_record is None:
            return 0
        pending = self.db.execute(
            "SELECT r.* FROM receipts r JOIN operational_outbox o ON o.receipt_id=r.id "
            "WHERE o.record_entry_id IS NULL ORDER BY r.created_at,r.id").fetchall()
        delivered = 0
        for row in pending:
            entry_id = mirror_receipt(self.operational_record, dict(row))
            self.db.execute(
                "UPDATE operational_outbox SET record_entry_id=?,delivered_at=? "
                "WHERE receipt_id=?", (entry_id, self.now(), row["id"]))
            self.db.commit()
            delivered += 1
        return delivered

    def _try_flush_operational_history(self) -> None:
        """Do not turn an unavailable Record port into a false rollback of Asset state."""
        if self.operational_record is None:
            return
        try:
            self.flush_operational_history()
        except (OSError, RuntimeError, ValueError, sqlite3.Error):
            # The local outbox is the durable evidence that delivery is still owed.
            # Explicit callers may call flush_operational_history() to surface the
            # underlying error; terminal Asset operations keep their truthful local
            # outcome rather than reporting failure after their state already committed.
            return

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
