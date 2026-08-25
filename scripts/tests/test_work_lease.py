"""Prove the work-lease evaluator refuses what the fixtures declare it refuses.

Two halves. The first runs the semantic fixtures in
``contracts/fixtures/work-lease.fixtures.json`` - the entries the schema accepts because
the defect lives between two records rather than inside one - and asserts that the check
each entry names actually catches it. The second covers the mechanics the fixtures do not
reach: fencing, expiry, budget arithmetic, and the readings.

A passing run establishes ``BUILT`` for the evaluator. It witnesses nothing.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovkernel import lease_budget  # noqa: E402
from sovkernel import work_lease  # noqa: E402

FIXTURES = ROOT / "contracts" / "fixtures" / "work-lease.fixtures.json"


def _entries() -> list[dict]:
    with FIXTURES.open(encoding="utf-8") as handle:
        return json.load(handle)


def _codes(defects) -> set[str]:
    return {defect.code for defect in defects}


def _lease(**overrides) -> dict:
    """A minimal well-formed lease, so each test states only what it is about."""
    lease = {
        "lease_schema": "soveraeign-work-lease/v1",
        "status": "PROPOSED",
        "lease_id": "lease:subject",
        "concern": {"kind": "ticket", "reference": "#1"},
        "holder": {
            "principal_id": "urn:soveraeign:principal:instance:session-000000",
            "relation": "PARENT",
            "parent_lease": None,
            "controller_principal": "urn:soveraeign:principal:human:bdo",
            "session": "session-000000",
            "definition": {"definition_id": "sov-worker", "definition_kind": "agent",
                           "provenance": "SYSTEM_AUTHORED", "version": "1"},
        },
        "grant": {"grant_id": None, "authority_type": None, "capabilities": [],
                  "effect_ceiling": "RECORD_LOCAL"},
        "budget": {"consumption": [], "emission": []},
        "closure": {"condition": "it lands", "defeating_evidence": "it does not land"},
        "fence": 1,
        "granted_at": "2026-08-24T00:00:00Z",
        "expires_at": "2026-08-24T02:00:00Z",
        "state": "HELD",
    }
    lease.update(overrides)
    return lease


class SemanticFixtureTests(unittest.TestCase):
    """Every fixture that declares a refusal must actually be refused for that reason."""

    def test_each_declared_refusal_is_produced(self) -> None:
        declared = [entry for entry in _entries() if "expected_refusal" in entry]
        self.assertTrue(declared, "no semantic fixtures to run")
        for entry in declared:
            with self.subTest(fixture=entry["id"]):
                family = list(entry.get("context", [])) + [entry["record"]]
                verdicts = work_lease.evaluate_set(family)
                subject = entry["record"]["lease_id"]
                self.assertIn(entry["expected_refusal"], _codes(verdicts[subject]),
                              f"{entry['id']} declares {entry['expected_refusal']} and the "
                              f"evaluator found {sorted(_codes(verdicts[subject]))}")

    def test_the_positive_fixtures_carry_no_defect(self) -> None:
        family = [entry["record"] for entry in _entries() if entry["polarity"] == "positive"]
        for lease_id, defects in work_lease.evaluate_set(family).items():
            with self.subTest(lease=lease_id):
                self.assertEqual([], defects, f"{lease_id}: {[d.message for d in defects]}")

    def test_every_declared_refusal_code_is_reachable(self) -> None:
        """A refusal code nothing can emit is a gap in the contract, not a spare part.

        The repository already carries one of those (OPEN-SEAMS.md S17). This test exists
        so this contract does not add a second.
        """
        emitted = set()
        for entry in _entries():
            family = list(entry.get("context", [])) + [entry["record"]]
            for defects in work_lease.evaluate_set(family).values():
                emitted |= _codes(defects)
        emitted |= _codes(EvaluatorTests.mechanical_refusals())
        self.assertEqual(set(work_lease.REFUSALS), emitted,
                         "declared and reachable refusal codes disagree")


class EvaluatorTests(unittest.TestCase):
    """The relations and mechanics the fixture records do not exercise."""

    @staticmethod
    def mechanical_refusals() -> list[work_lease.Defect]:
        """Every defect the cases below produce, so reachability can be totalled."""
        now = datetime(2026, 8, 24, 3, 0, tzinfo=timezone.utc)
        found = work_lease.evaluate(_lease(), now=now)
        found += work_lease.evaluate(
            _lease(grant={"grant_id": "grant:x", "authority_type": "VERIFICATION",
                          "capabilities": [], "effect_ceiling": "EXTERNAL_WORLD"}))
        orphan = _lease(lease_id="lease:orphan")
        orphan["holder"].update({"relation": "HELPER", "parent_lease": "lease:absent"})
        found += work_lease.evaluate(orphan)
        unanchored = _lease(lease_id="lease:unanchored")
        unanchored["holder"].update({"relation": "HELPER", "parent_lease": "lease:p",
                                     "controller_principal": None})
        found += work_lease.evaluate(unanchored)
        found += work_lease.evaluate(_lease(state="COMPLETED"))
        parent = _lease(lease_id="lease:p", state="COMPLETED", closure_evidence={
            "receipt_id": "r", "standing_reached": "WITNESSED",
            "evidence_addresses": ["a"], "witnessed_by": None})
        found += work_lease.evaluate(parent, children=[])
        return found

    def test_a_held_lease_past_its_expiry_is_stale(self) -> None:
        defects = work_lease.evaluate(
            _lease(), now=datetime(2026, 8, 24, 3, 0, tzinfo=timezone.utc))
        self.assertIn("STALE_LEASE", _codes(defects))

    def test_a_held_lease_inside_its_window_is_not(self) -> None:
        defects = work_lease.evaluate(
            _lease(), now=datetime(2026, 8, 24, 1, 0, tzinfo=timezone.utc))
        self.assertEqual([], defects)

    def test_a_newer_fence_supersedes_an_older_one(self) -> None:
        self.assertTrue(work_lease.supersedes(None, 1))
        self.assertTrue(work_lease.supersedes(2, 2))
        self.assertFalse(work_lease.supersedes(3, 2))

    def test_an_effect_ceiling_above_the_phase_is_refused(self) -> None:
        lease = _lease(grant={"grant_id": "grant:x", "authority_type": "VERIFICATION",
                              "capabilities": [], "effect_ceiling": "EXTERNAL_WORLD"})
        self.assertIn("EFFECT_CLASS_REFUSED", _codes(work_lease.evaluate(lease)))
        self.assertEqual([], work_lease.evaluate(lease, phase_ceiling="EXTERNAL_WORLD"))

    def test_a_helper_whose_parent_was_not_supplied_is_refused(self) -> None:
        lease = _lease()
        lease["holder"].update({"relation": "HELPER", "parent_lease": "lease:absent"})
        self.assertIn("HELPER_WITHOUT_PARENT", _codes(work_lease.evaluate(lease)))

    def test_a_recruited_holder_with_no_controller_is_refused(self) -> None:
        lease = _lease()
        lease["holder"].update({"relation": "HELPER", "parent_lease": "lease:p",
                                "controller_principal": None})
        self.assertIn("UNANCHORED_HOLDER", _codes(work_lease.evaluate(lease)))

    def test_a_helper_closing_itself_still_needs_its_parent_supplied(self) -> None:
        """The evaluator judges a record in its context, and a caller must supply it.

        Omitting the parent when a helper closes reads the helper as an orphan and refuses
        the one transition that should be allowed. The command line got this wrong first.
        """
        parent = _lease(lease_id="lease:p")
        helper = _lease(lease_id="lease:h", state="COMPLETED", closure_evidence={
            "receipt_id": "r", "standing_reached": "BUILT",
            "evidence_addresses": ["a"], "witnessed_by": None})
        helper["holder"].update({
            "relation": "HELPER", "parent_lease": "lease:p",
            "principal_id": "urn:soveraeign:principal:instance:session-000000.part"})
        self.assertIn("HELPER_WITHOUT_PARENT", _codes(work_lease.evaluate(helper)))
        self.assertEqual([], work_lease.evaluate(helper, parent=parent))

    def test_closure_without_evidence_is_refused(self) -> None:
        self.assertIn("CLOSURE_WITHOUT_EVIDENCE",
                      _codes(work_lease.evaluate(_lease(state="COMPLETED"))))

    def test_a_witnessed_claim_needs_a_witness_lease_by_another_principal(self) -> None:
        parent = _lease(state="COMPLETED", closure_evidence={
            "receipt_id": "r", "standing_reached": "WITNESSED",
            "evidence_addresses": ["a"], "witnessed_by": None})
        self.assertIn("UNWITNESSED_STANDING_CLAIM",
                      _codes(work_lease.evaluate(parent, children=[])))

        witness = _lease(lease_id="lease:witness")
        witness["holder"].update({
            "relation": "WITNESS", "parent_lease": "lease:subject",
            "principal_id": "urn:soveraeign:principal:instance:session-999999",
            "controller_principal": "urn:soveraeign:principal:human:bdo"})
        witness["state"] = "COMPLETED"
        witness["closure_evidence"] = {"receipt_id": "r2", "standing_reached": "BUILT",
                                       "evidence_addresses": ["obs"], "witnessed_by": None}
        self.assertEqual([], work_lease.evaluate(parent, children=[witness]))


class BudgetTests(unittest.TestCase):
    """Drawing against an envelope, and what the drawing looks like from outside."""

    def _lease_with_budget(self) -> dict:
        return _lease(budget={
            "consumption": [{"dimension": "tokens", "limit": 1000},
                            {"dimension": "turns", "limit": 10}],
            "emission": [{"counter": "pull_requests", "limit": 1}]})

    def _draws(self) -> list[dict]:
        return [
            {"lease_id": "lease:subject", "kind": "consumption",
             "dimension": "tokens", "amount": 900},
            {"lease_id": "lease:subject", "kind": "consumption",
             "dimension": "turns", "amount": 4},
            {"lease_id": "lease:subject", "kind": "emission",
             "counter": "pull_requests", "amount": 1},
            {"lease_id": "lease:other", "kind": "consumption",
             "dimension": "tokens", "amount": 5000},
        ]

    def test_another_leases_draws_are_not_counted(self) -> None:
        accounted = lease_budget.account(self._lease_with_budget(), self._draws())
        self.assertEqual(900, accounted["consumed"]["tokens"])

    def test_remaining_is_reported_per_dimension(self) -> None:
        accounted = lease_budget.account(self._lease_with_budget(), self._draws())
        self.assertEqual({"tokens": 100, "turns": 6, "pull_requests": 0},
                         accounted["remaining"])

    def test_an_overdrawn_dimension_is_named(self) -> None:
        draws = self._draws() + [{"lease_id": "lease:subject", "kind": "consumption",
                                  "dimension": "tokens", "amount": 500}]
        readings = lease_budget.readings(self._lease_with_budget(), draws)
        self.assertIn("BUDGET_EXCEEDED", {reading["code"] for reading in readings})

    def test_an_invented_dimension_is_refused_rather_than_absorbed(self) -> None:
        with self.assertRaises(lease_budget.UnknownDimension):
            lease_budget.account(self._lease_with_budget(), [
                {"lease_id": "lease:subject", "kind": "consumption",
                 "dimension": "context_window", "amount": 1}])

    def test_a_dimension_no_receipt_can_carry_is_reported(self) -> None:
        readings = lease_budget.readings(self._lease_with_budget(), self._draws())
        self.assertIn("UNRECEIPTABLE_USAGE", {reading["code"] for reading in readings})

    def test_an_unbounded_dimension_is_reported_not_refused(self) -> None:
        draws = self._draws() + [{"lease_id": "lease:subject", "kind": "consumption",
                                  "dimension": "usd", "amount": 3}]
        codes = {reading["code"] for reading in lease_budget.readings(
            self._lease_with_budget(), draws)}
        self.assertIn("UNBOUNDED_DIMENSION", codes)
        self.assertNotIn("BUDGET_EXCEEDED", codes)

    def test_pressure_selects_the_worst_dimension_and_never_sums(self) -> None:
        accounted = lease_budget.account(self._lease_with_budget(), self._draws())
        # tokens 900/1000, turns 4/10, pull_requests 1/1. The answer is 1.0, not 2.3.
        self.assertEqual(1.0, lease_budget.pressure(accounted, self._lease_with_budget()))

    def test_coordination_without_closure_is_named(self) -> None:
        readings = lease_budget.readings(self._lease_with_budget(), self._draws())
        self.assertIn("COORDINATION_WITHOUT_CLOSURE",
                      {reading["code"] for reading in readings})

    def test_closure_evidence_silences_that_reading(self) -> None:
        lease = self._lease_with_budget()
        lease["state"] = "COMPLETED"
        lease["closure_evidence"] = {"receipt_id": "r", "standing_reached": "BUILT",
                                     "evidence_addresses": ["a"], "witnessed_by": None}
        self.assertNotIn("COORDINATION_WITHOUT_CLOSURE",
                         {reading["code"] for reading in
                          lease_budget.readings(lease, self._draws())})

    def test_a_quiet_lease_produces_no_reading(self) -> None:
        self.assertEqual([], lease_budget.readings(self._lease_with_budget(), []))


if __name__ == "__main__":
    unittest.main()
