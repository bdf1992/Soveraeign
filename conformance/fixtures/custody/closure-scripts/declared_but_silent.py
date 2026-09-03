"""A module with an entry point that runs and prints nothing.

This is the case the static screen cannot see: `has_entry_point` is satisfied,
the command exits 0, and a participant reading its custody's declared closure
reads silence as a pass. Only `grade_live` catches it, which is why the two
readings are not redundant.
"""

from __future__ import annotations


def main() -> int:
    """Do work, report none of it."""
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
