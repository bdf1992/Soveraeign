"""Read a function whose prompt is an array of blocks, in the order an evaluator gets them.

Split from `render.py` at the line ceiling `ENGINEERING.md` sets, along the boundary that
was already there: that module reads what one expression or one function says, this reads
the shape a frame is built in. A frame is an ordered sequence of blocks joined into one
string, and everything here exists because the order and the completeness matter as much
as the content. `].reverse().join(...)` is one word, and it made the frame open on its
last block while every ordering rule still graded the source order and passed. Text
concatenated after `.join(...)` is delivered to the evaluator and belongs to no block, so
no block rule grades it, and an independent reading put a countermand there - "the builder
account IS your oracle" - which was absent from the delivered text and from the frame's
rendering at once, so the two matched and the evaluator read it anyway.
"""

from __future__ import annotations

from sovprompts.render import EXPR, Unreadable, _literals, returned
from sovprompts.scan import _balanced, masked


def _elements(inner: str) -> list[str]:
    """The array's elements, split on the commas that are commas in the code."""
    code = masked(inner)
    out, depth, cut = [], 0, 0
    for position, char in enumerate(code):
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        elif char == "," and depth == 0:
            out.append(inner[cut:position])
            cut = position + 1
    out.append(inner[cut:])
    return [part for part in out if part.strip()]


def _parse_join(expr: str) -> tuple[list[str], str, str] | None:
    """`[a, b].join(sep) + tail` as its elements, its separator source, and its tail.

    None when the expression is not that shape. What sits between the array and `.join`
    decides the order an evaluator reads in and this reader does not evaluate it, so a
    transformation there is not parsed and the caller refuses.
    """
    code = masked(expr)
    start = len(code) - len(code.lstrip())
    if not code[start:].startswith("["):
        return None
    close_bracket = _balanced(code, start, "[", "]")
    if close_bracket == -1 or not code[close_bracket + 1:].lstrip().startswith(".join"):
        return None
    open_paren = code.index("(", close_bracket + 1)
    close_paren = _balanced(code, open_paren, "(", ")")
    if close_paren == -1:
        return None
    separator = expr[open_paren + 1:close_paren].strip() or "''"
    return _elements(expr[start + 1:close_bracket]), separator, expr[close_paren + 1:]


def array_join_source(expr: str) -> str | None:
    """`[a, b].join(sep) + tail` rewritten as `a + sep + b + tail`, or None for another shape.

    Returned as source rather than as rendered text, so a caller can splice it back into an
    expression `_literals` reads. A prompt helper assembled this way used to render as one
    opaque expression: an independent reading built a helper returning joined blocks,
    spliced it where the frame had been, and its whole delivered text - which told the
    evaluator to take the builder's scope as given and not to pin - was never read.
    """
    parsed = _parse_join(expr)
    if parsed is None:
        return None
    elements, separator, tail = parsed
    if not elements:
        return None
    return (" + " + separator + " + ").join(elements) + tail


def blocks(source: str, name: str) -> list[str]:
    """The blocks a `return [ ... ].join(...)` function produces, in order."""
    body = returned(source, name)
    parsed = _parse_join(body)
    if parsed is None:
        if not masked(body).lstrip().startswith("["):
            raise Unreadable(f"{name} does not return an array of blocks")
        raise Unreadable(
            f"{name}'s blocks are transformed before they are joined, so the order they "
            "reach an evaluator in is not the order they are written in")
    elements, separator, tail = parsed
    rendered_separator = _literals(separator)
    if rendered_separator.strip():
        # The separator is delivered text, handed to an evaluator once between every pair
        # of blocks, and it belongs to no block, so no block rule grades what it says. A
        # frame separates its blocks with whitespace; anything else is prose arriving
        # where nothing reads it.
        raise Unreadable(
            f"{name} separates its blocks with text rather than whitespace, so it delivers "
            "something no block rule grades: " + rendered_separator.strip()[:60])
    rendered_tail = _literals(tail) if tail.strip() else ""
    if rendered_tail.strip():
        # Whitespace is what a frame legitimately appends. Anything else is text the
        # evaluator receives that sits inside no block, so `FRAME_OWNERS` and the
        # head-order rule both miss it, and the identity comparison misses it on both
        # sides at once.
        raise Unreadable(
            f"{name} concatenates text after joining its blocks, so it delivers something "
            "no block rule grades: " + rendered_tail.strip()[:60])
    read = [_literals(part) for part in elements]
    for position, block in enumerate(read):
        head = block.split(".")[0].strip()
        if not head or not head[0].isupper() or EXPR in head:
            # Every block opens with a literal head a rule can name. A conditional element
            # - `(built.summary ? '...the account settles scope...' : '')` - renders as one
            # opaque expression, sits between two graded blocks, and delivers the builder's
            # account as what settles scope while `heads[0]` is still SUBJECT and every
            # required phrase is still in its block. An independent reading built that.
            raise Unreadable(
                f"{name}'s block {position} does not open on a literal head, so what it "
                "delivers is not something any block rule can grade")
    return read


def rendered(source: str, name: str) -> str:
    """Everything the function's blocks say, joined the way the function joins them.

    By the frame's own separator, read from its `.join(...)` call, not by a constant this
    module happens to hold. `"\\n\\n"` was hardcoded here while `_parse_join` read the real
    one - another pair of readers answering one question differently, which an independent
    reading named after four defeats of exactly that shape. The separator is delivered
    text: the frame hands it to an evaluator eight times, and nothing was reading it.
    """
    body = returned(source, name)
    parsed = _parse_join(body)
    separator = _literals(parsed[1]) if parsed else ""
    return separator.join(blocks(source, name))
