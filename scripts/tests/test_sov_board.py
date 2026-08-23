"""Unit tests for the board management mechanics and the GitHub write crossing.

The semantic cases live in ``conformance/fixtures/board/survey-cases.json`` and run
through ``scripts/sov_board.py selfcheck``. These tests cover the local mechanics that
decide whether an approval can turn into a write: which kinds are approvable, which
commands the crossing builds, and which inputs it refuses instead of approximating.
"""

from __future__ import annotations

from pathlib import Path
import importlib.util
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovboard import render as rendermod  # noqa: E402
from sovboard import survey as surveymod  # noqa: E402
from sovboard.actions import Action, Batch, load_batch, select  # noqa: E402


def _load_crossing():
    """Load the write crossing by path; ``adapters/`` is not an importable package."""
    spec = importlib.util.spec_from_file_location(
        "github_apply", ROOT / "adapters" / "github" / "apply.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


crossing = _load_crossing()

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


class CrossingPlanTests(unittest.TestCase):
    """The crossing builds the exact command it will run, or refuses to build one."""

    def test_label_add_and_remove_use_the_matching_flag(self) -> None:
        add = crossing.plan(LABEL_ADD.as_dict(), "owner/name")
        self.assertEqual(add[:5], ["gh", "issue", "edit", "40", "--repo"])
        self.assertIn("--add-label", add)
        removal = Action(
            kind="LABEL_REMOVE", target="#40", argument="type: bit",
            evidence="e", rule="r", recommendation="d",
        )
        self.assertIn("--remove-label", crossing.plan(removal.as_dict(), "owner/name"))

    def test_branch_delete_targets_the_ref_endpoint(self) -> None:
        action = Action(
            kind="BRANCH_DELETE", target="feat/done", argument="feat/done",
            evidence="e", rule="r", recommendation="d",
        )
        command = crossing.plan(action.as_dict(), "owner/name")
        self.assertEqual(command[-1], "repos/owner/name/git/refs/heads/feat/done")
        self.assertIn("DELETE", command)

    def test_report_only_kind_is_not_admitted_by_the_crossing(self) -> None:
        with self.assertRaises(crossing.CrossingRefusal) as caught:
            crossing.plan(DEFECT.as_dict(), "owner/name")
        self.assertEqual(caught.exception.code, "ACTION_NOT_ADMITTED")

    def test_non_numeric_issue_target_is_refused(self) -> None:
        action = dict(LABEL_ADD.as_dict(), target="#not-a-number")
        with self.assertRaises(crossing.CrossingRefusal) as caught:
            crossing.plan(action, "owner/name")
        self.assertEqual(caught.exception.code, "MALFORMED_TARGET")

    def test_a_ref_shaped_branch_argument_is_refused(self) -> None:
        action = {
            "kind": "BRANCH_DELETE", "target": "x", "argument": "refs/heads/main",
            "id": "x", "evidence": "e", "rule": "r", "recommendation": "d",
        }
        with self.assertRaises(crossing.CrossingRefusal):
            crossing.plan(action, "owner/name")


class CrossingExecuteTests(unittest.TestCase):
    """Nothing crosses the boundary without an approval, and every attempt leaves a receipt."""

    def test_dry_run_plans_without_crossing(self) -> None:
        receipt = crossing.execute(LABEL_ADD.as_dict(), "owner/name", dry_run=True)
        self.assertEqual(receipt["outcome"], "PLANNED")
        self.assertEqual(receipt["effect_class"], "EXTERNAL_WORLD")
        self.assertIn("gh issue edit 40", receipt["command"])

    def test_an_empty_approval_refuses_rather_than_succeeding_vacuously(self) -> None:
        with self.assertRaises(crossing.CrossingRefusal) as caught:
            crossing.apply_all([], "owner/name", dry_run=True)
        self.assertEqual(caught.exception.code, "NO_APPROVAL")

    def test_an_unadmitted_action_yields_a_refusal_receipt_not_an_exception(self) -> None:
        receipts = crossing.apply_all([DEFECT.as_dict()], "owner/name", dry_run=True)
        self.assertEqual(receipts[0]["outcome"], "REFUSED")
        self.assertEqual(receipts[0]["reason_code"], "ACTION_NOT_ADMITTED")

    def test_one_refusal_does_not_hide_the_actions_after_it(self) -> None:
        receipts = crossing.apply_all(
            [DEFECT.as_dict(), LABEL_ADD.as_dict()], "owner/name", dry_run=True
        )
        self.assertEqual([entry["outcome"] for entry in receipts], ["REFUSED", "PLANNED"])


class SurveyScopeTests(unittest.TestCase):
    """The survey judges the live board only, against the contracts in this checkout."""

    def test_a_closed_issue_is_surveyed_for_nothing(self) -> None:
        capture = {
            "issues": [{"number": 51, "title": "gone", "state": "CLOSED", "body": "no block", "labels": []}],
            "pulls": [], "branches": [], "receipt": RECEIPT,
        }
        self.assertEqual(surveymod.build(ROOT, capture).actions, [])

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
