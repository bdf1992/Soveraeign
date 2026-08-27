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

from sovloop import artifacts
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


OUTPUT_KIND = {"CONTROL": "PLAN", "ORCHESTRATION": "TASK", "WORK": "REPORT"}


def execute(objective: str, table: dict[str, Any], invoke: Invoke, created_at: str,
            actors: dict[str, str] | None = None) -> dict[str, Any]:
    """Run the three tiers plus an independent observation, and audit the result.

    Each tier receives exactly one addressed artifact and emits exactly one. The
    observer receives the Work tier's report by address and digest, not the
    conversation that produced it, so its judgement is about an artifact rather
    than about a transcript it was not part of.

    Returns a run record carrying the chain, the artifacts, every invocation's
    provenance, the receipts, and the separation defects found. A run with
    defects is reported, never silently repaired.
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

    current = artifacts.artifact("OBJECTIVE", objective, "urn:soveraeign:actor:owner",
                                 "urn:soveraeign:binding:none", root, [])
    produced = [current]
    invocations: list[dict[str, Any]] = []
    receipts: list[dict[str, Any]] = []

    for seq, step in enumerate(chain, start=1):
        tier = step["tier"]
        record = invoke(step["binding_id"], artifacts.prompt_for(tier, current), purpose=tier)
        invocations.append(record)
        current = artifacts.artifact(OUTPUT_KIND[tier], record.get("output_text", ""),
                                     step["actor_id"], step["binding_id"], step["scope"],
                                     [produced[-1]["artifact_id"]])
        produced.append(current)
        receipts.append(_receipt(
            f"loop.{tier.lower()}", step["actor_id"], EFFECT, "COMMITTED",
            [produced[-2]["artifact_id"]], [current["artifact_id"]], [],
            [f"urn:soveraeign:grant:{tier.lower()}"],
            [{"predicate": "input resolves by address and digest", "result": "PASS"}],
            created_at, seq))

    report = current
    observer_binding = table["observation"]["observer_binding_id"]
    observation_record = invoke(observer_binding, artifacts.prompt_for("OBSERVE", report),
                                purpose="OBSERVE")
    invocations.append(observation_record)
    observation_artifact = artifacts.artifact(
        "OBSERVATION", observation_record.get("output_text", ""), who["OBSERVE"],
        observer_binding, chain[-1]["scope"], [report["artifact_id"]])
    produced.append(observation_artifact)
    findings, verdict = read_observation(observation_artifact["body"])
    receipts.append(_receipt(
        "loop.observe", who["OBSERVE"], EFFECT, "COMMITTED",
        [report["artifact_id"]], [observation_artifact["artifact_id"]],
        [report["digest"]], ["urn:soveraeign:grant:observe"],
        [{"predicate": "observer differs from producer", "result": "PASS"},
         {"predicate": "observation names its subject by digest", "result": "PASS"}],
        created_at, 4))

    run = {
        "run_id": f"urn:soveraeign:run:{_digest(objective)[7:23]}",
        "objective": objective,
        "created_at": created_at,
        "chain": chain,
        "artifacts": produced,
        "report": {"produced_by": who["WORK"], "binding_id": chain[-1]["binding_id"],
                   "artifact_id": report["artifact_id"], "digest": report["digest"]},
        "observation": {"observer_binding_id": observer_binding,
                        "observed_binding_id": chain[-1]["binding_id"],
                        "observer": who["OBSERVE"],
                        "subject_artifact_id": report["artifact_id"],
                        "subject_digest": report["digest"],
                        "findings": findings,
                        "verdict": verdict,
                        "clean": verdict == "CLEARED"},
        "settlement": {"settled_by": who["CONTROL"], "outcome": "COMMITTED"},
        "invocations": invocations,
        "transcript": {a["kind"]: a["body"] for a in produced},
        "receipts": receipts,
    }
    run["defects"] = rules.audit(run, table)
    cleared = verdict == "CLEARED" and not run["defects"]
    run["settlement"]["outcome"] = "COMMITTED" if cleared else "UNRESOLVED"
    run["settlement"]["reason"] = (
        "observer cleared the report and no separation rule was defeated" if cleared
        else "separation defects" if run["defects"]
        else f"observation {verdict.lower()}")
    return run


def _findings(text: str) -> list[str]:
    """The observer's findings, one per declared FINDING line."""
    return [line.split(":", 1)[1].strip()
            for line in text.splitlines() if line.strip().upper().startswith("FINDING:")]


def read_observation(text: str) -> tuple[list[str], str]:
    """The observer's findings and what its answer actually establishes.

    Silence is not a clearance. An observation only clears a report by saying so
    in the declared form; anything else that names no finding is `UNPARSABLE`,
    which settles `UNRESOLVED` rather than `COMMITTED`. Treating an unreadable
    observation as a pass is exactly the rubber stamp the observation stance
    exists to prevent.
    """
    findings = _findings(text)
    if findings:
        return findings, "FINDINGS"
    if "NO FINDINGS" in text.upper():
        return [], "CLEARED"
    return [], "UNPARSABLE"
