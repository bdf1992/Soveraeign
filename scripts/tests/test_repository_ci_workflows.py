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
OBSERVE_TARGET = re.compile(
    r"--observe\s+(?:\"\$RUNNER_TEMP/(?P<quoted>[^\"]+)\"|\$RUNNER_TEMP/(?P<bare>\S+))")
CONDITION = re.compile(r"^\s+if:\s*(?P<expr>.+?)\s*$", re.M)
# A step that runs whenever the job reached it, however the author spelled it.
# `always()` also runs on cancellation; `!cancelled()` does not, which is why the
# workflows use the latter - a cancelled matrix leg has no records to keep and
# should not be reported as a job that lost them.
UNCONDITIONAL = frozenset({"always()", "${{ always() }}",
                          "!cancelled()", "${{ !cancelled() }}"})


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


def steps_of(block: list[str]) -> list[str]:
    """The step blocks of one job, split on the dash indent its own `steps:` uses."""
    try:
        start = next(i for i, line in enumerate(block) if line.rstrip().endswith("steps:"))
    except StopIteration:
        return []
    marks = [i for i in range(start + 1, len(block)) if re.match(r"^ +- ", block[i])]
    if not marks:
        return []
    depth = len(block[marks[0]]) - len(block[marks[0]].lstrip())
    marks = [i for i in marks if len(block[i]) - len(block[i].lstrip()) == depth]
    return ["\n".join(block[a:b]) for a, b in zip(marks, marks[1:] + [len(block)])]


def jobs_of(text: str) -> dict[str, list[str]]:
    """Split one workflow into job name -> step blocks, without a YAML parser.

    PyYAML is not in the standard library and CI installs a bare interpreter, so
    reading these files textually is a constraint rather than a shortcut. This
    reader knows the one shape a workflow has: jobs at a fixed indent under
    `jobs:`, a `steps:` list in each, steps beginning with a dash at a fixed
    deeper indent. A job it cannot split yields no steps, so an unreadable
    workflow reports nothing rather than passing quietly - which is why the
    caller also asserts that the workflows it reads do contain verify steps.
    """
    lines = text.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.rstrip() == "jobs:")
    except StopIteration:
        return {}
    body = []
    for line in lines[start + 1:]:
        if line.strip() and not line.startswith(" ") and not line.startswith("#"):
            break
        body.append(line)
    heads = [i for i, line in enumerate(body)
             if re.match(r"^ {2}\S", line) and line.rstrip().endswith(":")]
    jobs = {}
    for position, head in enumerate(heads):
        end = heads[position + 1] if position + 1 < len(heads) else len(body)
        jobs[body[head].strip().rstrip(":")] = steps_of(body[head:end])
    return jobs


def unretained(text: str) -> list[str]:
    """Every `scripts/verify.py` step in one workflow that keeps only its exit code.

    A verify run already builds one Observation per check against
    `contracts/observation.schema.json`, carrying the addresses that check read.
    A job that runs it and keeps one bit cannot tell a defective change from a
    busy host from another session writing the tree. A step is retained when it
    writes the records and the job that wrote them uploads that exact file,
    unconditionally, refusing if the file is absent.

    Read per step and per job rather than per line. The first version of this
    guard matched `run: python scripts/verify.py` and an independent witness
    defeated it eight ways in one sitting: a folded `run: >-` scalar (already the
    idiom in these files), a literal `run: |` block, `python3`, a `bash -lc`
    wrapper, a `cd && ` prefix, a `.yaml` extension the glob missed, an upload
    from a different job whose `$RUNNER_TEMP` is a different machine, and a
    retention step with no `- name:` line. Each of those is a legal way to write
    the thing this guard exists to require, so each is a case below.
    """
    missing = []
    for job, steps in jobs_of(text).items():
        uploads = [step for step in steps if "upload-artifact@" in step]
        for step in steps:
            if "scripts/verify.py" not in step:
                continue
            found = OBSERVE_TARGET.search(step)
            if found is None:
                missing.append(f"{job}: a verify step does not pass --observe")
                continue
            name = found.group("quoted") or found.group("bare")
            keepers = [one for one in uploads if "runner.temp }}/" + name in one]
            if not keepers:
                missing.append(f"{job}: {name} is written and no step in that job uploads it")
                continue
            for keeper in keepers:
                condition = CONDITION.search(keeper)
                if condition is None or condition.group("expr") not in UNCONDITIONAL:
                    missing.append(f"{job}: {name} is kept only when the job goes well")
                if "if-no-files-found: error" not in keeper:
                    missing.append(f"{job}: {name} may go missing without refusing")
    return missing


def workflow(steps: str) -> str:
    """A miniature workflow carrying `steps`, for grading `unretained` on one shape."""
    return ("name: probe\n\njobs:\n  only:\n    runs-on: ubuntu-latest\n"
            "    steps:\n" + steps)


RETAIN = ('      - name: Retain\n'
          '        if: ${{ !cancelled() }}\n'
          '        uses: actions/upload-artifact@v4\n'
          '        with:\n'
          '          name: probe\n'
          '          path: ${{ runner.temp }}/obs.json\n'
          '          if-no-files-found: error\n')


class VerificationRunsLeaveARecord(unittest.TestCase):
    def workflows(self):
        found = sorted(WORKFLOWS.glob("*.yml")) + sorted(WORKFLOWS.glob("*.yaml"))
        self.assertTrue(found, "no workflows found to grade")
        return found

    def test_every_workflow_verify_step_retains_its_observations(self):
        graded = 0
        for path in self.workflows():
            text = path.read_text(encoding="utf-8")
            self.assertEqual([], unretained(text), f"{path.name} keeps only an exit code")
            graded += sum("scripts/verify.py" in step
                          for steps in jobs_of(text).values() for step in steps)
        # The reader returning nothing would pass every assertion above. Four verify
        # steps exist across these workflows; a change that drops one is a change to
        # this line, not a silently smaller sweep.
        self.assertEqual(4, graded, "the reader found a different number of verify steps")

    def test_a_bare_verify_step_is_refused(self):
        self.assertEqual(
            ["only: a verify step does not pass --observe"],
            unretained(workflow("      - run: python scripts/verify.py\n")),
        )

    def test_records_written_to_a_path_nobody_uploads_are_refused(self):
        self.assertEqual(
            ["only: obs.json is written and no step in that job uploads it"],
            unretained(workflow(
                '      - run: python scripts/verify.py --observe "$RUNNER_TEMP/obs.json"\n')),
        )

    def test_a_folded_run_block_is_read(self):
        """`run: >-` is the idiom these workflows already use, so it must not hide."""
        bare = workflow("      - name: Verify\n"
                        "        run: >-\n"
                        "          python scripts/verify.py\n")
        self.assertEqual(["only: a verify step does not pass --observe"], unretained(bare))
        kept = workflow("      - name: Verify\n"
                        "        run: >-\n"
                        "          python scripts/verify.py\n"
                        '          --observe "$RUNNER_TEMP/obs.json"\n' + RETAIN)
        self.assertEqual([], unretained(kept))

    def test_a_literal_run_block_is_read(self):
        self.assertEqual(
            ["only: a verify step does not pass --observe"],
            unretained(workflow("      - name: Verify\n"
                                "        run: |\n"
                                "          python scripts/verify.py\n")),
        )

    def test_a_wrapped_or_renamed_interpreter_is_read(self):
        for line in ('        run: python3 scripts/verify.py\n',
                     '        run: bash -lc "python scripts/verify.py"\n',
                     '        run: cd "$GITHUB_WORKSPACE" && python scripts/verify.py\n'):
            with self.subTest(line=line.strip()):
                self.assertEqual(
                    ["only: a verify step does not pass --observe"],
                    unretained(workflow("      - name: Verify\n" + line)),
                )

    def test_an_upload_from_another_job_does_not_count(self):
        """A different job is a different runner, so its $RUNNER_TEMP is another disk."""
        text = (workflow('      - run: python scripts/verify.py --observe "$RUNNER_TEMP/obs.json"\n')
                + "  elsewhere:\n    runs-on: ubuntu-latest\n    steps:\n" + RETAIN)
        self.assertEqual(
            ["only: obs.json is written and no step in that job uploads it"], unretained(text))

    def test_a_retention_step_without_a_name_is_still_graded(self):
        text = workflow('      - run: python scripts/verify.py --observe "$RUNNER_TEMP/obs.json"\n'
                        '      - if: success()\n'
                        '        uses: actions/upload-artifact@v4\n'
                        '        with:\n'
                        '          path: ${{ runner.temp }}/obs.json\n'
                        '          if-no-files-found: error\n')
        self.assertEqual(["only: obs.json is kept only when the job goes well"], unretained(text))

    def test_a_narrowed_always_is_refused(self):
        """`always() && <anything>` reads as unconditional and is not."""
        text = workflow('      - run: python scripts/verify.py --observe "$RUNNER_TEMP/obs.json"\n'
                        + RETAIN.replace("${{ !cancelled() }}",
                                         "always() && github.event_name == 'push'"))
        self.assertEqual(["only: obs.json is kept only when the job goes well"], unretained(text))

    def test_a_missing_record_must_refuse_rather_than_warn(self):
        text = workflow('      - run: python scripts/verify.py --observe "$RUNNER_TEMP/obs.json"\n'
                        + RETAIN.replace("if-no-files-found: error", "if-no-files-found: warn"))
        self.assertEqual(["only: obs.json may go missing without refusing"], unretained(text))

    def test_a_templated_observe_path_is_accepted(self):
        """The guard must not refuse a legal matrix-scoped filename."""
        name = "${{ matrix.python-version }}-obs.json"
        text = workflow(f'      - run: python scripts/verify.py --observe "$RUNNER_TEMP/{name}"\n'
                        + RETAIN.replace("runner.temp }}/obs.json", "runner.temp }}/" + name))
        self.assertEqual([], unretained(text))


if __name__ == "__main__":
    unittest.main()
