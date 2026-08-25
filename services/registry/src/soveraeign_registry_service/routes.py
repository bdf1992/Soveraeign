"""Service-owned in-process route for the one built Registry operation."""

from __future__ import annotations

from typing import Any

from .core import RegistryService


class RegistryRoutes:
    """Expose exact Registry argument identity without performing authority checks."""

    OPERATIONS = ("resolve",)
    ARGUMENTS = {"resolve": {"required": ("name",), "optional": ()}}

    def __init__(self, service: RegistryService) -> None:
        self.service = service

    @classmethod
    def operation_ids(cls) -> tuple[str, ...]:
        return cls.OPERATIONS

    @classmethod
    def argument_contract(cls, operation: str) -> dict[str, tuple[str, ...]]:
        return cls.ARGUMENTS[operation]

    def call(self, operation: str, arguments: dict[str, Any], actor: str) -> dict[str, Any]:
        if operation != "resolve":
            raise KeyError(f"registry route {operation!r} is not bound")
        if set(arguments) != {"name"} or not isinstance(arguments.get("name"), str):
            raise ValueError("resolve requires exactly one string argument: name")
        if not arguments["name"]:
            raise ValueError("resolve name may not be empty")
        return self.service.resolve(arguments["name"], actor)


__all__ = ["RegistryRoutes"]
