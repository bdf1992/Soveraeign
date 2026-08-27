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
import ast
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


class Independence(unittest.TestCase):
    """The walk must not borrow the participant's arithmetic to check the participant.

    This is the property every other claim the walk makes rests on, and until now
    nothing enforced it. An independent witness proved the gap by editing
    `sovwitness/record_chain.py` to import `digest_for_profile` from the service
    and return it: the walk still printed 28/28 and exited 0, and the repository
    would have kept citing that run as an independent observation of a function
    agreeing with itself.

    `scripts/tests/test_gateway_observe.py` has had the equivalent check for the
    sibling verifier since it was written. This is that check, for this one.
    """

    #: The walk and every module it reaches for chain arithmetic. `record_tampers`
    #: and `record_profiles` are here because both write forgeries and seed rows,
    #: which is exactly where importing the service is most tempting.
    OUTSIDE_THE_PARTICIPANT = (
        Path("scripts") / "witness_record.py",
        Path("scripts") / "sovwitness" / "record_chain.py",
        Path("scripts") / "sovwitness" / "record_tampers.py",
        Path("scripts") / "sovwitness" / "record_profiles.py",
    )

    #: The participant's package. The walk is allowed to *name* it - it launches
    #: `python -m soveraeign_record_service.cli` as a subprocess and sets PYTHONPATH
    #: for it - so a substring search over the source reports the walk's own correct
    #: behaviour as a violation. The sibling check in `test_gateway_observe.py` can
    #: use a substring only because that observer never names the package at all.
    PARTICIPANT = "soveraeign_record_service"

    def _imports(self, source: str) -> list[str]:
        """Every module this file imports, including inside a function body.

        Parsed rather than matched. The way this rule gets broken is a local import
        in the middle of a function, which reads as ordinary code and which a
        line-oriented check at the top of the file would never see.
        """
        found: list[str] = []
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Import):
                found.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                found.append(node.module)
        return found

    def test_the_walk_imports_no_participant_implementation(self) -> None:
        for relative in self.OUTSIDE_THE_PARTICIPANT:
            imported = self._imports((ROOT / relative).read_text(encoding="utf-8"))
            borrowed = [name for name in imported
                        if name == self.PARTICIPANT or name.startswith(self.PARTICIPANT + ".")]
            self.assertEqual(
                borrowed, [],
                f"{relative} imports {borrowed}; the walk recomputes the chain from "
                "services/record/CHARTER.md and reaches the service only as a "
                "subprocess, or it is not an independent observation")

    def test_the_rule_can_see_an_import_hidden_inside_a_function(self) -> None:
        """The check must catch the way it would actually be broken."""
        hidden = ("def recompute(previous, entry):\n"
                  f"    from {self.PARTICIPANT}.digest import digest_for_profile\n"
                  "    return digest_for_profile(entry)\n")
        self.assertIn(f"{self.PARTICIPANT}.digest", self._imports(hidden))
        self.assertEqual(self._imports("import json\n"), ["json"])

    def test_the_check_reads_files_that_exist(self) -> None:
        """Otherwise a renamed module makes the check above pass by reading nothing."""
        for relative in self.OUTSIDE_THE_PARTICIPANT:
            self.assertTrue((ROOT / relative).is_file(), f"{relative} is not there")


if __name__ == "__main__":
    unittest.main()
