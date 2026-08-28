"""Positive and defeating cases for the reusable Collection mechanism."""

from __future__ import annotations

from pathlib import Path
import copy
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovsurface.primitives import code  # noqa: E402
from sovsurface.collection import (  # noqa: E402
    Affordance,
    Collection,
    FacetError,
    Record,
    Section,
    cards_total,
    counts,
    facet_total,
    facet_manifest,
    render,
    render_record,
)


def record(identity: str = "thing-1", **overrides: object) -> Record:
    base = {
        "identity": identity,
        "kind": "thing",
        "title": identity,
        "eyebrow": "a thing",
        "search": f"{identity} searchable",
        "facets": {"kind": ("thing",), "colour": ("red", "blue")},
        "sections": (Section("Identity", (("Id", code(identity)),)),),
    }
    base.update(overrides)
    return Record(**base)  # type: ignore[arg-type]


def collection(**overrides: object) -> Collection:
    base = {
        "collection_id": "things",
        "label": "Things",
        "description": "Things read from somewhere else.",
        "source": "somewhere/else.py list --json",
        "records": (record(),),
        "facets": ("kind", "colour"),
    }
    base.update(overrides)
    return Collection(**base)  # type: ignore[arg-type]


class UnreadableCollectionsAreNotCounted(unittest.TestCase):
    """`available=False` means the source was never read, so it contributes no cards.

    `counts()` pins this already: an unavailable collection returns None, not 0,
    because zero is a claim that the source was read and reported nothing. Its
    two siblings had the same guard and nothing pinned it, so dropping
    `if item.available` from either left the totals counting records the page
    will not render - which is the exact defect this module exists to repair,
    reachable through a frozen dataclass any future adapter can build.
    """

    def unread(self) -> Collection:
        """A collection carrying records it never managed to read."""
        return collection(collection_id="unread", available=False,
                          records=(record("ghost-1"), record("ghost-2")))

    def test_counts_says_not_read_rather_than_zero(self) -> None:
        self.assertEqual(counts([self.unread()]), {"unread": None})

    def test_cards_total_excludes_an_unreadable_collection(self) -> None:
        readable = collection(collection_id="things", records=(record("thing-1"),))
        self.assertEqual(cards_total([readable, self.unread()]), 1,
                         "the total counted cards the page will not render")

    def test_facet_total_excludes_an_unreadable_collection(self) -> None:
        readable = collection(collection_id="things", records=(record("thing-1"),))
        self.assertEqual(facet_total([readable, self.unread()], "kind", "thing"), 1,
                         "the filter's count promised cards its filter cannot reveal")

    def test_the_three_totals_agree_about_what_was_read(self) -> None:
        """A count beside a control, a total, and a per-collection reading are
        three statements about one population; they may not disagree."""
        both = [collection(collection_id="things", records=(record("thing-1"),)),
                self.unread()]
        self.assertEqual(counts(both)["unread"], None)
        self.assertEqual(cards_total(both), facet_total(both, "kind", "thing"))


class CollectionMechanism(unittest.TestCase):
    def test_a_record_exposes_identity_kind_search_facets_and_inspector(self) -> None:
        html = render_record(record(), ("kind", "colour"), layout="grid")
        self.assertIn('data-identity="thing-1"', html)
        self.assertIn('data-kind="thing"', html)
        self.assertIn('data-search="thing-1 searchable"', html)
        self.assertIn('data-colour="red blue"', html)
        self.assertIn('data-component="inspector"', html)
        self.assertIn("Identity", html)

    def test_only_declared_facets_become_filterable_attributes(self) -> None:
        html = render_record(record(), ("kind",), layout="grid")
        self.assertIn('data-kind="thing"', html)
        self.assertNotIn("data-colour", html)

    def test_a_facet_key_the_query_grammar_cannot_address_is_refused(self) -> None:
        for bad in ("Kind", "working_tree", "working-tree", "2kind", ""):
            with self.assertRaises(FacetError):
                collection(facets=("kind", bad))

    def test_facet_manifest_declares_keys_to_the_query_script_as_data(self) -> None:
        manifest = facet_manifest(
            [collection(), collection(collection_id="other", facets=("live",))]
        )
        payload = json.loads(manifest.split(">", 1)[1].rsplit("<", 1)[0])
        self.assertEqual(payload, ["colour", "kind", "live"])

    def test_rendering_does_not_mutate_the_records_it_reads(self) -> None:
        built = collection()
        before = copy.deepcopy(built.records[0].facets)
        render(built)
        self.assertEqual(built.records[0].facets, before)

    def test_a_missing_source_renders_unavailable_and_names_the_reason(self) -> None:
        html = render(
            collection(records=(), available=False, unavailable_reason="the CLI is absent")
        )
        self.assertIn("Things unavailable", html)
        self.assertIn("the CLI is absent", html)
        self.assertIn("somewhere/else.py list --json", html)
        self.assertNotIn("data-card=", html)

    def test_an_empty_source_is_not_reported_as_a_missing_one(self) -> None:
        html = render(collection(records=()))
        self.assertIn("empty source, not a missing one", html)
        self.assertNotIn("unavailable", html)

    def test_provenance_stays_recoverable_from_the_rendered_collection(self) -> None:
        html = render(collection())
        self.assertIn('data-component="provenance"', html)
        self.assertIn("somewhere/else.py list --json", html)

    def test_omissions_are_rendered_rather_than_dropped(self) -> None:
        html = render(collection(omissions=("no instance read exists",)))
        self.assertIn("material omission", html)
        self.assertIn("no instance read exists", html)

    def test_an_unavailable_affordance_is_stated_and_never_offered(self) -> None:
        html = render_record(
            record(
                affordances=(
                    Affordance("Do the thing", detail="no route exists", available=False),
                )
            ),
            ("kind",),
            layout="grid",
        )
        self.assertIn("Do the thing unavailable", html)
        self.assertIn("no route exists", html)
        self.assertNotIn("data-filter=\"Do the thing\"", html)

    def test_an_available_affordance_offers_a_filter_or_a_command_never_a_grant(self) -> None:
        html = render_record(
            record(
                affordances=(
                    Affordance("Browse", filter_value="kind:thing"),
                    Affordance("Run", command="python do.py"),
                )
            ),
            ("kind",),
            layout="grid",
        )
        self.assertIn('data-filter="kind:thing"', html)
        self.assertIn("python do.py", html)
        self.assertNotIn("<a href", html)
        self.assertNotIn("<form", html)

    def test_an_unread_collection_has_no_count_rather_than_a_count_of_zero(self) -> None:
        built = [
            collection(),
            collection(collection_id="empty", records=()),
            collection(collection_id="gone", available=False),
        ]
        self.assertEqual(counts(built), {"things": 1, "empty": 0, "gone": None})

    def test_facet_values_count_records_not_values(self) -> None:
        built = collection(
            records=(
                record("a", facets={"kind": ("thing",), "colour": ("red",)}),
                record("b", facets={"kind": ("thing",), "colour": ("red", "blue")}),
            )
        )
        self.assertEqual(built.facet_values("colour"), {"blue": 1, "red": 2})

    def test_record_values_are_escaped_before_entering_the_page(self) -> None:
        html = render_record(
            record("<script>x</script>", facets={"colour": ('"onload=',)}),
            ("colour",),
            layout="grid",
        )
        self.assertNotIn("<script>x</script>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("&quot;onload=", html)

    def test_a_kind_facet_that_disagrees_with_the_card_is_refused(self) -> None:
        with self.assertRaises(FacetError):
            record(facets={"kind": ("session",)})

    def test_the_kind_attribute_is_written_once_from_the_record(self) -> None:
        html = render_record(record(facets={"kind": ("thing",)}), ("kind",), layout="grid")
        self.assertEqual(html.count("data-kind="), 1)
        self.assertIn('data-kind="thing"', html)

    def test_summary_and_section_rows_are_composed_html_the_adapter_owns(self) -> None:
        """The split the Record docstring declares, pinned so it cannot drift silently.

        Escaping every field would make an adapter unable to compose a card, and
        escaping none would let a source string become markup. The mechanism
        escapes the scalar fields and takes ``summary`` and row values as HTML
        the adapter has already composed, so the adapter owns their escaping.
        """
        html = render_record(
            record(
                summary="<p class='card-statline'>composed</p>",
                sections=(Section("Identity", (("Id", "<b>composed</b>"),)),),
            ),
            ("kind",),
            layout="grid",
        )
        self.assertIn("<p class='card-statline'>composed</p>", html)
        self.assertIn("<b>composed</b>", html)

    def test_every_field_the_adapter_does_not_compose_is_escaped(self) -> None:
        """The other half of the same split: nothing else may become markup."""
        hostile = "<img src=x onerror=alert(1)>"
        html = render_record(
            record(
                "id" + hostile,
                title=hostile,
                eyebrow=hostile,
                search=hostile,
                omissions=(hostile,),
                sections=(Section(hostile, (), note=hostile),),
                affordances=(Affordance(hostile, detail=hostile, filter_value=hostile),),
                facets={"colour": (hostile,)},
            ),
            ("colour",),
            layout="grid",
        )
        self.assertNotIn("<img", html)
        self.assertNotIn(hostile, html)
        # Nine fields were seeded; every one has to arrive escaped, and some
        # reach the page more than once, so the floor is the count that matters.
        self.assertGreaterEqual(html.count("&lt;img src=x onerror=alert(1)&gt;"), 9)

    def test_a_section_note_is_escaped_even_though_its_rows_are_not(self) -> None:
        html = render_record(
            record(sections=(Section("Identity", (("Id", "<b>ok</b>"),), note="<hr>"),)),
            ("kind",),
            layout="grid",
        )
        self.assertIn("<b>ok</b>", html)
        self.assertNotIn("<hr>", html)
        self.assertIn("&lt;hr&gt;", html)


if __name__ == "__main__":
    unittest.main()
