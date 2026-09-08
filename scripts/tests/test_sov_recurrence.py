"""Tests for the definition-recurrence reader.

The properties worth holding are the ones that decide whether this reader can be trusted
rather than merely stay green. Settled experience must exclude a member nobody
independently observed and a member that never landed, because a basis drawn from either
would cite work that settled nothing. The candidate's identity must move when its basis
moves, or two different bases would propose the same thing. Synthesis must leave the
governing records byte-identical, since a reader that edits its own basis has rewritten the
rule that produced it. Institution neutrality must turn on a closed vocabulary rather than
on a role name appearing in prose, which is the distinction the clause actually makes.

The contract is exercised against this repository too: the ten primitives must resolve, and
the live reading must grade every predicate.
"""

from __future__ import annotations

from pathlib import Path
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovrecurrence import candidate, experience, fixture, neutrality, recurrence  # noqa: E402


class SettledExperience(unittest.TestCase):
    """What may enter the basis, and what may not."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = fixture.build(Path(self.temp.name))
        self.addCleanup(self.temp.cleanup)

    def test_excludes_a_member_nobody_witnessed(self) -> None:
        gathered = experience.gather(self.root, fixture.COLLECTION)
        cited = {source["address"] for source in gathered["sources"]}
        self.assertNotIn(fixture.BUILT_ONLY_ADDRESS, cited)

    def test_excludes_a_witnessed_member_that_never_landed(self) -> None:
        path = self.root / fixture.COLLECTION
        collection = json.loads(path.read_text(encoding="utf-8"))
        collection["custodies"][0]["members"][0]["work_state"] = "PRESENTED"
        path.write_text(json.dumps(collection, indent=2), encoding="utf-8", newline="\n")
        gathered = experience.gather(self.root, fixture.COLLECTION)
        self.assertNotIn("scripts/fixture_member_1.py",
                         {source["address"] for source in gathered["sources"]})

    def test_an_address_that_is_not_present_is_a_defect_not_a_silent_drop(self) -> None:
        (self.root / "witness/fixture-1.md").unlink()
        gathered = experience.gather(self.root, fixture.COLLECTION)
        self.assertTrue(any("witness/fixture-1.md" in defect for defect in gathered["defects"]))


class CandidateIdentity(unittest.TestCase):
    """The proposal identity is a function of the basis and of nothing else."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = fixture.build(Path(self.temp.name))
        self.addCleanup(self.temp.cleanup)

    def _synthesize(self) -> dict:
        gathered = experience.gather(self.root, fixture.COLLECTION)
        collection = json.loads((self.root / fixture.COLLECTION).read_text(encoding="utf-8"))
        return candidate.synthesize(self.root, gathered, collection)

    def test_the_same_basis_proposes_the_same_thing(self) -> None:
        self.assertEqual(self._synthesize()["proposal_id"], self._synthesize()["proposal_id"])

    def test_a_moved_basis_proposes_a_different_thing(self) -> None:
        before = self._synthesize()["proposal_id"]
        member = self.root / "scripts/fixture_member_1.py"
        member.write_text(member.read_text(encoding="utf-8") + "# moved\n",
                          encoding="utf-8", newline="\n")
        self.assertNotEqual(before, self._synthesize()["proposal_id"])

    def test_the_candidate_takes_no_standing_and_no_authority(self) -> None:
        synthesized = self._synthesize()
        self.assertEqual(synthesized["standing"], candidate.RECORDED)
        self.assertEqual(synthesized["authority_effect"], "NONE")

    def test_synthesis_leaves_every_governing_record_byte_identical(self) -> None:
        before = candidate.governing_digests(self.root)
        self._synthesize()
        self.assertEqual(before, candidate.governing_digests(self.root))


class InstitutionNeutrality(unittest.TestCase):
    """Neutrality turns on a closed vocabulary, not on a word appearing in prose."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = fixture.build(Path(self.temp.name))
        self.addCleanup(self.temp.cleanup)

    def test_a_role_name_in_prose_does_not_defeat_neutrality(self) -> None:
        path = self.root / neutrality.PRIMITIVES["finding"]
        document = json.loads(path.read_text(encoding="utf-8"))
        document["description"] = "A Witness forms one; an Orchestrator may form another."
        path.write_text(json.dumps(document, indent=2), encoding="utf-8", newline="\n")
        read = neutrality.read(self.root)
        self.assertFalse(read["fixed_role_names_required"])
        self.assertTrue(read["alternate_institution_composes"])

    def test_a_vocabulary_closed_to_the_proving_roles_defeats_it(self) -> None:
        path = self.root / neutrality.PRIMITIVES["finding"]
        path.write_text(json.dumps({"properties": {"role": {"enum": [
            "CONTROLLER", "ORCHESTRATOR", "WORKER", "WITNESS"]}}}),
            encoding="utf-8", newline="\n")
        read = neutrality.read(self.root)
        self.assertTrue(read["fixed_role_names_required"])
        self.assertFalse(read["alternate_institution_composes"])

    def test_an_open_vocabulary_that_merely_includes_the_roles_does_not(self) -> None:
        path = self.root / neutrality.PRIMITIVES["finding"]
        path.write_text(json.dumps({"properties": {"role": {"enum": [
            "CONTROLLER", "WITNESS", "PROCUREMENT_STEWARD"]}}}),
            encoding="utf-8", newline="\n")
        self.assertFalse(neutrality.read(self.root)["fixed_role_names_required"])

    def test_the_alternate_institution_shares_no_name_with_the_proving_roles(self) -> None:
        alternate = {role.upper().replace("-", "_") for role in neutrality.ALTERNATE_INSTITUTION["roles"]}
        self.assertFalse(alternate & neutrality.PROVING_ROLES)


class AgainstThisRepository(unittest.TestCase):
    """The live reading, exercised where it will actually run."""

    def test_every_declared_primitive_resolves(self) -> None:
        read = neutrality.read(ROOT)
        self.assertEqual(read["unresolved"], [])
        self.assertEqual(sorted(read["generic_primitives"]), sorted(neutrality.PRIMITIVES))

    def test_the_live_reading_grades_every_predicate(self) -> None:
        result = recurrence.run(ROOT)
        self.assertEqual(sorted(result["grades"]), sorted(recurrence.PREDICATES))

    def test_the_basis_is_drawn_only_from_settled_members(self) -> None:
        gathered = experience.gather(ROOT)
        self.assertEqual(gathered["defects"], [])
        self.assertTrue(gathered["sources"], "no settled experience found to cite")


if __name__ == "__main__":
    unittest.main()
