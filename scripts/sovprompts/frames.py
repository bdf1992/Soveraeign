"""Read a function whose prompt is an array of blocks, in the order an evaluator gets them.

Split from `render.py` at the line ceiling `ENGINEERING.md` sets, along the boundary that
was already there: that module reads what one expression or one function says, this reads
the shape a frame is built in. A frame is an ordered sequence of blocks joined into one
string, and everything here exists because the order matters as much as the content -
`].reverse().join(...)` is one word, and it made the frame open on its last block while
every ordering rule still graded the source order and passed.
"""

from __future__ import annotations

from sovprompts.render import Unreadable, _literals, returned
from sovprompts.scan import masked


def array_join_source(expr: str) -> str | None:
    """`[a, b, c].join(sep)` rewritten as `a + sep + b + sep + c`, or None for another shape.

    Returned as source rather than as rendered text, so a caller can splice them back into
    an expression `_literals` reads. A prompt helper assembled this way used to render as
    one opaque expression: an independent reading built `witnessBrief(...)` returning
    joined blocks, spliced it where the frame had been, and its whole delivered text -
    which told the evaluator to take the builder's scope as given and not to pin - was
    never read by any rule.
    """
    code = masked(expr)
    start = len(code) - len(code.lstrip())
    if not code[start:].startswith("["):
        return None
    index, depth = start, 0
    while index < len(code):
        if code[index] == "[":
            depth += 1
        elif code[index] == "]":
            depth -= 1
            if depth == 0:
                break
        index += 1
    else:
        return None
    after = code[index + 1:].lstrip()
    if not after.startswith(".join"):
        # Same refusal `blocks` makes: what sits between the array and `.join` decides the
        # order an evaluator reads in, and this reader does not evaluate it.
        return None
    open_paren = code.index("(", index + 1)
    close, depth = open_paren, 0
    while close < len(code):
        if code[close] == "(":
            depth += 1
        elif code[close] == ")":
            depth -= 1
            if depth == 0:
                break
        close += 1
    else:
        return None
    # The separator is delivered text too. Dropping it made the rendered frame and the
    # delivered prompt differ by exactly the blank lines between blocks, which is enough
    # to defeat a comparison between them.
    separator = expr[open_paren + 1:close].strip() or "''"
    inner, code_inner = expr[start + 1:index], code[start + 1:index]
    parts, depth, cut = [], 0, 0
    for position, char in enumerate(code_inner):
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        elif char == "," and depth == 0:
            parts.append(inner[cut:position])
            cut = position + 1
    parts.append(inner[cut:])
    kept = [part for part in parts if part.strip()]
    return (" + " + separator + " + ").join(kept) if kept else None


def blocks(source: str, name: str) -> list[str]:
    """The blocks a `return [ ... ].join(...)` function produces, in order."""
    body = returned(source, name)
    if not masked(body).lstrip().startswith("["):
        raise Unreadable(f"{name} does not return an array of blocks")
    start = len(body) - len(body.lstrip())
    index, depth = start, 0
    while index < len(body):
        if body[index] == "[":
            depth += 1
        elif body[index] == "]":
            depth -= 1
            if depth == 0:
                break
        index += 1
    else:
        raise Unreadable(f"{name}'s return array is unterminated")
    after = masked(body[index + 1:]).lstrip()
    if not after.startswith(".join"):
        # What sits between the array and `.join` decides the order the evaluator reads in,
        # and this reader does not evaluate it. `].reverse().join(...)` is one word, and it
        # made the frame open on its last block while every ordering rule still graded the
        # source order and passed. Refused rather than read.
        raise Unreadable(
            f"{name}'s blocks are transformed before they are joined, so the order they "
            "reach an evaluator in is not the order they are written in")
    inner = body[start + 1:index]
    # Where the separating commas are is a structural question, and it is answered on the
    # one mask rather than by a scan of this module's own. This split used to be a private
    # character scan that did not skip comments, so a comma inside `/* first, always */`
    # broke one block into two and convicted legal JavaScript. `masked` preserves length,
    # so every offset below is valid in `inner` itself.
    code = masked(inner)
    parts, depth, cut = [], 0, 0
    for position, char in enumerate(code):
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        elif char == "," and depth == 0:
            parts.append(inner[cut:position])
            cut = position + 1
    parts.append(inner[cut:])
    return [_literals(part) for part in parts if part.strip()]


def rendered(source: str, name: str) -> str:
    """Everything the function's blocks say, joined."""
    return "\n\n".join(blocks(source, name))

