"""Version identity survives relocation; reads depend on current custody only."""

from __future__ import annotations

import json
import shutil
import sys
import unittest
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from soveraeign_asset_service import AssetService  # noqa: E402
from soveraeign_asset_service.custody import (  # noqa: E402
    DigestMismatch,
    UnknownRecord,
    read_version,
)
from soveraeign_asset_service.routes import AssetRoutes  # noqa: E402
from soveraeign_asset_service.store import PayloadIntegrityError  # noqa: E402


class CustodyRelocation(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.original = self.root / "original"
        self.current = self.root / "current"
        self.data = b"Captured custody\x00\xff\n"
        source = self.root / "source.bin"
        source.write_bytes(self.data)
        service = AssetService(self.original)
        try:
            self.captured = service.ingest(source, "Fixture", "reader")
            self.version_id = self.captured["version_id"]
            self.digest = sha256(self.data).hexdigest()
            self.records = {
                table: [dict(row) for row in service.db.execute(f"SELECT * FROM {table}")]
                for table in ("assets", "versions", "sources")
            }
            self.receipts = service.receipts()
            self.pending = service.store.pending_operational_history()
        finally:
            service.close()
        source.unlink()

    def open_current(self, *, move: bool = False) -> AssetService:
        if move:
            self.original.rename(self.current)
            self.assertFalse(self.original.exists())
        else:
            shutil.copytree(self.original, self.current)
        service = AssetService(self.current)
        self.addCleanup(service.close)
        return service

    def current_blob(self) -> Path:
        return self.current / "blobs" / "sha256" / self.digest[:2] / self.digest

    def assert_read(self, service: AssetService) -> None:
        result = read_version(service, self.version_id, "reader")
        row, data = service.store.verified_version(self.version_id)
        self.assertEqual(data, self.data)
        self.assertEqual(result["bytes"], self.data)
        self.assertEqual(dict(row), self.records["versions"][0])
        for key in ("asset_id", "version_id", "source_id", "digest"):
            self.assertEqual(result[key], self.captured[key])
        receipt = next(r for r in service.receipts() if r["id"] == result["receipt_id"])
        self.assertEqual(receipt["event"], "asset.read-version")
        self.assertEqual(receipt["outcome"], "COMMITTED")
        self.assertEqual(receipt["subject_id"], self.version_id)
        payload = json.loads(receipt["payload_json"])
        self.assertEqual(payload["digest"], self.digest)
        self.assertEqual(payload["payload_address"], f"urn:sha256:{self.digest}")

    def assert_refused(self, service: AssetService, reason: str) -> dict:
        with self.assertRaises(PayloadIntegrityError):
            service.store.verified_version(self.version_id)
        with self.assertRaises(DigestMismatch) as caught:
            read_version(service, self.version_id, "reader")
        receipt = next(r for r in service.receipts() if r["id"] == caught.exception.receipt_id)
        self.assertEqual(receipt["event"], "asset.read-version")
        self.assertEqual(receipt["outcome"], "REFUSED")
        self.assertEqual(receipt["subject_id"], self.version_id)
        payload = json.loads(receipt["payload_json"])
        self.assertEqual(payload["reason"], reason)
        self.assertEqual(payload["version_id"], self.version_id)
        self.assertEqual(payload["asset_id"], self.captured["asset_id"])
        return payload

    def test_move_preserves_bytes_identity_history_and_pending_receipts(self) -> None:
        service = self.open_current(move=True)
        self.assertEqual(service.receipts(), self.receipts)
        self.assertEqual(service.store.pending_operational_history(), self.pending)
        self.assert_read(service)
        for table, records in self.records.items():
            observed = [dict(row) for row in service.db.execute(f"SELECT * FROM {table}")]
            self.assertEqual(observed, records)
        current_receipts = {row["id"]: row for row in service.receipts()}
        for receipt in self.receipts:
            self.assertEqual(current_receipts[receipt["id"]], receipt)
        self.assertEqual(len(current_receipts), len(self.receipts) + 1)
        self.assertTrue(set(self.pending) < set(service.store.pending_operational_history()))

    def test_copy_reads_current_bytes_with_original_still_readable(self) -> None:
        service = self.open_current()
        self.assert_read(service)
        original_blob = Path(self.records["versions"][0]["blob_path"])
        original_blob.write_bytes(b"changed original")
        self.assert_read(service)

    def test_missing_copy_refuses_without_falling_back_to_original(self) -> None:
        service = self.open_current()
        self.current_blob().unlink()
        self.assertEqual(Path(self.records["versions"][0]["blob_path"]).read_bytes(), self.data)
        payload = self.assert_refused(service, "PAYLOAD_ABSENT")
        self.assertEqual(payload["digest"], self.digest)

    def test_corrupt_copy_refuses_without_falling_back_to_original(self) -> None:
        service = self.open_current()
        corrupt = b"corrupt copy"
        self.current_blob().write_bytes(corrupt)
        self.assertEqual(Path(self.records["versions"][0]["blob_path"]).read_bytes(), self.data)
        payload = self.assert_refused(service, "DIGEST_MISMATCH")
        self.assertEqual(payload["recorded"], self.digest)
        self.assertEqual(payload["observed"], sha256(corrupt).hexdigest())

    def test_unknown_version_preserves_refusal_and_receipt(self) -> None:
        service = self.open_current(move=True)
        with self.assertRaises(KeyError):
            service.store.verified_version("unknown")
        with self.assertRaises(UnknownRecord) as caught:
            read_version(service, "unknown", "reader")
        receipt = next(r for r in service.receipts() if r["id"] == caught.exception.receipt_id)
        self.assertEqual(receipt["outcome"], "REFUSED")
        self.assertEqual(json.loads(receipt["payload_json"]),
                         {"reason": "VERSION_UNKNOWN", "version_id": "unknown"})

    def test_malformed_digest_cannot_read_outside_current_custody(self) -> None:
        service = self.open_current(move=True)
        outside = self.root / "outside.bin"
        outside.write_bytes(self.data)
        for digest in (str(outside), "../../../outside.bin", "..\\outside.bin",
                       "f" * 63, "g" * 64, self.digest.upper(), ""):
            with self.subTest(digest=digest):
                service.db.execute("UPDATE versions SET digest=? WHERE id=?",
                                   (digest, self.version_id))
                service.db.commit()
                with patch.object(Path, "read_bytes") as reads:
                    payload = self.assert_refused(service, "DIGEST_MISMATCH")
                    reads.assert_not_called()
                self.assertEqual(payload["recorded"], digest)

    def test_blob_digest_route_refusal_survives_reopening_without_payload_read(self) -> None:
        service = self.open_current(move=True)
        malformed = b"\x00\xff"
        service.db.execute("UPDATE versions SET digest=? WHERE id=?",
                           (malformed, self.version_id))
        service.db.commit()
        with patch.object(Path, "read_bytes") as reads:
            with self.assertRaises(PayloadIntegrityError):
                service.store.verified_version(self.version_id)
            receipt = AssetRoutes(service).call(
                "read-version", {"version_id": self.version_id}, "reader")
            reads.assert_not_called()
        self.assertEqual(receipt["outcome"], "REFUSED")
        self.assertEqual(receipt["event"], "asset.read-version")
        self.assertEqual(receipt["subject_type"], "version")
        self.assertEqual(receipt["subject_id"], self.version_id)
        self.assertEqual(receipt["actor"], "reader")
        payload = json.loads(receipt["payload_json"])
        self.assertEqual(payload, {
            "reason": "DIGEST_MISMATCH", "version_id": self.version_id,
            "asset_id": self.captured["asset_id"], "observed": None,
            "recorded": {"sqlite_type": "blob", "hex": "00ff"},
        })
        service.close()
        reopened = AssetService(self.current)
        self.addCleanup(reopened.close)
        recovered = next(r for r in reopened.receipts() if r["id"] == receipt["id"])
        self.assertEqual(recovered, receipt)
        self.assertEqual(len(reopened.receipts()), len(self.receipts) + 1)
        self.assertIn(receipt["id"], reopened.store.pending_operational_history())
        stored = reopened.db.execute(
            "SELECT digest,typeof(digest) FROM versions WHERE id=?", (self.version_id,)
        ).fetchone()
        self.assertEqual(tuple(stored), (malformed, "blob"))
        recorded = json.loads(recovered["payload_json"])["recorded"]
        self.assertEqual(bytes.fromhex(recorded["hex"]), malformed)

    def test_verified_version_retains_size_check_after_move(self) -> None:
        service = self.open_current(move=True)
        service.db.execute("UPDATE versions SET size=size+1 WHERE id=?", (self.version_id,))
        service.db.commit()
        with self.assertRaises(PayloadIntegrityError):
            service.store.verified_version(self.version_id)


if __name__ == "__main__":
    unittest.main()
