"""Prove the product ground holds, and refuse the ways it could stop holding.

Ground exists to be small, stable, and load-bearing. Three things can quietly ruin that:
a claim nothing carries, a promise reaching for a claim that is not there, and a promise
that is canonical only because someone built it that way. Each is a declared defeat with
a case here.

One rule is deliberately harsher than a check. A promise classified
`IMPLEMENTATION_DERIVED` fails, always. The enum value exists so a participant can write
down honestly where a promise came from while fixing it; carrying one into an accepted
canon is exactly the direction-of-authority error the classification was added to catch.

Passing establishes `BUILT` for the ground record and its checker. It witnesses nothing,
and it is not evidence that any claim here is true of the product: sixteen well-formed
claims about the wrong product would pass every case below.
"""

from __future__ import annotations

from pathlib import Path
import copy
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovkernel import ground as ground_module  # noqa: E402
from sovkernel.jsonschema import validate  # noqa: E402

GROUND = json.loads((ROOT / "contracts" / "product-ground.json").read_text("utf-8"))
SCHEMA = json.loads((ROOT / "contracts" / "product-ground.schema.json").read_text("utf-8"))
CANON = json.loads((ROOT / "contracts" / "product-canon.json").read_text("utf-8"))
WORDING = (ROOT / "GROUND.md").read_bytes().decode("utf-8")


def _codes(defects: list[str]) -> set[str]:
    return {defect.split(":")[0] for defect in defects}


class CheckedInGroundTest(unittest.TestCase):
    """The positive case: the ground as it stands, against the canon as it stands."""

    def test_the_ground_satisfies_its_schema(self) -> None:
        self.assertEqual(validate(GROUND, SCHEMA), [])

    def test_the_ground_is_internally_sound(self) -> None:
        defects = ground_module.ground_defects(GROUND)
        self.assertEqual(defects, [], "\n".join(defects))

    def test_every_join_to_the_canon_resolves(self) -> None:
        defects = ground_module.join_defects(CANON, GROUND)
        self.assertEqual(defects, [], "\n".join(defects))

    def test_every_claim_is_worded(self) -> None:
        defects = ground_module.wording_defects(GROUND, WORDING)
        self.assertEqual(defects, [], "\n".join(defects))

    def test_ground_is_small(self) -> None:
        """Between eight and twenty. More means claims are being minted per feature."""
        self.assertGreaterEqual(len(GROUND["claims"]), 8)
        self.assertLessEqual(len(GROUND["claims"]), 20)

    def test_ground_carries_far_more_than_it_declares(self) -> None:
        """The ratio is the point: a few claims standing under many operations."""
        capability_map = json.loads(
            (ROOT / "contracts" / "fixtures" / "capability-map.reference.json")
            .read_text("utf-8"))
        self.assertGreater(len(capability_map["capabilities"]), len(GROUND["claims"]) * 4)

    def test_no_promise_is_canonical_only_because_it_was_built(self) -> None:
        sources = {promise["source"] for promise in CANON["promises"]}
        self.assertNotIn(ground_module.IMPLEMENTATION_ONLY, sources)


class RenderingTest(unittest.TestCase):
    """Rendering, revision and epoch are three levels and must not be conflated."""

    def test_the_checked_in_rendering_renders_its_own_revision(self) -> None:
        self.assertEqual(ground_module.rendering_defects(GROUND, "GROUND"), [])

    def test_a_rendering_of_another_revision_is_refused(self) -> None:
        """A rendering carries no change of meaning, so it cannot outrun one."""
        ground = copy.deepcopy(GROUND)
        ground["rendering"] = "GROUND-2.0"
        self.assertIn("RENDERING_MISMATCH",
                      _codes(ground_module.rendering_defects(ground, "GROUND")))

    def test_a_rendering_with_no_amendment_part_is_refused(self) -> None:
        ground = copy.deepcopy(GROUND)
        ground["rendering"] = "GROUND-1"
        self.assertIn("MALFORMED_RENDERING",
                      _codes(ground_module.rendering_defects(ground, "GROUND")))

    def test_an_amendment_is_not_a_new_revision(self) -> None:
        """A typo must not imply that the product entered a new epoch."""
        ground = copy.deepcopy(GROUND)
        ground["rendering"] = "GROUND-1.7"
        self.assertEqual(ground_module.rendering_defects(ground, "GROUND"), [])
        self.assertEqual(ground["revision"], GROUND["revision"])
        self.assertEqual(ground["epoch"], GROUND["epoch"])


class JoinDefectTest(unittest.TestCase):
    """Each declared defeat of the ground-to-canon join, driven through the judgement."""

    def test_a_promise_deriving_from_an_unknown_claim_is_refused(self) -> None:
        canon = copy.deepcopy(CANON)
        canon["promises"][0]["derives_from"].append("GROUND-999")
        self.assertIn("UNKNOWN_GROUND", _codes(ground_module.join_defects(canon, GROUND)))

    def test_a_claim_no_promise_carries_is_refused(self) -> None:
        """Ground carrying something the product does not undertake has drifted."""
        ground = copy.deepcopy(GROUND)
        ground["claims"].append({
            "ground_id": "GROUND-900",
            "statement": "A stable claim about the product that nothing here undertakes "
                         "to make possible for anyone at all.",
            "grounded_in": ["GROUND.md"],
            "if_false": "Nothing would change, which is the whole reason a claim nothing "
                        "carries does not belong in a product ground.",
        })
        self.assertIn("UNREALIZED_GROUND", _codes(ground_module.join_defects(CANON, ground)))

    def test_a_promise_deriving_from_a_retired_claim_is_refused(self) -> None:
        ground = copy.deepcopy(GROUND)
        retiring = CANON["promises"][0]["derives_from"][0]
        ground["claims"] = [c for c in ground["claims"] if c["ground_id"] != retiring]
        ground["retired"].append({"id": retiring, "retired_in": "GROUND-1",
                                  "epoch": "EPOCH-1",
                                  "because": "withdrawn to prove the join refuses this"})
        codes = _codes(ground_module.join_defects(CANON, ground))
        self.assertIn("RETIRED_GROUND_DERIVATION", codes)

    def test_a_retired_claim_declared_again_is_refused(self) -> None:
        """Retired, not reserved: an identifier never comes back meaning something else."""
        ground = copy.deepcopy(GROUND)
        ground["retired"].append({"id": "GROUND-001", "retired_in": "GROUND-1",
                                  "epoch": "EPOCH-1",
                                  "because": "superseded by a narrower wording"})
        self.assertIn("RETIRED_GROUND_REUSED", _codes(ground_module.ground_defects(ground)))

    def test_a_duplicate_claim_is_refused(self) -> None:
        ground = copy.deepcopy(GROUND)
        ground["claims"].append(copy.deepcopy(ground["claims"][0]))
        self.assertIn("DUPLICATE_GROUND", _codes(ground_module.ground_defects(ground)))

    def test_a_promise_that_exists_because_it_was_built_is_refused(self) -> None:
        """The direction-of-authority rule, made mechanical.

        An implementation is evidence about product intent and never authority for
        creating it. CANON-1 carried PROMISE-12 this way; CANON-2 does not.
        """
        canon = copy.deepcopy(CANON)
        canon["promises"][11]["source"] = ground_module.IMPLEMENTATION_ONLY
        self.assertIn("IMPLEMENTATION_DERIVED_PROMISE",
                      _codes(ground_module.join_defects(canon, GROUND)))

    def test_a_canon_pinned_to_the_wrong_ground_revision_is_refused(self) -> None:
        canon = copy.deepcopy(CANON)
        canon["ground_revision"] = "GROUND-4"
        self.assertIn("GROUND_REVISION_MISMATCH",
                      _codes(ground_module.join_defects(canon, GROUND)))

    def test_a_canon_from_another_epoch_is_refused(self) -> None:
        """A changed epoch means a different product, not a later draft."""
        canon = copy.deepcopy(CANON)
        canon["epoch"] = "EPOCH-2"
        self.assertIn("EPOCH_MISMATCH", _codes(ground_module.join_defects(canon, GROUND)))

    def test_a_claim_absent_from_the_wording_is_refused(self) -> None:
        ground = copy.deepcopy(GROUND)
        ground["claims"][0]["ground_id"] = "GROUND-901"
        self.assertIn("UNWORDED_GROUND",
                      _codes(ground_module.wording_defects(ground, WORDING)))


class AcceptanceTest(unittest.TestCase):
    """An accepted revision must be recorded where it says it is recorded."""

    RECORDED = (ROOT / "STATUS.yaml").read_bytes().decode("utf-8")

    def test_the_checked_in_records_agree_with_the_acceptance_record(self) -> None:
        for record, label in ((GROUND, "GROUND"), (CANON, "CANON")):
            with self.subTest(label=label):
                defects = ground_module.acceptance_defects(record, label, self.RECORDED)
                self.assertEqual(defects, [], " / ".join(defects))

    def test_both_are_accepted_under_one_epoch(self) -> None:
        self.assertEqual(GROUND["status"], "ACCEPTED")
        self.assertEqual(CANON["status"], "ACCEPTED")
        self.assertEqual(GROUND["epoch"], CANON["epoch"])

    def test_acceptance_of_a_revision_that_is_not_recorded_is_refused(self) -> None:
        """Two places hold one fact, so something has to check they agree."""
        record = copy.deepcopy(GROUND)
        record["revision"] = "GROUND-9"
        record["rendering"] = "GROUND-9.0"
        record["accepted"]["revision"] = "GROUND-9"
        self.assertIn("ACCEPTANCE_NOT_RECORDED",
                      _codes(ground_module.acceptance_defects(record, "GROUND",
                                                              self.RECORDED)))

    def test_acceptance_attached_to_another_revision_is_refused(self) -> None:
        record = copy.deepcopy(GROUND)
        record["accepted"]["revision"] = "GROUND-4"
        self.assertIn("ACCEPTANCE_REVISION_MISMATCH",
                      _codes(ground_module.acceptance_defects(record, "GROUND",
                                                              self.RECORDED)))

    def test_calling_itself_accepted_with_no_record_is_refused(self) -> None:
        record = copy.deepcopy(GROUND)
        del record["accepted"]
        self.assertIn("UNRECORDED_ACCEPTANCE",
                      _codes(ground_module.acceptance_defects(record, "GROUND",
                                                              self.RECORDED)))

    def test_an_acceptance_record_on_a_proposal_is_refused(self) -> None:
        record = copy.deepcopy(GROUND)
        record["status"] = "PROPOSED"
        self.assertIn("ACCEPTANCE_WITHOUT_STATUS",
                      _codes(ground_module.acceptance_defects(record, "GROUND",
                                                              self.RECORDED)))

    def test_acceptance_says_nothing_about_whether_a_claim_is_kept(self) -> None:
        """GROUND-010 is accepted and the node cannot presently keep it."""
        self.assertIn("not", GROUND["accepted"]["note"].lower())


class SchemaTest(unittest.TestCase):
    """Shapes the schema itself must refuse."""

    def test_ground_larger_than_twenty_claims_is_refused(self) -> None:
        ground = copy.deepcopy(GROUND)
        template = ground["claims"][0]
        while len(ground["claims"]) <= 20:
            extra = copy.deepcopy(template)
            extra["ground_id"] = f"GROUND-{900 + len(ground['claims']):03d}"
            ground["claims"].append(extra)
        self.assertNotEqual(validate(ground, SCHEMA), [])

    def test_a_claim_with_no_if_false_line_is_refused(self) -> None:
        """The admission test is a required field, not a convention."""
        ground = copy.deepcopy(GROUND)
        del ground["claims"][0]["if_false"]
        self.assertNotEqual(validate(ground, SCHEMA), [])

    def test_a_claim_grounded_in_nothing_is_refused(self) -> None:
        ground = copy.deepcopy(GROUND)
        ground["claims"][0]["grounded_in"] = []
        self.assertNotEqual(validate(ground, SCHEMA), [])

    def test_an_epoch_with_a_fractional_part_is_refused(self) -> None:
        ground = copy.deepcopy(GROUND)
        ground["epoch"] = "EPOCH-1.1"
        self.assertNotEqual(validate(ground, SCHEMA), [])


if __name__ == "__main__":
    unittest.main()
