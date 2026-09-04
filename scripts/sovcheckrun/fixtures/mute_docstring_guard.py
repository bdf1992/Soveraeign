"""A module that looks runnable and is not.

This file exists to be refused by `scripts/sov_closure_checks.py`. Running it
prints nothing and exits 0, which is the defect the closure-check reader was
built to catch, and it contains the exact text `__name__ == "__main__"` inside
this docstring so a reader that searches for that substring is fooled into
admitting it. An independent witness drove that case against the first version
of the reader; the AST test in `sovcheckrun/resolve.py` is the repair.

Do not give this file an entry point. Its whole contract is not having one.
"""

from __future__ import annotations


def never_called() -> str:
    """Present so the module is not empty; no caller and no side effect."""
    return "this module has no entry point by design"
