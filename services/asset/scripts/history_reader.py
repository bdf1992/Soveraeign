#!/usr/bin/env python3
"""History reader: derive sanitized Recordings from captured session Sources.

Closes the KNOWN-GAPS.md "Derivation reconstruction" row (C2; PROD-I-2; SPEC
Reader/Recording) for history payloads: every reading resolves its exact
source digest, reader identity and version, configuration digest, fidelity,
and one recorded omission per removal, so the derivation reconstructs
deterministically from the immutable source plus the named definitions.

Versioned omission definitions (a later ``-v2`` produces a new recording and
leaves the old one): ``sanitize-v1`` omits absolute host paths and secret
shapes, both reused from ``scripts/lint.py`` (the one repository secret
oracle, loaded from its file location, never re-authored), plus tool-result
bodies over the limit the definition itself names (65536; changing it is a
``-v2``); ``pii-v1`` omits configured owner emails and host usernames, which
are configuration pinned by the configuration digest, never committed text.
The sessions directory arrives as ``--sessions-dir`` or ``SOV_SESSIONS_DIR``;
no absolute host path is committed or printed. CLI output lands in a
caller-named directory (default: gitignored ``.local/lineage/recordings``).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
import argparse
import functools
import getpass
import hashlib
import importlib.util
import json
import os
import re


ROOT = Path(__file__).resolve().parents[3]
READER_ID = "soveraeign-asset-history-reader"
READER_VERSION = "1"
OVERSIZED_LIMIT_BYTES = 65536  # Named by sanitize-v1; changing it is a -v2.
SESSIONS_DIR_ENV = "SOV_SESSIONS_DIR"
OWNER_EMAIL_ENV = "SOV_OWNER_EMAIL"
_LEADING_CONTEXT = " \t\r\n'\""  # context character a lint local-path shape may capture


def _load_lint():
    """Load scripts/lint.py from its file location: one secret oracle, reused."""
    spec = importlib.util.spec_from_file_location(
        "soveraeign_repository_lint", ROOT / "scripts" / "lint.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_LINT = _load_lint()


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _canonical_digest(record: dict) -> str:
    return _sha256(json.dumps(record, sort_keys=True, ensure_ascii=True).encode("ascii"))


def definition_record(definition_id: str) -> dict:
    """The exact content a versioned omission definition digests over."""
    if definition_id == "sanitize-v1":
        return {
            "definition_id": "sanitize-v1",
            "oversized_limit_bytes": OVERSIZED_LIMIT_BYTES,
            "secret_shapes": {n: p.pattern for n, p in sorted(_LINT.SECRET_PATTERNS.items())},
            "local_path_shapes": [p.pattern for p in _LINT.LOCAL_PATH_PATTERNS],
            "kinds": ["secret-shape", "local-absolute-user-path", "oversized-tool-result"],
        }
    if definition_id == "pii-v1":
        return {
            "definition_id": "pii-v1",
            "targets": ["owner-email", "host-username"],
            "kinds": ["email-address", "host-username"],
            "note": "identities are configuration, pinned by the configuration digest",
        }
    raise ValueError(f"OMISSION_DEFINITION_UNKNOWN: {definition_id}")


@functools.lru_cache(maxsize=None)
def definition_digest(definition_id: str) -> str:
    return _canonical_digest(definition_record(definition_id))


@dataclass(frozen=True)
class ReaderConfig:
    """Configuration in force for one reading; digested into every manifest."""

    definitions: tuple[str, ...] = ("sanitize-v1", "pii-v1")
    pii_emails: tuple[str, ...] = ()
    pii_usernames: tuple[str, ...] = ()

    def digest(self) -> str:
        return _canonical_digest({
            "definitions": sorted(self.definitions),
            "definition_digests": {n: definition_digest(n) for n in sorted(self.definitions)},
            "pii_emails": list(self.pii_emails),
            "pii_usernames": list(self.pii_usernames),
        })


def _marker(kind: str, definition_id: str) -> str:
    return f"[omitted:{kind}:{definition_id}]"


def _omission(kind: str, definition_id: str, start: int, length: int) -> dict:
    # start indexes the text the removing pass observed: the decoded source
    # for oversized bodies, the post-oversized text for span removals.
    return {"kind": kind, "definition": definition_id,
            "definition_digest": definition_digest(definition_id),
            "start": start, "length": length}


def _prune_tool_results(node, limit: int) -> list[int]:
    """Replace oversized tool_result content in place; return removed sizes."""
    removed: list[int] = []
    if isinstance(node, dict):
        if node.get("type") == "tool_result" and "content" in node:
            content = node["content"]
            size = len(content) if isinstance(content, str) else len(
                json.dumps(content, ensure_ascii=False, sort_keys=True))
            if size > limit:
                node["content"] = _marker("oversized-tool-result", "sanitize-v1")
                removed.append(size)
        for value in node.values():
            removed.extend(_prune_tool_results(value, limit))
    elif isinstance(node, list):
        for value in node:
            removed.extend(_prune_tool_results(value, limit))
    return removed


def _strip_oversized_bodies(text: str, omissions: list[dict]) -> str:
    """sanitize-v1: omit tool-result bodies over the declared limit, per JSONL line.

    Only omission-carrying lines are re-serialized (compact separators,
    deterministic); every untouched line passes through byte-identical.
    """
    pieces = text.split("\n")
    offset = 0
    for index, line in enumerate(pieces):
        # An oversized body implies an oversized line: JSON escaping never shrinks.
        if len(line) > OVERSIZED_LIMIT_BYTES and line.lstrip().startswith("{"):
            try:
                parsed = json.loads(line)
            except ValueError:
                parsed = None
            removed = _prune_tool_results(parsed, OVERSIZED_LIMIT_BYTES) if parsed else []
            if removed:
                for size in removed:
                    omissions.append(_omission("oversized-tool-result", "sanitize-v1",
                                               offset, size))
                pieces[index] = json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))
        offset += len(line) + 1
    return "\n".join(pieces)


def _collect_spans(text: str, config: ReaderConfig) -> list[tuple[int, int, str, str]]:
    """Every removal span (start, end, kind, definition) against one text."""
    spans: list[tuple[int, int, str, str]] = []
    if "sanitize-v1" in config.definitions:
        for pattern in _LINT.SECRET_PATTERNS.values():
            for match in pattern.finditer(text):
                spans.append((match.start(), match.end(), "secret-shape", "sanitize-v1"))
        for pattern in _LINT.LOCAL_PATH_PATTERNS:
            for match in pattern.finditer(text):
                start = match.start()
                if text[start] in _LEADING_CONTEXT:
                    start += 1  # keep the context character the lint shape captured
                end = match.end()
                while end < len(text) and not text[end].isspace():
                    end += 1  # remove the whole path token, not only the matched prefix
                spans.append((start, end, "local-absolute-user-path", "sanitize-v1"))
    if "pii-v1" in config.definitions:
        for email in config.pii_emails:
            for match in re.finditer(re.escape(email), text):
                spans.append((match.start(), match.end(), "email-address", "pii-v1"))
        for username in config.pii_usernames:
            for match in re.finditer(rf"\b{re.escape(username)}\b", text):
                spans.append((match.start(), match.end(), "host-username", "pii-v1"))
    return spans


def _merge_spans(spans: list[tuple[int, int, str, str]]) -> list[list]:
    """Earlier, longer spans absorb contained and overlapping ones, so one
    removed region is one omission (a username inside a removed path or email
    is not double-counted)."""
    merged: list[list] = []
    for start, end, kind, definition in sorted(spans, key=lambda s: (s[0], -(s[1] - s[0]))):
        if merged and start < merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
            continue
        merged.append([start, end, kind, definition])
    return merged


def _apply_spans(text: str, spans: list[list], omissions: list[dict]) -> str:
    pieces = []
    previous = 0
    for start, end, kind, definition in spans:
        pieces.append(text[previous:start])
        pieces.append(_marker(kind, definition))
        omissions.append(_omission(kind, definition, start, end - start))
        previous = end
    pieces.append(text[previous:])
    return "".join(pieces)


def read_source(payload: bytes, source_id: str, config: ReaderConfig) -> tuple[bytes, dict]:
    """Read one immutable source; return sanitized payload bytes and the manifest.

    Deterministic: identical payload and configuration produce identical bytes
    and an identical manifest. EXACT means output byte-identical to the
    source; otherwise every removal is one omission naming its kind and
    versioned definition (LOSSY). An undeclared omission definition is
    refused (OMISSION_DEFINITION_UNKNOWN).
    """
    for definition_id in config.definitions:
        definition_record(definition_id)
    source_digest = _sha256(payload)
    text = payload.decode("utf-8", errors="surrogateescape")
    omissions: list[dict] = []
    if "sanitize-v1" in config.definitions:
        text = _strip_oversized_bodies(text, omissions)
    text = _apply_spans(text, _merge_spans(_collect_spans(text, config)), omissions)
    sanitized = text.encode("utf-8", errors="surrogateescape")
    omissions.sort(key=lambda entry: (entry["start"], entry["kind"]))
    manifest = {
        "source_id": source_id,
        "source_digest": source_digest,
        "reader_id": READER_ID,
        "reader_version": READER_VERSION,
        "configuration_digest": config.digest(),
        "payload_digest": _sha256(sanitized),
        "fidelity": "LOSSY" if omissions else "EXACT",
        "omissions": omissions,
    }
    return sanitized, manifest


def resolve_sessions_dir(argument: str | None, environ: Mapping[str, str]) -> Path:
    """The sessions directory is never committed; it arrives per invocation."""
    value = argument or environ.get(SESSIONS_DIR_ENV, "")
    if not value:
        raise ValueError(
            f"SESSIONS_DIR_UNDECLARED: pass --sessions-dir or set {SESSIONS_DIR_ENV}")
    path = Path(value).expanduser()
    if not path.is_dir():
        raise ValueError("SESSIONS_DIR_MISSING: the declared sessions directory does not exist")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sessions-dir", default=None,
                        help=f"session transcript directory (or {SESSIONS_DIR_ENV})")
    parser.add_argument("--out", type=Path, default=ROOT / ".local" / "lineage" / "recordings",
                        help="output directory (default: gitignored .local/lineage/recordings)")
    parser.add_argument("--glob", default="*.jsonl", help="source filename pattern")
    parser.add_argument("--owner-email", default=os.environ.get(OWNER_EMAIL_ENV, ""),
                        help=f"pii-v1 owner email (or {OWNER_EMAIL_ENV}; never committed)")
    parser.add_argument("--host-username", default=getpass.getuser(),
                        help="pii-v1 host username (default: current user; never committed)")
    args = parser.parse_args(argv)
    try:
        sessions = resolve_sessions_dir(args.sessions_dir, os.environ)
    except ValueError as refusal:
        print(f"REFUSED: {refusal}")
        return 2
    config = ReaderConfig(pii_emails=tuple(v for v in [args.owner_email] if v),
                          pii_usernames=tuple(v for v in [args.host_username] if v))
    args.out.mkdir(parents=True, exist_ok=True)
    sources = sorted(sessions.glob(args.glob))
    lossy = 0
    for path in sources:
        source_id = f"claude-session:{path.stem}"
        sanitized, manifest = read_source(path.read_bytes(), source_id, config)
        stem = manifest["payload_digest"].split(":", 1)[1][:32]
        (args.out / f"{stem}.payload").write_bytes(sanitized)
        (args.out / f"{stem}.manifest.json").write_bytes(
            (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"))
        lossy += manifest["fidelity"] == "LOSSY"
        print(f"{source_id}: fidelity={manifest['fidelity']} "
              f"omissions={len(manifest['omissions'])} payload={manifest['payload_digest'][:23]}")
    print(f"read {len(sources)} sources ({lossy} LOSSY); payloads and manifests "
          "under --out (uncommitted; no host path printed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
