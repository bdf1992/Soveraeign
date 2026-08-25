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

    def __init__(self, service: AssetService) -> None:
        self.service = service
        self._routes: dict[str, Callable[[dict[str, Any], str], dict[str, Any]]] = {
            "ingest-asset": self._ingest_asset,
        }

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
