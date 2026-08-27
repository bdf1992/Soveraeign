"""Read a witness probe's source: what it says it reaches, and how it handles not reaching.

Split from `sovwitness/probes.py`, which grades a probe. This module only reads
one, and the boundary is worth keeping: everything here is a fact about the
module's syntax tree, and everything there is a judgement about the tree it runs
against.

Nothing in this file measures whether a declaration is true. `reach_targets`
reads the paths a probe's own constants name, which is the probe's testimony
about itself; `sovwitness/probes.py` records what that does and does not buy.
"""

from __future__ import annotations

import ast

NO_OP_NODES = (ast.Pass, ast.Continue, ast.Break)


def root_names(tree: ast.Module) -> set[str]:
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


def used_names(tree: ast.Module) -> set[str]:
    """Every name the module loads, as opposed to the ones it only binds."""
    return {node.id for node in ast.walk(tree)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)}


def reach_targets(tree: ast.Module) -> dict[str, str]:
    """The repository paths this module declares it reaches, keyed by constant name.

    These are the module-level `ROOT / "..."` constants. A bare alias of the root
    resolves to the empty tuple, which is registered so paths built through it stay
    visible, and emitted as no target of its own. Registering it matters: skipping
    the alias let a probe hide its real reach behind one existing decoy constant.
    """
    roots = root_names(tree)
    known: dict[str, tuple[str, ...]] = {}
    targets: dict[str, str] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        parts = _flatten(node.value, known, roots)
        if parts is None:
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name):
                continue
            known[target.id] = parts
            if parts:
                targets[target.id] = "/".join(parts)
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
    """Whether this handler would catch one of the named exception types.

    Qualified forms count: `except errors.ProbeError` catches the same class that
    `except ProbeError` does, so the attribute name is compared as well.
    """
    if handler.type is None:
        return True
    caught = {node.id for node in ast.walk(handler.type) if isinstance(node, ast.Name)}
    caught |= {node.attr for node in ast.walk(handler.type)
               if isinstance(node, ast.Attribute)}
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


def handler_defects(tree: ast.Module) -> tuple[list[str], list[str]]:
    """Grade every handler that could catch a reach failure. Returns (defects, debts).

    A handler that discards the failure outright fails. One that catches it and
    carries on without re-raising is reported as debt and not failed, because
    whether the reason reaches the report is not decidable from the source; that
    is the limit `sovwitness/probes.py` records.

    Grading does not depend on the probe having declared a reach-failure class.
    An earlier version returned here when none was declared, so a probe carrying
    `except Exception: pass` and no class of its own was never graded at all and
    read `LIVE` — the rule was evaded by deleting one line. The missing class
    stays a debt; the handlers are graded either way, against the builtin bases a
    reach failure would travel through.
    """
    declared, bases = _reach_failure_names(tree)
    debts: list[str] = []
    if not declared:
        debts.append("declares no reach-failure exception, so a probe that cannot reach "
                     "its subject is indistinguishable from one that did")
    catchable = declared | bases
    defects: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler) or not _catches(node, catchable):
            continue
        where = f"line {node.lineno}"
        if _is_no_op(node.body):
            defects.append(f"{where}: catches its reach failure and discards it")
            continue
        if not any(isinstance(inner, ast.Raise) for inner in ast.walk(node)):
            debts.append(f"{where}: catches a reach failure and does not re-raise, so "
                         "whether the reason reaches the report is not checkable here")
    return defects, debts


def entry_point_defects(tree: ast.Module) -> list[str]:
    """Whether the module can still be run the way its documentation says."""
    defects: list[str] = []
    names = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    if "main" not in names:
        defects.append("no main(), so the documented entry point is gone")
    guarded = any(isinstance(node, ast.If) and any(
        isinstance(inner, ast.Name) and inner.id == "__name__" for inner in ast.walk(node.test))
        for node in tree.body)
    if not guarded:
        defects.append("no __main__ guard, so it cannot be run as documented")
    return defects
