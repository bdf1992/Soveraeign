"""Transport-neutral dispatch from one declared ``sov://`` request to a service route."""

from __future__ import annotations

from typing import Any
import uuid

from soveraeign_record_service import RecordService

from .contract import (
    ACTIVE,
    ATTRIBUTION_ARGUMENTS,
    RECORD_LOCAL,
    AuthorityCheck,
    GatewayFault,
    GatewayRefusal,
    ServiceRoute,
    expected_endpoint,
    input_state_digest,
    load_surface,
    receipt_actor,
    receipt_id,
    receipt_outcome,
    terminal_receipt,
)
from .evidence import (
    fail,
    record_authority,
    record_request,
    record_resolution,
    record_return,
    record_routing,
    refuse,
)


class Gateway:
    """Resolve, authorize, and route declared operations through one reusable path."""

    def __init__(self, record: RecordService, capability_map: dict[str, Any],
                 manifests: dict[str, dict[str, Any]], capability_table: dict[str, Any],
                 authority: AuthorityCheck, routes: dict[str, ServiceRoute], *,
                 authority_denials: tuple[type[BaseException], ...] = ()) -> None:
        self.record = record
        self.capability_map = capability_map
        self.authority = authority
        self.authority_denials = authority_denials
        self.routes = dict(routes)
        self.capability_table = capability_table
        self._surface_fresh = capability_map.get("input_state_digest") == input_state_digest(
            manifests, capability_table)
        self._operations = {
            entry["logical_endpoint"]: (manifest["service_id"], entry)
            for manifest in manifests.values()
            for entry in manifest.get("operations", [])
        }
        self._capabilities: dict[str, dict[str, Any]] = {}
        self._duplicate_capabilities: set[str] = set()
        for row in capability_map.get("capabilities", []):
            key = f"sov://{row.get('service_id')}/{row.get('operation')}"
            if key in self._capabilities:
                self._duplicate_capabilities.add(key)
            self._capabilities[key] = row

    def dispatch(self, request: dict[str, Any]) -> dict[str, Any]:
        """Cross the Gateway or return durable evidence explaining why it did not."""
        request_id = f"gateway_request_{uuid.uuid4().hex}"
        request_entry = record_request(self.record, request, request_id)
        try:
            accepted = self._accept(request)
            capability, endpoint = self._resolve(accepted)
            resolution = record_resolution(
                self.record, accepted, request_id, capability, endpoint,
                self.capability_map["input_state_digest"])
            grant_id, authority_record = self._check_authority(
                accepted, request_id, resolution["entry_id"], capability)
            route = self._admit_route(capability, endpoint)
        except GatewayRefusal as rejection:
            return refuse(self.record, request, request_id, request_entry["entry_id"], rejection)
        except GatewayFault as fault:
            return fail(self.record, request, request_id, request_entry["entry_id"], fault)

        routing = record_routing(
            self.record, accepted, request_id, request_entry["entry_id"],
            resolution["entry_id"], authority_record["entry_id"], capability, endpoint, grant_id)
        try:
            service_receipt = route(
                capability["operation"], accepted["arguments"], accepted["actor"])
        except Exception as error:
            return fail(
                self.record, accepted, request_id, request_entry["entry_id"],
                GatewayFault("SERVICE_EXECUTION_FAILED", str(error),
                             event="gateway.route-request", stage="service-execution",
                             error_type=type(error).__name__),
                routing_entry_id=routing["entry_id"])

        if not terminal_receipt(service_receipt):
            return refuse(
                self.record, accepted, request_id, request_entry["entry_id"],
                GatewayRefusal(
                    "RECEIPT_MISSING",
                    f"{accepted['logical_endpoint']} returned no terminal receipt",
                    stage="return-receipt", diagnostic_code="NON_TERMINAL_SERVICE_RESULT"),
                routing_entry_id=routing["entry_id"])
        if receipt_actor(service_receipt) != accepted["actor"]:
            return fail(
                self.record, accepted, request_id, request_entry["entry_id"],
                GatewayFault(
                    "SERVICE_ATTRIBUTION_MISMATCH",
                    "service terminal receipt does not name the checked Gateway actor",
                    event="gateway.return-receipt", stage="return-receipt"),
                routing_entry_id=routing["entry_id"])

        record_return(
            self.record, accepted, request_id, routing["entry_id"],
            receipt_id(service_receipt) or "unreachable",
            receipt_outcome(service_receipt) or "unreachable")
        return service_receipt

    def _accept(self, request: dict[str, Any]) -> dict[str, Any]:
        required = ("actor", "actor_kind", "logical_endpoint", "transport", "scope", "arguments")
        if not isinstance(request, dict) or any(name not in request for name in required):
            raise GatewayRefusal("MALFORMED_REQUEST", "gateway request is incomplete",
                                 stage="accept-request")
        if (not isinstance(request["actor"], str) or not request["actor"]
                or request["actor_kind"] not in ("HUMAN", "MODEL", "WORKER", "SYSTEM")
                or not isinstance(request["logical_endpoint"], str)
                or not request["logical_endpoint"].startswith("sov://")
                or not isinstance(request["transport"], str)
                or not isinstance(request["scope"], str) or not request["scope"]
                or not isinstance(request["arguments"], dict)):
            raise GatewayRefusal("MALFORMED_REQUEST", "gateway request has invalid fields",
                                 stage="accept-request")
        attribution = ATTRIBUTION_ARGUMENTS.intersection(request["arguments"])
        if attribution:
            raise GatewayRefusal(
                "MALFORMED_REQUEST",
                f"service arguments may not override checked attribution: {sorted(attribution)}",
                stage="accept-request", diagnostic_code="ACTOR_ATTRIBUTION_CONFLICT")
        return dict(request)

    def _resolve(self, request: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        logical_endpoint = request["logical_endpoint"]
        if not self._surface_fresh:
            raise GatewayRefusal(
                "ENDPOINT_UNKNOWN", "capability map is stale against its declared inputs",
                stage="resolve-capability", diagnostic_code="CAPABILITY_MAP_STALE")
        if logical_endpoint in self._duplicate_capabilities:
            raise GatewayFault(
                "CAPABILITY_MAP_INVALID",
                f"{logical_endpoint} appears more than once in the capability map",
                event="gateway.resolve-capability", stage="resolve-capability")

        declared = self._operations.get(logical_endpoint)
        capability = self._capabilities.get(logical_endpoint)
        if declared is None or capability is None:
            raise GatewayRefusal(
                "ENDPOINT_UNKNOWN", f"{logical_endpoint} is not declared",
                stage="resolve-capability", diagnostic_code="ENDPOINT_UNDECLARED")
        service_id, operation = declared
        capability_id = f"{service_id}.{operation['operation']}"
        assignment = self.capability_table.get("assignments", {}).get(capability_id)
        if not isinstance(assignment, dict):
            raise GatewayFault(
                "CAPABILITY_MAP_INVALID", f"{capability_id} has no capability-office assignment",
                event="gateway.resolve-capability", stage="resolve-capability")

        expected = {
            "capability_id": capability_id,
            "service_id": service_id,
            "operation": operation["operation"],
            "office": assignment.get("office", "BACK"),
            "counter": assignment.get("counter", "unassigned"),
            "service_standing": operation.get("standing", "PROPOSED"),
            "effect_class": assignment.get("effect_class", RECORD_LOCAL),
            "required_authority": assignment.get("required_authority", "UNASSIGNED"),
            "actor_kinds": list(assignment.get("actor_kinds", ["SYSTEM"])),
            "endpoints": [
                expected_endpoint(service_id, capability_id,
                                  operation.get("standing", "PROPOSED"), transport,
                                  self.capability_table)
                for transport in self.capability_table.get("transport_policy", {})],
        }
        drift = [name for name, value in expected.items() if capability.get(name) != value]
        if drift:
            raise GatewayFault(
                "CAPABILITY_MAP_INVALID",
                f"{logical_endpoint} projection drift: {', '.join(sorted(drift))}",
                event="gateway.resolve-capability", stage="resolve-capability")

        matching = [endpoint for endpoint in capability["endpoints"]
                    if endpoint.get("transport") == request["transport"]]
        if not matching or matching[0].get("activation") != ACTIVE:
            raise GatewayRefusal(
                "TRANSPORT_NOT_ACTIVATED",
                f"{request['transport']} is not active for {logical_endpoint}",
                stage="accept-request")
        return capability, matching[0]

    def _check_authority(self, request: dict[str, Any], request_id: str,
                         resolution_entry_id: str,
                         capability: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        if request["actor_kind"] not in capability.get("actor_kinds", []):
            record_authority(
                self.record, request, request_id, resolution_entry_id, capability,
                decision="REFUSED", diagnostic_code="ACTOR_KIND_NOT_ADMITTED")
            raise GatewayRefusal(
                "AUTHORITY_REFUSED", f"{request['actor_kind']} may not call this operation",
                stage="check-authority", diagnostic_code="ACTOR_KIND_NOT_ADMITTED")
        try:
            grant_id = self.authority(
                request["actor"], capability["required_authority"], request["scope"])
        except Exception as error:
            if self.authority_denials and isinstance(error, self.authority_denials):
                record_authority(
                    self.record, request, request_id, resolution_entry_id, capability,
                    decision="REFUSED", diagnostic_code=type(error).__name__)
                raise GatewayRefusal(
                    "AUTHORITY_REFUSED", str(error), stage="check-authority",
                    diagnostic_code=type(error).__name__) from error
            record_authority(
                self.record, request, request_id, resolution_entry_id, capability,
                decision="FAILED", diagnostic_code=type(error).__name__)
            raise GatewayFault(
                "AUTHORITY_CHECK_FAILED", str(error), event="gateway.check-authority",
                stage="check-authority", error_type=type(error).__name__) from error
        if not isinstance(grant_id, str) or not grant_id:
            record_authority(
                self.record, request, request_id, resolution_entry_id, capability,
                decision="FAILED", diagnostic_code="INVALID_GRANT_REFERENCE")
            raise GatewayFault(
                "AUTHORITY_CHECK_FAILED", "authority reader returned no durable grant identifier",
                event="gateway.check-authority", stage="check-authority",
                error_type="InvalidGrantReference")
        evidence = record_authority(
            self.record, request, request_id, resolution_entry_id, capability,
            decision="ALLOWED", grant_id=grant_id)
        return grant_id, evidence

    def _admit_route(self, capability: dict[str, Any], endpoint: dict[str, Any]) -> ServiceRoute:
        if capability.get("effect_class") != RECORD_LOCAL:
            raise GatewayRefusal(
                "EFFECT_CLASS_REFUSED", f"{capability.get('effect_class')} is outside this slice",
                stage="route-request")
        route = self.routes.get(endpoint.get("address"))
        if route is None:
            raise GatewayRefusal(
                "SERVICE_UNREACHABLE", f"no route is bound for {endpoint.get('address')}",
                stage="route-request")
        return route


__all__ = ["Gateway", "GatewayRefusal", "load_surface"]
