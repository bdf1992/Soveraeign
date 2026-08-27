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
    CURRENT_PROFILE, DIGEST_PROFILE, GENESIS, LEGACY_DIGEST_PROFILE, BrokenChain,
    RecordService, _digest, _legacy_canonical, _legacy_digest,
)
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


if __name__ == "__main__":
    unittest.main()
