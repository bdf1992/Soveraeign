"""Record Service writes owned by the Gateway crossing, not by domain services."""

from __future__ import annotations

from typing import Any

from soveraeign_record_service import RecordService

from .contract import GatewayFault, GatewayRefusal, request_actor_subject


def record_request(record: RecordService, request: dict[str, Any], request_id: str) -> dict[str, Any]:
    """Record receipt of the envelope before any path can refuse it."""
    mapping = request if isinstance(request, dict) else {}
    actor, subject = request_actor_subject(mapping)
    arguments = mapping.get("arguments")
    return record.append(
        "EVENT", subject, actor,
        {"record_kind": "gateway-request", "request_id": request_id,
         "actor_kind": mapping.get("actor_kind")
         if isinstance(mapping.get("actor_kind"), str) else None,
         "transport": mapping.get("transport")
         if isinstance(mapping.get("transport"), str) else None,
         "scope": mapping.get("scope") if isinstance(mapping.get("scope"), str) else None,
         "argument_names": sorted(arguments)
         if isinstance(arguments, dict) and all(isinstance(name, str) for name in arguments) else [],
         "envelope_fields": sorted(name for name in mapping if isinstance(name, str))})


def record_resolution(record: RecordService, request: dict[str, Any], request_id: str,
                      capability: dict[str, Any], endpoint: dict[str, Any],
                      map_digest: str) -> dict[str, Any]:
    return record.append(
        "EVENT", request["logical_endpoint"], request["actor"],
        {"record_kind": "gateway-capability-resolution",
         "request_id": request_id, "capability_id": capability["capability_id"],
         "service_id": capability["service_id"], "operation": capability["operation"],
         "effect_class": capability["effect_class"], "transport": request["transport"],
         "route_address": endpoint["address"], "capability_map_digest": map_digest})


def record_authority(record: RecordService, request: dict[str, Any], request_id: str,
                     resolution_entry_id: str, capability: dict[str, Any], *,
                     decision: str, grant_id: str | None = None,
                     diagnostic_code: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "record_kind": "gateway-authority-check", "request_id": request_id,
        "resolution_entry_id": resolution_entry_id, "actor_kind": request["actor_kind"],
        "required_authority": capability["required_authority"], "scope": request["scope"],
        "decision": decision,
    }
    if grant_id is not None:
        payload["authority_grant_id"] = grant_id
    if diagnostic_code is not None:
        payload["diagnostic_code"] = diagnostic_code
    return record.append("EVENT", request["logical_endpoint"], request["actor"], payload)


def record_routing(record: RecordService, request: dict[str, Any], request_id: str,
                   request_entry_id: str, resolution_entry_id: str,
                   authority_entry_id: str, capability: dict[str, Any],
                   endpoint: dict[str, Any], grant_id: str) -> dict[str, Any]:
    return record.append(
        "EVENT", request["logical_endpoint"], request["actor"],
        {"record_kind": "gateway-routing-record", "request_id": request_id,
         "request_entry_id": request_entry_id, "resolution_entry_id": resolution_entry_id,
         "authority_entry_id": authority_entry_id, "capability_id": capability["capability_id"],
         "service_id": capability["service_id"], "operation": capability["operation"],
         "transport": request["transport"], "route_address": endpoint["address"],
         "authority_grant_id": grant_id, "effect_class": capability["effect_class"],
         "scope": request["scope"]})


def record_return(record: RecordService, request: dict[str, Any], request_id: str,
                  routing_entry_id: str, terminal_receipt_id: str,
                  terminal_outcome: str) -> dict[str, Any]:
    return record.append(
        "EVENT", request["logical_endpoint"], request["actor"],
        {"record_kind": "gateway-returned-receipt", "request_id": request_id,
         "routing_entry_id": routing_entry_id, "terminal_receipt_id": terminal_receipt_id,
         "terminal_outcome": terminal_outcome})


def refuse(record: RecordService, request: dict[str, Any], request_id: str,
           request_entry_id: str, refusal: GatewayRefusal, *,
           routing_entry_id: str | None = None) -> dict[str, Any]:
    actor, subject = request_actor_subject(request)
    detail: dict[str, Any] = {
        "request_id": request_id, "request_entry_id": request_entry_id,
        "reason_code": refusal.code, "failure_class": "GOVERNED_REFUSAL",
        "stage": refusal.stage,
    }
    if refusal.diagnostic_code is not None:
        detail["diagnostic_code"] = refusal.diagnostic_code
    if routing_entry_id is not None:
        detail["routing_entry_id"] = routing_entry_id
    return record.receipt("REFUSED", "gateway.refuse-request", subject, actor, detail)


def fail(record: RecordService, request: dict[str, Any], request_id: str,
         request_entry_id: str, fault: GatewayFault, *,
         routing_entry_id: str | None = None) -> dict[str, Any]:
    actor, subject = request_actor_subject(request)
    detail: dict[str, Any] = {
        "request_id": request_id, "request_entry_id": request_entry_id,
        "reason_code": fault.code, "failure_class": "OPERATIONAL_FAULT", "stage": fault.stage,
    }
    if fault.error_type is not None:
        detail["error_type"] = fault.error_type
    if routing_entry_id is not None:
        detail["routing_entry_id"] = routing_entry_id
    return record.receipt("FAILED", fault.event, subject, actor, detail)
