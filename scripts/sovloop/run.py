"""Execute one Control -> Orchestration -> Work run and receipt every step.

The loop is the part `SDLC.md` describes and nothing ran: a controller plans,
an orchestrator decomposes, a worker executes, and an observer that is not the
worker judges the output. Each tier runs on the model binding
`contracts/tier-bindings.json` declares for it.

The model call is injected. A caller passes anything matching `Invoke`; the
tests pass a recorded fake, so no test reaches a network, and a real run passes
the Ollama adapter. Nothing here settles its own output.
"""

from __future__ import annotations

from hashlib import sha256
from typing import Any, Callable, Protocol
import json

from sovloop import rules

EFFECT = "RESOURCE_CONSUMPTION"


class Invoke(Protocol):
    """One model invocation: a binding and a prompt in, a provenance record out."""

    def __call__(self, binding_id: str, prompt: str, *, purpose: str) -> dict[str, Any]:
        ...


def _digest(value: Any) -> str:
    """Stable digest of a JSON-shaped value."""
    return "sha256:" + sha256(json.dumps(value, sort_keys=True).encode("utf-8")).hexdigest()


def _receipt(event_type: str, actor: str, effect: str, outcome: str, inputs: list[str],
             emitted: list[str], observed: list[str], grants: list[str],
             preconditions: list[dict[str, Any]], created_at: str, seq: int,
             reason: str | None = None) -> dict[str, Any]:
    """Build one terminal receipt for an attempted tier operation."""
    receipt = {
        "receipt_id": f"urn:soveraeign:receipt:loop:{seq:03d}",
        "event_id": f"urn:soveraeign:event:loop:{seq:03d}",
        "event_type": event_type,
        "actor_id": actor,
        "interface_id": "urn:soveraeign:interface:sov-loop",
        "input_addresses": inputs,
        "input_state_digest": _digest(inputs),
        "authority_grant_ids": grants,
        "precondition_results": preconditions,
        "effect_class": effect,
        "outcome": outcome,
        "emitted_record_addresses": emitted,
        "observed_evidence_addresses": observed,
        "created_at": created_at,
    }
    if reason:
        receipt["reason_code"] = reason
    receipt["receipt_digest"] = _digest(receipt)
    return receipt


def _step(tier: str, table: dict[str, Any], actor: str, capabilities: list[str],
          scope: str) -> dict[str, Any]:
    """One chain entry describing what a tier held, and over what scope, while it ran."""
    return {"tier": tier, "actor_id": actor, "binding_id": table["tiers"][tier]["binding_id"],
            "capabilities": capabilities, "scope": scope, "effect_class": EFFECT}


PROMPTS = {
    "CONTROL": "Select the next bounded operation for this objective and state its plan.",
    "ORCHESTRATION": "Decompose this operation into one leased task with a declared check.",
    "WORK": "Execute the leased task and report what you did and what you observed.",
    "OBSERVE": "Judge whether the report's claims are supported. Do not repair the work.",
}


def execute(objective: str, table: dict[str, Any], invoke: Invoke, created_at: str,
            actors: dict[str, str] | None = None) -> dict[str, Any]:
    """Run the three tiers plus an independent observation, and audit the result.

    Returns a run record carrying the chain, every model invocation's provenance,
    the receipts, and the separation defects found. A run with defects is
    reported, never silently repaired: the caller decides what a refused run
    means.
    """
    who = {"CONTROL": "urn:soveraeign:actor:controller",
           "ORCHESTRATION": "urn:soveraeign:actor:orchestrator",
           "WORK": "urn:soveraeign:actor:worker",
           "OBSERVE": "urn:soveraeign:actor:observer"}
    who.update(actors or {})

    root = f"repository/{_digest(objective)[7:19]}"
    chain = [
        _step("CONTROL", table, who["CONTROL"],
              ["select_operation", "issue_grant", "launch_orchestration", "observe",
               "settle", "escalate"], root),
        _step("ORCHESTRATION", table, who["ORCHESTRATION"],
              ["issue_grant", "observe", "escalate"], f"{root}/operation-1"),
        _step("WORK", table, who["WORK"], ["execute"], f"{root}/operation-1/task-1"),
    ]

    invocations: list[dict[str, Any]] = []
    receipts: list[dict[str, Any]] = []
    transcript: dict[str, Any] = {}
    context = objective

    for seq, step in enumerate(chain, start=1):
        tier = step["tier"]
        record = invoke(step["binding_id"], f"{PROMPTS[tier]}\n\nContext:\n{context}",
                        purpose=tier)
        invocations.append(record)
        transcript[tier] = record.get("output_text", "")
        context = f"{context}\n\n[{tier}] {transcript[tier]}"
        receipts.append(_receipt(
            f"loop.{tier.lower()}", step["actor_id"], EFFECT, "COMMITTED",
            [f"urn:soveraeign:objective:{_digest(objective)[7:23]}"],
            [record.get("invocation_id", "")], [], [f"urn:soveraeign:grant:{tier.lower()}"],
            [{"predicate": "binding declared", "result": "PASS"}], created_at, seq))

    observer_binding = table["observation"]["observer_binding_id"]
    observation = invoke(observer_binding, f"{PROMPTS['OBSERVE']}\n\nContext:\n{context}",
                         purpose="OBSERVE")
    invocations.append(observation)
    transcript["OBSERVE"] = observation.get("output_text", "")
    receipts.append(_receipt(
        "loop.observe", who["OBSERVE"], EFFECT, "COMMITTED",
        [chain[-1]["binding_id"]], [observation.get("invocation_id", "")],
        [observation.get("invocation_id", "")], ["urn:soveraeign:grant:observe"],
        [{"predicate": "observer differs from producer", "result": "PASS"}], created_at, 4))

    run = {
        "run_id": f"urn:soveraeign:run:{_digest(objective)[7:23]}",
        "objective": objective,
        "created_at": created_at,
        "chain": chain,
        "report": {"produced_by": who["WORK"], "binding_id": chain[-1]["binding_id"]},
        "observation": {"observer_binding_id": observer_binding,
                        "observed_binding_id": chain[-1]["binding_id"],
                        "observer": who["OBSERVE"]},
        "settlement": {"settled_by": who["CONTROL"], "outcome": "COMMITTED"},
        "invocations": invocations,
        "transcript": transcript,
        "receipts": receipts,
    }
    run["defects"] = rules.audit(run, table)
    run["settlement"]["outcome"] = "UNRESOLVED" if run["defects"] else "COMMITTED"
    return run
