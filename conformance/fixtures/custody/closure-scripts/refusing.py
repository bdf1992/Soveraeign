"""A module that reports a defect and exits non-zero, which is the check working.

The positive case that keeps the live reading from treating every non-zero exit
as a defect: a closure check is supposed to refuse when its subject is bad.
"""

from __future__ import annotations


def main() -> int:
    """Refuse, loudly and in writing."""
    print("DEFECT: the subject this custody closes on is not done")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
