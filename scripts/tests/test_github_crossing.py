"""Unit tests for the GitHub write crossing under ``adapters/github/apply.py``.

The crossing is the only module that can write to GitHub, so these tests cover the two
things that decide whether a write happens at all: the exact command it builds for each
admitted action, and the inputs it refuses instead of approximating. Nothing here
reaches the network; every case runs through ``plan`` or a dry run.
"""

from __future__ import annotations

from pathlib import Path
import importlib.util
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovboard.actions import Action  # noqa: E402


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
    evidence="no metadata block", rule="contracts/issue-metadata.schema.json",
    recommendation="author one",
)


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

    def test_label_create_carries_the_declared_colour(self) -> None:
        action = Action(
            kind="LABEL_CREATE", target="repository", argument="type: engagement",
            extra=(("color", "B60205"), ("description", "an engagement")),
            evidence="e", rule="r", recommendation="d",
        )
        command = crossing.plan(action.as_dict(), "owner/name")
        self.assertEqual(command[:4], ["gh", "label", "create", "type: engagement"])
        self.assertIn("B60205", command)

    def test_label_create_without_a_colour_is_refused(self) -> None:
        action = Action(
            kind="LABEL_CREATE", target="repository", argument="type: engagement",
            evidence="e", rule="r", recommendation="d",
        )
        with self.assertRaises(crossing.CrossingRefusal) as caught:
            crossing.plan(action.as_dict(), "owner/name")
        self.assertEqual(caught.exception.code, "MALFORMED_TARGET")

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


if __name__ == "__main__":
    unittest.main()
