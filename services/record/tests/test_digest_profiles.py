from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import math
import sqlite3
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from soveraeign_record_service.core import (  # noqa: E402
    BOUND_DIGEST_PROFILE, CURRENT_PROFILE, DIGEST_PROFILE, GENESIS,
    LEGACY_DIGEST_PROFILE, BrokenChain, ProfileNotAdopted, RecordService, _digest,
    _legacy_canonical, _legacy_digest,
)
from soveraeign_record_service.digest import digest_for_profile  # noqa: E402
from soveraeign_record_service.custody import (  # noqa: E402
    LEGACY_EXPORT_SCHEMA, restore, verify_export,
)


class DigestProfiles(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.opened: list[RecordService] = []

    def tearDown(self) -> None:
        for service in self.opened:
            service.close()
        self.tmp.cleanup()

    def service(self, name: str) -> RecordService:
        service = RecordService(self.root / name)
        self.opened.append(service)
        return service

    def test_v2_separates_fields_that_collide_under_v1(self) -> None:
        left = (GENESIS, "EVENT", "alpha|beta", "gamma", {"step": 1})
        right = (GENESIS, "EVENT", "alpha", "beta|gamma", {"step": 1})
        self.assertEqual(_legacy_digest(*left), _legacy_digest(*right))
        self.assertNotEqual(_digest(*left), _digest(*right))

    def test_new_entries_carry_the_current_profile_and_never_fall_back(self) -> None:
        """Relabelling an entry to any weaker profile has to break it, not soften it.

        The profile column decides which digest function verification uses, so a
        row relabelled downward would otherwise be graded under a profile that
        covers less than the one it was written with.
        """
        for weaker in (LEGACY_DIGEST_PROFILE, DIGEST_PROFILE):
            service = self.service(f"new-{weaker[-2:]}")
            entry = service.append("EVENT", "subject", "actor", {"step": 1})
            self.assertEqual(entry["digest_profile"], CURRENT_PROFILE)
            service.db.execute(
                "UPDATE journal SET digest_profile=? WHERE entry_id=?",
                (weaker, entry["entry_id"]),
            )
            service.db.commit()
            with self.assertRaises(BrokenChain):
                service.reconstruct()

    def test_opening_a_v1_store_marks_existing_rows_without_rewriting_them(self) -> None:
        root = self.root / "legacy"
        root.mkdir()
        database = root / "record-service.sqlite3"
        connection = sqlite3.connect(database)
        connection.execute(
            "CREATE TABLE journal(seq INTEGER PRIMARY KEY AUTOINCREMENT, entry_id TEXT NOT NULL "
            "UNIQUE, kind TEXT NOT NULL, subject TEXT NOT NULL, actor TEXT NOT NULL, "
            "source_address TEXT, payload_json TEXT NOT NULL, recorded_at REAL NOT NULL, "
            "prev_digest TEXT NOT NULL, entry_digest TEXT NOT NULL)"
        )
        payload = {"text": "caf\u00e9"}
        digest = _legacy_digest(GENESIS, "EVENT", "subject", "actor", payload)
        connection.execute(
            "INSERT INTO journal(entry_id,kind,subject,actor,source_address,payload_json,"
            "recorded_at,prev_digest,entry_digest) VALUES(?,?,?,?,?,?,?,?,?)",
            ("entry_legacy", "EVENT", "subject", "actor", None,
             _legacy_canonical(payload), 1.0, GENESIS, digest),
        )
        connection.commit()
        connection.close()

        service = RecordService(root)
        self.opened.append(service)
        [entry] = service.reconstruct()
        self.assertEqual(entry["digest_profile"], LEGACY_DIGEST_PROFILE)
        self.assertEqual(entry["entry_digest"], digest)

    def test_v1_export_remains_readable_and_restorable(self) -> None:
        payload = {"step": 1}
        digest = _legacy_digest(GENESIS, "EVENT", "subject", "actor", payload)
        document = {
            "export_schema": LEGACY_EXPORT_SCHEMA,
            "entry_count": 1,
            "head_digest": digest,
            "entries": [{
                "entry_id": "entry_legacy",
                "kind": "EVENT",
                "subject": "subject",
                "actor": "actor",
                "source_address": None,
                "payload": payload,
                "recorded_at": 1.0,
                "prev_digest": GENESIS,
                "entry_digest": digest,
            }],
        }
        self.assertEqual(verify_export(json.loads(json.dumps(document))), digest)
        target = self.service("restored")
        self.assertEqual(restore(target, document), 1)
        [entry] = target.reconstruct()
        self.assertEqual(entry["digest_profile"], LEGACY_DIGEST_PROFILE)

    def test_v1_export_with_legacy_nan_remains_restorable(self) -> None:
        payload = {"legacy_value": float("nan")}
        digest = _legacy_digest(GENESIS, "EVENT", "subject", "actor", payload)
        document = {
            "export_schema": LEGACY_EXPORT_SCHEMA,
            "entry_count": 1,
            "head_digest": digest,
            "entries": [{
                "entry_id": "entry_legacy_nan",
                "kind": "EVENT",
                "subject": "subject",
                "actor": "actor",
                "source_address": None,
                "payload": payload,
                "recorded_at": 1.0,
                "prev_digest": GENESIS,
                "entry_digest": digest,
            }],
        }
        self.assertEqual(verify_export(document), digest)
        target = self.service("restored-nan")
        self.assertEqual(restore(target, document), 1)
        [entry] = target.reconstruct()
        self.assertTrue(math.isnan(entry["payload"]["legacy_value"]))


class TheRefusalsNothingExercised(unittest.TestCase):
    """Two refusals stated in `decisions/0072` that no case could falsify.

    An independent witness found both by mutation: making `digest_for_profile`'s
    v3 branch return the v2 digest instead of raising, and making `digest_for_row`
    fall back to the v1 arithmetic for a profile it does not implement, each left
    all 54 record tests green. A refusal named in a governed record and defended by
    nothing is the shape this whole concern keeps producing.
    """

    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_verifying_v3_without_what_it_binds_raises_instead_of_grading_it_as_v2(self) -> None:
        """`decisions/0072`: the caller raises rather than silently grading under v2.

        Falling back would return a digest that verifies - computed over strictly
        less than the entry was written with - so a v3 row's identifier and moment
        would be unprotected again by a caller that simply forgot two arguments.
        """
        args = (GENESIS, "EVENT", "subject", "actor", {"step": 1})
        bound = digest_for_profile(BOUND_DIGEST_PROFILE, *args, entry_id="entry_a",
                                   source_address=None, recorded_at=1.0)
        for missing in ({"source_address": None, "recorded_at": 1.0},
                        {"entry_id": "entry_a", "source_address": None}):
            with self.assertRaises(ValueError):
                digest_for_profile(BOUND_DIGEST_PROFILE, *args, **missing)
        # The thing the raise prevents: a weaker digest that would verify.
        self.assertNotEqual(bound, digest_for_profile(DIGEST_PROFILE, *args),
                            "if these agreed, falling back would be undetectable")

    def test_an_unimplemented_profile_on_the_read_path_is_a_broken_chain(self) -> None:
        """Not a bad argument: the row exists, and this service cannot verify it.

        `test_adoption_refuses_a_profile_that_is_not_implemented` covers the write
        path only. This is the read path, which is where an unknown profile
        actually arrives - from a restore, or from a store written by a service
        this one has never met.
        """
        service = RecordService(self.root / "unknown")
        try:
            entry = service.append("EVENT", "subject", "actor", {"step": 1})
            service.db.execute("UPDATE journal SET digest_profile=? WHERE entry_id=?",
                               ("soveraeign-record-chain/v9", entry["entry_id"]))
            service.db.commit()
            with self.assertRaises(BrokenChain) as caught:
                service.reconstruct()
            self.assertIn("v9", str(caught.exception),
                          "the refusal names the profile it cannot implement")
        finally:
            service.close()


def _v1_only_reader(service: RecordService) -> int:
    """Verify a journal the way the service did before the profile column existed.

    Returns how many entries verified before the arithmetic stopped agreeing. This
    is the reader running in every checkout that predates profiles, and it is the
    thing a silent upgrade breaks: it is not wrong, it is old.
    """
    previous, held = GENESIS, 0
    for entry in service.entries():
        expected = _legacy_digest(previous, entry["kind"], entry["subject"],
                                  entry["actor"], entry["payload"])
        if entry["prev_digest"] != previous or entry["entry_digest"] != expected:
            return held
        previous = entry["entry_digest"]
        held += 1
    return held


class AStoreKeepsItsOwnProfile(unittest.TestCase):
    """What a store writes is the store's property, not the library's.

    `append` used to write whichever profile the library named as current, so a
    newer service opening an older journal upgraded it from the next row on. The
    live operator journal `.local/console` is the worked example: six v3 rows
    landed on 406 v1 rows and every session running the older checkout got
    `BrokenChain` at the first of them, while the journal itself stayed intact and
    verified completely under a v3-aware reader.
    """

    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.opened: list[RecordService] = []

    def tearDown(self) -> None:
        for service in self.opened:
            service.close()
        self.tmp.cleanup()

    def v1_store(self, name: str = "legacy", rows: int = 3) -> RecordService:
        """A journal written the way a pre-profile service wrote one."""
        root = self.root / name
        root.mkdir(parents=True)
        connection = sqlite3.connect(root / "record-service.sqlite3")
        connection.execute(
            "CREATE TABLE journal(seq INTEGER PRIMARY KEY AUTOINCREMENT, entry_id TEXT NOT NULL "
            "UNIQUE, kind TEXT NOT NULL, subject TEXT NOT NULL, actor TEXT NOT NULL, "
            "source_address TEXT, payload_json TEXT NOT NULL, recorded_at REAL NOT NULL, "
            "prev_digest TEXT NOT NULL, entry_digest TEXT NOT NULL)"
        )
        previous = GENESIS
        for index in range(rows):
            # Non-ASCII on purpose: v1 escapes it and v2/v3 do not, so a row that
            # silently changed encoder shows up here rather than hiding behind
            # bytes the two profiles happen to agree on.
            payload = {"step": index, "text": "café"}
            digest = _legacy_digest(previous, "EVENT", "subject", "actor", payload)
            connection.execute(
                "INSERT INTO journal(entry_id,kind,subject,actor,source_address,payload_json,"
                "recorded_at,prev_digest,entry_digest) VALUES(?,?,?,?,?,?,?,?,?)",
                (f"entry_legacy_{index}", "EVENT", "subject", "actor", None,
                 _legacy_canonical(payload), float(index), previous, digest),
            )
            previous = digest
        connection.commit()
        connection.close()
        service = RecordService(root)
        self.opened.append(service)
        return service

    def test_the_profile_is_the_strongest_any_row_carries_not_the_newest(self) -> None:
        """The shape the live journal actually has, which defeated the newest-row rule.

        Eleven sessions share that tree. An older checkout wrote v1 rows after this
        branch's service had written v3 ones, so `.local/console` runs v1, v3, v1,
        v3. Reading only the newest row makes the store's answer depend on which
        checkout wrote last; once any row is v3 no v1-only reader can verify
        through it, so writing v1 again restores nobody.
        """
        service = self.v1_store(name="interleaved", rows=2)
        service.adopt_profile(BOUND_DIGEST_PROFILE, "operator:bdo")
        # An older checkout appends two v1 rows on top, exactly as one did live.
        self.append_as_an_older_checkout(service, steps=2)
        profiles = [row["digest_profile"] for row in
                    service.db.execute("SELECT digest_profile FROM journal ORDER BY seq")]
        self.assertEqual(
            profiles,
            [LEGACY_DIGEST_PROFILE, LEGACY_DIGEST_PROFILE, BOUND_DIGEST_PROFILE,
             LEGACY_DIGEST_PROFILE, LEGACY_DIGEST_PROFILE],
            "this case needs a store whose newest row is weaker than one before it")
        self.assertEqual(service.writing_profile(), BOUND_DIGEST_PROFILE,
                         "the newest row is v1; the store has written v3 and cannot go back")
        self.assertEqual(
            service.append("EVENT", "subject", "actor", {"step": 9})["digest_profile"],
            BOUND_DIGEST_PROFILE)

    def test_a_profile_this_service_cannot_verify_refuses_rather_than_sorting_low(self) -> None:
        """An unknown profile is not the weakest profile; it is a row that cannot be read."""
        service = self.v1_store(name="unknown-row")
        service.db.execute("UPDATE journal SET digest_profile=? WHERE seq=1",
                           ("soveraeign-record-chain/v9",))
        service.db.commit()
        with self.assertRaises(BrokenChain):
            service.writing_profile()
        with self.assertRaises(BrokenChain):
            service.append("EVENT", "subject", "actor", {"step": 1})

    def append_as_an_older_checkout(self, service: RecordService, steps: int = 1) -> None:
        """Append v1 rows the way a pre-profile service would, bypassing this one.

        Straight SQL on purpose. The point is a writer that knows nothing about
        profiles, which is what actually wrote into the live store.
        """
        for step in range(steps):
            previous = service.head()
            payload = {"older": step}
            digest = _legacy_digest(previous, "EVENT", "subject", "older-checkout", payload)
            service.db.execute(
                "INSERT INTO journal(entry_id,kind,subject,actor,source_address,payload_json,"
                "recorded_at,prev_digest,entry_digest,digest_profile) "
                "VALUES(?,?,?,?,?,?,?,?,?,?)",
                (f"entry_older_{step}_{id(service)}", "EVENT", "subject", "older-checkout",
                 None, _legacy_canonical(payload), 100.0 + step, previous, digest,
                 LEGACY_DIGEST_PROFILE),
            )
        service.db.commit()

    def test_an_empty_store_starts_at_the_current_profile(self) -> None:
        service = self.service_at("fresh")
        self.assertEqual(service.writing_profile(), CURRENT_PROFILE)
        entry = service.append("EVENT", "subject", "actor", {"step": 1})
        self.assertEqual(entry["digest_profile"], CURRENT_PROFILE)

    def service_at(self, name: str) -> RecordService:
        service = RecordService(self.root / name)
        self.opened.append(service)
        return service

    def test_appending_to_a_v1_store_writes_v1_and_leaves_old_readers_working(self) -> None:
        """The defect, stated as the case that failed: this is what broke the console."""
        service = self.v1_store(rows=3)
        self.assertEqual(service.writing_profile(), LEGACY_DIGEST_PROFILE)
        entry = service.append("EVENT", "subject", "actor", {"step": 3, "text": "café"})
        self.assertEqual(entry["digest_profile"], LEGACY_DIGEST_PROFILE)
        # The bytes follow the profile too, or the row would carry v2 encoding
        # under a v1 label and stop verifying the moment anyone read it.
        self.assertEqual(
            service.db.execute("SELECT payload_json FROM journal WHERE entry_id=?",
                               (entry["entry_id"],)).fetchone()["payload_json"],
            _legacy_canonical({"step": 3, "text": "café"}))
        self.assertEqual(len(service.reconstruct()), 4)
        self.assertEqual(_v1_only_reader(service), 4)

    def test_a_v1_store_still_refuses_a_non_finite_payload(self) -> None:
        """The regression the fix could have introduced, pinned before it arrives.

        `legacy_canonical` permits NaN and has to keep permitting it, or the v1
        rows already carrying one stop verifying. Writing v1 bytes therefore had
        to gain an explicit admission check, because the refusal used to be a side
        effect of always encoding with `canonical`.
        """
        service = self.v1_store(name="legacy-nan")
        for value in (float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                service.append("EVENT", "subject", "actor", {"value": value})
        self.assertEqual(len(service.reconstruct()), 3)

    def test_adopting_a_profile_is_itself_an_entry_under_the_new_one(self) -> None:
        service = self.v1_store(name="adopting")
        adopted = service.adopt_profile(BOUND_DIGEST_PROFILE, "operator:bdo")
        self.assertEqual(adopted["digest_profile"], BOUND_DIGEST_PROFILE)
        self.assertEqual(adopted["payload"]["superseded"], LEGACY_DIGEST_PROFILE)
        self.assertEqual(service.writing_profile(), BOUND_DIGEST_PROFILE)
        following = service.append("EVENT", "subject", "actor", {"step": 9})
        self.assertEqual(following["digest_profile"], BOUND_DIGEST_PROFILE)
        self.assertEqual(len(service.reconstruct()), 5)

    def test_an_old_reader_stops_exactly_at_the_adopted_entry(self) -> None:
        """The consequence the adoption entry states, measured rather than asserted."""
        service = self.v1_store(name="boundary", rows=3)
        service.adopt_profile(BOUND_DIGEST_PROFILE, "operator:bdo")
        service.append("EVENT", "subject", "actor", {"step": 9})
        self.assertEqual(_v1_only_reader(service), 3)

    def test_adoption_refuses_to_stand_still_or_go_backwards(self) -> None:
        service = self.service_at("no-move")
        service.append("EVENT", "subject", "actor", {"step": 1})
        for target in (CURRENT_PROFILE, DIGEST_PROFILE, LEGACY_DIGEST_PROFILE):
            with self.assertRaises(ProfileNotAdopted):
                service.adopt_profile(target, "operator:bdo")
        self.assertEqual(len(service.reconstruct()), 1)

    def test_adoption_refuses_a_profile_that_is_not_implemented(self) -> None:
        service = self.v1_store(name="unknown")
        with self.assertRaises(ValueError):
            service.adopt_profile("soveraeign-record-chain/v9", "operator:bdo")
        self.assertEqual(len(service.reconstruct()), 3)


if __name__ == "__main__":
    unittest.main()
