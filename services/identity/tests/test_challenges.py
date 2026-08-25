"""Positive and defeating cases for the challenge lifecycle (decisions/0048 ID-12..14).

Passing establishes `BUILT` for this component. It witnesses nothing.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import itertools
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from soveraeign_identity_service.challenges import (  # noqa: E402
    CHALLENGE_EXPIRED, CHALLENGE_SPENT, CHANNEL_REFUSED, CHANNEL_UNDECLARED,
    PRINCIPAL_MISMATCH, PRINCIPAL_REVOKED, TOKEN_UNKNOWN, Challenges, digest_of,
)

T0 = datetime(2026, 8, 23, 12, 0, tzinfo=timezone.utc)
CONSOLE = {"kind": "console-session", "reference": "the session Bdo operates"}
EXTERNAL = {"kind": "external", "reference": "mailto:someone@example.invalid"}


class Clock:
    def __init__(self, start: datetime = T0) -> None:
        self.now = start

    def advance(self, seconds: float) -> None:
        self.now = self.now + timedelta(seconds=seconds)

    def __call__(self) -> datetime:
        return self.now


def principal(pid: str = "principal:bdo", channel: dict | None = CONSOLE,
              revoked: dict | None = None) -> dict:
    return {"principal_id": pid, "verification_channel": channel, "revoked": revoked}


class ChallengeLifecycle(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = Clock()
        tokens = (f"token-{n}" for n in itertools.count(1))
        ids = (f"challenge:{n}" for n in itertools.count(1))
        self.challenges = Challenges(clock=self.clock, tokens=lambda: next(tokens),
                                     ids=lambda: next(ids))

    # -- positive ------------------------------------------------------------

    def test_mint_deliver_present(self) -> None:
        record, token = self.challenges.mint(principal())
        self.assertEqual(record["outcome"], "COMMITTED")
        self.assertIsNotNone(token)
        delivery = self.challenges.deliver(record["challenge_id"])
        self.assertEqual(delivery["outcome"], "COMMITTED")
        self.assertEqual(delivery["effect_class"], "RECORD_LOCAL")
        presented = self.challenges.present(token, principal())
        self.assertEqual(presented["outcome"], "COMMITTED")
        self.assertEqual(presented["verifies"], "principal:bdo")
        self.assertEqual(self.challenges.verification_basis(record["challenge_id"]),
                         "urn:soveraeign:challenge:challenge:1")

    def test_presentable_at_the_last_moment(self) -> None:
        record, token = self.challenges.mint(principal(), ttl_seconds=600)
        self.clock.advance(600)
        self.assertEqual(self.challenges.present(token, principal())["outcome"], "COMMITTED")
        del record

    # -- defeating -----------------------------------------------------------

    def test_a_microsecond_past_expiry_is_refused(self) -> None:
        """Regression: expiry compared ISO stamps as strings.

        A whole-second expiry renders as `...12:10:00Z` and a moment just past it
        as `...12:10:00.000001Z`. Lexically `.` sorts below `Z`, so the later
        moment compared as *earlier* and an expired token was still spendable.
        Expiry compares moments, so the window closes when it says it closes.
        """
        _, token = self.challenges.mint(principal(), ttl_seconds=600)
        self.clock.advance(600.000001)
        presented = self.challenges.present(token, principal())
        self.assertEqual(presented["reason_code"], CHALLENGE_EXPIRED, presented)

    def test_replay_is_refused(self) -> None:
        _, token = self.challenges.mint(principal())
        self.assertEqual(self.challenges.present(token, principal())["outcome"], "COMMITTED")
        replay = self.challenges.present(token, principal())
        self.assertEqual(replay["outcome"], "REFUSED")
        self.assertEqual(replay["reason_code"], CHALLENGE_SPENT)

    def test_expired_token_is_refused(self) -> None:
        _, token = self.challenges.mint(principal(), ttl_seconds=600)
        self.clock.advance(601)
        expired = self.challenges.present(token, principal())
        self.assertEqual(expired["reason_code"], CHALLENGE_EXPIRED)

    def test_expired_token_cannot_be_revived(self) -> None:
        _, token = self.challenges.mint(principal(), ttl_seconds=600)
        self.clock.advance(601)
        self.challenges.present(token, principal())
        self.clock.now = T0
        again = self.challenges.present(token, principal())
        self.assertEqual(again["reason_code"], CHALLENGE_SPENT)

    def test_stolen_token_is_refused(self) -> None:
        _, token = self.challenges.mint(principal("principal:bdo"))
        stolen = self.challenges.present(token, principal("principal:someone-else"))
        self.assertEqual(stolen["reason_code"], PRINCIPAL_MISMATCH)
        self.assertEqual(stolen["presented_by"], "principal:someone-else")

    def test_stolen_token_is_burned_not_left_live(self) -> None:
        _, token = self.challenges.mint(principal("principal:bdo"))
        self.challenges.present(token, principal("principal:someone-else"))
        owner = self.challenges.present(token, principal("principal:bdo"))
        self.assertEqual(owner["reason_code"], CHALLENGE_SPENT)

    def test_unknown_token_is_refused(self) -> None:
        refused = self.challenges.present("never-minted", principal())
        self.assertEqual(refused["reason_code"], TOKEN_UNKNOWN)
        self.assertIsNone(refused["challenge_id"])

    def test_external_channel_is_refused_in_phase_i(self) -> None:
        record, token = self.challenges.mint(principal(channel=EXTERNAL))
        self.assertEqual(record["reason_code"], CHANNEL_REFUSED)
        self.assertIsNone(token)

    def test_undeclared_channel_is_refused(self) -> None:
        record, token = self.challenges.mint(principal(channel=None))
        self.assertEqual(record["reason_code"], CHANNEL_UNDECLARED)
        self.assertIsNone(token)

    def test_revoked_principal_cannot_mint(self) -> None:
        revoked = {"revoked_at": "2026-08-23T00:00:00Z", "revoked_by": "principal:bdo",
                   "reason": "rotated"}
        record, token = self.challenges.mint(principal(revoked=revoked))
        self.assertEqual(record["reason_code"], PRINCIPAL_REVOKED)
        self.assertIsNone(token)

    def test_revocation_after_mint_refuses_presentation(self) -> None:
        _, token = self.challenges.mint(principal())
        revoked = {"revoked_at": "2026-08-23T12:05:00Z", "revoked_by": "principal:bdo",
                   "reason": "channel compromised"}
        presented = self.challenges.present(token, principal(revoked=revoked))
        self.assertEqual(presented["reason_code"], PRINCIPAL_REVOKED)

    def test_deliver_of_unknown_challenge_is_refused(self) -> None:
        self.assertEqual(self.challenges.deliver("challenge:ghost")["reason_code"],
                         TOKEN_UNKNOWN)

    def test_unpresented_challenge_has_no_verification_basis(self) -> None:
        record, _ = self.challenges.mint(principal())
        self.assertIsNone(self.challenges.verification_basis(record["challenge_id"]))
        self.assertIsNone(self.challenges.verification_basis("challenge:ghost"))

    # -- the secret never enters the record ----------------------------------

    def test_no_record_ever_carries_a_token(self) -> None:
        record, token = self.challenges.mint(principal())
        self.challenges.deliver(record["challenge_id"])
        self.challenges.present(token, principal())
        self.challenges.present("never-minted", principal())
        rendered = repr(self.challenges.records)
        self.assertNotIn(token, rendered)
        self.assertNotIn("never-minted", rendered)
        self.assertIn(digest_of(token), rendered)
        held = self.challenges.challenge(record["challenge_id"])
        self.assertNotIn(token, repr(held.to_dict()))


if __name__ == "__main__":
    unittest.main()
