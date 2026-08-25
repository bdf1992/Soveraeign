from __future__ import annotations

import json
import sys
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from soveraeign_asset_service import (
    AssetService,
    AuthorityRefused,
    ConfigurationChanged,
    ReaderDeclaration,
    ReaderChanged,
    ReaderUndeclared,
    RecordingChanged,
    SourceChanged,
    StaleLease,
    digest_configuration,
)


class WalkingSkeleton(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.service = AssetService(self.root / "state")
        self.service.grant("Bdo", "Bdo", "operate:derive")
        self.service.grant("Bdo", "Bdo", "ratify:judgement")
        self.service.grant("Bdo", "Bdo", "retract:record")
        self.reader = ReaderDeclaration.from_materials(
            reader_id="asset.metadata-card",
            reader_version="1.0.0",
            reader_artifact=b'{"entrypoint":"builtin:metadata-card"}',
            configuration={"format": "json", "schema": "card-v1"},
            fidelity="LOSSY",
            omissions=("binary-payload",),
        )

    def tearDown(self):
        self.service.close()
        self.tmp.cleanup()

    def source(self, name: str, content: bytes) -> Path:
        path = self.root / name
        path.write_bytes(content)
        return path

    def test_agentic_asset_walk(self):
        original = self.source("campaign-hero.txt", b"ORIGINAL CAMPAIGN ASSET\n")
        campaign = self.source("campaign.txt", b"Autumn launch\n")
        before = original.read_bytes()
        asset = self.service.ingest(original, "Campaign Hero", "Bdo")
        campaign_asset = self.service.ingest(campaign, "Autumn Campaign", "Bdo")

        run = self.service.request_derivative(
            asset["asset_id"], asset["version_id"], "Bdo", reader=self.reader
        )
        fence = self.service.claim(run, "local-worker")
        card = json.dumps({"title": "Campaign Hero", "source": asset["digest"]}).encode()
        output_version = self.service.report_derivative(run, "local-worker", fence, card)
        recording = self.service.reconstruct_recording(output_version)
        self.assertEqual(recording["source_id"], asset["version_id"])
        self.assertEqual(recording["operation"], "metadata-card")
        self.assertEqual(recording["reader_id"], self.reader.reader_id)
        self.assertEqual(recording["reader_version"], self.reader.reader_version)
        self.assertTrue(recording["reader_address"].startswith("cas:sha256:"))
        self.assertTrue(recording["reader_artifact_address"].startswith("cas:sha256:"))
        self.assertTrue(recording["configuration_address"].startswith("cas:sha256:"))
        self.assertEqual(recording["reader_address"], f"cas:{recording['reader_digest']}")
        self.assertEqual(
            recording["reader_artifact_address"],
            f"cas:{recording['reader_artifact_digest']}",
        )
        self.assertEqual(
            recording["configuration_address"],
            f"cas:{recording['configuration_digest']}",
        )
        self.assertEqual(recording["configuration_digest"], self.reader.configuration_digest)
        self.assertEqual(recording["output_role"], "RECORDING")
        self.assertEqual(recording["fidelity"], "LOSSY")
        self.assertEqual(recording["omissions"], ["binary-payload"])
        self.assertEqual(recording["standing"], "RECORDED")
        contract = json.loads(
            (Path(__file__).parents[1] / "contracts" / "derivative-recording.schema.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(set(recording), set(contract["properties"]))
        self.assertEqual(
            self.service.db.execute(
                "SELECT status FROM runs WHERE id=?", (run,)
            ).fetchone()[0],
            "REPORTED",
        )
        self.service.observe(run, "independent-observer")
        self.assertEqual(
            self.service.db.execute(
                "SELECT status FROM runs WHERE id=?", (run,)
            ).fetchone()[0],
            "COMMITTED",
        )
        self.assertEqual(original.read_bytes(), before)

        proposal = self.service.propose(asset["asset_id"], "claude-adapter", {
            "description": "Primary visual for the autumn launch",
            "tags": ["autumn", "hero"],
            "relationship": {"predicate": "USED_BY", "dst_asset": campaign_asset["asset_id"]},
        })
        with self.assertRaises(AuthorityRefused):
            self.service.ratify(proposal, "claude-adapter")
        self.service.ratify(proposal, "Bdo")
        counts = self.service.rebuild_projections()
        self.assertEqual(counts, {"search": 2, "edges": 1})
        self.assertIn(asset["asset_id"], self.service.search("autumn"))
        edges = self.service.neighbors(asset["asset_id"])
        self.assertEqual(edges[0]["predicate"], "USED_BY")
        self.assertTrue(edges[0]["source_receipt"].startswith("rcpt_"))

        relation_id = self.service.db.execute("SELECT id FROM relationships").fetchone()[0]
        self.service.retract("relationship", relation_id, "Bdo", "wrong campaign use")
        self.service.rebuild_projections()
        self.assertEqual(self.service.neighbors(asset["asset_id"]), [])
        self.assertIsNotNone(
            self.service.db.execute(
                "SELECT id FROM relationships WHERE id=? AND standing='COUNTERED'",
                (relation_id,),
            ).fetchone()
        )
        self.assertIsNotNone(
            self.service.db.execute(
                "SELECT id FROM versions WHERE id=?", (output_version,)
            ).fetchone()
        )

        receipt = self.service.federation_cross("Bdo", asset["asset_id"])
        outcome = self.service.db.execute(
            "SELECT outcome,payload_json FROM receipts WHERE id=?", (receipt,)
        ).fetchone()
        self.assertEqual(outcome["outcome"], "REFUSED")
        self.assertEqual(json.loads(outcome["payload_json"])["reason"], "UNCONFIGURED")

    def test_stale_worker_cannot_settle(self):
        path = self.source("asset.txt", b"asset")
        asset = self.service.ingest(path, "Asset", "Bdo")
        run = self.service.request_derivative(
            asset["asset_id"], asset["version_id"], "Bdo", reader=self.reader
        )
        stale = self.service.claim(run, "worker-a", ttl_seconds=0.001)
        time.sleep(0.01)
        current = self.service.claim(run, "worker-b")
        with self.assertRaises(StaleLease):
            self.service.report_derivative(run, "worker-a", stale, b"stale")
        self.service.report_derivative(run, "worker-b", current, b"current")

    def test_lossy_reader_without_recoverable_omissions_is_refused(self):
        path = self.source("asset.txt", b"asset")
        asset = self.service.ingest(path, "Asset", "Bdo")
        configuration_digest = digest_configuration({"mode": "sketch"})
        invalid_readers = (
            ReaderDeclaration.from_materials(
                "asset.pencil", "1", b"pencil-v1", {"mode": "sketch"}, "LOSSY"
            ),
            ReaderDeclaration.from_materials(
                "asset.pencil",
                "1",
                b"pencil-v1",
                {"mode": "sketch"},
                "EXACT",
                ("color",),
            ),
            ReaderDeclaration.from_materials(
                "asset.pencil",
                "1",
                b"pencil-v1",
                {"mode": "sketch"},
                "LOSSY",
                ["color"],
            ),
            ReaderDeclaration.from_materials(
                reader_id="asset.pencil",
                reader_version="1",
                reader_artifact=b"",
                configuration={"mode": "sketch"},
                fidelity="LOSSY",
                omissions=("color",),
            ),
            ReaderDeclaration(
                "asset.pencil", "1", configuration_digest, "LOSSY", ("color",)
            ),
        )
        for reader in invalid_readers:
            with self.subTest(reader=reader), self.assertRaises(ReaderUndeclared):
                self.service.request_derivative(
                    asset["asset_id"], asset["version_id"], "Bdo", reader=reader
                )
        refusal = self.service.db.execute(
            "SELECT payload_json FROM receipts WHERE event='asset.request-derivative' "
            "AND outcome='REFUSED' ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        self.assertEqual(json.loads(refusal["payload_json"])["reason"], "READER_UNDECLARED")

    def test_undeclared_legacy_derivative_is_not_a_recording(self):
        """Compatibility output remains a version and earns no recording claim."""
        path = self.source("asset.txt", b"asset")
        asset = self.service.ingest(path, "Asset", "Bdo")
        run = self.service.request_derivative(
            asset["asset_id"], asset["version_id"], "Bdo"
        )
        fence = self.service.claim(run, "local-worker")
        output = self.service.report_derivative(run, "local-worker", fence, b"output")
        self.assertIsNone(
            self.service.db.execute(
                "SELECT id FROM recordings WHERE output_version_id=?", (output,)
            ).fetchone()
        )
        with self.assertRaises(KeyError):
            self.service.reconstruct_recording(output)

    def test_source_change_after_request_refuses_derivative_report(self):
        path = self.source("asset.txt", b"asset")
        asset = self.service.ingest(path, "Asset", "Bdo")
        run = self.service.request_derivative(
            asset["asset_id"], asset["version_id"], "Bdo", reader=self.reader
        )
        fence = self.service.claim(run, "local-worker")
        blob_path = self.service.db.execute(
            "SELECT blob_path FROM versions WHERE id=?", (asset["version_id"],)
        ).fetchone()[0]
        Path(blob_path).write_bytes(b"changed")
        blob_root = self.root / "state" / "blobs" / "sha256"
        blobs_before = {path for path in blob_root.rglob("*") if path.is_file()}
        with self.assertRaises(SourceChanged):
            self.service.report_derivative(
                run, "local-worker", fence, b"unique refused output"
            )
        self.assertEqual(
            {path for path in blob_root.rglob("*") if path.is_file()}, blobs_before
        )
        self.assertEqual(
            self.service.db.execute("SELECT status FROM runs WHERE id=?", (run,)).fetchone()[0],
            "REFUSED",
        )
        self.assertEqual(
            self.service.db.execute("SELECT COUNT(*) FROM recordings").fetchone()[0],
            0,
        )

    def test_output_corruption_defeats_recording_reconstruction(self):
        path = self.source("asset.txt", b"asset")
        asset = self.service.ingest(path, "Asset", "Bdo")
        run = self.service.request_derivative(
            asset["asset_id"], asset["version_id"], "Bdo", reader=self.reader
        )
        fence = self.service.claim(run, "local-worker")
        output_version = self.service.report_derivative(
            run, "local-worker", fence, b"output"
        )
        blob_path = self.service.db.execute(
            "SELECT blob_path FROM versions WHERE id=?", (output_version,)
        ).fetchone()[0]
        Path(blob_path).write_bytes(b"corrupt")
        with self.assertRaises(RecordingChanged):
            self.service.reconstruct_recording(output_version)

    def test_source_corruption_after_report_defeats_observation(self):
        path = self.source("asset.txt", b"asset")
        asset = self.service.ingest(path, "Asset", "Bdo")
        run = self.service.request_derivative(
            asset["asset_id"], asset["version_id"], "Bdo", reader=self.reader
        )
        fence = self.service.claim(run, "local-worker")
        self.service.report_derivative(run, "local-worker", fence, b"output")
        blob_path = self.service.db.execute(
            "SELECT blob_path FROM versions WHERE id=?", (asset["version_id"],)
        ).fetchone()[0]
        Path(blob_path).write_bytes(b"corrupt")

        observation_id = self.service.observe(run, "independent-observer")

        run_status = self.service.db.execute(
            "SELECT status FROM runs WHERE id=?", (run,)
        ).fetchone()[0]
        evidence = self.service.db.execute(
            "SELECT evidence_json FROM observations WHERE id=?", (observation_id,)
        ).fetchone()[0]
        self.assertEqual(run_status, "FAILED")
        self.assertEqual(json.loads(evidence)["reason"], "SOURCE_CHANGED")

    def test_tampered_payload_address_defeats_recording_reconstruction(self):
        path = self.source("asset.txt", b"asset")
        asset = self.service.ingest(path, "Asset", "Bdo")
        run = self.service.request_derivative(
            asset["asset_id"], asset["version_id"], "Bdo", reader=self.reader
        )
        fence = self.service.claim(run, "local-worker")
        output_version = self.service.report_derivative(
            run, "local-worker", fence, b"output"
        )
        self.service.db.execute(
            "UPDATE recordings SET payload_address=? WHERE output_version_id=?",
            (f"cas:sha256:{'0' * 64}", output_version),
        )
        self.service.db.commit()

        with self.assertRaises(RecordingChanged):
            self.service.reconstruct_recording(output_version)

    def test_reader_artifact_corruption_defeats_reconstruction(self):
        path = self.source("asset.txt", b"asset")
        asset = self.service.ingest(path, "Asset", "Bdo")
        run = self.service.request_derivative(
            asset["asset_id"], asset["version_id"], "Bdo", reader=self.reader
        )
        fence = self.service.claim(run, "local-worker")
        output_version = self.service.report_derivative(
            run, "local-worker", fence, b"output"
        )
        recording = self.service.reconstruct_recording(output_version)
        artifact_digest = recording["reader_artifact_digest"].removeprefix("sha256:")
        artifact_path = (
            self.root / "state" / "blobs" / "sha256" / artifact_digest[:2] / artifact_digest
        )
        artifact_path.write_bytes(b"corrupt")

        with self.assertRaises(ReaderChanged):
            self.service.reconstruct_recording(output_version)

    def test_reader_identity_substitution_defeats_reconstruction(self):
        path = self.source("asset.txt", b"asset")
        asset = self.service.ingest(path, "Asset", "Bdo")
        run = self.service.request_derivative(
            asset["asset_id"], asset["version_id"], "Bdo", reader=self.reader
        )
        fence = self.service.claim(run, "local-worker")
        output_version = self.service.report_derivative(
            run, "local-worker", fence, b"output"
        )
        self.service.db.execute(
            "UPDATE derivative_plans SET reader_version='substituted' WHERE run_id=?",
            (run,),
        )
        self.service.db.execute(
            "UPDATE recordings SET reader_version='substituted' WHERE run_id=?",
            (run,),
        )
        self.service.db.commit()

        with self.assertRaises(ReaderChanged):
            self.service.reconstruct_recording(output_version)

    def test_configuration_corruption_defeats_reconstruction(self):
        path = self.source("asset.txt", b"asset")
        asset = self.service.ingest(path, "Asset", "Bdo")
        run = self.service.request_derivative(
            asset["asset_id"], asset["version_id"], "Bdo", reader=self.reader
        )
        fence = self.service.claim(run, "local-worker")
        output_version = self.service.report_derivative(
            run, "local-worker", fence, b"output"
        )
        recording = self.service.reconstruct_recording(output_version)
        configuration_digest = recording["configuration_digest"].removeprefix("sha256:")
        configuration_path = (
            self.root
            / "state"
            / "blobs"
            / "sha256"
            / configuration_digest[:2]
            / configuration_digest
        )
        configuration_path.write_bytes(b"corrupt")

        with self.assertRaises(ConfigurationChanged):
            self.service.reconstruct_recording(output_version)

    def test_same_bytes_do_not_collapse_asset_identity(self):
        """Two sources holding identical bytes are two identities sharing one blob.

        The fixture uses two paths deliberately. Capturing one path twice is the
        same source again, which is a version of one asset rather than a second
        asset (`test_recapturing_one_source_versions_it`), so it cannot test this
        claim.
        """
        first = self.service.ingest(self.source("same.bin", b"same"), "First use", "Bdo")
        second = self.service.ingest(self.source("copy.bin", b"same"), "Second use", "Bdo")
        self.assertEqual(first["digest"], second["digest"])
        self.assertNotEqual(first["asset_id"], second["asset_id"])
        self.assertEqual(len(list((self.root / "state" / "blobs" / "sha256").glob("*/*"))), 1)
        self.assertEqual([entry["holders"] for entry in self.service.duplicates()], [2])

    def test_recapturing_one_source_versions_it(self):
        """`CLASSIFICATION.md`: an asset is an identity with a version history."""
        path = self.source("brief.md", b"first draft\n")
        first = self.service.ingest(path, "Brief", "Bdo", locator="repo:brief.md")
        path.write_bytes(b"second draft\n")
        second = self.service.ingest(path, "Brief", "Bdo", locator="repo:brief.md")
        self.assertEqual(first["asset_id"], second["asset_id"])
        self.assertEqual([first["role"], second["role"]], ["ORIGINAL", "REVISION"])
        self.assertEqual(len(self.service.history(first["asset_id"])), 2)

    def test_recapturing_unchanged_bytes_adds_no_version(self):
        """The defeating case: a re-read is not a new state, so it earns no version."""
        path = self.source("brief.md", b"first draft\n")
        first = self.service.ingest(path, "Brief", "Bdo", locator="repo:brief.md")
        again = self.service.ingest(path, "Brief", "Bdo", locator="repo:brief.md")
        self.assertTrue(again["unchanged"])
        self.assertEqual(again["version_id"], first["version_id"])
        self.assertEqual(len(self.service.history(first["asset_id"])), 1)
        outcomes = [r["outcome"] for r in self.service.receipts() if r["event"] == "asset.ingest-asset"]
        self.assertEqual(outcomes, ["COMMITTED", "ATTEMPTED"])


if __name__ == "__main__":
    unittest.main()
