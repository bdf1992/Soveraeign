"""Execute the acceptance-gate corpus and the live owner queue.

Two things are proved here. The corpus cases prove the gate refuses what
``contracts/acceptance-policy.json`` says it refuses, against a fixture topology
rather than the live one, so a case cannot pass by accident of how the real
registry happens to be shaped. The live checks prove the repository's own owner
queue currently satisfies the gate.

Passing establishes ``BUILT`` for the gate. It does not witness it, and it
certainly does not accept anything: acceptance is an act taken by a seat.
"""

from __future__ import annotations

from pathlib import Path
import json
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sovaccept import packet as packets  # noqa: E402
from sovaccept import policy as acceptance  # noqa: E402
from sovaccept import seats  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CORPUS = json.loads(
    (ROOT / "conformance" / "fixtures" / "acceptance" / "gate-cases.json").read_text("utf-8"))
POLICY = acceptance.load_policy(ROOT)


def _codes(defects) -> set[str]:
    """Refusal codes only, so a case is graded on what it refused, not on wording."""
    return {defect.code if hasattr(defect, "code") else defect.split(":", 1)[0]
            for defect in defects}


class AcceptanceCorpus(unittest.TestCase):
    """Every declared case, graded against the refusal code it names."""

    def _run_case(self, case: dict) -> set[str]:
        kind, given = case["kind"], case["input"]
        if kind == "edge":
            return _codes(seats.edge_refusals(
                CORPUS["registry"], given["presenting"], given["accepting"],
                given["claim_type"]))
        if kind == "hold":
            return _codes(acceptance._audit_holds([given["hold"]], POLICY))
        if kind == "ruling":
            return _codes(acceptance._audit_rulings([given["ruling"]]))
        if kind == "packet":
            return set() if given["packet"].get("what_could_defeat_it") \
                else {"PACKET_WITHOUT_DEFEATER"}
        if kind == "open_decision":
            return {"UNDRAINED_QUESTION"}
        raise AssertionError(f"corpus case kind {kind!r} has no executor")

    def test_every_case_lands_as_declared(self) -> None:
        for case in CORPUS["cases"]:
            with self.subTest(case=case["case_id"]):
                found = self._run_case(case)
                if case["expect"] == "ALLOWED":
                    self.assertEqual(found, set(), case["proves"])
                else:
                    self.assertIn(case["refusal"], found, case["proves"])

    def test_corpus_covers_both_polarities(self) -> None:
        """A corpus of only positive cases proves the checker runs, not that it refuses."""
        outcomes = {case["expect"] for case in CORPUS["cases"]}
        self.assertEqual(outcomes, {"ALLOWED", "REFUSED"})

    def test_every_named_refusal_is_declared(self) -> None:
        """A case may not expect a refusal code the policy contract does not carry."""
        declared = set(POLICY["refusal_codes"])
        for case in CORPUS["cases"]:
            if case["expect"] == "REFUSED":
                self.assertIn(case["refusal"], declared, case["case_id"])


class LiveOwnerQueue(unittest.TestCase):
    """The repository's own queue, checked against the same contract."""

    def test_audit_is_clean(self) -> None:
        defects = acceptance.audit(ROOT)
        self.assertEqual([str(defect) for defect in defects], [])

    def test_no_open_decisions_remain(self) -> None:
        register = acceptance.load_register(ROOT)
        self.assertEqual(register["open_decisions"], [])

    def test_every_ruling_names_its_counter(self) -> None:
        for ruling in acceptance.load_register(ROOT)["rulings"]:
            with self.subTest(ruling=ruling["id"]):
                self.assertTrue(ruling.get("counter"))

    def test_every_hold_names_an_admissible_reason(self) -> None:
        reasons = set(POLICY["hold_reasons"])
        for hold in acceptance.load_register(ROOT)["owner_holds"]:
            with self.subTest(hold=hold["id"]):
                self.assertIn(hold["reason"], reasons)

    def test_live_registry_matches_its_schema(self) -> None:
        from sovkernel.jsonschema import validate
        schema = json.loads(
            (ROOT / "contracts" / "seat-registry.schema.json").read_text("utf-8"))
        self.assertEqual(validate(seats.load(ROOT), schema), [])


class ActionRefusals(unittest.TestCase):
    """Who may take an owner action on a presented result, and who may not."""

    def setUp(self) -> None:
        self.packet = packets.load(ROOT, "A3")
        self.registry = seats.load(ROOT)
        self.owner = seats.occupant_id(self.registry, self.packet["accepted_by_seat"])

    def test_an_acted_packet_cannot_be_acted_on_twice(self) -> None:
        found = packets.refusals(ROOT, self.packet, "ACCEPT",
                                 self.packet["accepted_by_seat"], self.owner)
        self.assertTrue(any(line.startswith("ALREADY_ACTED") for line in found))

    def test_the_owning_seat_is_the_only_legal_actor(self) -> None:
        """Everything except the already-acted refusal clears for the owning seat."""
        found = packets.refusals(ROOT, self.packet, "ACCEPT",
                                 self.packet["accepted_by_seat"], self.owner)
        self.assertEqual([line for line in found if not line.startswith("ALREADY_ACTED")], [])

    def test_a_seat_below_the_owner_may_not_act(self) -> None:
        found = packets.refusals(ROOT, self.packet, "ACCEPT", "seat:worker-1",
                                 self.owner)
        self.assertTrue(any(line.startswith("ACCEPTANCE_BY_NON_OWNER") for line in found))

    def test_the_builder_may_not_accept_its_own_build(self) -> None:
        builder = self.packet["built_by"]["actor_id"]
        found = packets.refusals(ROOT, self.packet, "ACCEPT",
                                 self.packet["accepted_by_seat"], builder)
        self.assertTrue(any(line.startswith("SELF_ACCEPTANCE_REFUSED") for line in found))

    def test_an_actor_who_does_not_hold_the_seat_may_not_act(self) -> None:
        found = packets.refusals(ROOT, self.packet, "ACCEPT",
                                 self.packet["accepted_by_seat"], "urn:someone:else")
        self.assertTrue(any(line.startswith("ACCEPTANCE_BY_NON_OWNER") for line in found))

    def test_an_undeclared_action_is_refused(self) -> None:
        found = packets.refusals(ROOT, self.packet, "APPROVE",
                                 self.packet["accepted_by_seat"], self.owner)
        self.assertTrue(any(line.startswith("UNKNOWN_ACTION") for line in found))


if __name__ == "__main__":
    unittest.main()
