"""Boring in-process routes for declared Asset Service operations.

A route is not another authority boundary. The Gateway supplies the actor it
already checked, the route invokes the existing service operation, and the
route returns the service's own terminal receipt object unchanged.
"""

from __future__ import annotations

from typing import Any, Callable

from soveraeign_asset_service.core import AssetService


class AssetRoutes:
    """Map declared operation ids to the already-built Asset Service methods."""

    OPERATIONS = ("ingest-asset",)
    ARGUMENTS = {
        "ingest-asset": {"required": ("path", "label"), "optional": ("locator",)},
    }

    def __init__(self, service: AssetService) -> None:
        self.service = service
        self._routes: dict[str, Callable[[dict[str, Any], str], dict[str, Any]]] = {
            "ingest-asset": self._ingest_asset,
        }

    @classmethod
    def operation_ids(cls) -> tuple[str, ...]:
        """Exact operation census without constructing a service or opening storage."""
        return cls.OPERATIONS

    @classmethod
    def argument_contract(cls, operation: str) -> dict[str, tuple[str, ...]]:
        """Service-owned argument names; Gateway and renderers do not reinterpret them."""
        return cls.ARGUMENTS[operation]

    def call(self, operation: str, arguments: dict[str, Any], actor: str) -> dict[str, Any]:
        route = self._routes.get(operation)
        if route is None:
            raise KeyError(f"asset route {operation!r} is not bound")
        return route(arguments, actor)

    def _ingest_asset(self, arguments: dict[str, Any], actor: str) -> dict[str, Any]:
        allowed = {"path", "label", "locator"}
        unknown = set(arguments) - allowed
        if unknown or "path" not in arguments or "label" not in arguments:
            raise ValueError(f"invalid ingest-asset arguments: {sorted(unknown)}")
        result = self.service.ingest(arguments["path"], arguments["label"], actor,
                                     arguments.get("locator"))
        receipt_id = result["receipt_id"]
        for receipt in reversed(self.service.receipts()):
            if receipt["id"] == receipt_id:
                return receipt
        raise RuntimeError(f"asset receipt {receipt_id} was not durable after ingest")


__all__ = ["AssetRoutes"]
