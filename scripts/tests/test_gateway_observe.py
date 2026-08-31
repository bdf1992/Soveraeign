from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import sqlite3
from tempfile import TemporaryDirectory
import unittest
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "gateway_observe", ROOT / "scripts" / "gateway_observe.py"
)
assert SPEC and SPEC.loader
observe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(observe)
import witness_gateway  # noqa: E402


class GatewayObserverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = TemporaryDirectory()
        cls.state = Path(cls.temporary.name) / "state"
        cls.actor = "observer-test"
        cls.output = witness_gateway.run_driver(cls.state, cls.actor, "HUMAN")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def test_independent_observer_reconstructs_exact_crossing(self) -> None:
        self.assertEqual(observe.crossing_defects(
            ROOT, self.state, self.output, self.actor, "HUMAN"
        ), [])

    def test_independent_observer_rejects_spoofed_caller_return(self) -> None:
        spoofed = json.loads(json.dumps(self.output))
        spoofed["returned_receipt"]["actor"] = "mallory"
        defects = observe.crossing_defects(ROOT, self.state, spoofed, self.actor, "HUMAN")
        self.assertIn("TERMINAL_RECEIPT_MISMATCH", defects)
        self.assertIn("TERMINAL_ATTRIBUTION_INVALID", defects)

    def test_independent_observer_rejects_session_record_mismatch(self) -> None:
        tampered = Path(self.temporary.name) / "session-mismatch"
        shutil.copytree(self.state, tampered)
        database = tampered / "record" / "record-service.sqlite3"
        connection = sqlite3.connect(database)
        try:
            row = connection.execute(
                "SELECT seq, payload_json FROM journal WHERE payload_json LIKE ? ORDER BY seq LIMIT 1",
                ('%"record_kind":"operator-session"%',)).fetchone()
            self.assertIsNotNone(row)
            payload = json.loads(row[1])
            payload["binding_id"] = "forged-host-binding"
            connection.execute(
                "UPDATE journal SET payload_json=? WHERE seq=?",
                (json.dumps(payload, sort_keys=True, separators=(",", ":")), row[0]))
            connection.commit()
        finally:
            connection.close()
        defects = observe.crossing_defects(ROOT, tampered, self.output, self.actor, "HUMAN")
        self.assertIn("SESSION_RECORD_INVALID", defects)

    def test_independent_observer_rejects_rewritten_gateway_evidence(self) -> None:
        tampered = Path(self.temporary.name) / "tampered"
        shutil.copytree(self.state, tampered)
        database = tampered / "record" / "record-service.sqlite3"
        connection = sqlite3.connect(database)
        connection.execute("UPDATE journal SET actor='mallory' WHERE seq=(SELECT MAX(seq) FROM journal)")
        connection.commit()
        connection.close()
        defects = observe.crossing_defects(ROOT, tampered, self.output, self.actor, "HUMAN")
        self.assertIn("JOURNAL_CHAIN_INVALID", defects)

    def test_independent_observer_refuses_unknown_digest_profile(self) -> None:
        tampered = Path(self.temporary.name) / "unknown-profile"
        shutil.copytree(self.state, tampered)
        database = tampered / "record" / "record-service.sqlite3"
        connection = sqlite3.connect(database)
        connection.execute(
            "UPDATE journal SET digest_profile='soveraeign-record-chain/v99' "
            "WHERE seq=(SELECT MAX(seq) FROM journal)"
        )
        connection.commit()
        connection.close()
        defects = observe.crossing_defects(ROOT, tampered, self.output, self.actor, "HUMAN")
        self.assertIn("JOURNAL_CHAIN_INVALID", defects)

    def _bytes_only_tamper(self, name: str, rewrite) -> list[str]:
        """Rewrite the newest row's payload bytes without changing what they parse to.

        Every profile binds the payload's *parsed value*, so a tamper of this shape
        leaves the digest untouched and can only be caught by the separate rule
        requiring the stored bytes to be the profile's canonical encoding. The
        other cases in this file change a value or a profile, so the digest catches
        all of them and none reaches that rule.
        """
        tampered = Path(self.temporary.name) / name
        shutil.copytree(self.state, tampered)
        database = tampered / "record" / "record-service.sqlite3"
        connection = sqlite3.connect(database)
        try:
            row = connection.execute(
                "SELECT seq, payload_json FROM journal ORDER BY seq DESC LIMIT 1").fetchone()
            substitute = rewrite(row[1])
            self.assertNotEqual(substitute, row[1], "this tamper changes no bytes")
            self.assertEqual(json.loads(substitute), json.loads(row[1]),
                             "this tamper changes the value, so the digest would catch it")
            connection.execute("UPDATE journal SET payload_json=? WHERE seq=?",
                               (substitute, row[0]))
            connection.commit()
        finally:
            connection.close()
        return observe.crossing_defects(ROOT, tampered, self.output, self.actor, "HUMAN")

    def test_observer_rejects_payload_bytes_that_parse_to_the_same_value(self) -> None:
        """The defeating case for the canonical byte rule, which nothing exercised.

        Without it this observer grades a strictly weaker property than the
        participant: two readers of one committed row can disagree about its
        content while the chain endorses both.
        """
        spaced = self._bytes_only_tamper(
            "spaced-bytes",
            lambda stored: json.dumps(json.loads(stored), sort_keys=True,
                                      separators=(", ", ": ")))
        self.assertIn("JOURNAL_CHAIN_INVALID", spaced)

    def test_observer_rejects_a_duplicate_key_injected_into_a_committed_row(self) -> None:
        """The concrete harm: a parser keeps the last key, another reader the first."""
        def inject(stored: str) -> str:
            parsed = json.loads(stored)
            key = sorted(parsed)[0]
            body = json.dumps(parsed, sort_keys=True, separators=(",", ":"))
            forged = json.dumps(key) + ":" + json.dumps("forged") + ","
            return "{" + forged + body[1:]
        self.assertIn("JOURNAL_CHAIN_INVALID", self._bytes_only_tamper("duplicate-key", inject))

    def test_observer_imports_no_participant_implementation(self) -> None:
        source = (ROOT / "scripts" / "gateway_observe.py").read_text(encoding="utf-8")
        self.assertNotIn("soveraeign_", source)
        self.assertNotIn("gateway_witness_driver", source)


if __name__ == "__main__":
    unittest.main()
