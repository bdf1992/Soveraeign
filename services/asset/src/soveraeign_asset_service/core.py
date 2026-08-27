"""Dependency-free reference binding for the Soveraeign asset service.

This module owns the asset lifecycle only. Payload custody and receipts live in
`store.py`, grants and sessions in `authority.py`, the rebuildable views in
`projections.py`, typed collections and membership in `organization.py`, and the
conformance read over them in `librarian.py`. The SQLite database is the
canonical reference ledger for this slice; the search and graph tables are
disposable projections.

The organizational lifecycle is reached at `service.organization` and
`service.librarian` rather than wrapped method by method here: those two objects
are its public surface, the way `service.authority` is authority's, and copying
every signature into this module would buy nothing but length.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
import json
import mimetypes
import time

from soveraeign_asset_service import authority as authority_module
from soveraeign_asset_service import organization as organization_module
from soveraeign_asset_service import projections as projections_module
from soveraeign_asset_service import runs as runs_module
from soveraeign_asset_service.authority import (
    DEFAULT_GRANT_TTL_SECONDS,
    Authority,
    AuthorityRefused,
)
from soveraeign_asset_service.identity import ORIGINAL, REVISION, Identity
from soveraeign_asset_service.librarian import Librarian
from soveraeign_asset_service.organization import Organization, OrganizationRefused
from soveraeign_asset_service.reads import ReadSurface
from soveraeign_asset_service.projections import Projections
from soveraeign_asset_service.recording import ReaderDeclaration
from soveraeign_asset_service.runs import DEFAULT_LEASE_TTL_SECONDS, Runs, StaleLease
from soveraeign_asset_service.store import Store, new_id


def _id(prefix: str) -> str:
    return new_id(prefix)


def _now() -> float:
    return time.time()


SCHEMA = """
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
CREATE TABLE IF NOT EXISTS proposals(
  id TEXT PRIMARY KEY, asset_id TEXT NOT NULL REFERENCES assets(id),
  actor TEXT NOT NULL, payload_json TEXT NOT NULL,
  standing TEXT NOT NULL, required_authority TEXT NOT NULL,
  created_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS relationships(
  id TEXT PRIMARY KEY, src_asset TEXT NOT NULL, predicate TEXT NOT NULL,
  dst_asset TEXT NOT NULL, proposal_id TEXT NOT NULL,
  standing TEXT NOT NULL, created_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS retractions(
  id TEXT PRIMARY KEY, target_type TEXT NOT NULL, target_id TEXT NOT NULL,
  actor TEXT NOT NULL, reason TEXT NOT NULL, created_at REAL NOT NULL);
"""


class AssetService(ReadSurface):
    """The asset lifecycle: capture, propose, ratify, derive, observe, retract."""

    def __init__(self, root: str | Path, clock: Callable[[], float] = time.time):
        self.store = Store(root, clock)
        self.root = self.store.root
        self.blobs = self.store.blobs
        self.db = self.store.db
        self.store.apply_schema(SCHEMA, authority_module.SCHEMA,
                                projections_module.SCHEMA, runs_module.SCHEMA,
                                organization_module.SCHEMA)
        self.authority = Authority(self.store)
        self.identity = Identity(self.db)
        self.projections = Projections(self.store)
        self.runs = Runs(self.store, self.authority)
        self.organization = Organization(self.store, self.authority)
        self.librarian = Librarian(self.store, self.organization)

    def close(self) -> None:
        self.store.close()

    def _receipt(self, outcome: str, event: str, subject_type: str,
                 subject_id: str, actor: str, payload: dict[str, Any]) -> str:
        return self.store.receipt(outcome, event, subject_type, subject_id, actor, payload)

    def _store_blob(self, data: bytes) -> tuple[str, Path]:
        return self.store.store_blob(data)

    # -- authority --------------------------------------------------------

    def open_session(self, participant: str, model_identity: str,
                     ttl_seconds: float | None = None) -> str:
        """Start a bounded session; grants bound to it die when it closes."""
        if ttl_seconds is None:
            return self.authority.open_session(participant, model_identity)
        return self.authority.open_session(participant, model_identity, ttl_seconds)

    def close_session(self, session_id: str, actor: str) -> str:
        """End a session and stop every grant bound to it."""
        return self.authority.close_session(session_id, actor)

    def grant(self, issuer: str, actor: str, capability: str, scope: str = "*",
              ttl_seconds: float = DEFAULT_GRANT_TTL_SECONDS,
              session_id: str | None = None) -> str:
        """Issue a live, expiring grant, attenuated to what the issuer holds."""
        return self.authority.grant(issuer, actor, capability, scope, ttl_seconds, session_id)

    def revoke(self, grant_id: str, actor: str) -> str:
        """Revoke a grant ahead of its expiry."""
        return self.authority.revoke(grant_id, actor)

    def _authorized(self, actor: str, capability: str, scope: str) -> bool:
        return self.authority.authorized(actor, capability, scope)

    def _require(self, actor: str, capability: str, scope: str,
                 subject_type: str, subject_id: str) -> None:
        self.authority.require(actor, capability, scope, subject_type, subject_id)

    # -- lifecycle --------------------------------------------------------

    def ingest(self, path: str | Path, label: str, actor: str,
               locator: str | None = None) -> dict[str, str]:
        """Capture a payload as a version of the asset its locator identifies.

        An asset is an identity with a version history (`CLASSIFICATION.md`), so
        capturing the same locator again adds a version rather than a second
        identity. Unchanged bytes add nothing: that is not a new state of the
        asset, so no version follows.
        """
        source_path = Path(path)
        data = source_path.read_bytes()
        digest, blob = self._store_blob(data)
        address = locator or source_path.resolve().as_uri()
        held = self.identity.by_locator(address)
        if held is not None and held["digest"] == digest:
            receipt = self._receipt("ATTEMPTED", "asset.ingest-asset", "asset", held["asset_id"],
                                    actor, {"version_id": held["version_id"],
                                            "digest": digest, "locator": address,
                                            "reason": "NO_NEW_STATE"})
            self.db.commit()
            return {"asset_id": held["asset_id"], "source_id": held["source_id"],
                    "version_id": held["version_id"], "digest": digest,
                    "receipt_id": receipt, "role": held["role"], "unchanged": True}
        source = _id("source")
        asset = held["asset_id"] if held is not None else _id("asset")
        role = REVISION if held is not None else ORIGINAL
        version = _id("version")
        self.db.execute("INSERT INTO sources VALUES(?,?,?,?)",
                        (source, address, digest, _now()))
        if held is None:
            self.db.execute("INSERT INTO assets VALUES(?,?,?)", (asset, label, _now()))
        mime = mimetypes.guess_type(source_path.name)[0] or "application/octet-stream"
        self.db.execute("INSERT INTO versions VALUES(?,?,?,?,?,?,?,?,?,?)",
                        (version, asset, source, digest, mime, len(data), str(blob),
                         role, None, _now()))
        receipt = self._receipt("COMMITTED", "asset.ingest-asset", "asset", asset, actor,
                                {"source_id": source, "version_id": version,
                                 "digest": digest, "role": role,
                                 "supersedes": held["version_id"] if held else None})
        self.db.commit()
        return {"asset_id": asset, "source_id": source, "version_id": version, "role": role,
                "digest": digest, "receipt_id": receipt}

    def propose(self, asset_id: str, actor: str, payload: dict[str, Any],
                required_authority: str = "ratify:judgement") -> str:
        """Record a proposal. Recording claims nothing; ratification is separate."""
        proposal = _id("proposal")
        self.db.execute("INSERT INTO proposals VALUES(?,?,?,?,?,?,?)",
                        (proposal, asset_id, actor, json.dumps(payload, sort_keys=True),
                         "RECORDED", required_authority, _now()))
        self._receipt("COMMITTED", "asset.propose-description", "proposal", proposal, actor,
                      {"asset_id": asset_id, "standing": "RECORDED"})
        self.db.commit()
        return proposal

    def ratify(self, proposal_id: str, actor: str) -> str:
        """Ratify a recorded proposal under the authority it declared it needs."""
        proposal = self.db.execute("SELECT * FROM proposals WHERE id=?", (proposal_id,)).fetchone()
        if proposal is None:
            raise KeyError(proposal_id)
        self._require(actor, proposal["required_authority"], proposal["asset_id"],
                      "proposal", proposal_id)
        payload = json.loads(proposal["payload_json"])
        self.db.execute("UPDATE proposals SET standing='RATIFIED' WHERE id=?", (proposal_id,))
        relation = payload.get("relationship")
        if relation:
            relationship = _id("rel")
            self.db.execute("INSERT INTO relationships VALUES(?,?,?,?,?,?,?)",
                            (relationship, proposal["asset_id"], relation["predicate"],
                             relation["dst_asset"], proposal_id, "EFFECTIVE", _now()))
        receipt = self._receipt("COMMITTED", "asset.ratify-proposal", "proposal",
                                proposal_id, actor, {"asset_id": proposal["asset_id"]})
        self.db.commit()
        return receipt

    def request_derivative(self, asset_id: str, version_id: str | list[str],
                           actor: str, kind: str = "metadata-card", *,
                           reader: ReaderDeclaration | None = None) -> str:
        """Request a derived version. The request is an attempt, not a result."""
        return self.runs.request(asset_id, version_id, actor, kind, reader)

    def claim(self, run_id: str, worker: str,
              ttl_seconds: float = DEFAULT_LEASE_TTL_SECONDS) -> int:
        """Lease a run to one worker and return its fencing token."""
        return self.runs.claim(run_id, worker, ttl_seconds)

    def report_derivative(self, run_id: str, worker: str, fence: int,
                          output: bytes, mime: str = "application/json") -> str:
        """Accept a worker's report. A report settles nothing."""
        return self.runs.report(run_id, worker, fence, output, mime)

    def reconstruct_recording(self, recording_or_version_id: str) -> dict[str, Any]:
        """Resolve every addressed material of a declared derivative recording."""
        return self.runs.reconstruct(recording_or_version_id)

    def observe(self, run_id: str, observer: str) -> str:
        """Check a reported run against its durable output."""
        return self.runs.observe(run_id, observer)

    def retract(self, target_type: str, target_id: str, actor: str, reason: str) -> str:
        """Add a counter-record. The original event is never erased."""
        scope = target_id
        if target_type == "relationship":
            row = self.db.execute("SELECT src_asset FROM relationships WHERE id=?",
                                  (target_id,)).fetchone()
            if row is None:
                raise KeyError(target_id)
            scope = row["src_asset"]
        self._require(actor, "retract:record", scope, target_type, target_id)
        retraction = _id("retract")
        self.db.execute("INSERT INTO retractions VALUES(?,?,?,?,?,?)",
                        (retraction, target_type, target_id, actor, reason, _now()))
        if target_type == "relationship":
            self.db.execute("UPDATE relationships SET standing='COUNTERED' WHERE id=?",
                            (target_id,))
        receipt = self._receipt("COUNTERED", "asset.retract-record", target_type,
                                target_id, actor, {"retraction_id": retraction,
                                                   "reason": reason})
        self.db.commit()
        return receipt

    # -- projections and crossings ----------------------------------------
    #
    # The read-only delegations that used to sit here live in `reads.ReadSurface`,
    # mixed into this class. What remains is what writes.

    def rebuild_projections(self, actor: str = "projector") -> dict[str, int]:
        """Derive both views again from ratified records."""
        return self.projections.rebuild(actor)

    def federation_cross(self, actor: str, asset_id: str) -> str:
        """Refuse a federation crossing while no second node is configured."""
        receipt = self._receipt("REFUSED", "federation.cross", "asset", asset_id,
                                actor, {"reason": "UNCONFIGURED", "node_two": None})
        self.db.commit()
        return receipt


__all__ = ["AssetService", "AuthorityRefused", "OrganizationRefused", "StaleLease"]
