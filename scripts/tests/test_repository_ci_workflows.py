"""Cases for the CI evidence subjects, and for the guard that keeps their records.

The reader these cases exercise lives in `scripts/sovverify/workflows.py`, not
here. A third independent witness pointed out that a hundred lines of hand-rolled
YAML reading had been sitting under `scripts/tests/`, the one tree `scripts/lint.py`
is written not to grade, so the guard now lives where the size and hygiene checks
can see it and this module holds only its cases.
"""

from __future__ import annotations

from pathlib import Path
import json
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sovverify.workflows import graded_steps, jobs_of, unretained  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
VERIFY = ROOT / ".github" / "workflows" / "verify.yml"
QA = ROOT / ".github" / "workflows" / "qa-lanes.yml"
CONTRACT = ROOT / "contracts" / "repository-ci-evidence.json"
HEAD_REF = "ref: ${{ github.event.pull_request.head.sha }}"
# `.github/actions` is swept as well. A composite action is written with `runs:`
# rather than `jobs:`, so the reader finds no jobs in one; naming the verifier there
# refuses rather than passing, which is the point.
SWEPT = (ROOT / ".github" / "workflows", ROOT / ".github" / "actions")


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


def workflow(steps: str, head: str = "  only:\n") -> str:
    """A miniature workflow carrying `steps`, for grading `unretained` on one shape."""
    return "name: probe\n\njobs:\n" + head + "    runs-on: ubuntu-latest\n    steps:\n" + steps


VERIFY_STEP = '      - run: python scripts/verify.py --observe "$RUNNER_TEMP/obs.json"\n'
RETAIN = ('      - name: Retain\n'
          '        if: ${{ !cancelled() }}\n'
          '        uses: actions/upload-artifact@v4\n'
          '        with:\n'
          '          name: probe\n'
          '          path: ${{ runner.temp }}/obs.json\n'
          '          if-no-files-found: error\n')
NO_OBSERVE = ["only: a verify step does not pass --observe"]
NOT_UPLOADED = ["only: obs.json is written and no step in that job uploads it"]
ONLY_WHEN_WELL = ["only: obs.json is kept only when the job goes well"]
MAY_GO_MISSING = ["only: obs.json may go missing without refusing"]
NOBODY_LISTENS = ["only: obs.json refuses an absent file and nothing listens"]
THROUGH_SHELL = ["only: a verify step runs through shell this cannot read"]
UNSEEN_JOB = "shadow: runs the verifier in a shape the reader cannot see"
UNSEEN_FILE = "this file runs the verifier in a shape the reader cannot see"


class VerificationRunsLeaveARecord(unittest.TestCase):
    def workflows(self):
        found = [path for root in SWEPT if root.is_dir()
                 for path in sorted(root.rglob("*.yml")) + sorted(root.rglob("*.yaml"))]
        self.assertTrue(found, "no workflow files found to grade")
        return found

    def test_the_shape_every_refusal_below_mutates_is_itself_clean(self):
        """Each case below deletes one property from this. It must pass intact, or
        those cases would prove nothing but that the probe was already broken."""
        self.assertEqual([], unretained(workflow(VERIFY_STEP + RETAIN)))

    def test_every_workflow_verify_step_retains_its_observations(self):
        for path in self.workflows():
            self.assertEqual([], unretained(path.read_text(encoding="utf-8")),
                             f"{path.name} keeps only an exit code")

    def test_the_reader_still_reaches_all_four_live_steps(self):
        """A count, and only a count. A witness showed that a reader returning each
        job as one opaque step hits this number exactly, so this is an anchor against
        a step quietly disappearing, never evidence that the reader can see."""
        self.assertEqual(4, sum(graded_steps(path.read_text(encoding="utf-8"))
                                for path in self.workflows()))

    def test_each_property_is_load_bearing_on_each_real_step(self):
        """Grade the four live steps, not only the miniature. Deleting any one of
        the three properties from any one of them has to refuse."""
        mutations = (("--observe", "--no-observe"),
                     ("if: ${{ !cancelled() }}", "if: success()"),
                     ("if-no-files-found: error", "if-no-files-found: warn"))
        tried = 0
        for path in self.workflows():
            original = path.read_text(encoding="utf-8")
            for _, steps in jobs_of(original).values():
                for step in steps:
                    if "-observations.json" not in step:
                        continue
                    for was, now in mutations:
                        if was not in step:
                            continue
                        tried += 1
                        broken = original.replace(step, step.replace(was, now, 1), 1)
                        with self.subTest(file=path.name, removed=was):
                            self.assertNotEqual([], unretained(broken))
        # Four verify steps and four retention steps: one mutation for each verify
        # step, two for each retention step.
        self.assertEqual(12, tried, "a live step was not mutated")

    def test_a_bare_verify_step_is_refused(self):
        self.assertEqual(NO_OBSERVE, unretained(workflow(
            "      - run: python scripts/verify.py\n")))

    def test_records_written_to_a_path_nobody_uploads_are_refused(self):
        self.assertEqual(NOT_UPLOADED, unretained(workflow(VERIFY_STEP)))

    def test_a_folded_run_block_is_read(self):
        """`run: >-` is the idiom these workflows already use, so it must not hide."""
        self.assertEqual(NO_OBSERVE, unretained(workflow(
            "      - name: Verify\n        run: >-\n          python scripts/verify.py\n")))
        self.assertEqual([], unretained(workflow(
            "      - name: Verify\n"
            "        run: >-\n"
            "          python scripts/verify.py\n"
            '          --observe "$RUNNER_TEMP/obs.json"\n' + RETAIN)))

    def test_a_literal_run_block_is_read(self):
        self.assertEqual(NO_OBSERVE, unretained(workflow(
            "      - name: Verify\n        run: |\n          python scripts/verify.py\n")))

    def test_a_wrapped_or_renamed_interpreter_is_read(self):
        for line in ('        run: python3 scripts/verify.py\n',
                     '        run: bash -lc "python scripts/verify.py"\n',
                     '        run: cd "$GITHUB_WORKSPACE" && python scripts/verify.py\n'):
            with self.subTest(line=line.strip()):
                self.assertEqual(NO_OBSERVE,
                                 unretained(workflow("      - name: Verify\n" + line)))

    def test_a_heredoc_refuses_rather_than_reading_its_body_as_arguments(self):
        """`--observe` inside a heredoc is not an argument, and nothing parses shell.
        A neighbouring line can also fabricate the named file, so `error` would not
        catch it at runtime either. The only safe reading is to refuse."""
        self.assertEqual(THROUGH_SHELL, unretained(workflow(
            "      - run: |\n"
            "          cat <<EOF\n"
            '          --observe "$RUNNER_TEMP/obs.json"\n'
            "          EOF\n"
            "          python scripts/verify.py\n" + RETAIN)))

    def test_an_upload_from_another_job_does_not_count(self):
        """A different job is a different runner, so its $RUNNER_TEMP is another disk."""
        self.assertEqual(NOT_UPLOADED, unretained(
            workflow(VERIFY_STEP) + "  elsewhere:\n    runs-on: ubuntu-latest\n"
            "    steps:\n" + RETAIN))

    def test_a_retention_step_without_a_name_is_still_graded(self):
        """Both shapes: the condition on the dash line, and the condition below it."""
        for unnamed in ('      - if: success()\n        uses: actions/upload-artifact@v4\n',
                        '      - uses: actions/upload-artifact@v4\n        if: success()\n'):
            with self.subTest(dash=unnamed.splitlines()[0].strip()):
                tail = ('        with:\n'
                        '          path: ${{ runner.temp }}/obs.json\n'
                        '          if-no-files-found: error\n')
                self.assertEqual(ONLY_WHEN_WELL,
                                 unretained(workflow(VERIFY_STEP + unnamed + tail)))

    def test_a_narrowed_always_is_refused(self):
        """`always() && <anything>` reads as unconditional and is not."""
        self.assertEqual(ONLY_WHEN_WELL, unretained(workflow(
            VERIFY_STEP + RETAIN.replace("${{ !cancelled() }}",
                                         "always() && github.event_name == 'push'"))))

    def test_a_missing_record_must_refuse_rather_than_warn(self):
        self.assertEqual(MAY_GO_MISSING, unretained(workflow(
            VERIFY_STEP + RETAIN.replace("if-no-files-found: error",
                                         "if-no-files-found: warn"))))

    def test_every_truthy_continue_on_error_takes_the_refusal_back(self):
        """`if-no-files-found: error` is the whole of the runtime enforcement, and
        `continue-on-error` neuters exactly it. It takes an expression, so testing
        for the string `true` caught one spelling of four."""
        for value in ("true", "True", "TRUE", "${{ true }}",
                      "${{ github.event_name == 'push' }}"):
            step = RETAIN.replace("        uses: actions/upload-artifact@v4\n",
                                  f"        continue-on-error: {value}\n"
                                  "        uses: actions/upload-artifact@v4\n")
            with self.subTest(where="step", value=value):
                self.assertEqual(NOBODY_LISTENS, unretained(workflow(VERIFY_STEP + step)))
            with self.subTest(where="job", value=value):
                self.assertEqual(NOBODY_LISTENS, unretained(
                    workflow(VERIFY_STEP + RETAIN).replace(
                        "    runs-on: ubuntu-latest\n",
                        f"    runs-on: ubuntu-latest\n    continue-on-error: {value}\n")))

    def test_a_continue_on_error_that_is_plainly_off_is_accepted(self):
        self.assertEqual([], unretained(workflow(
            VERIFY_STEP + RETAIN.replace("        uses: actions/upload-artifact@v4\n",
                                         "        continue-on-error: false\n"
                                         "        uses: actions/upload-artifact@v4\n"))))

    def test_a_required_value_present_only_in_a_comment_is_refused(self):
        self.assertEqual(MAY_GO_MISSING, unretained(workflow(
            VERIFY_STEP + RETAIN.replace(
                "          if-no-files-found: error\n",
                "          # if-no-files-found: error\n"
                "          if-no-files-found: warn\n"))))

    def test_an_observe_flag_present_only_in_a_comment_is_refused(self):
        self.assertEqual(NO_OBSERVE, unretained(workflow(
            "      - run: |\n"
            '          # --observe "$RUNNER_TEMP/obs.json" would go here\n'
            "          python scripts/verify.py\n" + RETAIN)))

    def test_a_condition_inside_the_with_block_is_not_the_steps_condition(self):
        """An `if:` nested under `with:` leaves the step itself unconditioned."""
        self.assertEqual(ONLY_WHEN_WELL, unretained(workflow(
            VERIFY_STEP + RETAIN.replace("        if: ${{ !cancelled() }}\n", "")
            .replace("          name: probe\n",
                     "          name: probe\n          if: ${{ !cancelled() }}\n"))))

    def test_a_hidden_job_beside_a_clean_one_is_refused(self):
        """The rule that covers unenumerated shapes has to survive being hidden
        beside a step it can see. It was once per file and gated on the file
        grading nothing, so appending either of these to a real workflow put a bare
        verify step into CI and passed. Both are valid YAML and both run it."""
        clean = workflow(VERIFY_STEP + RETAIN)
        for label, shadow in (
                ("a trailing comment on steps:",
                 "  shadow:\n    runs-on: ubuntu-latest\n    steps:  # run it\n"
                 "      - run: python scripts/verify.py\n"),
                ("a flow sequence of steps",
                 "  shadow:\n    runs-on: ubuntu-latest\n"
                 "    steps: [{run: python scripts/verify.py}]\n")):
            with self.subTest(shape=label):
                found = unretained(clean + shadow)
                self.assertTrue(found, f"{label} hid a verify step")
                self.assertTrue(any(entry.startswith("shadow:") for entry in found), found)

    def test_a_file_with_no_readable_job_at_all_is_refused(self):
        for text in (workflow(VERIFY_STEP).replace("jobs:\n", "JOBS:\n"),
                     "runs:\n  using: composite\n  steps:\n" + VERIFY_STEP):
            with self.subTest(text=text.splitlines()[0]):
                self.assertEqual([UNSEEN_FILE], unretained(text))

    def test_a_job_head_with_a_trailing_comment_or_quotes_is_still_read(self):
        for head in ('  only:  # a note\n', '  "only":\n', "  'only':\n"):
            with self.subTest(head=head.strip()):
                self.assertEqual(NOT_UPLOADED, unretained(workflow(VERIFY_STEP, head)))

    def test_legal_spellings_are_not_over_refused(self):
        """Twelve forms earlier readers refused for being written differently. Each
        was found by an independent witness rather than imagined here."""
        clean = workflow(VERIFY_STEP + RETAIN)
        for was, now in (
                ("if: ${{ !cancelled() }}", 'if: "${{ !cancelled() }}"'),
                ("if: ${{ !cancelled() }}", "if: '${{ !cancelled() }}'"),
                ("if: ${{ !cancelled() }}", "if: always()"),
                ("if: ${{ !cancelled() }}", "if: ${{ !cancelled() }}  # keep these"),
                ("if-no-files-found: error", "if-no-files-found: error  # refuse an absence"),
                ("if-no-files-found: error", 'if-no-files-found: "error"'),
                ("${{ runner.temp }}", "${{runner.temp}}"),
                ('--observe "$RUNNER_TEMP/obs.json"', '--observe="$RUNNER_TEMP/obs.json"'),
                ('--observe "$RUNNER_TEMP/obs.json"', "--observe '$RUNNER_TEMP/obs.json'"),
                ('--observe "$RUNNER_TEMP/obs.json"',
                 '--observe "${{ runner.temp }}/obs.json"')):
            with self.subTest(now=now):
                self.assertEqual([], unretained(clean.replace(was, now)))

    def test_a_templated_observe_path_is_accepted(self):
        """The guard must not refuse a legal matrix-scoped filename."""
        name = "${{ matrix.python-version }}-obs.json"
        self.assertEqual([], unretained(workflow(
            VERIFY_STEP.replace("obs.json", name)
            + RETAIN.replace("runner.temp }}/obs.json", "runner.temp }}/" + name))))


if __name__ == "__main__":
    unittest.main()
