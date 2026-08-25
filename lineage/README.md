# Lineage

Attributed ancestry for Soveraeign. This directory commits manifests and the
source lock only; it never commits payload bytes.

- `SOURCES.lock` is a JSON enumeration of history sources: git commits (SHA and
  subject; author names and emails are deliberately never captured), GitHub
  pull requests and issues (number, title, state, read read-only through `gh`),
  and Claude Code session files (session id, byte size, SHA-256 of the raw
  bytes; a digest of raw bytes reveals no content, and the host directory is
  never recorded). Each entry carries the SPEC.md `Source` fields:
  `source_id`, `source_address`, `payload_digest`, `payload_size`,
  `captured_at`, `captured_by` (an actor name, never an email).
- Sanitized payload bytes live in the local, uncommitted Asset Service
  content-addressed store. They are rebuildable by re-running the reader:
  `python services/asset/scripts/history_sources.py --sessions-dir <host
  sessions directory>` (or set `SOVERAEIGN_SESSIONS_DIR`). Session entries are
  point-in-time captures; a live session file grows after capture.
- `lineage/evidence/` holds immutable attributed input when present. Evidence
  files are never edited (`decisions/0003-evidence-boundary.md`); this
  enumeration does not touch them.

`scripts/verify_bootstrap.py` checks the lock structurally and refuses a lock
that leaks an email address or an absolute host path. The reader itself refuses
to write such a lock (`services/asset/scripts/history_sources.py`).

Standing: the lock is a capture record at proposal standing. Evidence grants no
authority; nothing here is ratified by existing.
