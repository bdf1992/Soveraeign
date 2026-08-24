"""Bounded YAML-subset reader for the metadata block at the top of an issue body.

The reader accepts only the constructs the ticket contract uses: a single document of
string-valued keys, block sequences, flow sequences, and one level of nested mapping.
Every other construct is refused by name rather than approximated, so a ticket cannot
acquire meaning the contract never declared. Scalars are returned as strings or null
because ``contracts/issue-metadata.schema.json`` declares no numeric or boolean field.
"""

from __future__ import annotations

import re

FENCE = re.compile(r"^```[ \t]*(?:yaml|yml)[ \t]*$", re.IGNORECASE)
CLOSING_FENCE = re.compile(r"^```[ \t]*$")
HEADING = re.compile(r"^#{1,6} ")
KEY_LINE = re.compile(r"^(?P<indent> *)(?P<key>[A-Za-z_][A-Za-z0-9_]*):(?P<rest>.*)$")
ITEM_LINE = re.compile(r"^(?P<indent> *)- (?P<value>.*)$")
NULL_LITERALS = frozenset({"null", "Null", "NULL", "~", ""})
REFUSED_CONSTRUCTS = {
    "\t": "tab indentation",
    "---": "explicit document marker",
    "&": "anchor",
    "*": "alias",
    "!!": "explicit tag",
}


class TicketBlockError(ValueError):
    """A ticket metadata block used a construct the contract does not admit."""


def extract_block(body: str) -> str:
    """Return the first fenced YAML block in ``body``.

    Only blank lines and markdown headings may precede the block. Prose before the
    metadata means the issue leads with narrative rather than its contract, so an issue
    without a leading machine-readable block is not a ticket under the contract.
    """
    lines = body.replace("\r\n", "\n").split("\n")
    start = None
    for index, line in enumerate(lines):
        if FENCE.match(line):
            start = index + 1
            break
        if line.strip() and not HEADING.match(line):
            break
    if start is None:
        raise TicketBlockError("issue body does not open with a fenced yaml metadata block")
    for index in range(start, len(lines)):
        if CLOSING_FENCE.match(lines[index]):
            return "\n".join(lines[start:index])
    raise TicketBlockError("fenced yaml metadata block is not closed")


def _scalar(raw: str) -> str | None:
    """Return one scalar, stripping a matched quote pair and mapping null literals.

    A quoted value is always a string; an unquoted ``null``, ``~``, or empty value is
    the YAML null the ticket schema admits for an unobserved field.
    """
    value = raw.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    if value in NULL_LITERALS:
        return None
    return value


def _flow_sequence(raw: str) -> list[str | None]:
    """Parse a single-line flow sequence such as ``[a, "#4", c]``."""
    inner = raw.strip()[1:-1].strip()
    if not inner:
        return []
    parts: list[str | None] = []
    depth = 0
    current = ""
    quote = ""
    for char in inner:
        if quote:
            current += char
            if char == quote:
                quote = ""
            continue
        if char in "\"'":
            quote = char
            current += char
            continue
        if char in "[{":
            depth += 1
        elif char in "]}":
            depth -= 1
        if char == "," and depth == 0:
            parts.append(current)
            current = ""
            continue
        current += char
    parts.append(current)
    return [_scalar(part) for part in parts]


def _refuse_unsupported(line: str, number: int) -> None:
    """Raise when a line uses a construct outside the admitted subset."""
    stripped = line.strip()
    for marker, name in REFUSED_CONSTRUCTS.items():
        if marker == "\t" and "\t" in line:
            raise TicketBlockError(f"line {number}: {name} is not admitted")
        if marker != "\t" and stripped.startswith(marker):
            raise TicketBlockError(f"line {number}: {name} is not admitted")
    if stripped.endswith((" |", " >", ":|", ":>")) or stripped in {"|", ">"}:
        raise TicketBlockError(f"line {number}: multi-line scalar is not admitted")


def parse_block(text: str) -> dict[str, object]:
    """Parse the admitted YAML subset into a mapping of strings, lists, and mappings."""
    result: dict[str, object] = {}
    lines = text.replace("\r\n", "\n").split("\n")
    current_key: str | None = None
    pending: list[object] | dict[str, object] | None = None
    for number, line in enumerate(lines, 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        _refuse_unsupported(line, number)
        item = ITEM_LINE.match(line)
        if item and current_key is not None:
            if not isinstance(pending, list):
                raise TicketBlockError(f"line {number}: sequence item outside a sequence")
            pending.append(_scalar(item.group("value")))
            continue
        match = KEY_LINE.match(line)
        if not match:
            raise TicketBlockError(f"line {number}: not an admitted key or sequence item")
        indent, key, rest = match.group("indent"), match.group("key"), match.group("rest")
        if indent:
            if not isinstance(pending, dict):
                raise TicketBlockError(f"line {number}: nested key outside a nested mapping")
            pending[key] = _flow_sequence(rest) if rest.strip().startswith("[") else _scalar(rest)
            continue
        if key in result:
            raise TicketBlockError(f"line {number}: duplicate key {key!r}")
        value = rest.strip()
        if not value:
            pending = []
            result[key] = pending
            current_key = key
            _stage_nested(lines, number, key, result)
            pending = result[key]
            continue
        if value.startswith("["):
            result[key] = _flow_sequence(value)
        elif value.startswith("{"):
            raise TicketBlockError(f"line {number}: flow mapping is not admitted")
        else:
            result[key] = _scalar(value)
        current_key = key
        pending = None
    return result


def _stage_nested(lines: list[str], number: int, key: str, result: dict[str, object]) -> None:
    """Replace an empty value with a mapping when the next indented line is a key."""
    for following in lines[number:]:
        if not following.strip() or following.lstrip().startswith("#"):
            continue
        if ITEM_LINE.match(following):
            return
        match = KEY_LINE.match(following)
        if match and match.group("indent"):
            result[key] = {}
        return


def load_ticket(body: str) -> dict[str, object]:
    """Extract and parse the ticket metadata block from a complete issue body."""
    return parse_block(extract_block(body))
