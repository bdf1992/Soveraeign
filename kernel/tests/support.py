"""Shared test scaffolding: a kernel with an injectable clock and deterministic ids."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
import json
import sys
import unittest

KERNEL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = KERNEL_ROOT.parent
sys.path.insert(0, str(KERNEL_ROOT / "src"))

from soveraeign_kernel import AuthorityGrant, Kernel, sequential_ids  # noqa: E402

MATRIX = json.loads((KERNEL_ROOT / "fixtures" / "transition-matrix.json").read_text("utf-8"))
EXPECTED = {case["id"]: case for case in MATRIX["cases"]}
COVERED: dict[str, dict[str, Any]] = {}

T0 = datetime(2026, 8, 23, 12, 0, tzinfo=timezone.utc)
BDO, MODEL, WORKER, WITNESS = ("urn:soveraeign:actor:bdo", "urn:soveraeign:actor:model",
                               "urn:soveraeign:actor:worker", "urn:soveraeign:actor:witness")


class Clock:
    def __init__(self) -> None:
        self.now = T0

    def advance(self, seconds: int) -> None:
        self.now = self.now + timedelta(seconds=seconds)

    def __call__(self) -> datetime:
        return self.now


def grant(kernel: Kernel, grant_id: str, actor: str, authority_type: str, capability: str,
          scope: str = "*", budget: int = 10, valid_until: str = "2026-12-31T00:00:00Z",
          revoked_at: str | None = None) -> AuthorityGrant:
    return kernel.register_grant(AuthorityGrant(
        grant_id=grant_id, issuer_id=BDO, actor_id=actor, authority_type=authority_type,
        capability=capability, scope=scope, budget=budget, valid_from="2026-01-01T00:00:00Z",
        valid_until=valid_until, revoked_at=revoked_at))


def plan(**overrides: Any) -> dict[str, Any]:
    base = {
        "operation_id": "urn:soveraeign:operation:derive-1", "operation_type": "asset/derive",
        "requester_id": BDO, "interface_id": "urn:soveraeign:interface:test",
        "input_addresses": ["urn:soveraeign:version:1"], "input_digests": ["sha256:v1"],
        "readings": [{"reader_id": "r", "reader_version": "1"}],
        "configuration_digest": "sha256:cfg", "required_capabilities": ["operate"],
        "preconditions": [{"predicate": "version_present"}],
        "expected_observations": [{"predicate": "derivative_present"}],
        "effect_class": "RECORD_LOCAL", "limits": {"seconds": 60},
        "refusal_behavior": {"reason_codes": ["STALE_LEASE"], "receipt_required": True},
        "created_at": "2026-08-23T12:00:00Z",
    }
    base.update(overrides)
    return base


class KernelCase(unittest.TestCase):
    """Base case: fresh kernel, fixed clock, and fixture-driven expectations."""

    def setUp(self) -> None:
        self.clock = Clock()
        self.kernel = Kernel(clock=self.clock, id_factory=sequential_ids())
        grant(self.kernel, "g-judgement", BDO, "JUDGEMENT", "ratify")
        grant(self.kernel, "g-retract", BDO, "JUDGEMENT", "retract")
        grant(self.kernel, "g-verify", MODEL, "VERIFICATION", "ratify")
        grant(self.kernel, "g-operate", BDO, "VERIFICATION", "operate")

    def expect(self, case_id: str, receipt: dict[str, Any]) -> dict[str, Any]:
        """Assert the receipt matches the declared matrix case and mark it covered."""
        case = EXPECTED[case_id]
        self.assertEqual(receipt["outcome"], case["expected"]["outcome"], case_id)
        self.assertEqual(receipt["reason_code"], case["expected"]["reason_code"], case_id)
        COVERED[case_id] = receipt
        return receipt

    def submit(self, **overrides: Any) -> dict[str, Any]:
        fields = {"actor_id": MODEL, "actor_kind": "MODEL", "content_address": "sha256:content",
                  "source_addresses": ["urn:soveraeign:source:1"], "input_digests": ["sha256:in1"],
                  "cost_record": {"tokens": 12}, "required_authority_type": "JUDGEMENT",
                  "scope": "asset/1"}
        fields.update(overrides)
        return self.kernel.submit_proposal(**fields)

    def recorded(self, **overrides: Any) -> str:
        return self.submit(**overrides)["emitted_record_addresses"][0]

    def admitted(self, **overrides: Any) -> str:
        record_id = self.recorded(**overrides)
        receipt = self.kernel.admit(record_id, actor_id=BDO, actor_kind="HUMAN",
                                    expected_state=self.kernel.state_digest(record_id),
                                    predicate_results=[{"predicate": "complete", "result": True}])
        assert receipt["outcome"] == "COMMITTED", receipt
        return record_id

    def ratified(self, **overrides: Any) -> str:
        record_id = self.admitted(**overrides)
        receipt = self.kernel.ratify(record_id, actor_id=BDO, actor_kind="HUMAN",
                                     expected_state=self.kernel.state_digest(record_id),
                                     grant_id="g-judgement")
        assert receipt["outcome"] == "COMMITTED", receipt
        return record_id

    def attested(self, record_id: str, outcome: str = "REPRODUCED",
                 input_digests: list[str] | None = None) -> dict[str, Any]:
        return self.kernel.attest(record_id, validator_id=WITNESS, validator_version="1.0",
                                  input_addresses=["urn:soveraeign:source:1"],
                                  input_digests=input_digests or ["sha256:in1"], run_id=None,
                                  outcome=outcome, evidence_addresses=["sha256:evidence"])

    def begun(self, worker: str | None = WORKER, **overrides: Any) -> str:
        receipt = self.kernel.begin_run(plan(**overrides), actor_id=BDO, actor_kind="HUMAN",
                                        grant_id="g-operate", worker_id=worker, lease_seconds=30)
        assert receipt["outcome"] == "COMMITTED", receipt
        return receipt["emitted_record_addresses"][0]

    def reported(self, run_id: str, claimed: str = "COMMITTED") -> dict[str, Any]:
        run = self.kernel.runs[run_id]
        return self.kernel.report_run(run_id, worker_id=WORKER, lease_fence=run.lease_fence,
                                      outputs=[{"address": "urn:soveraeign:derivative:1",
                                                "digest": "sha256:d1"}], claimed_outcome=claimed)

    def observed(self, run_id: str, result: Any = True) -> dict[str, Any]:
        return self.kernel.observe_run(
            run_id, observer_id=WITNESS, observer_relation="INDEPENDENT_READ_OF_DURABLE_STATE",
            observed_state_addresses=["urn:soveraeign:derivative:1"],
            observed_state_digests=["sha256:d1"],
            predicate_results=[{"predicate": "derivative_present", "result": result}])

    def settled(self, run_id: str, expected_state: str | None = "current",
                input_digest: str | None = None) -> dict[str, Any]:
        run = self.kernel.runs[run_id]
        if expected_state == "current":
            expected_state = self.kernel.run_state_digest(run_id)
        return self.kernel.settle_run(
            run_id, actor_id="urn:soveraeign:actor:kernel", expected_state=expected_state,
            current_input_state_digest=input_digest or run.input_state_digest)
