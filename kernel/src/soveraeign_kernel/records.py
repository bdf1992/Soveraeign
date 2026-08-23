"""Logical records the shared kernel governs, compiled from ``SPEC.md``.

Each class carries the field block ``SPEC.md`` declares for the object and
nothing a storage engine would add. ``to_dict`` is the canonical projection the
kernel digests and journals; the dataclass itself is the in-memory projection.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

RECORD_STANDINGS = ("RECORDED", "ADMITTED", "RATIFIED", "EFFECTIVE")
AUTHORITY_TYPES = ("VERIFICATION", "JUDGEMENT")
ACTOR_KINDS = ("HUMAN", "MODEL", "WORKER", "SYSTEM")
EFFECT_CLASSES = ("RECORD_LOCAL", "RESOURCE_CONSUMPTION", "EXTERNAL_WORLD")
ATTESTATION_OUTCOMES = ("REPRODUCED", "DISSENTED", "UNATTESTABLE")
RUN_OUTCOMES = ("ATTEMPTED", "COMMITTED", "FAILED", "REFUSED", "UNRESOLVED")

# The fourteen legal transitions of SPEC.md, so every binding discovers one list.
LEGAL_TRANSITIONS = (
    "capture_source", "read_source", "submit_proposal", "admit", "ratify", "attest",
    "make_effective", "begin_run", "report_run", "observe_run", "settle_run", "retract",
    "cross", "invoke_model",
)

# Transitions this reference realizes; the rest are realized by a service or adapter
# that composes these (ENGINEERING.md, Composing larger motion).
KERNEL_TRANSITIONS = (
    "submit_proposal", "admit", "ratify", "attest", "make_effective",
    "begin_run", "report_run", "observe_run", "settle_run", "retract",
)

PLAN_FIELDS = (
    "operation_id", "operation_type", "requester_id", "interface_id", "input_addresses",
    "input_digests", "readings", "configuration_digest", "required_capabilities",
    "preconditions", "expected_observations", "effect_class", "limits", "refusal_behavior",
    "created_at",
)


@dataclass
class AuthorityGrant:
    """A typed, scoped, budgeted, time-bound, revocable grant (SPEC.md AuthorityGrant)."""

    grant_id: str
    issuer_id: str
    actor_id: str
    authority_type: str
    capability: str
    scope: str
    budget: int
    valid_from: str
    valid_until: str
    revoked_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Record:
    """A proposal and its standing history (SPEC.md Proposal; Historical standing).

    ``standing_history`` only grows. ``effective`` is held apart from it because
    current effectiveness is not a standing (CLASSIFICATION.md, Standing and
    outcomes) and a counter-record may clear it without touching history.
    """

    record_id: str
    actor_id: str
    actor_kind: str
    content_address: str
    source_addresses: list[str]
    input_digests: list[str]
    cost_record: dict[str, Any]
    required_authority_type: str
    scope: str
    created_at: str
    standing_history: list[str] = field(default_factory=lambda: ["RECORDED"])
    effective: bool = False
    countered_by: list[str] = field(default_factory=list)

    @property
    def standing(self) -> str:
        return self.standing_history[-1]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Attestation:
    """A validator's reproduction outcome for a ratified claim (SPEC.md Attestation)."""

    attestation_id: str
    claim_id: str
    validator_id: str
    validator_version: str
    input_addresses: list[str]
    input_digests: list[str]
    run_id: str | None
    outcome: str
    evidence_addresses: list[str]
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Run:
    """One attributed attempt under a plan, fenced by a lease when delegated."""

    run_id: str
    operation_id: str
    actor_id: str
    worker_id: str | None
    input_state_digest: str
    lease_fence: str | None
    lease_expires_at: str | None
    started_at: str
    effect_class: str
    expected_observations: list[dict[str, Any]]
    completed_at: str | None = None
    outcome: str = "ATTEMPTED"
    emitted_record_addresses: list[str] = field(default_factory=list)
    report: dict[str, Any] | None = None
    observation_ids: list[str] = field(default_factory=list)
    begin_receipt_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Observation:
    """Independent evidence about a run's durable results (SPEC.md Observation)."""

    observation_id: str
    run_id: str
    observer_id: str
    observer_relation: str
    observed_state_addresses: list[str]
    observed_state_digests: list[str]
    predicate_results: list[dict[str, Any]]
    observed_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CounterRecord:
    """The retraction act (SPEC.md Retraction). It names what it did not undo."""

    counter_record_id: str
    target_record_id: str
    target_receipt_id: str
    actor_id: str
    authority_grant_id: str
    reason: str
    effect_class: str
    not_reversed: str | None
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
