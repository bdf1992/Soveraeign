"""Read a workflow's bytes well enough to know which parts are code.

Split from `calls.py` at the line ceiling. That module decides which dispatches exist and
which agent each reaches; this one answers the question underneath both - where the code
is - and it is the layer two silent failures came from.

Both failures removed work from the check rather than adding it, which is the worst way
for a check to fail. An apostrophe in `// the grant's budget` opened a span that swallowed
six dispatches. A quote inside `.replace(/"/g, "'")` desynchronised the scan for the rest
of `sov-loop.js`, so every dispatch below it stopped existing. Comments and regular
expressions are skipped before strings for that reason.

One ambiguity has no answer here: whether `/` after `)` or `]` divides or opens a regex
needs a parser. Rather than guess and hope, `_string_spans` takes the guess as a
parameter, and `calls.scan_is_stable` runs both readings and refuses a file whose contents
depend on which one is used.
"""

from __future__ import annotations

from functools import lru_cache

#: A `/` here opens a regular expression rather than dividing. Standard JavaScript
#: disambiguation: a regex may follow an operator or an opening bracket, never a value.
BEFORE_REGEX = set("(,=:[!&|?{};+-*%~^<>") | {""}
BEFORE_REGEX_WORDS = frozenset({
    "return", "typeof", "case", "in", "of", "new", "delete", "void", "throw", "do", "else",
})


def _opens_regex(source: str, index: int, permissive: bool = False) -> bool:
    """Whether the `/` at `index` starts a regex literal rather than a division."""
    back = index - 1
    while back >= 0 and source[back] in " \t\r\n":
        back -= 1
    if back < 0:
        return True
    if source[back] in BEFORE_REGEX:
        return True
    if permissive and source[back] in ")]":
        # The other reading of the one genuinely ambiguous case. `a[0] / x / y` is
        # division and `a[0]\n/re/.test(s)` is a regex, and no rule settles both without
        # a parser. Running the scan under both readings is what makes the disagreement
        # visible instead of silent.
        return True
    word = ""
    while back >= 0 and (source[back].isalnum() or source[back] in "_$"):
        word = source[back] + word
        back -= 1
    return word in BEFORE_REGEX_WORDS


@lru_cache(maxsize=None)
def _string_spans(source: str, permissive: bool = False) -> tuple[tuple[int, int], ...]:
    """Where the string literals are, so prose is not enumerated as code.

    This repository's backlog workflow says "judging agent(s)" in a sentence. Enumerating
    the raw bytes reads that as a dispatch.

    Comments and regular expressions are skipped before strings, and both were found the
    hard way. An apostrophe in `// the grant's budget` opens a span that swallows the next
    lines of code. And `.replace(/"/g, "'")` in `sov-loop.js` puts a quote inside a regex:
    reading it as a string opener desynchronised the scan for the remaining 1,800
    characters of the file, so every dispatch below it stopped existing. Both failures are
    silent and both remove work from the check rather than adding it, which is why this
    scanner is written against the two constructions that defeat it rather than against
    the common case.
    """
    spans: list[tuple[int, int]] = []
    index, length = 0, len(source)
    while index < length:
        char = source[index]
        if char == "/" and index + 1 < length and source[index + 1] in "/*":
            if source[index + 1] == "/":
                found = source.find("\n", index)
            else:
                found = source.find("*/", index)
                found = found + 2 if found != -1 else -1
            index = length if found == -1 else found
            continue
        if char == "/" and _opens_regex(source, index, permissive):
            index += 1
            in_class = False
            while index < length:
                here = source[index]
                if here == "\\":
                    index += 2
                    continue
                if here == "[":
                    in_class = True
                elif here == "]":
                    in_class = False
                elif here == "/" and not in_class:
                    break
                elif here == "\n":
                    break
                index += 1
            index += 1
            continue
        if char in "'\"`":
            quote, start = char, index
            index += 1
            while index < length and source[index] != quote:
                index += 2 if source[index] == "\\" else 1
            spans.append((start, min(index, length - 1)))
        index += 1
    # A tuple because this is cached; a list would let one caller's edit reach the next.
    return tuple(spans)


def _inside(spans: tuple[tuple[int, int], ...], position: int) -> bool:
    return any(start <= position <= end for start, end in spans)
