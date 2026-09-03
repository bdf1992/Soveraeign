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
import argparse
import ast
import json
import re
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]

REFUSALS = {
    "UNRUNNABLE_CLOSURE_CHECK":
        "The closure check names a command whose script is not in the repository, so the "
        "custody's declared closure cannot be run at all.",
    "SILENT_CLOSURE_CHECK":
        "The closure check names a Python module with no entry point, so running it as "
        "declared produces no reading and its silence reads as a pass.",
    "UNREPORTING_CLOSURE_CHECK":
        "The closure check ran and printed nothing, so the custody's declared closure "
        "reports no reading a participant could act on.",
}

#: `python`, `python3`, `python3.12`, `pythonw`, and the Windows launcher `py`.
INTERPRETER = re.compile(r"^(?:python|py)[0-9.]*w?(?:\.exe)?$", re.IGNORECASE)

#: Interpreter options that consume the token after them, so it is not the script.
VALUED_OPTIONS = frozenset({"-W", "-X", "--check-hash-based-pycs"})

Defect = tuple[str, str]


def script_of(expression: str) -> str | None:
    """The repository-relative script a `python ...` expression would run, if any.

    `None` means the expression is not a plain interpreter-plus-file invocation
    and this module declines to judge it statically: `-m` and `-c` name an
    import target or a literal rather than a file, and a non-Python command is
    somebody else's vocabulary. `grade_live` asks those the only way that works,
    which is to run them.
    """
    try:
        argv = shlex.split(expression)
    except ValueError:
        return None
    # A `NAME=value` prefix is environment, not the interpreter. Without this,
    # `PYTHONPATH=scripts python foo.py` reads `pythonpath=scripts` as an
    # interpreter and returns `python` as the script.
    while argv and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", argv[0]):
        argv = argv[1:]
    if len(argv) < 2 or not INTERPRETER.match(Path(argv[0]).name):
        return None

    rest = iter(argv[1:])
    for token in rest:
        if token in ("-m", "-c"):
            return None
        if token in VALUED_OPTIONS:
            next(rest, None)
            continue
        if token.startswith("-"):
            continue
        return token
    return None


def _names_main(test: ast.expr) -> bool:
    """True for `__name__ == "__main__"` and its `in (...)` spelling, only."""
    if not isinstance(test, ast.Compare) or len(test.ops) != 1:
        return False
    operator, right = test.ops[0], test.comparators[0]
    if not isinstance(test.left, ast.Name) or test.left.id != "__name__":
        return False
    if isinstance(operator, ast.Eq):
        return isinstance(right, ast.Constant) and right.value == "__main__"
    if isinstance(operator, ast.In) and isinstance(right, (ast.Tuple, ast.List)):
        return any(isinstance(item, ast.Constant) and item.value == "__main__"
                   for item in right.elts)
    return False


def _does_something(body: list[ast.stmt]) -> bool:
    """False for a guard body that is only `pass`, `...`, or a docstring."""
    for statement in body:
        if isinstance(statement, ast.Pass):
            continue
        if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant):
            continue
        return True
    return False


def has_entry_point(source: str) -> bool:
    """True when running the module as a command would execute something.

    A `__main__` guard is the ordinary spelling, and a bare top-level call is
    the other one: a module ending in `main()` or `sys.exit(main())` runs when
    invoked. Both are accepted; a guard whose body is `pass` is not, because it
    declares an entry point and executes nothing.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for node in tree.body:
        if isinstance(node, ast.If) and _names_main(node.test):
            return _does_something(node.body)
        if isinstance(node, (ast.Expr, ast.Raise)):
            value = node.value if isinstance(node, ast.Expr) else node.exc
            if isinstance(value, ast.Call):
                return True
    return False


def _check_of(custody: dict[str, Any]) -> dict[str, Any]:
    check = (custody.get("closure") or {}).get("check") or {}
    return check if check.get("kind") == "COMMAND" else {}


def grade(custody: dict[str, Any], root: Path = ROOT) -> list[Defect]:
    """Screen one custody's declared closure command without running it."""
    check = _check_of(custody)
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


def grade_collection(custodies: list[dict[str, Any]], root: Path = ROOT) -> list[Defect]:
    """Screen every custody's declared closure command."""
    return [defect for custody in custodies for defect in grade(custody, root)]


def run(custody: dict[str, Any], root: Path = ROOT, timeout: int = 120) -> dict[str, Any]:
    """Execute one declared closure command and report what it actually said."""
    check = _check_of(custody)
    expression = str(check.get("expression") or "")
    argv = shlex.split(expression)
    if argv and INTERPRETER.match(Path(argv[0]).name):
        argv[0] = sys.executable
    try:
        result = subprocess.run(argv, cwd=root, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError) as error:
        return {"expression": expression, "ran": False, "reported": False,
                "exit_code": None, "lines": 0, "detail": str(error)}
    reading = (result.stdout or "").strip()
    return {"expression": expression, "ran": True, "exit_code": result.returncode,
            "reported": bool(reading), "lines": len(reading.splitlines())}


def grade_live(custodies: list[dict[str, Any]], root: Path = ROOT) -> tuple[list[dict], list[Defect]]:
    """Run each declared closure command and refuse one that reports nothing.

    This is what the static screen only approximates. A non-zero exit is not a
    defect here: a closure check is meant to refuse when its subject is
    defective, and refusing loudly is the check working.
    """
    rows: list[dict[str, Any]] = []
    defects: list[Defect] = []
    for custody in custodies:
        if not _check_of(custody):
            continue
        custody_id = str(custody.get("custody_id") or "unnamed custody")
        row = {"custody_id": custody_id, **run(custody, root)}
        rows.append(row)
        if not row["reported"]:
            defects.append((
                "UNREPORTING_CLOSURE_CHECK",
                f"{custody_id} declares `{row['expression']}`, which "
                + (f"exited {row['exit_code']} and printed nothing"
                   if row["ran"] else f"could not be run: {row.get('detail')}")))
    return rows, defects


def _active_phase(root: Path) -> str:
    """The phase STATUS projects, so no check table hardcodes an assumed phase."""
    text = (root / "STATUS.yaml").read_text(encoding="utf-8")
    match = re.search(r"(?m)^phase:\s*(\S+)\s*$", text)
    return match.group(1) if match else ""


def command_closures(args: argparse.Namespace) -> int:
    """Read every declared closure check, statically and optionally by running it."""
    from sovcustody import model as modelmod  # noqa: PLC0415

    phase = getattr(args, "phase", None)
    if phase == "active":
        phase = _active_phase(ROOT)
        if not phase or phase == "NONE_ACTIVE":
            print("no active phase; no exit custody carries a live closure check")
            return 0
    records = modelmod.custodies(phase)
    defects = grade_collection(records)
    rows: list[dict[str, Any]] = []
    if getattr(args, "run", False):
        rows, live = grade_live(records)
        defects += live
    else:
        rows = [{"custody_id": str(custody.get("custody_id") or ""),
                 "expression": str(_check_of(custody).get("expression") or "")}
                for custody in records if _check_of(custody)]

    if getattr(args, "as_json", False):
        print(json.dumps({"phase": phase, "checks": rows,
                          "defects": [{"code": code, "detail": detail}
                                      for code, detail in defects]}, indent=2))
    else:
        print(f"{len(rows)} declared COMMAND closure check(s)"
              + (f" in {phase}" if phase else ""))
        for row in rows:
            print(f"  {row['custody_id']}\n           {row['expression']}")
            if getattr(args, "run", False):
                state = "no reading" if not row["reported"] else f"{row['lines']} line(s)"
                print(f"           exit {row['exit_code']}, {state}")
        for code, detail in defects:
            print(f"  DEFECT {code}: {detail}")
    return 1 if defects else 0
