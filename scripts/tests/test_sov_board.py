"""Unit tests for the board survey, the approval gate, and the review surface.

The semantic cases live in ``conformance/fixtures/board/survey-cases.json`` and run
through ``scripts/sov_board.py selfcheck``. These tests cover the local mechanics of
what a survey proposes, what an approval may select, and what the surface must show.
The write crossing itself is covered by ``test_github_crossing.py``.
"""

from __future__ import annotations

from pathlib import Path
import importlib.util
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovboard import render as rendermod  # noqa: E402
from sovboard import survey as surveymod  # noqa: E402
from sovboard.actions import Action, Batch, load_batch, select  # noqa: E402
from sovticket import labels as labelmod  # noqa: E402

board = importlib.import_module("sov_board")


LABEL_ADD = Action(
    kind="LABEL_ADD", target="#40", argument="type: bit",
    evidence="metadata implies it", rule="CONTRIBUTING.md", recommendation="add it",
)
DEFECT = Action(
    kind="CONTRACT_DEFECT", target="#52", argument="",
    evidence="no metadata block", rule="contracts/issue-metadata.schema.json", recommendation="author one",
)
RECEIPT = {
    "source_repository": "fixture/board",
    "captured_at": "2026-08-23T12:00:00Z",
    "export_digest": "sha256:" + "0" * 64,
}


class ActionKindTests(unittest.TestCase):
    """An action's kind decides whether an approval can ever execute it."""

    def test_unknown_kind_is_refused_at_construction(self) -> None:
        with self.assertRaises(ValueError):
            Action(kind="CLOSE_ISSUE", target="#1", evidence="e", rule="r", recommendation="d")

    def test_disposition_follows_the_declared_tables(self) -> None:
        self.assertEqual(LABEL_ADD.disposition, "PROPOSE")
        self.assertEqual(DEFECT.disposition, "REPORT")

    def test_report_actions_are_rendered_as_observe_only(self) -> None:
        """A report cannot be executed, so it must never claim an external effect class."""
        self.assertEqual(LABEL_ADD.as_dict()["effect_class"], "EXTERNAL_WORLD")
        self.assertEqual(DEFECT.as_dict()["effect_class"], "OBSERVE_ONLY")

    def test_identity_is_stable_across_position_and_wording(self) -> None:
        restated = Action(
            kind="LABEL_ADD", target="#40", argument="type: bit",
            evidence="different words", rule="different rule", recommendation="different move",
        )
        self.assertEqual(LABEL_ADD.identity, restated.identity)

    def test_identity_separates_different_targets(self) -> None:
        other = Action(
            kind="LABEL_ADD", target="#41", argument="type: bit",
            evidence="e", rule="r", recommendation="d",
        )
        self.assertNotEqual(LABEL_ADD.identity, other.identity)


class ApprovalTests(unittest.TestCase):
    """Approval is the whole gate, so every way of getting it wrong must refuse by name."""

    def setUp(self) -> None:
        self.batch = Batch("fixture/board", RECEIPT["captured_at"], RECEIPT["export_digest"],
                           [LABEL_ADD, DEFECT])

    def test_all_selects_every_proposal_and_no_report(self) -> None:
        approved, refusals = select(self.batch, ["all"])
        self.assertEqual([action.identity for action in approved], [LABEL_ADD.identity])
        self.assertEqual(refusals, [])

    def test_approving_a_report_refuses_rather_than_dropping_it(self) -> None:
        approved, refusals = select(self.batch, [DEFECT.identity])
        self.assertEqual(approved, [])
        self.assertIn("report-only", refusals[0])

    def test_unknown_id_refuses(self) -> None:
        _, refusals = select(self.batch, ["deadbeefcafe"])
        self.assertIn("no action with that id", refusals[0])

    def test_repeated_id_is_approved_once(self) -> None:
        approved, refusals = select(self.batch, [LABEL_ADD.identity, LABEL_ADD.identity])
        self.assertEqual(len(approved), 1)
        self.assertEqual(refusals, [])

    def test_round_trip_through_the_batch_payload_preserves_identity(self) -> None:
        rebuilt = load_batch(self.batch.as_dict())
        self.assertEqual(
            [action.identity for action in rebuilt.actions],
            [action.identity for action in self.batch.actions],
        )

    def test_unknown_batch_schema_is_refused(self) -> None:
        payload = self.batch.as_dict()
        payload["batch_schema"] = "soveraeign-board-batch/v99"
        with self.assertRaises(ValueError):
            load_batch(payload)


class SurveyScopeTests(unittest.TestCase):
    """The survey judges the live board only, against the contracts in this checkout."""

    def setUp(self) -> None:
        self.catalogue = [dict(entry) for entry in labelmod.load_catalogue_entries(ROOT)]

    def test_a_closed_issue_is_surveyed_for_nothing(self) -> None:
        capture = {
            "issues": [{"number": 51, "title": "gone", "state": "CLOSED", "body": "no block", "labels": []}],
            "pulls": [], "branches": [], "labels": self.catalogue, "receipt": RECEIPT,
        }
        self.assertEqual(surveymod.build(ROOT, capture).actions, [])

    def test_a_declared_label_the_repository_lacks_is_proposed_for_creation(self) -> None:
        """The gap that made a write fail must be visible in the survey instead."""
        actions = surveymod.survey_catalogue(ROOT, self.catalogue[1:])
        self.assertEqual([action.kind for action in actions], ["LABEL_CREATE"])
        self.assertEqual(actions[0].argument, self.catalogue[0]["name"])
        self.assertEqual(dict(actions[0].extra)["color"], self.catalogue[0]["color"])

    def test_a_complete_catalogue_proposes_nothing(self) -> None:
        self.assertEqual(surveymod.survey_catalogue(ROOT, self.catalogue), [])

    def test_a_stock_label_outside_the_governed_namespace_is_ignored(self) -> None:
        live = self.catalogue + [{"name": "bug", "color": "d73a4a", "description": "d"}]
        self.assertEqual(surveymod.survey_catalogue(ROOT, live), [])

    def test_a_governed_label_the_catalogue_omits_is_reported_not_deleted(self) -> None:
        live = self.catalogue + [{"name": "type: story", "color": "E16F24", "description": "d"}]
        actions = surveymod.survey_catalogue(ROOT, live)
        self.assertEqual([action.kind for action in actions], ["CATALOGUE_UNDECLARED"])
        self.assertEqual(actions[0].disposition, "REPORT")

    def test_a_merged_branch_already_deleted_is_not_proposed_again(self) -> None:
        pulls = [{"number": 1, "state": "MERGED", "headRefName": "feat/gone", "title": "t"}]
        self.assertEqual(surveymod.survey_branches(pulls, [{"name": "main"}]), [])

    def test_stale_hours_moves_what_is_reported(self) -> None:
        pulls = [{
            "number": 9, "state": "OPEN", "headRefName": "feat/quiet", "title": "quiet",
            "isDraft": True, "updatedAt": "2026-08-23T06:00:00Z",
        }]
        now = surveymod._parse_time(RECEIPT["captured_at"])
        self.assertEqual(len(surveymod.survey_pulls(pulls, now, stale_hours=4)), 1)
        self.assertEqual(surveymod.survey_pulls(pulls, now, stale_hours=12), [])


class CaptureCompletenessTests(unittest.TestCase):
    """A partial capture must refuse, because an empty collection reads as \"nothing to do\"."""

    def _write(self, directory: Path, sidecars: dict[str, str]) -> Path:
        export = directory / "tickets.json"
        export.write_text("[]", encoding="utf-8")
        (directory / "tickets.receipt.json").write_text(json.dumps(RECEIPT), encoding="utf-8")
        for suffix, payload in sidecars.items():
            (directory / f"tickets{suffix}").write_text(payload, encoding="utf-8")
        return export

    def test_a_missing_label_catalogue_refuses_rather_than_surveying_against_none(self) -> None:
        """Every declared label looks absent against an empty catalogue; that is not a survey."""
        with tempfile.TemporaryDirectory() as raw:
            export = self._write(Path(raw), {".pulls.json": "[]", ".branches.json": "[]"})
            with self.assertRaises(SystemExit) as caught:
                board._load_capture(export)
        self.assertIn("CAPTURE_INCOMPLETE", str(caught.exception))
        self.assertIn("tickets.labels.json", str(caught.exception))

    def test_a_complete_capture_loads_every_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            export = self._write(
                Path(raw),
                {".pulls.json": "[]", ".branches.json": "[]", ".labels.json": "[]"},
            )
            capture = board._load_capture(export)
        self.assertEqual(set(capture), {"issues", "receipt", "pulls", "branches", "labels"})


class RenderTests(unittest.TestCase):
    """The surface must carry the evidence, or approving from it is approving blind."""

    def test_every_report_shows_evidence_rule_and_move(self) -> None:
        batch = Batch("fixture/board", RECEIPT["captured_at"], RECEIPT["export_digest"], [DEFECT])
        surface = rendermod.render(batch, "batch.json")
        self.assertIn("no metadata block", surface)
        self.assertIn("contracts/issue-metadata.schema.json", surface)
        self.assertIn("author one", surface)

    def test_the_proposed_table_is_addressable_by_action_id(self) -> None:
        batch = Batch("fixture/board", RECEIPT["captured_at"], RECEIPT["export_digest"], [LABEL_ADD])
        self.assertIn(LABEL_ADD.identity, rendermod.render(batch, "batch.json"))

    def test_an_empty_batch_says_so_in_both_sections(self) -> None:
        batch = Batch("fixture/board", RECEIPT["captured_at"], RECEIPT["export_digest"], [])
        surface = rendermod.render(batch, "batch.json")
        self.assertIn("PROPOSED (0)", surface)
        self.assertIn("REPORTED (0)", surface)


if __name__ == "__main__":
    unittest.main()
