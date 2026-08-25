"""Contract tests for the alternate composable Human Binding shell."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_surface  # noqa: E402
from sovsurface.composed import render  # noqa: E402


class ComposedSurface(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.interface = sov_surface.surface()
        cls.page = render(cls.interface)

    def section(self, operation_id: str) -> str:
        marker = f'<code class="id">{operation_id}</code>'
        return self.page.split(marker, 1)[1].split("</details>", 1)[0]

    def test_shell_is_composed_from_workspace_roles(self) -> None:
        for component in (
            "service-rail",
            "browser-nav",
            "command-bar",
            "workspace",
            "utility-drawer",
            "filter-pills",
        ):
            self.assertIn(f'data-component="{component}"', self.page)

    def test_discord_interaction_grammar_does_not_claim_live_presence(self) -> None:
        self.assertIn("No live presence implied", self.page)
        self.assertIn("does not fake an Active Now list", self.page)
        self.assertIn("OBJECT_INSTANCES_NOT_PROJECTED", self.page)
        self.assertNotIn(">Active Now<", self.page)

    def test_asset_browser_is_a_filter_over_canonical_records(self) -> None:
        self.assertIn('data-filter="service:asset"', self.page)
        self.assertIn("Asset &amp; subject browser", self.page)
        self.assertIn("Declared subjects only", self.page)

    def test_query_grammar_filters_existing_dimensions_only(self) -> None:
        for query in (
            "service:asset",
            "affordance:ACTION",
            "subject:Asset",
            "authority:read:registry",
            "kind:operation",
        ):
            self.assertIn(query, self.page)

    def test_exact_routes_are_the_only_cards_with_invoke_commands(self) -> None:
        self.assertIn("sov_surface.py try", self.section("asset.ingest-asset"))
        self.assertIn("sov_surface.py try", self.section("registry.resolve"))
        self.assertNotIn("sov_surface.py try", self.section("asset.read-asset"))
        self.assertNotIn("sov_surface.py try", self.section("console.resolve-judgement"))

    def test_affordance_reason_survives_card_composition(self) -> None:
        read_asset = self.section("asset.read-asset")
        self.assertIn("INSPECT", read_asset)
        self.assertIn("ACTIVE_POLICY_HAS_NO_EXACT_ROUTE", read_asset)

    def test_footer_keeps_projection_boundary_visible(self) -> None:
        self.assertIn(self.interface["input_state_digest"], self.page)
        self.assertIn("rendering grants nothing", self.page)
        self.assertIn("not an observation", self.page)


if __name__ == "__main__":
    unittest.main()
