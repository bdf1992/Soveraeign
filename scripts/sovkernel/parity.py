"""Prove each participant already decides the way the kernel decides.

Issue #6 requires that all services use the same kernel semantics rather than
private transition rules. `SPEC.md` admits reference implementations only as
participants tested against the contract, so the way to meet that is to drive
both sides on the same fact and compare their decisions - not to rewrite a
working service into the kernel and call the rewrite evidence.

Each correspondence in `contracts/kernel-parity.json` names one fact, the
participant refusal that realizes it, and the kernel refusal it corresponds to.
This module makes the fact happen on both sides. A participant that stops
agreeing fails here rather than diverging quietly.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from sovkernel import participants, transitions as kernel

DIGEST = "a1" * 32


def load_contract(root: Path) -> dict[str, Any]:
    """Load the declared parity correspondences."""
    return json.loads((root / "contracts" / "kernel-parity.json").read_text("utf-8"))


def _kernel_refusal(root: Path, request: dict[str, Any], current: dict[str, Any]) -> str:
    decision = kernel.evaluate(request, kernel.load_table(root), current)
    return "PERMITTED" if decision.permitted else str(decision.reason_code)


KERNEL_FACTS = {
    "a superseded fence may not report": (
        {
            "request_schema": "soveraeign-kernel-transition/v1",
            "transition": "report_run",
            "actor_id": "worker-a",
            "actor_kind": "WORKER",
            "effect_class": "RECORD_LOCAL",
            "reason": "parity fact",
            "declared": {"lease_fence": 1, "lease_expires_at": 2000,
                         "worker_id": "worker-a", "output_record_addresses": ["v1"]},
            "lease": {"holder_id": "worker-a", "fence": 1, "expires_at": 2000},
        },
        {"lease_holder_id": "worker-b", "lease_fence": 2, "now": 1000},
    ),
    "an executor report is not settlement": (
        {
            "request_schema": "soveraeign-kernel-transition/v1",
            "transition": "report_run",
            "actor_id": "worker-a",
            "actor_kind": "WORKER",
            "effect_class": "RECORD_LOCAL",
            "reason": "parity fact",
            "requested_outcome": "COMMITTED",
            "declared": {"lease_fence": 1, "lease_expires_at": 2000,
                         "worker_id": "worker-a", "output_record_addresses": ["v1"]},
            "lease": {"holder_id": "worker-a", "fence": 1, "expires_at": 2000},
        },
        {"lease_holder_id": "worker-a", "lease_fence": 1, "now": 1000},
    ),
    "the actor that built an artifact may not witness it": (
        {
            "request_schema": "soveraeign-kernel-transition/v1",
            "transition": "settle_run",
            "actor_id": "model/worker-a",
            "actor_kind": "MODEL",
            "effect_class": "RECORD_LOCAL",
            "reason": "parity fact",
            "requested_outcome": "COMMITTED",
            "pre_state_digest": DIGEST,
            "declared": {"run_id": "run-1", "input_state_digest": DIGEST,
                         "observation_id": "obs-1"},
            "observation": {"observation_id": "obs-1", "observer_id": "model/worker-a",
                            "observer_relation": "SELF", "satisfactory": True},
        },
        {"state_digest": DIGEST, "reporter_id": "model/worker-a"},
    ),
    "an actor without judgement authority may not ratify": (
        {
            "request_schema": "soveraeign-kernel-transition/v1",
            "transition": "ratify",
            "actor_id": "model/verifier",
            "actor_kind": "MODEL",
            "effect_class": "RECORD_LOCAL",
            "reason": "parity fact",
            "pre_state_digest": DIGEST,
            "declared": {"pre_state_digest": DIGEST, "authority_grant_id": "grant-9"},
            "authority": {"grant_id": "grant-9", "authority_type": "VERIFICATION"},
        },
        {"state_digest": DIGEST},
    ),
    "a model claim without a proposal is incomplete": (
        {
            "request_schema": "soveraeign-kernel-transition/v1",
            "transition": "submit_proposal",
            "actor_id": "model/sov",
            "actor_kind": "MODEL",
            "effect_class": "RECORD_LOCAL",
            "reason": "parity fact",
            # No `source_address`: the claim names nothing the kernel can read back.
            "declared": {"actor_id": "model/sov", "cost": 0, "scope": "thread-1",
                         "required_authority": "JUDGEMENT"},
        },
        {},
    ),
    "no live grant covers this transition": (
        {
            "request_schema": "soveraeign-kernel-transition/v1",
            "transition": "retract",
            "actor_id": "model/stranger",
            "actor_kind": "MODEL",
            "effect_class": "RECORD_LOCAL",
            "reason": "parity fact",
            "declared": {"target_record_address": "record-1", "known_effect": "RECORD_LOCAL",
                         "authority_grant_id": "grant-absent"},
        },
        {"state_digest": DIGEST},
    ),
    "external-world effects are refused in this phase": (
        {
            "request_schema": "soveraeign-kernel-transition/v1",
            "transition": "cross",
            "actor_id": "model/orchestrator",
            "actor_kind": "MODEL",
            "effect_class": "EXTERNAL_WORLD",
            "reason": "parity fact",
            "declared": {"source_address": "src-1", "reader_declaration": "reader-1",
                         "omissions": ["none"], "authority_grant_id": "grant-1",
                         "destination_address": "dst-1"},
        },
        {},
    ),
}


def run(root: Path) -> tuple[list[str], int]:
    """Check every declared correspondence and return failures and the count."""
    contract = load_contract(root)
    observed = {**participants.asset(root), **participants.console(root),
                **participants.ticket(root)}
    failures: list[str] = []
    checked = 0

    for participant in contract["participants"]:
        name = participant["participant"]
        for correspondence in participant["correspondences"]:
            fact = correspondence["fact"]
            checked += 1
            if fact not in KERNEL_FACTS:
                failures.append(f"{name}: no kernel request states the fact {fact!r}")
                continue
            request, current = KERNEL_FACTS[fact]
            actual_kernel = _kernel_refusal(root, request, current)
            actual_participant = observed.get(fact, "NOT OBSERVED")

            if actual_kernel != correspondence["kernel_refusal"]:
                failures.append(
                    f"{name}: {fact!r}: kernel refused {actual_kernel}, "
                    f"contract declares {correspondence['kernel_refusal']}"
                )
            if actual_participant != correspondence["participant_refusal"]:
                failures.append(
                    f"{name}: {fact!r}: participant refused {actual_participant!r}, "
                    f"contract declares {correspondence['participant_refusal']!r}"
                )
            if actual_kernel == "PERMITTED" or actual_participant == "PERMITTED":
                failures.append(
                    f"{name}: {fact!r}: one side permitted what the other refused"
                )
    return failures, checked
