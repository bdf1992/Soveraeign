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
WORKFLOWS = ROOT / ".github" / "workflows"
VERIFY_STEP = re.compile(r"run: python scripts/verify\.py(?P<rest>[^\n]*)")
OBSERVE_TARGET = re.compile(r"--observe \"\$RUNNER_TEMP/(?P<name>[\w.-]+)\"")


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


def unretained(text: str) -> list[str]:
    """Every `scripts/verify.py` step in one workflow that keeps only its exit code.

    A verify run already builds one Observation per check against
    `contracts/observation.schema.json`, carrying the addresses that check read.
    A job that runs it bare throws that away and keeps one bit, which cannot tell
    a defective change from a busy host from another session writing the tree.
    A step is retained here when it writes the records and the workflow uploads
    the exact file it wrote; writing them to a path nobody keeps is the same loss
    with more steps.
    """
    missing = []
    for step in VERIFY_STEP.finditer(text):
        target = OBSERVE_TARGET.search(step.group("rest"))
        if target is None:
            missing.append(f"{step.group(0).strip()} does not pass --observe")
            continue
        name = target.group("name")
        if "path: ${{ runner.temp }}/" + name not in text:
            missing.append(f"{name} is written and never uploaded")
    return missing


class VerificationRunsLeaveARecord(unittest.TestCase):
    def test_every_workflow_verify_step_retains_its_observations(self):
        for path in sorted(WORKFLOWS.glob("*.yml")):
            text = path.read_text(encoding="utf-8")
            self.assertEqual([], unretained(text), f"{path.name} keeps only an exit code")

    def test_a_bare_verify_step_is_refused(self):
        self.assertEqual(
            ["run: python scripts/verify.py does not pass --observe"],
            unretained("      - name: Verify\n        run: python scripts/verify.py\n"),
        )

    def test_records_written_to_a_path_nobody_uploads_are_refused(self):
        text = ('      - name: Verify\n'
                '        run: python scripts/verify.py --observe "$RUNNER_TEMP/orphan.json"\n')
        self.assertEqual(["orphan.json is written and never uploaded"], unretained(text))

    def test_the_records_survive_a_failing_run(self):
        """The red run is the one whose attribution matters, so retention is unconditional."""
        for path in sorted(WORKFLOWS.glob("*.yml")):
            text = path.read_text(encoding="utf-8")
            for step in VERIFY_STEP.finditer(text):
                target = OBSERVE_TARGET.search(step.group("rest"))
                if target is None:
                    continue
                upload = text.split("path: ${{ runner.temp }}/" + target.group("name"), 1)[0]
                retain = upload.rsplit("- name:", 1)[1]
                self.assertIn("if: always()", retain,
                              f"{path.name}: {target.group('name')} is kept only when green")


if __name__ == "__main__":
    unittest.main()
