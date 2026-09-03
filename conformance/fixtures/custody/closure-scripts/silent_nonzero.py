"""A module that exits non-zero and says nothing on either stream.

The same silence as the Phase 1.5 shape, wearing a different exit code. A rule
that reads only `exit 0 and empty stdout` admits this, and a participant running
it is left with no reading at all.
"""

from __future__ import annotations

import sys


def main() -> int:
    """Fail without saying why."""
    return 3


if __name__ == "__main__":
    sys.exit(main())
