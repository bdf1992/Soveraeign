"""The ordered layers a fresh participant traverses, each returning what it resolved.

Every layer reads the artifact or a store the probe opened; none reads the operator.
Where a layer refuses, it returns the refusal rather than raising, because the
instrument grades the shape of what was resolved and a refusal is part of that shape.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator
import argparse
import json
import os

from sovcustody import model as custody_model
from sovkernel import authority
from sovlease import commands as lease_commands
from sovlease import store as lease_store
from sovnode.bindings import MODEL, BindingRefusal, invocation_request, resolve
from sovnode.interface_inputs import rebuild
from sovsession import phase_context, principals, store

GRANTS = "contracts/standing-grants.json"
EXIT_CUSTODY = "custody:phase-1-5/fresh-participation"
SESSION_BINDING = "urn:soveraeign:binding:session:probe"
DEFINITION = "scripts/sov_fresh.py"


@contextmanager
def speaking_as(principal_id: str) -> Iterator[None]:
    """Declare the registered principal this participant speaks as, for the resolver.

    The registry names a principal; it never authenticates one. The declaration is
    the participant's own, made through the same channel the CLI reads.
    """
    saved = os.environ.get(principals.ENV_PRINCIPAL)
    os.environ[principals.ENV_PRINCIPAL] = principal_id
    try:
        yield
    finally:
        if saved is None:
            os.environ.pop(principals.ENV_PRINCIPAL, None)
        else:
            os.environ[principals.ENV_PRINCIPAL] = saved


def open_session(directory: Path, session: str, root: Path, principal_id: str) -> dict[str, Any]:
    """Layer 1: register a session with no prior events in this store, and resolve it."""
    with speaking_as(principal_id):
        claim = principals.resolve(root, session)
    store.append(directory, store.SESSIONS_LOG, {
        "event": "register", "session": session, "pid": os.getpid(),
        "principal": claim["principal"], "verification": claim["verification"],
        "tree": str(root), "branch": "(probe)", "intent": "fresh participation probe",
    })
    return {"session_id": session, "principal": claim}


def campaign(root: Path) -> dict[str, Any]:
    """Layer 2: the open campaign and the authority it is read from, by digest."""
    context = phase_context.collect(root)
    sources = [f"{item.get('path')}@{item.get('digest')}" for item in context.get("sources", [])]
    return {
        "phase_state": context.get("status_phase") or "",
        "next_gate": context.get("next_gate") or "",
        "governance_context": " + ".join(sources),
        "defects": list(context.get("defects") or []),
    }


def bounded_work(root: Path) -> dict[str, Any]:
    """Layer 3: one unit of accepted work, read from the custody collection."""
    custody = custody_model.by_id(EXIT_CUSTODY)
    if custody is None:
        return {"address": None, "custody": None}
    closure = custody.get("closure") or {}
    return {
        "address": custody["custody_id"],
        "custody": custody,
        "closure_condition": (closure.get("check") or {}).get("expression"),
        "defeating_condition": closure.get("defeated_by"),
        "cleanup_obligations": list(custody.get("cleanup_obligations") or []),
    }


def _lease_args(work: dict[str, Any]) -> argparse.Namespace:
    return argparse.Namespace(
        definition=DEFINITION, definition_kind="skill", provenance="SYSTEM_AUTHORED",
        definition_version="1", derives_from=None, definition_source=DEFINITION,
        grant=None, authority_type=None, capability=None, effect_ceiling="RECORD_LOCAL",
        budget=None, emit=None, minutes=lease_commands.DEFAULT_MINUTES,
        closure=work["closure_condition"] or "", defeat=work["defeating_condition"] or "",
        concern_kind="concern", reference=work["address"], capability_served=None,
        principal=None,
    )


def take_lease(root: Path, directory: Path, session: str, work: dict[str, Any],
               controller: str | None) -> dict[str, Any]:
    """Layer 4: hold the work under a lease the contract accepts, in the shared store.

    The holder is this run's instance principal, derived from the session; the durable
    principal the participant speaks as is the controller one step up. The lease keeps
    the two apart, which is the distinction P15-Q1.3 asks for.
    """
    existing = lease_store.leases(directory)
    lease_id = "lease:" + lease_store.slug(f"{work['address']}/{session}")
    lease = lease_commands._build(_lease_args(work), lease_id, session,
                                  "PARENT", None, controller,
                                  lease_store.next_fence(existing, lease_id))
    lease_commands._validate(lease, root)
    lease_store.append(directory, lease_store.LEASES_LOG,
                       {"event": "take", "lease_id": lease_id, "session": session,
                        "lease": lease})
    return lease


def _bind(document: dict[str, Any], operation_id: str, session: str, principal_id: str,
          arguments: dict[str, Any]) -> dict[str, Any]:
    try:
        request = invocation_request(document, operation_id, MODEL, principal_id,
                                     "fresh-participation", arguments, session_id=session,
                                     session_binding_id=SESSION_BINDING,
                                     principal_id=principal_id)
    except BindingRefusal as refusal:
        return {"verdict": "REFUSED", "code": refusal.code, "interface_binding_id": None}
    return {"verdict": "BOUND", "code": None,
            "interface_binding_id": request["interface_binding_id"]}


def reachable_capability(session: str, principal_id: str) -> dict[str, Any]:
    """Layer 5: discover one reachable operation and bind an invocation to this session.

    Capability comes from the derived Node Interface; authority is not read here. The
    same operation is bound twice: once as this session, once carrying another session's
    id in its arguments, which the binding must refuse rather than attribute.
    """
    document, defects = rebuild()
    if defects:
        return {"defects": defects}
    candidates = [record for record in document["operations"]
                  if record["facts"].get("reachable") and MODEL in record["actor_kinds"]]
    if not candidates:
        return {"defects": ["no reachable operation admits a MODEL actor"]}
    record = resolve(document, sorted(c["operation_id"] for c in candidates)[0])
    return {
        "operation_id": record["operation_id"],
        "required_authority": record["required_authority"],
        "effect_class": record["effect_class"],
        "binding": _bind(document, record["operation_id"], session, principal_id, {}),
        "foreign_binding": _bind(document, record["operation_id"], session, principal_id,
                                 {"session_id": session + "-other"}),
        "defects": [],
    }


def graded_authority(root: Path, actor_id: str, capability: dict[str, Any]) -> dict[str, Any]:
    """Layer 6: grade this actor against the standing grants, separately from capability.

    The request is the participant's own: its actor is the principal it speaks as.
    A refusal is the ordinary reading for a principal no grant names.
    """
    grants = json.loads((root / GRANTS).read_text(encoding="utf-8"))["grants"]
    request = {
        "request_schema": "soveraeign-authority-request/v1",
        "actor_id": actor_id,
        "capability": "repository.commit",
        "effect_class": capability.get("effect_class") or "RECORD_LOCAL",
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "branch": "main",
        "paths": ["scripts/sov_fresh.py"],
        "evidence": {"checks": {"verify": "PASS", "lint": "PASS"}},
    }
    result = authority.evaluate(grants, request)
    considered = [item["grant_id"] for item in result.get("considered", [])]
    return {
        "verdict": result["verdict"],
        "code": result.get("code"),
        "grant_id": result.get("grant_id") or (considered[0] if considered else None),
        "grants_considered": considered,
    }
