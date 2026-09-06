"""The node layer of the fresh participation probe: sessions, grants, and one crossing.

Everything here is read back from records the node's own services wrote: the Console
Service opens the session and issues the grant, the Gateway refuses or admits the
crossing, and the receipt carries the reason. The probe composes requests; it decides
nothing about whether they are admitted.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import sys

from sovnode.bindings import MODEL, BindingRefusal, invocation_request, resolve
from sovnode.composition import LocalActionPath

ROOT = Path(__file__).resolve().parents[2]
for _service in ("console", "record"):
    _src = ROOT / "services" / _service / "src"
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

from soveraeign_console_service import reads as console_reads  # noqa: E402

OPERATION = "registry.resolve"
SCOPE = "registry:any"
ARGUMENTS = {"name": "sov://asset/ingest-asset"}
SESSION_BINDING = "urn:soveraeign:binding:session:fresh-probe"
OPEN_SESSION = "open:session"


def open_node(work_dir: Path) -> LocalActionPath:
    """A node of this repository's declared shape, with empty stores under `work_dir`."""
    return LocalActionPath(work_dir / "node")


def admit(node: LocalActionPath, issuer: str | None, actor: str, principal_id: str | None,
          required_authority: str) -> dict[str, Any]:
    """Open the participant's console session and, when an issuer exists, record its grant.

    With no issuer nothing is granted and no session opens: a node whose permits office
    has never been opened admits nobody, which is the honest reading of a fresh node.
    """
    if issuer is None:
        return {"session": None, "grant_id": None,
                "reason": "no issuer: this node has recorded no grant for any actor"}
    node.console.grant(actor, OPEN_SESSION, actor, granted_by=issuer)
    granted = node.console.grant(actor, required_authority, SCOPE, granted_by=issuer)
    session = node.console.open_session(actor, MODEL, SESSION_BINDING, principal_id)
    return {"session": session, "grant_id": granted["grant_id"], "reason": None}


def reachable_operation(document: dict[str, Any]) -> dict[str, Any]:
    """The one operation this probe crosses, resolved from the derived Node Interface."""
    record = resolve(document, OPERATION)
    if not record["facts"].get("reachable") or MODEL not in record["actor_kinds"]:
        raise RuntimeError(f"{OPERATION} is not reachable for a MODEL actor at this revision")
    return record


def bind(document: dict[str, Any], actor: str, session: dict[str, Any] | None,
         principal_id: str | None, arguments: dict[str, Any] | None = None,
         session_id: str | None = None) -> dict[str, Any]:
    """Bind one invocation to a session; a refusal is returned, not raised."""
    try:
        request = invocation_request(
            document, OPERATION, MODEL, actor, SCOPE, dict(arguments or ARGUMENTS),
            session_id=session_id or (session or {}).get("session_id") or "",
            session_binding_id=(session or {}).get("binding_id") or SESSION_BINDING,
            principal_id=principal_id)
    except BindingRefusal as refusal:
        return {"verdict": "REFUSED", "code": refusal.code, "request": None,
                "interface_binding_id": None}
    return {"verdict": "BOUND", "code": None, "request": request,
            "interface_binding_id": request["interface_binding_id"]}


def _detail(receipt: dict[str, Any]) -> dict[str, Any]:
    payload = receipt.get("payload")
    if isinstance(payload, dict) and isinstance(payload.get("detail"), dict):
        return payload["detail"]
    return {}


def cross(node: LocalActionPath, binding: dict[str, Any]) -> dict[str, Any]:
    """Dispatch a bound request and read the Gateway's receipt for outcome and reason."""
    if binding["request"] is None:
        return {"outcome": "REFUSED", "stage": "bind", "reason": binding["code"],
                "diagnostic": None}
    receipt = node.dispatch(binding["request"])
    payload = receipt.get("payload") if isinstance(receipt.get("payload"), dict) else {}
    detail = _detail(receipt)
    return {
        "outcome": payload.get("outcome") or receipt.get("outcome"),
        "stage": detail.get("stage"),
        "reason": detail.get("reason_code"),
        "diagnostic": detail.get("diagnostic_code"),
        "grant_id": detail.get("grant_id") or payload.get("grant_id"),
        "receipt_id": receipt.get("entry_id") or receipt.get("id"),
    }


def console_session_state(node: LocalActionPath, session_id: str | None) -> str | None:
    """The console session's lifecycle as the journal reads it now."""
    if not session_id:
        return None
    try:
        return console_reads.session(node.record.reconstruct(), session_id).get("lifecycle")
    except Exception:  # noqa: BLE001 - an unknown session is reported, not raised
        return None
