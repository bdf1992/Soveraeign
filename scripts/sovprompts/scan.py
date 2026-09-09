"""Mask everything in a workflow that is not code, once, for every reader in this package.

Split from `calls.py` at the line ceiling and then rewritten, because an independent
reader that had seen none of the earlier work found the package holding eight partial
JavaScript scanners with six different rule sets for comments, regular expressions and
template literals. Two of the four defects it demonstrated were direct consequences of
that divergence: `_without_strings` stripped strings but not comments, so a comment
containing `witnessFrame(` removed a dispatch from the repo-wide rule, and it discarded
a whole template literal including its interpolations, so `` `${built.summary}` `` in the
oracle position resolved to nothing at all.

One mask fixes both by construction rather than by two more patches. `masked` replaces
the contents of comments, string literals, regular expressions and the literal parts of
template strings with spaces, preserving length so every offset stays valid, and keeps
`${...}` contents because a template interpolation is code and is exactly where an
account gets laundered.

The one ambiguity that has no answer here is whether `/` after `)` or `]` divides or
opens a regex; that needs a parser. `masked` takes the guess as a parameter and
`calls.scan_is_stable` runs both readings and refuses a file whose contents depend on it.
"""

from __future__ import annotations

from functools import lru_cache

#: A `/` here opens a regular expression rather than dividing: a regex may follow an
#: operator or an opening bracket, never a value.
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
        return True
    word = ""
    while back >= 0 and (source[back].isalnum() or source[back] in "_$"):
        word = source[back] + word
        back -= 1
    return word in BEFORE_REGEX_WORDS


def regex_end(source: str, index: int) -> int:
    """Where the regex literal opening at `index` ends, by the mask's own rule.

    Exposed so `render._literals` can skip a regex the same way `masked` does. It used to
    fall into a brace-depth scan instead, and `/'/.source` inside a prompt desynchronised
    it for the rest of the expression: an independent reading reached two refusals this
    package had recorded as unreachable, on JavaScript the lexer accepts. Two readers
    disagreeing about where a construct ends is what this module exists to stop.
    """
    index, in_class = index + 1, False
    while index < len(source):
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
    return min(index + 1, len(source))


def _blank(text: str) -> str:
    """The same length, with newlines kept so line numbers and offsets survive."""
    return "".join("\n" if char == "\n" else " " for char in text)


@lru_cache(maxsize=None)
def masked(source: str, permissive: bool = False) -> str:
    """`source` with every non-code region blanked and every offset preserved.

    Template interpolations stay: `${...}` is code, and blanking it is what let an
    account reach a witness through `` `${built.summary}` `` while every reader in this
    package reported the expression as empty.
    """
    out: list[str] = []
    index, length = 0, len(source)
    while index < length:
        char = source[index]
        if char == "/" and index + 1 < length and source[index + 1] in "/*":
            if source[index + 1] == "/":
                end = source.find("\n", index)
                end = length if end == -1 else end
            else:
                end = source.find("*/", index)
                end = length if end == -1 else end + 2
            out.append(_blank(source[index:end]))
            index = end
            continue
        if char == "/" and _opens_regex(source, index, permissive):
            start, index, in_class = index, index + 1, False
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
            index = min(index + 1, length)
            out.append(_blank(source[start:index]))
            continue
        if char == "`":
            out.append(" ")
            index += 1
            while index < length and source[index] != "`":
                if source[index] == "\\":
                    out.append("  ")
                    index += 2
                    continue
                if source[index:index + 2] == "${":
                    depth = 0
                    start = index
                    while index < length:
                        if source[index] == "{":
                            depth += 1
                        elif source[index] == "}":
                            depth -= 1
                            if depth == 0:
                                index += 1
                                break
                        index += 1
                    # Kept verbatim: an interpolation is code, and the account hides here.
                    out.append(source[start:index])
                    continue
                out.append("\n" if source[index] == "\n" else " ")
                index += 1
            out.append(" " if index < length else "")
            index += 1
            continue
        if char in "'\"":
            quote, start = char, index
            index += 1
            while index < length and source[index] != quote:
                index += 2 if source[index] == "\\" else 1
            index = min(index + 1, length)
            out.append(_blank(source[start:index]))
            continue
        out.append(char)
        index += 1
    return "".join(out)


#: Continuation shapes. A statement runs on when its line ends on one of these, or when
#: the next line opens on one; reading only the first truncated most prompts in this tree.
ENDS_OPEN = ("+", "?", ":", "&&", "||", ",", "=", "(", "[")
OPENS_OPEN = ("+", "?", ":", ".", "&&", "||")


def _statement(source: str, start: int) -> str:
    """The expression beginning at `start`, read to the end of its statement."""
    index, depth, quote = start, 0, ""
    while index < len(source):
        char = source[index]
        if quote:
            if char == "\\":
                index += 2
                continue
            if char == quote:
                quote = ""
            index += 1
            continue
        if char in "'\"`":
            quote = char
        elif char in "([{":
            depth += 1
        elif char in ")]}":
            if depth == 0:
                break
            depth -= 1
        elif char == ";" and depth == 0:
            # A statement ends at its own semicolon. Without this, the init clause of
            # `for (var i = 0; i < plan.operations.length; i++)` was returned whole as the
            # expression written into `i`, so every name in the *condition* counted as
            # something the counter carries: an independent reading measured 272 bindings
            # convicted as agent-derived on the pristine tree, a loop counter among them.
            break
        elif char == "\n" and depth == 0:
            ends = source[start:index].rstrip().endswith(ENDS_OPEN)
            if not ends and not source[index + 1:].lstrip().startswith(OPENS_OPEN):
                break
        index += 1
    return source[start:index]
