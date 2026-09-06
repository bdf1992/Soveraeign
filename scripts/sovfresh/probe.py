"""One fresh-participation run: the closed path from entry to a graded observation.

The path is: session -> principal -> campaign -> work -> lease -> capability ->
authority -> Record projection -> session end -> survival check -> instrument. The last
layer is a check whose result is derived from the run, which is what closes a vertical
slice under `contracts/work-circuit.json`. Variants exist so each predicate's defeating
case fires against the live layers rather than only against a fixture template.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import sys
import uuid

from sovfresh import layers
from sovkernel.jsonschema import validate
from sovlease import store as lease_store
from sovsession import store

ROOT = Path(__file__).resolve().parents[2]
RECORD_SRC = ROOT / "services" / "record" / "src"
if str(RECORD_SRC) not in sys.path:
    sys.path.insert(0, str(RECORD_SRC))

CONFORMANCE = ROOT / "conformance"
if str(CONFORMANCE) not in sys.path:
    sys.path.insert(0, str(CONFORMANCE))

from soveraeign_record_service.core import open_service  # noqa: E402
import commissioning  # noqa: E402

PREDICATES = ("P15-Q1.1", "P15-Q1.2", "P15-Q1.3")

VARIANTS = {
    "positive": "every layer resolves from the artifact and the store the probe opened",
    "unregistered-principal": "the participant declares a principal the registry does not name",
    "work-dies-with-session": "the work is written only into the session's own register event",
    "borrowed-authority": "the authority request carries the standing grant's actor instead "
                          "of the session's own principal",
}

PROJECTION_SCHEMA = ROOT / "contracts" / "record-projection.schema.json"


def _session_name() -> str:
    return "fresh-" + uuid.uuid4().hex[:8]


def _record_entry(root: Path, work_dir: Path, session: str, principal: str,
                  facts: list[tuple[str, str, dict[str, Any]]]) -> dict[str, Any]:
    """Append the run's facts to a Record the probe opened and project them back."""
    service = open_service(work_dir / "record")
    try:
        for subject, kind, payload in facts:
            service.append(kind, subject, principal or "principal:unidentified", payload)
        projection = service.evidence_projection(
            [session], principal or "principal:unidentified", "PARTICIPANT",
            "fresh participation context")
    finally:
        service.close()
    defects = validate(projection, json.loads(PROJECTION_SCHEMA.read_text(encoding="utf-8")))
    return {"projection": projection, "schema_defects": defects}


def run(root: Path, work_dir: Path, principal_id: str, variant: str = "positive") -> dict[str, Any]:
    """Run one variant and return observations, grades, and the trace they came from."""
    if variant not in VARIANTS:
        raise ValueError(f"unknown variant {variant!r}; declared: {', '.join(VARIANTS)}")
    directory = work_dir / "sov-sessions"
    session = _session_name()
    trace: list[str] = []

    entry = layers.open_session(directory, session, root, principal_id)
    claim = entry["principal"]
    resolved_principal = claim["principal"]
    trace.append(f"session {session} registered; principal {resolved_principal or 'UNIDENTIFIED'}")

    phase = layers.campaign(root)
    trace.append(f"phase {phase['phase_state']} from {phase['governance_context']}")

    work = layers.bounded_work(root)
    trace.append(f"work {work['address']}")

    lease: dict[str, Any] | None = None
    if variant != "work-dies-with-session" and work["address"]:
        lease = layers.take_lease(root, directory, session, work, resolved_principal)
        trace.append(f"lease {lease['lease_id']} held")
    else:
        store.append(directory, store.SESSIONS_LOG,
                     {"event": "heartbeat", "session": session, "work": work["address"]})
        trace.append("work recorded only on the session")

    capability = layers.reachable_capability(session, resolved_principal or "")
    trace.append(f"capability {capability.get('operation_id')}: own session "
                 f"{(capability.get('binding') or {}).get('verdict')}, foreign session "
                 f"{(capability.get('foreign_binding') or {}).get('code')}")

    actor = "sov" if variant == "borrowed-authority" else (resolved_principal or "")
    graded = layers.graded_authority(root, actor, capability)
    trace.append(f"authority for {actor!r}: {graded['verdict']} {graded.get('code') or graded.get('grant_id')}")

    facts = [
        (session, "EVENT", {"event": "register", "principal": resolved_principal}),
        (session, "EVENT", {"event": "work", "address": work["address"],
                            "lease": lease["lease_id"] if lease else None}),
        (session, "EVENT", {"event": "capability", **{k: v for k, v in capability.items()
                                                       if k != "defects"}}),
        (session, "EVENT", {"event": "authority", **graded}),
    ]
    projected = _record_entry(root, work_dir, session, resolved_principal or "", facts)
    projection = projected["projection"]
    trace.append(f"projection {projection['projection_id']}")

    store.append(directory, store.SESSIONS_LOG, {"event": "end", "session": session})
    after = lease_store.leases(directory)
    survives = bool(lease) and after.get(lease["lease_id"], {}).get("state") == "HELD" \
        and layers.bounded_work(root)["address"] == work["address"]
    trace.append(f"session ended; work survives: {survives}")

    binding = capability.get("binding") or {}
    foreign = capability.get("foreign_binding") or {}
    # Both neighbouring facts must be refused: another session's id in this session's
    # request, and another actor's grant on this principal's request.
    cross_session = foreign.get("verdict") == "REFUSED"
    cross_principal = graded["verdict"] == "REFUSED"
    mismatch = "REFUSED" if cross_session and cross_principal else (
        graded["verdict"] if not cross_principal else "BOUND")
    cleanup = list(work.get("cleanup_obligations") or [])
    cleanup += [f"release {lease['lease_id']}"] if lease else []
    cleanup += [f"end session {session}"]

    observations = {
        "P15-Q1.1": {
            "principal_id": resolved_principal,
            "session_id": session,
            "phase_state": phase["phase_state"],
            "work_address": work["address"],
            "capability": capability.get("operation_id"),
            "required_authority": capability.get("required_authority"),
            "effect_envelope": capability.get("effect_class"),
            "governance_context": phase["governance_context"],
            "record_projection_id": projection["projection_id"],
            "oral_history_used": False,
        },
        "P15-Q1.2": {
            "work": {
                "address": work["address"],
                "custody_or_lease": lease["lease_id"] if lease else None,
                "closure_condition": work.get("closure_condition"),
                "defeating_condition": work.get("defeating_condition"),
                "cleanup_obligations": cleanup,
            },
            "survives_session": survives,
        },
        "P15-Q1.3": {
            "identities": {
                "principal_id": resolved_principal,
                "session_id": session,
                "grant_id": graded.get("grant_id"),
                "interface_binding_id": binding.get("interface_binding_id")
                or layers.SESSION_BINDING,
            },
            "cross_principal_session_mismatch": mismatch,
        },
    }
    grades = {predicate: commissioning.evaluate(predicate, observations[predicate])
              for predicate in PREDICATES}
    grades_extra = list(projected["schema_defects"]) + list(phase["defects"]) \
        + list(capability.get("defects") or [])
    return {
        "variant": variant,
        "session": session,
        "principal": resolved_principal,
        "observations": observations,
        "grades": grades,
        "other_defects": grades_extra,
        "passed": not any(grades.values()) and not grades_extra,
        "trace": trace,
    }
