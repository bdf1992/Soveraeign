"""How a console record reaches the journal, and how a refusal does.

Every console transition ends the same way: one `EVENT` carrying the record, then one
terminal `RECEIPT` naming what it emitted, under which grants, at which effect class.
Keeping that shape in one place is what makes the guarantee checkable rather than
repeated - `services/console/conformance/006-thread-post-parity.yaml` requires that a
human post and a model post produce receipts of the same shape, and they do because
they travel through this function and not through two similar ones.

A refusal is appended too. A transition that refused and left no trace would be
indistinguishable from one nobody attempted, and the difference is exactly what an
operator reviewing the node needs to see.

Standing is checked here rather than at each call site because it is the one claim no
console record may make: a console record enters at RECORDED and climbs only through
kernel transitions this service does not own.
"""

from __future__ import annotations

from typing import Any, Sequence

from soveraeign_console_service.refusals import ConsoleRefusal, StandingClaim
from soveraeign_record_service import RecordService

ENTRY_STANDING = "RECORDED"
EFFECT_CLASS = "RECORD_LOCAL"


def emit(record: RecordService, kind: str, subject: str, actor: str,
         payload: dict[str, Any], event: str,
         grant_ids: Sequence[str] = ()) -> dict[str, Any]:
    """Append one console record and its terminal receipt, and return the record."""
    if payload.get("standing", ENTRY_STANDING) != ENTRY_STANDING:
        raise StandingClaim(f"{kind} may not enter at {payload['standing']}")
    entry = record.append("EVENT", subject, actor, dict(payload, record_kind=kind))
    record.receipt(
        "COMMITTED", event, subject, actor,
        {"emitted_record_addresses": [entry["entry_id"]],
         "authority_grant_ids": list(grant_ids),
         "effect_class": EFFECT_CLASS,
         "operation_type": event,
         "interface_id": payload.get("binding_id"),
         "reason_code": None})
    return dict(payload, record_kind=kind, entry_id=entry["entry_id"],
                entry_digest=entry["entry_digest"])


def refuse(record: RecordService, error: ConsoleRefusal, event: str, subject: str,
           actor: str) -> ConsoleRefusal:
    """Record a refusal as a terminal receipt, then return the error to be raised.

    The receipt carries the reason code, never the message. A caller matches on a
    stable value instead of parsing prose, and nothing an exception happens to say
    reaches the record.
    """
    record.receipt("REFUSED", event, subject, actor,
                   {"reason_code": error.reason_code,
                    "effect_class": EFFECT_CLASS,
                    "message": str(error)})
    return error
