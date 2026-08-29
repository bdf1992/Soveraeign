"""Tests for the landing ledger: what accumulates, and what it must never do.

The defect this module exists against is not a crash. It is that a landing ran
`verify`, ran `lint`, graded an independent observation, printed all three, and
kept none of them. So the cases that matter most here are the accumulation cases
and one refusal case that must never fire: a ledger failure may not stop a merge
the grant already permitted.
"""

from __future__ import annotations

from pathlib import Path
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovland import ledger  # noqa: E402


def _request(**overrides):
    """A landing request shaped the way `sov_land.build_request` assembles one."""
    request = {
        "request_schema": "soveraeign-authority-request/v1",
        "actor_id": "sov",
        "capability": "repository.land",
        "effect_class": "RESOURCE_CONSUMPTION",
        "branch": "main",
        "paths": ["scripts/sovland/ledger.py"],
        "spend": {"unit": "agent_invocations", "amount": 3},
        "evidence": {
            "checks": {"lint": "PASS", "verify": "PASS"},
            "observation": {
                "observation_id": "obs-1",
                "observer_id": "witness:other-session",
                "verdict": "CONFIRMED",
                "contributed_to_build": False,
                "body": "a long narrative the ledger must not copy",
            },
        },
    }
    request.update(overrides)
    return request


def _result(verdict="PERMITTED", code=None, detail="grant covers every path"):
    return {"verdict": verdict, "grant_id": "grant:standing-landing-loop",
            "code": code, "detail": detail}


def _reading(covered, total=44):
    """One ledger entry carrying a declared-coverage reading, for movement tests."""
    return {"outcome": ledger.LANDED, "spend": {"amount": 1},
            "goal": {"reading": "DECLARED_FIXTURE_COVERAGE",
                     "predicates_covered": covered, "predicates_total": total,
                     "closed": False, "open_predicates": []}}


class RecordShape(unittest.TestCase):
    """What one landing puts in the ledger."""

    def test_a_permitted_landing_records_its_checks_and_observation(self):
        """The positive case: the three readings a landing takes are all kept."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            line = ledger.record(root, _request(), _result(), "feat/x", ledger.LANDED,
                                 merge_commit="abc123")
            self.assertIn("recorded", line)
            entries = ledger.load(root)
            self.assertEqual(len(entries), 1)
            entry = entries[0]
            self.assertEqual(entry["outcome"], ledger.LANDED)
            self.assertEqual(entry["checks"], {"lint": "PASS", "verify": "PASS"})
            self.assertEqual(entry["observation"]["observer_id"], "witness:other-session")
            self.assertEqual(entry["observation"]["verdict"], "CONFIRMED")
            self.assertIs(entry["observation"]["contributed_to_build"], False)
            self.assertEqual(entry["merge_commit"], "abc123")
            self.assertEqual(entry["spend"], {"unit": "agent_invocations", "amount": 3})

    def test_the_ledger_keeps_the_observation_address_not_its_body(self):
        """Context hygiene: the ledger records where evidence is, never a second copy."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger.record(root, _request(), _result(), "feat/x", ledger.LANDED)
            entry = ledger.load(root)[0]
            self.assertNotIn("body", entry["observation"])
            self.assertNotIn("a long narrative", json.dumps(entry))

    def test_a_refused_landing_is_recorded_too(self):
        """A refusal is evidence. Recording only successes is how a ledger flatters."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger.record(root, _request(),
                          _result("REFUSED", "SCOPE_EXCLUDED", "STATUS.yaml is excluded"),
                          "feat/x", ledger.REFUSED_AUTHORITY)
            entry = ledger.load(root)[0]
            self.assertEqual(entry["outcome"], ledger.REFUSED_AUTHORITY)
            self.assertEqual(entry["refusal_code"], "SCOPE_EXCLUDED")
            self.assertIsNone(entry["merge_commit"])

    def test_a_landing_with_no_observation_records_that_it_had_none(self):
        """Absent evidence is recorded as absent, never omitted into looking present."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request = _request()
            request["evidence"]["observation"] = None
            ledger.record(root, request, _result(), "feat/x", ledger.LANDED)
            self.assertIsNone(ledger.load(root)[0]["observation"])

    def test_landings_accumulate_rather_than_overwrite(self):
        """The whole point: the second landing does not replace the first."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for _ in range(3):
                ledger.record(root, _request(), _result(), "feat/x", ledger.LANDED)
            self.assertEqual(len(ledger.load(root)), 3)

    def test_the_coverage_reading_is_labelled_as_declarations_not_evidence(self):
        """`predicates_covered` counts declared fixtures. Naming it evidence would
        repeat the confusion this module exists to correct."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger.record(root, _request(), _result(), "feat/x", ledger.LANDED)
            goal = ledger.load(root)[0]["goal"]
            self.assertIn(goal["reading"], ("DECLARED_FIXTURE_COVERAGE", "UNREAD"))


class NeverRefuses(unittest.TestCase):
    """The discipline taken from `sovland/attest.py`: accounting holds no veto."""

    def test_an_unwritable_ledger_does_not_raise(self):
        """The defeating case. If this ever raises, a bookkeeping fault can abort a
        merge the grant permitted, and the ledger has become a second authority."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # A file where the ledger's directory must go, so mkdir cannot succeed.
            (root / ".local").mkdir()
            (root / ".local" / "landing").write_text("not a directory", encoding="utf-8")
            line = ledger.record(root, _request(), _result(), "feat/x", ledger.LANDED)
            self.assertIn("not recorded", line)

    def test_a_malformed_request_does_not_raise(self):
        """A request missing everything still returns a line rather than exploding."""
        line = ledger.record(Path(tempfile.gettempdir()), {}, {}, "feat/x", ledger.LANDED,
                             dry=True)
        self.assertIn("landing ledger:", line)

    def test_dry_writes_nothing(self):
        """`plan` promises to change nothing, and the ledger must keep that promise."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            line = ledger.record(root, _request(), _result(), "feat/x", ledger.LANDED,
                                 dry=True)
            self.assertIn("would record", line)
            self.assertFalse(ledger.ledger_path(root).exists())
            self.assertEqual(ledger.load(root), [])

    def test_a_malformed_ledger_line_is_skipped_not_fatal(self):
        """A half-written line from a killed process must not blind every later read."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger.record(root, _request(), _result(), "feat/x", ledger.LANDED)
            with ledger.ledger_path(root).open("a", encoding="utf-8") as handle:
                handle.write('{"truncated": \n')
            self.assertEqual(len(ledger.load(root)), 1)


class Movement(unittest.TestCase):
    """The reading the controller acts on: did the goal move, and at what spend."""

    def test_no_movement_across_many_landings_is_named(self):
        """The 187-commit case. Production without goal movement must be visible."""
        report = ledger.movement([_reading(36) for _ in range(12)])
        self.assertEqual(report["state"], "NO_GOAL_DELTA")
        self.assertEqual(report["landings_since_movement"], 12)
        self.assertEqual(report["spend_since_movement"], 12)
        self.assertFalse(report["ever_moved"])

    def test_a_predicate_moving_is_named_as_movement(self):
        report = ledger.movement([_reading(36), _reading(36), _reading(37)])
        self.assertEqual(report["state"], "MOVED")
        self.assertEqual(report["predicates_covered"], 37)
        self.assertTrue(report["ever_moved"])

    def test_movement_then_stall_reports_the_stall(self):
        """Having moved once does not excuse the tranche that followed it."""
        entries = [_reading(36), _reading(37)] + [_reading(37) for _ in range(5)]
        report = ledger.movement(entries)
        self.assertEqual(report["state"], "NO_GOAL_DELTA")
        self.assertTrue(report["ever_moved"])
        self.assertGreaterEqual(report["landings_since_movement"], 5)

    def test_an_empty_ledger_reports_no_reading_rather_than_zero(self):
        """Nothing recorded is not the same claim as nothing moved."""
        self.assertEqual(ledger.movement([])["state"], "NO_READING")

    def test_movement_reports_and_refuses_nothing(self):
        """Whether a stall may refuse a landing is Bdo's ruling and a decision record.
        This module makes the stall visible and stops there."""
        report = ledger.movement([_reading(36) for _ in range(50)])
        self.assertNotIn("verdict", report)
        self.assertNotIn("refused", json.dumps(report).lower())


if __name__ == "__main__":
    unittest.main()
