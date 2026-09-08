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
# `.github/actions` is swept as well. Nothing there runs the verifier today, and a
# composite action is written with `runs:` rather than `jobs:`, so this reader finds
# no steps in one. That is deliberate: the unreadable-file rule in `unretained` turns
# "the reader cannot see this" into a refusal, so putting a verify step somewhere new
# fails loudly rather than passing quietly until someone teaches the reader its shape.
SWEPT = (ROOT / ".github" / "workflows", ROOT / ".github" / "actions")
OBSERVE_TARGET = re.compile(
    r"--observe[\s=]+(?:\"\$RUNNER_TEMP/(?P<quoted>[^\"]+)\"|\$RUNNER_TEMP/(?P<bare>\S+))")
PAIR = re.compile(r"^\s*-?\s*\"?(?P<key>[A-Za-z_][\w-]*)\"?:\s*(?P<value>.*?)\s*$")
# A step that runs whenever the job reached it, however the author spelled it.
# `always()` also runs when the job is cancelled; `!cancelled()` does not. The
# workflows use `!cancelled()`, and its cost is real rather than nil: with
# `fail-fast: true`, a matrix leg cancelled after its own verify finished loses
# records `always()` would have kept. The trade is that every leg cancelled before
# verify ran would otherwise fail its upload under `if-no-files-found: error`, adding
# a red step to runs already being read for the failure that caused the cancellation.
# Either spelling is accepted here.
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


def _unquoted(value: str) -> str:
    """One scalar with its surrounding quotes removed, if it carries a matched pair."""
    if len(value) > 1 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1].strip()
    return value


def mapping_at(lines: list[str], start: int, depth: int) -> dict[str, str]:
    """The `key: value` pairs written at exactly `depth`, until the block ends.

    Comment lines and deeper blocks are skipped rather than read, which is what
    separates a step's own keys from the keys of its `with:` block. An earlier
    version of this module tested for `if-no-files-found: error` by substring over
    the whole step, and an independent witness passed it by leaving that text in a
    `#` comment while the live value read `warn`.
    """
    found = {}
    for line in lines[start:]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        here = len(line) - len(line.lstrip())
        if here < depth:
            break
        if here != depth:
            continue
        pair = PAIR.match(line)
        if pair:
            found[pair.group("key")] = _unquoted(pair.group("value"))
    return found


def keys_of(step: str) -> dict[str, str]:
    """One step's own mapping keys, including any written on the dash line."""
    lines = step.splitlines()
    depth = len(lines[0]) - len(lines[0].lstrip()) + 2
    found = {}
    first = PAIR.match(lines[0])
    if first:
        found[first.group("key")] = _unquoted(first.group("value"))
    found.update(mapping_at(lines, 1, depth))
    return found


def with_of(step: str) -> dict[str, str]:
    """One step's `with:` block, read at its own indent rather than by substring."""
    lines = step.splitlines()
    depth = len(lines[0]) - len(lines[0].lstrip()) + 2
    for index, line in enumerate(lines):
        if line.lstrip().startswith("#"):
            continue
        if len(line) - len(line.lstrip()) == depth and line.strip() == "with:":
            return mapping_at(lines, index + 1, depth + 2)
    return {}


def steps_of(block: list[str]) -> list[str]:
    """The step blocks of one job, split on the dash indent its own `steps:` uses."""
    try:
        start = next(i for i, line in enumerate(block)
                     if not line.lstrip().startswith("#") and line.rstrip().endswith("steps:"))
    except StopIteration:
        return []
    marks = [i for i in range(start + 1, len(block)) if re.match(r"^ +- ", block[i])]
    if not marks:
        return []
    depth = len(block[marks[0]]) - len(block[marks[0]].lstrip())
    marks = [i for i in marks if len(block[i]) - len(block[i].lstrip()) == depth]
    return ["\n".join(block[a:b]) for a, b in zip(marks, marks[1:] + [len(block)])]


def jobs_of(text: str) -> dict[str, tuple[str, list[str]]]:
    """Split one workflow into job name -> (job text, step blocks), without a parser.

    PyYAML is not in the standard library and CI installs a bare interpreter, so
    reading these files textually is a constraint rather than a shortcut. This reader
    knows the one shape a workflow has: jobs at a fixed indent under `jobs:`, a
    `steps:` list in each, steps at a fixed deeper dash indent. What it cannot split
    it reports as nothing, and `unretained` turns that silence into a refusal for any
    file that mentions the verifier at all.
    """
    lines = text.splitlines()
    try:
        start = next(i for i, line in enumerate(lines)
                     if re.match(r"^\"?jobs\"?:\s*(#.*)?$", line.rstrip()))
    except StopIteration:
        return {}
    body = []
    for line in lines[start + 1:]:
        if line.strip() and not line.startswith(" ") and not line.lstrip().startswith("#"):
            break
        body.append(line)
    heads = [i for i, line in enumerate(body)
             if re.match(r"^ {2}\"?[A-Za-z_][\w-]*\"?:\s*(#.*)?$", line.rstrip())]
    jobs = {}
    for position, head in enumerate(heads):
        end = heads[position + 1] if position + 1 < len(heads) else len(body)
        name = _unquoted(body[head].split("#", 1)[0].strip().rstrip(":"))
        jobs[name] = ("\n".join(body[head:end]), steps_of(body[head:end]))
    return jobs


def unretained(text: str) -> list[str]:
    """Every `scripts/verify.py` step in one workflow that keeps only its exit code.

    A verify run already builds one Observation per check against
    `contracts/observation.schema.json`, carrying the addresses that check read. A
    job that runs it and keeps one bit cannot tell a defective change from a busy
    host from another session writing the tree. A step is retained when it writes
    the records and the job that wrote them uploads that exact file:
    unconditionally, refusing an absent file, and without a `continue-on-error`
    that would turn that refusal back into a warning.

    Two independent witnesses have attacked this. The first defeated a per-line
    reader eight ways - a folded `run: >-` scalar (the idiom in these same files), a
    `run: |` block, `python3`, a `bash -lc` wrapper, a `cd && ` prefix, a `.yaml`
    extension, an upload from another job, and a step with no `- name:` line. The
    second defeated the per-step reader that replaced it five more - a
    `continue-on-error` on the retention step, the required value present only in a
    comment, an `if:` misplaced inside `with:`, `--observe` inside a comment, and job
    heads the reader could not see. Every one of those is a case in this module.

    The last of those is why an unreadable file refuses rather than passing: the
    supply of shapes nobody has thought of is not exhausted by thirteen of them.

    The known limit, stated here rather than found later: `--observe` inside a
    heredoc body still reads as an argument. Nothing here parses shell.
    """
    missing = []
    graded = 0
    for job, (block, steps) in jobs_of(text).items():
        settings = mapping_at(block.splitlines(), 1, 4)
        uploads = [step for step in steps if "upload-artifact@" in step]
        for step in steps:
            live = "\n".join(line for line in step.splitlines()
                             if not line.lstrip().startswith("#"))
            if "scripts/verify.py" not in live:
                continue
            graded += 1
            found = OBSERVE_TARGET.search(live)
            if found is None:
                missing.append(f"{job}: a verify step does not pass --observe")
                continue
            name = found.group("quoted") or found.group("bare")
            keepers = [one for one in uploads if "runner.temp }}/" + name in one]
            if not keepers:
                missing.append(f"{job}: {name} is written and no step in that job uploads it")
                continue
            for keeper in keepers:
                if keys_of(keeper).get("if") not in UNCONDITIONAL:
                    missing.append(f"{job}: {name} is kept only when the job goes well")
                if with_of(keeper).get("if-no-files-found") != "error":
                    missing.append(f"{job}: {name} may go missing without refusing")
                if "true" in (keys_of(keeper).get("continue-on-error"),
                              settings.get("continue-on-error")):
                    missing.append(f"{job}: {name} refuses an absent file and nothing listens")
    if not graded and "scripts/verify.py" in text:
        missing.append("this file runs the verifier in a shape the reader cannot see")
    return missing


def workflow(steps: str) -> str:
    """A miniature workflow carrying `steps`, for grading `unretained` on one shape."""
    return ("name: probe\n\njobs:\n  only:\n    runs-on: ubuntu-latest\n"
            "    steps:\n" + steps)


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
UNREADABLE = ["this file runs the verifier in a shape the reader cannot see"]


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
        graded = 0
        for path in self.workflows():
            text = path.read_text(encoding="utf-8")
            self.assertEqual([], unretained(text), f"{path.name} keeps only an exit code")
            graded += sum("scripts/verify.py" in step
                          for _, steps in jobs_of(text).values() for step in steps)
        # A reader that found nothing would satisfy every assertion above. Four verify
        # steps exist across these files; dropping one is a change to this line, not a
        # silently smaller sweep.
        self.assertEqual(4, graded, "the reader found a different number of verify steps")

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

    def test_an_upload_from_another_job_does_not_count(self):
        """A different job is a different runner, so its $RUNNER_TEMP is another disk."""
        self.assertEqual(NOT_UPLOADED, unretained(
            workflow(VERIFY_STEP) + "  elsewhere:\n    runs-on: ubuntu-latest\n"
            "    steps:\n" + RETAIN))

    def test_a_retention_step_without_a_name_is_still_graded(self):
        """Both shapes: the condition on the dash line, and the condition below it."""
        for unnamed in ('      - if: success()\n'
                        '        uses: actions/upload-artifact@v4\n',
                        '      - uses: actions/upload-artifact@v4\n'
                        '        if: success()\n'):
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

    def test_a_continue_on_error_takes_the_refusal_back(self):
        """`if-no-files-found: error` is the runtime half of this guarantee, and
        `continue-on-error` neuters exactly it: the upload fails, the job does not."""
        step = workflow(VERIFY_STEP + RETAIN.replace(
            "        uses: actions/upload-artifact@v4\n",
            "        continue-on-error: true\n        uses: actions/upload-artifact@v4\n"))
        self.assertEqual(NOBODY_LISTENS, unretained(step))
        job = workflow(VERIFY_STEP + RETAIN).replace(
            "    runs-on: ubuntu-latest\n",
            "    runs-on: ubuntu-latest\n    continue-on-error: true\n")
        self.assertEqual(NOBODY_LISTENS, unretained(job))

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

    def test_a_shape_the_reader_cannot_see_refuses_rather_than_passes(self):
        """Reader blindness has to be loud. A file that runs the verifier in a shape
        the split cannot reach must fail, not read as an empty and therefore clean
        file. This is the rule that covers the shapes nobody has thought of yet."""
        self.assertEqual(UNREADABLE, unretained(
            workflow(VERIFY_STEP).replace("jobs:\n", "JOBS:\n")))
        self.assertEqual(UNREADABLE, unretained(
            "runs:\n  using: composite\n  steps:\n" + VERIFY_STEP))

    def test_a_job_head_with_a_trailing_comment_or_quotes_is_still_read(self):
        for head in ('  only:  # a note\n', '  "only":\n'):
            with self.subTest(head=head.strip()):
                self.assertEqual(NOT_UPLOADED, unretained(
                    "name: probe\n\njobs:\n" + head + "    runs-on: ubuntu-latest\n"
                    "    steps:\n" + VERIFY_STEP))

    def test_legal_spellings_are_not_over_refused(self):
        """Three forms the previous reader refused for being written differently."""
        for was, now in (("if: ${{ !cancelled() }}", 'if: "${{ !cancelled() }}"'),
                         ("if: ${{ !cancelled() }}", "if: always()"),
                         ('--observe "$RUNNER_TEMP/obs.json"',
                          '--observe="$RUNNER_TEMP/obs.json"')):
            with self.subTest(now=now):
                self.assertEqual([], unretained(
                    workflow(VERIFY_STEP + RETAIN).replace(was, now)))

    def test_a_templated_observe_path_is_accepted(self):
        """The guard must not refuse a legal matrix-scoped filename."""
        name = "${{ matrix.python-version }}-obs.json"
        self.assertEqual([], unretained(workflow(
            VERIFY_STEP.replace("obs.json", name)
            + RETAIN.replace("runner.temp }}/obs.json", "runner.temp }}/" + name))))


if __name__ == "__main__":
    unittest.main()
