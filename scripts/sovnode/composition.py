"""The smallest local action composition behind the Node Interface.

This assembles the proven Gateway verticals. It owns no domain state and
creates no grant: callers must arrive with authority already recorded by the
Console authority reader. Asset and Registry remain the owners of their results.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
for service in ("gateway", "asset", "console", "record", "registry"):
    sys.path.insert(0, str(ROOT / "services" / service / "src"))

from soveraeign_asset_service import AssetService  # noqa: E402
from soveraeign_asset_service.routes import AssetRoutes  # noqa: E402
from soveraeign_console_service import ConsoleService  # noqa: E402
from soveraeign_console_service import authority as console_authority  # noqa: E402
from soveraeign_console_service.refusals import AuthorityRefused  # noqa: E402
from soveraeign_gateway_service import Gateway, load_surface  # noqa: E402
from soveraeign_record_service import RecordService  # noqa: E402
from soveraeign_registry_service import RegistryRoutes, RegistryService  # noqa: E402
from sovkernel.closure_inputs import rebuild as rebuild_closure  # noqa: E402
from sovkernel.kernel_binding import binding_defects  # noqa: E402
from sovkernel.kernel_sources import load_source_digests  # noqa: E402

COMMON_ROUTE_SOURCES = (
    "scripts/sovnode/composition.py",
    "services/gateway/src/soveraeign_gateway_service/contract.py",
    "services/gateway/src/soveraeign_gateway_service/core.py",
)
ASSET_ROUTE_SOURCES = COMMON_ROUTE_SOURCES + (
    "services/asset/src/soveraeign_asset_service/core.py",
    "services/asset/src/soveraeign_asset_service/routes.py",
)
REGISTRY_ROUTE_SOURCES = COMMON_ROUTE_SOURCES + (
    "scripts/sovkernel/closure_inputs.py",
    "services/registry/src/soveraeign_registry_service/core.py",
    "services/registry/src/soveraeign_registry_service/index.py",
    "services/registry/src/soveraeign_registry_service/routes.py",
)


def route_census() -> list[dict[str, Any]]:
    """Exact routes this composition can bind, without opening participant state."""
    routes = []
    for operation in AssetRoutes.operation_ids():
        arguments = AssetRoutes.argument_contract(operation)
        routes.append({
            "operation_id": f"asset.{operation}",
            "logical_endpoint": f"sov://asset/{operation}",
            "transport": "IN_PROCESS",
            "address": "asset:in-process",
            "required_arguments": list(arguments["required"]),
            "optional_arguments": list(arguments["optional"]),
            "source_addresses": list(ASSET_ROUTE_SOURCES),
        })
    for operation in RegistryRoutes.operation_ids():
        arguments = RegistryRoutes.argument_contract(operation)
        routes.append({
            "operation_id": f"registry.{operation}",
            "logical_endpoint": f"sov://registry/{operation}",
            "transport": "IN_PROCESS",
            "address": "registry:in-process",
            "required_arguments": list(arguments["required"]),
            "optional_arguments": list(arguments["optional"]),
            "source_addresses": list(REGISTRY_ROUTE_SOURCES),
        })
    return routes


def _self_identity() -> dict[str, Any]:
    registry = json.loads((ROOT / "contracts" / "fixtures" /
                           "node-registry.reference.json").read_text("utf-8"))
    matches = [node for node in registry["nodes"] if node.get("relation") == "SELF"]
    if len(matches) != 1 or registry.get("self_node") != matches[0].get("node_id"):
        raise RuntimeError("local node registry does not resolve exactly one SELF identity")
    return matches[0]


class LocalActionPath:
    """Compose local participants behind one transport-neutral Gateway."""

    def __init__(self, state_root: str | Path) -> None:
        identity = _self_identity()
        self.node_id = identity["node_id"]
        self.root_seat = identity["root_seat"]
        root = Path(state_root)
        self.record = RecordService(root / "record")
        self.console = ConsoleService(self.record, root / "console", self.node_id)
        self.asset = AssetService(root / "asset")
        capability_map, manifests, table = load_surface(ROOT)
        (closure, closure_manifests, transitions, paradigms,
         closure_sources, source_defects) = rebuild_closure(ROOT)
        defects = source_defects + binding_defects(
            closure_manifests, transitions, paradigms)
        if manifests != closure_manifests:
            defects.append("service manifests differ between Gateway and Kernel loaders")
        index_addresses = [entry["address"] for entry in closure_sources]
        index_addresses.append("contracts/capability-offices.json")
        index_sources, index_defects = load_source_digests(ROOT, index_addresses)
        defects.extend(index_defects)
        if defects:
            raise RuntimeError("local composition refused: " + "; ".join(defects))
        asset_routes = AssetRoutes(self.asset)
        self.registry = RegistryService(
            self.record, ROOT, closure, manifests, table, index_sources)
        registry_routes = RegistryRoutes(self.registry)

        def authority(actor: str, capability: str, scope: str) -> str:
            return console_authority.check(
                self.record.reconstruct(), actor, capability, scope)

        self.gateway = Gateway(
            self.record, capability_map, manifests, table, authority,
            {"asset:in-process": asset_routes.call,
             "registry:in-process": registry_routes.call},
            authority_denials=(AuthorityRefused,),
        )

    def dispatch(self, request: dict[str, Any]) -> dict[str, Any]:
        """Carry one request; the owning service or Gateway returns the receipt."""
        return self.gateway.dispatch(request)

    def close(self) -> None:
        self.asset.close()
        self.record.close()

    def __enter__(self) -> "LocalActionPath":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


__all__ = ["LocalActionPath", "route_census"]
