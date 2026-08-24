"""Addressed artifacts passed between tiers, and the prompt each tier receives.

The first version of the loop threaded a growing conversation from tier to tier
and handed the observer the whole of it. In a live run the observer said it
could not find a report to judge, which was correct: it had been given a
transcript, not an artifact.

A tier now receives exactly one addressed input with a digest, and emits exactly
one addressed output. The observer receives the Work tier's report the same way,
so it is judging a thing with a name rather than reading a conversation it was
not part of.
"""

from __future__ import annotations

from hashlib import sha256
from typing import Any

KINDS = ("OBJECTIVE", "PLAN", "TASK", "REPORT", "OBSERVATION")


def digest(text: str) -> str:
    """Content digest of an artifact body."""
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


def artifact(kind: str, body: str, produced_by: str, binding_id: str, scope: str,
             inputs: list[str]) -> dict[str, Any]:
    """One addressed artifact: what it is, who made it, and what it was made from."""
    if kind not in KINDS:
        raise ValueError(f"unknown artifact kind {kind!r}")
    body_digest = digest(body)
    return {
        "artifact_id": f"urn:soveraeign:artifact:{kind.lower()}:{body_digest[7:23]}",
        "kind": kind,
        "produced_by": produced_by,
        "binding_id": binding_id,
        "scope": scope,
        "input_addresses": inputs,
        "digest": body_digest,
        "body": body,
    }


def _framed(item: dict[str, Any]) -> str:
    """An artifact rendered for a model: its address first, then its bytes."""
    return (f"ARTIFACT {item['artifact_id']}\n"
            f"kind: {item['kind']}\n"
            f"produced_by: {item['produced_by']}\n"
            f"binding: {item['binding_id']}\n"
            f"digest: {item['digest']}\n"
            f"---\n{item['body']}\n---")


CONTROL = """You hold the Control tier. You may plan and delegate; you may not execute the work
yourself and you may not ratify anything.

Read the objective below and state the single next bounded operation, its declared
check, and what evidence would settle it. Be specific and brief.

{input}"""

ORCHESTRATION = """You hold the Orchestration tier. You may decompose and lease; you may not execute
the work and you may not settle your own operation.

Read the plan below and state exactly one leased task: what the worker must do, what
it must produce, and the check its output must satisfy.

{input}"""

WORK = """You hold the Work tier. You execute the leased task and report. You may not settle
your own output and you may not judge it.

Read the task below and report what you did and what you observed. If you could not
actually perform a step, say so plainly in the report rather than describing what the
step would have produced.

{input}"""

OBSERVE = """You are an independent observer. You did not produce the report below and you may
not repair it. Your job is to find claims the report does not support.

Judge only the report's own text. Treat each of these as unsupported:
- a result stated as fact when the report also says the step was simulated, skipped,
  or not actually run;
- an identifier, digest, hash, or path that is a placeholder rather than a real value;
- a switch to a different model, tool, or method mid-task presented as equivalent;
- an evidence address that is cited but never produced or resolved;
- the producer settling, approving, or accepting its own work.

Output one finding per line, in this form:
FINDING: <the claim> -- <why it is not supported>

Say nothing about claims that are properly supported. If the report contains no
unsupported claim, output exactly: NO FINDINGS

{input}"""

PROMPTS = {"CONTROL": CONTROL, "ORCHESTRATION": ORCHESTRATION,
           "WORK": WORK, "OBSERVE": OBSERVE}


def prompt_for(tier: str, item: dict[str, Any]) -> str:
    """The exact prompt a tier receives, carrying one addressed input."""
    return PROMPTS[tier].format(input=_framed(item))
