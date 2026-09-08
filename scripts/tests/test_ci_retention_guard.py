"""Cases for the guard that keeps each verification run's records.

The guard is `scripts/sovverify/workflows.py`, which reads a workflow, and
`scripts/sovverify/retention.py`, which grades retention against that reading.
Both are production modules under the size ceiling; a third witness found the
reader living here instead, in the one tree `scripts/lint.py` is written not to
grade, and a fifth found these cases back over 400 lines in the same concern that
had split the reader for being at 349. So this module holds cases and nothing
else.

Nearly every case below was executed by an independent witness against the real
workflow bytes before it was written down. Five of them read this guard in turn
and all five dissented; the shapes they defeated are the reason each case exists,
and the docstrings in the two modules record which limits remain.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sovverify.retention import graded_steps, unretained  # noqa: E402
from sovverify.workflows import jobs_of, strays_of  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
# `.github/actions` is swept as well. A composite action is written with `runs:`
# rather than `jobs:`, so the reader finds no jobs in one; naming the verifier
# there refuses rather than passing, which is the point.
SWEPT = (ROOT / ".github" / "workflows", ROOT / ".github" / "actions")


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


class TheCountedRuleHoldsItsAttribution(unittest.TestCase):
    """Counting conserves a total; a refusal needs the total attributed correctly.

    A fourth witness showed that the reader did not drop a job head it could not
    name - it merged those lines into the job above, which then carried their
    steps, so the mention count and the graded count rose together and the counted
    rule stayed silent. Two of these put a bare verifier into this repository's own
    verify.yml and passed the whole suite.
    """

    def test_a_job_head_the_reader_cannot_name_refuses_on_its_own_account(self):
        clean = workflow(VERIFY_STEP + RETAIN)
        bare = "    runs-on: ubuntu-latest\n    steps:\n      - run: python scripts/verify.py\n"
        with self.subTest(head="a space before the colon"):
            self.assertNotEqual([], unretained(clean + "  shadow :\n" + bare))
        with self.subTest(head="an explicit key"):
            self.assertNotEqual([], unretained(clean + "  ? shadow\n  :\n" + bare))
            self.assertTrue(any("cannot be named" in entry
                                for entry in unretained(clean + "  ? shadow\n  :\n" + bare)))

    def test_the_live_workflows_carry_no_stray_head(self):
        for path in VerificationRunsLeaveARecord().workflows():
            with self.subTest(file=path.name):
                self.assertEqual([], strays_of(path.read_text(encoding="utf-8")))

    def test_an_observe_flag_hidden_in_a_trailing_comment_is_refused(self):
        """A trailing `#` is a comment in YAML and in shell alike, so a flag read
        out of one is a bare verifier. Whole-line stripping was not enough."""
        self.assertEqual(NO_OBSERVE, unretained(workflow(
            '      - run: python scripts/verify.py  # --observe "$RUNNER_TEMP/obs.json"\n'
            + RETAIN)))

    def test_spellings_of_the_same_file_are_counted_as_that_file(self):
        for label, line in (("a dot segment", "      - run: python scripts/./verify.py\n"),
                            ("a doubled slash", "      - run: python scripts//verify.py\n"),
                            ("a shell continuation",
                             "      - run: |\n          python scripts/veri\\\n          fy.py\n")):
            with self.subTest(spelling=label):
                self.assertEqual(NO_OBSERVE, unretained(workflow(line + RETAIN)))

    def test_the_keeper_is_found_by_its_own_path_and_not_by_substring(self):
        for label, keeper in (
                ("a commented-out path",
                 RETAIN.replace("          path: ${{ runner.temp }}/obs.json\n",
                                "          # path: ${{ runner.temp }}/obs.json\n")),
                ("a longer name sharing the prefix", RETAIN.replace("/obs.json\n",
                                                                    "/obs.json.bak\n")),
                ("a match in the artifact name",
                 RETAIN.replace("          name: probe\n",
                                "          name: ${{ runner.temp }}/obs.json\n")
                 .replace("          path: ${{ runner.temp }}/obs.json\n",
                          "          path: elsewhere/x.json\n"))):
            with self.subTest(keeper=label):
                self.assertEqual(NOT_UPLOADED, unretained(workflow(VERIFY_STEP + keeper)))

    def test_only_a_bare_false_reads_as_continue_on_error_being_off(self):
        """`no` and `off` are YAML 1.1 booleans a 1.2 reader takes as strings, and
        this key is evaluated as an expression. None of that is settled here, so
        everything but a bare false fails closed."""
        for value in ("no", "off", "'false'", '"false"'):
            with self.subTest(refused=value):
                self.assertEqual(NOBODY_LISTENS, unretained(workflow(
                    VERIFY_STEP + RETAIN.replace(
                        "        uses: actions/upload-artifact@v4\n",
                        f"        continue-on-error: {value}\n"
                        "        uses: actions/upload-artifact@v4\n"))))
        for value in ("false", "False"):
            with self.subTest(accepted=value):
                self.assertEqual([], unretained(workflow(
                    VERIFY_STEP + RETAIN.replace(
                        "        uses: actions/upload-artifact@v4\n",
                        f"        continue-on-error: {value}\n"
                        "        uses: actions/upload-artifact@v4\n"))))

    def test_the_verifier_named_only_in_a_comment_is_not_a_verify_step(self):
        """The mirror of the refusals above: a comment must not invent a step."""
        self.assertEqual([], unretained(workflow(
            VERIFY_STEP + "      - run: echo done  # scripts/verify.py ran above\n" + RETAIN)))

    def test_a_step_that_only_names_the_upload_action_is_not_a_keeper(self):
        """The upload step was selected by substring, so a comment or a `name:`
        saying `upload-artifact@` made a step an upload. That is the class four
        witnesses kept finding - a property read off raw text rather than off the
        key that declares it - and this instance was found by a pass over the
        module rather than by a fifth witness."""
        for label, decoy in (
                ("named only in a comment",
                 '      - name: Retain\n        if: ${{ !cancelled() }}\n'
                 '        # uses: actions/upload-artifact@v4\n'
                 '        uses: some/other-action@v1\n'),
                ("named in the step name",
                 '      - name: pretend actions/upload-artifact@v4\n'
                 '        if: ${{ !cancelled() }}\n        uses: some/other-action@v1\n')):
            with self.subTest(decoy=label):
                self.assertEqual(NOT_UPLOADED, unretained(workflow(
                    VERIFY_STEP + decoy + '        with:\n'
                    '          path: ${{ runner.temp }}/obs.json\n'
                    '          if-no-files-found: error\n')))


class EveryPropertyIsReadOffItsOwnKey(unittest.TestCase):
    """The class four witnesses kept finding, and the two instances a fifth found.

    A property read off a step's raw text rather than off the key that declares
    it. The fifth witness's finding was not another shape: it was that the module
    named two remaining text reads and there were four, and the two it missed
    failed open. These are those two, plus the quoting difference that fed one.
    """

    def test_the_flag_belongs_to_the_command_that_runs_the_verifier(self):
        for label, step in (
                ("written into the step name",
                 '      - name: Verify --observe "$RUNNER_TEMP/obs.json"\n'
                 "        run: python scripts/verify.py\n"),
                ("echoed on the line above a bare verifier",
                 "      - name: Verify\n        run: |\n"
                 '          echo skipping --observe "$RUNNER_TEMP/obs.json"\n'
                 "          python scripts/verify.py\n"),
                ("echoed, with the file fabricated so the runtime check passes too",
                 "      - name: Verify\n        run: |\n"
                 '          echo "[]" > "$RUNNER_TEMP/obs.json"\n'
                 '          echo skipping --observe "$RUNNER_TEMP/obs.json"\n'
                 "          python scripts/verify.py\n")):
            with self.subTest(where=label):
                self.assertEqual(NO_OBSERVE, unretained(workflow(step + RETAIN)))

    def test_a_plain_scalar_ends_at_a_comment_however_it_looks(self):
        """YAML ends a plain scalar at ` #` with no quoting to respect, so an
        apostrophe before it does not protect the flag from the runner - only
        from a reader that tracks quotes where YAML does not."""
        self.assertEqual(NO_OBSERVE, unretained(workflow(
            "      - run: python scripts/verify.py ' "
            '# --observe "$RUNNER_TEMP/obs.json"\n' + RETAIN)))

    def test_a_quoted_run_keeps_its_hash(self):
        """The other polarity: a quoted scalar's `#` is content, not a comment."""
        self.assertEqual([], unretained(workflow(
            '      - run: "python scripts/verify.py --observe '
            "'$RUNNER_TEMP/obs.json'\"\n" + RETAIN.replace(
                "          path: ${{ runner.temp }}/obs.json\n",
                "          path: ${{ runner.temp }}/obs.json\n"))))

    def test_continue_on_error_is_found_wherever_the_key_is_legal(self):
        for label, text in (
                ("as the keeper's first key, on the dash line",
                 workflow(VERIFY_STEP + RETAIN.replace(
                     "      - name: Retain\n",
                     "      - continue-on-error: true\n        name: Retain\n"))),
                ("on the job, written below its steps",
                 workflow(VERIFY_STEP + RETAIN) + "    continue-on-error: true\n")):
            with self.subTest(where=label):
                self.assertEqual(NOBODY_LISTENS, unretained(text))


class TheReaderSaysWhatItCannotName(unittest.TestCase):
    """`strays_of` is the newest rule and had one case standing behind it."""

    def test_heads_the_reader_can_name_are_named(self):
        bare = ("    runs-on: ubuntu-latest\n    steps:\n"
                "      - run: python scripts/verify.py\n")
        for head in ("  shadow :\n", "  shadow  :\n", '  "shadow" :\n', "  shadow:  # a note\n"):
            with self.subTest(head=head.strip()):
                found = unretained(workflow(VERIFY_STEP + RETAIN) + head + bare)
                self.assertTrue(any(entry.startswith("shadow:") for entry in found), found)
                self.assertFalse(any("cannot be named" in entry for entry in found), found)

    def test_heads_the_reader_cannot_name_are_refused_as_strays(self):
        for head in ("  ? shadow\n  :\n", "  my.job:\n", "  9shadow:\n"):
            with self.subTest(head=head.strip()):
                text = (workflow(VERIFY_STEP + RETAIN) + head
                        + "    runs-on: ubuntu-latest\n    steps:\n"
                        "      - run: python scripts/verify.py\n")
                self.assertTrue(any("cannot be named" in entry for entry in unretained(text)),
                                unretained(text))

    def test_the_live_workflows_carry_no_stray(self):
        for path in VerificationRunsLeaveARecord().workflows():
            with self.subTest(file=path.name):
                self.assertEqual([], strays_of(path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
