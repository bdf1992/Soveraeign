"""Cases for the fresh-context observation emitter and its observed-evidence reader.

Per `AGENTS.md` Testing and verification, every check carries a positive case
and a case proving the required refusal. Nothing here reaches the network;
every System of Record this test opens lives under its own temporary
directory.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import sov_observe  # noqa: E402
import sov_opening_readiness  # noqa: E402
from sovsession import commands as session_commands  # noqa: E402
from sovsession import principals  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


class EmitAndGrade(unittest.TestCase):
    """A fresh participant's own identity, declared through the same
    environment variables `sov_session.py` and `sov_fresh.py` already read,
    emits a real observation that `--observed` grades PASS."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.out_dir = Path(self.tmp.name) / "observed"
        self.saved_env = {key: os.environ.get(key) for key in ("SOV_SESSION", "SOV_PRINCIPAL")}
        os.environ["SOV_SESSION"] = "session-test-fresh-context"
        os.environ["SOV_PRINCIPAL"] = "principal:claude-fable-5-1"

    def tearDown(self) -> None:
        for key, value in self.saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self.tmp.cleanup()

    def test_emit_then_observed_reports_pass(self) -> None:
        emitted = sov_observe.observe_p15(ROOT, self.out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        path = self.out_dir / "P15-Q1.1.json"
        path.write_text(json.dumps(emitted, sort_keys=True, indent=2) + "\n",
                        encoding="utf-8", newline="\n")
        report = sov_opening_readiness.observed_report(self.out_dir)
        self.assertEqual(report["rows"], [{"predicate": "P15-Q1.1", "verdict": "PASS",
                                           "defects": []}])

    def test_cli_emits_the_named_file(self) -> None:
        exit_code = sov_observe.main(["p15", "--predicate", "P15-Q1.1", "--out", str(self.out_dir)])
        self.assertEqual(exit_code, 0)
        target = self.out_dir / "P15-Q1.1.json"
        self.assertTrue(target.is_file())
        observation = json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual(
            sorted(observation),
            sorted(["principal_id", "session_id", "phase_state", "work_address", "capability",
                    "required_authority", "effect_envelope", "governance_context",
                    "record_projection_id", "oral_history_used"]))

    def test_each_field_is_traceable(self) -> None:
        emitted = sov_observe.observe_p15(ROOT, self.out_dir)

        phases_bytes = (ROOT / "contracts" / "phases.json").read_bytes()
        self.assertTrue(
            emitted["governance_context"].endswith("sha256:" + sha256(phases_bytes).hexdigest()))

        custodies = json.loads(
            (ROOT / "contracts" / "custodies" / "phase-1-5.json").read_text(encoding="utf-8"))
        custody_ids = {row["custody_id"] for row in custodies["custodies"]}
        self.assertIn(emitted["work_address"], custody_ids)

        name = session_commands.session_name()
        claim = principals.resolve(ROOT, name)
        self.assertEqual(emitted["principal_id"], claim["principal"])
        self.assertEqual(emitted["session_id"], f"session:{name}")

    def test_defeating_case_removed_field_reports_open_naming_it(self) -> None:
        emitted = sov_observe.observe_p15(ROOT, self.out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        defeated = dict(emitted)
        del defeated["governance_context"]
        path = self.out_dir / "P15-Q1.1.json"
        path.write_text(json.dumps(defeated, sort_keys=True, indent=2) + "\n",
                        encoding="utf-8", newline="\n")
        report = sov_opening_readiness.observed_report(self.out_dir)
        self.assertEqual(len(report["rows"]), 1)
        row = report["rows"][0]
        self.assertEqual(row["verdict"], "OPEN")
        self.assertTrue(any("governance_context" in defect for defect in row["defects"]))


class UnidentifiedParticipant(unittest.TestCase):
    """A session that never declared `SOV_SESSION`/`SOV_PRINCIPAL` resolves no
    principal; the field is written `null`, never a placeholder, and the
    grader reports it missing rather than passing by accident."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.out_dir = Path(self.tmp.name) / "observed"
        self.saved_env = {key: os.environ.get(key) for key in
                         ("SOV_SESSION", "SOV_PRINCIPAL", "CLAUDE_CODE_SESSION_ID")}
        for key in ("SOV_SESSION", "SOV_PRINCIPAL", "CLAUDE_CODE_SESSION_ID"):
            os.environ.pop(key, None)

    def tearDown(self) -> None:
        for key, value in self.saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self.tmp.cleanup()

    def test_no_declared_identity_leaves_principal_null(self) -> None:
        emitted = sov_observe.observe_p15(ROOT, self.out_dir)
        self.assertIsNone(emitted["principal_id"])
        self.assertIsNone(emitted["record_projection_id"])


if __name__ == "__main__":
    unittest.main()
