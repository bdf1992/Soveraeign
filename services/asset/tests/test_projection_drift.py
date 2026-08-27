"""Positive and defeating cases for detecting projection drift without rebuilding.

`test_projection_authority.py` proves the other half: a forged row does not
survive a rebuild. That is about what a rebuild restores. These cases are about
what can be *known* before one — because rebuilding to find out destroys the
evidence in the act of collecting it, and the check that stood in for it compared
row counts.

The case that matters is `test_a_row_rewritten_in_place_is_caught_although_the_
counts_agree`. Rewriting a projected row leaves every count identical, so a count
check reports the view in step while the view returns a forged asset for a forged
query and the real label finds nothing. Every other case here is ordinary; that
one is the defect the drift check exists for.

These establish BUILT evidence only.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from soveraeign_asset_service import AssetService
from soveraeign_asset_service.projections import ALTERED, BEHIND, UNSOURCED

FORGED_RECEIPT = "rcpt_forged"


class ProjectionDrift(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.service = AssetService(self.root / "state")
        self.service.grant("Bdo", "Bdo", "ratify:judgement")

    def tearDown(self) -> None:
        self.service.close()
        self.tmp.cleanup()

    def source(self, name: str, content: bytes) -> Path:
        path = self.root / name
        path.write_bytes(content)
        return path

    def ratified_pair(self) -> tuple[str, str]:
        """Two assets and one ratified USED_BY relationship, through the kernel."""
        hero = self.service.ingest(self.source("hero.txt", b"hero"), "Campaign Hero", "Bdo")
        campaign = self.service.ingest(
            self.source("campaign.txt", b"campaign"), "Autumn Campaign", "Bdo")
        proposal = self.service.propose(hero["asset_id"], "claude-adapter", {
            "description": "Primary visual for the autumn launch",
            "relationship": {"predicate": "USED_BY", "dst_asset": campaign["asset_id"]},
        })
        self.service.ratify(proposal, "Bdo")
        self.service.rebuild_projections()
        return hero["asset_id"], campaign["asset_id"]

    def counts(self) -> tuple[int, int]:
        held = self.service.db.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
        projected = self.service.db.execute(
            "SELECT COUNT(*) FROM search_projection").fetchone()[0]
        return held, projected

    def defects(self) -> list[str]:
        return [entry["defect"] for entry in self.service.projection_drift()]

    def test_a_freshly_rebuilt_projection_reports_no_drift(self) -> None:
        self.ratified_pair()
        self.assertEqual(self.service.projection_drift(), [])

    def test_a_row_rewritten_in_place_is_caught_although_the_counts_agree(self) -> None:
        """The failure a row count is structurally blind to."""
        hero, _campaign = self.ratified_pair()
        before = self.counts()

        self.service.db.execute(
            "UPDATE search_projection SET text_value=? WHERE asset_id=?",
            ("Totally Different Thing", hero))
        self.service.db.commit()

        # The count check, which is what stood in for this, still reports in step.
        self.assertEqual(self.counts(), before)
        # And the view now answers for a label that was never ingested.
        self.assertEqual(self.service.search("Totally Different"), [hero])
        self.assertEqual(self.service.search("Campaign Hero"), [])

        drift = self.service.projection_drift()
        self.assertEqual([entry["defect"] for entry in drift], [ALTERED])
        self.assertEqual(drift[0]["table"], "search_projection")
        self.assertEqual(drift[0]["asset_id"], hero)

    def test_a_forged_row_with_nothing_behind_it_is_named_unsourced(self) -> None:
        hero, campaign = self.ratified_pair()
        self.service.db.execute(
            "INSERT INTO graph_projection VALUES(?,?,?,?,?)",
            ("rel_forged", campaign, "OWNS", hero, FORGED_RECEIPT))
        self.service.db.commit()

        drift = self.service.projection_drift()
        self.assertEqual([entry["defect"] for entry in drift], [UNSOURCED])
        self.assertEqual(drift[0]["relationship_id"], "rel_forged")

    def test_a_view_that_has_not_been_rebuilt_is_named_behind(self) -> None:
        self.ratified_pair()
        self.service.ingest(self.source("late.txt", b"late"), "Late Arrival", "Bdo")

        drift = self.service.projection_drift()
        self.assertEqual([entry["defect"] for entry in drift], [BEHIND])
        self.assertNotIn("Late Arrival", str(self.service.search("Late")))

    def test_a_deleted_projection_row_is_also_named_behind(self) -> None:
        hero, _campaign = self.ratified_pair()
        self.service.db.execute("DELETE FROM search_projection WHERE asset_id=?", (hero,))
        self.service.db.commit()
        self.assertEqual(self.defects(), [BEHIND])

    def test_drift_writes_nothing_at_all(self) -> None:
        """A check that changed what it checks would answer about a different store."""
        hero, _campaign = self.ratified_pair()
        self.service.db.execute(
            "UPDATE search_projection SET text_value=? WHERE asset_id=?", ("Forged", hero))
        self.service.db.commit()
        receipts_before = [entry["id"] for entry in self.service.receipts()]

        self.assertEqual(self.defects(), [ALTERED])

        self.assertEqual([entry["id"] for entry in self.service.receipts()], receipts_before,
                         "drift wrote a receipt; it is a read")
        self.assertEqual(self.service.db.execute(
            "SELECT text_value FROM search_projection WHERE asset_id=?", (hero,)
        ).fetchone()[0], "Forged", "drift repaired the row it was asked to report on")

    def test_rebuilding_is_what_clears_drift(self) -> None:
        """Detection and repair stay separate, and the two agree about the ledger."""
        hero, campaign = self.ratified_pair()
        self.service.db.execute(
            "UPDATE search_projection SET text_value=? WHERE asset_id=?", ("Forged", hero))
        self.service.db.execute(
            "INSERT INTO graph_projection VALUES(?,?,?,?,?)",
            ("rel_forged", campaign, "OWNS", hero, FORGED_RECEIPT))
        self.service.db.commit()
        self.assertEqual(sorted(self.defects()), [ALTERED, UNSOURCED])

        self.service.rebuild_projections()

        self.assertEqual(self.service.projection_drift(), [])
        self.assertEqual(self.service.search("Campaign Hero"), [hero])

    def test_an_empty_store_has_no_drift_rather_than_an_error(self) -> None:
        self.assertEqual(self.service.projection_drift(), [])

    def test_a_ratification_written_under_the_older_event_name_is_still_found(self) -> None:
        """Found on a live store, where 153 assets were about to lose their receipts.

        `.local/history-corpus` was ingested before commit e384285 renamed the
        ratification receipt from `proposal.ratify` to `asset.ratify-proposal`.
        Reading only the current name derived every one of those rows as
        UNRATIFIED_LABEL, so a rebuild would have replaced a real receipt id with
        "no receipt" - and the drift check would then have called the store clean,
        because stored and derived would agree on the loss.
        """
        hero, _campaign = self.ratified_pair()
        receipt = self.service.db.execute(
            "SELECT id FROM search_projection JOIN receipts "
            "ON receipts.id = search_projection.source_receipt "
            "WHERE search_projection.asset_id = ?", (hero,)).fetchone()
        self.assertIsNotNone(receipt, "the fixture did not source its row from a receipt")

        # Rewrite the receipt under the name the service used before the rename.
        self.service.db.execute(
            "UPDATE receipts SET event='proposal.ratify' WHERE event='asset.ratify-proposal'")
        self.service.db.commit()

        self.assertEqual(self.service.projection_drift(), [],
                         "the older receipt name reads as a different, missing receipt")
        self.service.rebuild_projections()
        rebuilt = self.service.db.execute(
            "SELECT source_receipt FROM search_projection WHERE asset_id=?", (hero,)
        ).fetchone()[0]
        self.assertEqual(rebuilt, receipt[0],
                         "a rebuild dropped the ratification this row was sourced from")


if __name__ == "__main__":
    unittest.main()
