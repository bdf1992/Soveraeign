"""Read a GitHub workflow well enough to say what each of its steps declares.

PyYAML is not in the standard library and CI installs a bare interpreter, so
reading these files textually is a constraint rather than a shortcut. This module
knows the one shape a workflow has: jobs at a fixed indent under `jobs:`, a
`steps:` list in each, steps at a fixed deeper dash indent. It owns the reading
only; `scripts/sovverify/retention.py` owns what the reading is graded against.

Four independent witnesses in a row defeated a guard built on this, and nearly
every defeat was a shape the reader could not see rather than a rule that was
wrong. So it reports what it cannot name rather than passing over it: an
unrecognised line where a job head belongs used to merge into the job above and
carry its steps, which kept a counted rule silent. `strays_of` is that repair.
"""

from __future__ import annotations

import re

JOBS_HEAD = re.compile(r"""^['"]?jobs['"]?:\s*(#.*)?$""")
# A space before the colon is ordinary YAML. An earlier spelling of this required
# the colon to follow the name immediately, so `shadow :` did not match - and an
# unmatched head was not dropped, it was merged into the job above, which carried
# its steps and made both counters rise together. That is why `strays_of` exists.
JOB_HEAD = re.compile(r"""^ {2}['"]?[A-Za-z_][\w-]*['"]?\s*:\s*(#.*)?$""")
STEPS_KEY = re.compile(r"""^\s*['"]?steps['"]?:\s*(#.*)?$""")
PAIR = re.compile(r"""^\s*-?\s*['"]?(?P<key>[A-Za-z_][\w-]*)['"]?:\s*(?P<value>.*?)\s*$""")
VERIFIER = "scripts/verify.py"
CONTINUED = re.compile(r"\\\s*\n\s*")
REDUNDANT = re.compile(r"/(?:\./)+|/{2,}")
TEMP = r"(?:\$RUNNER_TEMP|\$\{\{\s*runner\.temp\s*\}\})"
TEMP_ROOT = re.compile(rf"^{TEMP}/")
EXPRESSION = re.compile(r"\$\{\{\s*(?P<inner>.*?)\s*\}\}")
# A step that runs whenever the job reached it, however the author spelled it.

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


def decomment(line: str) -> str:
    """One line with any comment removed, respecting quotes.

    Whole-line comments are not enough. `run: python scripts/verify.py  # --observe
    "$RUNNER_TEMP/x.json"` is a bare verifier in YAML and in shell alike, and a
    witness used exactly that to put one into this repository's own workflow while
    the guard read the flag out of the comment.
    """
    quote = ""
    for index, char in enumerate(line):
        if quote:
            if char == quote:
                quote = ""
        elif char in "\"'":
            quote = char
        elif char == "#" and (not index or line[index - 1] in " \t"):
            return line[:index]
    return line


def live(text: str) -> str:
    """One block with every comment removed, whole-line and trailing alike."""
    return "\n".join(decomment(line) for line in text.splitlines())


def canonical(text: str) -> str:
    """One block with the spellings that name the same file collapsed onto one.

    Shell line continuations are joined and redundant path separators removed, so
    `scripts/./verify.py`, `scripts//verify.py` and a name split across a
    backslash continuation each count as the mention they are. This is lexical and
    cannot be complete - `$(echo scripts)/verify.py` runs the same file and is not
    reachable from here - which is why the module docstring scopes the claim.
    """
    return REDUNDANT.sub("/", CONTINUED.sub("", text))


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
        if len(line) - len(line.lstrip()) == depth and decomment(line).strip() == "with:":
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


def _jobs_body(text: str) -> list[str]:
    """The lines under `jobs:`, or nothing when the file declares no jobs."""
    lines = text.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if JOBS_HEAD.match(line.rstrip()))
    except StopIteration:
        return []
    body = []
    for line in lines[start + 1:]:
        if line.strip() and not line.startswith(" ") and not line.lstrip().startswith("#"):
            break
        body.append(line)
    return body


def strays_of(text: str) -> list[str]:
    """Lines sitting where a job head belongs that this reader cannot name.

    Such a line is not skipped, it is absorbed into the job above, which then
    carries its steps. Both the mention count and the graded count rise together
    and the counted rule stays silent. So a stray is its own refusal.
    """
    return [line.strip() for line in _jobs_body(text)
            if line.strip() and not line.lstrip().startswith("#")
            and len(line) - len(line.lstrip()) == 2 and not JOB_HEAD.match(line.rstrip())]


def jobs_of(text: str) -> dict[str, tuple[str, list[str]]]:
    """Split one workflow into job name -> (job text, step blocks), without a parser."""
    body = _jobs_body(text)
    heads = [i for i, line in enumerate(body) if JOB_HEAD.match(line.rstrip())]
    jobs = {}
    for position, head in enumerate(heads):
        end = heads[position + 1] if position + 1 < len(heads) else len(body)
        name = unquoted(decomment(body[head]).strip().rstrip(":").strip())
        jobs[name] = ("\n".join(body[head:end]), steps_of(body[head:end]))
    return jobs



def before_steps(block: str) -> str:
    """One job's own settings, without the steps beneath them."""
    lines = block.splitlines()
    for index, line in enumerate(lines):
        if STEPS_KEY.match(line):
            return "\n".join(lines[:index])
    return block


def under_temp(value: str) -> str:
    """What one path names beneath the runner's temporary directory, or ""."""
    found = TEMP_ROOT.match(value.strip())
    return value.strip()[found.end():] if found else ""




__all__ = ["JOBS_HEAD", "JOB_HEAD", "PAIR", "STEPS_KEY", "TEMP", "TEMP_ROOT",
           "VERIFIER", "before_steps", "canonical", "decomment", "jobs_of",
           "keys_of", "live", "mapping_at", "normalise", "scalar", "steps_of",
           "strays_of", "under_temp", "unquoted", "with_of"]
