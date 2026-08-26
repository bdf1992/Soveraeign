"""Export and restore: making the record survive its medium (decisions/0049).

`ENGINEERING.md` now carries a durability concern, and this is its smallest
honest realization. An export is a portable document of the whole journal;
a restore replays that document into an empty store and proves it arrived
whole. Neither introduces technology: the journal already chains every entry
to the digest of the one before it, so a copy either replays into the same
chain or visibly does not.

What self-verification does and does not reach is worth stating plainly,
because the difference is the same shape as the root-recovery problem in
`decisions/0048`.

An export detects, on its own:

- an edited payload, actor, subject, or kind — the entry's digest stops matching
  what its own contents produce;
- a reordered pair — each entry names its predecessor's digest;
- an entry removed from the middle — the link across the hole breaks.

An export cannot detect, on its own:

- **truncation.** Drop the last N entries and the remainder is a perfectly
  valid shorter journal. Every link holds. Nothing internal to the document
  says how long it was supposed to be, and rewriting the declared head in the
  header is as easy as dropping the entries.

So the export declares its head digest, and detecting truncation means holding
that digest somewhere the export does not reach — written down beside the
recovery secrets, for instance. This is not a weakness of the chain; it is what
a chain is. A record cannot certify its own completeness from the inside, in
the same way the root cannot recover itself from inside the node.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from soveraeign_record_service.core import (
    DIGEST_PROFILE, GENESIS, LEGACY_DIGEST_PROFILE, BrokenChain, RecordService,
    _canonical, _digest_for_profile,
)

EXPORT_SCHEMA = "soveraeign-record-export/v2"
LEGACY_EXPORT_SCHEMA = "soveraeign-record-export/v1"
ENTRY_FIELDS_V1 = ("entry_id", "kind", "subject", "actor", "source_address", "payload",
                   "recorded_at", "prev_digest", "entry_digest")
ENTRY_FIELDS = ENTRY_FIELDS_V1 + ("digest_profile",)


class ExportRefused(RuntimeError):
    """The journal could not be exported as it stands."""


class RestoreRefused(RuntimeError):
    """The export could not be restored into this store."""


class TruncatedExport(RestoreRefused):
    """The export replays cleanly but does not reach the head it declares."""


def export_document(service: RecordService) -> dict[str, Any]:
    """Verify the journal, then render it as a portable self-verifying document.

    An unverifiable journal is never exported: a copy of a broken chain is a
    broken chain that now exists twice.
    """
    try:
        entries = service.reconstruct()
    except BrokenChain as broken:
        raise ExportRefused(f"journal does not verify at {broken}; nothing exported") from broken
    return {
        "export_schema": EXPORT_SCHEMA,
        "entry_count": len(entries),
        "head_digest": entries[-1]["entry_digest"] if entries else GENESIS,
        "entries": [{field: entry.get(field) for field in ENTRY_FIELDS} for entry in entries],
    }


def write_export(service: RecordService, path: str | Path) -> dict[str, Any]:
    """Write an export to ``path``. Where the copy then lives is the operator's act."""
    document = export_document(service)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return document


def verify_export(document: Any, *, expected_head: str | None = None) -> str:
    """Replay an export without a database and return the head it actually reaches.

    Pass ``expected_head`` — held outside this document — to detect truncation.
    Without it, a truncated export verifies, because a shorter journal is a
    valid journal.
    """
    if not isinstance(document, dict) or document.get("export_schema") not in {
        EXPORT_SCHEMA, LEGACY_EXPORT_SCHEMA
    }:
        raise RestoreRefused("not a Soveraeign record export")
    legacy = document["export_schema"] == LEGACY_EXPORT_SCHEMA
    entries = document.get("entries")
    if not isinstance(entries, list):
        raise RestoreRefused("export carries no entry list")
    previous = GENESIS
    for position, entry in enumerate(entries):
        required_fields = ENTRY_FIELDS_V1 if legacy else ENTRY_FIELDS
        missing = [field for field in required_fields if field not in entry]
        if missing:
            raise RestoreRefused(f"entry {position} lacks {missing}")
        profile = LEGACY_DIGEST_PROFILE if legacy else entry["digest_profile"]
        expected = _digest_for_profile(
            profile, previous, entry["kind"], entry["subject"], entry["actor"],
            entry["payload"]
        )
        if entry["prev_digest"] != previous:
            raise BrokenChain(f"entry {position} does not follow its predecessor")
        if entry["entry_digest"] != expected:
            raise BrokenChain(f"entry {position} digest does not match its contents")
        previous = entry["entry_digest"]
    if document.get("entry_count") != len(entries):
        raise RestoreRefused("declared entry count does not match the entries carried")
    if document.get("head_digest") != previous:
        raise BrokenChain("declared head does not match the replayed head")
    if expected_head is not None and expected_head != previous:
        raise TruncatedExport(
            f"export reaches {previous} but the head held outside it is {expected_head}; "
            "entries are missing from the end")
    return previous


def restore(service: RecordService, document: Any, *,
            expected_head: str | None = None) -> int:
    """Replay a verified export into an empty store, then prove the head matches.

    Refuses a store that already holds entries. Restoring into a live journal
    would interleave two histories into one chain that verifies as neither.
    """
    if service.head() != GENESIS:
        raise RestoreRefused("store already holds a journal; restore only into an empty one")
    head = verify_export(document, expected_head=expected_head)
    legacy = document["export_schema"] == LEGACY_EXPORT_SCHEMA
    rows = [
        (entry["entry_id"], entry["kind"], entry["subject"], entry["actor"],
         entry["source_address"], _canonical(entry["payload"]), entry["recorded_at"],
         entry["prev_digest"], entry["entry_digest"],
         LEGACY_DIGEST_PROFILE if legacy else entry["digest_profile"])
        for entry in document["entries"]
    ]
    service.db.executemany(
        "INSERT INTO journal(entry_id,kind,subject,actor,source_address,"
        "payload_json,recorded_at,prev_digest,entry_digest,digest_profile) "
        "VALUES(?,?,?,?,?,?,?,?,?,?)",
        rows,
    )
    service.db.commit()
    restored = service.reconstruct()
    if service.head() != head:
        raise RestoreRefused("restored journal does not reach the exported head")
    service.rebuild_projections()
    return len(restored)


def restore_file(service: RecordService, path: str | Path, *,
                 expected_head: str | None = None) -> int:
    """Restore from a file written by ``write_export``."""
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RestoreRefused(f"export at {path} is unreadable: {error}") from error
    return restore(service, document, expected_head=expected_head)
