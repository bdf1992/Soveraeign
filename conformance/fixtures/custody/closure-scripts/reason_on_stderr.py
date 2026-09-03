"""A module that writes its whole reading to stderr and exits non-zero.

The shape every declared command in this repository that exits non-zero
actually takes, and the reason the predicate is "wrote a reason anywhere"
rather than "printed to stdout" or "did not print a traceback". A failing
`-m unittest` suite is this shape, and it is a closure check refusing its
defective subject, which is the check working.
"""

from __future__ import annotations

import sys


def main() -> int:
    """Refuse, in writing, on the stream a test runner would use."""
    print("DEFECT: the subject this custody closes on is not done", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
