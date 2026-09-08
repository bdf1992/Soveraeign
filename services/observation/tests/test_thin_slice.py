"""Drive the Observation Service thin slice: five operations, every declared refusal.

These are the participant's own tests. They establish `BUILT` for the mechanics and witness
nothing: the service that owns observation cannot observe itself, and the first observation of
this service remains Red work by a different participant (`KNOWN-GAPS.md`, last row).

Two things are held to contracts written before the implementation existed and not edited to
fit it: every inference is validated against `relation-inference.schema.json`, and every
observation against the kernel's `contracts/observation.schema.json`.
"""

from __future__ import annotations

from pathlib import Path
import hashlib
import json
import sys
import unittest

SERVICE = Path(__file__).resolve().parents[1]
ROOT = SERVICE.parents[1]
sys.path.insert(0, str(SERVICE / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from sovkernel.jsonschema import validate  # noqa: E402

from soveraeign_observation_service.relation import EDGES  # noqa: E402
from soveraeign_observation_service import (  # noqa: E402
    DigestMismatch,
    IncompleteProposal,
    ObservationMissing,
    ObservationService,
    ObserverNotIndependent,
    PredicatesUndeclared,
    RelationUndetermined,
    RunNotTerminal,
    RunRecord,
    Unreadable,
    declare_predicates,
    observe_run,
)

INFERENCE_SCHEMA = json.loads(
    (SERVICE / "contracts" / "relation-inference.schema.json").read_text(encoding="utf-8"))
OBSERVATION_SCHEMA = json.loads(
    (ROOT / "contracts" / "observation.schema.json").read_text(encoding="utf-8"))
REQUEST_SCHEMA = json.loads(
    (SERVICE / "contracts" / "observation-request.schema.json").read_text(encoding="utf-8"))

RUN = "urn:soveraeign:run:asset-ingest-1"
SUBJECT = "urn:soveraeign:work:asset-ingest"
OUTPUT_BYTES = b'{"asset_id": "asset-1", "standing": "RECORDED"}'
OUTPUT_DIGEST = hashlib.sha256(OUTPUT_BYTES).hexdigest()


def _profile(name: str) -> dict:
    """An operating profile as the record carries it: an address and the bytes' digest."""
    return {"address": f"profile/{name}",
            "digest": hashlib.sha256(f"profile:{name}".encode("utf-8")).hexdigest()}


WORKER_PROFILE = _profile("sov-worker")
WITNESS_PROFILE = _profile("sov-witness")


def _entry(entry_id: str, kind: str, subject: str, actor: str, payload: dict) -> dict:
    digest = hashlib.sha256(f"{entry_id}|{subject}|{actor}".encode("utf-8")).hexdigest()
    return {"entry_id": entry_id, "kind": kind, "subject": subject, "actor": actor,
            "payload": payload, "entry_digest": digest}


def journal(*, lease_holder="worker-a", grant_id="grant-run", output_actor="worker-a",
            subject=SUBJECT,
            with_outputs=True, with_report=True, omit_subject=False,
            omit_context_kinds=False, witness_context=("OBJECTIVE", "ARTIFACT"),
            witness_profile=WITNESS_PROFILE,
            predicates_author="contract:observation",
            predicates_kind="CONTRACT") -> list[dict]:
    """A run's journal slice: the run, its grants, the launches, and the subject's arrows.

    `witness-z` is launched with subject-side context and its own profile, so it reads
    INDEPENDENT. `helper-h` is handed the builder's reasoning, so it does not.
    """
    lease = {"holder_id": lease_holder, "fence": 1, "expires_at": "2026-09-03T01:00:00Z"}
    attempt = {"event": "ATTEMPTED", "operation_plan_id": "plan-1", "lease": lease,
               "grant_id": grant_id, "profile": WORKER_PROFILE}
    if not omit_subject:
        attempt["subject_id"] = subject
    launch_witness = {"event": "LAUNCH", "launched_actor_id": "witness-z",
                      "launched_by": "worker-a", "profile": witness_profile,
                      "predicates_source_kind": predicates_kind,
                      "predicates_source_actor": predicates_author}
    if not omit_context_kinds:
        launch_witness["context_passed"] = list(witness_context)
    entries = [
        _entry("e-grant-root", "EVENT", "grant-root", "seat:root",
               {"event": "GRANT", "holder_id": "orchestrator-o", "parent_grant_id": None}),
        _entry("e-grant-run", "EVENT", "grant-run", "orchestrator-o",
               {"event": "GRANT", "holder_id": "worker-a", "parent_grant_id": "grant-root"}),
        _entry("e-grant-witness", "EVENT", "grant-witness", "orchestrator-o",
               {"event": "GRANT", "holder_id": "witness-z", "parent_grant_id": "grant-root"}),
        _entry("e-grant-helper", "EVENT", "grant-helper", "worker-a",
               {"event": "GRANT", "holder_id": "helper-h", "parent_grant_id": "grant-run"}),
        _entry("e-attempt", "EVENT", RUN, "worker-a", attempt),
        _entry("e-standing-built", "EVENT", SUBJECT, "worker-a",
               {"event": "STANDING", "from": "OPEN", "to": "BUILT"}),
        _entry("e-launch-witness", "EVENT", "witness-z", "worker-a", launch_witness),
        _entry("e-launch-helper", "EVENT", "helper-h", "worker-a",
               {"event": "LAUNCH", "launched_actor_id": "helper-h", "launched_by": "worker-a",
                "context_passed": ["OBJECTIVE", "ARTIFACT", "REASONING"],
                "profile": _profile("helper"),
                "predicates_source_kind": "CONTRACT",
                "predicates_source_actor": "contract:observation"}),
    ]
    if with_outputs:
        entries.append(_entry("e-out-1", "EVENT", "out/1", output_actor,
                              {"event": "OUTPUT", "digest": OUTPUT_DIGEST}))
    if with_report:
        entries.append(_entry("e-report", "EVENT", RUN, "worker-a",
                              {"event": "REPORTED", "output_record_addresses": ["out/1"]}))
    return entries


def reader(address: str) -> bytes:
    if address == "out/1":
        return OUTPUT_BYTES
    raise FileNotFoundError(address)


PREDICATES = [
    {"predicate_id": "output-present", "kind": "BYTES_PRESENT", "address": "out/1"},
    {"predicate_id": "output-digest", "kind": "DIGEST_EQUALS", "address": "out/1",
     "expected": "sha256:" + OUTPUT_DIGEST},
    {"predicate_id": "asset-recorded", "kind": "JSON_FIELD_EQUALS", "address": "out/1",
     "field": "standing", "expected": "RECORDED"},
]


class Clock:
    """Strictly increasing ISO moments, so declared-before-observed is decidable."""

    def __init__(self) -> None:
        self.tick = 0

    def __call__(self) -> str:
        self.tick += 1
        return f"2026-09-03T00:{self.tick:02d}:00+00:00"


class ThinSlice(unittest.TestCase):
    def setUp(self) -> None:
        self.service = ObservationService(Clock())
        self.record = RunRecord.from_entries(RUN, journal())

    def _valid(self, record: dict, schema: dict) -> None:
        self.assertEqual([], validate(record, schema, schema, "/"))

    def test_an_independent_witness_observes_the_run(self) -> None:
        request = self.service.request_observation(self.record, "worker-a", "WORKER", RUN)
        self._valid(request, REQUEST_SCHEMA)
        self.service.declare_predicates(RUN, PREDICATES)
        inference = self.service.infer_relation(self.record, "witness-z", "MODEL")
        self._valid(inference, INFERENCE_SCHEMA)
        self.assertEqual("INDEPENDENT", inference["outcome"])
        self.assertEqual("worker-a", inference["executor_id"])
        self.assertEqual(7, len(inference["edges_examined"]))
        observation = self.service.observe_run(self.record, "witness-z", reader)
        self._valid(observation, OBSERVATION_SCHEMA)
        self.assertEqual({"output-present": True, "output-digest": True, "asset-recorded": True},
                         observation["predicate_results"])
        self.assertEqual(["sha256:" + OUTPUT_DIGEST], observation["observed_state_digests"])
        read = self.service.read_observation(observation["observation_id"])
        self.assertEqual(observation, read["observation"])
        self.assertEqual(inference, read["inference"])
        self.assertEqual(["RECORDED", "COMMITTED", "COMMITTED", "COMMITTED", "DERIVED"],
                         [receipt["outcome"] for receipt in self.service.receipts])

    def test_the_executor_may_not_observe_its_own_run(self) -> None:
        inference = self.service.infer_relation(self.record, "worker-a", "WORKER")
        self._valid(inference, INFERENCE_SCHEMA)
        self.assertEqual("DIRECT", inference["outcome"])
        self.assertIn("SAME_ACTOR_VERSION",
                      [edge["edge"] for edge in inference["edges_found"]])
        self.service.declare_predicates(RUN, PREDICATES)
        with self.assertRaises(ObserverNotIndependent):
            self.service.observe_run(self.record, "worker-a", reader)
        self.assertEqual("OBSERVER_NOT_INDEPENDENT", self.service.receipts[-1]["reason_code"])

    def test_the_lease_holder_is_direct(self) -> None:
        record = RunRecord.from_entries(RUN, journal(lease_holder="lease-holder-x"))
        inference = self.service.infer_relation(record, "lease-holder-x", "WORKER")
        self.assertEqual([{"edge": "HOLDS_RUN_LEASE", "evidence_address": "e-attempt"}],
                         inference["edges_found"])

    def test_a_helper_handed_the_builders_reasoning_is_direct(self) -> None:
        """The context axis. `helper-h` was passed REASONING, so it is inside the build."""
        inference = self.service.infer_relation(self.record, "helper-h", "MODEL")
        self.assertEqual("DIRECT", inference["outcome"])
        self.assertEqual([{"edge": "CONSTRUCTION_CONTEXT_INHERITED",
                           "evidence_address": "e-launch-helper"}], inference["edges_found"])

    def test_a_grant_descending_from_the_run_is_no_longer_an_edge(self) -> None:
        """`decisions/0104`: launch lineage is not a relation.

        The witness holds a grant whose parent is the run's own grant - the shape that read
        DIRECT before this ruling - and reads INDEPENDENT, because what it was handed and what
        it is are both clear of the build.
        """
        entries = journal()
        entries.insert(3, _entry("e-grant-z", "EVENT", "grant-z", "worker-a",
                                 {"event": "GRANT", "holder_id": "witness-z",
                                  "parent_grant_id": "grant-run"}))
        record = RunRecord.from_entries(RUN, entries)
        inference = self.service.infer_relation(record, "witness-z", "MODEL")
        self._valid(inference, INFERENCE_SCHEMA)
        self.assertEqual("INDEPENDENT", inference["outcome"])

    def test_a_version_of_the_executor_is_not_independent(self) -> None:
        """The perspective axis. A different id loading the builder's profile is a version."""
        entries = journal(witness_profile=WORKER_PROFILE)
        record = RunRecord.from_entries(RUN, entries)
        inference = self.service.infer_relation(record, "witness-z", "MODEL")
        self.assertEqual("DIRECT", inference["outcome"])
        self.assertEqual("SAME_ACTOR_VERSION", inference["edges_found"][0]["edge"])

    def test_a_witness_graded_against_the_builders_criteria_is_not_independent(self) -> None:
        """The rubber-stamp `decisions/0100` named as its own defeater, now a refusal."""
        record = RunRecord.from_entries(RUN, journal(predicates_author="worker-a",
                                                     predicates_kind="ACTOR"))
        inference = self.service.infer_relation(record, "witness-z", "MODEL")
        self.assertEqual("DIRECT", inference["outcome"])
        self.assertEqual([{"edge": "PREDICATES_SUPPLIED_BY_EXECUTOR",
                           "evidence_address": "e-launch-witness"}], inference["edges_found"])

    def test_the_builder_at_an_earlier_arrow_is_direct_at_a_later_one(self) -> None:
        """Lifecycle scope. A per-run walk finds no edge to a run the builder did not execute."""
        entries = journal()
        entries.insert(6, _entry("e-standing-open", "EVENT", SUBJECT, "builder-b",
                                 {"event": "STANDING", "from": "OPEN", "to": "BUILT"}))
        entries.append(_entry("e-launch-b", "EVENT", "builder-b", "worker-a",
                              {"event": "LAUNCH", "launched_actor_id": "builder-b",
                               "launched_by": "worker-a", "context_passed": ["OBJECTIVE"],
                               "profile": _profile("builder"),
                               "predicates_source_kind": "CONTRACT",
                               "predicates_source_actor": "contract:observation"}))
        record = RunRecord.from_entries(RUN, entries)
        inference = self.service.infer_relation(record, "builder-b", "MODEL")
        self.assertEqual("DIRECT", inference["outcome"])
        self.assertEqual([{"edge": "PRIOR_STANDING_ACTOR",
                           "evidence_address": "e-standing-open"}], inference["edges_found"])

    def test_a_run_that_names_no_subject_cannot_answer_the_lifecycle_edge(self) -> None:
        record = RunRecord.from_entries(RUN, journal(omit_subject=True))
        with self.assertRaises(RelationUndetermined):
            self.service.infer_relation(record, "witness-z", "MODEL")
        self.assertEqual(["PRIOR_STANDING_ACTOR"],
                         self.service.inferences[-1]["unanswerable_edges"])

    def test_an_executor_relaying_an_observation_is_refused(self) -> None:
        """A finding that reaches the record through the builder is the builder's report."""
        self.service.infer_relation(self.record, "witness-z", "MODEL")
        self.service.declare_predicates(RUN, PREDICATES)
        with self.assertRaises(ObserverNotIndependent):
            self.service.observe_run(self.record, "witness-z", reader, submitted_by="worker-a")
        self.assertEqual("OBSERVER_NOT_INDEPENDENT", self.service.receipts[-1]["reason_code"])

    def test_the_producer_of_an_output_is_direct(self) -> None:
        record = RunRecord.from_entries(RUN, journal(output_actor="producer-p"))
        inference = self.service.infer_relation(record, "producer-p", "WORKER")
        self.assertEqual("DIRECT", inference["outcome"])
        self.assertEqual("PRODUCED_THE_OUTPUT", inference["edges_found"][0]["edge"])

    def test_a_run_with_only_a_report_admits_no_observer(self) -> None:
        record = RunRecord.from_entries(RUN, journal(with_outputs=False))
        inference = self.service.infer_relation(record, "witness-z", "MODEL")
        self._valid(inference, INFERENCE_SCHEMA)
        self.assertEqual("DIRECT", inference["outcome"])
        self.assertIn("ONLY_EXECUTOR_REPORT", [edge["edge"] for edge in inference["edges_found"]])

    def test_an_incomplete_record_is_undetermined_not_independent(self) -> None:
        record = RunRecord.from_entries(RUN, journal(omit_context_kinds=True))
        with self.assertRaises(RelationUndetermined):
            self.service.infer_relation(record, "witness-z", "MODEL")
        inference = self.service.inferences[-1]
        self._valid(inference, INFERENCE_SCHEMA)
        self.assertEqual("UNDETERMINED", inference["outcome"])
        self.assertEqual(["CONSTRUCTION_CONTEXT_INHERITED"],
                         inference["unanswerable_edges"])
        self.assertEqual("RELATION_UNDETERMINED", self.service.receipts[-1]["reason_code"])
        self.service.declare_predicates(RUN, PREDICATES)
        with self.assertRaises(RelationUndetermined):
            self.service.observe_run(record, "witness-z", reader)

    def test_a_candidate_the_record_never_saw_launched_is_undetermined(self) -> None:
        """No launch entry answers neither context edge, and no profile answers perspective."""
        with self.assertRaises(RelationUndetermined):
            self.service.infer_relation(self.record, "stranger-s", "HUMAN")

    def test_a_run_in_flight_cannot_be_observed(self) -> None:
        record = RunRecord.from_entries(RUN, journal(with_report=False))
        with self.assertRaises(RunNotTerminal):
            self.service.request_observation(record, "worker-a", "WORKER", RUN)
        with self.assertRaises(RunNotTerminal):
            self.service.infer_relation(record, "witness-z", "MODEL")
        self.assertEqual(["RUN_NOT_TERMINAL", "RUN_NOT_TERMINAL"],
                         [receipt["reason_code"] for receipt in self.service.receipts])

    def test_a_requester_may_not_nominate_itself(self) -> None:
        with self.assertRaises(IncompleteProposal):
            self.service.request_observation(self.record, "worker-a", "WORKER", RUN,
                                             proposed_observer_id="worker-a")

    def test_predicates_declared_after_the_looking_refuse(self) -> None:
        inference = self.service.infer_relation(self.record, "witness-z", "MODEL")
        late = declare_predicates(RUN, PREDICATES, "2026-09-03T02:00:00+00:00")
        with self.assertRaises(PredicatesUndeclared):
            observe_run(self.record, inference, late, "witness-z", reader,
                        "2026-09-03T01:59:00+00:00")

    def test_no_declaration_refuses(self) -> None:
        self.service.infer_relation(self.record, "witness-z", "MODEL")
        with self.assertRaises(PredicatesUndeclared):
            self.service.observe_run(self.record, "witness-z", reader)
        self.assertEqual("PREDICATES_UNDECLARED", self.service.receipts[-1]["reason_code"])

    def test_a_predicate_that_reads_the_report_refuses(self) -> None:
        self.service.infer_relation(self.record, "witness-z", "MODEL")
        self.service.declare_predicates(RUN, [
            {"predicate_id": "reads-report", "kind": "BYTES_PRESENT", "address": "e-report"}])
        with self.assertRaises(PredicatesUndeclared):
            self.service.observe_run(self.record, "witness-z", reader)

    def test_an_empty_or_unknown_predicate_refuses(self) -> None:
        with self.assertRaises(PredicatesUndeclared):
            self.service.declare_predicates(RUN, [])
        with self.assertRaises(PredicatesUndeclared):
            self.service.declare_predicates(RUN, [
                {"predicate_id": "p", "kind": "TRUST_ME", "address": "out/1"}])

    def test_an_unreadable_output_refuses(self) -> None:
        self.service.infer_relation(self.record, "witness-z", "MODEL")
        self.service.declare_predicates(RUN, PREDICATES)
        with self.assertRaises(Unreadable):
            self.service.observe_run(self.record, "witness-z", lambda address: None)
        self.assertEqual("UNREADABLE", self.service.receipts[-1]["reason_code"])

    def test_bytes_disagreeing_with_the_record_refuse(self) -> None:
        self.service.infer_relation(self.record, "witness-z", "MODEL")
        self.service.declare_predicates(RUN, PREDICATES)
        with self.assertRaises(DigestMismatch):
            self.service.observe_run(self.record, "witness-z", lambda address: b"tampered")
        self.assertEqual("DIGEST_MISMATCH", self.service.receipts[-1]["reason_code"])

    def test_a_failed_predicate_is_recorded_not_hidden(self) -> None:
        self.service.infer_relation(self.record, "witness-z", "MODEL")
        self.service.declare_predicates(RUN, [
            {"predicate_id": "wrong-standing", "kind": "JSON_FIELD_EQUALS", "address": "out/1",
             "field": "standing", "expected": "EFFECTIVE"}])
        observation = self.service.observe_run(self.record, "witness-z", reader)
        self.assertEqual({"wrong-standing": False}, observation["predicate_results"])

    def test_reading_an_absent_observation_refuses(self) -> None:
        with self.assertRaises(ObservationMissing):
            self.service.read_observation("urn:soveraeign:observation:none")

    def test_every_attempt_leaves_exactly_one_receipt(self) -> None:
        attempts = 0
        for act in (
            lambda: self.service.infer_relation(self.record, "worker-a", "WORKER"),
            lambda: self.service.infer_relation(self.record, "witness-z", "MODEL"),
            lambda: self.service.declare_predicates(RUN, []),
            lambda: self.service.declare_predicates(RUN, PREDICATES),
            lambda: self.service.observe_run(self.record, "worker-a", reader),
            lambda: self.service.observe_run(self.record, "witness-z", reader),
        ):
            attempts += 1
            try:
                act()
            except Exception:  # noqa: BLE001 - the receipt, not the exception, is the subject
                pass
            self.assertEqual(attempts, len(self.service.receipts))
        # A DIRECT inference commits as an inference; the refusal fires when it is used.
        refused = [receipt["reason_code"] for receipt in self.service.receipts
                   if receipt["outcome"] == "REFUSED"]
        self.assertEqual(["PREDICATES_UNDECLARED", "OBSERVER_NOT_INDEPENDENT"], refused)


class WitnessFindingsOn7be1323(unittest.TestCase):
    """The seven-edge walk's first witness pass. Each case is a defeat it drove itself.

    All but one were reached by building a journal slice and reading the outcome, so each
    test below is that slice. The pass dissented and supported no standing; these are the
    repairs, pinned so the walk cannot quietly return to answering "no" where it cannot see.
    """

    def setUp(self) -> None:
        self.service = ObservationService(Clock())
        self.record = RunRecord.from_entries(RUN, journal())

    def test_a_prior_arrow_actor_without_a_profile_is_not_read_as_different(self) -> None:
        """P1a. A candidate loading the builder's profile under another id read INDEPENDENT,
        because the arrow's actor carried no launch entry and the comparison answered "no"
        rather than "cannot say". That defeats Ruling 3 by rename."""
        entries = journal()
        entries.insert(6, _entry("e-standing-open", "EVENT", SUBJECT, "builder-b",
                                 {"event": "STANDING", "from": "OPEN", "to": "BUILT"}))
        record = RunRecord.from_entries(RUN, entries)
        with self.assertRaises(RelationUndetermined):
            self.service.infer_relation(record, "witness-z", "MODEL")
        self.assertIn("PRIOR_STANDING_ACTOR",
                      self.service.inferences[-1]["unanswerable_edges"])

    def test_a_decoy_subject_no_actor_of_this_run_ever_moved_is_not_walked(self) -> None:
        """P3b. The subject is named by the executor's own ATTEMPTED payload, so it is
        corroborated before it is walked: the decoy carries real arrows by unrelated parties
        and is not this run's lifecycle."""
        entries = journal(subject="urn:soveraeign:work:decoy")
        entries.insert(6, _entry("e-standing-decoy", "EVENT", "urn:soveraeign:work:decoy",
                                 "stranger-s", {"event": "STANDING", "from": "OPEN",
                                                "to": "BUILT"}))
        record = RunRecord.from_entries(RUN, entries)
        with self.assertRaises(RelationUndetermined):
            self.service.infer_relation(record, "witness-z", "MODEL")
        self.assertIn("PRIOR_STANDING_ACTOR",
                      self.service.inferences[-1]["unanswerable_edges"])

    def test_a_predicate_author_of_unstated_kind_is_not_cleared(self) -> None:
        """P4. An alias of the executor and a contract address are the same bytes to this
        service, so the record must say which kind it named."""
        record = RunRecord.from_entries(RUN, journal(predicates_kind="UNSTATED"))
        with self.assertRaises(RelationUndetermined):
            self.service.infer_relation(record, "witness-z", "MODEL")
        self.assertEqual(["PREDICATES_SUPPLIED_BY_EXECUTOR"],
                         self.service.inferences[-1]["unanswerable_edges"])

    def test_an_actor_author_the_record_cannot_place_is_not_cleared(self) -> None:
        record = RunRecord.from_entries(RUN, journal(predicates_author="worker-a-alias",
                                                     predicates_kind="ACTOR"))
        with self.assertRaises(RelationUndetermined):
            self.service.infer_relation(record, "witness-z", "MODEL")
        self.assertEqual(["PREDICATES_SUPPLIED_BY_EXECUTOR"],
                         self.service.inferences[-1]["unanswerable_edges"])

    def test_an_unreadable_lease_is_a_question_not_a_denial(self) -> None:
        """P2, carried from before this change: a non-object lease answered "no holder"."""
        entries = journal()
        entries[4]["payload"]["lease"] = "lease-abc"
        record = RunRecord.from_entries(RUN, entries)
        with self.assertRaises(RelationUndetermined):
            self.service.infer_relation(record, "witness-z", "MODEL")
        self.assertIn("HOLDS_RUN_LEASE", self.service.inferences[-1]["unanswerable_edges"])

    def test_an_incomplete_inference_reading_independent_is_refused_at_the_gate(self) -> None:
        """F2. The schema forbade this shape; the runtime gate read `outcome` and admitted it,
        then wrote an observer_relation asserting a COMPLETE record it never read."""
        forged = dict(self.service.infer_relation(self.record, "witness-z", "MODEL"))
        forged["record_completeness"] = "INCOMPLETE"
        forged["unanswerable_edges"] = ["SAME_ACTOR_VERSION"]
        self.service.declare_predicates(RUN, PREDICATES)
        with self.assertRaises(RelationUndetermined):
            observe_run(self.record, forged, self.service.declarations[-1], "witness-z",
                        reader, "2026-09-08T00:00:00+00:00")

    def test_a_narrowed_examination_is_refused_at_the_gate(self) -> None:
        forged = dict(self.service.infer_relation(self.record, "witness-z", "MODEL"))
        forged["edges_examined"] = ["SAME_ACTOR_VERSION", "HOLDS_RUN_LEASE"]
        self.service.declare_predicates(RUN, PREDICATES)
        with self.assertRaises(RelationUndetermined):
            observe_run(self.record, forged, self.service.declarations[-1], "witness-z",
                        reader, "2026-09-08T00:00:00+00:00")

    def test_an_inference_about_another_run_does_not_admit_this_one(self) -> None:
        forged = dict(self.service.infer_relation(self.record, "witness-z", "MODEL"))
        forged["run_id"] = "urn:soveraeign:run:somewhere-else"
        self.service.declare_predicates(RUN, PREDICATES)
        with self.assertRaises(RelationUndetermined):
            observe_run(self.record, forged, self.service.declarations[-1], "witness-z",
                        reader, "2026-09-08T00:00:00+00:00")

    def test_a_second_session_of_the_executor_may_not_relay_an_observation(self) -> None:
        """F3. The relay refusal compared ids while the walk compared profiles, so the service
        gave two opposite answers about one actor on one record."""
        entries = journal()
        entries.append(_entry("e-launch-a2", "EVENT", "worker-a-2", "worker-a",
                              {"event": "LAUNCH", "launched_actor_id": "worker-a-2",
                               "launched_by": "worker-a", "context_passed": ["OBJECTIVE"],
                               "profile": WORKER_PROFILE,
                               "predicates_source_kind": "CONTRACT",
                               "predicates_source_actor": "contract:observation"}))
        record = RunRecord.from_entries(RUN, entries)
        self.service.infer_relation(record, "witness-z", "MODEL")
        self.service.declare_predicates(RUN, PREDICATES)
        with self.assertRaises(ObserverNotIndependent):
            self.service.observe_run(record, "witness-z", reader, submitted_by="worker-a-2")

    def test_the_observer_relation_quotes_the_inference_rather_than_asserting(self) -> None:
        self.service.infer_relation(self.record, "witness-z", "MODEL")
        self.service.declare_predicates(RUN, PREDICATES)
        observation = self.service.observe_run(self.record, "witness-z", reader)
        inference = self.service.inferences[-1]
        self.assertIn(inference["outcome"], observation["observer_relation"])
        self.assertIn(inference["record_completeness"], observation["observer_relation"])


class WitnessFindingsOnF28e43b(unittest.TestCase):
    """The second pass over the seven-edge walk. It dissented too.

    Its central finding was that `decisions/0104` claimed one module with one reading while
    two edges still compared raw ids, and that the repair for the decoy subject had made
    admission decrease as the record grew. Both are pinned here, the second by a pair: the
    decoy must refuse and the experienced observer must be admitted, together.
    """

    def setUp(self) -> None:
        self.service = ObservationService(Clock())
        self.record = RunRecord.from_entries(RUN, journal())

    def _valid(self, record: dict, schema: dict) -> None:
        self.assertEqual([], validate(record, schema, schema, "/"))

    def _versioned(self, actor: str, profile: dict) -> dict:
        return _entry(f"e-launch-{actor}", "EVENT", actor, "worker-a",
                      {"event": "LAUNCH", "launched_actor_id": actor, "launched_by": "worker-a",
                       "context_passed": ["OBJECTIVE"], "profile": profile,
                       "predicates_source_kind": "CONTRACT",
                       "predicates_source_actor": "contract:observation"})

    def test_a_version_of_the_lease_holder_is_direct(self) -> None:
        """D1. A lease holder need not be the attempter, so SAME_ACTOR_VERSION does not cover
        it, and this edge compared raw ids."""
        held = _profile("lease-holder")
        entries = journal(lease_holder="lease-holder-x")
        entries.append(self._versioned("lease-holder-x", held))
        entries.append(self._versioned("lease-holder-x2", held))
        record = RunRecord.from_entries(RUN, entries)
        inference = self.service.infer_relation(record, "lease-holder-x2", "MODEL")
        self.assertEqual("DIRECT", inference["outcome"])
        self.assertEqual([{"edge": "HOLDS_RUN_LEASE", "evidence_address": "e-attempt"}],
                         inference["edges_found"])

    def test_a_version_of_the_output_producer_is_direct(self) -> None:
        """D1, the other half: a candidate that is a version of the actor which produced the
        very output it proposes to observe."""
        made = _profile("producer")
        entries = journal(output_actor="producer-p")
        entries.append(self._versioned("producer-p", made))
        entries.append(self._versioned("producer-p2", made))
        record = RunRecord.from_entries(RUN, entries)
        inference = self.service.infer_relation(record, "producer-p2", "MODEL")
        self.assertEqual("DIRECT", inference["outcome"])
        self.assertEqual("PRODUCED_THE_OUTPUT", inference["edges_found"][0]["edge"])

    def test_an_observer_with_prior_work_elsewhere_is_refused_not_admitted(self) -> None:
        """D4, and the cost pass 2 named, now taken deliberately.

        Pass 2 objected that charging a candidate for prior work anywhere makes an experienced
        observer unattestable. Pass 3 then defeated the alternative: corroborating the subject
        alone is satisfied by any decoy the executor has itself moved, and admits the subject's
        own builder as its independent observer. The subject is the executor's word either way,
        so the walk refuses rather than guesses. This is a refusal, not a pass, and the cost is
        a KNOWN-GAPS row.
        """
        entries = journal()
        entries.insert(6, _entry("e-standing-elsewhere", "EVENT", "urn:soveraeign:work:other",
                                 "witness-z", {"event": "STANDING", "from": "OPEN",
                                               "to": "BUILT"}))
        record = RunRecord.from_entries(RUN, entries)
        with self.assertRaises(RelationUndetermined):
            self.service.infer_relation(record, "witness-z", "MODEL")
        self.assertEqual(["PRIOR_STANDING_ACTOR"],
                         self.service.inferences[-1]["unanswerable_edges"])

    def test_an_unreadable_context_kind_is_a_question_not_subject_side(self) -> None:
        """D2. The launcher told the truth and the service could not read the word."""
        for kind in ("transcript", "CONCLUSIONS", "FULL_BUILD_CONTEXT"):
            with self.subTest(kind=kind):
                service = ObservationService(Clock())
                record = RunRecord.from_entries(RUN, journal(witness_context=(kind,)))
                with self.assertRaises(RelationUndetermined):
                    service.infer_relation(record, "witness-z", "MODEL")
                self.assertEqual(["CONSTRUCTION_CONTEXT_INHERITED"],
                                 service.inferences[-1]["unanswerable_edges"])

    def test_a_hand_written_inference_does_not_admit_its_own_author(self) -> None:
        """D3. The run's own executor observed its own run on a fabricated dict, because the
        gate graded fields of the declaration and never the record."""
        forged = {
            "inference_id": "urn:soveraeign:observation:relation-inference:forged",
            "run_id": RUN, "candidate_observer_id": "worker-a",
            "candidate_observer_kind": "WORKER", "executor_id": "worker-a",
            "edges_examined": list(EDGES), "edges_found": [],
            "record_completeness": "COMPLETE", "outcome": "INDEPENDENT",
            "evidence_addresses": ["e-attempt"], "evidence_digests": ["sha256:" + "0" * 64],
            "inferred_at": "2026-09-08T00:00:00Z",
        }
        self.service.declare_predicates(RUN, PREDICATES)
        with self.assertRaises(RelationUndetermined):
            observe_run(self.record, forged, self.service.declarations[-1], "worker-a",
                        reader, "2026-09-08T01:00:00+00:00")

    def test_an_inference_citing_entries_this_record_does_not_carry_is_refused(self) -> None:
        genuine = self.service.infer_relation(self.record, "witness-z", "MODEL")
        forged = dict(genuine, evidence_addresses=genuine["evidence_addresses"] + ["e-elsewhere"])
        self.service.declare_predicates(RUN, PREDICATES)
        with self.assertRaises(RelationUndetermined):
            observe_run(self.record, forged, self.service.declarations[-1], "witness-z",
                        reader, "2026-09-08T01:00:00+00:00")

    def test_an_inference_about_another_observer_is_refused(self) -> None:
        """D5. The admission check added for this had no defeating case at all."""
        genuine = self.service.infer_relation(self.record, "witness-z", "MODEL")
        self.service.declare_predicates(RUN, PREDICATES)
        with self.assertRaises(RelationUndetermined):
            observe_run(self.record, genuine, self.service.declarations[-1], "someone-else",
                        reader, "2026-09-08T01:00:00+00:00")

    def test_an_unanswered_edge_alone_refuses_at_the_gate(self) -> None:
        """D5. This clause and the completeness clause were only jointly pinned."""
        forged = dict(self.service.infer_relation(self.record, "witness-z", "MODEL"),
                      unanswerable_edges=["SAME_ACTOR_VERSION"])
        self.service.declare_predicates(RUN, PREDICATES)
        with self.assertRaises(RelationUndetermined):
            observe_run(self.record, forged, self.service.declarations[-1], "witness-z",
                        reader, "2026-09-08T01:00:00+00:00")

    def test_an_incomplete_record_alone_refuses_at_the_gate(self) -> None:
        forged = dict(self.service.infer_relation(self.record, "witness-z", "MODEL"),
                      record_completeness="INCOMPLETE")
        self.service.declare_predicates(RUN, PREDICATES)
        with self.assertRaises(RelationUndetermined):
            observe_run(self.record, forged, self.service.declarations[-1], "witness-z",
                        reader, "2026-09-08T01:00:00+00:00")

    def test_the_observer_relation_names_what_the_inference_read(self) -> None:
        """D5. The earlier assertion could not fail: the gate refuses anything but
        INDEPENDENT over COMPLETE, so quoting and asserting were indistinguishable on every
        reachable input. The addresses come from the record and do differ."""
        self.service.infer_relation(self.record, "witness-z", "MODEL")
        self.service.declare_predicates(RUN, PREDICATES)
        observation = self.service.observe_run(self.record, "witness-z", reader)
        for address in self.service.inferences[-1]["evidence_addresses"]:
            self.assertIn(address, observation["observer_relation"])

    def test_a_version_of_an_executor_is_not_read_as_distinct_by_the_relay_guard(self) -> None:
        """D5. `is_version_of_any`'s UNKNOWN arm is the point of the function and nothing
        held it there."""
        entries = journal()
        entries.append(_entry("e-launch-ghost", "EVENT", "ghost", "worker-a",
                              {"event": "LAUNCH", "launched_actor_id": "ghost",
                               "launched_by": "worker-a", "context_passed": ["OBJECTIVE"],
                               "predicates_source_kind": "CONTRACT",
                               "predicates_source_actor": "contract:observation"}))
        record = RunRecord.from_entries(RUN, entries)
        self.service.infer_relation(record, "witness-z", "MODEL")
        self.service.declare_predicates(RUN, PREDICATES)
        with self.assertRaises(ObserverNotIndependent):
            self.service.observe_run(record, "witness-z", reader, submitted_by="ghost")


class WitnessFindingsOn3c24420(unittest.TestCase):
    """The third pass. It defeated two repairs the previous commit stated as complete.

    Its deepest finding is not repaired here and is not repairable here: every field this walk
    reads to establish either axis is written by the party being graded. See `CHARTER.md`,
    "What this walk detects", and `decisions/0104` judgement item 4.
    """

    def setUp(self) -> None:
        self.service = ObservationService(Clock())
        self.record = RunRecord.from_entries(RUN, journal())

    def test_a_decoy_the_executor_itself_moved_does_not_clear_the_candidate(self) -> None:
        """F1. Corroboration asks only that an actor of the run appear on the named subject,
        and the executor writes the name, so it satisfies that on any subject it has moved.
        The candidate's arrow on the real subject sat in the same record, unread."""
        entries = journal(subject="urn:soveraeign:work:decoy")
        entries.insert(6, _entry("e-standing-decoy", "EVENT", "urn:soveraeign:work:decoy",
                                 "worker-a", {"event": "STANDING", "from": "OPEN",
                                              "to": "BUILT"}))
        entries.insert(7, _entry("e-standing-real", "EVENT", SUBJECT, "witness-z",
                                 {"event": "STANDING", "from": "OPEN", "to": "BUILT"}))
        record = RunRecord.from_entries(RUN, entries)
        with self.assertRaises(RelationUndetermined):
            self.service.infer_relation(record, "witness-z", "MODEL")
        self.assertEqual(["PRIOR_STANDING_ACTOR"],
                         self.service.inferences[-1]["unanswerable_edges"])

    def test_an_uncorroborated_subject_refuses_even_when_the_candidate_is_clear(self) -> None:
        """M3. The corroboration guard had no case that failed when it was deleted: its own
        declared defeating case was killed by the UNKNOWN arm instead, because the decoy's
        mover carried no profile. This one gives that mover a profile, so only corroboration
        can refuse it."""
        stranger = _profile("stranger")
        entries = journal(subject="urn:soveraeign:work:decoy")
        entries.insert(6, _entry("e-standing-decoy", "EVENT", "urn:soveraeign:work:decoy",
                                 "outsider-o", {"event": "STANDING", "from": "OPEN",
                                                "to": "BUILT"}))
        entries.append(_entry("e-launch-outsider", "EVENT", "outsider-o", "worker-a",
                              {"event": "LAUNCH", "launched_actor_id": "outsider-o",
                               "launched_by": "worker-a", "context_passed": ["OBJECTIVE"],
                               "profile": stranger, "predicates_source_kind": "CONTRACT",
                               "predicates_source_actor": "contract:observation"}))
        record = RunRecord.from_entries(RUN, entries)
        with self.assertRaises(RelationUndetermined):
            self.service.infer_relation(record, "witness-z", "MODEL")
        self.assertEqual(["PRIOR_STANDING_ACTOR"],
                         self.service.inferences[-1]["unanswerable_edges"])

    def test_a_correctly_hashed_forged_inference_is_refused(self) -> None:
        """F2. The gate re-hashed three fields the caller supplies, so the id was identical for
        every verdict the walk could reach about one subject: an honest DIRECT and a forged
        INDEPENDENT carried the same one. The earlier fixture used an obviously invalid id,
        which is not the threat model - the recipe is in the repository."""
        honest = self.service.infer_relation(self.record, "worker-a", "WORKER")
        forged = dict(honest, outcome="INDEPENDENT", edges_found=[],
                      record_completeness="COMPLETE")
        forged.pop("unanswerable_edges", None)
        self.assertEqual(honest["inference_id"], forged["inference_id"])
        self.service.declare_predicates(RUN, PREDICATES)
        with self.assertRaises(RelationUndetermined):
            observe_run(self.record, forged, self.service.declarations[-1], "worker-a",
                        reader, "2026-09-08T02:00:00+00:00")

    def test_a_verdict_that_disagrees_with_the_walk_is_refused_field_by_field(self) -> None:
        genuine = self.service.infer_relation(self.record, "witness-z", "MODEL")
        self.service.declare_predicates(RUN, PREDICATES)
        for field, value in (("executor_id", "someone-else"),
                             ("evidence_addresses", ["e-attempt"]),
                             ("edges_examined", list(reversed(EDGES)))):
            with self.subTest(field=field):
                with self.assertRaises(RelationUndetermined):
                    observe_run(self.record, dict(genuine, **{field: value}),
                                self.service.declarations[-1], "witness-z", reader,
                                "2026-09-08T02:00:00+00:00")

    def test_the_observer_relation_never_prints_an_empty_evidence_list(self) -> None:
        """F2's tail: the sentence read `record read at ; outputs read directly`, a hole where
        its evidence goes, on a record the pass had forged its way past."""
        self.service.infer_relation(self.record, "witness-z", "MODEL")
        self.service.declare_predicates(RUN, PREDICATES)
        observation = self.service.observe_run(self.record, "witness-z", reader)
        self.assertNotIn("read at ;", observation["observer_relation"])


class WitnessFindingsOn169182f(unittest.TestCase):
    """Each case is a defeat the first witness pass found; each now refuses as it should."""

    def setUp(self) -> None:
        self.service = ObservationService(Clock())

    def test_the_reporter_is_an_executor_even_when_another_actor_attempted(self) -> None:
        entries = journal()
        entries[-1] = _entry("e-report", "EVENT", RUN, "reporter-r",
                             {"event": "REPORTED", "output_record_addresses": ["out/1"]})
        record = RunRecord.from_entries(RUN, entries)
        inference = self.service.infer_relation(record, "reporter-r", "WORKER")
        self.assertEqual([{"edge": "SAME_ACTOR_VERSION", "evidence_address": "e-report"}],
                         inference["edges_found"])

    def test_a_second_attempt_names_a_second_executor(self) -> None:
        entries = journal()
        entries.insert(-1, _entry("e-attempt-2", "EVENT", RUN, "retrier-q", {
            "event": "ATTEMPTED", "operation_plan_id": "plan-1", "lease": None,
            "grant_id": "grant-run", "subject_id": SUBJECT}))
        record = RunRecord.from_entries(RUN, entries)
        inference = self.service.infer_relation(record, "retrier-q", "WORKER")
        self.assertEqual("DIRECT", inference["outcome"])
        self.assertEqual("e-attempt-2", inference["edges_found"][0]["evidence_address"])

    def test_a_record_without_digests_refuses_unreadable_with_a_receipt(self) -> None:
        entries = journal()
        for entry in entries:
            entry.pop("entry_digest", None)
        record = RunRecord.from_entries(RUN, entries)
        with self.assertRaises(Unreadable):
            self.service.infer_relation(record, "witness-z", "MODEL")
        self.assertEqual(1, len(self.service.receipts))
        self.assertEqual("UNREADABLE", self.service.receipts[-1]["reason_code"])

    def test_an_output_whose_declared_digest_is_malformed_refuses(self) -> None:
        entries = journal()
        entries[-2]["payload"]["digest"] = "not-a-digest"
        record = RunRecord.from_entries(RUN, entries)
        self.service.infer_relation(record, "witness-z", "MODEL")
        self.service.declare_predicates(RUN, PREDICATES)
        with self.assertRaises(Unreadable):
            self.service.observe_run(record, "witness-z", reader)
        self.assertEqual("UNREADABLE", self.service.receipts[-1]["reason_code"])

    def test_the_report_listed_as_its_own_output_is_still_not_a_predicate_address(self) -> None:
        entries = journal()
        entries[-1]["payload"]["output_record_addresses"] = ["out/1", "e-report"]
        entries.append(_entry("e-out-report", "EVENT", "e-report", "worker-a",
                              {"event": "OUTPUT", "digest": OUTPUT_DIGEST}))
        record = RunRecord.from_entries(RUN, entries)
        self.service.infer_relation(record, "witness-z", "MODEL")
        self.service.declare_predicates(RUN, [
            {"predicate_id": "reads-report", "kind": "BYTES_PRESENT", "address": "e-report"}])
        with self.assertRaises(PredicatesUndeclared) as caught:
            self.service.observe_run(record, "witness-z", lambda address: OUTPUT_BYTES)
        self.assertIn("run's own entry", str(caught.exception))

    def test_a_reported_run_without_a_receipt_is_requested_as_unresolved(self) -> None:
        record = RunRecord.from_entries(RUN, journal())
        request = self.service.request_observation(record, "worker-a", "WORKER", RUN)
        self.assertEqual("UNRESOLVED", request["run_outcome"])
        refused = journal(with_report=False, with_outputs=False)
        refused.append(_entry("e-refusal", "RECEIPT", RUN, "kernel",
                              {"outcome": "REFUSED", "event": "begin_run"}))
        record = RunRecord.from_entries(RUN, refused)
        self.assertEqual("REFUSED", record.terminal_outcome())
        self.assertTrue(record.is_terminal())


class WitnessResidualsOn540bc01(unittest.TestCase):
    """The second pass's residuals, each now a refusal or a direct edge through the surface."""

    def setUp(self) -> None:
        self.service = ObservationService(Clock())

    def test_an_anonymous_report_is_unreadable_not_ignored(self) -> None:
        entries = journal()
        entries[-1]["actor"] = ""
        record = RunRecord.from_entries(RUN, entries)
        with self.assertRaises(Unreadable):
            self.service.infer_relation(record, "witness-z", "MODEL")
        self.assertEqual("UNREADABLE", self.service.receipts[-1]["reason_code"])

    def test_a_second_attempts_lessee_is_direct(self) -> None:
        entries = journal()
        entries.insert(-1, _entry("e-attempt-2", "EVENT", RUN, "worker-a", {
            "event": "ATTEMPTED", "operation_plan_id": "plan-1",
            "lease": {"holder_id": "lessee-two", "fence": 2, "expires_at": "2026-09-03T02:00:00Z"},
            "grant_id": "grant-run", "subject_id": SUBJECT}))
        record = RunRecord.from_entries(RUN, entries)
        inference = self.service.infer_relation(record, "lessee-two", "WORKER")
        self.assertEqual([{"edge": "HOLDS_RUN_LEASE", "evidence_address": "e-attempt-2"}],
                         inference["edges_found"])

    def test_an_output_entry_without_a_subject_is_unreadable(self) -> None:
        entries = journal()
        entries[-2]["subject"] = ""
        record = RunRecord.from_entries(RUN, entries + [entries[-2]])
        with self.assertRaises(Unreadable):
            self.service.infer_relation(record, "witness-z", "MODEL")
        self.assertEqual("UNREADABLE", self.service.receipts[-1]["reason_code"])

    def test_a_refused_run_with_nothing_to_read_is_refused_through_the_surface(self) -> None:
        refused = journal(with_report=False, with_outputs=False)
        refused.append(_entry("e-refusal", "RECEIPT", RUN, "kernel",
                              {"outcome": "REFUSED", "event": "begin_run"}))
        record = RunRecord.from_entries(RUN, refused)
        self.assertTrue(record.is_terminal())
        with self.assertRaises(IncompleteProposal) as caught:
            self.service.request_observation(record, "worker-a", "WORKER", RUN)
        self.assertIn("no durable output", str(caught.exception))

    def test_a_settled_run_may_still_be_observed(self) -> None:
        entries = journal()
        entries.append(_entry("e-settle", "RECEIPT", RUN, "kernel",
                              {"outcome": "COMMITTED", "event": "settle_run"}))
        record = RunRecord.from_entries(RUN, entries)
        request = self.service.request_observation(record, "worker-a", "WORKER", RUN)
        self.assertEqual("COMMITTED", request["run_outcome"])
        inference = self.service.infer_relation(record, "witness-z", "MODEL")
        self.assertEqual("INDEPENDENT", inference["outcome"])

    def test_the_run_id_itself_is_not_a_predicate_address(self) -> None:
        record = RunRecord.from_entries(RUN, journal())
        self.service.infer_relation(record, "witness-z", "MODEL")
        self.service.declare_predicates(RUN, [
            {"predicate_id": "reads-run", "kind": "BYTES_PRESENT", "address": RUN}])
        with self.assertRaises(PredicatesUndeclared):
            self.service.observe_run(record, "witness-z", reader)


class RealJournalFeedsTheWalk(unittest.TestCase):
    """The Record Service's own entries are the input, unchanged, so a projection can feed it."""

    def test_entries_from_a_record_service_journal_infer_independence(self) -> None:
        sys.path.insert(0, str(ROOT / "services" / "record" / "src"))
        from tempfile import TemporaryDirectory

        from soveraeign_record_service import RecordService

        with TemporaryDirectory(ignore_cleanup_errors=True) as raw:
            store = RecordService(Path(raw) / "state")
            try:
                for entry in journal():
                    store.append(entry["kind"], entry["subject"], entry["actor"], entry["payload"])
                record = RunRecord.from_entries(RUN, store.entries())
            finally:
                store.close()
        service = ObservationService(Clock())
        inference = service.infer_relation(record, "witness-z", "MODEL")
        self.assertEqual("INDEPENDENT", inference["outcome"])
        self.assertEqual([], validate(inference, INFERENCE_SCHEMA, INFERENCE_SCHEMA, "/"))
        self.assertTrue(all(digest.startswith("sha256:")
                            for digest in inference["evidence_digests"]))


if __name__ == "__main__":
    unittest.main()
