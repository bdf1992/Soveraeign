"""Grade the shape of the declared claim table, which no number can reveal.

Split out of `sovsnapshot/selfcheck.py` on 2026-08-26 at the 300-line budget, and
the seam is real: next door proves the grader fires on a page, and this proves the
table is still asking the commit. They fail for different reasons and a reader
chasing one should not have to read the other.

Bdo ruled the snapshot's referent on acceptance packet A5: the counts are counts
of committed state. Nothing in the grader can notice a claim that goes back to
globbing the working tree, because the number it produces looks exactly like a
real count - which is how the defect survived nine review rounds. So the invariant
is structural and is re-read from the bytes of `claims.py` on every run.

An independent reading planted five shapes against the first version of this and
watched every one of them pass, including a fall back to a glob through a local
variable named `committed`, which defeated the invariant rather than escaping it.
Each of the five is now a case in `scripts/tests/test_sov_snapshot.py`.
"""

from __future__ import annotations

from pathlib import Path
import ast

from sovsnapshot import claims

#: The module that is the record. Every route to a count ends here.
RECORD = "committed"

#: The modules a declared derivation may reach to answer. `declared` is here
#: because one claim counts a tuple in a committed module rather than committed
#: files, and that parsing lives apart from the path matching. Allowing a second
#: name is only safe if the second name is established rather than trusted, so
#: `_reader_is_thin` holds it to the same rule from its own bytes.
READERS = (RECORD, "declared")


def _claim_table(tree: ast.Module) -> list[tuple[str, ast.expr | None]]:
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


def _names_the_module(tree: ast.Module, name: str) -> str | None:
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


def derivations_read_the_commit() -> str | None:
    """The mismatch, if any declared claim derives from something other than the commit.

    Bdo ruled the snapshot's referent on acceptance packet A5: the counts are
    counts of committed state. Nothing in the grader can notice a new claim that
    globs the working tree instead - the number it produces looks exactly like a
    real count, which is how the defect survived in the first place. So the
    invariant is structural and is re-read from bytes on every run: every claim in
    the table reaches `sovsnapshot.committed`, and the one function allowed to read
    the page off disk is `page_text`.

    The second half is not decoration. `claims.page_text` is the deliberate
    exception, and an exception nothing pins is an exception that spreads.

    What it does not prove, stated so silence is not read as confirmation. It
    establishes that each declared derivation reaches the committed record; it does
    not establish that nothing else is reached. A derivation that calls `committed`
    and then falls back to a glob inside `except Underivable`, or that hands the
    work to a module-level helper, passes here. A blocklist of filesystem calls
    would be the narrowness `LESSONS.md` L-0007 names - it would catch the reach
    that has been seen and not the next one - so the invariant stays the positive
    one and the numbers themselves are graded by the cases in
    `scripts/tests/test_sov_snapshot.py`.
    """
    source = Path(claims.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    table = _claim_table(tree)
    stray = []
    if not table:
        # Without this the guard is satisfied by finding nothing, which is the
        # vacuity every other check in this module has had to be repaired for.
        stray.append(f"no claim table could be read from {Path(claims.__file__).name}, "
                     "so this guard graded nothing")
    if len(table) != len(claims.CLAIMS):
        stray.append(f"the source declares {len(table)} claims and the loaded table "
                     f"holds {len(claims.CLAIMS)}; the table is not a literal this can read")
    # Only the readers this source actually routes through. Demanding an import of
    # one it never mentions would report a module for not using a module.
    used = tuple(reader for reader in READERS
                 if any(isinstance(n, ast.Name) and n.id == reader for n in ast.walk(tree)))
    unbound = [why for reader in used if (why := _names_the_module(tree, reader))]
    stray.extend(unbound)
    stray.extend(why for reader in used if reader != RECORD
                 and (why := _reader_is_thin(reader)))
    functions = {node.name: node for node in ast.walk(tree)
                 if isinstance(node, ast.FunctionDef)}
    for name, expression in table:
        if expression is None:
            stray.append(f"{name}: its derivation could not be read from the declaration")
            continue
        if (isinstance(expression, ast.Attribute) and isinstance(expression.value, ast.Name)
                and expression.value.id in READERS and not unbound):
            continue
        body = functions.get(expression.id) if isinstance(expression, ast.Name) else None
        if body is None:
            stray.append(f"{name}: its derivation is not a function declared in "
                         f"{Path(claims.__file__).name}, so its source cannot be read here")
            continue
        if unbound or not _reaches(body, READERS):
            stray.append(f"{name}: {expression.id} reaches none of {list(READERS)}, "
                         "so it is not counting the commit at HEAD")
    off_page = sorted(node.name for node in functions.values() if node.name != "page_text"
                      and any(_reads_the_page(n) for n in ast.walk(node)))
    if off_page:
        stray.append(f"{off_page} read the page off disk; page_text is the only "
                     "working-tree read this module is allowed")
    return "; ".join(stray) if stray else None


def _reaches(node: ast.AST, names: tuple[str, ...]) -> bool:
    """Whether anything under this node takes an attribute off one of these names."""
    return any(isinstance(found, ast.Attribute) and isinstance(found.value, ast.Name)
               and found.value.id in names for found in ast.walk(node))


def _reader_is_thin(name: str) -> str | None:
    """Why an intermediary reader is not itself only reading the record, if it is not.

    Allowing a derivation to answer through `declared` rather than through
    `committed` widens the invariant, and a widened invariant that nobody re-reads
    is how "reaches the commit" quietly becomes "reaches one of two names, one of
    which nobody checked". So the intermediary is held to the same rule from its own
    source: `committed` imported, never rebound or shadowed, and reached by every
    function it defines.
    """
    source = Path(claims.__file__).with_name(f"{name}.py")
    if not source.is_file():
        return f"sovsnapshot.{name} is declared a reader and its source is not here"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    unbound = _names_the_module(tree, RECORD)
    if unbound:
        return f"sovsnapshot.{name}: {unbound}"
    adrift = sorted(node.name for node in ast.walk(tree)
                    if isinstance(node, ast.FunctionDef) and not _reaches(node, (RECORD,)))
    if adrift:
        return (f"sovsnapshot.{name}: {adrift} reach nothing in sovsnapshot.{RECORD}, "
                "so routing a claim through this module does not reach the record")
    return None


def _reads_the_page(node: ast.AST) -> bool:
    """Whether this node names the snapshot page, by constant or by binding.

    Both spellings, because checking only the name `SNAPSHOT` let a deriver reach
    the page as `(ROOT / "CLAUDE.md").read_text(...)` and pass.
    """
    return ((isinstance(node, ast.Name) and node.id == "SNAPSHOT")
            or (isinstance(node, ast.Constant) and node.value == claims.SNAPSHOT.name))
