"""The host-side layers a fresh participant traverses before it reaches the node.

Every layer reads the artifact or a store the probe opened; none reads the operator
beyond the principal and registry the caller declared. A layer that refuses returns the
refusal rather than raising, because the instrument grades the shape of what was
resolved and a refusal is part of that shape.
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator
import argparse
import json
import os

from sovcustody import model as custody_model
from sovlease import commands as lease_commands
from sovlease import store as lease_store
from sovsession import phase_context, principals, store

EXIT_CUSTODY = "custody:phase-1-5/fresh-participation"
DEFINITION = "scripts/sov_fresh.py"
ENVIRONMENT_INPUTS = (principals.ENV_REGISTRY, principals.ENV_PRINCIPAL)
"""Host variables the resolver honours; `speaking_as` overrides and restores both. Only the
registry can reach the resolver undeclared, and then it is oral history."""


def undeclared_inputs(registry_declared: bool) -> list[str]:
    """Environment inputs the resolver will read that the caller did not declare.

    The principal is always declared explicitly and overrides its variable, so only the
    registry can reach the resolver from the environment, and only when no registry was
    passed in.
    """
    if registry_declared or not os.environ.get(principals.ENV_REGISTRY, "").strip():
        return []
    return [principals.ENV_REGISTRY]


def root_principal(root: Path, registry: Path | None) -> str | None:
    """The root principal named by the registry the resolver itself will read.

    The same path the resolver honours, environment override included, so the issuer
    gate and the principal resolution can never read two different registries.
    """
    path = registry if registry is not None else principals.registry_path(root)
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("root_principal")
    except (OSError, ValueError):
        return None


@contextmanager
def speaking_as(principal_id: str, registry: Path | None) -> Iterator[None]:
    """Declare the principal this participant speaks as, and the registry that names it.

    The registry names a principal; it never authenticates one. Both declarations go
    through the channel the CLI reads, and both are restored on exit.
    """
    saved = {name: os.environ.get(name) for name in ENVIRONMENT_INPUTS}
    os.environ[principals.ENV_PRINCIPAL] = principal_id
    if registry is not None:
        os.environ[principals.ENV_REGISTRY] = str(registry)
    try:
        yield
    finally:
        for name, value in saved.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def open_session(directory: Path, session: str, root: Path, principal_id: str,
                 registry: Path | None) -> dict[str, Any]:
    """Layer 1: register a session with no prior events in this store, and resolve it."""
    with speaking_as(principal_id, registry):
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
        return {"address": None, "custody": None, "closure_condition": None,
                "defeating_condition": None, "cleanup_obligations": []}
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


def orphaned_inventory(directory: Path) -> list[str]:
    """Leases the store itself reads as held by a session that is no longer live."""
    live = {name for name, record in store.sessions(directory).items() if record.get("live")}
    return sorted(lease_store.orphaned(directory, live))
