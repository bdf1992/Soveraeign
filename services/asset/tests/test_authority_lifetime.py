"""Positive and defeating cases for grant lifetime, sessions, and attenuation.

`AGENTS.md` (Authority) requires a typed, scoped, *live* grant at every
consequential boundary, and forbids a participant acquiring authority merely by
operating successfully. Before these cases the `grants` table had no expiry and
the only disqualifier was `revoked`, so any grant ever issued was a permanent
credential - the exact thing the rule forbids.

These establish BUILT evidence only. They do not witness or ratify anything.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from soveraeign_asset_service import AssetService, AuthorityRefused


class Clock:
    """A hand-advanced clock, so expiry is proven rather than waited for."""

    def __init__(self, start: float = 1_000_000.0) -> None:
        self.value = start

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


class GrantLifetime(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.clock = Clock()
        self.service = AssetService(self.root / "state", clock=self.clock)

    def tearDown(self):
        self.service.close()
        self.tmp.cleanup()

    def test_a_live_grant_authorizes(self):
        self.service.grant("Bdo", "Bdo", "ratify:judgement", ttl_seconds=900)
        self.assertTrue(self.service._authorized("Bdo", "ratify:judgement", "any-scope"))

    def test_an_expired_grant_stops_authorizing(self):
        """The defeating case: time alone withdraws authority, with no revocation."""
        self.service.grant("Bdo", "Bdo", "ratify:judgement", ttl_seconds=900)
        self.clock.advance(901)
        self.assertFalse(self.service._authorized("Bdo", "ratify:judgement", "any-scope"))

    def test_an_expired_grant_refuses_the_transition_with_a_receipt(self):
        source = self.root / "hero.txt"
        source.write_bytes(b"ORIGINAL\n")
        self.service.grant("Bdo", "Bdo", "ratify:judgement", ttl_seconds=900)
        asset = self.service.ingest(source, "Hero", "Bdo")
        proposal = self.service.propose(asset["asset_id"], "Bdo", {"description": "a hero"})
        self.clock.advance(901)
        with self.assertRaises(AuthorityRefused):
            self.service.ratify(proposal, "Bdo")
        refusals = [r for r in self.service.receipts()
                    if r["outcome"] == "REFUSED" and r["event"] == "authority.check"]
        self.assertEqual(len(refusals), 1)

    def test_revocation_still_works_before_expiry(self):
        grant = self.service.grant("Bdo", "Bdo", "retract:record", ttl_seconds=900)
        self.assertTrue(self.service._authorized("Bdo", "retract:record", "x"))
        self.service.revoke(grant, "Bdo")
        self.assertFalse(self.service._authorized("Bdo", "retract:record", "x"))


class SessionBinding(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.clock = Clock()
        self.service = AssetService(Path(self.tmp.name) / "state", clock=self.clock)
        self.service.grant("Bdo", "Bdo", "ratify:judgement", ttl_seconds=3600)

    def tearDown(self):
        self.service.close()
        self.tmp.cleanup()

    def test_a_session_bound_grant_dies_with_its_session(self):
        """The defeating case: closing the session withdraws authority immediately."""
        session = self.service.open_session("claude", "claude-opus-5", ttl_seconds=3600)
        self.service.grant("Bdo", "claude", "ratify:judgement", ttl_seconds=900,
                           session_id=session)
        self.assertTrue(self.service._authorized("claude", "ratify:judgement", "x"))
        self.service.close_session(session, "Bdo")
        self.assertFalse(self.service._authorized("claude", "ratify:judgement", "x"))

    def test_a_grant_never_outlives_its_session(self):
        session = self.service.open_session("claude", "claude-opus-5", ttl_seconds=60)
        self.service.grant("Bdo", "claude", "ratify:judgement", ttl_seconds=9000,
                           session_id=session)
        self.clock.advance(61)
        self.assertFalse(self.service._authorized("claude", "ratify:judgement", "x"))

    def test_an_expired_session_cannot_carry_a_new_grant(self):
        session = self.service.open_session("claude", "claude-opus-5", ttl_seconds=60)
        self.clock.advance(61)
        with self.assertRaises(AuthorityRefused):
            self.service.grant("Bdo", "claude", "ratify:judgement", session_id=session)


class Attenuation(unittest.TestCase):
    """A delegated grant may narrow what its issuer holds. It may never widen it."""

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.clock = Clock()
        self.service = AssetService(Path(self.tmp.name) / "state", clock=self.clock)
        # The first issuer against an empty store is recorded as the root.
        self.service.grant("Bdo", "claude", "ratify:judgement", scope="asset_1",
                           ttl_seconds=900)

    def tearDown(self):
        self.service.close()
        self.tmp.cleanup()

    def test_the_first_issuer_is_recorded_as_the_root(self):
        self.assertEqual(self.service.authority.root_issuer(), "Bdo")

    def test_a_holder_may_pass_on_what_it_holds(self):
        self.service.grant("claude", "worker", "ratify:judgement", scope="asset_1",
                           ttl_seconds=300)
        self.assertTrue(self.service._authorized("worker", "ratify:judgement", "asset_1"))

    def test_an_issuer_cannot_grant_a_capability_it_does_not_hold(self):
        """The defeating case: no covering grant means no issue."""
        with self.assertRaises(AuthorityRefused):
            self.service.grant("claude", "worker", "retract:record", scope="asset_1")

    def test_an_issuer_cannot_widen_scope(self):
        with self.assertRaises(AuthorityRefused):
            self.service.grant("claude", "worker", "ratify:judgement", scope="*")

    def test_an_issuer_cannot_grant_past_its_own_expiry(self):
        with self.assertRaises(AuthorityRefused):
            self.service.grant("claude", "worker", "ratify:judgement", scope="asset_1",
                               ttl_seconds=9000)

    def test_a_refused_issue_is_recorded(self):
        with self.assertRaises(AuthorityRefused):
            self.service.grant("claude", "worker", "retract:record", scope="asset_1")
        refusals = [r for r in self.service.receipts()
                    if r["outcome"] == "REFUSED" and r["event"] == "authority.grant"]
        self.assertEqual(len(refusals), 1)


class LegacyStoreMigration(unittest.TestCase):
    """A store written before grants expired must not keep honouring them."""

    def test_a_grant_row_with_no_expiry_reads_as_expired(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "state"
            root.mkdir(parents=True)
            db = sqlite3.connect(root / "asset-service.sqlite3")
            db.executescript(
                "CREATE TABLE grants("
                "  id TEXT PRIMARY KEY, actor TEXT NOT NULL, capability TEXT NOT NULL,"
                "  scope TEXT NOT NULL, revoked INTEGER NOT NULL DEFAULT 0,"
                "  created_at REAL NOT NULL);"
            )
            db.execute("INSERT INTO grants VALUES('grant_legacy','Bdo','ratify:judgement',"
                       "'*',0,1.0)")
            db.commit()
            db.close()

            service = AssetService(root)
            try:
                self.assertFalse(service._authorized("Bdo", "ratify:judgement", "x"))
            finally:
                service.close()


if __name__ == "__main__":
    unittest.main()
