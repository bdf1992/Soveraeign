"""Defeating cases for the human rendering of the canonical Node Interface."""

from __future__ import annotations

from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
import io
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_surface  # noqa: E402
from sovsurface.page import render  # noqa: E402


class SurfaceProjection(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.interface = sov_surface.surface()
        cls.page = render(cls.interface)

    def operation(self, operation_id: str) -> dict:
        return next(item for item in self.interface["operations"]
                    if item["operation_id"] == operation_id)

    def test_every_canonical_operation_appears_once(self) -> None:
        identifiers = [item["operation_id"] for item in self.interface["operations"]]
        self.assertEqual(len(identifiers), self.interface["counts"]["declared"])
        self.assertEqual(len(identifiers), len(set(identifiers)))

    def test_reachability_is_not_inferred_from_policy_activation(self) -> None:
        read_asset = self.operation("asset.read-asset")
        self.assertTrue(read_asset["facts"]["policy_active"])
        self.assertFalse(read_asset["facts"]["reachable"])
        marker = '<code class="id">asset.read-asset</code>'
        section = self.page.split(marker, 1)[1].split("</details>", 1)[0]
        self.assertNotIn("sov_surface.py try", section)

    def test_only_the_three_exact_service_owned_routes_are_actionable(self) -> None:
        reachable = [item for item in self.interface["operations"]
                     if item["facts"]["reachable"]]
        self.assertEqual([item["operation_id"] for item in reachable],
                         ["asset.ingest-asset", "console.read-thread", "registry.resolve"])
        for operation in ("asset.ingest-asset", "console.read-thread", "registry.resolve"):
            marker = f'<code class="id">{operation}</code>'
            section = self.page.split(marker, 1)[1].split("</details>", 1)[0]
            self.assertIn("sov_surface.py try", section)

    def test_node_root_kernel_and_open_seams_are_visible(self) -> None:
        self.assertIn(self.interface["node"]["node_id"], self.page)
        self.assertIn(self.interface["node"]["root_seat"], self.page)
        self.assertIn("No universal health score", self.page)
        self.assertIn("asset.read-asset", self.page)

    def test_rendering_claims_neither_observation_nor_authority(self) -> None:
        self.assertEqual(self.interface["counts"]["observed"], 0)
        self.assertIn("grants nothing", self.page)
        self.assertIn("not an observation", self.page)


class DeterminismAndStaleness(unittest.TestCase):
    def test_same_inputs_produce_same_page(self) -> None:
        self.assertEqual(sov_surface.build(), sov_surface.build())

    def test_page_carries_input_digest(self) -> None:
        self.assertIn(sov_surface.input_digest(), sov_surface.build())

    def test_checked_interface_and_page_are_current(self) -> None:
        self.assertEqual(sov_surface.command_check(None), 0)

    def test_a_hand_edit_is_refused(self) -> None:
        original = sov_surface.PAGE.read_bytes()
        try:
            sov_surface.PAGE.write_bytes(original + b"<!-- private authority -->")
            self.assertEqual(sov_surface.command_check(None), 1)
        finally:
            sov_surface.PAGE.write_bytes(original)


class TryPath(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / "payload.txt"
        self.source.write_text("surface action\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_try(self, operation: str, binding: str = "HUMAN") -> tuple[int, str]:
        output = io.StringIO()
        with redirect_stdout(output):
            code = sov_surface.main([
                "try", operation, f"path={self.source}", "label=Surface",
                "--binding", binding, "--actor", "surface-actor", "--scope", "asset:new",
                "--state-root", str(self.root / binding.lower()),
            ])
        return code, output.getvalue()

    def test_human_action_without_authority_returns_actual_refused_receipt(self) -> None:
        code, output = self.run_try("asset.ingest-asset")
        self.assertEqual(code, 0)
        receipt = json.loads(output)
        self.assertEqual(receipt["kind"], "RECEIPT")
        self.assertEqual(receipt["payload"]["outcome"], "REFUSED")
        self.assertEqual(receipt["payload"]["detail"]["reason_code"], "AUTHORITY_REFUSED")

    def test_model_takes_the_same_gateway_refusal_path(self) -> None:
        code, output = self.run_try("asset.ingest-asset", "MODEL")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output)["payload"]["detail"]["reason_code"],
                         "AUTHORITY_REFUSED")

    def test_unreachable_operation_is_not_offered_to_gateway(self) -> None:
        code, output = self.run_try("console.resolve-judgement")
        self.assertEqual(code, 0)
        self.assertIn("REFUSED OPERATION_NOT_REACHABLE", output)
        self.assertFalse((self.root / "human").exists())


if __name__ == "__main__":
    unittest.main()
