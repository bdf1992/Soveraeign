"""Read JavaScript far enough to know a file is broken, without a parser.

An earlier reading of this repository withdrew three workflow checks and recorded the
reason as a ceiling: that without expression context a reader cannot tell a regex literal
from division, so bracket balance and string termination could not be graded. That was
convenient rather than true, and an independent reading refuted it. Two of the twenty-three
workflows were unparseable while the byte-level check that replaced those three reported
every file clean, and a test asserted it.

The standard method for a tokenizer without a parser is to resolve `/` by the last
significant token: a slash after a value - an identifier, a number, a string, a closing
bracket - is division, and a slash anywhere else opens a regex. That handles
`.replace(/"/g, "'")` and every other construction in this repository's workflows.

The honest limit, stated because the last statement of a limit here was wrong. This is a
lexer, not a parser. It sees that a string never closes, that a bracket never closes, and
that one closes the wrong opener. It cannot see a grammar error whose tokens are all
well-formed: a missing operator, a broken `${}` interpolation, an argument list with a
hole. Those pass here and are caught by a real engine or not at all.
"""

from __future__ import annotations

from typing import Iterator
import re

# A `/` following one of these is division. Following anything else it opens a regex.
#: Shared with `scan.masked`, so the package has one answer to "can a regex follow this".
from sovprompts.scan import _opens_regex  # noqa: E402
PAIRS = {")": "(", "]": "[", "}": "{"}
WORD = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_$")


class Broken(Exception):
    """The source cannot be read as JavaScript, with the line where reading stopped."""


def _string(text: str, index: int, line: int) -> tuple[int, int]:
    """Consume a quoted string; a template's `${...}` is consumed as ordinary text."""
    quote, start, index = text[index], line, index + 1
    while index < len(text):
        char = text[index]
        if char == "\\":
            line += text[index + 1:index + 2].count("\n")
            index += 2
            continue
        if char == quote:
            return index + 1, line
        if char == "\n":
            if quote != "`":
                raise Broken(f"line {start}: a {quote} string is not closed before the "
                             "line ends; an unescaped apostrophe inside one does this")
            line += 1
        index += 1
    raise Broken(f"line {start}: a {quote} string opens and never closes")


def _regex(text: str, index: int, line: int) -> tuple[int, int]:
    """Consume a regex literal, including a character class holding a delimiter."""
    start, index, klass = line, index + 1, False
    while index < len(text):
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == "[":
            klass = True
        elif char == "]":
            klass = False
        elif char == "\n":
            raise Broken(f"line {start}: a regex literal is not closed before the line ends")
        elif char == "/" and not klass:
            index += 1
            while index < len(text) and text[index] in "dgimsuvy":
                index += 1
            return index, line
        index += 1
    raise Broken(f"line {start}: a regex literal opens and never closes")


def significant(text: str) -> Iterator[tuple[str, str, int]]:
    """Every token that is not whitespace or a comment, as (kind, value, line)."""
    index, line, last = 0, 1, ("", "", 0)
    while index < len(text):
        char = text[index]
        if char == "\n":
            line += 1
            index += 1
            continue
        if char.isspace():
            index += 1
            continue
        if char == "/" and text[index + 1:index + 2] == "/":
            found = text.find("\n", index)
            index = len(text) if found == -1 else found
            continue
        if char == "/" and text[index + 1:index + 2] == "*":
            found = text.find("*/", index)
            if found == -1:
                raise Broken(f"line {line}: a block comment opens and never closes")
            line += text.count("\n", index, found)
            index = found + 2
            continue
        if char in "'\"`":
            end, line = _string(text, index, line)
            last = ("string", text[index:end], line)
            yield last
            index = end
            continue
        if char == "/":
            # Asked of `scan._opens_regex`, which is what the mask asks, so this reader
            # and `masked` cannot answer it differently. They used to: this decided from
            # its own token stream and the mask from the preceding character, and they
            # disagreed after a `.`, which let `concern./ { /g` hide a brace from one
            # reader and not the other. An independent reading used that to reach a
            # refusal this package had recorded as pre-empted by this very check. The
            # module's own comment already conceded the divergence and called both failing
            # closed "luck rather than design"; this is the design.
            divides = not _opens_regex(text, index)
            if divides:
                last = ("punct", "/", line)
                yield last
                index += 1
                continue
            end, line = _regex(text, index, line)
            last = ("regex", text[index:end], line)
            yield last
            index = end
            continue
        if char in WORD:
            start = index
            while index < len(text) and text[index] in WORD:
                index += 1
            value = text[start:index]
            last = ("number" if value[0].isdigit() else "word", value, line)
            yield last
            continue
        last = ("punct", char, line)
        yield last
        index += 1


def unreadable(text: str) -> str | None:
    """Why this source cannot be read as JavaScript, or None when it can."""
    stack: list[tuple[str, int]] = []
    try:
        for kind, value, line in significant(text):
            if kind != "punct":
                continue
            if value in "([{":
                stack.append((value, line))
            elif value in PAIRS:
                if not stack:
                    return f"line {line}: {value!r} closes nothing"
                opened, at = stack.pop()
                if opened != PAIRS[value]:
                    return (f"line {line}: {value!r} closes the {opened!r} opened on "
                            f"line {at}")
    except Broken as broken:
        return str(broken)
    if stack:
        opened, at = stack[-1]
        return f"line {at}: {opened!r} opens and never closes"
    return None


BROKEN_CONCAT = re.compile(r"['\"]\s*\+\s*\+\s*['\"]")


def broken_concatenation(source: str) -> bool:
    """`'a' + + 'b'` parses and yields NaN in the middle of a prompt.

    A syntax check passes it. Nothing lints these files. This is the one shape that bit
    while repairing them, so it is the one shape that is now refused.
    """
    return bool(BROKEN_CONCAT.search(source))
