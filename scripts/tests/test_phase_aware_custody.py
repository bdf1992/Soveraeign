"""Phase-scoped custody discovery without rewriting historical Phase-I custody."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovcustody import model  # noqa: E402


class PhaseAwareCustody(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.legacy = self.root / "custodies.json"
        self.scoped = self.root / "custodies"
        self.scoped.mkdir()
        self.old_collection = model.COLLECTION
        self.old_directory = model.COLLECTION_DIR
        model.COLLECTION = self.legacy
        model.COLLECTION_DIR = self.scoped
        self.addCleanup(self.restore)

    def restore(self) -> None:
        model.COLLECTION = self.old_collection
        model.COLLECTION_DIR = self.old_directory
        self.tmp.cleanup()

    @staticmethod
    def custody(custody_id: str, phase: str) -> dict:
        return {"custody_id": custody_id, "phase": phase}

    def write(self) -> None:
        self.legacy.write_text(json.dumps({
            "phase": "phase:i",
            "custodies": [self.custody("custody:phase-i/x", "phase:i")],
        }), encoding="utf-8")
        (self.scoped / "phase-1-5.json").write_text(json.dumps({
            "phase": "phase:1-5",
            "custodies": [self.custody("custody:phase-1-5/y", "phase:1-5")],
        }), encoding="utf-8")

    def test_legacy_collection_remains_part_of_global_history(self) -> None:
        self.write()
        self.assertEqual(
            [item["custody_id"] for item in model.custodies()],
            ["custody:phase-i/x", "custody:phase-1-5/y"],
        )

    def test_phase_filter_returns_only_that_campaign(self) -> None:
        self.write()
        self.assertEqual(
            [item["custody_id"] for item in model.custodies("phase:1-5")],
            ["custody:phase-1-5/y"],
        )
        self.assertEqual(
            [item["custody_id"] for item in model.custodies("phase:i")],
            ["custody:phase-i/x"],
        )

    def test_absent_scoped_directory_keeps_legacy_reader_working(self) -> None:
        self.write()
        for child in self.scoped.iterdir():
            child.unlink()
        self.scoped.rmdir()
        self.assertEqual(len(model.custodies()), 1)
        self.assertEqual(model.custodies()[0]["phase"], "phase:i")

    def test_lookup_crosses_collection_boundaries(self) -> None:
        self.write()
        self.assertEqual(model.by_id("custody:phase-1-5/y")["phase"], "phase:1-5")


if __name__ == "__main__":
    unittest.main()
