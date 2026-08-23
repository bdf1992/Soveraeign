"""Bind the ASSET-HL-2 history reader to the ASSET-HL-4 driver protocol.

Resolves each SOURCES.lock entry back to the exact captured bytes the lock
digested (soveraeign-sources-lock/1, services/asset/scripts/history_sources.py):
git-commit and github-pr/issue payloads re-derive locally from the captured
representation the lock itself carries, so no network crossing occurs here;
session-file payloads read from a sessions directory that arrives per
invocation (SOV_SESSIONS_DIR) and is recorded nowhere. A digest mismatch is
the SOURCE_CHANGED refusal of read_source (contracts/source.schema.json).

The reader's per-removal omission spans stay in its own uncommitted output;
the committed manifest carries the unique versioned definition set required
by contracts/recording.schema.json (definition_id, definition_digest only).

Effect class: RECORD_LOCAL. Refusal reasons carried on SourceRefused:
SESSIONS_DIR_UNDECLARED, SOURCE_MISSING, SOURCE_CHANGED,
UNSUPPORTED_SOURCE_KIND.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping
import getpass
import json
import os
import sys

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:  # script bootstrap; demo.py precedent
    sys.path.insert(0, str(_SCRIPTS))

import history_reader


class SourceRefused(Exception):
    """Per-source refusal; the driver records reason and continues the run."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def _digest(payload: bytes) -> str:
    return "sha256:" + sha256(payload).hexdigest()


def resolve_payload(entry: dict[str, Any], sessions_dir: Path | None) -> bytes:
    """The exact bytes the lock digested for this entry, or a named refusal."""
    kind = entry.get("kind") or str(entry["source_id"]).split(":", 1)[0]
    if kind == "git-commit":
        payload = (entry["source_address"] + "\t" + entry.get("title", "") + "\n").encode("utf-8")
    elif kind in ("github-pr", "github-issue"):
        record = {"number": int(entry["source_address"]), "state": entry.get("state", ""),
                  "title": entry.get("title", "")}
        payload = json.dumps(record, sort_keys=True).encode("utf-8")
    elif kind == "session-file":
        if sessions_dir is None:
            raise SourceRefused("SESSIONS_DIR_UNDECLARED")
        path = sessions_dir / (entry["source_address"] + ".jsonl")
        if not path.is_file():
            raise SourceRefused("SOURCE_MISSING")
        payload = path.read_bytes()
    else:
        raise SourceRefused("UNSUPPORTED_SOURCE_KIND")
    if _digest(payload) != entry["payload_digest"]:
        raise SourceRefused("SOURCE_CHANGED")
    return payload


def schema_omissions(omissions: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Collapse reader omission spans to the schema's unique definition set."""
    unique = {(entry["definition"], entry["definition_digest"]) for entry in omissions}
    return [{"definition_id": definition, "definition_digest": digest}
            for definition, digest in sorted(unique)]


class LockReader:
    """Driver-protocol reader over history_reader.read_source."""

    def __init__(self, config: history_reader.ReaderConfig, sessions_dir: Path | None = None):
        self.config = config
        self.sessions_dir = sessions_dir

    def read_source(self, source: dict[str, Any]) -> dict[str, Any]:
        payload = resolve_payload(source, self.sessions_dir)
        sanitized, manifest = history_reader.read_source(payload, source["source_id"], self.config)
        manifest["omissions"] = schema_omissions(manifest["omissions"])
        return {"payload": sanitized, "recording": manifest}


def build_reader(environ: Mapping[str, str] | None = None) -> LockReader:
    """Configuration arrives per invocation from the environment; never committed."""
    environ = os.environ if environ is None else environ
    sessions = environ.get(history_reader.SESSIONS_DIR_ENV, "")
    email = environ.get(history_reader.OWNER_EMAIL_ENV, "")
    username = environ.get("SOV_HOST_USERNAME", "") or getpass.getuser()
    config = history_reader.ReaderConfig(
        pii_emails=tuple(value for value in [email] if value),
        pii_usernames=tuple(value for value in [username] if value))
    return LockReader(config, Path(sessions) if sessions else None)


_DEFAULT = build_reader()


def read_source(source: dict[str, Any]) -> dict[str, Any]:
    """Module-level driver protocol entry point (ingest_history --reader target)."""
    return _DEFAULT.read_source(source)
