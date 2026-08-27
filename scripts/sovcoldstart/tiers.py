"""Reading a tier table safely, for the two modules that both need to.

One function, in its own module because `refusals` and `attribution` both read the table and
neither owns it. A tier row whose counts are not integers is not a row anyone can do
arithmetic on, and every check downstream assumes they can.
"""

from __future__ import annotations

from typing import Any


def _numbers(table: Any) -> list[dict[str, Any]]:
    """The tier rows, if they are shaped well enough to do arithmetic on."""
    if not isinstance(table, list):
        return []
    fields = ("asked", "scored", "hit", "unmeasured")
    return [row for row in table
            if isinstance(row, dict) and all(isinstance(row.get(f), int) for f in fields)]
