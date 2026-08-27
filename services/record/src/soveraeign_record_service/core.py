"""The operational System of Record: an append-preserving journal.

`ENGINEERING.md` names two Systems of Record. The design one is the governing
repository set. The operational one is this: an append-preserving journal of
addressed inputs, decisions, standing transitions, operations, observations,
receipts, and counter-records, recording what happened and under what authority.

Append-preserving is enforced rather than promised. Nothing here updates or
deletes a journal row. Retraction appends a counter-record and leaves the
original exactly where it was. Every entry carries the digest of the entry
before it, so a rewritten history stops verifying instead of quietly replacing
the real one.

Projections are derived. They are dropped and rebuilt from the journal alone,
and a projection can never be the thing an operation reads as authoritative.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable
import json
import sqlite3
import time
import uuid

from .digest import (
    BOUND_DIGEST_PROFILE, CURRENT_PROFILE, DIGEST_PROFILE, LEGACY_DIGEST_PROFILE,
    bound_digest as _bound_digest, canonical as _canonical, canonical_for,
    digest as _digest, digest_for_profile, legacy_canonical as _legacy_canonical,
    legacy_digest as _legacy_digest,
)
from .projections import ProjectionSurface

GENESIS = "0" * 64

# The design System of Record. Its documents govern; they are not operational
# event storage, and naming one as a journal source is refused rather than
# silently accepted.
DESIGN_SYSTEM_OF_RECORD = frozenset({
    "SYSTEM.md", "CONTRACT.md", "CLASSIFICATION.md", "PRD.md", "SPEC.md",
    "SDLC.md", "AGENTS.md", "ENGINEERING.md", "OPEN-SEAMS.md", "NAMING.md",
    "PUBLICATION.md", "ROADMAP.md", "STATUS.yaml", "AI-NATIVE.md", "BYOM.md",
})

ENTRY_KINDS = ("EVENT", "RECEIPT", "OBSERVATION", "COUNTER")


class DesignRecordRefused(PermissionError):
    """A governing document was offered as operational event storage."""


class BrokenChain(RuntimeError):
    """The journal no longer verifies against its own digest chain."""


class ProjectionNotAuthoritative(RuntimeError):
    """A projection was offered as the authoritative record."""


class UnknownEntry(KeyError):
    """The named entry is not in the journal."""


def _now() -> float:
    return time.time()


def _digest_for_profile(
    profile: str, previous: str, kind: str, subject: str, actor: str, payload: Any,
    *, entry_id: str | None = None, source_address: str | None = None,
    recorded_at: float | None = None,
) -> str:
    """Recompute one entry's digest under its own profile, or refuse the profile.

    The keyword arguments are what record-chain/v3 binds beyond v2. They are
    optional in the signature so a v1 or v2 caller is unchanged, and required by
    the v3 branch, which raises rather than grading an entry under a weaker
    profile than the one it was written with.
    """
    try:
        return digest_for_profile(
            profile, previous, kind, subject, actor, payload, entry_id=entry_id,
            source_address=source_address, recorded_at=recorded_at,
        )
    except ValueError as error:
        raise BrokenChain(str(error)) from error


class RecordService(ProjectionSurface):
    """An append-preserving operational journal over a local SQLite store."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.root / "record-service.sqlite3")
        self.db.row_factory = sqlite3.Row
        # WAL so a committed row survives an abrupt restart, and a transaction
        # that never commits leaves nothing behind.
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS journal(
              seq INTEGER PRIMARY KEY AUTOINCREMENT,
              entry_id TEXT NOT NULL UNIQUE,
              kind TEXT NOT NULL,
              subject TEXT NOT NULL,
              actor TEXT NOT NULL,
              source_address TEXT,
              payload_json TEXT NOT NULL,
              recorded_at REAL NOT NULL,
              prev_digest TEXT NOT NULL,
              entry_digest TEXT NOT NULL,
              digest_profile TEXT NOT NULL DEFAULT 'soveraeign-record-chain/v2'
            );
            CREATE TABLE IF NOT EXISTS subject_projection(
              subject TEXT PRIMARY KEY,
              entry_count INTEGER NOT NULL,
              last_kind TEXT NOT NULL,
              countered INTEGER NOT NULL,
              head_digest TEXT NOT NULL
            );
            """
        )
        columns = {row["name"] for row in self.db.execute("PRAGMA table_info(journal)")}
        if "digest_profile" not in columns:
            self.db.execute(
                "ALTER TABLE journal ADD COLUMN digest_profile TEXT NOT NULL "
                f"DEFAULT '{LEGACY_DIGEST_PROFILE}'"
            )
        self.db.commit()

    def close(self) -> None:
        """Release the store so the process can restart against it."""
        self.db.close()

    # ---- append path -------------------------------------------------------

    def head(self) -> str:
        """Return the digest of the newest entry, or the genesis digest."""
        row = self.db.execute(
            "SELECT entry_digest FROM journal ORDER BY seq DESC LIMIT 1"
        ).fetchone()
        return row["entry_digest"] if row else GENESIS

    def append(
        self,
        kind: str,
        subject: str,
        actor: str,
        payload: dict[str, Any],
        source_address: str | None = None,
    ) -> dict[str, Any]:
        """Append one entry and return it. Nothing in this class ever updates one."""
        if kind not in ENTRY_KINDS:
            raise ValueError(f"unknown entry kind {kind!r}")
        if source_address is not None and Path(source_address).name in DESIGN_SYSTEM_OF_RECORD:
            raise DesignRecordRefused(
                f"{source_address} governs system design and is not operational event storage"
            )
        previous = self.head()
        entry_id = f"entry_{uuid.uuid4().hex}"
        # Read the clock before hashing rather than at INSERT: under
        # record-chain/v3 the moment is bound into the digest, so the value in
        # the row and the value in the hash have to be the one reading.
        recorded_at = _now()
        digest = _bound_digest(previous, kind, subject, actor, payload,
                               entry_id=entry_id, source_address=source_address,
                               recorded_at=recorded_at)
        self.db.execute(
            "INSERT INTO journal(entry_id,kind,subject,actor,source_address,"
            "payload_json,recorded_at,prev_digest,entry_digest,digest_profile) "
            "VALUES(?,?,?,?,?,?,?,?,?,?)",
            (entry_id, kind, subject, actor, source_address,
             _canonical(payload), recorded_at, previous, digest, CURRENT_PROFILE),
        )
        self.db.commit()
        return self.entry(entry_id)

    def receipt(
        self, outcome: str, event: str, subject: str, actor: str,
        detail: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Append a terminal receipt for one attempted crossing or transition."""
        return self.append(
            "RECEIPT", subject, actor,
            {"outcome": outcome, "event": event, "detail": detail or {}},
        )

    def counter(self, entry_id: str, actor: str, reason: str) -> dict[str, Any]:
        """Counter an entry by appending. The original is never touched."""
        original = self.entry(entry_id)
        return self.append(
            "COUNTER", original["subject"], actor,
            {"counters": entry_id, "reason": reason},
        )

    # ---- read path ---------------------------------------------------------

    def entry(self, entry_id: str) -> dict[str, Any]:
        """Return one entry by id."""
        row = self.db.execute(
            "SELECT * FROM journal WHERE entry_id=?", (entry_id,)
        ).fetchone()
        if row is None:
            raise UnknownEntry(entry_id)
        item = dict(row)
        item["payload"] = json.loads(item.pop("payload_json"))
        return item

    def entries(self) -> list[dict[str, Any]]:
        """Return every entry in append order."""
        rows = self.db.execute("SELECT entry_id FROM journal ORDER BY seq").fetchall()
        return [self.entry(row["entry_id"]) for row in rows]

    def reconstruct(self) -> list[dict[str, Any]]:
        """Replay the journal, verifying every link and every payload encoding.

        The digest binds the payload's parsed value, not the bytes the column
        holds. Left there, byte-different but value-identical JSON went
        undetected, and duplicate-key injection with it: a committed row two
        readers read differently, endorsed by the chain. Requiring the stored
        bytes to be their profile's canonical encoding closes that, and costs
        nothing on a journal this service wrote, because it wrote them that way.
        """
        stored = {
            row["entry_id"]: row["payload_json"]
            for row in self.db.execute("SELECT entry_id,payload_json FROM journal")
        }
        previous, replayed = GENESIS, []
        for entry in self.entries():
            expected = _digest_for_profile(
                entry["digest_profile"], previous, entry["kind"], entry["subject"],
                entry["actor"], entry["payload"], entry_id=entry["entry_id"],
                source_address=entry["source_address"], recorded_at=entry["recorded_at"],
            )
            if entry["prev_digest"] != previous or entry["entry_digest"] != expected:
                raise BrokenChain(entry["entry_id"])
            try:
                encode = canonical_for(entry["digest_profile"])
            except ValueError as unknown:
                raise BrokenChain(str(unknown)) from None
            if stored.get(entry["entry_id"]) != encode(entry["payload"]):
                raise BrokenChain(
                    f"{entry['entry_id']}: payload bytes are not the canonical encoding "
                    "of the value the digest binds")
            previous = entry["entry_digest"]
            replayed.append(entry)
        return replayed

    def countered(self, entry_id: str) -> bool:
        """Report whether a counter-record exists for this entry."""
        for entry in self.entries():
            if entry["kind"] == "COUNTER" and entry["payload"].get("counters") == entry_id:
                return True
        return False

    # ---- projections -------------------------------------------------------
    #
    # Everything derived from the journal lives in `projections.ProjectionSurface`,
    # mixed into this class. What remains here is the journal itself.


def open_service(root: str | Path) -> RecordService:
    """Open the operational System of Record under ``root``."""
    return RecordService(root)


def digest_of(entries: Iterable[dict[str, Any]]) -> str:
    """Return the head digest of a replayed sequence."""
    last = GENESIS
    for entry in entries:
        last = entry["entry_digest"]
    return last
