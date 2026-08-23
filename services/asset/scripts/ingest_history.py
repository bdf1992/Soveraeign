#!/usr/bin/env python3
"""Ingest sanitized history recordings as Asset Service assets (ASSET-HL-4).

Wires the ASSET-HL-2 reader over the ASSET-HL-3 SOURCES.lock using only the
existing participant API: ingest -> propose -> ratify (relationship custody
inside the local runtime ledger, demo.py precedent) -> rebuild_projections,
plus the leased derivative pipeline for versions on re-read. One asset per
source; a derived-from edge from each recording asset to its Source identity.

The runtime SQLite ledger and CAS bytes go only to a git-ignored state path
(default .local/history-corpus/), verified before any write; they are never
committed. Per-recording manifests are committed under lineage/recordings/
per contracts/recording.schema.json; ingest_manifests.py owns that surface.

Reader protocol: an object exposing read_source(source: dict) -> {"payload":
bytes, "recording": dict} carrying the eight reader-owned fields; the bound
realization over the real reader is ingest_history_adapter.py. A refusal
exception may carry a reason attribute naming the per-source refusal.

Effect class: RECORD_LOCAL. Run refusals: PRECONDITION_MISSING,
STATE_NOT_IGNORED. Per-source refusals land in the run log as failed entries;
counts must reconcile: ingested + versioned + unchanged + failed equals
enumerated.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
import argparse
import importlib.util
import json
import subprocess
import sys

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:  # script bootstrap; demo.py precedent
    sys.path.insert(0, str(_SCRIPTS))

from ingest_manifests import (build_manifest, load_manifest_index, manifest_contaminants,
                              validate_lock_entry, validate_recording)

ASSET_ROOT = _SCRIPTS.parent
REPO_ROOT = ASSET_ROOT.parents[1]
DEFAULT_STATE = REPO_ROOT / ".local" / "history-corpus"
DEFAULT_LOCK = REPO_ROOT / "lineage" / "SOURCES.lock"
DEFAULT_MANIFESTS = REPO_ROOT / "lineage" / "recordings"
DEFAULT_ACTOR = "asset-history-driver"


def _default_ignore_check(path: Path) -> bool:
    """True when git ignores the path, or the path lies outside the repository."""
    try:
        relative = path.resolve().relative_to(REPO_ROOT)
    except ValueError:
        return True
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "check-ignore", "-q", str(relative)],
        capture_output=True, check=False, timeout=10)
    return result.returncode == 0


def ensure_state_admissible(state_dir: Path,
                            check: Callable[[Path], bool] | None = None) -> dict[str, str] | None:
    """Refuse before any write when the runtime state path could be committed."""
    if (check or _default_ignore_check)(state_dir):
        return None
    return {"outcome": "REFUSED", "reason": "STATE_NOT_IGNORED", "state_dir": str(state_dir),
            "rule": "runtime databases and payload stores are never committed"}


def _label_key(source_id: str) -> str:
    """Bracketed so one source id can never substring-match another in search."""
    return "[" + source_id + "]"


def _excerpt(payload: bytes, limit: int = 240) -> str:
    try:
        return payload.decode("utf-8")[:limit]
    except UnicodeDecodeError:
        return ""


def _latest_digest(service: Any, asset_id: str, manifest: dict[str, Any] | None) -> str | None:
    """Committed manifest first; the original ingest receipt when none survives."""
    if manifest is not None:
        return str(manifest["payload_digest"])
    for receipt in service.receipts():
        if receipt["event"] == "asset.ingest" and receipt["subject_id"] == asset_id:
            return "sha256:" + json.loads(receipt["payload_json"])["digest"]
    return None


def _ingest_new(service: Any, entry: dict[str, Any], payload: bytes, actor: str,
                recording_id: str) -> None:
    """First reading of a source: one new asset, one derived-from edge."""
    scratch = Path(service.root) / "incoming.bin"
    scratch.write_bytes(payload)
    result = service.ingest(scratch, "history-recording " + _label_key(entry["source_id"]),
                            actor, locator=entry["source_address"])
    scratch.unlink()
    proposal = service.propose(result["asset_id"], actor, {
        "relationship": {"predicate": "derived-from", "dst_asset": entry["source_id"]},
        "recording_id": recording_id, "description": _excerpt(payload),
    })
    service.ratify(proposal, actor)


def _reread_version(service: Any, asset_id: str, payload: bytes, actor: str,
                    recording_id: str) -> str | None:
    """Changed digest on re-read: a new version on the same asset through the
    leased derivative pipeline, the only existing-API path for versions."""
    version_id = None
    for receipt in service.receipts():
        if receipt["event"] == "asset.ingest" and receipt["subject_id"] == asset_id:
            version_id = json.loads(receipt["payload_json"])["version_id"]
    if version_id is None:
        return "REREAD_ASSET_AMBIGUOUS"
    run_id = service.request_derivative(asset_id, version_id, actor, kind="history-reread")
    fence = service.claim(run_id, actor)
    service.report_derivative(run_id, actor, fence, payload, mime="application/octet-stream")
    service.observe(run_id, actor)
    proposal = service.propose(asset_id, actor, {
        "recording_id": recording_id, "reread_excerpt": _excerpt(payload)})
    service.ratify(proposal, actor)
    return None


def _projection_snapshot(service: Any, actor: str) -> dict[str, Any]:
    """Rebuild, then read the projections back through the public read API."""
    counts = service.rebuild_projections(actor)
    assets = service.search("")
    return {"counts": counts, "assets": assets,
            "neighbors": {asset: service.neighbors(asset) for asset in assets}}


def run_ingest(service: Any, reader: Any, entries: list[Any], manifest_dir: Path,
               actor: str = DEFAULT_ACTOR, now: Callable[[], str] | None = None) -> dict[str, Any]:
    """One asset per source; versions on re-read; committed manifests; run-log
    reconciliation; a twin rebuild proving the projections are deterministic."""
    produced_at = now or (lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))
    manifest_dir.mkdir(parents=True, exist_ok=True)
    index = load_manifest_index(manifest_dir)
    service.grant(actor, actor, "ratify:judgement")
    service.grant(actor, actor, "operate:derive")
    service.rebuild_projections(actor)
    log: dict[str, Any] = {"enumerated": len(entries), "ingested": 0, "versioned": 0,
                           "unchanged": 0, "failed": []}
    processed: set[str] = set()

    def fail(entry: Any, reason: str) -> None:
        source_id = entry.get("source_id", "?") if isinstance(entry, dict) else "?"
        log["failed"].append({"source_id": source_id, "reason": reason})

    for entry in entries:
        reason = validate_lock_entry(entry)
        if reason is None and entry["source_id"] in processed:
            reason = "DUPLICATE_SOURCE"
        if reason:
            fail(entry, reason)
            continue
        processed.add(entry["source_id"])
        try:
            result = reader.read_source(entry)
            payload, recording = bytes(result["payload"]), result["recording"]
        except Exception as error:  # a reader defect must fail one source, not the run
            fail(entry, str(getattr(error, "reason", "")) or "READER_ERROR")
            continue
        reason = validate_recording(recording, entry, payload)
        if reason:
            fail(entry, reason)
            continue
        manifest = build_manifest(recording, actor, produced_at())
        text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        if manifest_contaminants(text):
            fail(entry, "MANIFEST_CONTAMINATED")
            continue
        hits = service.search(_label_key(entry["source_id"]))
        if len(hits) > 1:
            fail(entry, "REREAD_ASSET_AMBIGUOUS")
            continue
        manifest_path = manifest_dir / (manifest["recording_id"] + ".json")
        if hits:
            latest = _latest_digest(service, hits[0], index.get(entry["source_id"]))
            if latest == manifest["payload_digest"]:
                log["unchanged"] += 1
                if not manifest_path.exists():
                    manifest_path.write_text(text, encoding="utf-8", newline="\n")
                continue
            reason = _reread_version(service, hits[0], payload, actor, manifest["recording_id"])
            if reason:
                fail(entry, reason)
                continue
            log["versioned"] += 1
        else:
            _ingest_new(service, entry, payload, actor, manifest["recording_id"])
            log["ingested"] += 1
        manifest_path.write_text(text, encoding="utf-8", newline="\n")
        index[entry["source_id"]] = manifest

    first = _projection_snapshot(service, actor)
    second = _projection_snapshot(service, actor)
    log["projection_deterministic"] = first == second
    log["projection_counts"] = second["counts"]
    log["derived_from_edges"] = sum(
        1 for edges in second["neighbors"].values()
        for edge in edges if edge["predicate"] == "derived-from")
    succeeded = log["ingested"] + log["versioned"] + log["unchanged"]
    log["reconciled"] = succeeded + len(log["failed"]) == log["enumerated"]
    return log


def load_reader(path: Path) -> Any:
    """Load the reader module by file path (test_oracle.py bootstrap pattern)."""
    spec = importlib.util.spec_from_file_location("asset_history_reader_binding", path)
    if spec is None or spec.loader is None:
        raise ImportError(str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_lock(path: Path) -> list[Any]:
    """Accept the soveraeign-sources-lock/1 document or a bare entry list."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["sources"] if isinstance(data, dict) else data


def _refuse(reason: str, detail: dict[str, str]) -> int:
    print(json.dumps({"outcome": "REFUSED", "reason": reason, **detail}, sort_keys=True))
    return 2


def main(argv: list[str] | None = None) -> int:
    """Refuse missing preconditions loudly; otherwise run and write the log."""
    parser = argparse.ArgumentParser(description="Ingest sanitized history recordings")
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument("--reader", type=Path, default=None)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--manifests", type=Path, default=DEFAULT_MANIFESTS)
    parser.add_argument("--actor", default=DEFAULT_ACTOR)
    args = parser.parse_args(argv)
    if not args.lock.is_file():
        return _refuse("PRECONDITION_MISSING",
                       {"missing": "SOURCES.lock (ASSET-HL-3)", "path": str(args.lock)})
    if args.reader is None or not args.reader.is_file():
        return _refuse("PRECONDITION_MISSING",
                       {"missing": "reader module (ASSET-HL-2)", "path": str(args.reader or "")})
    refusal = ensure_state_admissible(args.state)
    if refusal is not None:
        print(json.dumps(refusal, sort_keys=True))
        return 2
    sys.path.insert(0, str(ASSET_ROOT / "src"))  # script bootstrap; demo.py precedent
    from soveraeign_asset_service import AssetService

    service = AssetService(args.state)
    try:
        log = run_ingest(service=service, reader=load_reader(args.reader),
                         entries=load_lock(args.lock), manifest_dir=args.manifests,
                         actor=args.actor)
    finally:
        service.close()
    (args.state / "run-log.json").write_text(
        json.dumps(log, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(log, indent=2, sort_keys=True))
    return 0 if log["reconciled"] and log["projection_deterministic"] else 1


if __name__ == "__main__":
    sys.exit(main())
