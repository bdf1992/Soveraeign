"""Extract the ``soveraeign-ticket/v1`` metadata block from an issue body.

The block is a fenced ``yaml`` region at the top of the body. This module reads
a deliberately small YAML subset - scalars, block sequences, flow sequences, and
one level of nested mapping - because the repository carries no runtime
dependency and the metadata contract needs no more than that. Anything outside
the subset raises ``MetadataError`` instead of being guessed at; a parse that
succeeds is evidence about shape only, never about standing.
"""

from __future__ import annotations

from typing import Any
import re


FENCE = re.compile(r"```ya?ml\s*\n(.*?)\n```", re.DOTALL)
FLOW = re.compile(r"^\[(.*)\]$")


class MetadataError(ValueError):
    """The body carries no metadata block, or one outside the parsed subset."""


def extract_block(body: str) -> str:
    """Return the first fenced YAML block of an issue body."""
    match = FENCE.search(body or "")
    if not match:
        raise MetadataError("no fenced yaml metadata block found")
    return match.group(1)


def _scalar(raw: str) -> Any:
    text = raw.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]
    if text in ("null", "~", ""):
        return None
    if text == "true":
        return True
    if text == "false":
        return False
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    if re.fullmatch(r"-?\d+\.\d+", text):
        return float(text)
    if text[0] in "&*|>{":
        raise MetadataError(f"value outside the parsed YAML subset: {text!r}")
    return text


def _flow_sequence(text: str) -> list[Any]:
    inner = FLOW.fullmatch(text).group(1).strip()
    if not inner:
        return []
    return [_scalar(item) for item in inner.split(",")]


def _lines(block: str) -> list[tuple[int, str]]:
    out = []
    for raw in block.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if "\t" in raw:
            raise MetadataError("tab indentation is outside the parsed YAML subset")
        out.append((len(raw) - len(raw.lstrip(" ")), raw.strip()))
    return out


def _split_key(text: str) -> tuple[str, str]:
    if ":" not in text:
        raise MetadataError(f"line outside the parsed YAML subset: {text!r}")
    key, _, value = text.partition(":")
    return key.strip(), value.strip()


def parse_block(block: str) -> dict[str, Any]:
    """Parse the metadata subset into a plain dictionary."""
    lines = _lines(block)
    result: dict[str, Any] = {}
    index = 0
    while index < len(lines):
        indent, text = lines[index]
        if indent != 0:
            raise MetadataError(f"unexpected indentation at {text!r}")
        if text.startswith("- "):
            raise MetadataError("a top-level sequence is not a metadata block")
        key, value = _split_key(text)
        if value:
            result[key] = _flow_sequence(value) if FLOW.fullmatch(value) else _scalar(value)
            index += 1
            continue
        child, index = _parse_child(lines, index + 1)
        result[key] = child
    return result


def _parse_child(lines: list[tuple[int, str]], index: int) -> tuple[Any, int]:
    """Read the block sequence or nested mapping owned by the preceding key."""
    if index >= len(lines) or lines[index][0] == 0:
        return None, index
    depth = lines[index][0]
    if lines[index][1].startswith("- "):
        items = []
        while index < len(lines) and lines[index][0] == depth and lines[index][1].startswith("- "):
            items.append(_scalar(lines[index][1][2:]))
            index += 1
        return items, index
    mapping: dict[str, Any] = {}
    while index < len(lines) and lines[index][0] == depth:
        key, value = _split_key(lines[index][1])
        if value:
            mapping[key] = _flow_sequence(value) if FLOW.fullmatch(value) else _scalar(value)
            index += 1
            continue
        nested, index = _parse_child(lines, index + 1)
        mapping[key] = nested
    return mapping, index


def parse_body(body: str) -> dict[str, Any]:
    """Extract and parse the metadata block of one issue body."""
    return parse_block(extract_block(body))
