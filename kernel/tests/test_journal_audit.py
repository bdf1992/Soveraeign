"""The journal exposes bypasses, and every emitted record meets the shared contracts."""

from __future__ import annotations

from pathlib import Path
import json
import sys

from support import BDO, MODEL, REPO_ROOT, WORKER, KernelCase, grant, plan

sys.path.insert(0, str(REPO_ROOT / "scripts"))

from sovticket.jsonschema import validate  # noqa: E402

CONTRACTS = REPO_ROOT / "contracts"


def schema(name: str) -> dict:
    return json.loads((CONTRACTS / name).read_text(encoding="utf-8"))


class JournalAudit(KernelCase):
    def full_walk(self) -> str:
        record_id = self.ratified()
        self.attested(record_id)
        self.kernel.make_effective(record_id, actor_id=BDO, actor_kind="HUMAN",
                                   expected_state=self.kernel.state_digest(record_id))
        run_id = self.begun()
        self.reported(run_id)
        self.observed(run_id)
        self.settled(run_id)
        self.kernel.retract(record_id, actor_id=BDO, actor_kind="HUMAN", grant_id="g-retract",
                            reason="walk complete")
        return record_id

    def test_clean_walk_audits_clean(self) -> None:
        self.full_walk()
        self.assertEqual(self.kernel.audit(), [])

    def test_one_receipt_per_attempt(self) -> None:
        self.full_walk()
        self.submit(cost_record=None)  # a refusal is an attempt too
        events = self.kernel.journal.bodies("EVENT")
        receipts = self.kernel.journal.bodies("RECEIPT")
        self.assertEqual(len(events), len(receipts))
        self.assertEqual({e["receipt_id"] for e in events}, {r["receipt_id"] for r in receipts})
        self.assertEqual({e["event_id"] for e in events}, {r["event_id"] for r in receipts})

    def test_emitted_records_meet_contracts(self) -> None:
        self.full_walk()
        self.submit(cost_record=None)
        receipt_schema = schema("receipt.schema.json")
        envelope_schema = schema("event-envelope.schema.json")
        for receipt in self.kernel.journal.bodies("RECEIPT"):
            self.assertEqual(validate(receipt, receipt_schema), [], receipt["event_type"])
        for event in self.kernel.journal.bodies("EVENT"):
            self.assertEqual(validate(event, envelope_schema), [], event["reason"])

    def test_service_edit_around_kernel_is_exposed(self) -> None:
        record_id = self.recorded()
        self.kernel.records[record_id].standing_history.append("RATIFIED")  # a private rule
        defects = self.kernel.audit()
        self.assertTrue(any("standing projection diverges" in d for d in defects), defects)

    def test_service_effectiveness_around_kernel_is_exposed(self) -> None:
        record_id = self.ratified()
        self.kernel.records[record_id].effective = True
        defects = self.kernel.audit()
        self.assertTrue(any("effectiveness diverges" in d for d in defects), defects)

    def test_raw_append_breaks_chain(self) -> None:
        self.recorded()
        rogue = {"sequence": 99, "kind": "RECORD", "body": {}, "prior_digest": "sha256:x",
                 "entry_digest": "sha256:y"}
        self.kernel.journal._entries.append(rogue)
        defects = self.kernel.journal.audit()
        self.assertTrue(any("chain link" in d for d in defects), defects)

    def test_unreceipted_event_is_exposed(self) -> None:
        self.kernel.journal.append("EVENT", {"event_id": "e-rogue", "receipt_id": None})
        self.assertIn("event e-rogue: no receipt", self.kernel.journal.audit())

    def test_retraction_that_erases_is_exposed(self) -> None:
        record_id = self.full_walk()
        journal = self.kernel.journal
        journal._entries = [e for e in journal._entries
                            if not (e["kind"] == "RECORD" and e["body"]["record_id"] == record_id)]
        defects = journal.audit()
        self.assertTrue(any("original record is not on record" in d for d in defects), defects)

    def test_forged_commit_through_attempt_is_exposed(self) -> None:
        record_id = self.recorded()
        forged = self.kernel.attempt("ratify", actor_id=BDO, actor_kind="HUMAN",
                                     inputs=[{"address": record_id, "digest": "sha256:x"}])
        forged.commit(reason="no checks at all")
        self.kernel.records[record_id].standing_history.append("ADMITTED")
        self.kernel.records[record_id].standing_history.append("RATIFIED")
        defects = self.kernel.audit()
        self.assertTrue(any("ratify committed without passing" in d for d in defects), defects)

    def test_fully_fabricated_commit_is_exposed(self) -> None:
        record_id = self.admitted()
        forged = self.kernel.attempt("ratify", actor_id=BDO, actor_kind="HUMAN",
                                     inputs=[{"address": record_id, "digest": "sha256:x"}])
        for predicate in ("record_present", "pre_state_current", "standing_is_admitted",
                          "grant_present", "actor_matches", "type_matches",
                          "capability_matches", "scope_matches", "grant_live",
                          "budget_available"):
            forged.check(predicate, True)
        forged.commit(reason="every predicate fabricated, no grant named")
        self.kernel.records[record_id].standing_history.append("RATIFIED")
        defects = self.kernel.audit()
        self.assertTrue(any("not on record: all of them" in d for d in defects), defects)

    def test_fabricated_commit_under_wrong_grant_fails_replay(self) -> None:
        record_id = self.admitted()  # requires JUDGEMENT; g-verify is VERIFICATION
        forged = self.kernel.attempt("ratify", actor_id=MODEL, actor_kind="MODEL",
                                     inputs=[{"address": record_id, "digest": "sha256:x"}],
                                     grant_ids=["g-verify"])
        for predicate in ("record_present", "pre_state_current", "standing_is_admitted",
                          "grant_present", "actor_matches", "type_matches",
                          "capability_matches", "scope_matches", "grant_live",
                          "budget_available"):
            forged.check(predicate, True)
        forged.commit(reason="fabricated over a real but wrong grant")
        self.kernel.records[record_id].standing_history.append("RATIFIED")
        defects = self.kernel.audit()
        self.assertTrue(any("fails replay of ['type_matches']" in d for d in defects), defects)

    def test_forged_commit_under_unrealized_transition_is_exposed(self) -> None:
        forged = self.kernel.attempt("cross", actor_id=BDO, actor_kind="HUMAN",
                                     inputs=[{"address": "x", "digest": "sha256:x"}])
        forged.commit(reason="no such kernel transition")
        defects = self.kernel.audit()
        self.assertTrue(any("not realized by this kernel" in d for d in defects), defects)

    def test_injected_projections_are_exposed(self) -> None:
        from soveraeign_kernel import Attestation, AuthorityGrant, Observation
        record_id = self.ratified()
        run_id = self.begun()
        self.kernel.grants["g-ghost"] = AuthorityGrant(
            "g-ghost", BDO, BDO, "JUDGEMENT", "ratify", "*", 1, "2026-01-01T00:00:00Z",
            "2026-12-31T00:00:00Z")
        self.kernel.attestations["a-ghost"] = Attestation(
            "a-ghost", record_id, "v", "1", [], ["sha256:in1"], None, "REPRODUCED", [], "t")
        self.kernel.observations["o-ghost"] = Observation(
            "o-ghost", run_id, "urn:soveraeign:actor:worker", "EXECUTOR", [], [],
            [{"predicate": "derivative_present", "result": True}], "t")
        self.kernel.runs[run_id].observation_ids.append("o-ghost")
        defects = self.kernel.audit()
        for expected in ("grant g-ghost: not on record", "attestation a-ghost: not on record",
                         "observation o-ghost: not on record",
                         f"run {run_id}: observations diverge from journal"):
            self.assertIn(expected, defects)

    def test_reset_run_outcome_is_exposed(self) -> None:
        run_id = self.begun()
        self.observed(run_id)
        self.settled(run_id)
        self.kernel.runs[run_id].outcome = "ATTEMPTED"
        self.assertIn(f"run {run_id}: outcome diverges from journal", self.kernel.audit())
        self.settled(run_id)  # a second settlement over the reset projection
        self.assertIn(f"run {run_id}: 2 settlements, expected at most one", self.kernel.audit())

    def test_cleared_counter_is_exposed(self) -> None:
        record_id = self.full_walk()
        self.kernel.records[record_id].countered_by.clear()
        self.assertIn(f"record {record_id}: counters diverge from journal", self.kernel.audit())

    def forge(self, transition: str, target: str, grant_ids: list[str] | None = None,
              actor: str = BDO, emitted: list[str] | None = None,
              operation_id: str | None = None) -> dict:
        """A forger who fabricates every predicate the audit table asks for."""
        from soveraeign_kernel.audit import REQUIRED_PASSING
        forged = self.kernel.attempt(transition, actor_id=actor, actor_kind="HUMAN",
                                     inputs=[{"address": target, "digest": "sha256:x"}],
                                     grant_ids=grant_ids or [], operation_id=operation_id)
        for predicate in REQUIRED_PASSING[transition]:
            forged.check(predicate, True)
        return forged.commit(reason="fabricated", emitted=emitted or [])

    def test_forged_rung_skip_is_exposed(self) -> None:
        record_id = self.recorded()  # RECORDED only; no ADMITTED on record
        self.forge("ratify", record_id, ["g-judgement"])
        defects = self.kernel.audit()
        self.assertTrue(any("journaled standing is 'RECORDED', not 'ADMITTED'" in d
                            for d in defects), defects)

    def test_forged_effectiveness_without_attestation_is_exposed(self) -> None:
        record_id = self.ratified()
        self.forge("make_effective", record_id)
        defects = self.kernel.audit()
        self.assertTrue(any("without a REPRODUCED attestation" in d for d in defects), defects)

    def test_forged_effectiveness_over_counter_is_exposed(self) -> None:
        record_id = self.ratified()
        self.attested(record_id)
        self.kernel.retract(record_id, actor_id=BDO, actor_kind="HUMAN", grant_id="g-retract",
                            reason="withdrawn")
        self.forge("make_effective", record_id)
        defects = self.kernel.audit()
        self.assertTrue(any("over a countered record" in d for d in defects), defects)

    def test_forged_settlement_without_observation_is_exposed(self) -> None:
        run_id = self.begun()
        self.reported(run_id)
        self.forge("settle_run", run_id)
        defects = self.kernel.audit()
        self.assertTrue(any("with no observation on record" in d for d in defects), defects)

    def test_forged_begin_run_fails_replay(self) -> None:
        from soveraeign_kernel import Run
        run = Run("urn:soveraeign:run:forged", "urn:soveraeign:operation:derive-1", MODEL, None,
                  "sha256:v", None, None, "t", "RECORD_LOCAL", [])
        self.kernel.journal.append("PLAN", plan())
        self.kernel.journal.append("RUN", run.to_dict())
        self.forge("begin_run", "urn:soveraeign:version:1", ["g-judgement"], actor=MODEL,
                   emitted=[run.run_id], operation_id=run.operation_id)
        defects = self.kernel.audit()
        self.assertTrue(any("begin_run under g-judgement fails replay" in d for d in defects),
                        defects)
        # A forged begin_run that names no journaled plan is exposed for that instead.
        self.forge("begin_run", "urn:soveraeign:version:1", ["g-operate"], emitted=["r2"])
        self.assertTrue(any("no journaled record or plan" in d for d in self.kernel.audit()))

    def test_raw_bodies_without_receipts_are_exposed(self) -> None:
        record_id = self.ratified()
        run_id = self.begun()
        self.kernel.journal.append("ATTESTATION", {
            "attestation_id": "a-raw", "claim_id": record_id, "validator_id": "v",
            "validator_version": "1", "input_addresses": [], "input_digests": ["sha256:in1"],
            "run_id": None, "outcome": "REPRODUCED", "evidence_addresses": [], "created_at": "t"})
        self.kernel.journal.append("OBSERVATION", {
            "observation_id": "o-raw", "run_id": run_id, "observer_id": WORKER,
            "observer_relation": "EXECUTOR", "observed_state_addresses": [],
            "observed_state_digests": [], "predicate_results": [], "observed_at": "t"})
        defects = self.kernel.audit()
        self.assertIn("attestation a-raw: no attest receipt emits it", defects)
        self.assertIn("observation o-raw: no observe_run receipt emits it", defects)

    def test_gate_and_receipt_share_one_clock_reading(self) -> None:
        receipt = self.kernel.ratify(self.admitted(), actor_id=BDO, actor_kind="HUMAN",
                                     expected_state=None, grant_id="g-judgement")
        self.assertEqual(receipt["created_at"], "2026-08-23T12:00:00Z")

    def test_commit_over_failed_precondition_is_impossible(self) -> None:
        attempt = self.kernel.attempt("admit", actor_id=BDO, actor_kind="HUMAN",
                                      inputs=[{"address": "r", "digest": "sha256:x"}])
        attempt.check("pre_state_current", False)
        with self.assertRaises(RuntimeError):
            attempt.commit(reason="forced")
        self.assertEqual(self.kernel.journal.bodies("RECEIPT"), [])

    def test_mutated_record_fields_are_exposed(self) -> None:
        record_id = self.ratified()
        self.kernel.records[record_id].input_digests = ["sha256:other"]
        self.kernel.records[record_id].scope = "asset/2"
        defects = self.kernel.audit()
        self.assertIn(f"record {record_id}: input_digests diverges from journal", defects)
        self.assertIn(f"record {record_id}: scope diverges from journal", defects)

    def test_spend_is_read_from_the_journal(self) -> None:
        grant(self.kernel, "g-one", BDO, "JUDGEMENT", "ratify", budget=1)
        record_id = self.admitted()
        self.kernel.ratify(record_id, actor_id=BDO, actor_kind="HUMAN",
                           expected_state=self.kernel.state_digest(record_id), grant_id="g-one")
        self.kernel.receipts.clear()  # a projection, not the record
        self.assertEqual(self.kernel.spent("g-one"), 1)
        second = self.admitted()
        receipt = self.kernel.ratify(second, actor_id=BDO, actor_kind="HUMAN",
                                     expected_state=self.kernel.state_digest(second),
                                     grant_id="g-one")
        self.assertEqual(receipt["reason_code"], "AUTHORITY_REFUSED")

    def test_vocabulary_is_enforced_before_an_attempt_opens(self) -> None:
        with self.assertRaises(ValueError):
            self.submit(actor_kind="ROBOT")
        with self.assertRaises(ValueError):
            self.kernel.begin_run(plan(effect_class="EXTERNAL_WORLD_LATER"), actor_id=BDO,
                                  actor_kind="HUMAN", grant_id="g-operate")
        self.assertEqual(len(self.kernel.journal), 4, "only the four setUp grants are on record")

    def test_malformed_grant_is_not_registered(self) -> None:
        with self.assertRaises(ValueError):
            grant(self.kernel, "g-bad", BDO, "JUDGEMENT", "ratify", valid_until="not-a-time")
        with self.assertRaises(ValueError):
            grant(self.kernel, "g-bad", BDO, "OPINION", "ratify")
        self.assertNotIn("g-bad", self.kernel.grants)

    def test_legal_transitions_are_discoverable(self) -> None:
        listed = self.kernel.transitions()
        self.assertEqual(len(listed["legal"]), 14)
        self.assertTrue(set(listed["realized_by_kernel"]) <= set(listed["legal"]))
        for name in listed["realized_by_kernel"]:
            self.assertTrue(callable(getattr(self.kernel, name)), name)

    def test_fixture_file_is_well_formed(self) -> None:
        path = Path(__file__).resolve().parents[1] / "fixtures" / "transition-matrix.json"
        matrix = json.loads(path.read_text(encoding="utf-8"))
        ids = [case["id"] for case in matrix["cases"]]
        self.assertEqual(len(ids), len(set(ids)), "duplicate case id")
        for case in matrix["cases"]:
            self.assertIn(case["polarity"], ("positive", "defeating"))
            if case["polarity"] == "defeating":
                self.assertTrue(case.get("defeats"), case["id"])
