"""Contract tests for the composable Human Binding workspace."""

from __future__ import annotations

from pathlib import Path
import copy
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_surface  # noqa: E402
from sovnode.interface_inputs import REFERENCE  # noqa: E402
from sovsurface import cards  # noqa: E402
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
        manifest = self.page.split("data-facet-keys>", 1)[1].split("</script>", 1)[0]
        self.assertEqual(json.loads(manifest), sorted(declared))

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

    def test_a_query_matching_nothing_reaches_its_own_empty_state(self) -> None:
        script = self.page.split("<script>", 1)[1].rsplit("</script>", 1)[0]
        self.assertIn("data-no-results", script)
        self.assertIn("none.hidden = shown > 0", script)
        self.assertIn("data-no-results hidden", self.page)

    def test_query_and_selection_never_reach_a_source(self) -> None:
        script = self.page.split("<script>", 1)[1].rsplit("</script>", 1)[0]
        for forbidden in ("fetch(", "XMLHttpRequest", "location", "<form", "localStorage"):
            self.assertNotIn(forbidden, script)

    def test_an_unread_session_source_is_never_counted_as_zero(self) -> None:
        self.assertIn("harness sessions not read", self.page)
        self.assertNotIn("0 harness sessions", self.page)
        nav = self.page.split('data-filter="kind:session"', 1)[1].split("</button>", 1)[0]
        self.assertNotIn('<span class="count">0</span>', nav)

    def test_footer_keeps_projection_boundary_visible(self) -> None:
        self.assertIn(self.interface["input_state_digest"], self.page)
        self.assertIn("rendering grants nothing", self.page)
        self.assertIn("not an observation", self.page)

    def test_every_offered_invocation_is_one_the_human_binding_is_admitted_to(self) -> None:
        """A card may only offer a command the canonical surface would also offer."""
        offered = 0
        for chunk in self.page.split('<details class="card')[1:]:
            card = chunk.split("</details>", 1)[0]
            if "sov_surface.py try" not in card:
                continue
            offered += 1
            self.assertIn("HUMAN binding", card)
            self.assertIn("ADMITTED", card)
            self.assertNotIn("NOT ADMITTED", card)
        self.assertEqual(offered, self.interface["counts"]["reachable"])

    def test_every_operation_card_states_its_binding_admission(self) -> None:
        for record in self.interface["operations"]:
            card = self.card(record["operation_id"])
            self.assertIn("HUMAN binding", card)
            self.assertIn("ACTOR_KIND_", card)


class OperationCardBinding(unittest.TestCase):
    """Route reachability and actor-kind admission are two facts, stated separately.

    The checked Node Interface currently admits HUMAN on every reachable
    operation, so the refusal is proved against a fixture derived from a real
    record rather than waiting for the interface to grow the case.
    """

    @classmethod
    def setUpClass(cls) -> None:
        reference = json.loads(REFERENCE.read_text(encoding="utf-8"))
        cls.reachable = next(
            item for item in reference["operations"] if item["facts"]["reachable"]
        )
        cls.inspect_only = next(
            item for item in reference["operations"] if not item["facts"]["reachable"]
        )

    def test_an_admitted_binding_over_an_exact_route_offers_the_invocation(self) -> None:
        record = copy.deepcopy(self.reachable)
        self.assertIn("HUMAN", record["actor_kinds"])
        card = cards.operation_record(record)
        invoke = card.affordances[0]
        self.assertTrue(invoke.available)
        self.assertIn("sov_surface.py try", invoke.command)
        self.assertEqual(card.facets["binding"], ("human",))

    def test_an_exact_route_the_human_binding_cannot_use_offers_nothing(self) -> None:
        record = copy.deepcopy(self.reachable)
        record["actor_kinds"] = ["MODEL"]
        card = cards.operation_record(record)
        invoke = card.affordances[0]
        self.assertFalse(invoke.available)
        self.assertEqual(invoke.command, "")
        self.assertIn("ACTOR_KIND_NOT_ADMITTED", invoke.detail)
        self.assertIn("does not widen it", invoke.detail)
        self.assertEqual(card.facets["binding"], ("none",))

    def test_admission_is_stated_even_where_no_exact_route_exists(self) -> None:
        card = cards.operation_record(copy.deepcopy(self.inspect_only))
        rows = dict(
            row
            for section in card.sections
            if section.title == "Affordance"
            for row in section.rows
        )
        self.assertIn("HUMAN binding", rows)
        self.assertFalse(card.affordances[0].available)

    def test_the_card_never_reads_a_route_affordance_the_interface_renamed(self) -> None:
        record = copy.deepcopy(self.reachable)
        record.pop("route_affordance")
        record["affordance"] = {"kind": "ACTION", "reason_code": "X", "explanation": "y"}
        with self.assertRaises(KeyError):
            cards.operation_record(record)


if __name__ == "__main__":
    unittest.main()
