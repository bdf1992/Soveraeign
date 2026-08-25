"""Route-and-receipt completion for the Asset Service read-version operation."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from soveraeign_asset_service import AssetService  # noqa: E402
from soveraeign_asset_service.custody import (  # noqa: E402
    SourceChanged,
    UnknownRecord,
    _path_from_locator,
    reread_source,
)
from soveraeign_asset_service.routes import AssetRoutes  # noqa: E402


class AssetRouteReceipts(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.service = AssetService(self.root / "state")
        self.routes = AssetRoutes(self.service)

    def tearDown(self) -> None:
        self.service.close()
        self.tmp.cleanup()

    def source(self, name: str, data: bytes) -> Path:
        path = self.root / name
        path.write_bytes(data)
        return path

    def ingest(self, data: bytes = b"route-owned bytes") -> dict[str, str]:
        return self.service.ingest(self.source("payload.bin", data), "Route payload", "ingester")

    def payload(self, receipt: dict) -> dict:
        return json.loads(receipt["payload_json"])

    def test_route_census_and_argument_contract_are_exact(self) -> None:
        self.assertEqual(AssetRoutes.operation_ids(), ("ingest-asset", "read-version"))
        self.assertEqual(AssetRoutes.argument_contract("ingest-asset"), {
            "required": ("path", "label"), "optional": ("locator",),
        })
        self.assertEqual(AssetRoutes.argument_contract("read-version"), {
            "required": ("version_id",), "optional": (),
        })
        with self.assertRaises(KeyError):
            self.routes.call("not-bound", {}, "operator")

    def test_route_rejects_argument_shape_before_service_execution(self) -> None:
        with self.assertRaises(ValueError):
            self.routes.call("ingest-asset", {"path": "unused"}, "operator")
        with self.assertRaises(ValueError):
            self.routes.call("ingest-asset", {"label": "Missing path"}, "operator")
        with self.assertRaises(ValueError):
            self.routes.call("ingest-asset", {
                "path": "unused", "label": "Unexpected", "unexpected": "value",
            }, "operator")
        with self.assertRaises(ValueError):
            self.routes.call("read-version", {}, "operator")
        with self.assertRaises(ValueError):
            self.routes.call("read-version", {
                "version_id": "unused", "unexpected": "value",
            }, "operator")
        self.assertEqual(self.service.receipts(), [])

    def test_ingest_route_returns_the_durable_asset_receipt(self) -> None:
        source = self.source("routed-ingest.bin", b"routed ingest")
        returned = self.routes.call("ingest-asset", {
            "path": str(source), "label": "Routed ingest",
        }, "operator")

        self.assertEqual(returned, self.service.receipts()[-1])
        self.assertEqual(returned["outcome"], "COMMITTED")
        self.assertEqual(returned["event"], "asset.ingest-asset")
        self.assertEqual(returned["actor"], "operator")

    def test_read_success_returns_the_durable_asset_receipt(self) -> None:
        data = b"exact bytes from custody\x00"
        ingested = self.ingest(data)

        returned = self.routes.call(
            "read-version", {"version_id": ingested["version_id"]}, "operator")
        durable = self.service.receipts()[-1]
        detail = self.payload(returned)

        self.assertEqual(returned, durable)
        self.assertEqual(returned["outcome"], "COMMITTED")
        self.assertEqual(returned["event"], "asset.read-version")
        self.assertEqual(returned["actor"], "operator")
        self.assertEqual(detail["version_id"], ingested["version_id"])
        self.assertEqual(detail["asset_id"], ingested["asset_id"])
        self.assertEqual(detail["digest"], sha256(data).hexdigest())
        self.assertEqual(detail["payload_address"], f"urn:sha256:{ingested['digest']}")
        self.assertEqual(detail["metadata"], {
            "created_at": self.service.db.execute(
                "SELECT created_at FROM versions WHERE id=?", (ingested["version_id"],)
            ).fetchone()["created_at"],
            "derivation": None,
            "mime": "application/octet-stream",
            "role": "ORIGINAL",
            "size": len(data),
            "source_id": ingested["source_id"],
        })
        self.assertNotIn("blob_path", returned["payload_json"])

    def test_unknown_version_returns_the_durable_asset_refusal(self) -> None:
        returned = self.routes.call(
            "read-version", {"version_id": "version_unknown"}, "operator")

        self.assertEqual(returned, self.service.receipts()[-1])
        self.assertEqual(returned["outcome"], "REFUSED")
        self.assertEqual(self.payload(returned), {
            "reason": "VERSION_UNKNOWN", "version_id": "version_unknown",
        })

    def test_missing_payload_returns_the_durable_asset_refusal(self) -> None:
        ingested = self.ingest()
        row = self.service.db.execute(
            "SELECT blob_path FROM versions WHERE id=?", (ingested["version_id"],)
        ).fetchone()
        Path(row["blob_path"]).unlink()

        returned = self.routes.call(
            "read-version", {"version_id": ingested["version_id"]}, "operator")

        self.assertEqual(returned, self.service.receipts()[-1])
        self.assertEqual(returned["outcome"], "REFUSED")
        self.assertEqual(self.payload(returned)["reason"], "PAYLOAD_ABSENT")

    def test_corrupt_payload_returns_the_durable_asset_refusal(self) -> None:
        ingested = self.ingest()
        row = self.service.db.execute(
            "SELECT blob_path FROM versions WHERE id=?", (ingested["version_id"],)
        ).fetchone()
        Path(row["blob_path"]).write_bytes(b"corrupt")

        returned = self.routes.call(
            "read-version", {"version_id": ingested["version_id"]}, "operator")
        detail = self.payload(returned)

        self.assertEqual(returned, self.service.receipts()[-1])
        self.assertEqual(returned["outcome"], "REFUSED")
        self.assertEqual(detail["reason"], "DIGEST_MISMATCH")
        self.assertEqual(detail["recorded"], ingested["digest"])
        self.assertEqual(detail["observed"], sha256(b"corrupt").hexdigest())

    def test_file_locator_resolution_refuses_non_file_schemes(self) -> None:
        path = self.source("locator space.bin", b"locator")
        self.assertEqual(_path_from_locator(path.resolve().as_uri()), path.resolve())
        self.assertIsNone(_path_from_locator("https://example.invalid/payload"))

    def test_reread_source_success_returns_exact_metadata_and_receipt(self) -> None:
        data = b"unchanged external source"
        ingested = self.ingest(data)

        returned = reread_source(self.service, ingested["source_id"], "reader")
        receipt = self.service.receipts()[-1]

        self.assertEqual(returned, {
            "source_id": ingested["source_id"],
            "digest": ingested["digest"],
            "locator": self.source("payload.bin", data).resolve().as_uri(),
            "size": len(data),
        })
        self.assertEqual(receipt["outcome"], "COMMITTED")
        self.assertEqual(receipt["event"], "source.reread")
        self.assertEqual(receipt["actor"], "reader")

    def test_reread_unknown_source_is_not_counterfeited(self) -> None:
        before = list(self.service.receipts())
        with self.assertRaises(UnknownRecord):
            reread_source(self.service, "source_unknown", "reader")
        self.assertEqual(self.service.receipts(), before)

    def test_reread_non_file_locator_is_receipted_as_unreachable(self) -> None:
        ingested = self.service.ingest(
            self.source("remote.bin", b"captured remote bytes"), "Remote", "ingester",
            locator="https://example.invalid/remote.bin",
        )
        with self.assertRaises(SourceChanged):
            reread_source(self.service, ingested["source_id"], "reader")
        detail = self.payload(self.service.receipts()[-1])
        self.assertEqual(detail, {
            "locator": "https://example.invalid/remote.bin", "reason": "SOURCE_UNREACHABLE",
        })

    def test_reread_missing_file_is_receipted_as_unreachable(self) -> None:
        ingested = self.ingest()
        self.source("payload.bin", b"route-owned bytes").unlink()
        with self.assertRaises(SourceChanged):
            reread_source(self.service, ingested["source_id"], "reader")
        self.assertEqual(self.payload(self.service.receipts()[-1])["reason"],
                         "SOURCE_UNREACHABLE")

    def test_reread_changed_source_is_receipted_with_both_digests(self) -> None:
        ingested = self.ingest()
        changed = b"source changed after capture"
        self.source("payload.bin", changed)
        with self.assertRaises(SourceChanged):
            reread_source(self.service, ingested["source_id"], "reader")
        detail = self.payload(self.service.receipts()[-1])
        self.assertEqual(detail["reason"], "SOURCE_CHANGED")
        self.assertEqual(detail["captured"], ingested["digest"])
        self.assertEqual(detail["observed"], sha256(changed).hexdigest())


if __name__ == "__main__":
    unittest.main()
