#!/usr/bin/env python3
"""Enumerate history sources and seed lineage/SOURCES.lock.

Sources enumerated (SPEC.md `Source`: source_id, source_address, payload_digest,
payload_size, captured_at, captured_by):

- git commits: SHA and subject line. Author names and emails are deliberately
  never requested from git, so they cannot leak into the lock.
- GitHub pull requests and issues: number, title, state, via read-only `gh`.
- Claude Code session files: session id (file stem), byte size, and SHA-256 of
  the raw bytes. A digest of raw bytes reveals no content. The directory is
  taken from --sessions-dir or SOVERAEIGN_SESSIONS_DIR and is never recorded.

The lock commits addresses and digests only. Payload bytes stay outside the
repository (the local content-addressed store), rebuildable by re-running this
reader. Before writing, the rendered lock is scanned for email addresses and
absolute host paths; a hit refuses the whole write rather than sanitizing it
silently. Effect class: RECORD_LOCAL.
"""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import argparse
import json
import os
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
LOCK_PATH = ROOT / "lineage" / "SOURCES.lock"
LOCK_FORMAT = "soveraeign-sources-lock/1"
SESSIONS_ENV = "SOVERAEIGN_SESSIONS_DIR"

# Shapes that must never enter the committed lock. The path pattern is built
# without a literal user-path substring so repository lint never matches this
# module's own source text.
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
HOST_PATH_PATTERN = re.compile(r"[/\\](?:Users|home)[/\\]")


def digest(payload: bytes) -> str:
    return "sha256:" + sha256(payload).hexdigest()


def run(command: list[str]) -> str:
    """Run one read-only subprocess with a bounded wait."""
    result = subprocess.run(command, cwd=ROOT, check=True, capture_output=True,
                            text=True, encoding="utf-8", timeout=60)
    return result.stdout


def enumerate_commits() -> list[tuple[str, str]]:
    """(sha, subject) per commit on the current branch, newest first."""
    lines = run(["git", "log", "--format=%H%x1f%s"]).splitlines()
    return [tuple(line.split("\x1f", 1)) for line in lines if "\x1f" in line]


def enumerate_github(kind: str) -> list[dict]:
    """Read-only `gh pr list` / `gh issue list`: number, title, state."""
    raw = run(["gh", kind, "list", "--state", "all", "--limit", "500",
               "--json", "number,title,state"])
    return sorted(json.loads(raw), key=lambda item: item["number"])


def enumerate_sessions(directory: Path) -> list[tuple[str, int, str]]:
    """(session_id, byte size, sha256 of raw bytes) per session file.

    Only files directly under the directory count; the directory path itself is
    read here and recorded nowhere.
    """
    sessions = []
    for path in sorted(directory.glob("*.jsonl")):
        payload = path.read_bytes()
        sessions.append((path.stem, len(payload), digest(payload)))
    return sessions


def source(kind: str, address: str, payload_digest: str, payload_size: int,
           captured_at: str, captured_by: str, **extra: str) -> dict:
    entry = {
        "kind": kind,
        "source_id": f"{kind}:{address}",
        "source_address": address,
        "payload_digest": payload_digest,
        "payload_size": payload_size,
        "captured_at": captured_at,
        "captured_by": captured_by,
    }
    entry.update(extra)
    return entry


def build_lock(commits: list[tuple[str, str]], pulls: list[dict],
               issues: list[dict], sessions: list[tuple[str, int, str]],
               captured_at: str, captured_by: str) -> dict:
    """Assemble the lock document. Digests for git and GitHub sources cover the
    captured representation recorded here; session digests cover raw bytes."""
    sources = []
    for sha, subject in commits:
        payload = f"{sha}\t{subject}\n".encode("utf-8")
        sources.append(source("git-commit", sha, digest(payload), len(payload),
                              captured_at, captured_by, title=subject))
    for kind, items in (("github-pr", pulls), ("github-issue", issues)):
        for item in items:
            record = {"number": item["number"], "state": item["state"],
                      "title": item["title"]}
            payload = json.dumps(record, sort_keys=True).encode("utf-8")
            sources.append(source(kind, str(item["number"]), digest(payload),
                                  len(payload), captured_at, captured_by,
                                  title=item["title"], state=item["state"]))
    for session_id, size, session_digest in sessions:
        sources.append(source("session-file", session_id, session_digest, size,
                              captured_at, captured_by))
    counts = {}
    for entry in sources:
        counts[entry["kind"]] = counts.get(entry["kind"], 0) + 1
    return {
        "lock_format": LOCK_FORMAT,
        "captured_at": captured_at,
        "captured_by": captured_by,
        "counts": counts,
        "sources": sources,
    }


def render(lock: dict) -> str:
    return json.dumps(lock, indent=2, sort_keys=True) + "\n"


def sensitive(text: str) -> str | None:
    """Name the first shape that must not enter the lock, or None."""
    if EMAIL_PATTERN.search(text):
        return "an email address"
    if HOST_PATH_PATTERN.search(text):
        return "an absolute host path"
    return None


def write_lock(lock: dict, path: Path) -> str | None:
    """Write the rendered lock, or return a refusal reason and write nothing."""
    rendered = render(lock)
    reason = sensitive(rendered)
    if reason:
        return f"{reason} would enter the lock; nothing written"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(rendered.encode("utf-8"))
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sessions-dir", type=Path,
                        default=os.environ.get(SESSIONS_ENV))
    parser.add_argument("--captured-by", default="Bdo",
                        help="actor name, never an email")
    parser.add_argument("--output", type=Path, default=LOCK_PATH)
    args = parser.parse_args(argv)

    if args.sessions_dir is None:
        print(f"REFUSED: UNREADABLE: no sessions directory; pass --sessions-dir "
              f"or set {SESSIONS_ENV} (the host path is never recorded)")
        return 1
    if not args.sessions_dir.is_dir():
        print("REFUSED: UNREADABLE: sessions directory is not a readable directory")
        return 1

    captured_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    lock = build_lock(enumerate_commits(), enumerate_github("pr"),
                      enumerate_github("issue"),
                      enumerate_sessions(args.sessions_dir),
                      captured_at, args.captured_by)
    refusal = write_lock(lock, args.output)
    if refusal:
        print(f"REFUSED: {refusal}")
        return 1
    summary = ", ".join(f"{kind}={count}"
                        for kind, count in sorted(lock["counts"].items()))
    print(f"seeded {args.output.name}: {summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
