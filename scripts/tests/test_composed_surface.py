"""Contract tests for the composable Human Binding workspace."""

from __future__ import annotations

from pathlib import Path
import copy
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_surface  # noqa: E402
from sovsurface.composed import collections, render  # noqa: E402

UNAVAILABLE = {
    "available": False,
    "source": "scripts/sov_session.py list --json",
    "reason": "scripts/sov_session.py is not present in this working tree",
    "sessions": [],
    "records": [],
    "held": {},
}


class ComposedSurface(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.interface = sov_surface.surface()
        cls.page = render(cls.interface, UNAVAILABLE)

    def card(self, identity: str) -> str:
        marker = f'data-identity="{identity}"'
        return self.page.split(marker, 1)[1].split("</details>", 1)[0]

    def test_shell_is_composed_from_workspace_roles(self) -> None:
        for component in (
            "service-rail",
            "browser-nav",
            "command-bar",
            "workspace",
            "utility-drawer",
            "filter-pills",
            "inspector",
            "provenance",
            "presence",
        ):
            self.assertIn(f'data-component="{component}"', self.page)

    def test_every_collection_reaches_the_workspace(self) -> None:
        for collection_id in ("sessions", "services", "subjects", "operations"):
            self.assertIn(f'data-collection="{collection_id}"', self.page)

    def test_rendering_never_mutates_the_interface_it_reads(self) -> None:
        before = copy.deepcopy(self.interface)
        render(self.interface, UNAVAILABLE)
        self.assertEqual(self.interface, before)

    def test_shell_does_not_claim_live_presence_it_has_not_read(self) -> None:
        self.assertIn("OBJECT_INSTANCES_NOT_PROJECTED", self.page)
        self.assertNotIn(">Active Now<", self.page)
        self.assertIn("Sessions unavailable", self.page)
        self.assertIn("not present in this working tree", self.page)

    def test_asset_browser_is_a_filter_over_canonical_records(self) -> None:
        self.assertIn('data-filter="service:asset"', self.page)
        self.assertIn("Declared subjects only", self.page)
        self.assertIn("No governed object-instance read projection exists", self.page)

    def test_query_grammar_declares_the_dimensions_the_records_carry(self) -> None:
        for query in (
            "service:asset",
            "affordance:ACTION",
            "subject:Asset",
            "authority:read:registry",
            "kind:session",
            "live:true",
            "has:claim",
        ):
            self.assertIn(query, self.page)

    def test_declared_facet_keys_reach_the_query_script_as_data(self) -> None:
        built = collections(self.interface, UNAVAILABLE)
        declared = {key for item in built for key in item.facets}
        for key in declared:
            self.assertIn(f'"{key}"', self.page.split("data-facet-keys>", 1)[1])

    def test_exact_routes_are_the_only_cards_with_invoke_commands(self) -> None:
        self.assertIn("sov_surface.py try", self.card("asset.ingest-asset"))
        self.assertIn("sov_surface.py try", self.card("registry.resolve"))
        self.assertNotIn("sov_surface.py try", self.card("asset.read-asset"))
        self.assertNotIn("sov_surface.py try", self.card("console.resolve-judgement"))

    def test_unreachable_operations_state_their_refusal_instead_of_hiding_it(self) -> None:
        read_asset = self.card("asset.read-asset")
        self.assertIn("INSPECT", read_asset)
        self.assertIn("ACTIVE_POLICY_HAS_NO_EXACT_ROUTE", read_asset)
        self.assertIn("unavailable", read_asset)
        self.assertIn("does not widen it", read_asset)

    def test_query_and_selection_never_reach_a_source(self) -> None:
        script = self.page.split("<script>", 1)[1].rsplit("</script>", 1)[0]
        for forbidden in ("fetch(", "XMLHttpRequest", "location", "<form", "localStorage"):
            self.assertNotIn(forbidden, script)

    def test_footer_keeps_projection_boundary_visible(self) -> None:
        self.assertIn(self.interface["input_state_digest"], self.page)
        self.assertIn("rendering grants nothing", self.page)
        self.assertIn("not an observation", self.page)


if __name__ == "__main__":
    unittest.main()
