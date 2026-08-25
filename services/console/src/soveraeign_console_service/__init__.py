"""Console Service: the operator continuity record path over the Record Service journal."""

from __future__ import annotations

from soveraeign_console_service.continuity import (
    Projection,
    read_thread,
    session_context,
)
from soveraeign_console_service.core import ConsoleService
from soveraeign_console_service.discovery import discover, operations
from soveraeign_console_service.refusals import (
    AuthorityRefused,
    ConsoleRefusal,
    ModelClaimWithoutProposal,
    PinIncomplete,
    SessionClosed,
    StaleCapabilityMap,
    StandingClaim,
    ThreadArchived,
    UnknownRecord,
)

__all__ = [
    "AuthorityRefused",
    "ConsoleRefusal",
    "ConsoleService",
    "ModelClaimWithoutProposal",
    "PinIncomplete",
    "Projection",
    "SessionClosed",
    "StaleCapabilityMap",
    "StandingClaim",
    "ThreadArchived",
    "UnknownRecord",
    "discover",
    "operations",
    "read_thread",
    "session_context",
]
