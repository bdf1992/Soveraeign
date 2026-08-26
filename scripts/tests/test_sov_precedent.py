from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_precedent  # noqa: E402


class PrecedentProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for relative, clauses in sov_precedent.REQUIRED_TEXT.items():
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("\n".join(clauses) + "\n", encoding="utf-8")
        profile = self.root / "bindings/sov/profile.json"
        profile.parent.mkdir(parents=True, exist_ok=True)
        profile.write_text(json.dumps({
            "governing_sources": ["CONTRACT.md", "ENGINEERING.md"]
        }), encoding="utf-8")
        schema = self.root / "contracts/example.schema.json"
        schema.parent.mkdir(parents=True, exist_ok=True)
        schema.write_text(json.dumps({"$schema": sov_precedent.DIALECT}), encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_complete_profile_passes(self) -> None:
        self.assertEqual(sov_precedent.check(self.root), [])

    def test_repository_profile_passes(self) -> None:
        self.assertEqual(sov_precedent.check(ROOT), [])

    def test_missing_root_rule_is_named(self) -> None:
        (self.root / "CONTRACT.md").write_text("# Contract\n", encoding="utf-8")
        self.assertTrue(any("C16" in defect for defect in sov_precedent.check(self.root)))

    def test_sov_cannot_drop_the_governing_profile(self) -> None:
        path = self.root / "bindings/sov/profile.json"
        path.write_text(json.dumps({"governing_sources": ["CONTRACT.md"]}), encoding="utf-8")
        self.assertIn(
            "bindings/sov/profile.json: Sov does not inherit ENGINEERING.md",
            sov_precedent.check(self.root),
        )

    def test_schema_validator_default_cannot_choose_the_dialect(self) -> None:
        path = self.root / "contracts/example.schema.json"
        path.write_text(json.dumps({"type": "object"}), encoding="utf-8")
        self.assertTrue(any("Draft 2020-12" in defect for defect in sov_precedent.check(self.root)))


if __name__ == "__main__":
    unittest.main()
