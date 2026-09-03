"""Refuse a custody whose declared closure check cannot produce a reading.

`contracts/custody.schema.json` requires a closure `check` with a `kind` and a
non-empty `expression`, and `sovcustody.model` refuses a custody that declares
neither a check nor a settling seat. Neither can see the failure this module
names: a `COMMAND` whose expression runs, exits 0, and says nothing.

Two of the six Phase 1.5 exit custodies opened that way. Their expressions named
real Python modules with real grading functions and no `__main__` entry point,
so `python scripts/sov_active_phase_progress.py` and
`python conformance/commissioning.py` each printed nothing and returned 0. A
participant running the declared check would read silence as a pass, which is
trap T2 wearing a custody's clothes.

Two readings, because one is not enough:

- `grade` is static and consumes nothing. It screens every declared command in
  the repository, including closed-phase history. It grades a *declaration*: a
  module with no entry point cannot report whatever it contains. It cannot see
  an entry point that reports nothing, and `if __name__ == "__main__": pass`
  satisfies it. That is the limit of any static proxy, which is why it is the
  screen and not the measurement.
- `grade_live` runs the commands and refuses one that reports nothing. It is the
  measurement, and it is scoped by the caller because running every declared
  command is `RESOURCE_CONSUMPTION` and reaches history nobody is carrying. The
  repository gate runs it over the active phase's exit custodies, which is the
  set a participant is asked to close today.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import os
import shlex
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sovcustody.invocation import INTERPRETER, has_entry_point, script_of  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]

REFUSALS = {
    "UNRUNNABLE_CLOSURE_CHECK":
        "The closure check names a command whose script is not in the repository, so the "
        "custody's declared closure cannot be run at all.",
    "SILENT_CLOSURE_CHECK":
        "The closure check names a Python module with no entry point, so running it as "
        "declared produces no reading and its silence reads as a pass.",
    "UNCITED_OBSERVATION":
        "A member claims a stage was observed by a citation that does not resolve to a file "
        "inside the repository, so the record carrying its standing cannot be opened.",
    "UNREPORTING_CLOSURE_CHECK":
        "The closure check said nothing on either stream, so whatever it exited with, "
        "a participant running it is left with no reading at all.",
}

def check_of(custody: dict[str, Any]) -> dict[str, Any]:
    check = (custody.get("closure") or {}).get("check") or {}
    return check if check.get("kind") == "COMMAND" else {}


def grade(custody: dict[str, Any], root: Path = ROOT) -> list[Defect]:
    """Screen one custody's declared closure command without running it."""
    check = check_of(custody)
    if not check:
        return []
    custody_id = str(custody.get("custody_id") or "unnamed custody")
    expression = str(check.get("expression") or "")
    script = script_of(expression)
    if script is None:
        return []
    path = root / script
    if not path.is_file():
        return [("UNRUNNABLE_CLOSURE_CHECK",
                 f"{custody_id} declares `{expression}`, and {script} is not in the repository")]
    if path.suffix == ".py" and not has_entry_point(path.read_text(encoding="utf-8")):
        return [("SILENT_CLOSURE_CHECK",
                 f"{custody_id} declares `{expression}`, and {script} runs nothing when "
                 "invoked, so the declared check reports nothing")]
    return []


def grade_observation(custody: dict[str, Any], root: Path = ROOT) -> list[Defect]:
    """Refuse a member whose observing citation does not open.

    `stage_observed_by` is what separates a stage a participant drew from one
    something else confirmed, and nothing graded it: a member could read
    `WITNESSED` citing a file that was never written, or one deleted afterwards,
    and every check stayed green. That is a citation nobody can follow, which is
    the same defect as a closure check nobody can read.

    It grades that the citation opens, and no more. A record that exists, says
    nothing about this member, and declares a revision the member does not live
    at satisfies this and should not be read as covering anything: whether an
    observation covers its subject is a reading, not a path test. The one thing
    beyond existence that is checked is escape, because `root / "/etc/passwd"`
    is `/etc/passwd` — pathlib drops the left operand on an absolute right — and
    a refusal saying "inside the repository" has to mean it.
    """
    custody_id = str(custody.get("custody_id") or "unnamed custody")
    defects: list[Defect] = []
    inside = root.resolve()
    for member in custody.get("members") or []:
        cited = member.get("stage_observed_by")
        if cited is None:
            continue
        target = (root / str(cited)).resolve()
        opens = str(cited) != "" and target.is_file() and target.is_relative_to(inside)
        if not opens:
            defects.append(("UNCITED_OBSERVATION",
                            f"{custody_id} member {member.get('address')} says its stage was "
                            f"observed by {cited!r}, which does not open inside the repository"))
    return defects


def grade_collection(custodies: list[dict[str, Any]], root: Path = ROOT) -> list[Defect]:
    """Screen every declared closure command, and every observation a member cites."""
    return [defect for custody in custodies
            for defect in grade(custody, root) + grade_observation(custody, root)]


#: Interpreter variables that make Python write to stderr on its own account. A
#: silent command reports nothing, which is the whole defect; under any of these
#: the interpreter says something the module never chose to say and the reading
#: becomes non-empty without the command having spoken. Each was confirmed to
#: launder the exact Phase 1.5 shape - a main() that runs, reports nothing,
#: returns 0 - into an admitted one.
#:
#: The line is diagnostics, not resolution. PYTHONPATH, PYTHONHOME, VIRTUAL_ENV
#: and the rest decide whether the command can run at all and are passed
#: through, which is why this is a denylist and not `-E` or `-I`.
DIAGNOSTIC_ENV = (
    "PYTHONDEVMODE", "PYTHONWARNINGS", "PYTHONVERBOSE", "PYTHONPROFILEIMPORTTIME",
    "PYTHONMALLOCSTATS", "PYTHONINSPECT", "PYTHONFAULTHANDLER",
)


def _child_env() -> dict[str, str]:
    """The environment a closure command runs under, with interpreter chatter off.

    The predicate is about what the command said, so what the interpreter says
    about it is turned off rather than counted.

    Two costs, both accepted. The list is a denylist, so a diagnostic variable
    nobody has found yet would still launder a silent command; isolated mode
    would close that and would also drop the resolution variables a command may
    need to start. And pinning warnings off silences a check whose whole reading
    is a deliberate `warnings.warn`, which would then be refused for saying
    nothing - no declared command reports that way, and `-W always` or
    `-W error` in the expression itself overrides the pin for one that does.
    """
    environment = {key: value for key, value in os.environ.items()
                   if key not in DIAGNOSTIC_ENV}
    environment["PYTHONWARNINGS"] = "ignore"
    return environment


def run(custody: dict[str, Any], root: Path = ROOT, timeout: int = 120) -> dict[str, Any]:
    """Execute one declared closure command and report what it actually said."""
    check = check_of(custody)
    expression = str(check.get("expression") or "")
    argv = shlex.split(expression)
    if argv and INTERPRETER.match(Path(argv[0]).name):
        argv[0] = sys.executable
    try:
        result = subprocess.run(argv, cwd=root, capture_output=True, text=True,
                                timeout=timeout, env=_child_env())
    except (OSError, subprocess.SubprocessError) as error:
        return {"expression": expression, "ran": False, "reported": False,
                "exit_code": None, "lines": 0, "detail": str(error)}
    reading = (result.stdout or "").strip()
    return {"expression": expression, "ran": True, "exit_code": result.returncode,
            "reported": bool(reading) or bool((result.stderr or "").strip()),
            "lines": len(reading.splitlines())}


def grade_live(custodies: list[dict[str, Any]], root: Path = ROOT) -> tuple[list[dict], list[Defect]]:
    """Run each declared closure command and refuse the one that says nothing.

    This is what the static screen only approximates, and it grades exactly one
    thing: did the command produce a reading. Nothing on stdout and nothing on
    stderr is the defect, whatever it exited with. That is the Phase 1.5 shape
    at exit 0, where silence is the whole reading and a participant takes it for
    a pass; and it is the same silence at exit 3, wearing a different code.

    The exit code decides nothing here, and neither does a traceback. A closure
    check exists to refuse when its subject is defective, so exiting non-zero
    with a written reason is the check working. All seven declared commands in
    this repository that exit non-zero write 135 to 195 characters of reason,
    which is why "wrote a reason anywhere" is the predicate and "printed a
    Python traceback" is not: the latter refuses a failing `-m unittest` suite,
    which is a check correctly refusing, and refuses a passing one for writing
    its result to stderr.

    Whether the reason is a good one is the holder's to answer. A command that
    rejects its own arguments is naming a capability its custody has not built,
    and a reader that crashes is a broken reader; both are that holder's work,
    and neither is a declaration nobody can read.
    """
    rows: list[dict[str, Any]] = []
    defects: list[Defect] = []
    for custody in custodies:
        if not check_of(custody):
            continue
        custody_id = str(custody.get("custody_id") or "unnamed custody")
        row = {"custody_id": custody_id, **run(custody, root)}
        rows.append(row)
        if not row["ran"]:
            defects.append(("UNREPORTING_CLOSURE_CHECK",
                            f"{custody_id} declares `{row['expression']}`, which could not "
                            f"be run: {row.get('detail')}"))
        elif not row["reported"]:
            defects.append(("UNREPORTING_CLOSURE_CHECK",
                            f"{custody_id} declares `{row['expression']}`, which exited "
                            f"{row['exit_code']} and said nothing on either stream"))
    return rows, defects


def live(custodies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The custodies still carrying work: everything without a terminal.

    Not "belongs to the active phase". That filter reads as history-versus-now
    and is not: two live custodies carry no phase at all, and scoping by phase
    equality drops them silently. A terminal is the record of an assignment
    that ended, which is the thing the gate should skip.
    """
    return [custody for custody in custodies if not custody.get("terminal")]
