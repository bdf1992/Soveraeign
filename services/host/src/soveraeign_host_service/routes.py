"""Service-owned in-process route for the built Host health reading."""

from __future__ import annotations

from typing import Any

from .core import HostService


class HostRoutes:
    """Expose the exact Host argument contract without checking authority again."""

    OPERATIONS = ("read-health",)
    ARGUMENTS = {"read-health": {"required": (), "optional": ()}}

    def __init__(self, service: HostService) -> None:
        self.service = service

    @classmethod
    def operation_ids(cls) -> tuple[str, ...]:
        return cls.OPERATIONS

    @classmethod
    def argument_contract(cls, operation: str) -> dict[str, tuple[str, ...]]:
        return cls.ARGUMENTS[operation]

    def call(self, operation: str, arguments: dict[str, Any], actor: str) -> dict[str, Any]:
        if operation != "read-health":
            raise KeyError(f"host route {operation!r} is not bound")
        if arguments:
            return self.service.malformed_read_health(actor)
        return self.service.read_health(actor)


__all__ = ["HostRoutes"]
