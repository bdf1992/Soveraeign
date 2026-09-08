"""Grade whether each CI verification run leaves its per-check records behind.

`scripts/verify.py --observe` emits one record per check against
`contracts/observation.schema.json`, carrying the addresses that check read and
both its clocks. A workflow job that runs the verifier and keeps only the exit
code throws that away and keeps one bit, and one bit cannot tell a defective
change from a busy host from another session writing the tree mid-run. This
module reads `.github/` and says which verify steps do that.

It lives here rather than beside its cases because it is the guard, not a test
of one: under `scripts/tests/` neither `scripts/lint.py` nor the module-size
ceiling can see it, which a third independent witness named as the thing worth
recording about a hundred lines of hand-rolled reader.

The reader is textual on purpose. PyYAML is not in the standard library and CI
installs a bare interpreter, so a parser is not available to it. It knows the
one shape a workflow has: jobs at a fixed indent under `jobs:`, a `steps:` list
in each, steps at a fixed deeper dash indent.

What it cannot read, it refuses. Three witnesses in a row defeated a guard that
tried to enumerate the ways of hiding a verify step - eight shapes, then five
more, then two more that survived the rule written to catch unenumerated ones -
so the rule here is counted rather than listed: every mention of the verifier
that does not resolve to a graded step is a refusal, per job and per file. That
turns "the reader went blind" from silence into failure, which is the only
version of this guard that does not need to be right about the shapes nobody
has written yet.

Known limits, stated rather than left to be found:
  - flow style (`steps: [{...}]`, `with: {...}`) is unreadable here, so a verify
    step written that way refuses rather than being guessed at;
  - a verify step that opens a heredoc refuses, because `--observe` inside a
    heredoc body is not an argument and nothing here parses shell.
Both are strictness, not blindness: they fail closed.
"""

from __future__ import annotations

import re

JOBS_HEAD = re.compile(r"""^['"]?jobs['"]?:\s*(#.*)?$""")
JOB_HEAD = re.compile(r"""^ {2}['"]?[A-Za-z_][\w-]*['"]?:\s*(#.*)?$""")
STEPS_KEY = re.compile(r"""^\s*['"]?steps['"]?:\s*(#.*)?$""")
PAIR = re.compile(r"""^\s*-?\s*['"]?(?P<key>[A-Za-z_][\w-]*)['"]?:\s*(?P<value>.*?)\s*$""")
VERIFIER = "scripts/verify.py"
TEMP = r"(?:\$RUNNER_TEMP|\$\{\{\s*runner\.temp\s*\}\})"
OBSERVE = re.compile(
    r'--observe[\s=]+'
    rf'(?:"(?P<double>{TEMP}/[^"]+)"'
    rf"|'(?P<single>{TEMP}/[^']+)'"
    rf'|(?P<bare>{TEMP}/\S+))')
EXPRESSION = re.compile(r"\$\{\{\s*(?P<inner>.*?)\s*\}\}")
# A step that runs whenever the job reached it, however the author spelled it.
UNCONDITIONAL = frozenset({"always()", "${{ always() }}", "!cancelled()", "${{ !cancelled() }}"})
# `continue-on-error` is refused unless it is plainly off. It takes an expression,
# so `True`, `${{ true }}` and `${{ github.event_name == 'push' }}` all enable it,
# and it neuters `if-no-files-found: error` - which is the whole of the runtime
# enforcement - by letting the upload fail without the job noticing.
DISABLED = frozenset({"", "false", "no", "off"})


def normalise(text: str) -> str:
    """One workflow with the whitespace inside every `${{ }}` expression settled."""
    return EXPRESSION.sub(lambda found: "${{ " + found.group("inner") + " }}", text)


def unquoted(value: str) -> str:
    """One scalar with its surrounding quotes removed, if it carries a matched pair."""
    if len(value) > 1 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1].strip()
    return value


def scalar(value: str) -> str:
    """One scalar with a trailing `#` comment dropped and its quotes removed.

    The comment is only dropped outside an expression, so a `#` inside `${{ }}`
    stays. Reading a value by substring over its whole step is what let a witness
    leave `if-no-files-found: error` in a comment while the live value said `warn`.
    """
    depth = 0
    for index, char in enumerate(value):
        if value.startswith("${{", index):
            depth += 1
        elif value.startswith("}}", index) and depth:
            depth -= 1
        elif char == "#" and not depth and index and value[index - 1] in " \t":
            value = value[:index]
            break
    return unquoted(value.strip())


def live(text: str) -> str:
    """One block with its whole-line comments removed."""
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))


def mapping_at(lines: list[str], start: int, depth: int) -> dict[str, str]:
    """The `key: value` pairs written at exactly `depth`, until the block ends."""
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
            found[pair.group("key")] = scalar(pair.group("value"))
    return found


def keys_of(step: str) -> dict[str, str]:
    """One step's own mapping keys, including any written on the dash line."""
    lines = step.splitlines()
    depth = len(lines[0]) - len(lines[0].lstrip()) + 2
    found = {}
    first = PAIR.match(lines[0])
    if first:
        found[first.group("key")] = scalar(first.group("value"))
    found.update(mapping_at(lines, 1, depth))
    return found


def with_of(step: str) -> dict[str, str]:
    """One step's `with:` block, read at its own indent rather than by substring."""
    lines = step.splitlines()
    depth = len(lines[0]) - len(lines[0].lstrip()) + 2
    for index, line in enumerate(lines):
        if line.lstrip().startswith("#"):
            continue
        if len(line) - len(line.lstrip()) == depth and line.split("#")[0].strip() == "with:":
            return mapping_at(lines, index + 1, depth + 2)
    return {}


def steps_of(block: list[str]) -> list[str]:
    """The step blocks of one job, split on the dash indent its own `steps:` uses.

    A `steps:` key carrying a value - a flow sequence - is not a list this reader
    can walk, so it yields nothing and the caller refuses the job.
    """
    try:
        start = next(i for i, line in enumerate(block) if STEPS_KEY.match(line))
    except StopIteration:
        return []
    marks = [i for i in range(start + 1, len(block)) if re.match(r"^ +- ", block[i])]
    if not marks:
        return []
    depth = len(block[marks[0]]) - len(block[marks[0]].lstrip())
    marks = [i for i in marks if len(block[i]) - len(block[i].lstrip()) == depth]
    return ["\n".join(block[a:b]) for a, b in zip(marks, marks[1:] + [len(block)])]


def jobs_of(text: str) -> dict[str, tuple[str, list[str]]]:
    """Split one workflow into job name -> (job text, step blocks), without a parser."""
    lines = text.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if JOBS_HEAD.match(line.rstrip()))
    except StopIteration:
        return {}
    body = []
    for line in lines[start + 1:]:
        if line.strip() and not line.startswith(" ") and not line.lstrip().startswith("#"):
            break
        body.append(line)
    heads = [i for i, line in enumerate(body) if JOB_HEAD.match(line.rstrip())]
    jobs = {}
    for position, head in enumerate(heads):
        end = heads[position + 1] if position + 1 < len(heads) else len(body)
        name = unquoted(body[head].split("#", 1)[0].strip().rstrip(":"))
        jobs[name] = ("\n".join(body[head:end]), steps_of(body[head:end]))
    return jobs


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
    graded = 0
    accounted = 0
    for job, (block, steps) in jobs_of(text).items():
        settings = mapping_at(block.splitlines(), 1, 4)
        uploads = [step for step in steps if "upload-artifact@" in step]
        seen = 0
        for step in steps:
            body = live(step)
            if VERIFIER not in body:
                continue
            seen += 1
            if "<<" in body:
                missing.append(f"{job}: a verify step runs through shell this cannot read")
                continue
            found = OBSERVE.search(body)
            if found is None:
                missing.append(f"{job}: a verify step does not pass --observe")
                continue
            raw = found.group("double") or found.group("single") or found.group("bare")
            name = raw.split("/", 1)[1]
            keepers = [one for one in uploads
                       if f"runner.temp }}}}/{name}" in one or f"$RUNNER_TEMP/{name}" in one]
            if not keepers:
                missing.append(f"{job}: {name} is written and no step in that job uploads it")
                continue
            for keeper in keepers:
                missing.extend(_keeper_faults(job, name, keeper))
                for where in (keys_of(keeper).get("continue-on-error"),
                              settings.get("continue-on-error")):
                    if where is not None and where.lower() not in DISABLED:
                        missing.append(
                            f"{job}: {name} refuses an absent file and nothing listens")
        named = live(block).count(VERIFIER)
        accounted += named
        graded += seen
        if named > seen:
            missing.append(f"{job}: runs the verifier in a shape the reader cannot see")
    if live(text).count(VERIFIER) > accounted:
        missing.append("this file runs the verifier in a shape the reader cannot see")
    return missing


def graded_steps(text: str) -> int:
    """How many verify steps the reader actually reached in one workflow."""
    return sum(VERIFIER in live(step)
               for _, steps in jobs_of(normalise(text)).values() for step in steps)


__all__ = ["graded_steps", "jobs_of", "keys_of", "mapping_at", "normalise", "scalar",
           "steps_of", "unquoted", "unretained", "with_of"]
