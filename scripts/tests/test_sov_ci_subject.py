from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_ci_subject  # noqa: E402


class RepositoryCISubject(unittest.TestCase):
    @staticmethod
    def git(root: Path, *args: str) -> str:
        return subprocess.run(
            ["git", *args], cwd=root, check=True, capture_output=True, text=True
        ).stdout.strip()

    def make_repo(self, parent: Path) -> tuple[Path, str, str]:
        root = parent / "repo"
        root.mkdir()
        self.git(root, "init", "-q", "-b", "main")
        self.git(root, "config", "user.email", "ci-subject@test")
        self.git(root, "config", "user.name", "CI Subject Test")
        (root / "x.txt").write_text("base\n", encoding="utf-8")
        self.git(root, "add", "x.txt")
        self.git(root, "commit", "-q", "-m", "base")
        base = self.git(root, "rev-parse", "HEAD")
        self.git(root, "checkout", "-q", "-b", "candidate")
        (root / "x.txt").write_text("candidate\n", encoding="utf-8")
        self.git(root, "commit", "-qam", "candidate")
        candidate = self.git(root, "rev-parse", "HEAD")
        return root, base, candidate

    def move_main(self, root: Path) -> str:
        self.git(root, "checkout", "-q", "main")
        (root / "base-only.txt").write_text("new base\n", encoding="utf-8")
        self.git(root, "add", "base-only.txt")
        self.git(root, "commit", "-q", "-m", "move base")
        return self.git(root, "rev-parse", "HEAD")

    def test_candidate_receipt_reads_exact_head_and_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, base, candidate = self.make_repo(Path(tmp))
            receipt = sov_ci_subject.candidate_receipt(base, candidate, root)
            self.assertEqual(receipt["evidence_kind"], "CANDIDATE")
            self.assertEqual(receipt["candidate_commit"], candidate)
            self.assertEqual(receipt["observed_commit"], candidate)
            self.assertEqual(receipt["candidate_tree"], receipt["observed_tree"])
            self.assertTrue(receipt["base_is_ancestor"])
            self.assertEqual(receipt["construction_history"], "LINEAR")
            self.assertEqual(receipt["construction_commits"], 1)

    def test_candidate_receipt_refuses_a_different_head(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, base, candidate = self.make_repo(Path(tmp))
            self.git(root, "checkout", "-q", "main")
            with self.assertRaises(sov_ci_subject.SubjectRefused) as raised:
                sov_ci_subject.candidate_receipt(base, candidate, root)
            self.assertIn("CANDIDATE_HEAD_MISMATCH", str(raised.exception))

    def test_candidate_refuses_a_target_base_it_has_not_reconciled(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, _base, candidate = self.make_repo(Path(tmp))
            current_base = self.move_main(root)
            self.git(root, "checkout", "-q", "candidate")
            with self.assertRaises(sov_ci_subject.SubjectRefused) as raised:
                sov_ci_subject.candidate_receipt(current_base, candidate, root)
            self.assertIn("CANDIDATE_BASE_NOT_RECONCILED", str(raised.exception))

    def test_rebasing_onto_current_base_earns_candidate_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, _base, _candidate = self.make_repo(Path(tmp))
            current_base = self.move_main(root)
            self.git(root, "checkout", "-q", "candidate")
            self.git(root, "rebase", "main")
            rebased = self.git(root, "rev-parse", "HEAD")
            receipt = sov_ci_subject.candidate_receipt(current_base, rebased, root)
            self.assertEqual(receipt["candidate_commit"], rebased)
            self.assertEqual(receipt["construction_history"], "LINEAR")
            self.assertTrue(receipt["base_is_ancestor"])

    def test_merging_current_base_into_topic_does_not_earn_candidate_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, _base, _candidate = self.make_repo(Path(tmp))
            current_base = self.move_main(root)
            self.git(root, "checkout", "-q", "candidate")
            self.git(root, "merge", "--no-ff", "main", "-m", "merge main into candidate")
            merged_candidate = self.git(root, "rev-parse", "HEAD")
            with self.assertRaises(sov_ci_subject.SubjectRefused) as raised:
                sov_ci_subject.candidate_receipt(current_base, merged_candidate, root)
            self.assertIn("CANDIDATE_HISTORY_NONLINEAR", str(raised.exception))

    def test_integration_receipt_requires_exact_base_then_candidate_parents(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, base, candidate = self.make_repo(Path(tmp))
            self.git(root, "checkout", "-q", "main")
            self.git(root, "merge", "--no-ff", "candidate", "-m", "integration")
            receipt = sov_ci_subject.integration_receipt(base, candidate, root)
            self.assertEqual(receipt["evidence_kind"], "INTEGRATION")
            self.assertEqual(receipt["observed_parents"], [base, candidate])
            self.assertEqual(receipt["candidate_commit"], candidate)
            self.assertNotEqual(receipt["integration_commit"], candidate)
            self.assertEqual(
                receipt["integration_tree"], receipt["candidate_tree"],
                "a no-conflict merge can have the same tree while remaining a different subject",
            )

    def test_integration_receipt_refuses_patch_or_parent_substitution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, base, candidate = self.make_repo(Path(tmp))
            self.git(root, "checkout", "-q", "main")
            self.git(root, "merge", "--no-ff", "candidate", "-m", "integration")
            with self.assertRaises(sov_ci_subject.SubjectRefused) as raised:
                sov_ci_subject.integration_receipt(base, "f" * 40, root)
            self.assertIn("INTEGRATION_PARENT_MISMATCH", str(raised.exception))

    def test_contract_keeps_candidate_and_integration_separate_even_with_equal_trees(self):
        contract = json.loads(
            (ROOT / "contracts" / "repository-ci-evidence.json").read_text(encoding="utf-8")
        )
        self.assertEqual(set(contract["evidence_kinds"]), {"CANDIDATE", "INTEGRATION"})
        self.assertEqual(contract["evidence_kinds"]["CANDIDATE"]["notation"], "CI(C)")
        self.assertEqual(contract["evidence_kinds"]["INTEGRATION"]["notation"], "CI(B,C)")
        self.assertIn(
            "candidate evidence refuses merge commits in the base..candidate construction range; reconcile by rebase before qualification",
            contract["invariants"],
        )
        self.assertIn(
            "CI(C) and CI(B,C) are separate evidence and neither substitutes for the other",
            contract["invariants"],
        )
        self.assertIn(
            "equal candidate and integration trees do not collapse their distinct commit subjects",
            contract["invariants"],
        )


if __name__ == "__main__":
    unittest.main()
