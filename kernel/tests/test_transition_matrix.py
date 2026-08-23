"""Execute the declared transition matrix: every positive and defeating case.

Each test asserts the receipt the kernel returned against the case declared in
``kernel/fixtures/transition-matrix.json``. Passing establishes ``BUILT`` only.
"""

from __future__ import annotations

from support import BDO, MODEL, WITNESS, WORKER, KernelCase, grant, plan


class StandingMatrix(KernelCase):
    def test_submit(self) -> None:
        receipt = self.expect("KERNEL-SUBMIT-POS", self.submit())
        record = self.kernel.records[receipt["emitted_record_addresses"][0]]
        self.assertEqual(record.standing_history, ["RECORDED"])
        self.assertFalse(record.effective)
        self.assertEqual(receipt["authority_grant_ids"], [])

    def test_submit_incomplete(self) -> None:
        self.expect("KERNEL-SUBMIT-DEF", self.submit(cost_record=None))
        self.assertEqual(self.kernel.records, {})

    def test_admit(self) -> None:
        record_id = self.recorded()
        receipt = self.kernel.admit(record_id, actor_id=BDO, actor_kind="HUMAN",
                                    expected_state=self.kernel.state_digest(record_id),
                                    predicate_results=[{"predicate": "complete", "result": True}])
        self.expect("KERNEL-ADMIT-POS", receipt)
        self.assertEqual(self.kernel.records[record_id].standing_history, ["RECORDED", "ADMITTED"])

    def test_admit_stale(self) -> None:
        record_id = self.recorded()
        stale = self.kernel.state_digest(record_id)
        self.kernel.admit(record_id, actor_id=BDO, actor_kind="HUMAN", expected_state=stale,
                          predicate_results=[{"predicate": "complete", "result": True}])
        second = self.recorded()
        receipt = self.kernel.admit(second, actor_id=BDO, actor_kind="HUMAN", expected_state=stale,
                                    predicate_results=[{"predicate": "complete", "result": True}])
        self.expect("KERNEL-ADMIT-DEF-STALE", receipt)
        self.assertEqual(self.kernel.records[second].standing, "RECORDED")

    def test_admit_predicate_failed(self) -> None:
        record_id = self.recorded()
        receipt = self.kernel.admit(record_id, actor_id=BDO, actor_kind="HUMAN",
                                    expected_state=self.kernel.state_digest(record_id),
                                    predicate_results=[{"predicate": "complete", "result": False}])
        self.expect("KERNEL-ADMIT-DEF-PREDICATE", receipt)
        self.assertEqual(self.kernel.records[record_id].standing, "RECORDED")

    def ratify_with(self, record_id: str, grant_id: str | None, actor: str = BDO,
                    expected_state: str | None = "current") -> dict:
        if expected_state == "current":
            expected_state = self.kernel.state_digest(record_id)
        return self.kernel.ratify(record_id, actor_id=actor, actor_kind="HUMAN",
                                  expected_state=expected_state, grant_id=grant_id)

    def test_ratify(self) -> None:
        record_id = self.admitted()
        receipt = self.expect("KERNEL-RATIFY-POS", self.ratify_with(record_id, "g-judgement"))
        record = self.kernel.records[record_id]
        self.assertEqual(record.standing_history, ["RECORDED", "ADMITTED", "RATIFIED"])
        self.assertFalse(record.effective, "ratification does not prove current applicability")
        self.assertEqual(receipt["authority_grant_ids"], ["g-judgement"])
        self.assertEqual(self.kernel.spent("g-judgement"), 1)

    def test_ratify_skips_admission(self) -> None:
        self.expect("KERNEL-RATIFY-DEF-SKIP", self.ratify_with(self.recorded(), "g-judgement"))

    def test_ratify_wrong_authority_type(self) -> None:
        receipt = self.ratify_with(self.admitted(), "g-verify", actor=MODEL)
        self.expect("KERNEL-RATIFY-DEF-TYPE", receipt)
        failed = [p["predicate"] for p in receipt["precondition_results"] if not p["result"]]
        self.assertEqual(failed, ["type_matches"])

    def test_ratify_expired(self) -> None:
        grant(self.kernel, "g-old", BDO, "JUDGEMENT", "ratify", valid_until="2026-02-01T00:00:00Z")
        self.expect("KERNEL-RATIFY-DEF-EXPIRED", self.ratify_with(self.admitted(), "g-old"))

    def test_ratify_revoked(self) -> None:
        grant(self.kernel, "g-gone", BDO, "JUDGEMENT", "ratify", revoked_at="2026-08-01T00:00:00Z")
        self.expect("KERNEL-RATIFY-DEF-REVOKED", self.ratify_with(self.admitted(), "g-gone"))

    def test_ratify_budget_exhausted(self) -> None:
        grant(self.kernel, "g-one", BDO, "JUDGEMENT", "ratify", budget=1)
        self.assertEqual(self.ratify_with(self.admitted(), "g-one")["outcome"], "COMMITTED")
        receipt = self.ratify_with(self.admitted(), "g-one")
        self.expect("KERNEL-RATIFY-DEF-BUDGET", receipt)
        self.assertEqual(self.kernel.spent("g-one"), 1, "spend is derived from receipts")

    def test_ratify_out_of_scope(self) -> None:
        grant(self.kernel, "g-elsewhere", BDO, "JUDGEMENT", "ratify", scope="asset/2")
        self.expect("KERNEL-RATIFY-DEF-SCOPE", self.ratify_with(self.admitted(), "g-elsewhere"))

    def test_ratify_stale(self) -> None:
        record_id = self.recorded()
        stale = self.kernel.state_digest(record_id)
        self.kernel.admit(record_id, actor_id=BDO, actor_kind="HUMAN", expected_state=stale,
                          predicate_results=[{"predicate": "complete", "result": True}])
        receipt = self.ratify_with(record_id, "g-judgement", expected_state=stale)
        self.expect("KERNEL-RATIFY-DEF-STALE", receipt)
        self.assertEqual(self.kernel.records[record_id].standing, "ADMITTED")

    def test_attest(self) -> None:
        record_id = self.ratified()
        before = list(self.kernel.records[record_id].standing_history)
        self.expect("KERNEL-ATTEST-POS", self.attested(record_id))
        self.assertEqual(self.kernel.records[record_id].standing_history, before)
        self.assertEqual(len(self.kernel.attestations), 1)

    def test_attest_undeclared(self) -> None:
        record_id = self.ratified()
        receipt = self.kernel.attest(record_id, validator_id=WITNESS, validator_version="",
                                     input_addresses=[], input_digests=["sha256:in1"], run_id=None,
                                     outcome="REPRODUCED", evidence_addresses=[])
        self.expect("KERNEL-ATTEST-DEF-UNDECLARED", receipt)

    def test_attest_unratified(self) -> None:
        self.expect("KERNEL-ATTEST-DEF-UNRATIFIED", self.attested(self.admitted()))

    def effective(self, record_id: str) -> dict:
        return self.kernel.make_effective(record_id, actor_id=BDO, actor_kind="HUMAN",
                                          expected_state=self.kernel.state_digest(record_id))

    def test_make_effective(self) -> None:
        record_id = self.ratified()
        self.attested(record_id)
        self.expect("KERNEL-EFFECTIVE-POS", self.effective(record_id))
        record = self.kernel.records[record_id]
        self.assertTrue(record.effective)
        self.assertEqual(record.standing_history[-1], "EFFECTIVE")

    def test_make_effective_unattested(self) -> None:
        self.expect("KERNEL-EFFECTIVE-DEF-UNATTESTED", self.effective(self.ratified()))

    def test_make_effective_dissent(self) -> None:
        record_id = self.ratified()
        self.attested(record_id, outcome="REPRODUCED")
        self.attested(record_id, outcome="DISSENTED")
        self.expect("KERNEL-EFFECTIVE-DEF-DISSENT", self.effective(record_id))
        self.assertFalse(self.kernel.records[record_id].effective)

    def test_make_effective_changed_inputs(self) -> None:
        record_id = self.ratified()
        self.attested(record_id, outcome="REPRODUCED", input_digests=["sha256:other"])
        self.expect("KERNEL-EFFECTIVE-DEF-CHANGED-INPUTS", self.effective(record_id))

    def test_retract(self) -> None:
        record_id = self.ratified()
        self.attested(record_id)
        self.effective(record_id)
        target_receipt = self.kernel._last_receipt_for(record_id)
        receipt = self.kernel.retract(record_id, actor_id=BDO, actor_kind="HUMAN",
                                      grant_id="g-retract", reason="superseded")
        self.expect("KERNEL-RETRACT-POS", receipt)
        record = self.kernel.records[record_id]
        self.assertFalse(record.effective)
        self.assertEqual(record.standing_history, ["RECORDED", "ADMITTED", "RATIFIED", "EFFECTIVE"])
        self.assertEqual(receipt["prior_receipt_id"], target_receipt)
        self.assertIn(target_receipt, self.kernel.receipts, "original receipt survives")
        self.assertIn(record_id, {b["record_id"] for b in self.kernel.journal.bodies("RECORD")})
        self.assertEqual(len(self.kernel.journal.bodies("COUNTER")), 1)

    def test_retract_without_authority(self) -> None:
        receipt = self.kernel.retract(self.ratified(), actor_id=MODEL, actor_kind="MODEL",
                                      grant_id="g-verify", reason="because")
        self.expect("KERNEL-RETRACT-DEF-AUTHORITY", receipt)

    def test_retract_consumption_unnamed(self) -> None:
        receipt = self.kernel.retract(self.ratified(), actor_id=BDO, actor_kind="HUMAN",
                                      grant_id="g-retract", reason="oops",
                                      effect_class="RESOURCE_CONSUMPTION")
        self.expect("KERNEL-RETRACT-DEF-CONSUMPTION", receipt)


class RunMatrix(KernelCase):
    def test_begin(self) -> None:
        receipt = self.kernel.begin_run(plan(), actor_id=BDO, actor_kind="HUMAN",
                                        grant_id="g-operate", worker_id=WORKER, lease_seconds=30)
        self.expect("KERNEL-BEGIN-POS", receipt)
        run = self.kernel.runs[receipt["emitted_record_addresses"][0]]
        self.assertEqual(run.outcome, "ATTEMPTED")
        self.assertIsNotNone(run.lease_fence)
        event = self.kernel.journal.bodies("EVENT")[-1]
        self.assertEqual((event["event_phase"], event["outcome"]), ("ATTEMPTED", "ATTEMPTED"))

    def test_begin_incomplete_plan(self) -> None:
        receipt = self.kernel.begin_run(plan(expected_observations=[]), actor_id=BDO,
                                        actor_kind="HUMAN", grant_id="g-operate")
        self.expect("KERNEL-BEGIN-DEF-PLAN", receipt)

    def test_begin_external_world(self) -> None:
        receipt = self.kernel.begin_run(plan(effect_class="EXTERNAL_WORLD"), actor_id=BDO,
                                        actor_kind="HUMAN", grant_id="g-operate")
        self.expect("KERNEL-BEGIN-DEF-EXTERNAL", receipt)

    def test_begin_without_grant(self) -> None:
        receipt = self.kernel.begin_run(plan(), actor_id=BDO, actor_kind="HUMAN", grant_id=None)
        self.expect("KERNEL-BEGIN-DEF-AUTHORITY", receipt)

    def test_report(self) -> None:
        run_id = self.begun()
        self.expect("KERNEL-REPORT-POS", self.reported(run_id))
        self.assertEqual(self.kernel.runs[run_id].outcome, "ATTEMPTED", "a report settles nothing")

    def test_report_wrong_fence(self) -> None:
        run_id = self.begun()
        receipt = self.kernel.report_run(run_id, worker_id=WORKER, lease_fence="fence-forged",
                                         outputs=[], claimed_outcome="COMMITTED")
        self.expect("KERNEL-REPORT-DEF-FENCE", receipt)

    def test_report_expired(self) -> None:
        run_id = self.begun()
        self.clock.advance(31)
        self.expect("KERNEL-REPORT-DEF-EXPIRED", self.reported(run_id))

    def test_observe(self) -> None:
        run_id = self.begun()
        self.reported(run_id)
        self.expect("KERNEL-OBSERVE-POS", self.observed(run_id))

    def test_observe_by_executor(self) -> None:
        run_id = self.begun()
        receipt = self.kernel.observe_run(run_id, observer_id=WORKER,
                                          observer_relation="INDEPENDENT",
                                          observed_state_addresses=[], observed_state_digests=[],
                                          predicate_results=[{"predicate": "derivative_present",
                                                              "result": True}])
        self.expect("KERNEL-OBSERVE-DEF-EXECUTOR", receipt)

    def test_observe_from_report(self) -> None:
        run_id = self.begun()
        self.reported(run_id)
        receipt = self.kernel.observe_run(run_id, observer_id=WITNESS,
                                          observer_relation="EXECUTOR_REPORT",
                                          observed_state_addresses=[], observed_state_digests=[],
                                          predicate_results=[{"predicate": "derivative_present",
                                                              "result": True}])
        self.expect("KERNEL-OBSERVE-DEF-RELATION", receipt)

    def test_settle(self) -> None:
        run_id = self.begun()
        begin_receipt = self.kernel.runs[run_id].begin_receipt_id
        self.reported(run_id)
        self.observed(run_id)
        receipt = self.expect("KERNEL-SETTLE-POS", self.settled(run_id))
        self.assertEqual(receipt["prior_receipt_id"], begin_receipt)
        self.assertEqual(self.kernel.runs[run_id].outcome, "COMMITTED")

    def test_settle_failed(self) -> None:
        run_id = self.begun()
        self.reported(run_id, claimed="COMMITTED")
        self.observed(run_id, result=False)
        self.expect("KERNEL-SETTLE-FAILED", self.settled(run_id))

    def test_settle_unresolved(self) -> None:
        run_id = self.begun()
        self.observed(run_id, result=None)
        self.expect("KERNEL-SETTLE-UNRESOLVED", self.settled(run_id))

    def test_settle_from_report_only(self) -> None:
        run_id = self.begun()
        self.reported(run_id, claimed="COMMITTED")
        self.expect("KERNEL-SETTLE-DEF-REPORT-ONLY", self.settled(run_id))
        self.assertEqual(self.kernel.runs[run_id].outcome, "ATTEMPTED")

    def test_settle_stale(self) -> None:
        run_id = self.begun()
        stale = self.kernel.run_state_digest(run_id)
        self.reported(run_id)
        self.observed(run_id)
        self.expect("KERNEL-SETTLE-DEF-STALE", self.settled(run_id, expected_state=stale))

    def test_settle_input_changed(self) -> None:
        run_id = self.begun()
        self.observed(run_id)
        receipt = self.settled(run_id, input_digest="sha256:changed")
        self.expect("KERNEL-SETTLE-DEF-INPUT-CHANGED", receipt)
