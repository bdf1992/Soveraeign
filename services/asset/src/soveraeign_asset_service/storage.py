"""SQLite ledger and filesystem content-addressed storage mechanisms."""

from __future__ import annotations

import sqlite3
import time
import uuid
from hashlib import sha256
from pathlib import Path


class PayloadIntegrityError(RuntimeError):
    """Raised when addressed bytes no longer match their recorded identity."""


def new_id(prefix: str) -> str:
    """Return a locally unique opaque identifier with a readable role prefix."""
    return f"{prefix}_{uuid.uuid4().hex}"


def now() -> float:
    """Return the current Unix timestamp for an injectable boundary later."""
    return time.time()


class AssetStore:
    """Own the reference SQLite mechanism and immutable payload custody."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.blobs = self.root / "blobs" / "sha256"
        self.blobs.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.root / "asset-service.sqlite3")
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA foreign_keys=ON")
        self._create_schema()

    def close(self) -> None:
        self.db.close()

    def _create_schema(self) -> None:
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS sources(
              id TEXT PRIMARY KEY, locator TEXT NOT NULL, digest TEXT NOT NULL,
              captured_at REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS assets(
              id TEXT PRIMARY KEY, label TEXT NOT NULL, created_at REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS versions(
              id TEXT PRIMARY KEY, asset_id TEXT NOT NULL REFERENCES assets(id),
              source_id TEXT REFERENCES sources(id), digest TEXT NOT NULL,
              mime TEXT NOT NULL, size INTEGER NOT NULL, blob_path TEXT NOT NULL,
              role TEXT NOT NULL, derivation_json TEXT, created_at REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS grants(
              id TEXT PRIMARY KEY, actor TEXT NOT NULL, capability TEXT NOT NULL,
              scope TEXT NOT NULL, revoked INTEGER NOT NULL DEFAULT 0,
              created_at REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS proposals(
              id TEXT PRIMARY KEY, asset_id TEXT NOT NULL REFERENCES assets(id),
              actor TEXT NOT NULL, payload_json TEXT NOT NULL,
              standing TEXT NOT NULL, required_authority TEXT NOT NULL,
              created_at REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS relationships(
              id TEXT PRIMARY KEY, src_asset TEXT NOT NULL, predicate TEXT NOT NULL,
              dst_asset TEXT NOT NULL, proposal_id TEXT NOT NULL,
              standing TEXT NOT NULL, created_at REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS runs(
              id TEXT PRIMARY KEY, kind TEXT NOT NULL, asset_id TEXT NOT NULL,
              input_version_id TEXT NOT NULL, requester TEXT NOT NULL,
              status TEXT NOT NULL, worker TEXT, lease_fence INTEGER NOT NULL DEFAULT 0,
              lease_expires REAL, output_version_id TEXT, report_json TEXT,
              observation_id TEXT, created_at REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS derivative_plans(
              run_id TEXT PRIMARY KEY REFERENCES runs(id),
              source_id TEXT NOT NULL, source_digest TEXT NOT NULL,
              reader_id TEXT NOT NULL, reader_version TEXT NOT NULL,
              configuration_digest TEXT NOT NULL, output_role TEXT NOT NULL,
              fidelity TEXT NOT NULL, omissions_json TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS recordings(
              id TEXT PRIMARY KEY, run_id TEXT NOT NULL UNIQUE REFERENCES runs(id),
              output_version_id TEXT NOT NULL UNIQUE REFERENCES versions(id),
              source_id TEXT NOT NULL, source_digest TEXT NOT NULL,
              reader_id TEXT NOT NULL, reader_version TEXT NOT NULL,
              configuration_digest TEXT NOT NULL, output_role TEXT NOT NULL,
              payload_address TEXT NOT NULL, payload_digest TEXT NOT NULL,
              fidelity TEXT NOT NULL,
              omissions_json TEXT NOT NULL, produced_at REAL NOT NULL,
              produced_by TEXT NOT NULL, standing TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS observations(
              id TEXT PRIMARY KEY, run_id TEXT NOT NULL, observer TEXT NOT NULL,
              evidence_json TEXT NOT NULL, passed INTEGER NOT NULL,
              created_at REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS retractions(
              id TEXT PRIMARY KEY, target_type TEXT NOT NULL, target_id TEXT NOT NULL,
              actor TEXT NOT NULL, reason TEXT NOT NULL, created_at REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS receipts(
              id TEXT PRIMARY KEY, outcome TEXT NOT NULL, event TEXT NOT NULL,
              subject_type TEXT NOT NULL, subject_id TEXT NOT NULL,
              actor TEXT NOT NULL, payload_json TEXT NOT NULL, created_at REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS search_projection(
              asset_id TEXT PRIMARY KEY, text_value TEXT NOT NULL,
              source_receipt TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS graph_projection(
              relationship_id TEXT PRIMARY KEY, src_asset TEXT NOT NULL,
              predicate TEXT NOT NULL, dst_asset TEXT NOT NULL,
              source_receipt TEXT NOT NULL);
            """
        )
        self.db.commit()

    def store_blob(self, data: bytes) -> tuple[str, Path]:
        """Store bytes by digest without replacing an existing payload."""
        digest = sha256(data).hexdigest()
        path = self.blobs / digest[:2] / digest
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_bytes(data)
        elif path.read_bytes() != data:
            raise PayloadIntegrityError("digest collision or corrupt blob")
        return digest, path

    def verified_version(self, version_id: str) -> tuple[sqlite3.Row, bytes]:
        """Resolve an exact version and refuse bytes that no longer match it."""
        version = self.db.execute(
            "SELECT * FROM versions WHERE id=?", (version_id,)
        ).fetchone()
        if version is None:
            raise KeyError(version_id)
        path = Path(version["blob_path"])
        if not path.is_file():
            raise PayloadIntegrityError(f"missing payload for {version_id}")
        data = path.read_bytes()
        if sha256(data).hexdigest() != version["digest"] or len(data) != version["size"]:
            raise PayloadIntegrityError(f"payload identity changed for {version_id}")
        return version, data
