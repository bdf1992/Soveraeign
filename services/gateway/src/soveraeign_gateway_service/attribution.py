"""Session-attribution evidence for one Gateway request crossing."""

from __future__ import annotations

from typing import Any

from soveraeign_record_service import RecordService

from .contract import AttributionCheck, GatewayFault, GatewayRefusal
from .evidence import record_attribution


def check(record: RecordService, request: dict[str, Any], request_id: str,
          request_entry_id: str, attribution: AttributionCheck,
          denials: tuple[type[BaseException], ...]) -> dict[str, Any]:
    """Prove the session claim before capability resolution or authority.

    Session identity and grant authority are separate questions. A valid session
    never supplies a grant; a valid grant never proves which session made the call.
    """
    try:
        attribution(
            request["actor"], request["actor_kind"], request["session_id"],
            request["session_binding_id"], request["principal_id"])
    except Exception as error:
        diagnostic = getattr(error, "reason_code", type(error).__name__)
        if denials and isinstance(error, denials):
            record_attribution(
                record, request, request_id, request_entry_id,
                decision="REFUSED", diagnostic_code=diagnostic)
            raise GatewayRefusal(
                diagnostic, str(error), stage="check-attribution",
                diagnostic_code=diagnostic) from error
        record_attribution(
            record, request, request_id, request_entry_id,
            decision="FAILED", diagnostic_code=type(error).__name__)
        raise GatewayFault(
            "ATTRIBUTION_CHECK_FAILED", str(error), event="gateway.check-attribution",
            stage="check-attribution", error_type=type(error).__name__) from error
    return record_attribution(
        record, request, request_id, request_entry_id, decision="ALLOWED")


__all__ = ["check"]
