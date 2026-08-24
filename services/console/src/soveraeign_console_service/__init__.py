"""Console Service: the operator continuity record path over the Record Service journal."""

from __future__ import annotations

from soveraeign_console_service.continuity import (
    OPERATIONS,
    Projection,
    read_thread,
    session_context,
)
from soveraeign_console_service.core import ConsoleService
from soveraeign_console_service.refusals import (
    AuthorityRefused,
    ConsoleRefusal,
    ModelClaimWithoutProposal,
    PinIncomplete,
    SessionClosed,
    StandingClaim,
    ThreadArchived,
    UnknownRecord,
)

__all__ = [
    "OPERATIONS",
    "AuthorityRefused",
    "ConsoleRefusal",
    "ConsoleService",
    "ModelClaimWithoutProposal",
    "PinIncomplete",
    "Projection",
    "SessionClosed",
    "StandingClaim",
    "ThreadArchived",
    "UnknownRecord",
    "read_thread",
    "session_context",
]
