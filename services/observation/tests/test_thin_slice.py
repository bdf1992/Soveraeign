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
OUTPUT_BYTES = b'{"asset_id": "asset-1", "standing": "RECORDED"}'
OUTPUT_DIGEST = hashlib.sha256(OUTPUT_BYTES).hexdigest()


def _entry(entry_id: str, kind: str, subject: str, actor: str, payload: dict) -> dict:
    digest = hashlib.sha256(f"{entry_id}|{subject}|{actor}".encode("utf-8")).hexdigest()
    return {"entry_id": entry_id, "kind": kind, "subject": subject, "actor": actor,
            "payload": payload, "entry_digest": digest}


def journal(*, lease_holder="worker-a", grant_id="grant-run", output_actor="worker-a",
            with_outputs=True, with_report=True, omit_grant_key=False) -> list[dict]:
    lease = {"holder_id": lease_holder, "fence": 1, "expires_at": "2026-09-03T01:00:00Z"}
    attempt = {"event": "ATTEMPTED", "operation_plan_id": "plan-1", "lease": lease}
    if not omit_grant_key:
        attempt["grant_id"] = grant_id
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
        self.assertEqual(5, len(inference["edges_examined"]))
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
        self.assertIn("SAME_ACTOR", [edge["edge"] for edge in inference["edges_found"]])
        self.service.declare_predicates(RUN, PREDICATES)
        with self.assertRaises(ObserverNotIndependent):
            self.service.observe_run(self.record, "worker-a", reader)
        self.assertEqual("OBSERVER_NOT_INDEPENDENT", self.service.receipts[-1]["reason_code"])

    def test_the_lease_holder_is_direct(self) -> None:
        record = RunRecord.from_entries(RUN, journal(lease_holder="lease-holder-x"))
        inference = self.service.infer_relation(record, "lease-holder-x", "WORKER")
        self.assertEqual([{"edge": "HOLDS_RUN_LEASE", "evidence_address": "e-attempt"}],
                         inference["edges_found"])

    def test_a_grant_descending_from_the_run_is_direct(self) -> None:
        inference = self.service.infer_relation(self.record, "helper-h", "MODEL")
        self.assertEqual("DIRECT", inference["outcome"])
        self.assertEqual("GRANT_DESCENDS_FROM_RUN", inference["edges_found"][0]["edge"])
        self.assertIn("e-grant-helper", inference["evidence_addresses"])

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
        record = RunRecord.from_entries(RUN, journal(omit_grant_key=True))
        with self.assertRaises(RelationUndetermined):
            self.service.infer_relation(record, "witness-z", "MODEL")
        inference = self.service.inferences[-1]
        self._valid(inference, INFERENCE_SCHEMA)
        self.assertEqual("UNDETERMINED", inference["outcome"])
        self.assertEqual(["GRANT_DESCENDS_FROM_RUN"], inference["unanswerable_edges"])
        self.assertEqual("RELATION_UNDETERMINED", self.service.receipts[-1]["reason_code"])
        self.service.declare_predicates(RUN, PREDICATES)
        with self.assertRaises(RelationUndetermined):
            self.service.observe_run(record, "witness-z", reader)

    def test_a_candidate_whose_grant_is_not_in_the_record_is_undetermined(self) -> None:
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
        self.assertEqual([{"edge": "SAME_ACTOR", "evidence_address": "e-report"}],
                         inference["edges_found"])

    def test_a_second_attempt_names_a_second_executor(self) -> None:
        entries = journal()
        entries.insert(-1, _entry("e-attempt-2", "EVENT", RUN, "retrier-q", {
            "event": "ATTEMPTED", "operation_plan_id": "plan-1", "lease": None,
            "grant_id": "grant-run"}))
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
