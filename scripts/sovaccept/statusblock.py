"""Bounded reader for the STATUS.yaml constructs the acceptance register uses.

STATUS.yaml is human-authored YAML and stays that way, so this reads the exact
subset it uses -- top-level scalars, string sequences, sequences of flat mappings,
and one level of nested mapping -- and refuses every other construct by name. A
reader that guessed at an unadmitted construct would report a passing audit over
text it did not understand, which is the failure ``AGENTS.md`` refuses when it
forbids treating a green build as authority.
"""

from __future__ import annotations

import re

KEY_LINE = re.compile(r"^(?P<indent> *)(?P<key>[A-Za-z_][A-Za-z0-9_]*):(?P<rest>.*)$")
ITEM_LINE = re.compile(r"^(?P<indent> *)- (?P<value>.*)$")
NULL_LITERALS = frozenset({"", "null", "Null", "NULL", "~"})
REFUSED = {
    "\t": "tab indentation",
    "&": "anchor",
    "*": "alias",
    "!!": "explicit tag",
}


class StatusBlockError(ValueError):
    """STATUS.yaml used a construct this reader does not admit."""


def _scalar(raw: str) -> str | None:
    """One scalar value, with a matched quote pair stripped and null literals mapped."""
    value = raw.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    if value in NULL_LITERALS:
        return None
    return value


def _refuse(line: str, number: int) -> None:
    """Raise when a line uses a construct outside the admitted subset."""
    stripped = line.strip()
    if "\t" in line:
        raise StatusBlockError(f"line {number}: {REFUSED['\t']} is not admitted")
    for marker in ("&", "*", "!!"):
        if stripped.startswith(marker):
            raise StatusBlockError(f"line {number}: {REFUSED[marker]} is not admitted")
    if stripped.endswith((" |", " >")) or stripped in {"|", ">"}:
        raise StatusBlockError(f"line {number}: multi-line scalar is not admitted")


def parse(text: str) -> dict[str, object]:
    """Parse the admitted subset into scalars, string lists, and lists of mappings."""
    result: dict[str, object] = {}
    container: object = None
    for number, line in enumerate(text.replace("\r\n", "\n").split("\n"), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        _refuse(line, number)
        item = ITEM_LINE.match(line)
        if item and item.group("indent"):
            container = _open_item(container, item, number)
            continue
        match = KEY_LINE.match(line)
        if not match:
            raise StatusBlockError(f"line {number}: not an admitted key or sequence item")
        indent, key, rest = match.group("indent"), match.group("key"), match.group("rest")
        if indent:
            container = _nested_key(container, key, rest, number)
            continue
        value = rest.strip()
        if value:
            result[key] = _scalar(value)
            container = None
            continue
        result[key] = []
        container = result[key]
    return result


def _open_item(container: object, item: re.Match[str], number: int) -> object:
    """Start a sequence item: a bare scalar, or the first key of a flat mapping."""
    if not isinstance(container, list):
        inner = getattr(container, "_owner", None)
        if not isinstance(inner, list):
            raise StatusBlockError(f"line {number}: sequence item outside a sequence")
        container = inner
    value = item.group("value")
    nested = KEY_LINE.match(value)
    if nested:
        entry: dict[str, object] = {nested.group("key"): _scalar(nested.group("rest"))}
        container.append(entry)
        return _Mapping(entry, container)
    container.append(_scalar(value))
    return container


def _nested_key(container: object, key: str, rest: str, number: int) -> object:
    """Continue a flat mapping inside a sequence item, or open a nested mapping."""
    if isinstance(container, _Mapping):
        container.entry[key] = _scalar(rest)
        return container
    if isinstance(container, list):
        if container:
            raise StatusBlockError(f"line {number}: nested key inside a scalar sequence")
        entry: dict[str, object] = {key: _scalar(rest)}
        container.append(entry)
        return _Mapping(entry, container)
    raise StatusBlockError(f"line {number}: nested key outside a mapping")


class _Mapping:
    """The mapping currently being filled inside a sequence item."""

    def __init__(self, entry: dict[str, object], owner: list[object]) -> None:
        self.entry = entry
        self._owner = owner


def entries(parsed: dict[str, object], key: str) -> list[dict[str, object]]:
    """Sequence-of-mappings value for ``key``, or an empty list when absent."""
    value = parsed.get(key)
    if value in (None, [], "[]"):
        return []
    if not isinstance(value, list) or not all(isinstance(row, dict) for row in value):
        raise StatusBlockError(f"{key} is not a sequence of mappings")
    return [row for row in value if isinstance(row, dict)]
