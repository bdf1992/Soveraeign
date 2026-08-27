"""Grade every witness probe on whether it can still reach the subject it names.

`witness/probes/` holds the code a witness wrote to take an observation. A probe
that has rotted is dead evidence dressed as live evidence: the receipt it
produced still reads as a measurement, and nothing says the code behind it stopped
working.

Grading a probe is deliberately not running its subject through a gate. A probe
observes and exits 0 whether or not the subject survives, and that boundary is
what makes it a witness rather than a judge. Nothing here reads whether a check
held; it reads only whether the probe can still get to the thing it examines.

Two tiers, because reaching is expensive:

- `inspect` is static and lives inside `scripts/verify.py`. It parses each probe,
  extracts the repository paths the module declares as its reach, and requires
  those paths to exist. A probe pointing at a deleted service fails here.
- `run` actually executes each probe and reads the report it emitted. This is the
  only tier that observes reaching rather than inferring it, and it is out of the
  verification budget: the three probes shipped on PR #119 cost 12.7s together,
  against a 15s SILVER ceiling for the whole suite.

What `run` must not do is judge by exit code. Every probe here exits 0 by design,
and the shipped probes catch `Exception` around each check and record
`{"held": null, "probe_error": ...}`. A probe whose every check failed to reach
its subject still exits 0 and still emits a well-formed report, so liveness is
read out of the report's contents and never from the process result.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import ast
import json
import subprocess
import sys

REACH_TIMEOUT_SECONDS = 300
NO_OP_NODES = (ast.Pass, ast.Continue, ast.Break)
LIVE, DEAD = "LIVE", "DEAD"
# Verdicts that fail the check. A probe that cannot be reached through is not
# weak evidence; it is evidence that stopped existing without saying so.
FAILING_VERDICTS = frozenset({DEAD})


def probes_dir(root: Path) -> Path:
    return root / "witness" / "probes"


def _root_names(tree: ast.Module) -> set[str]:
    """Module-level names bound to the repository root, i.e. derived from `__file__`."""
    found = set()
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(inner, ast.Name) and inner.id == "__file__"
                for inner in ast.walk(node.value)):
            found.update(target.id for target in node.targets
                         if isinstance(target, ast.Name))
    return found


def _flatten(value: ast.expr, known: dict[str, tuple[str, ...]],
             roots: set[str]) -> tuple[str, ...] | None:
    """Read `ROOT / "a" / "b"` into ("a", "b"), following names already resolved."""
    if isinstance(value, ast.Name):
        if value.id in roots:
            return ()
        return known.get(value.id)
    if not isinstance(value, ast.BinOp) or not isinstance(value.op, ast.Div):
        return None
    left = _flatten(value.left, known, roots)
    if left is None:
        return None
    if not isinstance(value.right, ast.Constant) or not isinstance(value.right.value, str):
        return None
    return left + (value.right.value,)


def reach_targets(tree: ast.Module) -> list[str]:
    """The repository paths this module declares it reaches, read out of its source.

    These are the module-level `ROOT / "..."` constants. They are what the probe
    says it touches; whether each one still exists is then a fact about the tree.
    """
    roots = _root_names(tree)
    known: dict[str, tuple[str, ...]] = {}
    targets: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        parts = _flatten(node.value, known, roots)
        if not parts:
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                known[target.id] = parts
        targets.append("/".join(parts))
    return targets


def _reach_failure_names(tree: ast.Module) -> tuple[set[str], set[str]]:
    """Locally declared reach-failure exception classes, and the bases they widen to.

    A handler catching a declared base catches the reach failure too. `ProbeError`
    subclasses `RuntimeError`, so `except RuntimeError` and `except Exception`
    both swallow it; the bases are collected for exactly that reason.
    """
    declared: set[str] = set()
    bases: set[str] = {"BaseException", "Exception"}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        base_names = {base.id for base in node.bases if isinstance(base, ast.Name)}
        if any(name.endswith(("Error", "Exception")) for name in base_names):
            declared.add(node.name)
            bases |= base_names
    return declared, bases


def _catches(handler: ast.ExceptHandler, names: set[str]) -> bool:
    """Whether this handler would catch one of the named exception types."""
    if handler.type is None:
        return True
    caught = {node.id for node in ast.walk(handler.type) if isinstance(node, ast.Name)}
    return bool(caught & names)


def _is_no_op(body: list[ast.stmt]) -> bool:
    """A handler body that discards the failure entirely."""
    for statement in body:
        if isinstance(statement, NO_OP_NODES):
            continue
        if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant):
            continue
        return False
    return True


def _handler_defects(tree: ast.Module) -> tuple[list[str], list[str]]:
    """Grade every handler that could catch a reach failure. Returns (defects, debts)."""
    declared, bases = _reach_failure_names(tree)
    if not declared:
        return [], ["declares no reach-failure exception, so a probe that cannot reach "
                    "its subject is indistinguishable from one that did"]
    catchable = declared | bases
    defects: list[str] = []
    debts: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler) or not _catches(node, catchable):
            continue
        where = f"line {node.lineno}"
        if _is_no_op(node.body):
            defects.append(f"{where}: catches its reach failure and discards it")
            continue
        raises = any(isinstance(inner, ast.Raise) for inner in ast.walk(node))
        binding = node.name
        carried = binding is not None and any(
            isinstance(inner, ast.Name) and inner.id == binding for inner in ast.walk(node))
        if not raises and not carried:
            debts.append(f"{where}: catches a reach failure without carrying the reason")
    return defects, debts


def inspect(path: Path, root: Path) -> dict[str, Any]:
    """Read one probe's source and grade whether its declared reach still exists."""
    result: dict[str, Any] = {"probe": path.name, "verdict": LIVE,
                              "reaches": [], "defects": [], "debts": []}
    source = path.read_bytes()
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as broken:
        result.update(verdict=DEAD, defects=[f"does not parse: {broken}"])
        return result

    targets = reach_targets(tree)
    result["reaches"] = targets
    if not targets:
        result["defects"].append("declares no reach target, so nothing says what it observes")
    for target in targets:
        if not (root / target).exists():
            result["defects"].append(f"declared reach {target} is not in the tree")

    names = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    if "main" not in names:
        result["defects"].append("no main(), so the documented entry point is gone")
    guarded = any(isinstance(node, ast.If) and any(
        isinstance(inner, ast.Name) and inner.id == "__name__" for inner in ast.walk(node.test))
        for node in tree.body)
    if not guarded:
        result["defects"].append("no __main__ guard, so it cannot be run as documented")

    defects, debts = _handler_defects(tree)
    result["defects"].extend(defects)
    result["debts"].extend(debts)
    if result["defects"]:
        result["verdict"] = DEAD
    return result


def _reach_failures(report: Any) -> list[str]:
    """Every place in a probe's report where it said it could not reach the subject.

    Read out of the report the probe emitted, never out of its exit code: every
    probe here exits 0 by design, so the exit code carries no liveness signal.
    """
    found: list[str] = []

    def walk(node: Any, trail: str) -> None:
        if isinstance(node, dict):
            if "probe_error" in node:
                found.append(f"{trail or 'report'}: {node['probe_error']}")
            elif node.get("held", False) is None:
                found.append(f"{trail or 'report'}: held is null with no probe_error")
            for key, value in node.items():
                walk(value, f"{trail}.{key}" if trail else str(key))
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, f"{trail}[{index}]")

    walk(report, "")
    return found


def run(path: Path, root: Path) -> dict[str, Any]:
    """Execute one probe and read whether it reached its subject out of its report."""
    result: dict[str, Any] = {"probe": path.name, "verdict": LIVE, "defects": []}
    try:
        done = subprocess.run([sys.executable, str(path)], capture_output=True, text=True,
                              cwd=str(root), timeout=REACH_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        result.update(verdict=DEAD,
                      defects=[f"did not finish inside {REACH_TIMEOUT_SECONDS}s"])
        return result
    result["exit_code"] = done.returncode
    try:
        report = json.loads(done.stdout)
    except json.JSONDecodeError:
        result.update(verdict=DEAD, defects=["emitted no readable report"])
        return result
    failures = _reach_failures(report)
    result["reach_failures"] = failures
    if failures:
        result.update(verdict=DEAD, defects=failures)
    return result


def modules(root: Path) -> list[Path]:
    directory = probes_dir(root)
    if not directory.is_dir():
        return []
    return sorted(directory.glob("probe_*.py"))


def joins(root: Path) -> tuple[list[str], list[str]]:
    """Grade the receipt/probe join both ways. Returns (defects, debts)."""
    from sovwitness.records import observations_dir

    present = {path.name for path in modules(root)}
    named: set[str] = set()
    defects: list[str] = []
    directory = observations_dir(root)
    for receipt in sorted(directory.glob("*.json")) if directory.is_dir() else []:
        try:
            document = json.loads(receipt.read_text(encoding="utf-8"))
            declared = document.get("telemetry", {}).get("probe")
        except (json.JSONDecodeError, OSError, AttributeError):
            continue
        if not isinstance(declared, str):
            continue
        named.add(Path(declared).name)
        if not (root / declared).exists():
            defects.append(f"{receipt.name} names probe {declared}, which is not in the tree")
    debts = [f"{name} is named by no receipt" for name in sorted(present - named)]
    return defects, debts
