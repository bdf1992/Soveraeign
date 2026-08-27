"""The refusals this service raises, in one place so every module can name them.

They lived in `core` and were imported from there, which meant `projections` and
`profiles` could not name a refusal without importing the module that imports
them. Both worked around it with function-local imports. A leaf module holding
only the exception types removes the cycle instead of hiding it.

`core` re-exports all five, so `from soveraeign_record_service.core import
BrokenChain` keeps working for every existing caller.
"""

from __future__ import annotations


class DesignRecordRefused(PermissionError):
    """A governing document was offered as operational event storage."""


class BrokenChain(RuntimeError):
    """The journal no longer verifies against its own digest chain."""


class ProjectionNotAuthoritative(RuntimeError):
    """A projection was offered as the authoritative record."""


class UnknownEntry(KeyError):
    """The named entry is not in the journal."""


class ProfileNotAdopted(RuntimeError):
    """A store was asked to write a profile it cannot move to from where it stands."""
