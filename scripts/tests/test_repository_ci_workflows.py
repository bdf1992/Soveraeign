from __future__ import annotations

from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
VERIFY = ROOT / ".github" / "workflows" / "verify.yml"
QA = ROOT / ".github" / "workflows" / "qa-lanes.yml"
CONTRACT = ROOT / "contracts" / "repository-ci-evidence.json"
HEAD_REF = "ref: ${{ github.event.pull_request.head.sha }}"


class RepositoryCIWorkflowIdentity(unittest.TestCase):
    def test_verify_keeps_candidate_and_integration_as_two_jobs(self):
        text = VERIFY.read_text(encoding="utf-8")
        self.assertIn("candidate:\n", text)
        self.assertIn("repository:\n", text)
        self.assertIn("sov_ci_subject.py candidate", text)
        self.assertIn("sov_ci_subject.py integration", text)
        self.assertIn(HEAD_REF, text)
        self.assertIn("candidate-ci-subject-", text)
        self.assertIn("integration-ci-subject-", text)

    def test_protected_repository_job_remains_integration_not_candidate(self):
        text = VERIFY.read_text(encoding="utf-8")
        repository = text.split("\n  repository:\n", 1)[1]
        self.assertIn("sov_ci_subject.py integration", repository)
        self.assertNotIn("sov_ci_subject.py candidate", repository)
        self.assertNotIn(HEAD_REF, repository)

    def test_every_qa_checkout_is_exact_candidate_head(self):
        text = QA.read_text(encoding="utf-8")
        checkout_count = text.count("uses: actions/checkout@v4")
        head_count = text.count(HEAD_REF)
        self.assertGreaterEqual(checkout_count, 4)
        self.assertEqual(checkout_count, head_count)
        self.assertNotIn("sov_ci_subject.py integration", text)
        self.assertGreaterEqual(text.count("sov_ci_subject.py candidate"), 4)

    def test_contract_and_workflows_agree_on_producer_kind(self):
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        producers = contract["producer_intent"]
        self.assertEqual(producers["verify.candidate"], "CANDIDATE")
        self.assertEqual(producers["verify.repository"], "INTEGRATION")
        self.assertEqual(producers["qa-lanes.blue"], "CANDIDATE")
        self.assertEqual(producers["qa-lanes.mutation-admission"], "CANDIDATE")

    def test_no_workflow_claims_candidate_evidence_only_by_job_name(self):
        for path in (VERIFY, QA):
            text = path.read_text(encoding="utf-8")
            for match in re.finditer(r"name: .*candidate.*", text, re.IGNORECASE):
                surrounding = text[max(0, match.start() - 500):match.start() + 1200]
                if "name: candidate · repository" in surrounding:
                    self.assertIn("sov_ci_subject.py candidate", text)


if __name__ == "__main__":
    unittest.main()
