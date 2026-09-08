"""Grade whether each CI verification run leaves its per-check records behind.

`scripts/verify.py --observe` emits one record per check against
`contracts/observation.schema.json`, carrying the addresses that check read and
both its clocks. A workflow job that runs the verifier and keeps only the exit
code throws that away and keeps one bit, and one bit cannot tell a defective
change from a busy host from another session writing the tree mid-run. This
module says which verify steps do that; `scripts/sovverify/workflows.py` owns
the reading it grades.

Four independent witnesses defeated the guards that came before this one - eight
shapes, then five, then two, then three - so the rule is counted rather than
listed: every mention of the verifier that does not resolve to a graded step is
a refusal, per job and per file, and a job head the reader cannot name is its own
refusal. That turns a blind reader into a failure, which is the only version of
this rule that need not be right about the shapes nobody has written yet.

Limits five readings have reached. This list is what has been found, not a proof
that nothing else is here - a fifth witness disproved the sentence that used to
stand in its place, which called the list complete and then missed two limits
that failed open. Read it as a record of where the sweep got to. Each of these
fails closed:
  - flow style (`steps: [{...}]`, `with: {...}`) is unreadable, so a verify step
    written that way refuses rather than being guessed at;
  - a verify step that opens a heredoc refuses, because `--observe` inside a
    heredoc body is not an argument and nothing here parses shell;
  - a step that merely names the file without running it - an `echo`, a message -
    reads as a verify step, because telling those apart also needs shell.

What counting does not reach is lexical, not structural. `canonical` folds the
spellings a witness executed, and `$(echo scripts)/verify.py` runs the same file
under a string nothing here can see. The claim is scoped to match: every hidden
verify step in a job this reader can name, and every job it cannot name refused
on its own account.

Every property is read off the key that declares it: the flag off the command
its `run:` actually runs, the condition and `continue-on-error` off the step's
own keys or the job's, the keeper off its `uses:` and its `with: path:`. Where a
reading is textual it is named above. That sentence is a description of the code
below and is worth checking against it rather than believing.
"""

from __future__ import annotations

import re

from sovverify.workflows import (VERIFIER, canonical, commands_of, jobs_of, keys_of,
                                 live, mapping_at, normalise, strays_of, under_temp,
                                 with_of)

UPLOAD = "actions/upload-artifact@"
OBSERVE = re.compile(
    r"--observe[\s=]+"
    r'(?:"(?P<double>(?:\$RUNNER_TEMP|\$\{\{\s*runner\.temp\s*\}\})/[^"]+)"'
    r"|'(?P<single>(?:\$RUNNER_TEMP|\$\{\{\s*runner\.temp\s*\}\})/[^']+)'"
    r"|(?P<bare>(?:\$RUNNER_TEMP|\$\{\{\s*runner\.temp\s*\}\})/\S+))")
UNCONDITIONAL = frozenset({"always()", "${{ always() }}", "!cancelled()", "${{ !cancelled() }}"})
# `continue-on-error` is refused unless it is plainly off. It takes an expression,
# so `True`, `${{ true }}` and `${{ github.event_name == 'push' }}` all enable it,
# and it neuters `if-no-files-found: error` - which is the whole of the runtime
# enforcement - by letting the upload fail without the job noticing.
# Only a bare false counts as off. `no` and `off` are YAML 1.1 booleans a 1.2
# reader takes as strings, `'false'` is a non-empty string, and this key is
# evaluated as an expression rather than read as a boolean, so none of their
# meanings is settled here. Refusing them fails closed: a legal spelling refused
# costs an edit, a truthy one accepted costs the runtime enforcement outright.
DISABLED = frozenset({"", "false"})


def continues_on_error(keys: dict[str, str]) -> bool:
    """Whether a mapping enables `continue-on-error` in any spelling but a bare false.

    Read off the key, never off the text around it. A line-anchored regex missed
    the dash-line spelling entirely - `- continue-on-error: true` as a step's
    first key - and `keys_of` had the right answer available the whole time.
    """
    value = keys.get("continue-on-error")
    return value is not None and value.lower() not in DISABLED


def job_keys(block: str) -> dict[str, str]:
    """One job's own keys, from anywhere in the job rather than above its steps.

    `continue-on-error` is legal after `steps:` and means the same thing there. An
    earlier read stopped at `steps:`, so writing it below the list disabled the
    runtime enforcement wherever the keeper was not the last step.
    """
    lines = block.splitlines()
    depth = len(lines[0]) - len(lines[0].lstrip()) + 2
    return mapping_at(lines, 1, depth, raw=True)


def _keeper_faults(job: str, name: str, keeper: str) -> list[str]:
    """What one upload step fails to guarantee about the file it names."""
    keys = keys_of(keeper)
    faults = []
    if keys.get("if") not in UNCONDITIONAL:
        faults.append(f"{job}: {name} is kept only when the job goes well")
    if with_of(keeper).get("if-no-files-found") != "error":
        faults.append(f"{job}: {name} may go missing without refusing")
    return faults


def unretained(text: str) -> list[str]:
    """Every `scripts/verify.py` step in one workflow that keeps only its exit code.

    A step is retained when it writes the records and the job that wrote them
    uploads that exact file: unconditionally, refusing an absent file, and with no
    `continue-on-error` to take that refusal back.
    """
    text = normalise(text)
    missing = []
    accounted = 0
    for job, (block, steps) in jobs_of(text).items():
        # Read `uses:` at its own key. Selecting upload steps by substring made a
        # step an upload because a comment or its `name:` said so, which is the
        # class four witnesses kept finding: a property read off the raw text
        # rather than off the key that declares it. Found in a pass over this
        # module rather than by a fifth witness, which is where it should have
        # been found the first four times.
        uploads = [step for step in steps
                   if keys_of(step).get("uses", "").startswith(UPLOAD)]
        seen = 0
        for step in steps:
            body = canonical(live(step))
            if VERIFIER not in body:
                continue
            seen += 1
            if "<<" in body:
                missing.append(f"{job}: a verify step runs through shell this cannot read")
                continue
            # Off the command that runs the verifier, never off the step's text.
            running = [one for one in commands_of(step) if VERIFIER in canonical(one)]
            found = next((match for match in
                          (OBSERVE.search(one) for one in running) if match), None)
            if found is None:
                missing.append(f"{job}: a verify step does not pass --observe")
                continue
            raw = found.group("double") or found.group("single") or found.group("bare")
            name = raw.split("/", 1)[1]
            # Read the keeper's own `path`, never a substring of its step. Matching
            # by substring accepted a commented-out `path:`, a longer name whose
            # prefix happened to agree, and the artifact's `name:` field.
            keepers = [one for one in uploads
                       if under_temp(with_of(one).get("path", "")) == name]
            if not keepers:
                missing.append(f"{job}: {name} is written and no step in that job uploads it")
                continue
            for keeper in keepers:
                missing.extend(_keeper_faults(job, name, keeper))
                if (continues_on_error(keys_of(keeper, raw=True))
                        or continues_on_error(job_keys(block))):
                    missing.append(
                        f"{job}: {name} refuses an absent file and nothing listens")
        named = canonical(live(block)).count(VERIFIER)
        accounted += named
        if named > seen:
            missing.append(f"{job}: runs the verifier in a shape the reader cannot see")
    for stray in strays_of(text):
        missing.append(f"{stray}: sits where a job head belongs and cannot be named")
    if canonical(live(text)).count(VERIFIER) > accounted:
        missing.append("this file runs the verifier in a shape the reader cannot see")
    return missing


def graded_steps(text: str) -> int:
    """How many verify steps the reader actually reached in one workflow."""
    return sum(VERIFIER in canonical(live(step))
               for _, steps in jobs_of(normalise(text)).values() for step in steps)


__all__ = ["continues_on_error", "graded_steps", "job_keys", "unretained"]
