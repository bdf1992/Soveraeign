"""An address below the file: `path#fragment`, resolved to the bytes it means.

A receipt, a clarity basis, or a diagram view that digests a whole file goes stale the
moment any part of that file moves, including a part it never read. Four gates shared
that shape on 2026-09-07: witness receipts, clarity bases, diagram views and the
discovery reader. This module gives them one finer address. A bare path still means the file's
exact bytes, so every existing address keeps its meaning.

Fragments, chosen by the file's suffix:

- `.json`: a JSON pointer (RFC 6901) whose steps may select a list element by field,
  `/custodies[custody_id=custody:x/y]/members[address=a.py]/note`; a slash inside the
  brackets belongs to the value. The bytes are the node's canonical JSON: sorted keys,
  no spaces, UTF-8.
- `.yaml` and `.yml`: a top-level key; the bytes are the key's block from its own line
  to the line before the next top-level key, without trailing blank lines and
  column-zero comments, which introduce the next key. No YAML parser is needed and
  none is used.
- `.md`: a heading's text, exact after the `#` marks and before any closing marks; the
  bytes are the section from the heading line to the line before the next heading of the
  same or a higher level. Lines inside fenced code blocks are never headings.

Every refusal names itself: `FRAGMENT_UNSUPPORTED`, `FRAGMENT_MALFORMED`,
`FRAGMENT_NOT_FOUND`, `SELECTOR_AMBIGUOUS`. Nothing here reads outside `root`; the
path half is the caller's to contain, and `split` hands it back untouched.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any
import json
import re

DIGEST_PREFIX = "sha256:"
SEPARATOR = "#"
TOP_LEVEL_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*:")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
STEP = re.compile(r"^(?P<name>[^\[\]]*)(?:\[(?P<key>[^=\]]+)=(?P<value>[^\]]*)\])?$")


class AddressError(ValueError):
    """A fragment that cannot be resolved, carrying the refusal's name in `code`."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code


def split(address: str) -> tuple[str, str | None]:
    """The path half and the fragment half, or None when the address is a whole file."""
    path, sep, fragment = address.partition(SEPARATOR)
    return path, (fragment if sep else None)


def canonical(node: Any) -> bytes:
    """The one byte form of a JSON node, so two readers of the same node agree."""
    return json.dumps(node, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8")


def _unescape(token: str) -> str:
    return token.replace("~1", "/").replace("~0", "~")


def _select(node: Any, key: str, value: str, where: str) -> Any:
    if not isinstance(node, list):
        raise AddressError("FRAGMENT_NOT_FOUND", f"{where} is not a list to select from")
    found = [item for item in node
             if isinstance(item, dict) and key in item and str(item[key]) == value]
    if not found:
        raise AddressError("FRAGMENT_NOT_FOUND", f"no element of {where} has {key}={value}")
    if len(found) > 1:
        raise AddressError("SELECTOR_AMBIGUOUS",
                           f"{len(found)} elements of {where} have {key}={value}")
    return found[0]


def _steps(pointer: str) -> list[str]:
    """Split a pointer on `/` outside brackets, so a selector value may hold a slash."""
    steps: list[str] = []
    current = ""
    depth = 0
    for char in pointer:
        if char == "[":
            depth += 1
        elif char == "]" and depth:
            depth -= 1
        if char == "/" and not depth:
            steps.append(current)
            current = ""
        else:
            current += char
    steps.append(current)
    return steps


def json_node(document: Any, pointer: str) -> Any:
    """Walk a pointer with optional `[key=value]` selectors and return the node."""
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise AddressError("FRAGMENT_MALFORMED", f"a JSON pointer starts with '/': {pointer!r}")
    node = document
    where = ""
    for raw in _steps(pointer[1:]):
        step = STEP.match(raw)
        if step is None:
            raise AddressError("FRAGMENT_MALFORMED", f"unreadable step {raw!r}")
        name = _unescape(step.group("name"))
        if name:
            where += "/" + name
            if isinstance(node, dict):
                if name not in node:
                    raise AddressError("FRAGMENT_NOT_FOUND", f"no key {where}")
                node = node[name]
            elif isinstance(node, list):
                if not name.isdigit() or int(name) >= len(node):
                    raise AddressError("FRAGMENT_NOT_FOUND", f"no index {where}")
                node = node[int(name)]
            else:
                raise AddressError("FRAGMENT_NOT_FOUND", f"{where} is below a scalar")
        if step.group("key") is not None:
            node = _select(node, _unescape(step.group("key")), step.group("value"), where or "/")
            where += f"[{step.group('key')}={step.group('value')}]"
    return node


def yaml_block(text: str, key: str) -> bytes:
    """A top-level key's block, read by line shape and never by a YAML parser."""
    lines = text.split("\n")
    starts = [i for i, line in enumerate(lines) if TOP_LEVEL_KEY.match(line)
              and line.split(":", 1)[0] == key]
    if not starts:
        raise AddressError("FRAGMENT_NOT_FOUND", f"no top-level key {key!r}")
    if len(starts) > 1:
        raise AddressError("SELECTOR_AMBIGUOUS",
                           f"top-level key {key!r} appears {len(starts)} times")
    start = starts[0]
    end = next((i for i in range(start + 1, len(lines)) if TOP_LEVEL_KEY.match(lines[i])),
               len(lines))
    while end > start + 1 and (not lines[end - 1].strip() or lines[end - 1].startswith("#")):
        end -= 1
    return "\n".join(lines[start:end]).encode("utf-8")


def markdown_section(text: str, heading: str) -> bytes:
    """A heading's section, to the line before the next heading at its level or above."""
    lines = text.split("\n")
    headings = _headings(lines)
    matches = [(i, level) for i, level, text_ in headings if text_ == heading]
    if not matches:
        raise AddressError("FRAGMENT_NOT_FOUND", f"no heading {heading!r}")
    if len(matches) > 1:
        raise AddressError("SELECTOR_AMBIGUOUS",
                           f"heading {heading!r} appears {len(matches)} times")
    start, level = matches[0]
    end = next((i for i, later, _ in headings if i > start and later <= level), len(lines))
    return "\n".join(lines[start:end]).encode("utf-8")


def _headings(lines: list[str]) -> list[tuple[int, int, str]]:
    """Every heading outside a fenced code block, as (line index, level, text)."""
    found: list[tuple[int, int, str]] = []
    fenced = False
    for index, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        match = HEADING.match(line)
        if match:
            found.append((index, len(match.group(1)), match.group(2)))
    return found


def resolve_bytes(path: Path, fragment: str | None) -> bytes:
    """The bytes an address means, given its already-contained path and its fragment."""
    raw = path.read_bytes()
    if fragment is None:
        return raw
    suffix = path.suffix.lower()
    if suffix not in (".json", ".yaml", ".yml", ".md"):
        raise AddressError("FRAGMENT_UNSUPPORTED",
                           f"{path.name}: a fragment is defined for .json, .yaml and .md only")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as broken:
        raise AddressError("FRAGMENT_MALFORMED", f"{path.name} is not UTF-8: {broken}")
    if suffix == ".json":
        try:
            document = json.loads(text)
        except ValueError as broken:
            raise AddressError("FRAGMENT_MALFORMED", f"{path.name} is not JSON: {broken}")
        return canonical(json_node(document, fragment))
    if suffix == ".md":
        return markdown_section(text, fragment)
    return yaml_block(text, fragment)


def resolve(root: Path, address: str) -> bytes:
    """The bytes at a repository-relative address, fragment and all."""
    path, fragment = split(address)
    return resolve_bytes(root / path, fragment)


def digest(root: Path, address: str) -> str:
    """`sha256:` over the bytes an address means."""
    return DIGEST_PREFIX + sha256(resolve(root, address)).hexdigest()
