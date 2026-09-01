from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest import mock
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovkernel import authority  # noqa: E402
from sovland import candidates, repo, tree  # noqa: E402


class CandidateEffects(unittest.TestCase):
    def make_repo(self, parent: Path) -> Path:
        root = parent / "repo"
        root.mkdir()

        def git(*args):
            return subprocess.run(["git", *args], cwd=root, check=True,
                                  capture_output=True, text=True).stdout.strip()

        git("init", "-q", "-b", "main")
        git("config", "user.email", "candidate@test")
        git("config", "user.name", "Candidate Test")
        (root / "x.py").write_text("base\n", encoding="utf-8")
        git("add", "x.py")
        git("commit", "-q", "-m", "base")
        git("checkout", "-q", "-b", "work")
        return root

    @staticmethod
    def permitted():
        return {
            "verdict": authority.PERMITTED,
            "code": None,
            "detail": "covered",
            "grant_id": "grant:test",
            "considered": [],
        }

    def freeze_args(self):
        return SimpleNamespace(
            path=["x.py"], target="main", actor="sov", spend=1,
            skip_checks=False, message="feat: freeze candidate",
            concern="test:candidate", output=None,
        )

    def freeze(self, root: Path) -> dict:
        (root / "x.py").write_text("candidate\n", encoding="utf-8")
        with (
            mock.patch.object(repo, "ROOT", root),
            mock.patch.object(tree, "_held_elsewhere", return_value=[]),
            mock.patch.object(tree, "gather_checks",
                              return_value=({"verify": "PASS", "lint": "PASS"}, {})),
            mock.patch.object(authority, "evaluate", return_value=self.permitted()),
        ):
            candidate, _result, _reading = candidates.freeze(self.freeze_args(), [])
        return candidate

    @staticmethod
    def observation(candidate: dict) -> dict:
        return {
            "observer_id": "witness-1",
            "contributed_to_build": False,
            "verdict": "CONFIRMED",
            "candidate_commit": candidate["candidate_commit"],
            "candidate_tree": candidate["candidate_tree"],
            "base_commit": candidate["base_commit"],
        }

    def test_freeze_commits_exact_candidate_after_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_repo(Path(tmp))
            (root / "x.py").write_text("candidate\n", encoding="utf-8")
            base = subprocess.run(["git", "rev-parse", "main"], cwd=root,
                                  check=True, capture_output=True, text=True).stdout.strip()
            with (
                mock.patch.object(repo, "ROOT", root),
                mock.patch.object(tree, "_held_elsewhere", return_value=[]),
                mock.patch.object(tree, "gather_checks",
                                  return_value=({"verify": "PASS", "lint": "PASS"}, {})),
                mock.patch.object(authority, "evaluate", return_value=self.permitted()),
            ):
                candidate, result, _reading = candidates.freeze(self.freeze_args(), [])
                head = repo.head_commit("work")
                commit_tree = repo.commit_tree(head)
                candidate_file = root / candidate["candidate_file"]

            self.assertEqual(result["verdict"], authority.PERMITTED)
            self.assertEqual(candidate["base_commit"], base)
            self.assertEqual(candidate["candidate_commit"], head)
            self.assertEqual(candidate["candidate_tree"], commit_tree)
            self.assertEqual(candidate["state"], "FROZEN")
            self.assertTrue(candidate_file.exists())

    def test_land_candidate_preserves_frozen_sha_as_merge_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            root = self.make_repo(parent)
            candidate = self.freeze(root)
            candidate_path = root / candidate["candidate_file"]
            observation_path = parent / "observation.json"
            observation_path.write_text(
                json.dumps(self.observation(candidate)), encoding="utf-8"
            )
            args = SimpleNamespace(
                candidate=str(candidate_path), observation=str(observation_path),
                target="main", actor="sov", spend=1,
                message="feat: settle candidate",
            )
            with (
                mock.patch.object(repo, "ROOT", root),
                mock.patch.object(authority, "evaluate", return_value=self.permitted()),
            ):
                landed, result, merge_commit = candidates.land(args, [])

            parents = subprocess.run(
                ["git", "show", "-s", "--format=%P", merge_commit], cwd=root,
                check=True, capture_output=True, text=True,
            ).stdout.strip().split()
            main = subprocess.run(["git", "rev-parse", "main"], cwd=root,
                                  check=True, capture_output=True, text=True).stdout.strip()
            self.assertEqual(result["verdict"], authority.PERMITTED)
            self.assertEqual(main, merge_commit)
            self.assertEqual(parents[1], landed["candidate_commit"])

    def test_land_resolves_observation_relative_to_repository_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_repo(Path(tmp))
            candidate = self.freeze(root)
            observation_path = root / ".local" / "observation.json"
            observation_path.parent.mkdir(parents=True, exist_ok=True)
            observation_path.write_text(
                json.dumps(self.observation(candidate)), encoding="utf-8"
            )
            args = SimpleNamespace(
                candidate=candidate["candidate_file"],
                observation=".local/observation.json",
                target="main", actor="sov", spend=1,
                message="feat: settle relative evidence",
            )
            with (
                mock.patch.object(repo, "ROOT", root),
                mock.patch.object(authority, "evaluate", return_value=self.permitted()),
            ):
                _candidate, result, _merge_commit = candidates.land(args, [])
            self.assertEqual(result["verdict"], authority.PERMITTED)

    def test_land_refuses_a_target_other_than_the_frozen_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_repo(Path(tmp))
            candidate = self.freeze(root)
            args = SimpleNamespace(
                candidate=candidate["candidate_file"], observation="unused.json",
                target="release", actor="sov", spend=1, message="wrong target",
            )
            with mock.patch.object(repo, "ROOT", root):
                with self.assertRaises(candidates.CandidateRefused) as raised:
                    candidates.land(args, [])
            self.assertIn("candidate target is 'main'", str(raised.exception))

    def test_land_refuses_evidence_for_another_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            root = self.make_repo(parent)
            candidate = self.freeze(root)
            observation_path = parent / "wrong-observation.json"
            wrong = self.observation(candidate)
            wrong["candidate_commit"] = "f" * 40
            observation_path.write_text(json.dumps(wrong), encoding="utf-8")
            args = SimpleNamespace(
                candidate=str(root / candidate["candidate_file"]),
                observation=str(observation_path), target="main",
                actor="sov", spend=1, message="should refuse",
            )
            with mock.patch.object(repo, "ROOT", root):
                with self.assertRaises(candidates.CandidateRefused) as raised:
                    candidates.land(args, [])
            self.assertIn("EVIDENCE_SUBJECT_MISMATCH", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
