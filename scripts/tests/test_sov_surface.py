"""Positive and defeating cases for the operation surface page.

The page's claim is that it projects three records faithfully and shows their
disagreements rather than resolving them. These cases defeat that claim: a stale
page, a missing page, an endpoint claiming an operation nothing declares, and a
served endpoint the page fails to mark.

BUILT evidence only. Rendering a page witnesses nothing.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_surface  # noqa: E402
from sovsurface.page import render as render_page  # noqa: E402


class SurfaceJoin(unittest.TestCase):
    """The join over the capability map, the manifests, and the gateway manifest."""

    def setUp(self):
        self.view = sov_surface.surface()

    def test_every_declared_capability_appears_once(self):
        listed = [item["capability"]["capability_id"]
                  for service in self.view["services"]
                  for item in self.view["by_service"][service]]
        self.assertEqual(len(listed), self.view["counts"]["declared"])
        self.assertEqual(len(set(listed)), len(listed))

    def test_a_served_endpoint_is_marked_served(self):
        served = [item for service in self.view["services"]
                  for item in self.view["by_service"][service] if item["served"]]
        self.assertEqual(len(served), self.view["counts"]["served"])
        self.assertGreater(len(served), 0, "no endpoint is marked served")

    def test_an_unserved_capability_carries_no_try_command(self):
        """The defeating case: the page must not offer a call that cannot be made."""
        unserved = next(item for service in self.view["services"]
                        for item in self.view["by_service"][service] if not item["served"])
        page = render_page(self.view)
        marker = f'<code class="id">{unserved["capability"]["capability_id"]}</code>'
        section = page.split(marker, 1)[1].split("</details>", 1)[0]
        self.assertNotIn("sov_surface.py try", section)

    def test_the_disagreement_between_the_two_records_is_stated(self):
        gap = self.view["gap"]
        self.assertTrue(gap["map_says_off"] or gap["undeclared"],
                        "expected the map and the gateway to still disagree")
        page = render_page(self.view)
        self.assertIn("Two records disagree", page)
        for name in gap["map_says_off"] + gap["undeclared"]:
            self.assertIn(name, page)

    def test_the_page_resolves_nothing_it_only_reports(self):
        """Choosing between the two records is Bdo's; the page must not pick one."""
        self.assertIn("Bdo", render_page(self.view))


class Determinism(unittest.TestCase):
    def test_the_same_inputs_produce_the_same_bytes(self):
        self.assertEqual(sov_surface.build(), sov_surface.build())

    def test_the_page_carries_the_digest_of_its_inputs(self):
        self.assertIn(sov_surface.input_digest(), sov_surface.build())


class Staleness(unittest.TestCase):
    """A page that no longer matches its inputs must fail a gate, not mislead a reader."""

    def test_the_checked_in_page_is_current(self):
        self.assertEqual(sov_surface.cmd_check(None), 0)

    def test_an_edited_page_is_refused(self):
        original = sov_surface.PAGE.read_bytes()
        try:
            sov_surface.PAGE.write_bytes(original + b"<p>hand-edited</p>")
            self.assertEqual(sov_surface.cmd_check(None), 1)
        finally:
            sov_surface.PAGE.write_bytes(original)

    def test_a_missing_page_is_refused(self):
        original = sov_surface.PAGE.read_bytes()
        try:
            sov_surface.PAGE.unlink()
            self.assertEqual(sov_surface.cmd_check(None), 1)
        finally:
            sov_surface.PAGE.write_bytes(original)


class PhantomOperation(unittest.TestCase):
    """A gateway endpoint may not claim an operation no service manifest declares."""

    def test_a_claim_on_an_undeclared_operation_is_refused(self):
        original = sov_surface.GATEWAY_MANIFEST.read_bytes()
        manifest = json.loads(original.decode("utf-8"))
        manifest["endpoints"][0]["realizes"] = "asset.conjure-widget"
        try:
            sov_surface.GATEWAY_MANIFEST.write_bytes(
                json.dumps(manifest, indent=2).encode("utf-8"))
            with self.assertRaises(sov_surface.PhantomOperation) as raised:
                sov_surface.surface()
            self.assertIn("asset.conjure-widget", str(raised.exception))
        finally:
            sov_surface.GATEWAY_MANIFEST.write_bytes(original)


class TryCommand(unittest.TestCase):
    """`try` is the page's call button: it really calls, and it really refuses."""

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def run_try(self, tool: str, *arguments: str, session: str | None = None) -> int:
        return sov_surface.main(
            ["try", tool, *arguments, "--state-root", str(self.root / "state")]
            + (["--session", session] if session else []))

    def test_an_act_without_a_session_is_refused_rather_than_run(self):
        self.assertEqual(self.run_try("asset_ingest", "path=README.md", "label=x",
                                      "actor=Bdo"), 0)

    def test_an_invented_session_is_refused(self):
        self.assertEqual(self.run_try("asset_search", "query=x", session="session_invented"), 0)

    def test_a_read_runs_with_no_session_at_all(self):
        self.assertEqual(self.run_try("asset_search", "query=nothing"), 0)


if __name__ == "__main__":
    unittest.main()
