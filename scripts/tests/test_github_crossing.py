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
import tempfile
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


def merged_pull(branch: str = "feat/done", base: str = "main", **overrides) -> dict:
    """The live GitHub proof an automatic retirement expects."""
    payload = {
        "merged": True,
        "head": {"ref": branch, "sha": HEAD_SHA, "repo": {"full_name": "owner/name"}},
        "base": {"ref": base},
    }
    payload.update(overrides)
    return payload


def repository(default: str = "main") -> dict:
    return {"default_branch": default}


def live_ref(branch: str = "feat/done", sha: str = HEAD_SHA) -> dict:
    return {"ref": f"refs/heads/{branch}", "object": {"sha": sha}}


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

    def test_automatic_retirement_revalidates_merge_ref_and_stack_state(self) -> None:
        answers = [
            (0, json.dumps(merged_pull())),
            (0, json.dumps(repository())),
            (0, json.dumps(live_ref())),
            (0, "[]"),
        ]
        with patch.object(crossing, "_run", side_effect=answers) as run:
            receipt = crossing.execute(automatic_branch(), "owner/name", dry_run=True)
        self.assertEqual(receipt["outcome"], "PLANNED")
        self.assertIn("automatic retirement", receipt["authority"])
        self.assertEqual(run.call_count, 4)

    def test_automatic_retirement_refuses_a_changed_pr_head_sha(self) -> None:
        changed = merged_pull()
        changed["head"] = dict(changed["head"], sha="b" * 40)
        with patch.object(crossing, "_run", return_value=(0, json.dumps(changed))):
            receipt = crossing.execute(automatic_branch(), "owner/name", dry_run=True)
        self.assertEqual(receipt["outcome"], "REFUSED")
        self.assertEqual(receipt["reason_code"], "AUTOMATION_PROOF_MISMATCH")

    def test_automatic_retirement_refuses_a_reused_branch_with_new_commits(self) -> None:
        answers = [
            (0, json.dumps(merged_pull())),
            (0, json.dumps(repository())),
            (0, json.dumps(live_ref(sha="b" * 40))),
        ]
        with patch.object(crossing, "_run", side_effect=answers):
            receipt = crossing.execute(automatic_branch(), "owner/name", dry_run=True)
        self.assertEqual(receipt["outcome"], "REFUSED")
        self.assertEqual(receipt["reason_code"], "BRANCH_HEAD_MOVED")
        self.assertIn("no longer points", receipt["detail"])

    def test_automatic_retirement_never_deletes_the_default_branch(self) -> None:
        action = automatic_branch()
        action["target"] = "main"
        action["argument"] = "main"
        action["extra"]["base_ref"] = "release"
        answers = [
            (0, json.dumps(merged_pull(branch="main", base="release"))),
            (0, json.dumps(repository(default="main"))),
        ]
        with patch.object(crossing, "_run", side_effect=answers):
            receipt = crossing.execute(action, "owner/name", dry_run=True)
        self.assertEqual(receipt["outcome"], "REFUSED")
        self.assertEqual(receipt["reason_code"], "PROTECTED_BRANCH")

    def test_automatic_retirement_refuses_a_live_stacked_child(self) -> None:
        answers = [
            (0, json.dumps(merged_pull())),
            (0, json.dumps(repository())),
            (0, json.dumps(live_ref())),
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



VALID_BODY = """```yaml
issue_schema: soveraeign-ticket/v1
tags:
  - "kind:chore"
  - "village:ground-and-evidence"
  - "horizon:now"
kind: chore
chore_id: CHORE-FIXTURE
path: charting/experiments/qa.skill.json
village: ground-and-evidence
village_issue: "#4"
parent: "#40"
standing: OPEN
horizon: NOW
authority: Bdo/phase-gate
effect_class: RECORD_LOCAL
evidence_pointer: charting/experiments/qa.skill.json
last_observed_at: null
walker_receipt: PENDING
demotion_pointer: "#demotion-pointer"
dependency_channels: [topology]
```

# A chore

Prose.
"""


def body_file(text: str) -> str:
    """Write a throwaway replacement body and return its path."""
    directory = Path(tempfile.mkdtemp())
    path = directory / "body.md"
    path.write_text(text, encoding="utf-8", newline="\n")
    return str(path)


def body_write(argument: str) -> dict:
    """One owner-directed body write, shaped as the crossing expects it."""
    return {
        "id": "body-52",
        "kind": "BODY_SET",
        "target": "#52",
        "argument": argument,
        "evidence": "the block drifted from the repository",
        "rule": "decisions/0067-issue-body-write-scope.md",
        "recommendation": "write the corrected block",
        "extra": {"authority_basis": crossing.BODY_WRITE_AUTHORITY},
    }


class BodyWriteTests(unittest.TestCase):
    """A body write validates what it will land and records what it replaces."""

    def test_it_writes_through_a_file_never_an_argv_body(self) -> None:
        command = crossing.plan(body_write(body_file(VALID_BODY)), "owner/name")
        self.assertEqual(command[:5], ["gh", "issue", "edit", "52", "--repo"])
        self.assertIn("--body-file", command)
        self.assertNotIn("--body", command)

    def test_a_valid_block_records_the_prior_body_and_both_digests(self) -> None:
        path = body_file(VALID_BODY)
        with patch.object(crossing, "_run", return_value=(0, json.dumps({"body": "before"}))):
            receipt = crossing.execute(body_write(path), "owner/name", dry_run=True)
        self.assertEqual(receipt["outcome"], "PLANNED")
        self.assertIn("prior_body_snapshot", receipt)
        self.assertTrue(receipt["prior_body_digest"].startswith("sha256:"))
        self.assertNotEqual(receipt["prior_body_digest"], receipt["replacement_digest"])
        snapshot = ROOT / receipt["prior_body_snapshot"]
        self.assertEqual(snapshot.read_text(encoding="utf-8"), "before")

    def test_a_block_the_contract_refuses_never_reaches_the_boundary(self) -> None:
        broken = VALID_BODY.replace("chore_id: CHORE-FIXTURE\n", "")
        with patch.object(crossing, "_run") as run:
            receipt = crossing.execute(body_write(body_file(broken)), "owner/name", dry_run=True)
        self.assertEqual(receipt["outcome"], "REFUSED")
        self.assertEqual(receipt["reason_code"], "BODY_BLOCK_REFUSED")
        run.assert_not_called()

    def test_an_empty_replacement_is_refused_rather_than_blanking_a_ticket(self) -> None:
        receipt = crossing.execute(body_write(body_file("   \n")), "owner/name", dry_run=True)
        self.assertEqual(receipt["reason_code"], "BODY_SOURCE_EMPTY")

    def test_a_missing_source_is_refused(self) -> None:
        receipt = crossing.execute(body_write("no/such/body.md"), "owner/name", dry_run=True)
        self.assertEqual(receipt["reason_code"], "BODY_SOURCE_MISSING")

    def test_a_body_write_may_not_ride_the_unproved_label_approval(self) -> None:
        """The default basis proves nothing; a body write must name its own."""
        action = body_write(body_file(VALID_BODY))
        action.pop("extra")
        receipt = crossing.execute(action, "owner/name", dry_run=True)
        self.assertEqual(receipt["reason_code"], "AUTHORITY_BASIS_UNKNOWN")

    def test_the_branch_proof_will_not_serve_a_body_write(self) -> None:
        action = body_write(body_file(VALID_BODY))
        action["extra"] = {"authority_basis": crossing.AUTOMATIC_BRANCH_AUTHORITY}
        receipt = crossing.execute(action, "owner/name", dry_run=True)
        self.assertEqual(receipt["reason_code"], "AUTOMATION_NOT_ADMITTED")

class CommentTests(unittest.TestCase):
    """A comment appends through a file and is the one admitted write with no inverse."""

    def _action(self, argument: str) -> dict:
        return {
            "id": "comment-8", "kind": "COMMENT_ADD", "target": "#8", "argument": argument,
            "evidence": "the standing moved", "rule": "decisions/0067-issue-body-write-scope.md",
            "recommendation": "record what moved it",
        }

    def test_it_comments_rather_than_replacing_the_body(self) -> None:
        command = crossing.plan(self._action(body_file("moved to built")), "owner/name")
        self.assertEqual(command[:4], ["gh", "issue", "comment", "8"])
        self.assertIn("--body-file", command)
        self.assertNotIn("edit", command)

    def test_a_missing_comment_file_is_refused(self) -> None:
        receipt = crossing.execute(self._action("no/such/comment.md"), "owner/name", dry_run=True)
        self.assertEqual(receipt["reason_code"], "BODY_SOURCE_MISSING")

    def test_a_comment_needs_no_proof_because_it_replaces_nothing(self) -> None:
        with patch.object(crossing, "_run") as run:
            receipt = crossing.execute(
                self._action(body_file("moved to built")), "owner/name", dry_run=True
            )
        self.assertEqual(receipt["outcome"], "PLANNED")
        self.assertNotIn("prior_body_snapshot", receipt)
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
