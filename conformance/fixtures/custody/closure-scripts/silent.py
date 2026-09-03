"""A module with no entry point, so running it as a command reports nothing.

This file exists to defeat SILENT_CLOSURE_CHECK. Owning the fixture rather than
pointing the case at a real library keeps the defeat stable: a library that
later grows a `__main__` guard would quietly stop defeating the refusal.
"""

from __future__ import annotations


def grade() -> list[str]:
    """A real grading function nothing runs when the module is invoked."""
    return []
