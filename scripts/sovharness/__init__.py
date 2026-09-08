"""Fixtures and helpers for the harness claim grader."""

from __future__ import annotations


def emits(name: str):
    """Bind a check to the kind it emits, at its definition.

    The kind set was once a tuple zipped against ALL_CHECKS. `zip` truncates
    silently, so removing one check shifted every later label and SELFCLAIM then
    named the wrong kind - a witness found it by deleting one check and reading
    the output rather than the code. The name is written once now, beside the
    function it belongs to, so there is no list to keep in step with anything.
    """
    def bind(check):
        check.kind = name
        return check
    return bind
