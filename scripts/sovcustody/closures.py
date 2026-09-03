"""Refuse a custody whose declared closure check cannot produce a reading.

`contracts/custody.schema.json` requires a closure `check` with a `kind` and a
non-empty `expression`, and `sovcustody.model` refuses a custody that declares
neither a check nor a settling seat. Neither can see the failure this module
names: a `COMMAND` whose expression runs, exits 0, and says nothing.

Two of the six Phase 1.5 exit custodies were opened that way. Their expressions
named real Python modules with real grading functions and no `__main__` entry
point, so `python scripts/sov_active_phase_progress.py` and
`python conformance/commissioning.py` each printed nothing and returned 0. A
participant running the declared check would read silence as a pass, which is
trap T2 wearing a custody's clothes.

The grade here is static and consumes nothing: a module with no `__main__` guard
cannot report, whatever its contents. `run` executes the declared commands
instead, and is deliberately not what the repository check calls: a static read
is `RECORD_LOCAL`, running arbitrary declared commands is not. The static read
cannot see a `main` that prints nothing; `run` is the reading that can.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import ast
import json
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
}

Defect = tuple[str, str]


def script_of(expression: str) -> str | None:
    """The repository-relative script a `python ...` expression would run, if any."""
    try:
        argv = shlex.split(expression)
    except ValueError:
        return None
    if len(argv) < 2 or not Path(argv[0]).name.lower().startswith("python"):
        return None
    for token in argv[1:]:
        if token in ("-m", "-c"):
            # `python -m package.module` names an import target, not a file this
            # module can read. Judging it would need the import path, so it is
            # left to `run`, which asks the command itself.
            return None
        if token.startswith("-"):
            continue
        return token
    return None


def has_entry_point(source: str) -> bool:
    """True when the module guards a `__main__` block, so running it does something."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for node in tree.body:
        if not isinstance(node, ast.If):
            continue
        test = node.test
        if not isinstance(test, ast.Compare) or len(test.comparators) != 1:
            continue
        left, right = test.left, test.comparators[0]
        names = {getattr(left, "id", None), getattr(right, "id", None)}
        values = {getattr(left, "value", None), getattr(right, "value", None)}
        if "__name__" in names and "__main__" in values:
            return True
    return False


def grade(custody: dict[str, Any], root: Path = ROOT) -> list[Defect]:
    """Grade one custody's declared closure command without running it."""
    closure = custody.get("closure") or {}
    check = closure.get("check") or {}
    if check.get("kind") != "COMMAND":
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
                 f"{custody_id} declares `{expression}`, and {script} has no __main__ entry "
                 "point, so the declared check reports nothing")]
    return []


def grade_collection(custodies: list[dict[str, Any]], root: Path = ROOT) -> list[Defect]:
    """Grade every custody's declared closure command."""
    return [defect for custody in custodies for defect in grade(custody, root)]


def run(custody: dict[str, Any], root: Path = ROOT, timeout: int = 120) -> dict[str, Any]:
    """Execute one declared closure command and report what it actually said."""
    closure = custody.get("closure") or {}
    check = closure.get("check") or {}
    expression = str(check.get("expression") or "")
    argv = shlex.split(expression)
    if argv and Path(argv[0]).name.lower().startswith("python"):
        argv[0] = sys.executable
    try:
        result = subprocess.run(argv, cwd=root, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError) as error:
        return {"expression": expression, "ran": False, "detail": str(error)}
    reading = (result.stdout or "").strip()
    return {
        "expression": expression,
        "ran": True,
        "exit_code": result.returncode,
        "reported": bool(reading),
        "lines": len(reading.splitlines()),
    }


def command_closures(args: argparse.Namespace) -> int:
    """Read every declared closure check, statically or by running it."""
    from sovcustody import model as modelmod  # noqa: PLC0415

    records = modelmod.custodies(getattr(args, "phase", None))
    defects = grade_collection(records)
    rows = []
    for custody in records:
        check = (custody.get("closure") or {}).get("check") or {}
        if check.get("kind") != "COMMAND":
            continue
        row = {"custody_id": str(custody.get("custody_id") or ""),
               "expression": str(check.get("expression") or "")}
        if getattr(args, "run", False):
            row.update(run(custody))
        rows.append(row)

    if getattr(args, "as_json", False):
        print(json.dumps({"checks": rows,
                          "defects": [{"code": code, "detail": detail}
                                      for code, detail in defects]}, indent=2))
    else:
        print(f"{len(rows)} declared COMMAND closure check(s)")
        for row in rows:
            print(f"  {row['custody_id']}\n           {row['expression']}")
            if getattr(args, "run", False):
                state = ("no reading" if not row.get("reported")
                         else f"{row.get('lines')} line(s)")
                print(f"           exit {row.get('exit_code', '-')}, {state}")
        for code, detail in defects:
            print(f"  DEFECT {code}: {detail}")
    return 1 if defects else 0
