"""Fixtures for the reader-to-driver binding (ASSET-HL-4 wiring).

Positive cases prove the adapter re-derives the exact captured bytes the
SOURCES.lock digested (by building entries through history_sources.build_lock
itself, so the projections match by construction) and collapses reader
omission spans to the contracts/recording.schema.json definition set.
Defeating cases prove the named per-source refusals: a changed source, an
undeclared sessions directory, an unsupported kind. The synthetic email is
joined in memory only and never written into a committed file.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest

ASSET_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ASSET_ROOT / "src"))
sys.path.insert(0, str(ASSET_ROOT / "scripts"))

import history_reader
import history_sources
import ingest_history
import ingest_history_adapter as adapter
import ingest_manifests
from soveraeign_asset_service import AssetService

SYNTHETIC_EMAIL = "owner" + "@example" + ".com"
CAPTURED_AT = "2026-08-23T00:00:00+00:00"


def build_entries(commits=(), pulls=(), issues=(), sessions=()) -> list[dict]:
    lock = history_sources.build_lock(list(commits), list(pulls), list(issues),
                                     list(sessions), CAPTURED_AT, "test-capture")
    return lock["sources"]


class AdapterResolutionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write_session(self, session_id: str, raw: bytes) -> list[dict]:
        (self.root / f"{session_id}.jsonl").write_bytes(raw)
        return build_entries(sessions=[(session_id, len(raw), adapter._digest(raw))])

    def test_git_and_github_bytes_rederive_from_the_lock_itself(self):
        entries = build_entries(
            commits=[("a" * 40, "feat: land the recording slice")],
            pulls=[{"number": 7, "title": "Bind the corpus", "state": "MERGED"}],
            issues=[{"number": 9, "title": "Adopt the manifest schema", "state": "OPEN"}])
        reader = adapter.LockReader(history_reader.ReaderConfig())
        for entry in entries:
            result = reader.read_source(entry)
            self.assertIsNone(ingest_manifests.validate_recording(
                result["recording"], entry, result["payload"]))
            self.assertEqual(result["recording"]["fidelity"], "EXACT")
            self.assertEqual(result["recording"]["omissions"], [])

    def test_lossy_omissions_collapse_to_the_schema_definition_set(self):
        raw = ("Synthetic transcript line mentioning " + SYNTHETIC_EMAIL + "\n").encode("utf-8")
        entries = self.write_session("synthetic-0001", raw)
        config = history_reader.ReaderConfig(pii_emails=(SYNTHETIC_EMAIL,))
        reader = adapter.LockReader(config, self.root)
        result = reader.read_source(entries[0])
        self.assertNotIn(SYNTHETIC_EMAIL.encode("utf-8"), result["payload"])
        self.assertEqual(result["recording"]["fidelity"], "LOSSY")
        self.assertEqual(result["recording"]["omissions"],
                         [{"definition_id": "pii-v1",
                           "definition_digest": history_reader.definition_digest("pii-v1")}])
        self.assertIsNone(ingest_manifests.validate_recording(
            result["recording"], entries[0], result["payload"]))

    def test_changed_source_is_refused_and_named_in_the_driver_log(self):
        raw = b"captured transcript bytes\n"
        entries = self.write_session("synthetic-0002", raw)
        (self.root / "synthetic-0002.jsonl").write_bytes(b"mutated after capture\n")
        reader = adapter.LockReader(history_reader.ReaderConfig(), self.root)
        with self.assertRaises(adapter.SourceRefused) as context:
            reader.read_source(entries[0])
        self.assertEqual(context.exception.reason, "SOURCE_CHANGED")
        service = AssetService(self.root / "state")
        try:
            log = ingest_history.run_ingest(service=service, reader=reader, entries=entries,
                                            manifest_dir=self.root / "recordings",
                                            actor="asset-history-driver")
        finally:
            service.close()
        self.assertEqual(log["failed"],
                         [{"source_id": entries[0]["source_id"], "reason": "SOURCE_CHANGED"}])
        self.assertTrue(log["reconciled"])

    def test_undeclared_sessions_dir_and_unknown_kind_are_refused(self):
        raw = b"captured transcript bytes\n"
        entries = self.write_session("synthetic-0003", raw)
        reader = adapter.LockReader(history_reader.ReaderConfig(), None)
        with self.assertRaises(adapter.SourceRefused) as context:
            reader.read_source(entries[0])
        self.assertEqual(context.exception.reason, "SESSIONS_DIR_UNDECLARED")
        unknown = dict(entries[0], kind="carrier-pigeon",
                       source_id="carrier-pigeon:synthetic-0003")
        with self.assertRaises(adapter.SourceRefused) as context:
            reader.read_source(unknown)
        self.assertEqual(context.exception.reason, "UNSUPPORTED_SOURCE_KIND")

    def test_driver_ingests_a_real_lock_projection_end_to_end(self):
        entries = build_entries(commits=[("b" * 40, "docs: adopt the manifest schema")])
        reader = adapter.LockReader(history_reader.ReaderConfig())
        service = AssetService(self.root / "state")
        try:
            log = ingest_history.run_ingest(service=service, reader=reader, entries=entries,
                                            manifest_dir=self.root / "recordings",
                                            actor="asset-history-driver")
        finally:
            service.close()
        self.assertEqual(log["ingested"], 1)
        self.assertTrue(log["reconciled"])
        self.assertEqual(log["derived_from_edges"], 1)
        self.assertEqual(len(list((self.root / "recordings").glob("rec-*.json"))), 1)

    def test_build_reader_takes_identity_from_the_environment_only(self):
        environ = {history_reader.SESSIONS_DIR_ENV: str(self.root),
                   history_reader.OWNER_EMAIL_ENV: SYNTHETIC_EMAIL,
                   "SOV_HOST_USERNAME": "example"}
        reader = adapter.build_reader(environ)
        self.assertEqual(reader.sessions_dir, self.root)
        self.assertEqual(reader.config.pii_emails, (SYNTHETIC_EMAIL,))
        self.assertEqual(reader.config.pii_usernames, ("example",))


if __name__ == "__main__":
    unittest.main()
