"""Prove ``sov_kernel.py settle`` performs ``settle_run`` and refuses what it must.

A throwaway Record store is built with the Record Service's own command line,
holding one run in the service's own entry shape (ATTEMPTED, OUTPUT, REPORTED,
OBSERVATION, as ``reports/observations/2026-09-05-thin-circuit-1-journal.json``
records them). ``settle`` is then driven as a subprocess, and the journal is
re-read through ``reconstruct-journal`` after every case: a refusal is proven
by the journal's head not moving, never by the refusal's own text.

Passing establishes ``BUILT`` for the settle participant. It witnesses nothing.
"""

from __future__ import annotations

from pathlib import Path
import copy
import inspect
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_kernel  # noqa: E402

RUN = "urn:soveraeign:run:settle-test-1"
WORKER = "urn:soveraeign:principal:instance:sov-worker-settle-test"
WITNESS = "urn:soveraeign:principal:instance:sov-witness-settle-test"
SETTLER = "urn:soveraeign:principal:instance:sov-controller-settle-test"
CONCERN = "concern:phase-1-5/wave-1/settle-test"
OBSERVATION = "urn:soveraeign:observation:0123456789abcdef01234567"
DIGEST = "c3" * 32
OUTPUT = "services/example/tests/test_example.py"

REQUEST = {
    "request_schema": "soveraeign-kernel-transition/v1",
    "transition": "settle_run",
    "actor_id": SETTLER,
    "actor_kind": "MODEL",
    "effect_class": "RECORD_LOCAL",
    "reason": "settle test",
    "declared": {"run_id": RUN, "input_state_digest": DIGEST, "observation_id": OBSERVATION},
    "requested_outcome": "COMMITTED",
    "pre_state_digest": DIGEST,
    "observation": {"observation_id": OBSERVATION, "observer_id": WITNESS,
                    "observer_relation": "INDEPENDENT", "satisfactory": True},
}
CURRENT = {"state_digest": DIGEST, "lease_holder_id": WORKER, "lease_fence": 1,
           "reporter_id": WORKER, "now": 1000}
THIN_CIRCUIT_EXPORT = ROOT / "reports" / "observations" / "2026-09-05-thin-circuit-1-journal.json"
THIN_FRESH_ACTOR = "urn:soveraeign:principal:instance:sov-controller-settle-test"


def thin_circuit_request(entries: list[dict]) -> tuple[dict, dict]:
    """A settle_run request built from the thin circuit's last observation and receipt."""
    observation = [e for e in entries if e["kind"] == "OBSERVATION"][-1]["payload"]["observation"]
    receipt = [e for e in entries if e["kind"] == "RECEIPT"][-1]["payload"]["detail"]
    digest = receipt["input_state_digest"]
    request = copy.deepcopy(REQUEST)
    request["declared"] = {"run_id": observation["run_id"], "input_state_digest": digest,
                           "observation_id": observation["observation_id"]}
    request["pre_state_digest"] = digest
    request["observation"] = {"observation_id": observation["observation_id"],
                              "observer_id": observation["observer_id"],
                              "observer_relation": "INDEPENDENT",
                              "satisfactory": all(observation["predicate_results"].values())}
    return request, {"state_digest": digest,
                     "reporter_id": "urn:soveraeign:principal:instance:sov-worker-thin-1"}


def record(store: Path, *args: str) -> dict:
    """Run one Record command as a subprocess and return what it printed."""
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "services" / "record" / "src")
    proc = subprocess.run(
        [sys.executable, "-m", "soveraeign_record_service.cli", "--root", str(store), *args],
        capture_output=True, text=True, env=env, cwd=str(ROOT), check=False)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return json.loads(proc.stdout)


def seed(store: Path) -> None:
    """One run, in the Record Service's own entry shape."""
    record(store, "append-entry", "--kind", "EVENT", "--subject", RUN, "--actor", WORKER,
           "--payload", json.dumps({"event": "ATTEMPTED", "grant_id": None,
                                    "operation_plan_id": "lease:settle-test",
                                    "lease": {"holder_id": WORKER, "fence": 1,
                                              "expires_at": "2026-09-05T21:05:34Z"},
                                    "pre_tree": "0" * 40}))
    record(store, "append-entry", "--kind", "EVENT", "--subject", OUTPUT, "--actor", WORKER,
           "--payload", json.dumps({"event": "OUTPUT", "run_id": RUN,
                                    "digest": "sha256:" + "ab" * 32}))
    record(store, "append-entry", "--kind", "EVENT", "--subject", RUN, "--actor", WORKER,
           "--payload", json.dumps({"event": "REPORTED", "output_record_addresses": [OUTPUT],
                                    "report": "one file changed"}))
    record(store, "append-entry", "--kind", "OBSERVATION", "--subject", RUN, "--actor", WITNESS,
           "--payload", json.dumps({
               "event": "OBSERVED", "observer_id": WITNESS,
               "inference_id": "urn:soveraeign:observation:relation-inference:settle-test",
               "observation": {"observation_id": OBSERVATION, "run_id": RUN,
                               "observer_id": WITNESS, "observer_relation": "INDEPENDENT",
                               "observed_at": "2026-09-05T18:32:36Z",
                               "observed_state_addresses": [OUTPUT],
                               "observed_state_digests": ["sha256:" + "ab" * 32],
                               "predicate_results": {"digest-0": True, "present-0": True}}}))


class SettleCase(unittest.TestCase):
    """Each case starts from a byte-identical copy of one seeded store."""

    base: tempfile.TemporaryDirectory

    @classmethod
    def setUpClass(cls) -> None:
        cls.base = tempfile.TemporaryDirectory()
        seed(Path(cls.base.name) / "store")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.base.cleanup()

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.store = self.dir / "store"
        shutil.copytree(Path(self.base.name) / "store", self.store)
        self.before = record(self.store, "reconstruct-journal")

    def settle(self, request: dict = REQUEST, current: dict = CURRENT, actor: str = SETTLER,
               store: Path | None = None, *extra: str) -> tuple[int, dict]:
        request_path, current_path = self.dir / "request.json", self.dir / "current.json"
        request_path.write_text(json.dumps(request), "utf-8")
        current_path.write_text(json.dumps(current), "utf-8")
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "sov_kernel.py"), "settle",
             "--request", str(request_path), "--current", str(current_path),
             "--record-root", str(store or self.store), "--actor", actor, *extra],
            capture_output=True, text=True, cwd=str(ROOT), check=False)
        self.assertTrue(proc.stdout.strip(), proc.stderr)
        return proc.returncode, json.loads(proc.stdout)

    def assert_unchanged(self) -> None:
        after = record(self.store, "reconstruct-journal")
        self.assertEqual(after["head"], self.before["head"])
        self.assertEqual(after["count"], self.before["count"])

    def assert_refused(self, code: int, out: dict, reason: str) -> None:
        self.assertEqual(code, 2, out)
        self.assertEqual(out["reason_code"], reason, out)
        self.assertEqual(out["appended"], [])
        self.assert_unchanged()

    # ---- positive ----------------------------------------------------------

    def test_permitted_appends_the_receipt_last(self) -> None:
        code, out = self.settle()
        self.assertEqual(code, 0, out)
        self.assertTrue(out["verdict"].startswith("PERMITTED: settle_run may commit"))
        after = record(self.store, "reconstruct-journal")
        self.assertEqual(after["count"], self.before["count"] + 1)
        last = after["entries"][-1]
        self.assertEqual(last["entry_id"], out["receipt"]["entry_id"])
        self.assertEqual(last["seq"], out["receipt"]["seq"])
        self.assertEqual((last["kind"], last["subject"], last["actor"]), ("RECEIPT", RUN, SETTLER))
        self.assertEqual(last["payload"]["event"], "settle_run")
        self.assertEqual(last["payload"]["outcome"], "COMMITTED")
        self.assertEqual(last["payload"]["detail"], {
            "kernel_verdict": out["verdict"], "observation_id": OBSERVATION,
            "input_state_digest": DIGEST, "settled_by": SETTLER})
        self.assertIsNone(out["reconcile"])
        self.assertIn("no RECONCILED entry appended", out["reconcile_note"])

    def test_concern_appends_reconciled_after_the_receipt(self) -> None:
        code, out = self.settle(REQUEST, CURRENT, SETTLER, None, "--concern", CONCERN,
                                "--relation", "advances", "--basis", "the run repaired R13")
        self.assertEqual(code, 0, out)
        after = record(self.store, "reconstruct-journal")
        self.assertEqual(after["count"], self.before["count"] + 2)
        receipt, reconcile = after["entries"][-2], after["entries"][-1]
        self.assertEqual(receipt["entry_id"], out["receipt"]["entry_id"])
        self.assertEqual(reconcile["entry_id"], out["reconcile"]["entry_id"])
        self.assertEqual((reconcile["kind"], reconcile["subject"], reconcile["actor"]),
                         ("EVENT", CONCERN, SETTLER))
        self.assertEqual(reconcile["payload"], {
            "event": "RECONCILED", "run_id": RUN, "receipt_entry_id": receipt["entry_id"],
            "relation": "advances", "basis": "the run repaired R13"})

    def test_concern_without_relation_and_basis_is_a_usage_error(self) -> None:
        code, out = self.settle(REQUEST, CURRENT, SETTLER, None, "--concern", CONCERN)
        self.assertEqual(code, 1, out)
        self.assert_unchanged()

    # ---- defeating ---------------------------------------------------------

    def test_settler_equal_to_reporter_is_refused(self) -> None:
        code, out = self.settle(actor=WORKER)
        self.assert_refused(code, out, "SELF_SETTLEMENT_REFUSED")

    def test_reporter_measured_from_the_journal_not_only_from_current(self) -> None:
        current = {key: value for key, value in CURRENT.items() if key != "reporter_id"}
        code, out = self.settle(current=current, actor=WORKER)
        self.assert_refused(code, out, "SELF_SETTLEMENT_REFUSED")

    def test_settler_equal_to_observer_is_refused(self) -> None:
        code, out = self.settle(actor=WITNESS)
        self.assert_refused(code, out, "SELF_SETTLEMENT_REFUSED")

    def test_observation_missing_from_the_request(self) -> None:
        request = copy.deepcopy(REQUEST)
        del request["observation"]
        code, out = self.settle(request)
        self.assert_refused(code, out, "OBSERVATION_MISSING")

    def test_observation_absent_from_the_store(self) -> None:
        request = copy.deepcopy(REQUEST)
        request["declared"]["observation_id"] = OBSERVATION + "-never-recorded"
        request["observation"]["observation_id"] = OBSERVATION + "-never-recorded"
        code, out = self.settle(request)
        self.assert_refused(code, out, "OBSERVATION_MISSING")
        self.assertIn(str(self.store), out["detail"])

    def test_stale_pre_state(self) -> None:
        code, out = self.settle(current={**CURRENT, "state_digest": "d4" * 32})
        self.assert_refused(code, out, "STALE_STATE")

    def test_second_settlement_of_the_same_run_is_stale(self) -> None:
        """An un-countered receipt is the run's state: the kernel's word STALE_STATE, pinned."""
        code, first = self.settle()
        self.assertEqual(code, 0, first)
        self.before = record(self.store, "reconstruct-journal")
        code, out = self.settle()
        self.assert_refused(code, out, "STALE_STATE")
        self.assertEqual(out["detail"], f"already settled: {first['receipt']['entry_id']}")
        self.assertEqual(out["measured"]["standing"], [first["receipt"]["entry_id"]])

    def test_digest_equal_replay_is_still_refused(self) -> None:
        """Witness dissent R1: declaring the receipt's own digest as pre-state settled twice."""
        code, first = self.settle()
        self.assertEqual(code, 0, first)
        self.before = record(self.store, "reconstruct-journal")
        receipt = self.before["entries"][-1]
        self.assertEqual(receipt["entry_id"], first["receipt"]["entry_id"])
        request = copy.deepcopy(REQUEST)
        request["pre_state_digest"] = receipt["entry_digest"]
        code, out = self.settle(request, {**CURRENT, "state_digest": receipt["entry_digest"]})
        self.assert_refused(code, out, "STALE_STATE")
        self.assertEqual(out["detail"], f"already settled: {receipt['entry_id']}")

    def test_countered_receipt_reopens_the_run(self) -> None:
        """The thin-circuit export at 14 entries: its receipt is countered, so a fresh actor
        that neither reported nor observed may settle, at seq 15, and reconcile at seq 16."""
        store = self.dir / "countered"
        record(store, "restore-journal", "--export", str(THIN_CIRCUIT_EXPORT))
        before = record(store, "reconstruct-journal")
        self.assertEqual(before["count"], 14)
        self.assertEqual(before["entries"][-1]["kind"], "COUNTER")
        request, current = thin_circuit_request(before["entries"])
        code, out = self.settle(request, current, THIN_FRESH_ACTOR, store,
                                "--concern", "concern:phase-1-5/thin-circuit-1",
                                "--relation", "advances", "--basis", "R13 repaired")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["measured"]["countered"], ["entry_6a14553aa71e4f8cb84fc6512bbfe672"])
        self.assertEqual(out["measured"]["standing"], [])
        self.assertEqual(out["receipt"]["seq"], 15)
        self.assertEqual(out["reconcile"]["seq"], 16)
        after = record(store, "reconstruct-journal")
        self.assertEqual([entry["kind"] for entry in after["entries"][-2:]], ["RECEIPT", "EVENT"])
        self.assertEqual(after["entries"][-1]["payload"]["event"], "RECONCILED")

    def test_record_root_unreachable(self) -> None:
        blocker = self.dir / "blocker"
        blocker.write_text("not a directory", "utf-8")
        code, out = self.settle(store=blocker / "store")
        self.assertEqual(code, 2, out)
        self.assertEqual(out["reason_code"], "SERVICE_UNREACHABLE")
        self.assertIn("NotADirectoryError", out["detail"])
        self.assert_unchanged()

    # ---- one judgement, not a copy -------------------------------------------

    def test_check_and_settle_share_one_judgement(self) -> None:
        source = inspect.getsource(sov_kernel.command_check)
        self.assertIn("settle.judge(", source)
        self.assertNotIn("kernel.evaluate(", source)


if __name__ == "__main__":
    unittest.main()
