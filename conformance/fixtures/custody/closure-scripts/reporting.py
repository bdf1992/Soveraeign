"""A module that reports when run, so its closure check is admissible.

The positive half of the SILENT_CLOSURE_CHECK pair.
"""

from __future__ import annotations


def main() -> int:
    """Print a reading, which is the whole point of a declared closure check."""
    print("reading: nothing outstanding")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
