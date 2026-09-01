from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_candidate  # noqa: E402


class RepositoryCandidateLifecycle(unittest.TestCase):
    def setUp(self):
        self.contract = sov_candidate.load_contract()

    def test_declared_corpus_passes(self):
        self.assertEqual(sov_candidate.cmd_selfcheck(None), 0)

    def test_patch_equivalence_never_transfers_evidence(self):
        self.assertFalse(
            self.contract["landing_policy"]["patch_equivalence_transfers_evidence"]
        )

    def test_frozen_candidate_cannot_reconcile(self):
        result = sov_candidate.evaluate(
            self.contract, {"operation": "RECONCILE", "state": "FROZEN"}
        )
        self.assertEqual(result["code"], sov_candidate.INVALID_STATE)

    def test_land_requires_exact_evidence_subject(self):
        claim = {
            "operation": "LAND",
            "state": "FROZEN",
            "candidate_commit": "2" * 40,
            "candidate_tree": "3" * 40,
            "base_commit": "1" * 40,
            "evidence_candidate_commit": "4" * 40,
            "evidence_candidate_tree": "3" * 40,
            "evidence_base_commit": "1" * 40,
            "current_base_commit": "1" * 40,
        }
        result = sov_candidate.evaluate(self.contract, claim)
        self.assertEqual(result["code"], sov_candidate.EVIDENCE_SUBJECT_MISMATCH)


if __name__ == "__main__":
    unittest.main()
