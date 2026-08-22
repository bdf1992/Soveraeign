"""Dependency-free reference binding for the Soveraeign asset service.

The SQLite database is the canonical reference ledger for this slice. Search
and graph tables are disposable projections. Asset bytes live in a local CAS.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any
import json
import mimetypes
import sqlite3
import time
import uuid


class AuthorityRefused(PermissionError):
    pass


class StaleLease(RuntimeError):
    pass


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def _now() -> float:
    return time.time()


class AssetService:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.blobs = self.root / "blobs" / "sha256"
        self.blobs.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.root / "asset-service.sqlite3")
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA foreign_keys=ON")
        self._schema()

    def close(self) -> None:
        self.db.close()

    def _schema(self) -> None:
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
              asset_id TEXT PRIMARY KEY, text_value TEXT NOT NULL, source_receipt TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS graph_projection(
              relationship_id TEXT PRIMARY KEY, src_asset TEXT NOT NULL,
              predicate TEXT NOT NULL, dst_asset TEXT NOT NULL,
              source_receipt TEXT NOT NULL);
            """
        )
        self.db.commit()

    def _receipt(self, outcome: str, event: str, subject_type: str,
                 subject_id: str, actor: str, payload: dict[str, Any]) -> str:
        receipt = _id("rcpt")
        self.db.execute(
            "INSERT INTO receipts VALUES(?,?,?,?,?,?,?,?)",
            (receipt, outcome, event, subject_type, subject_id, actor,
             json.dumps(payload, sort_keys=True), _now()),
        )
        return receipt

    def _store_blob(self, data: bytes) -> tuple[str, Path]:
        digest = sha256(data).hexdigest()
        path = self.blobs / digest[:2] / digest
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_bytes(data)
        elif path.read_bytes() != data:
            raise RuntimeError("digest collision or corrupt blob")
        return digest, path

    def grant(self, issuer: str, actor: str, capability: str, scope: str = "*") -> str:
        grant = _id("grant")
        self.db.execute("INSERT INTO grants VALUES(?,?,?,?,0,?)",
                        (grant, actor, capability, scope, _now()))
        self._receipt("COMMITTED", "authority.grant", "grant", grant, issuer,
                      {"actor": actor, "capability": capability, "scope": scope})
        self.db.commit()
        return grant

    def _authorized(self, actor: str, capability: str, scope: str) -> bool:
        row = self.db.execute(
            "SELECT 1 FROM grants WHERE actor=? AND capability=? AND revoked=0 "
            "AND scope IN (?, '*') LIMIT 1", (actor, capability, scope)
        ).fetchone()
        return row is not None

    def _require(self, actor: str, capability: str, scope: str,
                 subject_type: str, subject_id: str) -> None:
        if self._authorized(actor, capability, scope):
            return
        self._receipt("REFUSED", "authority.check", subject_type, subject_id,
                      actor, {"required": capability, "scope": scope})
        self.db.commit()
        raise AuthorityRefused(f"{actor} lacks {capability} for {scope}")

    def ingest(self, path: str | Path, label: str, actor: str,
               locator: str | None = None) -> dict[str, str]:
        source_path = Path(path)
        data = source_path.read_bytes()
        digest, blob = self._store_blob(data)
        source = _id("source")
        asset = _id("asset")
        version = _id("version")
        self.db.execute("INSERT INTO sources VALUES(?,?,?,?)",
                        (source, locator or source_path.resolve().as_uri(), digest, _now()))
        self.db.execute("INSERT INTO assets VALUES(?,?,?)", (asset, label, _now()))
        mime = mimetypes.guess_type(source_path.name)[0] or "application/octet-stream"
        self.db.execute("INSERT INTO versions VALUES(?,?,?,?,?,?,?,?,?,?)",
                        (version, asset, source, digest, mime, len(data), str(blob),
                         "ORIGINAL", None, _now()))
        receipt = self._receipt("COMMITTED", "asset.ingest", "asset", asset, actor,
                                {"source_id": source, "version_id": version,
                                 "digest": digest})
        self.db.commit()
        return {"asset_id": asset, "source_id": source, "version_id": version,
                "digest": digest, "receipt_id": receipt}

    def propose(self, asset_id: str, actor: str, payload: dict[str, Any],
                required_authority: str = "ratify:judgement") -> str:
        proposal = _id("proposal")
        self.db.execute("INSERT INTO proposals VALUES(?,?,?,?,?,?,?)",
                        (proposal, asset_id, actor, json.dumps(payload, sort_keys=True),
                         "RECORDED", required_authority, _now()))
        self._receipt("COMMITTED", "proposal.record", "proposal", proposal, actor,
                      {"asset_id": asset_id, "standing": "RECORDED"})
        self.db.commit()
        return proposal

    def ratify(self, proposal_id: str, actor: str) -> str:
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
        receipt = self._receipt("COMMITTED", "proposal.ratify", "proposal",
                                proposal_id, actor, {"asset_id": proposal["asset_id"]})
        self.db.commit()
        return receipt

    def request_derivative(self, asset_id: str, version_id: str,
                           actor: str, kind: str = "metadata-card") -> str:
        self._require(actor, "operate:derive", asset_id, "asset", asset_id)
        run = _id("run")
        self.db.execute("INSERT INTO runs(id,kind,asset_id,input_version_id,requester,status,created_at) "
                        "VALUES(?,?,?,?,?,'PENDING',?)",
                        (run, kind, asset_id, version_id, actor, _now()))
        self._receipt("ATTEMPTED", "operation.request", "run", run, actor,
                      {"kind": kind, "input_version_id": version_id})
        self.db.commit()
        return run

    def claim(self, run_id: str, worker: str, ttl_seconds: float = 60) -> int:
        row = self.db.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        if row is None:
            raise KeyError(run_id)
        if row["status"] not in ("PENDING", "LEASED"):
            raise RuntimeError("run is not claimable")
        if row["status"] == "LEASED" and (row["lease_expires"] or 0) > _now():
            raise RuntimeError("active lease exists")
        fence = row["lease_fence"] + 1
        self.db.execute("UPDATE runs SET status='LEASED',worker=?,lease_fence=?,lease_expires=? WHERE id=?",
                        (worker, fence, _now() + ttl_seconds, run_id))
        self._receipt("COMMITTED", "lease.claim", "run", run_id, worker,
                      {"fence": fence, "ttl_seconds": ttl_seconds})
        self.db.commit()
        return fence

    def report_derivative(self, run_id: str, worker: str, fence: int,
                          output: bytes, mime: str = "application/json") -> str:
        run = self.db.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        if (run is None or run["worker"] != worker or run["lease_fence"] != fence
                or (run["lease_expires"] or 0) <= _now() or run["status"] != "LEASED"):
            if run is not None:
                self._receipt("REFUSED", "operation.report", "run", run_id, worker,
                              {"reason": "STALE_LEASE", "fence": fence})
                self.db.commit()
            raise StaleLease(run_id)
        digest, blob = self._store_blob(output)
        version = _id("version")
        derivation = {"operation": run["kind"], "run_id": run_id,
                      "input_version_id": run["input_version_id"], "lossy": True}
        self.db.execute("INSERT INTO versions VALUES(?,?,?,?,?,?,?,?,?,?)",
                        (version, run["asset_id"], None, digest, mime, len(output),
                         str(blob), "DERIVATIVE", json.dumps(derivation, sort_keys=True), _now()))
        self.db.execute("UPDATE runs SET status='REPORTED',output_version_id=?,report_json=? WHERE id=?",
                        (version, json.dumps({"digest": digest}), run_id))
        self._receipt("ATTEMPTED", "operation.report", "run", run_id, worker,
                      {"output_version_id": version, "digest": digest})
        self.db.commit()
        return version

    def observe(self, run_id: str, observer: str) -> str:
        run = self.db.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        if run is None or run["status"] != "REPORTED":
            raise RuntimeError("run has no independently observable report")
        version = self.db.execute("SELECT * FROM versions WHERE id=?",
                                  (run["output_version_id"],)).fetchone()
        data = Path(version["blob_path"]).read_bytes()
        passed = sha256(data).hexdigest() == version["digest"] and len(data) == version["size"]
        observation = _id("obs")
        evidence = {"digest": sha256(data).hexdigest(), "size": len(data), "exists": True}
        self.db.execute("INSERT INTO observations VALUES(?,?,?,?,?,?)",
                        (observation, run_id, observer, json.dumps(evidence, sort_keys=True),
                         int(passed), _now()))
        status = "COMMITTED" if passed else "FAILED"
        self.db.execute("UPDATE runs SET status=?,observation_id=? WHERE id=?",
                        (status, observation, run_id))
        self._receipt(status, "operation.observe", "run", run_id, observer, evidence)
        self.db.commit()
        return observation

    def retract(self, target_type: str, target_id: str, actor: str, reason: str) -> str:
        scope = target_id
        if target_type == "relationship":
            row = self.db.execute("SELECT src_asset FROM relationships WHERE id=?", (target_id,)).fetchone()
            if row is None:
                raise KeyError(target_id)
            scope = row["src_asset"]
        self._require(actor, "retract:record", scope, target_type, target_id)
        retraction = _id("retract")
        self.db.execute("INSERT INTO retractions VALUES(?,?,?,?,?,?)",
                        (retraction, target_type, target_id, actor, reason, _now()))
        if target_type == "relationship":
            self.db.execute("UPDATE relationships SET standing='COUNTERED' WHERE id=?", (target_id,))
        receipt = self._receipt("COUNTERED", "record.retract", target_type,
                                target_id, actor, {"retraction_id": retraction, "reason": reason})
        self.db.commit()
        return receipt

    def rebuild_projections(self, actor: str = "projector") -> dict[str, int]:
        self.db.execute("DELETE FROM search_projection")
        self.db.execute("DELETE FROM graph_projection")
        for asset in self.db.execute("SELECT * FROM assets"):
            ratified = self.db.execute(
                "SELECT id,payload_json FROM proposals WHERE asset_id=? AND standing='RATIFIED'",
                (asset["id"],)).fetchall()
            text = [asset["label"]]
            source_receipt = ""
            for proposal in ratified:
                payload = json.loads(proposal["payload_json"])
                text.extend(str(v) for k, v in payload.items() if k != "relationship")
                receipt = self.db.execute(
                    "SELECT id FROM receipts WHERE event='proposal.ratify' AND subject_id=? "
                    "ORDER BY created_at DESC LIMIT 1", (proposal["id"],)).fetchone()
                source_receipt = receipt["id"] if receipt else source_receipt
            self.db.execute("INSERT INTO search_projection VALUES(?,?,?)",
                            (asset["id"], " ".join(text), source_receipt or "UNRATIFIED_LABEL"))
        for relation in self.db.execute("SELECT * FROM relationships WHERE standing='EFFECTIVE'"):
            receipt = self.db.execute(
                "SELECT id FROM receipts WHERE event='proposal.ratify' AND subject_id=? "
                "ORDER BY created_at DESC LIMIT 1", (relation["proposal_id"],)).fetchone()
            self.db.execute("INSERT INTO graph_projection VALUES(?,?,?,?,?)",
                            (relation["id"], relation["src_asset"], relation["predicate"],
                             relation["dst_asset"], receipt["id"]))
        counts = {
            "search": self.db.execute("SELECT COUNT(*) FROM search_projection").fetchone()[0],
            "edges": self.db.execute("SELECT COUNT(*) FROM graph_projection").fetchone()[0],
        }
        self._receipt("COMMITTED", "projection.rebuild", "projection", "all", actor, counts)
        self.db.commit()
        return counts

    def search(self, query: str) -> list[str]:
        return [row["asset_id"] for row in self.db.execute(
            "SELECT asset_id FROM search_projection WHERE lower(text_value) LIKE ? ORDER BY asset_id",
            (f"%{query.lower()}%",))]

    def neighbors(self, asset_id: str) -> list[dict[str, str]]:
        return [dict(row) for row in self.db.execute(
            "SELECT src_asset,predicate,dst_asset,source_receipt FROM graph_projection "
            "WHERE src_asset=? OR dst_asset=? ORDER BY predicate,dst_asset",
            (asset_id, asset_id))]

    def federation_cross(self, actor: str, asset_id: str) -> str:
        receipt = self._receipt("REFUSED", "federation.cross", "asset", asset_id,
                                actor, {"reason": "UNCONFIGURED", "node_two": None})
        self.db.commit()
        return receipt

    def receipts(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self.db.execute("SELECT * FROM receipts ORDER BY created_at,id")]
