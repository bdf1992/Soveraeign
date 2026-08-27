"""Read the declared claim table out of the bytes of `claims.py`.

Split from `shape.py` when a repair needed lines the 300-line budget did not have
and an independent reading named the same seam: this half reads a declaration out
of source, the half next door grades what it read. Neither knows anything about
the other's job, and the module boundary is what keeps a reader from having to
hold both at once.

Reading the source rather than importing the object is the point of both halves.
`claims.CLAIMS` is what a test patches to plant a refusing derivation; the source
is the file about to be landed, and grading the declaration is what makes this a
guard against regression rather than a report on whichever test is running.
"""

from __future__ import annotations

import ast


def read(tree: ast.Module) -> list[tuple[str, ast.expr | None]]:
    """Each declared claim's name and the expression that derives it, from the source.

    From the source and not from `claims.CLAIMS`, deliberately. The object is what
    a test patches to plant a refusing derivation; the source is the file about to
    be landed. Grading the declaration is what makes this a guard against
    regression rather than a report on whichever test is running.

    Module level only. `ast.walk` found a `CLAIMS` assigned anywhere, a nested one
    included, and graded that instead of the table the module exports. A claim
    whose derivation is passed by keyword is read as such rather than skipped: the
    skip reported "the source declares 0 claims", which sends a reader to look for
    a broken table when the table is fine and this reader is not.
    """
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == "CLAIMS" for t in node.targets):
            continue
        if not isinstance(node.value, (ast.Tuple, ast.List)):
            return []
        declared: list[tuple[str, ast.expr | None]] = []
        for element in node.value.elts:
            if not isinstance(element, ast.Call):
                declared.append(("<not a Claim(...)>", None))
                continue
            first = element.args[0] if element.args else None
            name = first.value if isinstance(first, ast.Constant) else "<unnamed>"
            derive = element.args[2] if len(element.args) >= 3 else next(
                (word.value for word in element.keywords if word.arg == "derive"), None)
            declared.append((str(name), derive))
        return declared
    return []


def names_the_module(tree: ast.Module, name: str) -> str | None:
    """Why `name` is not reliably the imported module here, if it is not.

    The guard below reads the base of an attribute access and checks it is spelled
    `committed`. Spelling is not binding, and an independent reading demonstrated
    it: `committed = ROOT / ".claude" / "skills"` followed by `committed.glob("*")`
    satisfied the invariant while doing the exact thing the invariant forbids. So
    the name is established as the import, and established as never rebound or
    shadowed anywhere in the file, before reaching it is allowed to mean anything.
    """
    if not any(isinstance(node, ast.Name) and node.id == name for node in ast.walk(tree)):
        return None
    if not any(isinstance(node, ast.ImportFrom)
               and any((alias.asname or alias.name) == name for alias in node.names)
               for node in tree.body):
        return f"`{name}` is not imported at module level, so reaching it proves nothing"
    for node in ast.walk(tree):
        stored = (isinstance(node, ast.Name) and node.id == name
                  and isinstance(node.ctx, ast.Store))
        shadowed = ((isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                     and node.name == name)
                    or (isinstance(node, ast.arg) and node.arg == name))
        if stored or shadowed:
            return (f"`{name}` is rebound or shadowed in this module, so an attribute "
                    "reached on it is not necessarily the committed record")
    return None
