"""Unit tests for the GitHub write crossing under ``adapters/github/apply.py``.

The crossing is the only module that can write to GitHub, so these tests cover the two
things that decide whether a write happens at all: the exact command it builds for each
admitted action, and the inputs it refuses instead of approximating. Network-dependent
proofs are injected; no case reaches GitHub.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch
import importlib.util
import json
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
HEAD_SHA = "a" * 40


def automatic_branch() -> dict:
    """One merge-event-shaped retirement action."""
    return {
        "id": "retire-101",
        "kind": "BRANCH_DELETE",
        "target": "feat/done",
        "argument": "feat/done",
        "evidence": "PR #101 merged this same-repository head",
        "rule": "AGENTS.md, Branch and commit strategy",
        "recommendation": "retire the merged head",
        "extra": {
            "authority_basis": crossing.AUTOMATIC_BRANCH_AUTHORITY,
            "pr_number": "101",
            "head_sha": HEAD_SHA,
            "base_ref": "main",
        },
    }


def merged_pull(**overrides) -> dict:
    """The live GitHub proof an automatic retirement expects."""
    payload = {
        "merged": True,
        "head": {"ref": "feat/done", "sha": HEAD_SHA, "repo": {"full_name": "owner/name"}},
        "base": {"ref": "main"},
    }
    payload.update(overrides)
    return payload


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
    """Nothing crosses the boundary without a proved authority basis and a receipt."""

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

    def test_automatic_retirement_revalidates_merge_and_stack_state(self) -> None:
        answers = [
            (0, json.dumps(merged_pull())),
            (0, "[]"),
        ]
        with patch.object(crossing, "_run", side_effect=answers) as run:
            receipt = crossing.execute(automatic_branch(), "owner/name", dry_run=True)
        self.assertEqual(receipt["outcome"], "PLANNED")
        self.assertIn("automatic retirement", receipt["authority"])
        self.assertEqual(run.call_count, 2)

    def test_automatic_retirement_refuses_a_changed_head_sha(self) -> None:
        changed = merged_pull()
        changed["head"] = dict(changed["head"], sha="b" * 40)
        with patch.object(crossing, "_run", return_value=(0, json.dumps(changed))):
            receipt = crossing.execute(automatic_branch(), "owner/name", dry_run=True)
        self.assertEqual(receipt["outcome"], "REFUSED")
        self.assertEqual(receipt["reason_code"], "AUTOMATION_PROOF_MISMATCH")

    def test_automatic_retirement_refuses_a_live_stacked_child(self) -> None:
        answers = [
            (0, json.dumps(merged_pull())),
            (0, json.dumps([{"number": 105}])),
        ]
        with patch.object(crossing, "_run", side_effect=answers):
            receipt = crossing.execute(automatic_branch(), "owner/name", dry_run=True)
        self.assertEqual(receipt["outcome"], "REFUSED")
        self.assertEqual(receipt["reason_code"], "STACK_BASE_LIVE")
        self.assertIn("#105", receipt["detail"])

    def test_unknown_automatic_authority_is_refused(self) -> None:
        action = automatic_branch()
        action["extra"]["authority_basis"] = "trust-me"
        receipt = crossing.execute(action, "owner/name", dry_run=True)
        self.assertEqual(receipt["outcome"], "REFUSED")
        self.assertEqual(receipt["reason_code"], "AUTHORITY_BASIS_UNKNOWN")


if __name__ == "__main__":
    unittest.main()
