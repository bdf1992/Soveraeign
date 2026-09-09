"""Exercise reviewed acceptance and retries through isolated real CLI processes."""

from __future__ import annotations

import copy
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER = "urn:test:owner"
SEAT = "seat:test-owner"


class AcceptanceReplayCLI(unittest.TestCase):
    """No command here reads or records an action in the live owner queue."""

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="sov-accept-replay-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        scripts = self.root / "scripts"
        scripts.mkdir()
        shutil.copytree(ROOT / "scripts/sovaccept", scripts / "sovaccept",
                        ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copy2(ROOT / "scripts/sov_accept.py", scripts)
        (scripts / "sovkernel").mkdir()
        for name in ("__init__.py", "jsonschema.py"):
            shutil.copy2(ROOT / "scripts/sovkernel" / name, scripts / "sovkernel")
        (self.root / "contracts").mkdir()
        for name in ("acceptance-packet.schema.json", "acceptance-policy.json"):
            shutil.copy2(ROOT / "contracts" / name, self.root / "contracts")
        self.write_json("contracts/seat-registry.json", {"seats": [
            {"seat_id": SEAT, "owner_seat": None, "settles": ["JUDGEMENT"],
             "occupant": {"actor_id": OWNER, "actor_kind": "HUMAN"}},
            {"seat_id": "seat:test-builder", "owner_seat": SEAT,
             "settles": [], "occupant": {"actor_id": "urn:test:builder"}},
        ]})
        self.packet = json.loads((ROOT / "acceptance/accepted/A3.json").read_text("utf-8"))
        self.packet.update(packet_id="A1", presented_by_seat="seat:test-builder",
                           accepted_by_seat=SEAT,
                           built_by={"actor_id": "urn:test:builder", "actor_kind": "MODEL"})
        self.packet["subject"]["artifact"] = "result.txt"
        self.packet["visible_result"]["demo"] = [sys.executable, "-c", "print('example')"]
        self.write_json("acceptance/A1.json", self.packet)
        (self.root / "result.txt").write_bytes(b"The reviewed result.\n")
        self.write_status(["A1"])
        self.ledger = self.root / ".local/acceptance/ledger.ndjson"

    def write_json(self, relative: str, value: object) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2), encoding="utf-8")

    def write_status(self, ids: list[str]) -> None:
        lines = ["open_decisions: []", "owner_holds: []", "rulings: []",
                 "owner_acceptance_queue:"]
        for packet_id in ids:
            lines.extend([f"  - id: {packet_id}",
                          f"    packet: acceptance/{packet_id}.json",
                          "    presented: a finished example", f"    waits_on: {SEAT}"])
        (self.root / "STATUS.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def command(self, *args: str) -> list[str]:
        return [sys.executable, str(self.root / "scripts/sov_accept.py"), *args]

    def run_cli(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(self.command(*args), cwd=self.root, capture_output=True,
                              text=True, timeout=20, check=False)

    def review(self) -> str:
        result = self.run_cli("present", "A1")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        token = re.search(r"--review\s+(sha256:[0-9a-f]{64})", result.stdout)
        self.assertIsNotNone(token, result.stdout)
        return token.group(1)

    def action_args(self, token: str | None, action: str = "accept",
                    *extra: str) -> list[str]:
        args = [action, "A1", "--seat", SEAT, "--actor", OWNER]
        if token is not None:
            args.extend(["--review", token])
        return [*args, *extra]

    def rows(self) -> list[dict]:
        if not self.ledger.exists():
            return []
        return [json.loads(line) for line in self.ledger.read_text("utf-8").splitlines()
                if line.strip()]

    def assert_refused(self, result: subprocess.CompletedProcess, code: str = "REFUSED") -> None:
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(code, result.stdout + result.stderr)

    def test_every_action_requires_the_review_token(self) -> None:
        for action in ("accept", "reject", "strike", "redirect"):
            with self.subTest(action=action):
                self.assert_refused(self.run_cli(*self.action_args(None, action)), "REVIEW_REQUIRED")
        self.assertEqual(self.rows(), [])

    def test_changed_or_missing_subject_refuses_old_review(self) -> None:
        token = self.review()
        subject = self.root / "result.txt"
        subject.write_bytes(b"A different result.\n")
        self.assert_refused(self.run_cli(*self.action_args(token)))
        subject.unlink()
        self.assert_refused(self.run_cli(*self.action_args(token)))
        self.assertEqual(self.rows(), [])

    def test_changed_packet_promise_refuses_old_review(self) -> None:
        token = self.review()
        self.packet["on_accept"] = "Accepting now authorises a different consequence."
        self.write_json("acceptance/A1.json", self.packet)
        self.assert_refused(self.run_cli(*self.action_args(token)))
        self.assertEqual(self.rows(), [])

    def test_packet_formatting_does_not_change_semantic_review(self) -> None:
        token = self.review()
        (self.root / "acceptance/A1.json").write_text(
            json.dumps(self.packet, sort_keys=True, separators=(",", ":")), encoding="utf-8")
        self.assertEqual(self.review(), token)

    def test_retry_returns_original_receipt_after_subject_changes(self) -> None:
        token = self.review()
        first = self.run_cli(*self.action_args(token, "accept", "--at", "2026-09-09T00:00:00Z"))
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        before = self.ledger.read_bytes()
        (self.root / "result.txt").write_bytes(b"Standing subsequently changed.\n")
        retry = self.run_cli(*self.action_args(token, "accept", "--at", "2026-09-10T00:00:00Z"))
        self.assertEqual(retry.returncode, 0, retry.stdout + retry.stderr)
        self.assertEqual(json.JSONDecoder().raw_decode(first.stdout.lstrip())[0],
                         json.JSONDecoder().raw_decode(retry.stdout.lstrip())[0])
        self.assertEqual(self.ledger.read_bytes(), before)
        self.assertEqual(len(self.rows()), 1)

    def test_changed_decision_or_note_does_not_overwrite_first_receipt(self) -> None:
        token = self.review()
        first = self.run_cli(*self.action_args(token))
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        before = self.ledger.read_bytes()
        for args in (self.action_args(token, "reject"),
                     self.action_args(token, "accept", "--note", "A new reason")):
            self.assert_refused(self.run_cli(*args), "ALREADY_ACTED")
        self.assertEqual(self.ledger.read_bytes(), before)

    def concurrent(self, token: str, actions: tuple[str, str]) -> list[tuple[int, str]]:
        children = [subprocess.Popen(self.command(*self.action_args(token, action)),
                                    cwd=self.root, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, text=True) for action in actions]
        results = []
        try:
            for child in children:
                stdout, stderr = child.communicate(timeout=20)
                results.append((child.returncode, stdout + stderr))
        finally:
            for child in children:
                if child.poll() is None:
                    child.kill()
                    child.communicate()
        return results

    def test_concurrent_identical_decisions_record_once(self) -> None:
        results = self.concurrent(self.review(), ("accept", "accept"))
        self.assertEqual([code for code, _ in results], [0, 0], results)
        self.assertEqual(len(self.rows()), 1)

    def test_concurrent_conflicting_decisions_have_one_winner(self) -> None:
        results = self.concurrent(self.review(), ("accept", "reject"))
        self.assertEqual(sum(code == 0 for code, _ in results), 1, results)
        self.assertIn("ALREADY_ACTED", next(output for code, output in results if code))
        self.assertEqual(len(self.rows()), 1)

    def test_corrupt_ledger_is_preserved_and_cannot_be_treated_as_empty(self) -> None:
        token = self.review()
        self.ledger.parent.mkdir(parents=True)
        damaged = b'{"packet_id": "A1", "action":'
        self.ledger.write_bytes(damaged)
        self.assert_refused(self.run_cli(*self.action_args(token)))
        self.assertEqual(self.ledger.read_bytes(), damaged)

    def test_malformed_review_in_ledger_is_a_typed_refusal(self) -> None:
        token = self.review()
        self.ledger.parent.mkdir(parents=True)
        for malformed in (None, [], "not a review"):
            with self.subTest(review=malformed):
                row = {"packet_id": "A1", "action": "ACCEPT", "review": malformed}
                original = (json.dumps(row) + "\n").encode("utf-8")
                self.ledger.write_bytes(original)
                result = self.run_cli(*self.action_args(token))
                self.assert_refused(result, "ACCEPTANCE_LEDGER_INVALID")
                self.assertNotIn("Traceback", result.stderr)
                self.assertEqual(self.ledger.read_bytes(), original)

    def test_process_death_releases_the_real_ledger_lock(self) -> None:
        token = self.review()
        code = ("import pathlib, sys; "
                "sys.path.insert(0, str(pathlib.Path(sys.argv[1]) / 'scripts')); "
                "from sovaccept import ledger; "
                "\nwith ledger.locked(pathlib.Path(sys.argv[1])):\n"
                " print('LOCKED', flush=True)\n sys.stdin.read()\n")
        child = subprocess.Popen([sys.executable, "-c", code, str(self.root)],
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, text=True)
        try:
            self.assertEqual(child.stdout.readline().strip(), "LOCKED")
        finally:
            child.kill()
            child.communicate(timeout=10)
        result = self.run_cli(*self.action_args(token))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(len(self.rows()), 1)

    def test_committed_decision_survives_death_before_response(self) -> None:
        token = self.review()
        # Only response delivery is faulted; CLI validation and persistence run unchanged.
        code = ("import builtins, os, runpy, sys; "
                "builtins.print = lambda *args, **kwargs: os._exit(91); "
                "sys.argv = sys.argv[1:]; runpy.run_path(sys.argv[0], run_name='__main__')")
        crashed = subprocess.run([sys.executable, "-c", code,
                                  *self.command(*self.action_args(token))[1:]],
                                 cwd=self.root, capture_output=True, text=True, timeout=20, check=False)
        self.assertEqual(crashed.returncode, 91, crashed.stdout + crashed.stderr)
        self.assertEqual(len(self.rows()), 1)
        original = self.ledger.read_bytes()
        retry = self.run_cli(*self.action_args(token))
        self.assertEqual(retry.returncode, 0, retry.stdout + retry.stderr)
        self.assertEqual(self.ledger.read_bytes(), original)

    def test_legacy_decision_blocks_id_reuse_without_inventing_review(self) -> None:
        token = self.review()
        old = {"packet_id": "A1", "action": "ACCEPT", "actor_id": OWNER,
               "accepted_by_seat": SEAT, "recorded_at": "2026-08-01T00:00:00Z"}
        self.ledger.parent.mkdir(parents=True)
        self.ledger.write_bytes((json.dumps(old) + "\n").encode("utf-8"))
        before = self.ledger.read_bytes()
        self.assert_refused(self.run_cli(*self.action_args(token)), "ALREADY_ACTED")
        self.assertEqual(self.ledger.read_bytes(), before)

    def test_archived_descriptive_subject_remains_readable_without_action_token(self) -> None:
        (self.root / "acceptance/A1.json").unlink()
        self.packet["subject"]["artifact"] = "the document set: first.md, second.md"
        self.write_json("acceptance/accepted/A1.json", self.packet)
        result = self.run_cli("present", "A1")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(self.packet["claim"], result.stdout)
        self.assertNotRegex(result.stdout, r"--review\s+sha256:[0-9a-f]{64}")
        self.assertEqual(self.rows(), [])

    def test_unrelated_a12_defect_does_not_block_a1(self) -> None:
        other = copy.deepcopy(self.packet)
        other["packet_id"] = "A12"
        other["what_could_defeat_it"] = []
        self.write_json("acceptance/A12.json", other)
        self.write_status(["A1", "A12"])
        result = self.run_cli(*self.action_args(self.review()))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual([row["packet_id"] for row in self.rows()], ["A1"])


if __name__ == "__main__":
    unittest.main()
