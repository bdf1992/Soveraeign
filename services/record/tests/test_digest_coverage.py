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
    LEGACY_DIGEST_PROFILE, canonical_for, digest_for_profile, uncovered,
)

INSERT = (
    "INSERT INTO journal(entry_id,kind,subject,actor,source_address,payload_json,"
    "recorded_at,prev_digest,entry_digest,digest_profile) VALUES(?,?,?,?,?,?,?,?,?,?)"
)

#: Every fixture row carries this same payload, so "the same value in different
#: bytes" means the same thing at every row position. Two keys, because a
#: single-key object cannot express a key-order difference.
PAYLOAD = {"n": 0, "z": 1}
#: One byte form carrying a different value, and three carrying PAYLOAD's value
#: written differently. The last is read as n=0 by a JSON parser and as n=999999
#: by anything taking the first key.
PAYLOAD_FORGED = '{"forged": true}'
PAYLOAD_SPACED = '{"n": 0, "z": 1}'
PAYLOAD_REORDERED = '{"z":1,"n":0}'
PAYLOAD_DUPLICATE = '{"n":999999,"z":1,"n":0}'

#: Several replacements per column, not one. A single value per column is what let
#: this check pass while the declaration was wrong in both directions: an
#: independent witness showed ``payload_json`` was bound by parsed value rather
#: than by stored bytes, and that ``seq`` at one row position could never reorder
#: anything. One fixture proved one thing about each column and the rest was
#: assumed from it - which is the failure ``decisions/0072`` diagnoses one level
#: up, arriving one level down.
#:
#: ``digest_profile`` is chosen per profile and ``seq`` is graded on its own,
#: because its value and its order have different answers.
TAMPERS: dict[str, tuple[tuple[str, object], ...]] = {
    "entry_id": (("another id", "entry_forged"), ("empty", "")),
    "kind": (("another kind", "OBSERVATION"),),
    "subject": (("another subject", "sub_forged"), ("empty", "")),
    "actor": (("another actor", "forged-actor"), ("empty", "")),
    "source_address": (("another path", "forged/elsewhere.md"), ("null", None),
                       ("empty", "")),
    "payload_json": (
        ("a different value", PAYLOAD_FORGED),
        # The three an independent witness proved undetected. Each parses to the
        # value the digest binds and differs in the bytes a reader reads; the last
        # is read as n=0 by a JSON parser and as n=999999 by anything taking the
        # first key, so one committed row is read two ways.
        ("same value, whitespace added", PAYLOAD_SPACED),
        ("same value, extra key ordered first", PAYLOAD_REORDERED),
        ("same value, duplicate key injected", PAYLOAD_DUPLICATE),
    ),
    "recorded_at": (("epoch zero", 0.0),
                    ("one microsecond later", 1_700_000_000.500001)),
    # Not genesis: row 0's prev_digest already IS genesis, so that replacement
    # changed nothing and the case graded a no-op as evidence.
    "prev_digest": (("all ones", "1" * 64),),
    "entry_digest": (("all f", "f" * 64),),
}

#: Graded on its own. ``seq`` carries no bound value, so renumbering that preserves
#: order is undetected and hides nothing, while every reordering breaks the chain
#: through the ``prev_digest`` link. Both are true of one column, which is why it
#: is absent from COVERAGE and still impossible to reorder unnoticed.
ORDER_ONLY = "seq"


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
                "source_address": f"source/{index}.md", "payload": dict(PAYLOAD),
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
        # A replacement equal to what is already stored writes nothing, so the
        # chain verifying afterwards is not evidence of anything. One case did
        # exactly that unnoticed, so it is refused here rather than graded.
        before = service.db.execute(
            f"SELECT {column} FROM journal WHERE entry_id = ?", (target,)).fetchone()[0]
        if before == value:
            raise AssertionError(
                f"the {column!r} replacement {value!r} equals what the fixture already "
                "stored, so this case tampers with nothing and proves nothing")
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

    def _cases(self, profile: str) -> list[tuple[str, str, object]]:
        """Every (column, label, replacement) this profile is graded on."""
        cases = [(column, label, value)
                 for column, options in TAMPERS.items()
                 for label, value in options]
        swap = DIGEST_PROFILE if profile == LEGACY_DIGEST_PROFILE else LEGACY_DIGEST_PROFILE
        cases.append(("digest_profile", "another profile", swap))
        return cases

    def _grade(self, profile: str) -> None:
        """Every column, every replacement, at the first row and at the last.

        Row position matters and grading only one hid a defect: a tamper on the
        final entry cannot disturb what follows it, so a value that would reorder
        the journal proved nothing when it was only ever applied to the last row.
        """
        declared = COVERAGE[profile]
        service, made = self._chain(profile, f"chain-{profile[-2:]}")
        for position, row in ((0, made[0]), (len(made) - 1, made[-1])):
            for column, label, value in self._cases(profile):
                noticed = self._notices(service, row["entry_id"], column, value)
                with self.subTest(profile=profile, column=column, tamper=label,
                                  row=position):
                    if column in declared:
                        self.assertTrue(noticed, (
                            f"{profile} declares it covers {column!r}, but the tamper "
                            f"{label!r} at row {position} left the chain verifying "
                            "clean. The declaration over-claims and a reader trusting "
                            "it is misled."))
                    else:
                        self.assertFalse(noticed, (
                            f"{profile} does not declare {column!r}, but the tamper "
                            f"{label!r} at row {position} broke the chain. The profile "
                            "protects more than it says; widen COVERAGE rather than "
                            "leaving the guarantee unstated."))
        self.assertNotIn(ORDER_ONLY, declared,
                         "seq is graded by TheOrderOfEntries, not by this sweep")

    def test_the_sweep_covers_every_column_of_the_table(self) -> None:
        """Otherwise a column could be omitted from TAMPERS and graded by nobody."""
        swept = set(TAMPERS) | {"digest_profile", ORDER_ONLY}
        self.assertEqual(swept, set(JOURNAL_COLUMNS),
                         "a journal column is graded by no case at all")

    def test_v1_covers_exactly_what_it_declares(self) -> None:
        self._grade(LEGACY_DIGEST_PROFILE)

    def test_v2_covers_exactly_what_it_declares(self) -> None:
        self._grade(DIGEST_PROFILE)

    def test_v3_covers_exactly_what_it_declares(self) -> None:
        self._grade(BOUND_DIGEST_PROFILE)


class TheOrderOfEntries(unittest.TestCase):
    """``seq`` has one answer for its value and another for its order, both true.

    An independent witness showed the earlier check asserted only that altering
    ``seq`` must not break the chain, using one value at the last of two rows,
    where it could never reorder anything. Reordering does break it, through the
    link rather than through any digest.
    """

    def _three(self) -> tuple[RecordService, TemporaryDirectory, list[str]]:
        tmp = TemporaryDirectory()
        service = RecordService(Path(tmp.name))
        made = [service.append("EVENT", f"sub_{index}", f"actor_{index}", {"n": index})
                ["entry_id"] for index in range(3)]
        return service, tmp, made

    def test_renumbering_that_preserves_order_is_undetected_and_hides_nothing(self):
        service, tmp, _made = self._three()
        try:
            before = service.head()
            service.db.execute("UPDATE journal SET seq = seq * 10 + 5000")
            service.db.commit()
            self.assertEqual(len(service.reconstruct()), 3)
            self.assertEqual(service.head(), before,
                             "renumbering moved a head it must not touch")
        finally:
            service.close()
            tmp.cleanup()

    def _move(self, service: RecordService, entry_id: str, seq: int) -> None:
        """Set one row's seq, parking any occupant so the unique index allows it.

        `seq` is the table's primary key, so a swap cannot be written in one
        statement. Doing it in three is what an attacker with write access would
        do, and it is the case worth proving.
        """
        service.db.execute("UPDATE journal SET seq=-9999 WHERE seq=?", (seq,))
        service.db.execute("UPDATE journal SET seq=? WHERE entry_id=?", (seq, entry_id))
        parked = service.db.execute(
            "SELECT entry_id FROM journal WHERE seq=-9999").fetchone()
        if parked is not None:
            service.db.execute("UPDATE journal SET seq=? WHERE entry_id=?",
                               (seq + 1000, parked[0]))
        service.db.commit()

    def test_every_reordering_breaks_the_chain(self) -> None:
        for label, target_index, seq in (
            ("first row to the end", 0, 999),
            ("last row to the front", 2, -1),
            ("adjacent swap of the first two", 0, 2),
        ):
            service, tmp, made = self._three()
            try:
                order_before = [row[0] for row in service.db.execute(
                    "SELECT entry_id FROM journal ORDER BY seq")]
                self._move(service, made[target_index], seq)
                order_after = [row[0] for row in service.db.execute(
                    "SELECT entry_id FROM journal ORDER BY seq")]
                with self.subTest(reordering=label):
                    self.assertNotEqual(order_before, order_after,
                                        "this case did not actually reorder anything")
                    with self.assertRaises(BrokenChain):
                        service.reconstruct()
            finally:
                service.close()
                tmp.cleanup()


class ThePayloadBytes(unittest.TestCase):
    """The digest binds the parsed value; verification also binds the bytes.

    Without the second half, byte-different but value-identical JSON went
    undetected. Duplicate-key injection is the sharp case: a JSON parser reads the
    last key and anything taking the first reads another number, so one committed
    row is read two ways and the chain endorses both.
    """

    def test_a_row_that_parses_the_same_but_reads_differently_is_refused(self) -> None:
        with TemporaryDirectory() as tmp:
            service = RecordService(Path(tmp))
            entry = service.append("EVENT", "sub", "alice", dict(PAYLOAD))
            for forged in (PAYLOAD_SPACED, PAYLOAD_REORDERED, PAYLOAD_DUPLICATE):
                service.db.execute("UPDATE journal SET payload_json=? WHERE entry_id=?",
                                   (forged, entry["entry_id"]))
                with self.subTest(stored_bytes=forged):
                    with self.assertRaises(BrokenChain):
                        service.reconstruct()
                service.db.rollback()
            self.assertEqual(len(service.reconstruct()), 1, "an honest row was refused")
            service.close()

    def test_every_profile_declares_the_encoding_its_bytes_must_have(self) -> None:
        for profile in (LEGACY_DIGEST_PROFILE, DIGEST_PROFILE, BOUND_DIGEST_PROFILE):
            self.assertTrue(callable(canonical_for(profile)))
        with self.assertRaises(ValueError):
            canonical_for("soveraeign-record-chain/v9")


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
