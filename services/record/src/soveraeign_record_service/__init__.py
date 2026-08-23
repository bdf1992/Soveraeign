"""Soveraeign Record Service: the operational System of Record."""

from .core import (
    BrokenChain,
    DesignRecordRefused,
    ProjectionNotAuthoritative,
    RecordService,
    UnknownEntry,
    open_service,
)

__all__ = [
    "BrokenChain",
    "DesignRecordRefused",
    "ProjectionNotAuthoritative",
    "RecordService",
    "UnknownEntry",
    "open_service",
]
