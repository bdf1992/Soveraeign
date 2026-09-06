"""The node layer of the fresh participation probe: sessions, grants, and crossings.

Everything here is read back from records the node's own services wrote: the Console
Service opens the session and issues the grant, the Gateway refuses or admits each
crossing, and its receipt carries the stage and reason. The probe composes requests,
including ones the node must refuse, and decides nothing about whether the node admits
them. It applies one rule of its own, in `admit`: which name may seed a fresh node's first
grant. That rule is the probe's and is reported as such.
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

from soveraeign_console_service import authority as console_authority  # noqa: E402
from soveraeign_console_service import reads as console_reads  # noqa: E402
from soveraeign_record_service import custody as record_custody  # noqa: E402

OPERATION = "registry.resolve"
SCOPE = "registry:any"
ARGUMENTS = {"name": "sov://asset/ingest-asset"}
BEYOND_OPERATION = "asset.ingest-asset"
BEYOND_ARGUMENTS = {"path": "/nonexistent/beyond-the-grant", "label": "beyond the grant"}
SESSION_BINDING = "urn:soveraeign:binding:session:fresh-probe"
OPEN_SESSION = "open:session"
CLOSE_SESSION = "close:session"
PROBE_ISSUER_GATE = "PROBE_ISSUER_GATE"
"""The probe's own refusal: an issuer the registry does not name as root seeds nothing."""


def open_node(work_dir: Path) -> LocalActionPath:
    """A node of this repository's declared shape, with empty stores under `work_dir`."""
    return LocalActionPath(work_dir / "node")


def open_node_at(state: Path) -> LocalActionPath:
    """The node whose stores live at `state`: opened once, its journal continues."""
    return LocalActionPath(state)


def open_office(node: LocalActionPath, issuer: str, operator: str,
                capabilities: dict[str, str]) -> list[dict[str, Any]]:
    """Record the issuer's grants to one operator; the first grant seats the issuer as root.

    This is the act the probe otherwise refuses to perform under any name but the
    registry's root. The journal is the receipt: each grant carries `granted_by`.
    """
    records = [node.console.grant(operator, OPEN_SESSION, operator, granted_by=issuer),
               node.console.grant(operator, CLOSE_SESSION, operator, granted_by=issuer)]
    for capability, scope in capabilities.items():
        records.append(node.console.grant(operator, capability, scope, granted_by=issuer))
    return records


def admit_persisted(node: LocalActionPath, actor: str, principal_id: str | None,
                    required_authority: str) -> dict[str, Any]:
    """Open the actor's session on a node whose office someone else opened; issue nothing.

    The grant is whichever live grant the journal holds for this actor and capability;
    the session opens only if the actor holds `open:session`, which the Console decides.
    """
    entries = node.record.reconstruct()
    held = [record for record in console_authority.held(entries, actor, node.node_id)
            if record["capability"] == required_authority]
    grant_id = held[-1]["grant_id"] if held else None
    try:
        session = node.console.open_session(actor, MODEL, SESSION_BINDING, principal_id)
    except console_authority.AuthorityRefused as refused:
        return {"session": None, "grant_id": grant_id, "refused_by": None,
                "reason": f"the node refused to open a session for {actor}: {refused}"}
    reason = None if grant_id else f"the node holds no live {required_authority} grant for {actor}"
    return {"session": session, "grant_id": grant_id, "refused_by": None, "reason": reason}


def close_participant_session(node: LocalActionPath, actor: str,
                              session_id: str | None) -> str | None:
    """Close the participant's own console session; the reason if the node refuses."""
    if not session_id:
        return None
    try:
        node.console.close_session(actor, session_id)
    except console_authority.AuthorityRefused as refused:
        return str(refused)
    return None


def export_journal(node: LocalActionPath) -> dict[str, Any]:
    """The node's journal as the Record Service exports it, verifiable by its head."""
    return record_custody.export_document(node.record)


def admit(node: LocalActionPath, issuer: str | None, root: str | None, actor: str,
          principal_id: str | None, required_authority: str) -> dict[str, Any]:
    """Open the participant's console session and, when the root issues, record its grant.

    With no issuer nothing is granted and no session opens: a node whose permits office
    has never been opened admits nobody, which is the honest reading of a fresh node.

    The Console makes whoever issues a fresh node's first grant that node's root and reads
    no registry. The probe therefore refuses, by its own rule `PROBE_ISSUER_GATE`, to offer
    that first grant under any name but the one the registry in force names as root. The
    rule is the probe's, not the node's; the node would have accepted the name.
    """
    if issuer is None:
        return {"session": None, "grant_id": None, "refused_by": None,
                "reason": "no issuer: this node has recorded no grant for any actor"}
    if not issuer or issuer != root:
        return {"session": None, "grant_id": None, "refused_by": PROBE_ISSUER_GATE,
                "reason": f"probe rule {PROBE_ISSUER_GATE}: issuer {issuer!r} is not the "
                          f"registry's root principal {root!r}; the probe seeded nothing"}
    node.console.grant(actor, OPEN_SESSION, actor, granted_by=issuer)
    node.console.grant(actor, CLOSE_SESSION, actor, granted_by=issuer)
    granted = node.console.grant(actor, required_authority, SCOPE, granted_by=issuer)
    session = node.console.open_session(actor, MODEL, SESSION_BINDING, principal_id)
    return {"session": session, "grant_id": granted["grant_id"], "refused_by": None,
            "reason": None}


def reachable_operation(document: dict[str, Any]) -> dict[str, Any]:
    """The one operation this probe crosses, resolved from the derived Node Interface."""
    record = resolve(document, OPERATION)
    if not record["facts"].get("reachable") or MODEL not in record["actor_kinds"]:
        raise RuntimeError(f"{OPERATION} is not reachable for a MODEL actor at this revision")
    return record


def bind(document: dict[str, Any], actor: str, session: dict[str, Any] | None,
         principal_id: str | None, arguments: dict[str, Any] | None = None,
         session_id: str | None = None, operation: str = OPERATION) -> dict[str, Any]:
    """Bind one invocation to a session; a refusal is returned, not raised."""
    try:
        request = invocation_request(
            document, operation, MODEL, actor, SCOPE, dict(arguments or ARGUMENTS),
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
