from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "custody_activation", ROOT / "scripts" / "custody_activation.py"
)
assert SPEC and SPEC.loader
activation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(activation)


class CustodyActivationTests(unittest.TestCase):
    def manifest(self) -> dict:
        return json.loads((ROOT / "infrastructure" / "phase-i.local.json").read_text(
            encoding="utf-8"))

    def activate(self, root: Path, policy: str = "VERIFY_ONLY") -> dict:
        return activation.activate(root, self.manifest(), policy, os.geteuid(), os.getegid())

    def test_empty_custody_refuses_under_deployment_default(self):
        with TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(activation.CustodyActivationRefused,
                                        "EMPTY_CUSTODY_NOT_ACTIVATED"):
                self.activate(Path(temporary) / "node")

    def test_explicit_initialization_materializes_and_receipts(self):
        with TemporaryDirectory() as temporary:
            node = Path(temporary) / "node"
            receipt = self.activate(node, "VERIFY_OR_INITIALIZE_EMPTY")
            self.assertEqual(receipt["outcome"], "INITIALIZED_AND_VERIFIED")
            self.assertEqual(receipt["continuity"], "ESTABLISHED")
            stored = node / "receipts" / "custody-activations" / (
                receipt["activation_id"] + ".json")
            self.assertTrue(stored.is_file())
            self.assertEqual(json.loads(stored.read_text(encoding="utf-8"))["custody_id"],
                             receipt["custody_id"])

    def test_restart_preserves_identity_and_appends_receipt(self):
        with TemporaryDirectory() as temporary:
            node = Path(temporary) / "node"
            first = self.activate(node, "VERIFY_OR_INITIALIZE_EMPTY")
            second = self.activate(node)
            self.assertEqual(first["custody_id"], second["custody_id"])
            self.assertNotEqual(first["activation_id"], second["activation_id"])
            self.assertEqual(second["continuity"], "PRESERVED")
            receipts = list((node / "receipts" / "custody-activations").glob("*.json"))
            self.assertEqual(len(receipts), 2)

    def test_wrong_manifest_digest_and_stale_receipt_refuse(self):
        with TemporaryDirectory() as temporary:
            node = Path(temporary) / "node"
            self.activate(node, "VERIFY_OR_INITIALIZE_EMPTY")
            receipt_path = node / activation.infrastructure.RECEIPT_NAME
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["manifest_digest"] = "0" * 64
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            with self.assertRaisesRegex(activation.CustodyActivationRefused,
                                        "CUSTODY_PRECONDITION_DRIFT"):
                self.activate(node)

    def test_missing_declared_path_refuses(self):
        with TemporaryDirectory() as temporary:
            node = Path(temporary) / "node"
            self.activate(node, "VERIFY_OR_INITIALIZE_EMPTY")
            (node / "work").rmdir()
            with self.assertRaisesRegex(activation.CustodyActivationRefused,
                                        "CUSTODY_VERIFY_FAILED"):
                self.activate(node)

    def test_unwritable_declared_identity_refuses(self):
        with TemporaryDirectory() as temporary:
            node = Path(temporary) / "node"
            self.activate(node, "VERIFY_OR_INITIALIZE_EMPTY")
            expected_uid = os.geteuid() + 1
            with patch.object(activation.os, "geteuid", return_value=expected_uid):
                with self.assertRaisesRegex(activation.CustodyActivationRefused,
                                            "CUSTODY_OWNERSHIP_UNWRITABLE"):
                    activation.activate(node, self.manifest(), "VERIFY_ONLY",
                                        expected_uid, os.getegid())

    def test_stale_custody_identity_refuses(self):
        with TemporaryDirectory() as temporary:
            node = Path(temporary) / "node"
            self.activate(node, "VERIFY_OR_INITIALIZE_EMPTY")
            identity_path = node / activation.IDENTITY_NAME
            identity = json.loads(identity_path.read_text(encoding="utf-8"))
            identity["manifest_digest"] = "f" * 64
            identity_path.write_text(json.dumps(identity), encoding="utf-8")
            with self.assertRaisesRegex(activation.CustodyActivationRefused,
                                        "CUSTODY_IDENTITY_DRIFT"):
                self.activate(node)


if __name__ == "__main__":
    unittest.main()
