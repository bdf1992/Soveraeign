"""Prove the Record Service witness can fail.

A witness that only ever passes is not evidence about the participant, it is
evidence about the witness. Each case here breaks one thing the walk on issue #7
claims to catch and checks that the walk catches it.

The chain verifier and the CLI boundary are exercised directly; the full
subprocess walk is the thing under test in `scripts/witness_record.py` and is not
re-run here.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import importlib.util
import json
import sqlite3
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "witness_record", ROOT / "scripts" / "witness_record.py"
)
assert SPEC and SPEC.loader
witness = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(witness)


def _walked(store: Path) -> list[dict]:
    """Commit two entries through the CLI and return the reconstructed journal."""
    witness.record(store, "append-entry", "--kind", "EVENT", "--subject", "s",
                   "--actor", "Bdo", "--payload", '{"step": "one"}')
    witness.record(store, "append-entry", "--kind", "EVENT", "--subject", "s",
                   "--actor", "Bdo", "--payload", '{"step": "two"}')
    return witness.record(store, "reconstruct-journal")["entries"]


class ChainVerification(unittest.TestCase):
    """The witness recomputes the chain rather than trusting the reported digest.

    One real journal is walked once for the whole class and each case works on its
    own copy. Every command here is a subprocess, so walking it per case would pay
    three process starts a test to observe the same two entries.
    """

    @classmethod
    def setUpClass(cls):
        cls._store = TemporaryDirectory(ignore_cleanup_errors=True)
        cls.walked = _walked(Path(cls._store.name) / "record")

    @classmethod
    def tearDownClass(cls):
        cls._store.cleanup()

    def entries(self) -> list[dict]:
        """A private copy, so a case that rewrites history does not rewrite it for others."""
        return json.loads(json.dumps(self.walked))

    def test_an_intact_chain_verifies(self):
        self.assertEqual(witness.verify_chain(self.entries()), [])

    def test_a_rewritten_payload_stops_verifying(self):
        entries = self.entries()
        entries[1]["payload"] = {"step": "something else entirely"}
        self.assertEqual(witness.verify_chain(entries), [entries[1]["entry_id"]])

    def test_a_rewritten_actor_stops_verifying(self):
        entries = self.entries()
        entries[0]["actor"] = "someone else"
        self.assertIn(entries[0]["entry_id"], witness.verify_chain(entries))

    def test_a_removed_entry_stops_verifying(self):
        """Dropping a link breaks the next one's prev_digest, which is the point."""
        entries = self.entries()
        self.assertEqual(witness.verify_chain(entries[1:]), [entries[1]["entry_id"]])


class ServiceBoundary(unittest.TestCase):
    """The refusals the walk relies on are reachable through the CLI, not only in code."""

    def test_a_rewritten_journal_refuses_reconstruction(self):
        with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            store = Path(tmp) / "record"
            _walked(store)
            connection = sqlite3.connect(store / "record-service.sqlite3")
            connection.execute("UPDATE journal SET actor='forged' WHERE seq=1")
            connection.commit()
            connection.close()
            refused = witness.record(store, "reconstruct-journal", expect=2)
            self.assertEqual(refused["reason_code"], "DIGEST_MISMATCH")

    def test_a_governing_document_is_refused_as_event_storage(self):
        with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            store = Path(tmp) / "record"
            refused = witness.record(store, "append-entry", "--kind", "EVENT",
                                     "--subject", "s", "--actor", "Bdo",
                                     "--source-address", "CONTRACT.md", expect=2)
            self.assertEqual(refused["reason_code"], "DESIGN_RECORD_REFUSED")

    def test_an_unknown_entry_refuses_rather_than_returning_empty(self):
        with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            store = Path(tmp) / "record"
            refused = witness.record(store, "read-entry", "--entry", "entry_absent", expect=3)
            self.assertEqual(refused["reason_code"], "MISSING_PRECONDITION")

    def test_an_undeclared_entry_kind_is_refused(self):
        """argparse holds the declared kinds, so an invalid one never reaches the store."""
        with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            store = Path(tmp) / "record"
            proc = subprocess.run(
                [sys.executable, "-m", "soveraeign_record_service.cli", "--root", str(store),
                 "append-entry", "--kind", "GUESS", "--subject", "s", "--actor", "Bdo"],
                capture_output=True, text=True, env=witness._environment(),
                cwd=str(ROOT), check=False)
            self.assertEqual(proc.returncode, 2)
            self.assertIn("GUESS", proc.stderr)


class DeclaredSurface(unittest.TestCase):
    """Discovery answers from the manifest, so the two cannot drift apart quietly."""

    def test_discovery_matches_the_manifest(self):
        manifest = json.loads(
            (ROOT / "services" / "record" / "contracts" / "service.json")
            .read_text(encoding="utf-8"))
        with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            declared = witness.record(Path(tmp) / "record", "operations")
        self.assertEqual([op["operation"] for op in declared["operations"]],
                         [op["operation"] for op in manifest["operations"]])

    def test_every_declared_operation_is_reachable(self):
        """A manifest that declares an operation the CLI cannot reach is a defect."""
        manifest = json.loads(
            (ROOT / "services" / "record" / "contracts" / "service.json")
            .read_text(encoding="utf-8"))
        sys.path.insert(0, str(ROOT / "services" / "record" / "src"))
        from soveraeign_record_service import cli  # noqa: PLC0415

        reachable = set(cli._commands())
        declared = {op["operation"] for op in manifest["operations"]}
        self.assertEqual(declared - reachable, set())

    def test_no_reachable_command_is_undeclared(self):
        """The reverse: a command the CLI reaches that the manifest does not declare."""
        manifest = json.loads(
            (ROOT / "services" / "record" / "contracts" / "service.json")
            .read_text(encoding="utf-8"))
        sys.path.insert(0, str(ROOT / "services" / "record" / "src"))
        from soveraeign_record_service import cli  # noqa: PLC0415

        declared = {op["operation"] for op in manifest["operations"]}
        # `operations` is discovery over the manifest, not an operation on a record.
        self.assertEqual(set(cli._commands()) - declared - {"operations"}, set())


if __name__ == "__main__":
    unittest.main()
