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

#: The custody contract is a POSIX node volume: it verifies uid/gid ownership and sets
#: file modes through ``os.fchmod``. A host without POSIX identity cannot hold that
#: contract, so these cases declare the requirement and skip visibly rather than erroring
#: with an AttributeError that reads like a defect in the code under test.
#:
#: This stays a bool rather than a ready-made decorator because two cases below branch on
#: it (``if POSIX_CUSTODY:`` asserts POSIX enforcement or the UNAVAILABLE receipt), and a
#: ``skipUnless`` object is always truthy - it would take the POSIX branch on Windows.
POSIX_CUSTODY = activation.custody_posix.available
NO_POSIX = ("POSIX ownership and mode bits do not exist on this platform. The check is "
            "skipped rather than passed, and every receipt written here records "
            "identity_enforcement UNAVAILABLE_ON_THIS_PLATFORM so it cannot be read as "
            "proof that custody was verified.")


@unittest.skipUnless(POSIX_CUSTODY, NO_POSIX)
class CustodyActivationTests(unittest.TestCase):
    def manifest(self) -> dict:
        return json.loads((ROOT / "infrastructure" / "phase-i.local.json").read_text(
            encoding="utf-8"))

    def activate(self, root: Path, policy: str = "VERIFY_ONLY") -> dict:
        uid, gid = activation.custody_posix.effective()
        return activation.activate(root, self.manifest(), policy, uid, gid)

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

    @unittest.skipUnless(POSIX_CUSTODY, NO_POSIX)
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

    def test_a_receipt_never_claims_custody_it_could_not_verify(self):
        """The platform's answer reaches the receipt instead of being assumed.

        On POSIX the receipt claims enforcement and carries a real uid. Where the
        platform has no such identity it says so, and records -1, so no reader can
        mistake an unenforced custody for a verified one.
        """
        with TemporaryDirectory() as temporary:
            node = Path(temporary) / "node"
            receipt = self.activate(node, "VERIFY_OR_INITIALIZE_EMPTY")
            claim = receipt["identity_enforcement"]
            if POSIX_CUSTODY:
                self.assertEqual(claim, "POSIX")
                self.assertNotEqual(receipt["effective_uid"], -1)
            else:
                self.assertEqual(claim, "UNAVAILABLE_ON_THIS_PLATFORM")
                self.assertEqual(receipt["effective_uid"], -1)

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

    def test_stale_activation_receipt_refuses_restart(self):
        with TemporaryDirectory() as temporary:
            node = Path(temporary) / "node"
            first = self.activate(node, "VERIFY_OR_INITIALIZE_EMPTY")
            receipt_path = node / "receipts" / "custody-activations" / (
                first["activation_id"] + ".json")
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["manifest_digest"] = "0" * 64
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            with self.assertRaisesRegex(activation.CustodyActivationRefused,
                                        "CUSTODY_ACTIVATION_RECEIPT_STALE"):
                self.activate(node)


if __name__ == "__main__":
    unittest.main()
