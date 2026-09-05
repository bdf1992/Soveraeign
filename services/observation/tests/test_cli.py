"""Drive the Observation Service through its command line, one invocation per operation.

The point of the CLI is that state outlives a process: predicates declared in one invocation
must still hold for an observation made in a later one, and every attempt, admitted or refused,
must leave a receipt file a later participant can read. The positive path, the three named
defeating cases (executor as observer, observation before declaration, tampered byte), and the
second-observation case run the module as a real subprocess over a journal fixture written to
disk, exactly as a later participant would. The remaining cases call `cli.main()` in-process,
which still rebuilds the service from the store on entry, to keep the suite inside its check
budget. They establish `BUILT` and witness nothing.
"""

from __future__ import annotations

from pathlib import Path
import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest

SERVICE = Path(__file__).resolve().parents[1]
ROOT = SERVICE.parents[1]
sys.path.insert(0, str(SERVICE / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from sovkernel.jsonschema import validate  # noqa: E402
from test_thin_slice import (  # noqa: E402
    Clock, OUTPUT_BYTES, OUTPUT_DIGEST, PREDICATES, RUN, journal, reader,
)

from soveraeign_observation_service import (  # noqa: E402
    ObservationRecorded, ObservationService, RunRecord, cli,
)
from soveraeign_observation_service.store import FileStore, file_name  # noqa: E402

OBSERVATION_SCHEMA = json.loads(
    (ROOT / "contracts" / "observation.schema.json").read_text(encoding="utf-8"))
MODULE = "soveraeign_observation_service.cli"


class CommandLine(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.journal = self.root / "journal.json"
        self.store = self.root / "store"
        self.outputs = self.root / "outputs"
        self.write_journal(journal())
        self.write_output(OUTPUT_BYTES)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write_journal(self, entries: list[dict]) -> None:
        document = {"export_schema": "test", "entries": entries, "entry_count": len(entries)}
        self.journal.write_text(json.dumps(document), encoding="utf-8")

    def write_output(self, payload: bytes) -> None:
        (self.outputs / "out").mkdir(parents=True, exist_ok=True)
        (self.outputs / "out" / "1").write_bytes(payload)

    def run_cli(self, *arguments: str, process: bool = False) -> tuple[int, dict]:
        """One invocation per call; `process=True` makes it a real subprocess.

        Either way the service is rebuilt from the store on entry, so nothing survives a
        call except what the store wrote. The subprocess form is the proof that holds
        across processes; the in-process form keeps the suite inside its check budget.
        """
        argv = ["--store", str(self.store), *arguments]
        if process:
            completed = subprocess.run(
                [sys.executable, "-m", MODULE, *argv], cwd=SERVICE / "src",
                capture_output=True, text=True, timeout=60, check=False)
            self.assertEqual("", completed.stderr)
            return completed.returncode, json.loads(completed.stdout)
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            code = cli.main(argv)
        return code, json.loads(captured.getvalue())

    def run_on(self, command: str, *arguments: str, process: bool = False) -> tuple[int, dict]:
        return self.run_cli(command, "--journal", str(self.journal), "--run", RUN, *arguments,
                            process=process)

    def declare(self, process: bool = False) -> tuple[int, dict]:
        return self.run_on("declare-predicates", "--predicates", json.dumps(PREDICATES),
                           process=process)

    def receipts_on_disk(self) -> list[dict]:
        return [json.loads(path.read_text(encoding="utf-8"))
                for path in sorted((self.store / "receipts").glob("*.json"))]

    # ---- positive path -----------------------------------------------------

    def test_declare_infer_and_observe_across_processes(self) -> None:
        code, declared = self.declare(process=True)
        self.assertEqual(0, code)
        self.assertEqual("COMMITTED", declared["receipt"]["outcome"])

        code, inferred = self.run_on("infer-relation", "--observer", "witness-z", process=True)
        self.assertEqual(0, code)
        self.assertEqual("INDEPENDENT", inferred["inference"]["outcome"])

        code, observed = self.run_on("observe-run", "--observer", "witness-z",
                                     "--reader-root", str(self.outputs), process=True)
        self.assertEqual(0, code, observed)
        observation = observed["observation"]
        self.assertEqual([], validate(observation, OBSERVATION_SCHEMA, OBSERVATION_SCHEMA, "/"))
        self.assertEqual({"output-present": True, "output-digest": True, "asset-recorded": True},
                         observation["predicate_results"])
        self.assertEqual(["sha256:" + OUTPUT_DIGEST], observation["observed_state_digests"])
        entry = observed["journal_entry"]
        self.assertEqual("OBSERVATION", entry["kind"])
        self.assertEqual(RUN, entry["subject"])
        self.assertEqual("witness-z", entry["actor"])
        self.assertEqual("OBSERVED", entry["payload"]["event"])
        self.assertEqual(observation, entry["payload"]["observation"])
        self.assertEqual(inferred["inference"]["inference_id"], entry["payload"]["inference_id"])
        self.assertEqual(declared["declaration"]["declaration_id"],
                         entry["payload"]["declaration_id"])

        code, read = self.run_cli("read-observation", "--observation",
                                  observation["observation_id"], process=True)
        self.assertEqual(0, code)
        self.assertEqual(observation, read["observation"])
        self.assertEqual(declared["declaration"], read["declaration"])
        self.assertEqual(inferred["inference"], read["inference"])
        self.assertEqual(["COMMITTED", "COMMITTED", "COMMITTED"],
                         [receipt["outcome"] for receipt in read["receipts"]])
        self.assertEqual(4, len(self.receipts_on_disk()))
        self.assertTrue((self.store / "observations"
                         / file_name(observation["observation_id"])).is_file())

    def test_predicates_may_be_declared_from_the_record(self) -> None:
        code, declared = self.run_on("declare-predicates", "--from-record")
        self.assertEqual(0, code)
        self.assertEqual([{"predicate_id": "digest-0", "kind": "DIGEST_EQUALS",
                           "address": "out/1", "expected": "sha256:" + OUTPUT_DIGEST}],
                         declared["declaration"]["predicates"])

    def test_predicates_may_be_read_from_a_file(self) -> None:
        path = self.root / "predicates.json"
        path.write_text(json.dumps(PREDICATES), encoding="utf-8")
        code, declared = self.run_on("declare-predicates", "--predicates-file", str(path))
        self.assertEqual(0, code)
        self.assertEqual(PREDICATES, declared["declaration"]["predicates"])
        code, refused = self.run_on("declare-predicates", "--predicates-file",
                                    str(self.root / "absent.json"))
        self.assertEqual(2, code)
        self.assertEqual("MISSING_PRECONDITION", refused["reason_code"])
        self.assertEqual("MISSING_PRECONDITION", refused["receipt"]["reason_code"])

    def test_request_observation_records_a_request(self) -> None:
        code, requested = self.run_on("request-observation", "--requester", "worker-a",
                                      "--requester-kind", "WORKER")
        self.assertEqual(0, code)
        self.assertEqual("RECORDED", requested["request"]["standing"])
        self.assertEqual(["out/1"], requested["request"]["durable_output_addresses"])

    def test_operations_answers_from_the_manifest(self) -> None:
        code, discovered = self.run_cli("operations")
        self.assertEqual(0, code)
        self.assertEqual("observation", discovered["service_id"])
        self.assertFalse(discovered["authoritative"])
        declared = {op["operation"] for op in discovered["operations"] if op["standing"] == "BUILT"}
        self.assertEqual(declared, set(discovered["reachable_here"]))

    # ---- defeating cases ---------------------------------------------------

    def test_the_executor_is_refused_as_observer(self) -> None:
        self.declare()
        code, inferred = self.run_on("infer-relation", "--observer", "worker-a")
        self.assertEqual(0, code)
        self.assertEqual("DIRECT", inferred["inference"]["outcome"])
        code, refused = self.run_on("observe-run", "--observer", "worker-a",
                                    "--reader-root", str(self.outputs), process=True)
        self.assertEqual(2, code)
        self.assertEqual("REFUSED", refused["outcome"])
        self.assertEqual("OBSERVER_NOT_INDEPENDENT", refused["reason_code"])
        self.assertEqual("OBSERVER_NOT_INDEPENDENT", refused["receipt"]["reason_code"])
        self.assertNotIn("kernel_reason_code", refused)
        self.assertEqual(["COMMITTED", "COMMITTED", "REFUSED"],
                         sorted(receipt["outcome"] for receipt in self.receipts_on_disk()))

    def test_observing_before_any_declaration_refuses(self) -> None:
        self.run_on("infer-relation", "--observer", "witness-z")
        code, refused = self.run_on("observe-run", "--observer", "witness-z",
                                    "--reader-root", str(self.outputs), process=True)
        self.assertEqual(2, code)
        self.assertEqual("PREDICATES_UNDECLARED", refused["reason_code"])
        self.assertEqual("MISSING_PRECONDITION", refused["kernel_reason_code"])
        self.assertEqual(["PREDICATES_UNDECLARED"],
                         [receipt["reason_code"] for receipt in self.receipts_on_disk()
                          if receipt["operation"] == "observe-run"])

    def test_a_tampered_output_byte_refuses(self) -> None:
        self.declare()
        self.run_on("infer-relation", "--observer", "witness-z")
        self.write_output(OUTPUT_BYTES + b"x")
        code, refused = self.run_on("observe-run", "--observer", "witness-z",
                                    "--reader-root", str(self.outputs), process=True)
        self.assertEqual(2, code)
        self.assertEqual("DIGEST_MISMATCH", refused["reason_code"])
        self.assertIn("out/1", refused["message"])
        self.assertFalse((self.store / "observations").exists())

    def test_a_second_observation_of_the_same_identity_is_refused_and_the_first_readable(
            self) -> None:
        self.declare()
        self.run_on("infer-relation", "--observer", "witness-z")
        code, first = self.run_on("observe-run", "--observer", "witness-z",
                                  "--reader-root", str(self.outputs), process=True)
        self.assertEqual(0, code)
        identity = first["observation"]["observation_id"]
        code, refused = self.run_on("observe-run", "--observer", "witness-z",
                                    "--reader-root", str(self.outputs), process=True)
        # The old behaviour committed at exit 0 and persisted nothing; this is its defeat.
        self.assertEqual(2, code, refused)
        self.assertEqual("OBSERVATION_RECORDED", refused["reason_code"])
        self.assertEqual("STALE_STATE", refused["kernel_reason_code"])
        self.assertIn(identity, refused["message"])
        self.assertEqual("OBSERVATION_RECORDED", refused["receipt"]["reason_code"])
        self.assertEqual([file_name(identity)],
                         [path.name for path in (self.store / "observations").glob("*.json")])
        code, read = self.run_cli("read-observation", "--observation", identity)
        self.assertEqual(0, code)
        self.assertEqual(first["observation"], read["observation"])
        self.assertEqual(["COMMITTED", "COMMITTED", "COMMITTED", "REFUSED"],
                         [receipt["outcome"] for receipt in read["receipts"]])

    def test_an_output_missing_from_the_reader_root_is_unreadable(self) -> None:
        self.declare()
        self.run_on("infer-relation", "--observer", "witness-z")
        code, refused = self.run_on("observe-run", "--observer", "witness-z",
                                    "--reader-root", str(self.root / "nowhere"))
        self.assertEqual(2, code)
        self.assertEqual("UNREADABLE", refused["reason_code"])

    def test_a_run_in_flight_refuses_with_the_kernel_word(self) -> None:
        self.write_journal(journal(with_report=False))
        code, refused = self.run_on("request-observation", "--requester", "worker-a")
        self.assertEqual(2, code)
        self.assertEqual("RUN_NOT_TERMINAL", refused["reason_code"])
        self.assertEqual("STALE_STATE", refused["kernel_reason_code"])

    def test_an_absent_observation_is_an_unknown_record(self) -> None:
        code, refused = self.run_cli("read-observation", "--observation", "urn:nothing")
        self.assertEqual(3, code)
        self.assertEqual("OBSERVATION_MISSING", refused["reason_code"])
        self.assertEqual(1, len(self.receipts_on_disk()))

    def test_a_journal_without_entries_is_unreadable(self) -> None:
        self.journal.write_text('{"head": "x"}', encoding="utf-8")
        code, refused = self.run_on("infer-relation", "--observer", "witness-z")
        self.assertEqual(2, code)
        self.assertEqual("UNREADABLE", refused["reason_code"])
        self.assertEqual("UNREADABLE", self.receipts_on_disk()[0]["reason_code"])

    def test_every_attempt_leaves_exactly_one_receipt_file(self) -> None:
        self.declare()
        self.run_on("infer-relation", "--observer", "worker-a")
        self.run_on("observe-run", "--observer", "worker-a", "--reader-root", str(self.outputs))
        self.run_on("infer-relation", "--observer", "witness-z")
        self.run_on("observe-run", "--observer", "witness-z", "--reader-root", str(self.outputs))
        self.run_cli("read-observation", "--observation", "urn:nothing")
        self.run_cli("operations")
        receipts = self.receipts_on_disk()
        self.assertEqual(6, len(receipts))
        self.assertEqual(6, len({receipt["receipt_id"] for receipt in receipts}))
        self.assertEqual({"declare-predicates": 1, "infer-relation": 2, "observe-run": 2,
                          "read-observation": 1},
                         {op: sum(1 for r in receipts if r["operation"] == op)
                          for op in {r["operation"] for r in receipts}})


class Identity(unittest.TestCase):
    def test_the_service_itself_refuses_a_second_observation_of_one_identity(self) -> None:
        service = ObservationService(Clock())
        record = RunRecord.from_entries(RUN, journal())
        service.declare_predicates(RUN, PREDICATES)
        service.infer_relation(record, "witness-z", "MODEL")
        first = service.observe_run(record, "witness-z", reader)
        with self.assertRaises(ObservationRecorded) as refused:
            service.observe_run(record, "witness-z", reader)
        self.assertIn(first["observation_id"], refused.exception.detail)
        self.assertEqual([first], service.observations)
        self.assertEqual(["COMMITTED", "COMMITTED", "COMMITTED", "REFUSED"],
                         [receipt["outcome"] for receipt in service.receipts])


class Store(unittest.TestCase):
    def test_replay_order_follows_the_recorded_moment_not_the_file_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = FileStore(Path(tmp))
            directory = Path(tmp) / "declarations"
            directory.mkdir()
            later = {"declaration_id": "urn:a", "run_id": RUN, "predicates": PREDICATES,
                     "declared_at": "2026-09-05T00:02:00+00:00"}
            earlier = {"declaration_id": "urn:b", "run_id": RUN, "predicates": PREDICATES,
                       "declared_at": "2026-09-05T00:01:00+00:00"}
            for record in (later, earlier):
                (directory / file_name(record["declaration_id"])).write_text(
                    json.dumps(record), encoding="utf-8")
            service = store.load(lambda: "2026-09-05T00:03:00+00:00")
            self.assertEqual(["urn:b", "urn:a"],
                             [entry["declaration_id"] for entry in service.declarations])
            self.assertEqual([], store.save(service))

    def test_file_names_carry_no_path_separators_or_colons(self) -> None:
        self.assertEqual("urn_soveraeign_observation_abc.json",
                         file_name("urn:soveraeign:observation:abc"))
        self.assertNotIn("/", file_name("out/1"))


if __name__ == "__main__":
    unittest.main()
