"""The typed action a board survey proposes, and the batch that carries a set of them.

Every action states four things a reviewer would otherwise have to reconstruct: what it
would do, the evidence that it is needed, the rule that makes it the right move, and
whether the survey is asking for approval at all. An action whose repair needs authorship
or owner judgement is carried as ``REPORT`` disposition so it appears on the same surface
without ever becoming something an approval could execute.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import hashlib
import json

BATCH_SCHEMA_ID = "soveraeign-board-batch/v1"

#: Actions the survey may ask to execute. Each is mechanically derived from a declared
#: contract and is recoverable after the fact, which is why it may carry an approval.
PROPOSABLE = frozenset({"LABEL_ADD", "LABEL_REMOVE", "BRANCH_DELETE"})

#: Actions the survey may only report. Repairing these needs authored metadata or an
#: owner judgement, and a batch approval is the wrong instrument for either.
REPORTABLE = frozenset(
    {"CONTRACT_DEFECT", "CONTRACT_BEHIND", "PR_STALE", "TICKET_UNROUTED", "LABEL_UNMAPPED"}
)

KINDS = PROPOSABLE | REPORTABLE


@dataclass(frozen=True)
class Action:
    """One proposed or reported move against the coordination surface.

    ``evidence`` is what was observed, ``rule`` is the declared authority that turns the
    observation into a recommendation, and ``recommendation`` is the plain-English move.
    ``target`` names the GitHub object; ``argument`` carries the single operand an
    executable action needs, such as a label name or a branch ref.
    """

    kind: str
    target: str
    evidence: str
    rule: str
    recommendation: str
    argument: str = ""
    effect_class: str = "EXTERNAL_WORLD"

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ValueError(f"unknown board action kind: {self.kind}")

    @property
    def disposition(self) -> str:
        """Report whether this action may be approved or is carried for reading only."""
        return "PROPOSE" if self.kind in PROPOSABLE else "REPORT"

    @property
    def identity(self) -> str:
        """Return the stable identity of this action, independent of its position."""
        seed = f"{self.kind}\x1f{self.target}\x1f{self.argument}"
        return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]

    def as_dict(self) -> dict[str, Any]:
        """Render this action as a contract-shaped mapping."""
        return {
            "id": self.identity,
            "kind": self.kind,
            "disposition": self.disposition,
            "target": self.target,
            "argument": self.argument,
            "effect_class": self.effect_class if self.disposition == "PROPOSE" else "OBSERVE_ONLY",
            "evidence": self.evidence,
            "rule": self.rule,
            "recommendation": self.recommendation,
        }


@dataclass
class Batch:
    """A surveyed set of actions plus the capture provenance it was derived from."""

    repository: str
    captured_at: str
    export_digest: str
    actions: list[Action] = field(default_factory=list)

    @property
    def proposed(self) -> list[Action]:
        """Return only the actions an approval may execute."""
        return [action for action in self.actions if action.disposition == "PROPOSE"]

    @property
    def reported(self) -> list[Action]:
        """Return only the actions carried for reading."""
        return [action for action in self.actions if action.disposition == "REPORT"]

    def as_dict(self) -> dict[str, Any]:
        """Render the batch as a contract-shaped mapping."""
        return {
            "batch_schema": BATCH_SCHEMA_ID,
            "repository": self.repository,
            "captured_at": self.captured_at,
            "export_digest": self.export_digest,
            "proposed_count": len(self.proposed),
            "reported_count": len(self.reported),
            "authority": "none granted; approval is the owner's and is recorded per action",
            "note": (
                "A surveyed action is a recommendation with its evidence attached. "
                "Nothing here has been executed and nothing here settles standing."
            ),
            "actions": [action.as_dict() for action in self.actions],
        }

    def dumps(self) -> str:
        """Serialize the batch for the review surface."""
        return json.dumps(self.as_dict(), indent=2) + "\n"


def load_batch(payload: dict[str, Any]) -> Batch:
    """Rebuild a batch from a serialized payload, refusing an unknown schema."""
    schema = payload.get("batch_schema")
    if schema != BATCH_SCHEMA_ID:
        raise ValueError(f"expected {BATCH_SCHEMA_ID}, found {schema!r}")
    batch = Batch(
        repository=payload["repository"],
        captured_at=payload["captured_at"],
        export_digest=payload["export_digest"],
    )
    for entry in payload.get("actions", []):
        batch.actions.append(
            Action(
                kind=entry["kind"],
                target=entry["target"],
                argument=entry.get("argument", ""),
                evidence=entry["evidence"],
                rule=entry["rule"],
                recommendation=entry["recommendation"],
            )
        )
    return batch


def select(batch: Batch, approvals: list[str]) -> tuple[list[Action], list[str]]:
    """Resolve approval tokens against a batch, returning the approved actions and refusals.

    A token is an action id or the literal ``all``. Approving a ``REPORT`` action is
    refused by name rather than silently dropped: a reviewer who approved it believed
    something would happen, and nothing would.
    """
    by_id = {action.identity: action for action in batch.actions}
    if approvals == ["all"]:
        return list(batch.proposed), []
    approved: list[Action] = []
    refusals: list[str] = []
    for token in approvals:
        action = by_id.get(token)
        if action is None:
            refusals.append(f"{token}: no action with that id is in this batch")
        elif action.disposition == "REPORT":
            refusals.append(f"{token}: {action.kind} is report-only and cannot be approved")
        elif action in approved:
            continue
        else:
            approved.append(action)
    return approved, refusals
