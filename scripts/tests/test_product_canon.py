"""Prove the product canon's joins resolve, and refuse the ways they could stop resolving.

The canon's whole value is that `PROMISE -> JOURNEY -> capability` can be checked rather
than asserted. A canon that named a capability no service declares, or a promise no
journey reaches, would read as a taxonomy while telling the reader nothing, so each of
those is a declared defeat with a case here.

Passing establishes `BUILT` for the canon record and its checker. It witnesses nothing,
and it is not evidence that any promise is kept: every crossing in it could be reachable
and the node would still only be able to keep the promise, not have kept it.
"""

from __future__ import annotations

from pathlib import Path
import copy
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovkernel import canon as canon_module  # noqa: E402
from sovkernel.jsonschema import validate  # noqa: E402

import sov_canon  # noqa: E402

CANON = json.loads((ROOT / "contracts" / "product-canon.json").read_text("utf-8"))
SCHEMA = json.loads((ROOT / "contracts" / "product-canon.schema.json").read_text("utf-8"))
CAPABILITY_MAP = json.loads(
    (ROOT / "contracts" / "fixtures" / "capability-map.reference.json").read_text("utf-8"))
WORDING = (ROOT / "CANON.md").read_bytes().decode("utf-8")


def _codes(defects: list[str]) -> set[str]:
    return {defect.split(":")[0] for defect in defects}


class CheckedInCanonTest(unittest.TestCase):
    """The positive case: the canon as it stands, against the map as it stands."""

    def test_the_canon_satisfies_its_schema(self) -> None:
        self.assertEqual(validate(CANON, SCHEMA), [])

    def test_every_join_resolves(self) -> None:
        defects = canon_module.defects(CANON, CAPABILITY_MAP)
        self.assertEqual(defects, [], "\n".join(defects))

    def test_every_identifier_is_worded(self) -> None:
        defects = sov_canon.wording_defects(CANON, WORDING)
        self.assertEqual(defects, [], "\n".join(defects))

    def test_owner_is_not_a_participant_role(self) -> None:
        """decisions/0020: Owner is a context over a role, never a role."""
        self.assertNotIn("owner", {p["role"] for p in CANON["participants"]})

    def test_every_phase_i_promise_has_a_journey_or_a_parent(self) -> None:
        served = {promise for journey in CANON["journeys"] for promise in journey["serves"]}
        composed = {part for promise in CANON["promises"]
                    for part in promise.get("composes", [])}
        for promise in CANON["promises"]:
            with self.subTest(promise=promise["promise_id"]):
                self.assertTrue(promise["promise_id"] in served | composed)


class ReadingTest(unittest.TestCase):
    """What the trace measures, and what it must not claim."""

    def test_a_journey_reading_counts_every_crossing_once(self) -> None:
        for journey in CANON["journeys"]:
            reading = canon_module.journey_reading(journey, CAPABILITY_MAP)
            with self.subTest(journey=journey["journey_id"]):
                self.assertEqual(sum(reading["counts"].values()), len(reading["crossings"]))
                self.assertEqual(
                    len(reading["crossings"]),
                    len(journey["capabilities"]) + len(journey["missing_capabilities"]))

    def test_a_missing_crossing_is_never_counted_as_reachable(self) -> None:
        for journey in CANON["journeys"]:
            for state in canon_module.crossing_states(journey, CAPABILITY_MAP):
                if state["state"] == canon_module.MISSING:
                    with self.subTest(crossing=state["crossing"]):
                        self.assertNotIn("transports", state)
                        self.assertIn("because", state)

    def test_a_journey_is_walkable_only_when_nothing_is_declared_or_missing(self) -> None:
        for journey in CANON["journeys"]:
            reading = canon_module.journey_reading(journey, CAPABILITY_MAP)
            with self.subTest(journey=journey["journey_id"]):
                if reading["walkable"]:
                    self.assertEqual(reading["counts"][canon_module.DECLARED], 0)
                    self.assertEqual(reading["counts"][canon_module.MISSING], 0)

    def test_a_compound_promise_answers_for_its_parts(self) -> None:
        """PROMISE-01 is reachable when what it composes is, not on its own journeys."""
        reading = canon_module.promise_reading(CANON, CAPABILITY_MAP, "PROMISE-01")
        direct = {journey["journey_id"] for journey in CANON["journeys"]
                  if "PROMISE-01" in journey["serves"]}
        self.assertGreater(len(reading["journeys"]), len(direct))

    def test_a_promise_counts_each_crossing_once(self) -> None:
        """Two journeys serving one promise routinely cross the same operation.

        Summing their counts would report a promise as needing more of the node than it
        does - the same double-counting that makes summing resource views wrong.
        """
        for promise in CANON["promises"]:
            reading = canon_module.promise_reading(
                CANON, CAPABILITY_MAP, promise["promise_id"])
            with self.subTest(promise=promise["promise_id"]):
                self.assertEqual(sum(reading["totals"].values()),
                                 reading["distinct_crossings"])
                self.assertGreaterEqual(reading["journey_appearances"],
                                        reading["distinct_crossings"])

    def test_at_least_one_promise_actually_shares_a_crossing(self) -> None:
        """Otherwise the case above would be proving nothing about this canon."""
        shared = [p["promise_id"] for p in CANON["promises"]
                  if (r := canon_module.promise_reading(CANON, CAPABILITY_MAP,
                                                        p["promise_id"]))
                  and r["journey_appearances"] > r["distinct_crossings"]]
        self.assertTrue(shared, "no promise shares a crossing between its journeys")


class DefectTest(unittest.TestCase):
    """Each declared defeat, driven through the judgement."""

    def _mutated(self) -> dict:
        return copy.deepcopy(CANON)

    def test_a_capability_no_manifest_declares_is_refused(self) -> None:
        canon = self._mutated()
        canon["journeys"][0]["capabilities"].append("asset.teleport")
        self.assertIn("UNDECLARED_CAPABILITY",
                      _codes(canon_module.defects(canon, CAPABILITY_MAP)))

    def test_a_journey_serving_an_undeclared_promise_is_refused(self) -> None:
        canon = self._mutated()
        canon["journeys"][0]["serves"].append("PROMISE-99")
        self.assertIn("UNKNOWN_PROMISE", _codes(canon_module.defects(canon, CAPABILITY_MAP)))

    def test_a_journey_walked_by_an_undeclared_participant_is_refused(self) -> None:
        canon = self._mutated()
        canon["journeys"][0]["participant"] = "nobody"
        self.assertIn("UNKNOWN_PARTICIPANT",
                      _codes(canon_module.defects(canon, CAPABILITY_MAP)))

    def test_a_promise_no_journey_reaches_is_refused(self) -> None:
        """A promise nothing realizes is a claim, and the canon must not carry one."""
        canon = self._mutated()
        canon["promises"].append({
            "promise_id": "PROMISE-99",
            "statement": "Something the node undertakes and nothing here ever reaches.",
            "phase": "PHASE_I", "source": "STRONGLY_DERIVED",
            "derives_from": ["GROUND-001"], "grounded_in": ["CANON.md"],
        })
        self.assertIn("UNREALIZED_PROMISE",
                      _codes(canon_module.defects(canon, CAPABILITY_MAP)))

    def test_recording_a_declared_capability_as_missing_is_refused(self) -> None:
        """The missing column must not be used to hide something that exists."""
        canon = self._mutated()
        canon["journeys"][0]["missing_capabilities"].append(
            {"name": "asset.ingest-asset", "because": "x" * 30})
        self.assertIn("MISSING_BUT_DECLARED",
                      _codes(canon_module.defects(canon, CAPABILITY_MAP)))

    def test_a_promise_composing_itself_is_refused(self) -> None:
        canon = self._mutated()
        canon["promises"][0]["composes"].append("PROMISE-01")
        self.assertIn("SELF_COMPOSING_PROMISE",
                      _codes(canon_module.defects(canon, CAPABILITY_MAP)))

    def test_a_retired_identifier_declared_again_is_refused(self) -> None:
        """Retired, not reserved: an identifier never comes back meaning something else."""
        canon = self._mutated()
        canon["retired"].append({"id": "PROMISE-02", "retired_in": "CANON-2",
                                 "because": "superseded by a narrower wording"})
        self.assertIn("RETIRED_IDENTIFIER_REUSED",
                      _codes(canon_module.defects(canon, CAPABILITY_MAP)))

    def test_a_promise_absent_from_the_wording_is_refused(self) -> None:
        canon = self._mutated()
        canon["promises"].append({
            "promise_id": "PROMISE-98",
            "statement": "A promise that exists in the record and in no document.",
            "phase": "PHASE_I", "source": "STRONGLY_DERIVED",
            "derives_from": ["GROUND-001"], "grounded_in": ["CANON.md"],
        })
        self.assertIn("UNWORDED_PROMISE", _codes(sov_canon.wording_defects(canon, WORDING)))

    def test_a_revision_absent_from_the_wording_is_refused(self) -> None:
        canon = self._mutated()
        canon["revision"] = "CANON-7"
        self.assertIn("UNWORDED_REVISION", _codes(sov_canon.wording_defects(canon, WORDING)))

    def test_a_retirement_the_wording_does_not_record_is_refused(self) -> None:
        """A reader following an old attribution has to be able to find out."""
        canon = self._mutated()
        canon["retired"].append({"id": "PROMISE-97", "retired_in": "CANON-2",
                                 "because": "withdrawn without ever being written down"})
        self.assertIn("UNWORDED_RETIREMENT",
                      _codes(sov_canon.wording_defects(canon, WORDING)))


class RetirementTest(unittest.TestCase):
    """PROMISE-13 was retired in CANON-2 and must stay answerable."""

    def test_the_retired_promise_is_gone_from_the_canon(self) -> None:
        self.assertNotIn("PROMISE-13", {p["promise_id"] for p in CANON["promises"]})

    def test_the_retired_promise_is_recorded_with_a_reason(self) -> None:
        entry = next(e for e in CANON["retired"] if e["id"] == "PROMISE-13")
        self.assertEqual(entry["retired_in"], "CANON-2")
        self.assertIn("PROMISE-16", entry["because"])

    def test_the_identifier_is_never_reused(self) -> None:
        """Retired, not reserved. Work attributed to PROMISE-13 keeps meaning proofing."""
        canon = copy.deepcopy(CANON)
        canon["promises"].append({
            "promise_id": "PROMISE-13",
            "statement": "Some later promise that quietly took over a retired identifier.",
            "phase": "PHASE_I", "source": "STRONGLY_DERIVED",
            "derives_from": ["GROUND-001"], "grounded_in": ["CANON.md"],
        })
        self.assertIn("RETIRED_IDENTIFIER_REUSED",
                      _codes(canon_module.defects(canon, CAPABILITY_MAP)))

    def test_no_journey_still_serves_it(self) -> None:
        served = {p for journey in CANON["journeys"] for p in journey["serves"]}
        self.assertNotIn("PROMISE-13", served)

    def test_the_replacement_carries_the_proofing_journey(self) -> None:
        journey = next(j for j in CANON["journeys"] if j["journey_id"] == "JOURNEY-11")
        self.assertIn("PROMISE-16", journey["serves"])

    def test_the_struck_promise_is_gone_and_recorded(self) -> None:
        """PROMISE-14 was struck by Bdo in CANON-3, with no successor."""
        self.assertNotIn("PROMISE-14", {p["promise_id"] for p in CANON["promises"]})
        entry = next(e for e in CANON["retired"] if e["id"] == "PROMISE-14")
        self.assertEqual(entry["retired_in"], "CANON-3")

    def test_the_journey_beneath_the_struck_promise_is_kept(self) -> None:
        """A journey does not need to be eternal product identity to be a real gap."""
        journey = next(j for j in CANON["journeys"] if j["journey_id"] == "JOURNEY-12")
        self.assertNotIn("PROMISE-14", journey["serves"])
        self.assertTrue(journey["serves"])
        self.assertTrue(journey["missing_capabilities"])

    def test_no_promise_carries_owner_confirmation_required(self) -> None:
        """The one that did was struck rather than confirmed."""
        self.assertNotIn("OWNER_CONFIRMATION_REQUIRED",
                         {p["source"] for p in CANON["promises"]})


class SchemaTest(unittest.TestCase):
    """Shapes the schema itself must refuse."""

    def test_a_promise_grounded_in_nothing_is_refused(self) -> None:
        canon = copy.deepcopy(CANON)
        canon["promises"][1]["grounded_in"] = []
        self.assertNotEqual(validate(canon, SCHEMA), [])

    def test_a_participant_with_no_stated_need_is_refused(self) -> None:
        canon = copy.deepcopy(CANON)
        canon["participants"][0]["needs"] = []
        self.assertNotEqual(validate(canon, SCHEMA), [])

    def test_a_missing_capability_with_no_reason_is_refused(self) -> None:
        canon = copy.deepcopy(CANON)
        canon["journeys"][0]["missing_capabilities"][0]["because"] = "short"
        self.assertNotEqual(validate(canon, SCHEMA), [])


class StateFactTest(unittest.TestCase):
    """The shape a fact takes when ground, state and evidence are all addressed."""

    FACTS = json.loads(
        (ROOT / "contracts" / "fixtures" / "state-fact.example.json").read_text("utf-8"))
    SCHEMA = json.loads(
        (ROOT / "contracts" / "state-fact.schema.json").read_text("utf-8"))

    def test_both_examples_satisfy_the_schema(self) -> None:
        for fact in self.FACTS["facts"]:
            with self.subTest(fact=fact["fact_id"]):
                self.assertEqual(validate(fact, self.SCHEMA), [])

    def test_every_identifier_an_example_names_exists(self) -> None:
        """A fact citing a promise nobody declares is a fact nobody can resolve."""
        ground = {c["ground_id"] for c in json.loads(
            (ROOT / "contracts" / "product-ground.json").read_text("utf-8"))["claims"]}
        promises = {p["promise_id"] for p in CANON["promises"]}
        journeys = {j["journey_id"] for j in CANON["journeys"]}
        rows = {row["capability_id"] for row in CAPABILITY_MAP["capabilities"]}
        for fact in self.FACTS["facts"]:
            with self.subTest(fact=fact["fact_id"]):
                self.assertLessEqual(set(fact["ground"]), ground)
                self.assertLessEqual(set(fact.get("promise", [])), promises)
                self.assertLessEqual(set(fact.get("journey", [])), journeys)
                self.assertLessEqual(set(fact.get("capability", [])), rows)

    def test_a_declared_fact_carries_no_observation(self) -> None:
        """State saying so is not evidence. CONTRACT.md C7, made a shape."""
        declared = [f for f in self.FACTS["facts"]
                    if f["evidential_status"] == "DECLARED"]
        self.assertTrue(declared)
        for fact in declared:
            with self.subTest(fact=fact["fact_id"]):
                self.assertEqual(fact.get("observations", []), [])

    def test_a_refuted_fact_says_what_looked(self) -> None:
        refuted = [f for f in self.FACTS["facts"] if f["evidential_status"] == "REFUTED"]
        self.assertTrue(refuted)
        for fact in refuted:
            with self.subTest(fact=fact["fact_id"]):
                self.assertTrue(fact["observations"])

    def test_a_fact_pins_the_state_it_was_read_from(self) -> None:
        """Without state inputs a fact can never go stale, because nothing says on what."""
        for fact in self.FACTS["facts"]:
            with self.subTest(fact=fact["fact_id"]):
                self.assertTrue(fact["state_inputs"]["capability_revision"])

    def test_the_examples_carry_both_a_current_and_a_superseded_reading(self) -> None:
        """Two digests in the fixture, so both paths through the reading are exercised."""
        pinned = {f["state_inputs"]["capability_revision"] for f in self.FACTS["facts"]}
        self.assertGreater(len(pinned), 1)

    def test_a_fact_reads_stale_exactly_when_its_pinned_state_moved(self) -> None:
        """Staleness is a comparison, not a stored value."""
        for fact in self.FACTS["facts"]:
            pinned = fact["state_inputs"]["capability_revision"]
            with self.subTest(fact=fact["fact_id"]):
                self.assertFalse(self._stale(fact, pinned))
                self.assertTrue(self._stale(fact, "0" * 64))

    @staticmethod
    def _stale(fact: dict, current: str) -> bool:
        return fact["state_inputs"]["capability_revision"] != current

    def test_staleness_is_computed_and_never_stored(self) -> None:
        """A fact whose state moved is left as it was; the reading changes, not the record.

        FACT-mcp-journal-withheld was recorded REFUTED against capability revision
        3aab7102, before Bdo ruled record.read-entry an operator act. It still says REFUTED
        because that is what was true when it was written.
        """
        current = max({f["state_inputs"]["capability_revision"]
                       for f in self.FACTS["facts"]},
                      key=lambda d: sum(1 for f in self.FACTS["facts"]
                                        if f["state_inputs"]["capability_revision"] == d))
        stale = [f for f in self.FACTS["facts"]
                 if f["state_inputs"]["capability_revision"] != current]
        self.assertTrue(stale, "no fact demonstrates the stale path")
        for fact in stale:
            with self.subTest(fact=fact["fact_id"]):
                self.assertNotEqual(fact["evidential_status"], "STALE")
                self.assertIn("superseded_by", fact)

    def test_a_superseding_fact_keeps_the_same_meaning(self) -> None:
        """Ground, promise and journey do not move when the world does."""
        old = next(f for f in self.FACTS["facts"]
                   if f["fact_id"] == "FACT-mcp-journal-withheld")
        new = next(f for f in self.FACTS["facts"] if f["fact_id"] == old["superseded_by"])
        self.assertEqual(old["ground"], new["ground"])
        self.assertEqual(old["promise"], new["promise"])
        self.assertEqual(old["journey"], new["journey"])
        self.assertNotEqual(old["evidential_status"], new["evidential_status"])

    def test_the_status_field_does_not_borrow_the_word_standing(self) -> None:
        """`standing` already means two lifecycles. A third meaning must not take it."""
        self.assertNotIn("standing", self.SCHEMA["properties"])
        self.assertIn("evidential_status", self.SCHEMA["properties"])


if __name__ == "__main__":
    unittest.main()
