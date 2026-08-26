"""Grade the shape of the declared claim table, which no number can reveal.

Split out of `sovsnapshot/selfcheck.py` on 2026-08-26 at the 300-line budget, and
the seam is real: next door proves the grader fires on a page, and this proves the
table is still asking the commit. They fail for different reasons and a reader
chasing one should not have to read the other.

Bdo ruled the snapshot's referent on acceptance packet A5: the counts are counts
of committed state, apart from the two claims the same ruling left on the working
tree. Nothing in the grader can notice a claim that goes back to globbing the
tree, because the number it produces looks exactly like a real count - which is
how the defect survived nine review rounds. So the invariant is structural and is
re-read from the bytes of `claims.py` on every run, and the two exceptions are
named here rather than left to be recognised.

An independent reading planted five shapes against the first version of this and
watched every one of them pass, including a fall back to a glob through a local
variable named `committed`, which defeated the invariant rather than escaping it.
A second reading then took `committed.ROOT` - a `Path` exported by the module
this treats as the record - and globbed the working tree with it while satisfying
every rule here. Each of those shapes is now a case in
`scripts/tests/test_sov_snapshot.py`.
"""

from __future__ import annotations

from pathlib import Path
import ast

from sovsnapshot import claims

#: The module that is the record. Every route to a count ends here.
RECORD = "committed"

#: The modules a declared derivation may reach to answer. One name today.
#: `sovsnapshot.declared` was a second until the two claims that needed it went
#: back to the working tree; the check that held it to the record from its own
#: bytes went with it, so adding a reader here again means writing that check
#: again rather than widening this tuple alone.
READERS = (RECORD,)

#: Attributes of a reader that are not answers. `committed.ROOT` is a `Path`, so a
#: derivation that takes it and globs reads the working tree while satisfying
#: "reaches `committed`" - the reach an independent reading demonstrated, and the
#: one shape here that could be closed rather than only named. Reaching one of
#: these does not count as reaching the record, and reaching one anywhere in
#: `claims.py` is reported.
NOT_AN_ANSWER = ("ROOT",)

#: The claims Bdo's ruling on acceptance packet A5 left on the working tree,
#: named so a third cannot join them quietly. Each counts something the repository
#: already computes - the check table `verify.py` imports, the capability map
#: projection `sov_capability.py` builds - so reading either out of the commit
#: would be a second implementation of an existing count. Held in both directions
#: below: one of these that reaches the record is an exception nobody removed, and
#: a name here that the table does not declare is an exception grading nothing.
WORKING_TREE = ("verification checks", "declared operations")


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
    """The mismatch, if any graded claim derives from something other than the commit.

    Bdo ruled the snapshot's referent on acceptance packet A5: the counts are
    counts of committed state, except for the two claims in `WORKING_TREE`, which
    the same ruling left where they were. Nothing in the grader can notice a new
    claim that globs the working tree instead - the number it produces looks
    exactly like a real count, which is how the defect survived in the first place.
    So the invariant is structural and is re-read from bytes on every run: every
    claim not named as an exception reaches `sovsnapshot.committed`, every named
    exception still does not, and the one function allowed to read the page off
    disk is `page_text`.

    The last two halves are not decoration. `claims.page_text` is the deliberate
    exception and so are those two claims, and an exception nothing pins is an
    exception that spreads.

    What it does not prove, stated so silence is not read as confirmation. It
    establishes that each graded derivation reaches the committed record; it does
    not establish that nothing else is reached. Four shapes have been demonstrated
    against it, and two of them are closed:

    - a derivation that takes `committed.ROOT` and globs it, and
    - a plain `pathlib` glob built from `committed.ROOT`.

    Both satisfied "reaches `committed`" while reading the working tree, and both
    are now reported: `NOT_AN_ANSWER` names `ROOT` as a path rather than an answer,
    so reaching it neither counts as reaching the record nor passes unremarked
    anywhere in `claims.py`. Two remain open and are named rather than described in
    general terms:

    - a derivation that calls `committed.tracked_paths()` and hands the counting to
      a module-level helper that globs, and
    - a derivation that reaches the record and then falls back to a glob inside
      `except Underivable`.

    A blocklist of filesystem calls would be the narrowness `LESSONS.md` L-0007
    names - it would catch the reach that has been seen and not the next one - so
    the invariant stays the positive one and the numbers themselves are graded by
    the cases in `scripts/tests/test_sov_snapshot.py`.
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
    functions = {node.name: node for node in ast.walk(tree)
                 if isinstance(node, ast.FunctionDef)}
    graded = []
    for name, expression in table:
        if expression is None:
            stray.append(f"{name}: its derivation could not be read from the declaration")
            continue
        adrift = _why_it_misses_the_record(name, expression, functions, bool(unbound))
        if name in WORKING_TREE:
            if adrift is None:
                stray.append(f"{name}: named as reading the working tree and it reaches "
                             f"sovsnapshot.{RECORD}; the exception outlived its reason")
            continue
        graded.append(name)
        if adrift:
            stray.append(adrift)
    stray.extend(_exceptions_are_live(table, graded))
    stray.extend(_paths_taken_off_the_record(tree))
    off_page = sorted(node.name for node in functions.values() if node.name != "page_text"
                      and any(_reads_the_page(n) for n in ast.walk(node)))
    if off_page:
        stray.append(f"{off_page} read the page off disk; page_text is the only "
                     "page read this module is allowed")
    return "; ".join(stray) if stray else None


def _why_it_misses_the_record(name: str, expression: ast.expr,
                              functions: dict[str, ast.FunctionDef],
                              unbound: bool) -> str | None:
    """Why this declared derivation does not reach the committed record, if it does not."""
    if (isinstance(expression, ast.Attribute) and isinstance(expression.value, ast.Name)
            and expression.value.id in READERS and not unbound):
        if expression.attr in NOT_AN_ANSWER:
            return (f"{name}: {expression.value.id}.{expression.attr} is a path and not "
                    "an answer, so declaring it derives nothing from the commit")
        return None
    body = functions.get(expression.id) if isinstance(expression, ast.Name) else None
    if body is None:
        return (f"{name}: its derivation is not a function declared in "
                f"{Path(claims.__file__).name}, so its source cannot be read here")
    if unbound or not _reaches(body, READERS):
        return (f"{name}: {expression.id} reaches none of {list(READERS)}, "
                "so it is not counting the commit at HEAD")
    return None


def _exceptions_are_live(table: list[tuple[str, ast.expr | None]],
                         graded: list[str]) -> list[str]:
    """Why the working-tree exceptions are not doing what they are declared for.

    An exception naming a claim the table does not declare grades nothing and
    reads as though it does, which is the same silence this guard exists to break.
    And a table where every claim is an exception is a guard satisfied by having
    nothing to check - the vacuity `_claim_table` returning empty already has a
    case for, one layer up.
    """
    declared = {name for name, _ in table}
    absent = [name for name in WORKING_TREE if name not in declared]
    stray = []
    if absent:
        stray.append(f"{absent} are named as reading the working tree and the claim "
                     "table declares no such claim, so the exception grades nothing")
    if table and not graded:
        stray.append("every declared claim is a named working-tree exception, so this "
                     "guard graded nothing")
    return stray


def _paths_taken_off_the_record(tree: ast.Module) -> list[str]:
    """Every path taken off a reader module anywhere in this source.

    Not only inside a declared derivation. The reach an independent reading
    demonstrated was `committed.ROOT` bound at module level and used from a
    deriver, so grading the derivations alone would have reported nothing.
    """
    taken = sorted({f"{node.value.id}.{node.attr}" for node in ast.walk(tree)
                    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                    and node.value.id in READERS and node.attr in NOT_AN_ANSWER})
    if not taken:
        return []
    return [f"{taken} taken in {Path(claims.__file__).name}; a reader's paths are not "
            "answers, and a derivation that globs one reads the working tree while "
            "satisfying this guard"]


def _reaches(node: ast.AST, names: tuple[str, ...]) -> bool:
    """Whether anything under this node takes an answer off one of these names.

    An answer, not any attribute. `committed.ROOT` is a `Path`, and counting it as
    a reach is what let a glob through it satisfy the invariant it defeats.
    """
    return any(isinstance(found, ast.Attribute) and isinstance(found.value, ast.Name)
               and found.value.id in names and found.attr not in NOT_AN_ANSWER
               for found in ast.walk(node))


def _reads_the_page(node: ast.AST) -> bool:
    """Whether this node names the snapshot page, by constant or by binding.

    Both spellings, because checking only the name `SNAPSHOT` let a deriver reach
    the page as `(ROOT / "CLAUDE.md").read_text(...)` and pass.
    """
    return ((isinstance(node, ast.Name) and node.id == "SNAPSHOT")
            or (isinstance(node, ast.Constant) and node.value == claims.SNAPSHOT.name))
