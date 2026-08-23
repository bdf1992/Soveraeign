"""BUILT-evidence fixtures for the history ingestion driver (ASSET-HL-4).

Positive and defeating cases for services/asset/scripts/ingest_history.py,
authored before the driver per the AGENTS.md implementation order. The driver
wires the ASSET-HL-2 reader over the ASSET-HL-3 SOURCES.lock; neither has
landed yet, so a StubReader stands in through the driver's declared,
provisional reader protocol, and these cases establish BUILT evidence only.

The committed-manifest contract is contracts/recording.schema.json (landed):
the required key set is read from that schema rather than duplicated here.
Contaminants are committed only as split parts, following the binding note in
conformance/fixtures/lineage/reader-cases.json: this module joins them in
memory only and never writes a joined contaminant into a committed file.
"""

from __future__ import annotations

from contextlib import redirect_stdout
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import io
import json
import re
import subprocess
import sys
import unittest

ASSET_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ASSET_ROOT.parents[1]
sys.path.insert(0, str(ASSET_ROOT / "src"))
sys.path.insert(0, str(ASSET_ROOT / "scripts"))

import ingest_history
from soveraeign_asset_service import AssetService

RECORDING_SCHEMA = json.loads(
    (REPO_ROOT / "contracts" / "recording.schema.json").read_text(encoding="utf-8"))
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
# Joined in memory only; never written into a committed file.
WINDOWS_USER_PATH = "C:" + "\\Users" + "\\example" + "\\session-0002.jsonl"
SYNTHETIC_EMAIL = "owner" + "@example" + ".com"


def sha(data: bytes) -> str:
    return "sha256:" + sha256(data).hexdigest()


def lock_entry(source_id: str, payload: bytes) -> dict:
    """A SOURCES.lock entry per contracts/source.schema.json for a stub source."""
    return {
        "source_id": source_id,
        "source_address": "claude-session:" + source_id.rsplit(":", 1)[-1],
        "payload_digest": sha(payload),
        "payload_size": len(payload),
        "captured_at": "2026-08-23T00:00:00+00:00",
        "captured_by": "test-capture",
    }


class StubReader:
    """ASSET-HL-2 stand-in honouring the driver's provisional reader protocol.

    EXACT readings: the recording payload equals the source bytes. overrides
    patches recording fields per source_id; a None value removes the field.
    """

    def __init__(self, payloads: dict[str, bytes], overrides: dict | None = None):
        self.payloads = payloads
        self.overrides = overrides or {}

    def read_source(self, source: dict) -> dict:
        payload = self.payloads[source["source_id"]]
        recording = {
            "source_id": source["source_id"],
            "source_digest": sha(payload),
            "reader_id": "stub-reader",
            "reader_version": "stub-1",
            "configuration_digest": sha(b"stub-configuration"),
            "payload_digest": sha(payload),
            "fidelity": "EXACT",
            "omissions": [],
        }
        for field, value in self.overrides.get(source["source_id"], {}).items():
            if value is None:
                recording.pop(field, None)
            else:
                recording[field] = value
        return {"payload": payload, "recording": recording}


class IngestHistoryDriverTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        root = Path(self.tmp.name)
        self.state = root / "state"
        self.manifests = root / "recordings"

    def tearDown(self):
        self.tmp.cleanup()

    def run_driver(self, entries: list, reader: StubReader) -> dict:
        service = AssetService(self.state)
        try:
            return ingest_history.run_ingest(
                service=service, reader=reader, entries=entries,
                manifest_dir=self.manifests, actor="asset-history-driver")
        finally:
            service.close()

    def open_service(self) -> AssetService:
        return AssetService(self.state)

    def test_one_asset_per_source_manifest_edge_and_search_hit(self):
        payloads = {
            "session:0001": b"The projection rebuilt from canonical receipts.\n",
            "session:0002": b"A fenced lease carried the walking skeleton run.\n",
        }
        entries = [lock_entry(sid, data) for sid, data in payloads.items()]
        log = self.run_driver(entries, StubReader(payloads))
        self.assertEqual(log["enumerated"], 2)
        self.assertEqual(log["ingested"], 2)
        self.assertEqual(log["failed"], [])
        self.assertTrue(log["reconciled"])
        self.assertTrue(log["projection_deterministic"])
        self.assertEqual(log["derived_from_edges"], 2)
        manifests = sorted(self.manifests.glob("rec-*.json"))
        self.assertEqual(len(manifests), 2)
        for path in manifests:
            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.endswith("\n"))
            self.assertNotIn("\r", text)
            self.assertEqual(ingest_history.manifest_contaminants(text), [])
            manifest = json.loads(text)
            self.assertEqual(set(manifest), set(RECORDING_SCHEMA["required"]))
            for field in ("source_digest", "configuration_digest", "payload_digest"):
                self.assertRegex(manifest[field], DIGEST)
            self.assertEqual(manifest["standing"], "RECORDED")
            self.assertEqual(
                manifest["payload_address"],
                "cas:sha256/" + manifest["payload_digest"].split(":", 1)[1])
        service = self.open_service()
        try:
            hits = service.search("canonical receipts")
            self.assertEqual(len(hits), 1)
            edges = service.neighbors(hits[0])
            self.assertEqual(len(edges), 1)
            self.assertEqual(edges[0]["predicate"], "derived-from")
            self.assertEqual(edges[0]["dst_asset"], "session:0001")
            self.assertTrue(edges[0]["source_receipt"])
        finally:
            service.close()

    def test_unchanged_reread_adds_no_asset_and_no_manifest(self):
        payloads = {"session:0001": b"Stable recording bytes.\n"}
        entries = [lock_entry("session:0001", payloads["session:0001"])]
        first = self.run_driver(entries, StubReader(payloads))
        self.assertEqual(first["ingested"], 1)
        second = self.run_driver(entries, StubReader(payloads))
        self.assertEqual(second["ingested"], 0)
        self.assertEqual(second["unchanged"], 1)
        self.assertTrue(second["reconciled"])
        self.assertEqual(len(list(self.manifests.glob("rec-*.json"))), 1)
        service = self.open_service()
        try:
            self.assertEqual(len(service.search("[session:0001]")), 1)
        finally:
            service.close()

    def test_changed_reread_versions_the_same_asset(self):
        old = {"session:0001": b"First reading with marker-alpha.\n"}
        new = {"session:0001": b"Second reading with marker-omega.\n"}
        self.run_driver([lock_entry("session:0001", old["session:0001"])], StubReader(old))
        log = self.run_driver([lock_entry("session:0001", new["session:0001"])], StubReader(new))
        self.assertEqual(log["versioned"], 1)
        self.assertEqual(log["ingested"], 0)
        self.assertTrue(log["reconciled"])
        self.assertEqual(len(list(self.manifests.glob("rec-*.json"))), 2)
        service = self.open_service()
        try:
            self.assertEqual(len(service.search("[session:0001]")), 1)
            self.assertEqual(len(service.search("marker-omega")), 1)
            observed = [r for r in service.receipts()
                        if r["event"] == "operation.observe" and r["outcome"] == "COMMITTED"]
            self.assertEqual(len(observed), 1)
        finally:
            service.close()

    def test_incomplete_recording_is_refused_and_counted(self):
        payloads = {"session:0001": b"Recording without a configuration digest.\n"}
        reader = StubReader(payloads, overrides={"session:0001": {"configuration_digest": None}})
        log = self.run_driver([lock_entry("session:0001", payloads["session:0001"])], reader)
        self.assertEqual(log["ingested"], 0)
        self.assertEqual(log["failed"],
                         [{"source_id": "session:0001", "reason": "RECORDING_INCOMPLETE"}])
        self.assertTrue(log["reconciled"])
        self.assertEqual(list(self.manifests.glob("rec-*.json")), [])

    def test_contaminated_manifest_is_refused_before_any_write(self):
        payloads = {
            "session:0001": b"Clean payload one.\n",
            "session:0002": b"Clean payload two.\n",
        }
        overrides = {
            "session:0001": {"reader_id": "stub-reader " + WINDOWS_USER_PATH},
            "session:0002": {"reader_version": "stub-1 " + SYNTHETIC_EMAIL},
        }
        entries = [lock_entry(sid, data) for sid, data in payloads.items()]
        log = self.run_driver(entries, StubReader(payloads, overrides=overrides))
        self.assertEqual(log["ingested"], 0)
        self.assertEqual([f["reason"] for f in log["failed"]],
                         ["MANIFEST_CONTAMINATED", "MANIFEST_CONTAMINATED"])
        self.assertTrue(log["reconciled"])
        self.assertEqual(list(self.manifests.glob("rec-*.json")), [])
        service = self.open_service()
        try:
            self.assertEqual(service.search(""), [])
        finally:
            service.close()

    def test_state_destination_must_be_git_ignored(self):
        state = Path(self.tmp.name) / "not-ignored"
        refusal = ingest_history.ensure_state_admissible(state, check=lambda path: False)
        self.assertEqual(refusal["outcome"], "REFUSED")
        self.assertEqual(refusal["reason"], "STATE_NOT_IGNORED")
        self.assertFalse(state.exists())
        self.assertIsNone(ingest_history.ensure_state_admissible(state, check=lambda path: True))

    def test_default_state_path_is_ignored_in_this_repository(self):
        relative = ingest_history.DEFAULT_STATE.relative_to(REPO_ROOT)
        result = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "check-ignore", "-q", str(relative)],
            capture_output=True, check=False, timeout=10)
        self.assertEqual(result.returncode, 0)

    def test_missing_lock_or_reader_is_a_named_precondition_refusal(self):
        root = Path(self.tmp.name)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = ingest_history.main(["--lock", str(root / "absent.lock"),
                                       "--reader", str(root / "absent_reader.py"),
                                       "--state", str(self.state),
                                       "--manifests", str(self.manifests)])
        self.assertEqual(code, 2)
        refusal = json.loads(buffer.getvalue())
        self.assertEqual(refusal["reason"], "PRECONDITION_MISSING")
        self.assertIn("ASSET-HL-3", refusal["missing"])
        lock = root / "sources.lock.json"
        lock.write_text(json.dumps([lock_entry("session:0001", b"x\n")]) + "\n",
                        encoding="utf-8")
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = ingest_history.main(["--lock", str(lock),
                                       "--reader", str(root / "absent_reader.py"),
                                       "--state", str(self.state),
                                       "--manifests", str(self.manifests)])
        self.assertEqual(code, 2)
        self.assertIn("ASSET-HL-2", json.loads(buffer.getvalue())["missing"])


if __name__ == "__main__":
    unittest.main()
