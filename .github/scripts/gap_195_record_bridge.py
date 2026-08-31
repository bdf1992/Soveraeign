from __future__ import annotations

from pathlib import Path


def replace(path: str, old: str, new: str, *, count: int = 1) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"expected block missing in {path}: {old[:120]!r}")
    target.write_text(text.replace(old, new, count), encoding="utf-8", newline="\n")


operational = '''"""The Asset Service port into the append-preserving operational journal.

Asset owns its domain state. Record owns operational history. This module is the
small adapter between those ownership boundaries: it mirrors an already-durable
Asset terminal receipt into Record without making Record authoritative for Asset
rows and without treating the mirror as a grant.
"""

from __future__ import annotations

from typing import Any, Protocol
import json


SOURCE_ADDRESS = "asset-service"
RECORD_KIND = "asset-terminal-receipt"


class OperationalJournal(Protocol):
    """Only the Record behavior Asset needs; no dependency on Record implementation."""

    def entries(self) -> list[dict[str, Any]]: ...

    def append(self, kind: str, subject: str, actor: str, payload: dict[str, Any],
               source_address: str | None = None) -> dict[str, Any]: ...


def _existing(journal: OperationalJournal, receipt_id: str) -> dict[str, Any] | None:
    """A prior mirror of this exact local receipt, if one already reached Record."""
    for entry in journal.entries():
        if entry.get("kind") != "RECEIPT" or entry.get("source_address") != SOURCE_ADDRESS:
            continue
        detail = entry.get("payload", {}).get("detail", {})
        if detail.get("record_kind") == RECORD_KIND and detail.get("asset_receipt_id") == receipt_id:
            return entry
    return None


def mirror_receipt(journal: OperationalJournal, receipt: dict[str, Any]) -> str:
    """Mirror one committed Asset receipt idempotently and return its Record entry id."""
    existing = _existing(journal, receipt["id"])
    if existing is not None:
        return existing["entry_id"]
    detail = {
        "record_kind": RECORD_KIND,
        "source_service": "asset",
        "asset_receipt_id": receipt["id"],
        "subject_type": receipt["subject_type"],
        "local_payload": json.loads(receipt["payload_json"]),
        "local_created_at": receipt["created_at"],
    }
    entry = journal.append(
        "RECEIPT", f"asset:{receipt['subject_type']}:{receipt['subject_id']}",
        receipt["actor"],
        {"outcome": receipt["outcome"], "event": receipt["event"], "detail": detail},
        source_address=SOURCE_ADDRESS,
    )
    return entry["entry_id"]


__all__ = ["OperationalJournal", "mirror_receipt"]
'''
Path("services/asset/src/soveraeign_asset_service/operational.py").write_text(
    operational, encoding="utf-8", newline="\n")

# Store.receipt is already the terminal choke point for Asset transitions. Make the
# local receipt + outbox intent one SQLite transaction; mirror only after that commit.
replace(
    "services/asset/src/soveraeign_asset_service/store.py",
    '''from typing import Any, Callable
''',
    '''from typing import Any, Callable

from soveraeign_asset_service.operational import OperationalJournal, mirror_receipt
''',
)
replace(
    "services/asset/src/soveraeign_asset_service/store.py",
    '''CREATE TABLE IF NOT EXISTS receipts(
  id TEXT PRIMARY KEY, outcome TEXT NOT NULL, event TEXT NOT NULL,
  subject_type TEXT NOT NULL, subject_id TEXT NOT NULL,
  actor TEXT NOT NULL, payload_json TEXT NOT NULL, created_at REAL NOT NULL);
''',
    '''CREATE TABLE IF NOT EXISTS receipts(
  id TEXT PRIMARY KEY, outcome TEXT NOT NULL, event TEXT NOT NULL,
  subject_type TEXT NOT NULL, subject_id TEXT NOT NULL,
  actor TEXT NOT NULL, payload_json TEXT NOT NULL, created_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS operational_outbox(
  receipt_id TEXT PRIMARY KEY REFERENCES receipts(id),
  record_entry_id TEXT, delivered_at REAL);
''',
)
replace(
    "services/asset/src/soveraeign_asset_service/store.py",
    '''    def __init__(self, root: str | Path, clock: Callable[[], float] = time.time) -> None:
''',
    '''    def __init__(self, root: str | Path, clock: Callable[[], float] = time.time,
                 operational_record: OperationalJournal | None = None) -> None:
''',
)
replace(
    "services/asset/src/soveraeign_asset_service/store.py",
    '''        self.now = clock
        self.db = sqlite3.connect(self.root / "asset-service.sqlite3")
''',
    '''        self.now = clock
        self.operational_record = operational_record
        self.db = sqlite3.connect(self.root / "asset-service.sqlite3")
''',
)
replace(
    "services/asset/src/soveraeign_asset_service/store.py",
    '''        self.db.executescript(combined)
        self.db.commit()

    def close(self) -> None:
        """Close the underlying connection."""
        self.db.close()

    def receipt(self, outcome: str, event: str, subject_type: str, subject_id: str,
                actor: str, payload: dict[str, Any]) -> str:
        """Write one receipt row and return its identifier. The caller commits."""
        receipt = new_id("rcpt")
        self.db.execute(
            "INSERT INTO receipts VALUES(?,?,?,?,?,?,?,?)",
            (receipt, outcome, event, subject_type, subject_id, actor,
             json.dumps(payload, sort_keys=True), self.now()),
        )
        return receipt
''',
    '''        self.db.executescript(combined)
        self.db.commit()
        self._try_flush_operational_history()

    def close(self) -> None:
        """Best-effort the outbox once more, then close the underlying connection."""
        self._try_flush_operational_history()
        self.db.close()

    def receipt(self, outcome: str, event: str, subject_type: str, subject_id: str,
                actor: str, payload: dict[str, Any]) -> str:
        """Commit one local terminal receipt and its Record outbox intent together.

        Asset state changes made immediately before this call share this SQLite
        transaction. Record delivery happens only after that transaction commits,
        so the operational journal never gets ahead of the local terminal receipt.
        A failed Record delivery leaves a durable outbox row for replay instead of
        rolling back or misreporting already-committed Asset state.
        """
        receipt = new_id("rcpt")
        created_at = self.now()
        self.db.execute(
            "INSERT INTO receipts VALUES(?,?,?,?,?,?,?,?)",
            (receipt, outcome, event, subject_type, subject_id, actor,
             json.dumps(payload, sort_keys=True), created_at),
        )
        self.db.execute(
            "INSERT INTO operational_outbox(receipt_id,record_entry_id,delivered_at) "
            "VALUES(?,NULL,NULL)", (receipt,))
        self.db.commit()
        self._try_flush_operational_history()
        return receipt

    def pending_operational_history(self) -> list[str]:
        """Local terminal receipts not yet confirmed in the bound Record journal."""
        return [row["receipt_id"] for row in self.db.execute(
            "SELECT receipt_id FROM operational_outbox WHERE record_entry_id IS NULL "
            "ORDER BY rowid")]

    def flush_operational_history(self) -> int:
        """Replay the durable outbox into Record, idempotently, when the port is bound."""
        if self.operational_record is None:
            return 0
        pending = self.db.execute(
            "SELECT r.* FROM receipts r JOIN operational_outbox o ON o.receipt_id=r.id "
            "WHERE o.record_entry_id IS NULL ORDER BY r.created_at,r.id").fetchall()
        delivered = 0
        for row in pending:
            entry_id = mirror_receipt(self.operational_record, dict(row))
            self.db.execute(
                "UPDATE operational_outbox SET record_entry_id=?,delivered_at=? "
                "WHERE receipt_id=?", (entry_id, self.now(), row["id"]))
            self.db.commit()
            delivered += 1
        return delivered

    def _try_flush_operational_history(self) -> None:
        """Do not turn an unavailable Record port into a false rollback of Asset state."""
        if self.operational_record is None:
            return
        try:
            self.flush_operational_history()
        except (OSError, RuntimeError, ValueError, sqlite3.Error):
            # The local outbox is the durable evidence that delivery is still owed.
            # Explicit callers may call flush_operational_history() to surface the
            # underlying error; terminal Asset operations keep their truthful local
            # outcome rather than reporting failure after their state already committed.
            return
''',
)

# Asset owns domain state while accepting the already-declared Record port as a
# dependency. No Record implementation import crosses into the service package.
replace(
    "services/asset/src/soveraeign_asset_service/core.py",
    '''from soveraeign_asset_service.organization import Organization, OrganizationRefused
from soveraeign_asset_service.projections import Projections
''',
    '''from soveraeign_asset_service.operational import OperationalJournal
from soveraeign_asset_service.organization import Organization, OrganizationRefused
from soveraeign_asset_service.projections import Projections
''',
)
replace(
    "services/asset/src/soveraeign_asset_service/core.py",
    '''    def __init__(self, root: str | Path, clock: Callable[[], float] = time.time):
        self.store = Store(root, clock)
''',
    '''    def __init__(self, root: str | Path, clock: Callable[[], float] = time.time,
                 operational_record: OperationalJournal | None = None):
        self.store = Store(root, clock, operational_record)
''',
)
replace(
    "services/asset/src/soveraeign_asset_service/core.py",
    '''The SQLite database is the
canonical reference ledger for this slice; the search and graph tables are
disposable projections.
''',
    '''The SQLite database remains the canonical domain ledger for this slice; the
search and graph tables are disposable projections. When the declared Record port
is bound, each terminal receipt is durably outboxed with that local transaction and
mirrored into Record as operational history. Record does not become authority over
Asset rows by receiving that history.
''',
)

# The local Node composition is the actual service-to-service crossing.
replace(
    "scripts/sovnode/composition.py",
    '''    "services/asset/src/soveraeign_asset_service/core.py",
    "services/asset/src/soveraeign_asset_service/custody.py",
''',
    '''    "services/asset/src/soveraeign_asset_service/core.py",
    "services/asset/src/soveraeign_asset_service/store.py",
    "services/asset/src/soveraeign_asset_service/operational.py",
    "services/asset/src/soveraeign_asset_service/custody.py",
''',
)
replace(
    "scripts/sovnode/composition.py",
    '''        self.asset = AssetService(root / "asset")
''',
    '''        self.asset = AssetService(root / "asset", operational_record=self.record)
''',
)

# The existing independent Gateway witness already exercises Asset through Record;
# bind the same port there and let the independent observer verify the extra evidence.
replace(
    "scripts/gateway_witness_driver.py",
    '''    asset = AssetService(state / "asset")
''',
    '''    asset = AssetService(state / "asset", operational_record=record)
''',
)
replace(
    "scripts/gateway_observe.py",
    '''        terminal = caller_output.get("returned_receipt")
        receipts = _asset_rows(state, "receipts")
''',
    '''        terminal = caller_output.get("returned_receipt")
        receipts = _asset_rows(state, "receipts")
''',
)
# Insert the independent mirror check after the terminal receipt itself has been
# validated, so the observer compares two independently read stores.
replace(
    "scripts/gateway_observe.py",
    '''        if (terminal.get("actor") != actor or terminal.get("event") != "asset.ingest-asset"
                or terminal.get("outcome") != "COMMITTED"):
            defects.append("TERMINAL_ATTRIBUTION_INVALID")
        if (returned["payload"].get("routing_entry_id") != routing["entry_id"]
''',
    '''        if (terminal.get("actor") != actor or terminal.get("event") != "asset.ingest-asset"
                or terminal.get("outcome") != "COMMITTED"):
            defects.append("TERMINAL_ATTRIBUTION_INVALID")
        mirrors = [row for row in rows
                   if row["kind"] == "RECEIPT"
                   and row.get("source_address") == "asset-service"
                   and row["payload"].get("detail", {}).get("asset_receipt_id")
                   == terminal.get("id")]
        if (len(mirrors) != 1
                or mirrors[0]["actor"] != actor
                or mirrors[0]["payload"].get("outcome") != "COMMITTED"
                or mirrors[0]["payload"].get("event") != "asset.ingest-asset"
                or mirrors[0]["payload"].get("detail", {}).get("record_kind")
                   != "asset-terminal-receipt"):
            defects.append("ASSET_OPERATIONAL_HISTORY_INVALID")
        if (returned["payload"].get("routing_entry_id") != routing["entry_id"]
''',
)

# Focused service evidence: normal delivery, durable retry, and idempotent replay.
test = '''from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "services" / "asset" / "src"))
sys.path.insert(0, str(ROOT / "services" / "record" / "src"))

from soveraeign_asset_service import AssetService  # noqa: E402
from soveraeign_record_service import RecordService  # noqa: E402


class FailingJournal:
    def entries(self):
        return []

    def append(self, *args, **kwargs):
        raise RuntimeError("record unavailable")


class OperationalRecordBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / "source.txt"
        self.source.write_bytes(b"operational history")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    @staticmethod
    def mirrors(record: RecordService) -> list[dict]:
        return [entry for entry in record.reconstruct()
                if entry["kind"] == "RECEIPT"
                and entry.get("source_address") == "asset-service"]

    def test_ingest_terminal_receipt_reaches_record_without_moving_domain_state(self) -> None:
        record = RecordService(self.root / "record")
        asset = AssetService(self.root / "asset", operational_record=record)
        try:
            result = asset.ingest(self.source, "Source", "operator")
            mirrors = self.mirrors(record)
            self.assertEqual(len(mirrors), 1)
            detail = mirrors[0]["payload"]["detail"]
            self.assertEqual(detail["asset_receipt_id"], result["receipt_id"])
            self.assertEqual(mirrors[0]["payload"]["event"], "asset.ingest-asset")
            self.assertEqual(mirrors[0]["payload"]["outcome"], "COMMITTED")
            self.assertEqual(asset.store.pending_operational_history(), [])
            self.assertEqual(asset.history(result["asset_id"])[0]["version_id"],
                             result["version_id"])
        finally:
            asset.close()
            record.close()

    def test_record_outage_leaves_a_durable_outbox_that_replays_on_restart(self) -> None:
        asset = AssetService(self.root / "asset", operational_record=FailingJournal())
        result = asset.ingest(self.source, "Source", "operator")
        self.assertEqual(asset.store.pending_operational_history(), [result["receipt_id"]])
        asset.close()

        record = RecordService(self.root / "record")
        resumed = AssetService(self.root / "asset", operational_record=record)
        try:
            self.assertEqual(resumed.store.pending_operational_history(), [])
            mirrors = self.mirrors(record)
            self.assertEqual(len(mirrors), 1)
            self.assertEqual(mirrors[0]["payload"]["detail"]["asset_receipt_id"],
                             result["receipt_id"])
        finally:
            resumed.close()
            record.close()

    def test_replaying_an_unacknowledged_outbox_does_not_duplicate_record_history(self) -> None:
        record = RecordService(self.root / "record")
        asset = AssetService(self.root / "asset", operational_record=record)
        try:
            result = asset.ingest(self.source, "Source", "operator")
            self.assertEqual(len(self.mirrors(record)), 1)
            asset.db.execute(
                "UPDATE operational_outbox SET record_entry_id=NULL,delivered_at=NULL "
                "WHERE receipt_id=?", (result["receipt_id"],))
            asset.db.commit()
            self.assertEqual(asset.store.flush_operational_history(), 1)
            self.assertEqual(len(self.mirrors(record)), 1)
            self.assertEqual(asset.store.pending_operational_history(), [])
        finally:
            asset.close()
            record.close()

    def test_other_receipted_asset_transitions_share_the_same_bridge(self) -> None:
        record = RecordService(self.root / "record")
        asset = AssetService(self.root / "asset", operational_record=record)
        try:
            session = asset.open_session("operator", "human")
            asset.grant("operator", "operator", "operate:derive", session_id=session)
            events = [entry["payload"]["event"] for entry in self.mirrors(record)]
            self.assertIn("session.open", events)
            self.assertIn("authority.grant", events)
        finally:
            asset.close()
            record.close()


if __name__ == "__main__":
    unittest.main()
'''
Path("services/asset/tests/test_operational_record.py").write_text(
    test, encoding="utf-8", newline="\n")
