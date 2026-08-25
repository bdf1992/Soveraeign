"""Positive and defeating cases for sealed recovery secrets (decisions/0048 ID-11).

Passing establishes `BUILT` for this component. It decides nothing about whether
recovery secrets are how the root recovers; that is Bdo's blank.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import itertools
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from soveraeign_identity_service.recovery import (  # noqa: E402
    ALREADY_ENROLLED, NOT_ENROLLED, SECRET_SPENT, SECRET_UNKNOWN, SET_REVOKED,
    Recovery, digest_of,
)

T0 = datetime(2026, 8, 23, 12, 0, tzinfo=timezone.utc)
ROOT = {"principal_id": "principal:bdo", "controller": None}
SESSION = {"principal_id": "principal:session", "controller": "principal:bdo"}


class Clock:
    def __init__(self) -> None:
        self.now = T0

    def advance(self, seconds: float) -> None:
        self.now = self.now + timedelta(seconds=seconds)

    def __call__(self) -> datetime:
        return self.now


class RecoverySecrets(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = Clock()
        source = (f"secret-{n}" for n in itertools.count(1))
        self.recovery = Recovery(clock=self.clock, secret_source=lambda: next(source))

    # -- positive ------------------------------------------------------------

    def test_enroll_then_redeem(self) -> None:
        record, issued = self.recovery.enroll("principal:bdo", count=3)
        self.assertEqual(record["outcome"], "COMMITTED")
        self.assertEqual(len(issued), 3)
        redeemed = self.recovery.redeem("principal:bdo", issued[1])
        self.assertEqual(redeemed["outcome"], "COMMITTED")
        self.assertEqual(redeemed["remaining"], 2)
        self.assertFalse(redeemed["exhausted"])

    def test_each_secret_is_independent(self) -> None:
        _, issued = self.recovery.enroll("principal:bdo", count=3)
        for secret in issued:
            self.assertEqual(self.recovery.redeem("principal:bdo", secret)["outcome"],
                             "COMMITTED")
        self.assertEqual(self.recovery.status("principal:bdo")["remaining"], 0)

    def test_exhaustion_is_visible_on_the_last_redemption(self) -> None:
        _, issued = self.recovery.enroll("principal:bdo", count=2)
        self.recovery.redeem("principal:bdo", issued[0])
        last = self.recovery.redeem("principal:bdo", issued[1])
        self.assertTrue(last["exhausted"])

    def test_revoke_then_re_enroll(self) -> None:
        _, first = self.recovery.enroll("principal:bdo", count=2)
        self.assertEqual(self.recovery.revoke("principal:bdo", revoked_by="principal:bdo",
                                              reason="paper copy lost")["outcome"],
                         "COMMITTED")
        record, second = self.recovery.enroll("principal:bdo", count=2)
        self.assertEqual(record["outcome"], "COMMITTED")
        self.assertEqual(self.recovery.redeem("principal:bdo", second[0])["outcome"],
                         "COMMITTED")
        self.assertEqual(self.recovery.redeem("principal:bdo", first[0])["reason_code"],
                         SECRET_UNKNOWN)

    # -- defeating -----------------------------------------------------------

    def test_replay_is_refused(self) -> None:
        _, issued = self.recovery.enroll("principal:bdo", count=2)
        self.recovery.redeem("principal:bdo", issued[0])
        replay = self.recovery.redeem("principal:bdo", issued[0])
        self.assertEqual(replay["reason_code"], SECRET_SPENT)

    def test_unknown_secret_is_refused(self) -> None:
        self.recovery.enroll("principal:bdo", count=2)
        self.assertEqual(self.recovery.redeem("principal:bdo", "guessed")["reason_code"],
                         SECRET_UNKNOWN)

    def test_redeeming_without_enrollment_is_refused(self) -> None:
        self.assertEqual(self.recovery.redeem("principal:nobody", "anything")["reason_code"],
                         NOT_ENROLLED)

    def test_revoked_set_cannot_be_redeemed(self) -> None:
        _, issued = self.recovery.enroll("principal:bdo", count=2)
        self.recovery.revoke("principal:bdo", revoked_by="principal:bdo", reason="rotated")
        self.assertEqual(self.recovery.redeem("principal:bdo", issued[0])["reason_code"],
                         SET_REVOKED)

    def test_enrollment_never_silently_replaces_a_live_set(self) -> None:
        _, first = self.recovery.enroll("principal:bdo", count=2)
        second_record, second = self.recovery.enroll("principal:bdo", count=2)
        self.assertEqual(second_record["reason_code"], ALREADY_ENROLLED)
        self.assertEqual(second, [])
        self.assertEqual(self.recovery.redeem("principal:bdo", first[0])["outcome"],
                         "COMMITTED")

    def test_double_revoke_is_refused(self) -> None:
        self.recovery.enroll("principal:bdo", count=1)
        self.recovery.revoke("principal:bdo", revoked_by="principal:bdo", reason="once")
        self.assertEqual(self.recovery.revoke("principal:bdo", revoked_by="principal:bdo",
                                              reason="twice")["reason_code"], SET_REVOKED)

    def test_revoking_without_enrollment_is_refused(self) -> None:
        self.assertEqual(self.recovery.revoke("principal:nobody", revoked_by="principal:bdo",
                                              reason="none")["reason_code"], NOT_ENROLLED)

    # -- the gap report ------------------------------------------------------

    def test_unenrolled_names_the_root_first_and_says_it_is_terminal(self) -> None:
        gaps = self.recovery.unenrolled([SESSION, ROOT])
        self.assertEqual(gaps[0]["principal_id"], "principal:bdo")
        self.assertTrue(gaps[0]["is_root"])
        self.assertIn("none can be supplied", gaps[0]["consequence"])
        self.assertIn("controller", gaps[1]["consequence"])

    def test_enrolled_principals_leave_the_gap_report(self) -> None:
        self.recovery.enroll("principal:bdo", count=1)
        self.assertEqual([gap["principal_id"] for gap in self.recovery.unenrolled([ROOT])], [])

    def test_exhausted_set_returns_to_the_gap_report(self) -> None:
        _, issued = self.recovery.enroll("principal:bdo", count=1)
        self.recovery.redeem("principal:bdo", issued[0])
        gaps = self.recovery.unenrolled([ROOT])
        self.assertEqual(gaps[0]["principal_id"], "principal:bdo")
        self.assertEqual(gaps[0]["remaining"], 0)

    def test_revoked_set_returns_to_the_gap_report(self) -> None:
        self.recovery.enroll("principal:bdo", count=1)
        self.recovery.revoke("principal:bdo", revoked_by="principal:bdo", reason="rotated")
        gaps = self.recovery.unenrolled([ROOT])
        self.assertTrue(gaps[0]["revoked"])

    # -- the secret never enters the record ----------------------------------

    def test_no_record_ever_carries_a_secret(self) -> None:
        record, issued = self.recovery.enroll("principal:bdo", count=2)
        self.recovery.redeem("principal:bdo", issued[0])
        self.recovery.redeem("principal:bdo", "guessed")
        rendered = repr(self.recovery.records)
        for secret in issued:
            self.assertNotIn(secret, rendered)
        self.assertNotIn("guessed", rendered)
        self.assertIn(digest_of(issued[0]), rendered)
        del record


if __name__ == "__main__":
    unittest.main()
