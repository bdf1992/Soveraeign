"""Grade every chain profile's declared coverage against what it actually detects.

``digest.COVERAGE`` states which journal columns each profile binds into the entry
digest. A declaration like that is worth nothing unless something proves it, so
this tampers with every column of a real journal, one column per case, and checks
the result both ways:

- every column the profile claims to cover MUST break the chain when altered;
- every column it does not claim MUST survive alteration, which keeps the
  declaration from quietly over-claiming.

The second direction is the one that matters. Under ``record-chain/v2`` the
journal's own identifiers were unbound: two entries could exchange ``entry_id``
values, the chain verified clean, and every receipt in the repository citing an
identifier could be repointed at other content without trace. Nothing failed,
because nothing had ever tampered with a column outside the payload.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from soveraeign_record_service.core import (  # noqa: E402
    GENESIS, BrokenChain, RecordService, _canonical,
)
from soveraeign_record_service.digest import (  # noqa: E402
    BOUND_DIGEST_PROFILE, COVERAGE, CURRENT_PROFILE, DIGEST_PROFILE, JOURNAL_COLUMNS,
    LEGACY_DIGEST_PROFILE, digest_for_profile, uncovered,
)

INSERT = (
    "INSERT INTO journal(entry_id,kind,subject,actor,source_address,payload_json,"
    "recorded_at,prev_digest,entry_digest,digest_profile) VALUES(?,?,?,?,?,?,?,?,?,?)"
)

#: One replacement per column, each guaranteed to differ from what the fixture
#: writes. ``digest_profile`` is handled separately because its replacement has to
#: be a profile other than the row's own.
TAMPER = {
    "seq": 999,
    "entry_id": "entry_forged",
    "kind": "OBSERVATION",
    "subject": "sub_forged",
    "actor": "forged-actor",
    "source_address": "forged/elsewhere.md",
    "payload_json": '{"forged": true}',
    "recorded_at": 0.0,
    "prev_digest": "0" * 64,
    "entry_digest": "f" * 64,
}


class Coverage(unittest.TestCase):
    """Every profile, every column, both directions."""

    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.opened: list[RecordService] = []

    def tearDown(self) -> None:
        for service in self.opened:
            service.close()
        self.tmp.cleanup()

    def _chain(self, profile: str, name: str) -> tuple[RecordService, list[dict]]:
        """Write two entries directly under ``profile``, bypassing ``append``.

        Direct insertion is what lets one case exercise a profile the service no
        longer writes. Every field differs between the two entries so a tamper
        always changes the stored value.
        """
        service = RecordService(self.root / name)
        self.opened.append(service)
        previous, made = GENESIS, []
        for index in (0, 1):
            row = {
                "entry_id": f"entry_{index}", "kind": "RECEIPT",
                "subject": f"sub_{index}", "actor": f"actor_{index}",
                "source_address": f"source/{index}.md", "payload": {"n": index},
                "recorded_at": 1_700_000_000.5 + index,
            }
            row["entry_digest"] = digest_for_profile(
                profile, previous, row["kind"], row["subject"], row["actor"],
                row["payload"], entry_id=row["entry_id"],
                source_address=row["source_address"], recorded_at=row["recorded_at"],
            )
            service.db.execute(INSERT, (
                row["entry_id"], row["kind"], row["subject"], row["actor"],
                row["source_address"], _canonical(row["payload"]), row["recorded_at"],
                previous, row["entry_digest"], profile,
            ))
            previous = row["entry_digest"]
            made.append(row)
        service.db.commit()
        return service, made

    def _notices(self, service: RecordService, target: str, column: str,
                 value: object) -> bool:
        """Alter one column, report whether verification objects, then roll it back.

        The write is never committed. Verification reads through the same
        connection, so it sees the uncommitted row exactly as a committed tamper
        would present it, and the rollback restores the chain without touching the
        disk. That matters to the whole repository rather than to this file: the
        store is opened `synchronous=FULL`, so a committed tamper per column per
        profile is thirty-three fsyncs, which is enough on its own to push
        `scripts/verify.py` past its fifteen-second budget.
        """
        service.db.execute(
            f"UPDATE journal SET {column} = ? WHERE entry_id = ?", (value, target))
        try:
            service.reconstruct()
            noticed = False
        except BrokenChain:
            noticed = True
        finally:
            service.db.rollback()
        # The rollback is load-bearing, not tidiness: the next column must grade
        # against an intact chain. Prove it did rather than assume it.
        service.reconstruct()
        return noticed

    def _replacement(self, profile: str, column: str) -> object:
        if column != "digest_profile":
            return TAMPER[column]
        return DIGEST_PROFILE if profile == LEGACY_DIGEST_PROFILE else LEGACY_DIGEST_PROFILE

    def _grade(self, profile: str) -> None:
        declared = COVERAGE[profile]
        service, made = self._chain(profile, f"chain-{profile[-2:]}")
        target = made[1]["entry_id"]
        for column in sorted(JOURNAL_COLUMNS):
            noticed = self._notices(service, target, column,
                                    self._replacement(profile, column))
            with self.subTest(profile=profile, column=column):
                if column in declared:
                    self.assertTrue(noticed, (
                        f"{profile} declares it covers {column!r}, but rewriting that "
                        "column left the chain verifying clean. The declaration "
                        "over-claims and a reader trusting it is misled."))
                else:
                    self.assertFalse(noticed, (
                        f"{profile} does not declare {column!r}, but rewriting it did "
                        "break the chain. The profile protects more than it says; "
                        "widen COVERAGE rather than leaving the guarantee unstated."))

    def test_v1_covers_exactly_what_it_declares(self) -> None:
        self._grade(LEGACY_DIGEST_PROFILE)

    def test_v2_covers_exactly_what_it_declares(self) -> None:
        self._grade(DIGEST_PROFILE)

    def test_v3_covers_exactly_what_it_declares(self) -> None:
        self._grade(BOUND_DIGEST_PROFILE)


class TheDeclarationItself(unittest.TestCase):
    def test_journal_columns_match_the_table_the_service_creates(self) -> None:
        """A column added to the table without a coverage ruling fails here."""
        with TemporaryDirectory() as tmp:
            service = RecordService(Path(tmp))
            actual = {row[1] for row in service.db.execute("PRAGMA table_info(journal)")}
            service.close()
        self.assertEqual(actual, set(JOURNAL_COLUMNS),
                         "the journal table and the coverage vocabulary disagree")

    def test_every_profile_declares_coverage(self) -> None:
        for profile in (LEGACY_DIGEST_PROFILE, DIGEST_PROFILE, BOUND_DIGEST_PROFILE):
            self.assertIn(profile, COVERAGE)

    def test_uncovered_is_the_complement_and_refuses_an_unknown_profile(self) -> None:
        for profile, expected in (
            (DIGEST_PROFILE, {"seq", "entry_id", "source_address", "recorded_at"}),
            (BOUND_DIGEST_PROFILE, {"seq"}),
        ):
            self.assertEqual(uncovered(profile), expected)
        with self.assertRaises(ValueError):
            uncovered("soveraeign-record-chain/v9")

    def test_the_current_profile_is_the_one_new_entries_carry(self) -> None:
        with TemporaryDirectory() as tmp:
            service = RecordService(Path(tmp))
            entry = service.append("EVENT", "subject", "actor", {"step": 1})
            service.close()
        self.assertEqual(entry["digest_profile"], CURRENT_PROFILE)
        self.assertEqual(CURRENT_PROFILE, BOUND_DIGEST_PROFILE)


class TheIdentifierSwap(unittest.TestCase):
    """The forgery v2 permitted, kept as the case that defeats a return to it."""

    def test_two_entries_cannot_exchange_identifiers_unnoticed(self) -> None:
        with TemporaryDirectory() as tmp:
            service = RecordService(Path(tmp))
            small = service.append("RECEIPT", "payment_to_alice", "alice", {"amount": 5})
            large = service.append("RECEIPT", "payment_to_bob", "bob", {"amount": 5000})
            service.db.execute("UPDATE journal SET entry_id=? WHERE entry_id=?",
                               ("swap", small["entry_id"]))
            service.db.execute("UPDATE journal SET entry_id=? WHERE entry_id=?",
                               (small["entry_id"], large["entry_id"]))
            service.db.execute("UPDATE journal SET entry_id=? WHERE entry_id=?",
                               (large["entry_id"], "swap"))
            service.db.commit()
            with self.assertRaises(BrokenChain):
                service.reconstruct()
            service.close()

    def test_a_moment_cannot_be_moved_unnoticed(self) -> None:
        with TemporaryDirectory() as tmp:
            service = RecordService(Path(tmp))
            entry = service.append("EVENT", "subject", "actor", {"step": 1})
            # One microsecond, not an obvious year-zero value: the moment enters the
            # digest as its exact float, so a change below display resolution counts.
            service.db.execute("UPDATE journal SET recorded_at=? WHERE entry_id=?",
                               (entry["recorded_at"] + 1e-6, entry["entry_id"]))
            service.db.commit()
            with self.assertRaises(BrokenChain):
                service.reconstruct()
            service.close()


class TheRoundTrip(unittest.TestCase):
    """Binding the moment must not make a faithful restore look like tampering."""

    def test_export_and_restore_preserve_a_v3_chain(self) -> None:
        from soveraeign_record_service.custody import (  # noqa: PLC0415
            export_document, restore, verify_export,
        )
        with TemporaryDirectory() as tmp:
            source = RecordService(Path(tmp) / "source")
            for index in range(3):
                source.append("RECEIPT", f"sub_{index}", f"actor_{index}", {"n": index},
                              source_address=f"src/{index}.md")
            head = source.head()
            document = export_document(source)
            self.assertEqual(document["entries"][0]["digest_profile"], BOUND_DIGEST_PROFILE)
            self.assertEqual(verify_export(document), head)

            restored = RecordService(Path(tmp) / "restored")
            self.assertEqual(restore(restored, document, expected_head=head), 3)
            self.assertEqual(restored.head(), head)
            self.assertEqual(len(restored.reconstruct()), 3)
            source.close()
            restored.close()


if __name__ == "__main__":
    unittest.main()
