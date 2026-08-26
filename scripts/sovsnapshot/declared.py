"""What a committed module declares, counted without running it.

Split out of `sovsnapshot/committed.py` on 2026-08-26 at the 300-line budget, and
the seam is a real one rather than a line count: everything next door matches path
strings against a listing, and this reads Python. One claim needs it - the page
says `runs N checks`, and the check table is a tuple in a module rather than a
directory of files.

The objection this has to answer is on the record in `acceptance/accepted/A5.json`:
parsing a count out of HEAD would be a second implementation of a number the
repository already computes, which is the failure that made a draft count
conformance cases as 9 against the suite's own 20. The answer is that this refuses
every shape it cannot count exactly, so there is no shape where it can be
confidently wrong, and that `scripts/tests/test_sov_snapshot.py` grades it against
`len(CHECKS)` from the import on identical bytes.
"""

from __future__ import annotations

import ast

from sovsnapshot import committed
from sovsnapshot.committed import Underivable


def literal_length(path: str, name: str, what: str) -> int:
    """How many elements a committed module assigns to a plain tuple or list literal.

    Every refusal here opens with the same `{what} could not be read`, and so does
    the one `committed.blob_text` raises. An earlier round guaranteed that phrase by
    wrapping this function's exception at the call site, which produced "the check
    table could not be read: the check table could not be read from the commit at
    HEAD" - a stutter that appeared only when the messages were printed rather than
    reasoned about.
    """
    unreadable = f"{what} could not be read"
    try:
        module = ast.parse(committed.blob_text(path, what), filename=path)
    except SyntaxError as broken:
        raise Underivable(f"{unreadable}: {path} at HEAD does not parse: "
                          f"{broken}") from broken
    assigned = []
    for node in module.body:
        if (isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name)
                and node.target.id == name):
            # `CHECKS += (...)`. The literal is then not the whole of it, and
            # returning its length would be confidently short.
            raise Underivable(f"{unreadable}: {name} in {path} is added to after it "
                              "is assigned, so a literal's length is not its length")
        targets = node.targets if isinstance(node, ast.Assign) else (
            [node.target] if isinstance(node, ast.AnnAssign) else [])
        if any(isinstance(t, ast.Name) and t.id == name for t in targets):
            assigned.append(node)
    if not assigned:
        raise Underivable(f"{unreadable}: {path} at HEAD assigns no module-level {name}")
    if len(assigned) > 1:
        # An earlier version returned on the first match, so a later reassignment -
        # a platform branch, a debug override - was counted at the wrong length
        # rather than refused.
        raise Underivable(f"{unreadable}: {path} assigns {name} {len(assigned)} times "
                          "at module level, so which one runs cannot be read here")
    value = assigned[0].value
    if not isinstance(value, (ast.Tuple, ast.List)):
        raise Underivable(f"{unreadable}: {name} in {path} is a "
                          f"{type(value).__name__}, which has no length here")
    if any(isinstance(element, ast.Starred) for element in value.elts):
        raise Underivable(f"{unreadable}: {name} in {path} unpacks another "
                          "sequence, so its elements cannot be counted without "
                          "running it")
    return len(value.elts)
