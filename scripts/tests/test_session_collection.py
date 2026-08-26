"""Positive and defeating cases for the Sessions collection.

The defeats that matter here are all one failure in different clothes: a surface
saying more about a session than the session source said.
"""

from __future__ import annotations

from pathlib import Path
import copy
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovsurface import sessions  # noqa: E402
from sovsurface.collection import render  # noqa: E402

LIVE = {
    "session": "session-a75dfb",
    "live": True,
    "ended": False,
    "registered": True,
    "branch": "feat/human-collection-substrate",
    "tree": "C:/Users/bdf19/Desktop/Soveraeign",
    "intent": "human interface integration",
    "at": "2026-08-25T03:54:12Z",
    "pid": 21264,
}
ENDED = {
    "session": "session-old",
    "live": False,
    "ended": True,
    "ended_at": "2026-08-25T01:00:00Z",
    "registered": True,
    "branch": "feat/old",
    "tree": "C:/Users/bdf19/Desktop/Soveraeign",
    "at": "2026-08-25T00:59:00Z",
}


def snapshot(records=(LIVE,), held=None) -> dict:
    return {
        "available": True,
        "source": "scripts/sov_session.py list --json",
        "reason": "",
        "sessions": [item for item in records if item.get("live")],
        "records": list(records),
        "held": held or {},
    }


class SessionCollection(unittest.TestCase):
    def test_a_live_session_becomes_one_card_with_its_own_identity(self) -> None:
        built = sessions.collection(snapshot())
        self.assertEqual([item.identity for item in built.records], ["session-a75dfb"])
        self.assertEqual(built.records[0].kind, "session")
        self.assertEqual(built.collection_id, "sessions")

    def test_the_inspector_carries_the_seven_declared_sections(self) -> None:
        html = render(sessions.collection(snapshot()))
        for section in (
            "Identity",
            "Location",
            "Activity",
            "Claims",
            "Relations",
            "Authority and standing",
            "Sources",
        ):
            self.assertIn(f">{section}</div>", html)

    def test_the_inspector_expands_the_same_record_that_made_the_card(self) -> None:
        built = sessions.collection(snapshot())
        html = render(built)
        card = html.split('data-identity="session-a75dfb"', 1)[1].split("</details>", 1)[0]
        self.assertIn("feat/human-collection-substrate", card)
        self.assertIn("human interface integration", card)
        self.assertIn("21264", card)
        self.assertIn("2026-08-25T03:54:12Z", card)

    def test_harness_presence_never_becomes_a_node_affordance(self) -> None:
        html = render(sessions.collection(snapshot()))
        self.assertIn("HARNESS", html)
        self.assertNotIn(">ACTION<", html)
        self.assertIn("Act as this session unavailable", html)
        self.assertIn("No Node operation is reachable from harness presence", html)
        self.assertIn("holds no Node authority", html)

    def test_an_ended_session_is_never_presented_as_live(self) -> None:
        built = sessions.collection(snapshot((LIVE, ENDED)))
        ended = next(item for item in built.records if item.identity == "session-old")
        self.assertEqual(ended.facets["live"], ("false",))
        self.assertIn(("not live", "muted"), ended.badges)
        self.assertNotIn(("live", "positive"), ended.badges)
        self.assertIn("reports this session as not live", " ".join(ended.omissions))

    def test_liveness_is_read_from_the_source_and_never_recomputed(self) -> None:
        stale = dict(LIVE, live=False, ended=False, at="1999-01-01T00:00:00Z")
        built = sessions.collection(snapshot((stale,)))
        self.assertEqual(built.records[0].facets["live"], ("false",))

    def test_an_absent_principal_is_reported_absent_and_never_defaulted(self) -> None:
        built = sessions.collection(snapshot())
        card = built.records[0]
        self.assertNotIn("principal", card.facets)
        self.assertNotIn("verification", card.facets)
        html = render(built)
        self.assertIn("not reported by this source", html)
        self.assertNotIn("UNVERIFIED", html)
        self.assertNotIn("UNIDENTIFIED", html)

    def test_a_reported_principal_is_carried_exactly_and_not_upgraded(self) -> None:
        claimed = dict(LIVE, principal="principal:claude-code", verification="UNVERIFIED")
        built = sessions.collection(snapshot((claimed,)))
        card = built.records[0]
        self.assertEqual(card.facets["principal"], ("principal:claude-code",))
        self.assertEqual(card.facets["verification"], ("UNVERIFIED",))
        self.assertIn("verification", card.facets["has"])
        html = render(built)
        self.assertIn("UNVERIFIED", html)
        self.assertNotIn("VERIFIED</code>", html.replace("UNVERIFIED</code>", ""))

    def test_claims_come_only_from_the_held_map_the_source_returned(self) -> None:
        held = {
            "scripts/sovsurface": [{"session": "session-a75dfb"}],
            "scripts/other.py": [{"session": "session-elsewhere"}],
        }
        built = sessions.collection(snapshot(held=held))
        card = built.records[0]
        self.assertEqual(card.facets["resource"], ("scripts/sovsurface",))
        self.assertIn("claim", card.facets["has"])
        self.assertNotIn("scripts/other.py", render(built))

    def test_a_session_without_claims_declares_no_claim_facet(self) -> None:
        card = sessions.collection(snapshot()).records[0]
        self.assertNotIn("resource", card.facets)
        self.assertNotIn("claim", card.facets.get("has", ()))
        self.assertIn("holds no path in the claim log", render(sessions.collection(snapshot())))

    def test_relations_are_derived_from_peers_and_nothing_else(self) -> None:
        built = sessions.collection(snapshot((LIVE, ENDED)))
        html = render(built)
        card = html.split('data-identity="session-a75dfb"', 1)[1].split("</details>", 1)[0]
        self.assertIn("Shares this working tree", card)
        self.assertIn("session-old", card)
        self.assertIn("Shares this branch", card)

    def test_a_path_with_whitespace_cannot_become_an_unqueryable_facet(self) -> None:
        held = {"scripts/a file.py": [{"session": "session-a75dfb"}]}
        built = sessions.collection(snapshot(held=held))
        card = built.records[0]
        self.assertNotIn("resource", card.facets)
        self.assertIn("scripts/a file.py", render(built))

    def test_an_unaddressable_claim_never_offers_a_filter_that_matches_nothing(self) -> None:
        held = {"scripts/a file.py": [{"session": "session-a75dfb"}]}
        html = render(sessions.collection(snapshot(held=held)))
        self.assertNotIn('data-filter="resource:scripts/a file.py"', html)
        self.assertIn("claims unavailable", html)
        self.assertIn("no claim a single query token can address", html)

    def test_an_addressable_claim_does_offer_its_filter(self) -> None:
        held = {"scripts/sovsurface": [{"session": "session-a75dfb"}]}
        html = render(sessions.collection(snapshot(held=held)))
        self.assertIn('data-filter="resource:scripts/sovsurface"', html)

    def test_the_tree_facet_never_collapses_two_different_trees(self) -> None:
        here = dict(LIVE, session="s-here", tree="C:/work/a/Soveraeign")
        there = dict(LIVE, session="s-there", tree="C:/work/b/Soveraeign")
        built = sessions.collection(snapshot((here, there)))
        values = [item.facets["tree"] for item in built.records]
        self.assertEqual(
            sorted(values), [("C:/work/a/Soveraeign",), ("C:/work/b/Soveraeign",)]
        )
        self.assertNotEqual(values[0], values[1])

    def test_a_session_alone_on_its_tree_is_not_told_the_field_was_withheld(self) -> None:
        html = render(sessions.collection(snapshot()))
        card = html.split('data-identity="session-a75dfb"', 1)[1].split("</details>", 1)[0]
        relations = card.split(">Relations</div>", 1)[1].split("</div>", 1)[0]
        self.assertIn("no other session", relations)
        self.assertNotIn("not reported by this source", relations)

    def test_a_session_with_no_tree_reported_says_so(self) -> None:
        nowhere = {k: v for k, v in LIVE.items() if k not in ("tree", "branch")}
        html = render(sessions.collection(snapshot((nowhere,))))
        relations = html.split(">Relations</div>", 1)[1].split("</dl>", 1)[0]
        self.assertIn("not reported by this source", relations)
        self.assertNotIn("no other session", relations)

    def test_an_unavailable_source_renders_unavailable_not_empty(self) -> None:
        built = sessions.collection(
            {
                "available": False,
                "source": "scripts/sov_session.py list --json",
                "reason": "scripts/sov_session.py is not present in this working tree",
                "sessions": [],
                "records": [],
                "held": {},
            }
        )
        self.assertFalse(built.available)
        self.assertEqual(built.records, ())
        html = render(built)
        self.assertIn("Sessions unavailable", html)
        self.assertIn("not present in this working tree", html)
        self.assertNotIn("empty source", html)
        self.assertNotIn("No sessions", html)

    def test_building_the_collection_never_mutates_the_snapshot(self) -> None:
        data = snapshot((LIVE, ENDED), held={"a": [{"session": "session-a75dfb"}]})
        before = copy.deepcopy(data)
        render(sessions.collection(data))
        self.assertEqual(data, before)

    def test_the_collection_declares_its_source_and_its_omissions(self) -> None:
        built = sessions.collection(snapshot())
        self.assertEqual(built.source, "scripts/sov_session.py list --json")
        html = render(built)
        self.assertIn("scripts/sov_session.py list --json", html)
        self.assertIn("Authority is not a session field", html)
        self.assertIn("Pull request and issue relations are not read", html)

    def test_presence_panel_summarizes_the_same_collection(self) -> None:
        built = sessions.collection(snapshot((LIVE, ENDED)))
        panel = sessions.presence_panel(built)
        self.assertIn("session-a75dfb", panel)
        self.assertIn("session-old", panel)
        self.assertIn("Presence grants no authority", panel)
        self.assertIn('data-filter="kind:session"', panel)

    def test_presence_panel_states_an_unavailable_source(self) -> None:
        panel = sessions.presence_panel(
            sessions.collection({"available": False, "reason": "no CLI here", "source": "x"})
        )
        self.assertIn("unavailable", panel)
        self.assertIn("no CLI here", panel)


if __name__ == "__main__":
    unittest.main()
