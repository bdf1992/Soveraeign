"""Positive and defeating cases for what makes two assets the same, or one.

Five words got used for four ideas. These cases fix which is which:

- versioned: capturing one source again is one identity with a history;
- duplicate: identical bytes under two sources are two identities sharing one
  blob, and re-reading unchanged bytes is neither a version nor a duplicate;
- derived: a version produced by an operation from other versions;
- composite: that same operation with more than one input, not a fifth kind;
- related: an assertion between two assets, which needs authority.

BUILT evidence only.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from soveraeign_asset_service import AssetService, AuthorityRefused  # noqa: E402


class AssetCase(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.service = AssetService(self.root / "state")
        self.service.grant("Bdo", "Bdo", "operate:derive", ttl_seconds=900)
        self.service.grant("Bdo", "Bdo", "ratify:judgement", ttl_seconds=900)

    def tearDown(self):
        self.service.close()
        self.tmp.cleanup()

    def source(self, name: str, content: bytes) -> Path:
        path = self.root / name
        path.write_bytes(content)
        return path


class Versioned(AssetCase):
    def test_a_rewritten_source_is_a_new_version_of_one_asset(self):
        path = self.source("spec.md", b"one\n")
        first = self.service.ingest(path, "Spec", "Bdo", locator="repo:spec.md")
        path.write_bytes(b"two\n")
        second = self.service.ingest(path, "Spec", "Bdo", locator="repo:spec.md")
        path.write_bytes(b"three\n")
        third = self.service.ingest(path, "Spec", "Bdo", locator="repo:spec.md")
        self.assertEqual({first["asset_id"], second["asset_id"], third["asset_id"]},
                         {first["asset_id"]})
        history = self.service.history(first["asset_id"])
        self.assertEqual([entry["role"] for entry in history],
                         ["ORIGINAL", "REVISION", "REVISION"])

    def test_history_is_oldest_first_and_carries_every_digest(self):
        path = self.source("spec.md", b"one\n")
        asset = self.service.ingest(path, "Spec", "Bdo", locator="repo:spec.md")
        path.write_bytes(b"two\n")
        self.service.ingest(path, "Spec", "Bdo", locator="repo:spec.md")
        history = self.service.history(asset["asset_id"])
        self.assertEqual(len(history), 2)
        self.assertNotEqual(history[0]["digest"], history[1]["digest"])
        self.assertLessEqual(history[0]["created_at"], history[1]["created_at"])

    def test_the_superseded_version_is_named_in_the_receipt(self):
        """History is only useful if each step says what it followed."""
        path = self.source("spec.md", b"one\n")
        first = self.service.ingest(path, "Spec", "Bdo", locator="repo:spec.md")
        path.write_bytes(b"two\n")
        self.service.ingest(path, "Spec", "Bdo", locator="repo:spec.md")
        latest = [r for r in self.service.receipts() if r["event"] == "asset.ingest-asset"][-1]
        self.assertEqual(json.loads(latest["payload_json"])["supersedes"],
                         first["version_id"])

    def test_an_old_version_is_never_rewritten(self):
        """The defeating case: a version is an immutable state, so nothing edits it."""
        path = self.source("spec.md", b"one\n")
        first = self.service.ingest(path, "Spec", "Bdo", locator="repo:spec.md")
        path.write_bytes(b"two\n")
        self.service.ingest(path, "Spec", "Bdo", locator="repo:spec.md")
        original = self.service.history(first["asset_id"])[0]
        self.assertEqual(original["id"], first["version_id"])
        self.assertEqual(original["digest"], first["digest"])


class Duplicate(AssetCase):
    def test_identical_bytes_under_two_sources_stay_two_identities(self):
        first = self.service.ingest(self.source("a.md", b"same\n"), "A", "Bdo",
                                    locator="repo:a.md")
        second = self.service.ingest(self.source("b.md", b"same\n"), "B", "Bdo",
                                     locator="repo:b.md")
        self.assertEqual(first["digest"], second["digest"])
        self.assertNotEqual(first["asset_id"], second["asset_id"])

    def test_the_store_holds_those_bytes_once(self):
        self.service.ingest(self.source("a.md", b"same\n"), "A", "Bdo", locator="repo:a.md")
        self.service.ingest(self.source("b.md", b"same\n"), "B", "Bdo", locator="repo:b.md")
        blobs = list((self.root / "state" / "blobs" / "sha256").glob("*/*"))
        self.assertEqual(len(blobs), 1)

    def test_shared_custody_is_read_not_asserted(self):
        first = self.service.ingest(self.source("a.md", b"same\n"), "A", "Bdo",
                                    locator="repo:a.md")
        second = self.service.ingest(self.source("b.md", b"same\n"), "B", "Bdo",
                                     locator="repo:b.md")
        entries = self.service.duplicates()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["asset_ids"],
                         sorted([first["asset_id"], second["asset_id"]]))

    def test_distinct_bytes_report_no_duplicate(self):
        """The defeating case: the read must not invent sameness."""
        self.service.ingest(self.source("a.md", b"one\n"), "A", "Bdo", locator="repo:a.md")
        self.service.ingest(self.source("b.md", b"two\n"), "B", "Bdo", locator="repo:b.md")
        self.assertEqual(self.service.duplicates(), [])

    def test_a_superseded_digest_does_not_linger_as_a_duplicate(self):
        """A digest one asset has moved past is not shared custody with anyone."""
        path = self.source("a.md", b"same\n")
        self.service.ingest(path, "A", "Bdo", locator="repo:a.md")
        self.service.ingest(self.source("b.md", b"same\n"), "B", "Bdo", locator="repo:b.md")
        self.assertEqual(len(self.service.duplicates()), 1)
        path.write_bytes(b"moved on\n")
        self.service.ingest(path, "A", "Bdo", locator="repo:a.md")
        still = [entry for entry in self.service.duplicates() if entry["holders"] > 1]
        self.assertEqual(still, [], "a past version should not read as present duplication")


class DerivedAndComposite(AssetCase):
    def _asset(self, name: str, body: bytes):
        return self.service.ingest(self.source(name, body), name, "Bdo", locator=f"repo:{name}")

    def test_a_single_input_derivation_records_one_input(self):
        asset = self._asset("hero.txt", b"hero\n")
        run = self.service.request_derivative(asset["asset_id"], asset["version_id"], "Bdo")
        fence = self.service.claim(run, "worker")
        version = self.service.report_derivative(run, "worker", fence, b"{}")
        row = self.service.db.execute("SELECT derivation_json,role FROM versions WHERE id=?",
                                      (version,)).fetchone()
        derivation = json.loads(row["derivation_json"])
        self.assertEqual(row["role"], "DERIVATIVE")
        self.assertEqual(derivation["input_version_ids"], [asset["version_id"]])
        self.assertFalse(derivation["composite"])

    def test_a_composite_records_every_input_it_was_assembled_from(self):
        one = self._asset("one.txt", b"one\n")
        two = self._asset("two.txt", b"two\n")
        three = self._asset("three.txt", b"three\n")
        inputs = [one["version_id"], two["version_id"], three["version_id"]]
        run = self.service.request_derivative(one["asset_id"], inputs, "Bdo", kind="digest-page")
        fence = self.service.claim(run, "worker")
        version = self.service.report_derivative(run, "worker", fence, b"assembled")
        derivation = json.loads(
            self.service.db.execute("SELECT derivation_json FROM versions WHERE id=?",
                                    (version,)).fetchone()["derivation_json"])
        self.assertEqual(derivation["input_version_ids"], inputs)
        self.assertTrue(derivation["composite"])

    def test_a_derivation_with_no_input_is_refused(self):
        """The defeating case: a derived version must say what it came from."""
        asset = self._asset("hero.txt", b"hero\n")
        with self.assertRaises(ValueError):
            self.service.request_derivative(asset["asset_id"], [], "Bdo")

    def test_deriving_without_a_grant_is_refused(self):
        asset = self._asset("hero.txt", b"hero\n")
        with self.assertRaises(AuthorityRefused):
            self.service.request_derivative(asset["asset_id"], asset["version_id"], "nobody")


class Related(AssetCase):
    """A relation is an assertion about two assets, so it needs authority."""

    def _two(self):
        first = self.service.ingest(self.source("a.md", b"a\n"), "A", "Bdo", locator="repo:a.md")
        second = self.service.ingest(self.source("b.md", b"b\n"), "B", "Bdo", locator="repo:b.md")
        return first, second

    def test_a_ratified_relation_becomes_effective(self):
        first, second = self._two()
        proposal = self.service.propose(
            first["asset_id"], "Bdo",
            {"relationship": {"predicate": "cites", "dst_asset": second["asset_id"]}})
        self.service.ratify(proposal, "Bdo")
        relations = self.service.relationships(first["asset_id"])
        self.assertEqual([(r["predicate"], r["standing"]) for r in relations],
                         [("cites", "EFFECTIVE")])

    def test_an_unratified_relation_does_not_exist_yet(self):
        """The defeating case: recording a proposal asserts nothing."""
        first, second = self._two()
        self.service.propose(
            first["asset_id"], "Bdo",
            {"relationship": {"predicate": "cites", "dst_asset": second["asset_id"]}})
        self.assertEqual(self.service.relationships(first["asset_id"]), [])

    def test_ratifying_without_authority_is_refused(self):
        first, second = self._two()
        proposal = self.service.propose(
            first["asset_id"], "Bdo",
            {"relationship": {"predicate": "cites", "dst_asset": second["asset_id"]}})
        with self.assertRaises(AuthorityRefused):
            self.service.ratify(proposal, "nobody")
        self.assertEqual(self.service.relationships(first["asset_id"]), [])

    def test_derivation_needs_no_ratification_because_an_operation_produced_it(self):
        """Derivation and assertion are not the same edge and are not gated the same."""
        asset = self.service.ingest(self.source("h.txt", b"h\n"), "H", "Bdo",
                                    locator="repo:h.txt")
        run = self.service.request_derivative(asset["asset_id"], asset["version_id"], "Bdo")
        fence = self.service.claim(run, "worker")
        version = self.service.report_derivative(run, "worker", fence, b"{}")
        self.assertIsNotNone(version)
        self.assertEqual(self.service.relationships(asset["asset_id"]), [])


if __name__ == "__main__":
    unittest.main()
