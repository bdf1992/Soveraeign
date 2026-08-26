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

    def test_observer_imports_no_participant_implementation(self) -> None:
        source = (ROOT / "scripts" / "gateway_observe.py").read_text(encoding="utf-8")
        self.assertNotIn("soveraeign_", source)
        self.assertNotIn("gateway_witness_driver", source)


if __name__ == "__main__":
    unittest.main()
