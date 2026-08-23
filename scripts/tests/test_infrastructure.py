from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import threading
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("infrastructure", ROOT / "scripts" / "infrastructure.py")
assert SPEC and SPEC.loader
infrastructure = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(infrastructure)

#: The custody contract is a POSIX node volume: it verifies uid/gid ownership and sets
#: file modes through ``os.fchmod``. A host without POSIX identity cannot hold that
#: contract, so these cases declare the requirement and skip visibly rather than erroring
#: with an AttributeError that reads like a defect in the code under test.
POSIX_CUSTODY = unittest.skipUnless(
    hasattr(os, "geteuid") and hasattr(os, "fchmod"),
    "custody materialization requires POSIX ownership and file modes",
)


class InfrastructureTests(unittest.TestCase):
    def manifest(self) -> dict:
        return json.loads((ROOT / "infrastructure" / "phase-i.local.json").read_text(encoding="utf-8"))

    def test_manifest_passes_phase_i_boundary(self):
        self.assertEqual(infrastructure.validate_manifest(self.manifest()), [])

    def test_plan_has_no_filesystem_effect(self):
        with TemporaryDirectory() as temporary:
            node = Path(temporary) / "node"
            proposal = infrastructure.plan(node, self.manifest())
            self.assertEqual(proposal["disposition"], "CREATE")
            self.assertFalse(node.exists())

    def test_unmanaged_nonempty_root_refuses(self):
        with TemporaryDirectory() as temporary:
            node = Path(temporary) / "node"
            node.mkdir()
            (node / "foreign.txt").write_text("not managed\n", encoding="utf-8")
            with self.assertRaisesRegex(infrastructure.InfrastructureRefused, "UNMANAGED"):
                infrastructure.apply(node, self.manifest())

    def test_escape_and_absolute_paths_are_defeating(self):
        """Judge custody paths as POSIX on every host, including root aliases."""
        for unsafe in ("../escape", "/tmp/escape", "C:\\escape", ".", "./", "work/.."):
            with self.subTest(unsafe=unsafe):
                manifest = self.manifest()
                manifest["custody"]["paths"]["work"] = unsafe
                self.assertIn("CUSTODY_PATH_UNSAFE", infrastructure.validate_manifest(manifest))

    def test_external_and_provider_dependencies_are_defeating(self):
        manifest = self.manifest()
        manifest["runtime"]["network_required"] = True
        manifest["policy"]["provider_required"] = True
        manifest["policy"]["external_effects"] = "ALLOW"
        defects = infrastructure.validate_manifest(manifest)
        self.assertIn("NETWORK_DEPENDENCY_NOT_ADMITTED", defects)
        self.assertIn("PROVIDER_DEPENDENCY_NOT_ADMITTED", defects)
        self.assertIn("EXTERNAL_EFFECTS_NOT_ADMITTED", defects)


@POSIX_CUSTODY
class CustodyMaterializationTests(unittest.TestCase):
    """Cases that actually create the custody volume, and so need POSIX modes."""

    def manifest(self) -> dict:
        return json.loads((ROOT / "infrastructure" / "phase-i.local.json").read_text(encoding="utf-8"))

    def test_apply_is_idempotent_and_verifiable(self):
        with TemporaryDirectory() as temporary:
            node = Path(temporary) / "node"
            first = infrastructure.apply(node, self.manifest())
            second = infrastructure.apply(node, self.manifest())
            self.assertEqual(first["outcome"], "COMMITTED")
            self.assertEqual(second["outcome"], "NOOP")
            self.assertEqual(infrastructure.verify(node, self.manifest()), [])

    def test_receipt_drift_is_observed(self):
        with TemporaryDirectory() as temporary:
            node = Path(temporary) / "node"
            infrastructure.apply(node, self.manifest())
            receipt = node / infrastructure.RECEIPT_NAME
            value = json.loads(receipt.read_text(encoding="utf-8"))
            value["manifest_digest"] = "0" * 64
            receipt.write_text(json.dumps(value), encoding="utf-8")
            self.assertIn("MANIFEST_DIGEST_MISMATCH", infrastructure.verify(node, self.manifest()))

    def test_receipt_path_binding_drift_is_observed(self):
        with TemporaryDirectory() as temporary:
            node = Path(temporary) / "node"
            infrastructure.apply(node, self.manifest())
            receipt = node / infrastructure.RECEIPT_NAME
            value = json.loads(receipt.read_text(encoding="utf-8"))
            value["paths"]["work"] = "/different/work"
            receipt.write_text(json.dumps(value), encoding="utf-8")
            self.assertIn("RECEIPT_PATH_BINDING_MISMATCH",
                          infrastructure.verify(node, self.manifest()))

    def test_symlinked_custody_path_is_observed(self):
        with TemporaryDirectory() as temporary:
            node = Path(temporary) / "node"
            infrastructure.apply(node, self.manifest())
            work = node / "work"
            work.rmdir()
            work.symlink_to(node / "record", target_is_directory=True)
            self.assertIn("CUSTODY_PATH_MISSING_OR_UNSAFE:work", infrastructure.verify(node, self.manifest()))

    def test_concurrent_apply_is_fenced(self):
        with TemporaryDirectory() as temporary:
            node = Path(temporary) / "node"
            entered = threading.Event()
            release = threading.Event()
            failures: list[BaseException] = []
            original = infrastructure._atomic_write

            def delayed_write(*args, **kwargs):
                entered.set()
                self.assertTrue(release.wait(timeout=2))
                return original(*args, **kwargs)

            def first_apply():
                try:
                    infrastructure.apply(node, self.manifest())
                except BaseException as error:
                    failures.append(error)

            with patch.object(infrastructure, "_atomic_write", side_effect=delayed_write):
                thread = threading.Thread(target=first_apply)
                thread.start()
                self.assertTrue(entered.wait(timeout=2))
                with self.assertRaisesRegex(infrastructure.InfrastructureRefused, "ALREADY_IN_PROGRESS"):
                    infrastructure.apply(node, self.manifest())
                release.set()
                thread.join(timeout=2)

            self.assertFalse(thread.is_alive())
            self.assertEqual(failures, [])
            self.assertEqual(infrastructure.verify(node, self.manifest()), [])


if __name__ == "__main__":
    unittest.main()
