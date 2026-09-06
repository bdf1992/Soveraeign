"""One fresh-participation run: the closed path from entry to a graded observation.

The path is: host session -> principal -> campaign -> work -> lease -> node session and
grant -> one crossing, plus two crossings the node must refuse -> Record projection ->
host session end -> survival and cleanup read back -> instrument. The last layer is a
check whose result is derived from the run, which is what closes a vertical slice under
`contracts/work-circuit.json`. Every variant is a state this node can actually be in.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import sys
import uuid

from sovfresh import layers, node as nodelayer
from sovkernel.jsonschema import validate
from sovlease import store as lease_store
from sovnode.interface_inputs import rebuild
from sovsession import store

ROOT = Path(__file__).resolve().parents[2]
CONFORMANCE = ROOT / "conformance"
if str(CONFORMANCE) not in sys.path:
    sys.path.insert(0, str(CONFORMANCE))

import commissioning  # noqa: E402

PREDICATES = ("P15-Q1.1", "P15-Q1.2", "P15-Q1.3")
PROJECTION_SCHEMA = ROOT / "contracts" / "record-projection.schema.json"
OTHER_ACTOR = "urn:soveraeign:principal:instance:another-participant"

VARIANTS = {
    "positive": "every layer resolves from the artifact, the store, and the node's records",
    "unregistered-principal": "the participant declares a principal the registry does not name",
    "work-dies-with-session": "the work is written only into the session's own register event",
    "no-grant": "no issuer has opened this node's permits office, so no grant names the actor",
}


def _facts(record: Any, subject: str, actor: str, facts: list[dict[str, Any]]) -> dict[str, Any]:
    for payload in facts:
        record.append("EVENT", subject, actor, payload)
    projection = record.evidence_projection([subject], actor, "PARTICIPANT",
                                            "fresh participation context")
    schema = json.loads(PROJECTION_SCHEMA.read_text(encoding="utf-8"))
    return {"projection": projection, "schema_defects": validate(projection, schema)}


def _refusals(node: Any, document: dict[str, Any], actor: str, admitted: dict[str, Any],
              principal: str | None, issuer: str | None) -> dict[str, Any]:
    """The crossings the node must refuse: a foreign session id, and another actor."""
    session = admitted["session"]
    foreign = nodelayer.bind(document, actor, session, principal,
                             {**nodelayer.ARGUMENTS, "session_id": "another-session"})
    readings = {"foreign_session": nodelayer.cross(node, foreign)}
    if issuer is not None and session is not None:
        node.console.grant(OTHER_ACTOR, nodelayer.OPEN_SESSION, OTHER_ACTOR, granted_by=issuer)
        other = node.console.open_session(OTHER_ACTOR, "MODEL", nodelayer.SESSION_BINDING,
                                          "principal:another-participant")
        readings["other_actor_on_this_session"] = nodelayer.cross(
            node, nodelayer.bind(document, OTHER_ACTOR, session, principal))
        readings["other_actor_without_the_grant"] = nodelayer.cross(
            node, nodelayer.bind(document, OTHER_ACTOR, other, "principal:another-participant"))
    return readings


def _mismatch(readings: dict[str, Any], own: dict[str, Any]) -> str:
    """REFUSED only when the node refused every borrowed fact for the reason it declares.

    A refusal for some other reason is reported as such rather than counted: the clause
    asks that a mismatch refuse, not that something somewhere refused.
    """
    required = {"foreign_session": "SESSION_ATTRIBUTION_CONFLICT",
                "other_actor_on_this_session": "ACTOR_ATTRIBUTION_MISMATCH",
                "other_actor_without_the_grant": "AuthorityRefused"}
    for name, code in required.items():
        reading = readings.get(name)
        if reading is None:
            return "UNOBSERVED"
        if reading["outcome"] != "REFUSED":
            return str(reading["outcome"] or "UNRESOLVED")
        if code not in (reading.get("reason"), reading.get("diagnostic")):
            return f"REFUSED_FOR_ANOTHER_REASON:{reading.get('diagnostic') or reading.get('reason')}"
    return "REFUSED" if own.get("outcome") == "COMMITTED" else "UNOBSERVED"


def run(root: Path, work_dir: Path, principal_id: str, variant: str = "positive", *,
        registry: Path | None = None, issuer: str | None = None,
        declared: set[str] | None = None) -> dict[str, Any]:
    """Run one variant and return observations, grades, and the trace they came from."""
    if variant not in VARIANTS:
        raise ValueError(f"unknown variant {variant!r}; declared: {', '.join(VARIANTS)}")
    undeclared = layers.undeclared_inputs(declared or set())
    directory = work_dir / "sov-sessions"
    session = "fresh-" + uuid.uuid4().hex[:8]
    if variant == "unregistered-principal":
        principal_id = f"principal:unregistered-{session}"
    if variant == "no-grant":
        issuer = None
    trace: list[str] = []

    entry = layers.open_session(directory, session, root, principal_id, registry)
    principal = entry["principal"]["principal"]
    actor = lease_store.principal_id(session)
    trace.append(f"host session {session}; principal {principal or 'UNIDENTIFIED'}; actor {actor}")
    phase = layers.campaign(root)
    trace.append(f"phase {phase['phase_state']} from {phase['governance_context']}")
    work = layers.bounded_work(root)
    lease = None
    if variant != "work-dies-with-session" and work["address"]:
        lease = layers.take_lease(root, directory, session, work, principal)
        trace.append(f"work {work['address']} held by {lease['lease_id']}")
    else:
        store.append(directory, store.SESSIONS_LOG,
                     {"event": "heartbeat", "session": session, "work": work["address"]})
        trace.append(f"work {work['address']} recorded only on the session")

    document, defects = rebuild()
    if defects:
        raise RuntimeError("Node Interface refused: " + "; ".join(defects))
    operation = nodelayer.reachable_operation(document)
    with nodelayer.open_node(work_dir) as node:
        admitted = nodelayer.admit(node, issuer, actor, principal, operation["required_authority"])
        own_binding = nodelayer.bind(document, actor, admitted["session"], principal)
        own = nodelayer.cross(node, own_binding)
        trace.append(f"{operation['operation_id']} as {actor}: {own['outcome']} "
                     f"{own.get('reason') or own.get('grant_id') or ''}".rstrip())
        readings = _refusals(node, document, actor, admitted, principal, issuer)
        for name, reading in readings.items():
            trace.append(f"  {name}: {reading['outcome']} "
                         f"{reading.get('diagnostic') or reading.get('reason')}")
        facts = [{"event": "register", "principal": principal, "actor": actor},
                 {"event": "work", "address": work["address"],
                  "lease": lease["lease_id"] if lease else None},
                 {"event": "crossing", "operation": operation["operation_id"], **own}]
        projected = _facts(node.record, session, actor, facts)
        trace.append(f"projection {projected['projection']['projection_id']}")
        store.append(directory, store.SESSIONS_LOG, {"event": "end", "session": session})
        orphaned = layers.orphaned_inventory(directory)
        console_state = nodelayer.console_session_state(
            node, (admitted["session"] or {}).get("session_id"))
    survives = bool(lease) and lease["lease_id"] in orphaned \
        and layers.bounded_work(root)["address"] == work["address"]
    cleanup = list(work["cleanup_obligations"]) + [f"release {item}" for item in orphaned]
    if console_state == "OPEN":
        cleanup.append(f"close console session {admitted['session']['session_id']}")
    trace.append(f"host session ended; work survives {survives}; cleanup {cleanup}")

    mismatch = _mismatch(readings, own)
    observations = {
        "P15-Q1.1": {
            "principal_id": principal, "session_id": session,
            "phase_state": phase["phase_state"], "work_address": work["address"],
            "capability": operation["operation_id"],
            "required_authority": operation["required_authority"],
            "effect_envelope": operation["effect_class"],
            "governance_context": phase["governance_context"],
            "record_projection_id": projected["projection"]["projection_id"],
            "oral_history_used": bool(undeclared),
        },
        "P15-Q1.2": {
            "work": {"address": work["address"],
                     "custody_or_lease": lease["lease_id"] if lease else None,
                     "closure_condition": work["closure_condition"],
                     "defeating_condition": work["defeating_condition"],
                     "cleanup_obligations": cleanup},
            "survives_session": survives,
        },
        "P15-Q1.3": {
            "identities": {"principal_id": principal,
                           "session_id": (admitted["session"] or {}).get("session_id"),
                           "grant_id": admitted["grant_id"],
                           "interface_binding_id": own_binding["interface_binding_id"]},
            "cross_principal_session_mismatch": mismatch,
        },
    }
    grades = {p: commissioning.evaluate(p, observations[p]) for p in PREDICATES}
    other = list(projected["schema_defects"]) + list(phase["defects"])
    if undeclared:
        other.append("undeclared environment inputs: " + ", ".join(undeclared))
    return {"variant": variant, "session": session, "principal": principal, "actor": actor,
            "issuer": issuer, "node": {"admitted": admitted["reason"], "own": own,
                                       "refusals": readings},
            "observations": observations, "grades": grades, "other_defects": other,
            "passed": not any(grades.values()) and not other, "trace": trace}
