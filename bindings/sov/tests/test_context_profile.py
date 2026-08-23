"""Independent positive and defeating checks for the Sov context profile."""

from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys
import unittest


SOV = Path(__file__).resolve().parents[1]
ROOT = SOV.parents[1]
VALIDATOR = SOV / "validate.py"


class SovContextProfileTests(unittest.TestCase):
    def run_fixture(self, name: str, expected_code: int) -> dict[str, object]:
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), str(SOV / "fixtures" / name)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, expected_code, result.stderr or result.stdout)
        return json.loads(result.stdout)

    def test_inspection_context_is_ready_but_not_authorized(self) -> None:
        result = self.run_fixture("inspection-only.json", 0)
        self.assertEqual(result["outcome"], "CONTEXT_READY")
        self.assertFalse(result["operation_authorized"])
        self.assertEqual(result["authority_source"], "OPERATION_BOUNDARY_NOT_PROFILE")
        self.assertIsNone(result["requested_effect_class"])

    def test_context_cannot_grant_authority(self) -> None:
        result = self.run_fixture("context-authority.json", 2)
        self.assertEqual(result["outcome"], "REFUSED")
        self.assertEqual(result["reason_code"], "PROFILE_AUTHORITY_REFUSED")

    def test_unresolved_grant_cannot_authorize_a_consequential_effect(self) -> None:
        result = self.run_fixture("consequential-effect.json", 2)
        self.assertEqual(result["outcome"], "REFUSED")
        self.assertEqual(result["reason_code"], "LIVE_GRANT_RESOLUTION_UNAVAILABLE")

    def test_profile_has_no_private_authority_or_state(self) -> None:
        profile = json.loads((SOV / "profile.json").read_text(encoding="utf-8"))
        self.assertEqual(profile["display_name"], "Sov")
        self.assertFalse(profile["authority"]["granted_by_profile"])
        self.assertFalse(profile["state"]["owns_authoritative_state"])
        self.assertFalse(profile["state"]["allows_private_durable_state"])
        self.assertIsNone(profile["default_effect_class"])
        self.assertEqual(profile["fallback_policy"], "NONE")

    def test_all_binding_json_surfaces_parse(self) -> None:
        for path in sorted(SOV.rglob("*.json")):
            with self.subTest(path=path.name):
                value = json.loads(path.read_text(encoding="utf-8"))
                self.assertIsInstance(value, dict)


if __name__ == "__main__":
    unittest.main()
