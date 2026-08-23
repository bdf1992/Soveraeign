"""Run transitions: begin, report, observe, settle.

A run is one attributed attempt under a complete ``OperationPlan``. Delegated
execution is fenced by a lease; a report under a stale or expired lease is
refused. The executor's report is stored and never settles anything (C7). An
observation must come from someone other than the executor and must say how it
avoids relying on the report. Settlement reads the observation, never the
report, and refuses when the declared pre-state of the run is no longer current.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from . import reasons
from .base import KernelBase
from .digests import digest_of
from .records import PLAN_FIELDS, Observation, Run

EXECUTOR_RELATIONS = ("EXECUTOR", "EXECUTOR_REPORT", "")
SETTLEMENT_REASONS = {"COMMITTED": None, "FAILED": reasons.PREDICATE_FAILED,
                      "UNRESOLVED": reasons.PREDICATE_UNRESOLVED}


class RunTransitions(KernelBase):
    """Mixin realizing the run rows of the transition contract."""

    def _run_inputs(self, run_id: str) -> list[dict[str, str]]:
        return [{"address": run_id, "digest": self.run_state_digest(run_id) or "sha256:absent"}]

    def begin_run(self, plan: dict[str, Any], *, actor_id: str, actor_kind: str,
                  grant_id: str | None, worker_id: str | None = None,
                  lease_seconds: int | None = None) -> dict[str, Any]:
        """Open a run under a complete plan; issue a fenced lease when delegated."""
        inputs = [{"address": address, "digest": digest}
                  for address, digest in zip(plan.get("input_addresses") or [],
                                             plan.get("input_digests") or [])]
        effect_class = plan.get("effect_class") or "RECORD_LOCAL"
        attempt = self.attempt("begin_run", actor_id=actor_id, actor_kind=actor_kind,
                               inputs=inputs or [{"address": "urn:soveraeign:absent",
                                                  "digest": "sha256:absent"}],
                               effect_class=effect_class, grant_ids=[grant_id] if grant_id else [],
                               operation_id=plan.get("operation_id"))
        missing = [name for name in PLAN_FIELDS if plan.get(name) in (None, "", [], {})]
        if not attempt.check("plan_complete", not missing, missing=missing):
            return attempt.refuse(reasons.INCOMPLETE_PLAN, f"plan missing {', '.join(missing)}")
        if not attempt.check("effect_class_admitted", effect_class != "EXTERNAL_WORLD"):
            return attempt.refuse(reasons.EFFECT_CLASS_REFUSED,
                                  "EXTERNAL_WORLD is refused in Phase I")
        capabilities = plan["required_capabilities"]
        capability = capabilities[0] if capabilities else "operate"
        if not attempt.check_authority(grant_id, authority_type="VERIFICATION",
                                       capability=capability, scope=plan["operation_type"]):
            return attempt.refuse(reasons.AUTHORITY_REFUSED, "no live grant for the plan")
        run = Run(run_id=self.new_id("run"), operation_id=plan["operation_id"], actor_id=actor_id,
                  worker_id=worker_id, input_state_digest=digest_of(plan["input_digests"]),
                  lease_fence=None, lease_expires_at=None, started_at=self.timestamp(),
                  effect_class=effect_class, expected_observations=plan["expected_observations"])
        if worker_id:
            run.lease_fence = self.new_id("fence")
            expires = self.now() + timedelta(seconds=lease_seconds or 60)
            run.lease_expires_at = expires.isoformat().replace("+00:00", "Z")
        self.runs[run.run_id] = run
        self.journal.append("RUN", run.to_dict())
        receipt = attempt.commit(event_outcome="ATTEMPTED", phase="ATTEMPTED",
                                 reason="plan complete; gates passed", emitted=[run.run_id])
        run.begin_receipt_id = receipt["receipt_id"]
        return receipt

    def report_run(self, run_id: str, *, worker_id: str, lease_fence: str | None,
                   outputs: list[dict[str, str]], claimed_outcome: str) -> dict[str, Any]:
        """Store the executor's report under a current lease. It settles nothing."""
        attempt = self.attempt("report_run", actor_id=worker_id, actor_kind="WORKER",
                               inputs=self._run_inputs(run_id),
                               operation_id=self._operation_of(run_id))
        run = self.runs.get(run_id)
        if not attempt.check("run_present", run is not None):
            return attempt.refuse(reasons.TARGET_UNKNOWN, "no such run")
        if not attempt.check("run_open", run.outcome == "ATTEMPTED"):
            return attempt.refuse(reasons.STANDING_REFUSED, f"run is {run.outcome}")
        current = run.lease_fence is not None and lease_fence == run.lease_fence
        attempt.check("lease_current", current, presented=lease_fence)
        unexpired = bool(run.lease_expires_at) and self.timestamp() <= run.lease_expires_at
        attempt.check("lease_unexpired", unexpired, expires_at=run.lease_expires_at)
        if not (current and unexpired and attempt.check("worker_matches",
                                                         run.worker_id == worker_id)):
            return attempt.refuse(reasons.STALE_LEASE, "lease is not current for this worker")
        run.report = {"worker_id": worker_id, "outputs": outputs,
                      "claimed_outcome": claimed_outcome, "reported_at": self.timestamp()}
        run.emitted_record_addresses = [item["address"] for item in outputs]
        self.journal.append("REPORT", {"run_id": run_id, **run.report})
        return attempt.commit(event_outcome="ATTEMPTED", phase="REPORTED", outputs=outputs,
                              reason="executor report stored; not settled")

    def observe_run(self, run_id: str, *, observer_id: str, observer_relation: str,
                    observed_state_addresses: list[str], observed_state_digests: list[str],
                    predicate_results: list[dict[str, Any]]) -> dict[str, Any]:
        """Record independent evidence about the run's durable results."""
        attempt = self.attempt("observe_run", actor_id=observer_id, actor_kind="SYSTEM",
                               inputs=self._run_inputs(run_id),
                               operation_id=self._operation_of(run_id))
        run = self.runs.get(run_id)
        if not attempt.check("run_present", run is not None):
            return attempt.refuse(reasons.TARGET_UNKNOWN, "no such run")
        independent = (observer_id not in (run.worker_id, run.actor_id)
                       and observer_relation not in EXECUTOR_RELATIONS)
        if not attempt.check("observer_independent", independent, relation=observer_relation):
            return attempt.refuse(reasons.OBSERVER_NOT_INDEPENDENT,
                                  "observer is the executor or relies on its report")
        expected = {item.get("predicate") for item in run.expected_observations}
        observed = {item.get("predicate") for item in predicate_results}
        if not attempt.check("expected_predicates_observed", expected <= observed,
                             missing=sorted(expected - observed)):
            return attempt.refuse(reasons.OBSERVATION_MISSING, "expected predicates not observed")
        observation = Observation(
            observation_id=self.new_id("observation"), run_id=run_id, observer_id=observer_id,
            observer_relation=observer_relation, observed_state_addresses=observed_state_addresses,
            observed_state_digests=observed_state_digests, predicate_results=predicate_results,
            observed_at=self.timestamp())
        self.observations[observation.observation_id] = observation
        run.observation_ids.append(observation.observation_id)
        self.journal.append("OBSERVATION", observation.to_dict())
        return attempt.commit(event_outcome="ATTEMPTED", phase="OBSERVED",
                              reason="independent observation recorded",
                              emitted=[observation.observation_id],
                              evidence=observed_state_addresses)

    def settle_run(self, run_id: str, *, actor_id: str, expected_state: str | None,
                   current_input_state_digest: str) -> dict[str, Any]:
        """Close the run from its observations: ``COMMITTED``, ``FAILED``, or ``UNRESOLVED``."""
        attempt = self.attempt("settle_run", actor_id=actor_id, actor_kind="SYSTEM",
                               inputs=self._run_inputs(run_id),
                               operation_id=self._operation_of(run_id))
        run = self.runs.get(run_id)
        if not attempt.check("run_present", run is not None):
            return attempt.refuse(reasons.TARGET_UNKNOWN, "no such run")
        if not attempt.check_pre_state(expected_state, self.run_state_digest(run_id)):
            return attempt.refuse(reasons.STALE_STATE, "declared run pre-state is not current")
        if not attempt.check("input_state_current",
                             current_input_state_digest == run.input_state_digest):
            return attempt.refuse(reasons.STALE_STATE, "input state changed since the plan")
        if not attempt.check("run_open", run.outcome == "ATTEMPTED"):
            return attempt.refuse(reasons.STANDING_REFUSED, f"run is {run.outcome}")
        observations = [self.observations[item] for item in run.observation_ids]
        if not attempt.check("observation_present", bool(observations)):
            return attempt.refuse(reasons.OBSERVATION_MISSING,
                                  "an executor report is not an observation")
        results = [item.get("result") for obs in observations for item in obs.predicate_results]
        outcome = ("UNRESOLVED" if any(result is None for result in results)
                   else "COMMITTED" if all(results) else "FAILED")
        run.outcome, run.completed_at = outcome, self.timestamp()
        return attempt.commit(outcome=outcome, phase="SETTLED",
                              reason=f"settled from {len(observations)} observation(s)",
                              reason_code=SETTLEMENT_REASONS[outcome],
                              emitted=run.emitted_record_addresses,
                              evidence=[obs.observation_id for obs in observations],
                              prior_receipt_id=run.begin_receipt_id)

    def _operation_of(self, run_id: str) -> str | None:
        run = self.runs.get(run_id)
        return run.operation_id if run else None
