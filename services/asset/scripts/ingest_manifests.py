"""Committed-manifest contract surface for the history ingestion driver.

Owns validation of SOURCES.lock entries (contracts/source.schema.json), of the
eight reader-owned recording fields (bound by
conformance/fixtures/lineage/reader-cases.json), completion of the committed
manifest per contracts/recording.schema.json, the committed-manifest index,
and the contamination guard. scripts/lint.py skips lineage/, so the guard here
is the automated check on committed manifest bytes: no absolute host path or
email address may survive.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any
import json
import re

LOCK_FIELDS = ("source_id", "source_address", "payload_digest", "payload_size",
               "captured_at", "captured_by")
READER_FIELDS = ("source_id", "source_digest", "reader_id", "reader_version",
                 "configuration_digest", "payload_digest", "fidelity", "omissions")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
# The shapes scripts/lint.py refuses in repository text, plus an email shape it
# does not own; pattern sources are split so no committed line here matches a
# lint shape itself.
CONTAMINANTS = {
    "absolute drive path": re.compile(r"[A-Za-z]:[\\/]"),
    "UNC path": re.compile(r"\\\\[A-Za-z0-9._-]+\\"),
    "posix user path": re.compile("/" + "Users/[^/\\s]+|/" + "home/[^/\\s]+"),
    "email address": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
}


def manifest_contaminants(text: str) -> list[str]:
    """Name every contaminant shape found in would-be committed manifest text."""
    return [name for name, pattern in CONTAMINANTS.items() if pattern.search(text)]


def validate_lock_entry(entry: Any) -> str | None:
    """Hold a SOURCES.lock entry to the contracts/source.schema.json required set."""
    if not isinstance(entry, dict) or any(entry.get(f) in ("", None) for f in LOCK_FIELDS):
        return "LOCK_ENTRY_INVALID"
    return None


def validate_recording(recording: Any, entry: dict[str, Any], payload: bytes) -> str | None:
    """Hold the reader to the eight fields bound by reader-cases and to its digests."""
    if not isinstance(recording, dict) or any(
            f not in recording or (f != "omissions" and recording[f] in ("", None))
            for f in READER_FIELDS):
        return "RECORDING_INCOMPLETE"
    omissions = recording["omissions"]
    if (recording["fidelity"] not in ("EXACT", "LOSSY") or not isinstance(omissions, list)
            or (recording["fidelity"] == "EXACT") != (omissions == [])
            or any(not DIGEST.match(str(recording[f]))
                   for f in ("source_digest", "configuration_digest", "payload_digest"))):
        return "RECORDING_INCOMPLETE"
    if recording["source_id"] != entry["source_id"]:
        return "RECORDING_SOURCE_MISMATCH"
    if recording["payload_digest"] != "sha256:" + sha256(payload).hexdigest():
        return "READER_DIGEST_MISMATCH"
    return None


def build_manifest(recording: dict[str, Any], actor: str, produced_at: str) -> dict[str, Any]:
    """Complete the committed manifest per contracts/recording.schema.json."""
    identity = recording["source_id"] + "|" + recording["payload_digest"]
    manifest = {field: recording[field] for field in READER_FIELDS}
    manifest.update({
        "recording_id": "rec-" + sha256(identity.encode("utf-8")).hexdigest()[:16],
        "payload_address": "cas:sha256/" + recording["payload_digest"].split(":", 1)[1],
        "produced_at": produced_at, "produced_by": actor, "standing": "RECORDED",
    })
    return manifest


def load_manifest_index(manifest_dir: Path) -> dict[str, dict[str, Any]]:
    """Latest committed manifest per source, by produced_at then filename order."""
    index: dict[str, dict[str, Any]] = {}
    for path in sorted(manifest_dir.glob("rec-*.json")):
        manifest = json.loads(path.read_text(encoding="utf-8"))
        current = index.get(manifest["source_id"])
        if current is None or manifest["produced_at"] >= current["produced_at"]:
            index[manifest["source_id"]] = manifest
    return index
