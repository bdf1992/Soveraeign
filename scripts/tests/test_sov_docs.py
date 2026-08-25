"""Positive and defeating cases for the documentation reader.

Two claims are under test. The renderer's: every document this node publishes
renders to balanced, escaped HTML, and a construct it cannot handle degrades to
text rather than vanishing. The page's: it shows what the Asset Service holds
for each document, and says so when the bytes on disk have moved since.

BUILT evidence only. Rendering a document witnesses nothing about it.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from unittest import mock
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_docs  # noqa: E402
from sovdocs.markdown import render, slug  # noqa: E402

BALANCED = ("table", "pre", "ul", "ol", "li", "blockquote", "p", "strong", "em", "code",
            "h1", "h2", "h3", "thead", "tbody", "tr", "th", "td", "a")


class MarkdownBlocks(unittest.TestCase):
    def html(self, text: str) -> str:
        return render(text)[0]

    def test_headings_carry_stable_anchors(self):
        body, headings = render("# Open Seams\n\n## S1 - Corpus alignment\n")
        self.assertEqual([h[2] for h in headings], ["open-seams", "s1---corpus-alignment"])
        self.assertIn('id="open-seams"', body)

    def test_a_fenced_block_keeps_its_text_verbatim(self):
        body = self.html("```python\nif a < b:\n    pass\n```")
        self.assertIn("if a &lt; b:", body)
        self.assertIn('data-lang="python"', body)

    def test_a_table_renders_with_a_header(self):
        body = self.html("| Path | Owns |\n| --- | --- |\n| /contracts | Schemas |\n")
        self.assertIn("<th>Path</th>", body)
        self.assertIn("<td>/contracts</td>", body)

    def test_a_nested_list_nests(self):
        body = self.html("- outer\n  - inner\n- second\n")
        self.assertIn("<ul><li>outer<ul><li>inner</li></ul></li><li>second</li></ul>", body)

    def test_front_matter_is_metadata_not_text(self):
        body = self.html("---\nname: a-memory\n---\n\nThe body.\n")
        self.assertNotIn("a-memory", body)
        self.assertIn("The body.", body)

    def test_inline_markup(self):
        body = self.html("**bold** and *italic* and `code` and [a link](https://example.com).")
        self.assertIn("<strong>bold</strong>", body)
        self.assertIn("<em>italic</em>", body)
        self.assertIn("<code>code</code>", body)
        self.assertIn('<a href="https://example.com">a link</a>', body)

    def test_markup_inside_a_code_span_is_not_markup(self):
        """The defeating case: a code span is text, whatever it looks like."""
        body = self.html("Use `**not bold**` here.")
        self.assertIn("<code>**not bold**</code>", body)
        self.assertNotIn("<strong>", body)


class DocumentDecidesNothing(unittest.TestCase):
    """A document must never decide how the viewer behaves."""

    def test_raw_html_in_a_document_is_shown_not_run(self):
        body = render("A <script>alert(1)</script> in prose.\n")[0]
        self.assertNotIn("<script>", body)
        self.assertIn("&lt;script&gt;", body)

    def test_an_angle_bracket_placeholder_survives_as_text(self):
        body = render("Name it `feat/<scope>` when you branch.\n")[0]
        self.assertIn("feat/&lt;scope&gt;", body)

    def test_a_javascript_link_is_made_inert(self):
        body = render("[click](javascript:alert(1))\n")[0]
        self.assertIn('href="#"', body)
        self.assertNotIn("javascript:", body)

    def test_a_relative_link_is_kept(self):
        self.assertIn('href="AGENTS.md"', render("[contract](AGENTS.md)\n")[0])


class EveryPublishedDocument(unittest.TestCase):
    """The renderer runs against the real corpus, not a fixture standing in for it."""

    @classmethod
    def setUpClass(cls):
        cls.sources = sov_docs.sources()

    def test_the_corpus_is_not_empty(self):
        self.assertGreater(len(self.sources), 100)

    def test_every_document_renders_with_balanced_tags(self):
        for source in self.sources:
            body = render(source.read_text(encoding="utf-8", errors="replace"))[0]
            for tag in BALANCED:
                opened = len(re.findall(rf"<{tag}[ >]", body))
                closed = body.count(f"</{tag}>")
                self.assertEqual(opened, closed,
                                 f"{source.relative_to(ROOT)}: <{tag}> {opened}/{closed}")

    def test_every_document_gets_a_unique_identifier(self):
        identifiers = [sov_docs._identifier(s.relative_to(ROOT).as_posix())
                       for s in self.sources]
        self.assertEqual(len(set(identifiers)), len(identifiers))

    def test_no_document_lands_outside_a_group(self):
        # Grouping depends only on each document's path. Re-rendering the whole
        # corpus here duplicates the renderer proof immediately above without
        # strengthening this assertion.
        built = [{"path": source.relative_to(ROOT).as_posix()} for source in self.sources]
        placed = sum(len(group) for _, group in sov_docs.grouped(built))
        self.assertEqual(placed, len(built))


class Custody(unittest.TestCase):
    """The page shows what the Asset Service holds, and flags where it has moved on."""

    SOURCE = ROOT / "AGENTS.md"

    def test_an_uningested_document_says_so_rather_than_claiming_custody(self):
        page = sov_docs.render_site(*self._one({}), 0)
        self.assertIn("Not yet ingested", page)
        self.assertNotIn("changed since ingest", page)

    def test_a_matching_digest_shows_the_recorded_version(self):
        built, groups = self._one(self._ledger(match=True))
        page = sov_docs.render_site(built, groups, 1)
        self.assertIn("asset_recorded", page)
        self.assertNotIn("changed since ingest", page)

    def test_a_moved_document_is_flagged_not_quietly_reattributed(self):
        """The defeating case: newer bytes must never appear under an older receipt."""
        built, groups = self._one(self._ledger(match=False))
        page = sov_docs.render_site(built, groups, 1)
        self.assertIn("changed since ingest", page)

    def _one(self, ledger):
        # Custody semantics only need one real published document. Full-corpus
        # coverage is independently exercised by EveryPublishedDocument above.
        with mock.patch.object(sov_docs, "sources", return_value=[self.SOURCE]):
            built = sov_docs.documents(ledger)
        self.assertEqual(len(built), 1)
        self.assertEqual(built[0]["path"], "AGENTS.md")
        return built, [("Governing set", built)]

    def _ledger(self, match: bool):
        digest = sha256(self.SOURCE.read_bytes()).hexdigest()
        return {"AGENTS.md": {"asset_id": "asset_recorded", "version_id": "version_recorded",
                              "receipt_id": "rcpt_recorded",
                              "digest": digest if match else "0" * 64}}


class Staleness(unittest.TestCase):
    SOURCE = ROOT / "AGENTS.md"

    def test_the_built_page_is_current(self):
        # This is the one whole-corpus site-build integration check.
        self.assertEqual(sov_docs.cmd_check(None), 0)

    def test_the_same_documents_produce_the_same_bytes(self):
        # Determinism is a property of the build pipeline, not corpus size. Use
        # one real published source so this checks the same renderer/group/site
        # path without rebuilding all ~158 documents twice.
        with (mock.patch.object(sov_docs, "sources", return_value=[self.SOURCE]),
              mock.patch.object(sov_docs, "read_ledger", return_value={})):
            self.assertEqual(sov_docs.build(), sov_docs.build())

    def test_an_edited_page_is_refused(self):
        # This case tests comparison/refusal mechanics; the preceding current-page
        # case already proves the canonical real-corpus build.
        original = sov_docs.PAGE.read_text(encoding="utf-8")
        try:
            sov_docs.PAGE.write_text(original + "<!-- by hand -->", encoding="utf-8")
            with mock.patch.object(sov_docs, "build", return_value=original):
                self.assertEqual(sov_docs.cmd_check(None), 1)
        finally:
            sov_docs.PAGE.write_text(original, encoding="utf-8", newline="\n")


class Slugs(unittest.TestCase):
    def test_punctuation_does_not_leak_into_an_anchor(self):
        self.assertEqual(slug("O12 - Does Bdo ratify?"), "o12---does-bdo-ratify")

    def test_an_empty_heading_still_gets_an_anchor(self):
        self.assertEqual(slug("***"), "section")


if __name__ == "__main__":
    unittest.main()
