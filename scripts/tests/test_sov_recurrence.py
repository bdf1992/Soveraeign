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

from sovrecurrence import (candidate, declaration, experience, fixture, neutrality,
                           recurrence)  # noqa: E402


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

    def test_the_basis_does_not_come_from_the_member_prose(self) -> None:
        """Deleting the paths a member names must not shrink what the reader cites.

        This is the defeat two independent witnesses used: a guard keyed on a substring the
        same participant writes removes the evidence and the alarm in one edit.
        """
        path = self.root / fixture.COLLECTION
        collection = json.loads(path.read_text(encoding="utf-8"))
        before = len(experience.gather(self.root, fixture.COLLECTION)["sources"])
        for custody in collection["custodies"]:
            for member in custody["members"]:
                member["stage_observed_by"] = "observed; this sentence names no path at all"
        path.write_text(json.dumps(collection, indent=2), encoding="utf-8", newline="\n")
        after = experience.gather(self.root, fixture.COLLECTION)
        self.assertEqual(len(after["sources"]), before)
        self.assertEqual(after["defects"], [])

    def test_a_member_settled_at_ratified_is_admitted(self) -> None:
        """RATIFIED is above WITNESSED; admitting only the exact token would drop it."""
        path = self.root / fixture.COLLECTION
        collection = json.loads(path.read_text(encoding="utf-8"))
        collection["custodies"][0]["members"][0]["standing"] = "RATIFIED"
        path.write_text(json.dumps(collection, indent=2), encoding="utf-8", newline="\n")
        gathered = experience.gather(self.root, fixture.COLLECTION)
        self.assertIn("scripts/fixture_member_1.py",
                      {source["address"] for source in gathered["sources"]})

    def test_a_member_with_no_work_state_is_not_admitted(self) -> None:
        """An absent field must refuse, never default open."""
        path = self.root / fixture.COLLECTION
        collection = json.loads(path.read_text(encoding="utf-8"))
        del collection["custodies"][0]["members"][0]["work_state"]
        path.write_text(json.dumps(collection, indent=2), encoding="utf-8", newline="\n")
        gathered = experience.gather(self.root, fixture.COLLECTION)
        self.assertNotIn("scripts/fixture_member_1.py",
                         {source["address"] for source in gathered["sources"]})

    def test_the_tree_digest_reads_bytes_not_just_paths(self) -> None:
        """A directory member is pinned by what it contains, not by its file names."""
        tree = self.root / "tree"
        (tree / "inner").mkdir(parents=True)
        leaf = tree / "inner" / "file.txt"
        leaf.write_text("before\n", encoding="utf-8", newline="\n")
        before = experience.digest(tree)
        leaf.write_text("after\n", encoding="utf-8", newline="\n")
        self.assertNotEqual(before, experience.digest(tree))

    def test_a_member_address_that_is_not_present_is_a_defect(self) -> None:
        """The member's own address must resolve to bytes; a missing one is never skipped."""
        (self.root / "scripts/fixture_member_1.py").unlink()
        gathered = experience.gather(self.root, fixture.COLLECTION)
        self.assertTrue(any("scripts/fixture_member_1.py" in defect
                            for defect in gathered["defects"]))


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
        path = self.root / neutrality.PRIMITIVES["finding"][0]
        document = json.loads(path.read_text(encoding="utf-8"))
        document["description"] = ("A Witness forms this finding; an Orchestrator may form "
                                   "another.")
        path.write_text(json.dumps(document, indent=2), encoding="utf-8", newline="\n")
        read = neutrality.read(self.root)
        self.assertFalse(read["fixed_role_names_required"])
        self.assertTrue(read["alternate_institution_composes"])

    def test_a_vocabulary_closed_to_the_proving_roles_defeats_it(self) -> None:
        path = self.root / neutrality.PRIMITIVES["finding"][0]
        path.write_text(json.dumps(fixture._stub("finding", properties={"role": {"enum": [
            "CONTROLLER", "ORCHESTRATOR", "WORKER", "WITNESS"]}})),
            encoding="utf-8", newline="\n")
        read = neutrality.read(self.root)
        self.assertTrue(read["fixed_role_names_required"])
        self.assertFalse(read["alternate_institution_composes"])

    def test_a_vocabulary_admitting_two_roles_and_no_alternate_is_closed(self) -> None:
        """The witness's counterexample: closed against procurement without being four-of-four."""
        self.assertTrue(neutrality._closes(["worker", "orchestrator", "controller", "owner"]))

    def test_exactly_two_proving_roles_is_the_threshold(self) -> None:
        """Pins the rule at two. A witness noted >= 3 survived every other test."""
        self.assertTrue(neutrality._closes(["worker", "orchestrator"]))
        self.assertFalse(neutrality._closes(["worker"]))

    def test_a_binding_to_a_contract_that_never_names_the_primitive_is_unresolved(self) -> None:
        """Resolution must mean the contract declares the primitive, not merely that it parses."""
        original = dict(neutrality.PRIMITIVES)
        neutrality.PRIMITIVES["session"] = (original["finding"][0], "session")
        self.addCleanup(neutrality.PRIMITIVES.__setitem__, "session", original["session"])
        read = neutrality.read(self.root)
        self.assertTrue(any("session" in item for item in read["unresolved"]))

    def test_an_actor_kind_taxonomy_sharing_one_word_is_not_closed(self) -> None:
        """WORKER is also a kind of actor; one overlapping word is not the institution."""
        self.assertFalse(neutrality._closes(["HUMAN", "MODEL", "WORKER", "SYSTEM"]))

    def test_a_const_closure_is_a_stated_gap_not_a_silent_one(self) -> None:
        """A const pins a field to one role and this reader does not see it. Held visible
        here so the limitation is a failing assumption if anyone ever fixes it silently."""
        path = self.root / neutrality.PRIMITIVES["finding"][0]
        path.write_text(json.dumps(fixture._stub("finding", properties={
            "a": {"const": "WITNESS"}, "b": {"const": "CONTROLLER"}})),
            encoding="utf-8", newline="\n")
        self.assertEqual(neutrality.read(self.root)["closed_vocabularies"], [])

    def test_an_open_vocabulary_that_merely_includes_the_roles_does_not(self) -> None:
        path = self.root / neutrality.PRIMITIVES["finding"][0]
        path.write_text(json.dumps(fixture._stub("finding", properties={"role": {"enum": [
            "CONTROLLER", "WITNESS", "PROCUREMENT_STEWARD"]}})),
            encoding="utf-8", newline="\n")
        self.assertFalse(neutrality.read(self.root)["fixed_role_names_required"])

    def test_a_term_in_a_title_is_not_a_declaration(self) -> None:
        """The fourth witness's plant, both ways, in one test.

        `contracts/work-circuit.json` resolved only because its title is a sentence with the
        word `work` in it, and `contracts/ticket-settlement.json` failed only because it has
        no title at all. Both were one-string edits away from the opposite verdict.
        """
        path = self.root / neutrality.PRIMITIVES["finding"][0]
        path.write_text(json.dumps({"title": "A finding is what an evaluator forms",
                                    "properties": {"actor_id": {"type": "string"}}}),
                        encoding="utf-8", newline="\n")
        self.assertTrue(any("finding" in item for item in neutrality.read(self.root)["unresolved"]))

    def test_a_declared_identity_is_a_declaration(self) -> None:
        """What replaced the title: the identifier a contract gives itself, root level only."""
        path = self.root / neutrality.PRIMITIVES["finding"][0]
        path.write_text(json.dumps({"policy_id": "soveraeign-finding/v1"}),
                        encoding="utf-8", newline="\n")
        self.assertEqual(neutrality.read(self.root)["unresolved"], [])

    def test_an_identifier_in_example_data_is_not_the_contract_identity(self) -> None:
        """Root only. An identifier nested in an example belongs to the example."""
        path = self.root / neutrality.PRIMITIVES["finding"][0]
        path.write_text(json.dumps({"examples": [{"policy_id": "soveraeign-finding/v1"}]}),
                        encoding="utf-8", newline="\n")
        self.assertTrue(any("finding" in item for item in neutrality.read(self.root)["unresolved"]))

    def test_a_closure_a_primitive_names_as_governing_it_is_graded(self) -> None:
        """The third witness's leak, now graded rather than disclosed."""
        (self.root / fixture.GOVERNING_STUB).write_text(
            json.dumps({"$id": "fixture-governing",
                        "properties": {"filled_by": {"enum": list(fixture.CLOSED_ROLES)}}}),
            encoding="utf-8", newline="\n")
        read = neutrality.read(self.root)
        self.assertTrue(read["fixed_role_names_required"])
        self.assertTrue(any("is governed by" in item for item in read["closed_vocabularies"]))

    def test_a_closure_no_primitive_names_is_reported_and_not_graded(self) -> None:
        """Grading follows the primitives; an unrelated contract defeats none of them."""
        (self.root / "contracts/unrelated.json").write_text(
            json.dumps({"$id": "unrelated",
                        "properties": {"filled_by": {"enum": list(fixture.CLOSED_ROLES)}}}),
            encoding="utf-8", newline="\n")
        read = neutrality.read(self.root)
        self.assertFalse(read["fixed_role_names_required"])
        self.assertTrue(any("unrelated.json" in item for item in read["closed_elsewhere"]))

    def test_a_governed_closure_outside_the_contracts_tree_is_still_scanned(self) -> None:
        """The scan is the contracts tree plus what a primitive names, not the tree alone."""
        outside = self.root / "services/fixture/contracts/governing.json"
        outside.parent.mkdir(parents=True, exist_ok=True)
        outside.write_text(json.dumps({"$id": "outside", "properties": {
            "filled_by": {"enum": list(fixture.CLOSED_ROLES)}}}), encoding="utf-8", newline="\n")
        bound = self.root / neutrality.PRIMITIVES["settlement"][0]
        document = json.loads(bound.read_text(encoding="utf-8"))
        document["governed_by"] = ["services/fixture/contracts/governing.json"]
        bound.write_text(json.dumps(document), encoding="utf-8", newline="\n")
        read = neutrality.read(self.root)
        self.assertTrue(read["fixed_role_names_required"])
        self.assertTrue(any("is governed by" in item for item in read["closed_vocabularies"]))

    def test_every_excluded_instance_key_is_exercised_by_the_mispaired_variant(self) -> None:
        """The fixture may not be derived from the rule it exists to refuse.

        `_mispaired` fills a written-out list of instance keys, not `EXAMPLE_KEYS` itself,
        because a variant built from the constant empties itself when the constant is
        narrowed - which is exactly the regression the variant is there to catch. The two
        lists must still name the same keys: a key the rule reads would make the variant
        resolve legitimately, and a key the rule excludes but the fixture skips is a hole.
        Narrowing `EXAMPLE_KEYS` fails the self-check; widening it fails here.
        """
        self.assertEqual(set(declaration.EXAMPLE_KEYS), set(fixture.INSTANCE_KEYS))
        self.assertEqual(set(declaration.PROSE_KEYS), set(fixture.PROSE_KEYS))

    def test_a_properties_dict_inside_an_example_declares_nothing(self) -> None:
        """Identity is read at the root; declared names must follow the same line."""
        path = self.root / neutrality.PRIMITIVES["finding"][0]
        path.write_text(json.dumps({"$id": "unrelated", "examples": [
            {"properties": {"finding_id": {"type": "string"}}}]}),
            encoding="utf-8", newline="\n")
        self.assertTrue(any("finding" in item
                            for item in neutrality.read(self.root)["unresolved"]))

    def test_a_root_identifier_carrying_prose_is_not_an_identifier(self) -> None:
        """A root key that ends in `_id` cannot smuggle a sentence back in."""
        path = self.root / neutrality.PRIMITIVES["finding"][0]
        path.write_text(json.dumps({"policy_id": "a record of every finding an evaluator makes"}),
                        encoding="utf-8", newline="\n")
        self.assertTrue(any("finding" in item
                            for item in neutrality.read(self.root)["unresolved"]))

    def test_the_alternate_institution_shares_no_name_with_the_proving_roles(self) -> None:
        alternate = {role.upper().replace("-", "_") for role in neutrality.ALTERNATE_INSTITUTION["roles"]}
        self.assertFalse(alternate & neutrality.PROVING_ROLES)


class AgainstThisRepository(unittest.TestCase):
    """The live reading, exercised where it will actually run."""

    def test_every_unresolved_pairing_names_its_contract_and_its_term(self) -> None:
        """Pins the mechanism, not the verdict.

        An earlier version asserted which primitives were unresolved. That pins a failing
        reading into the build, so satisfying the clause would turn the suite red - an
        independent witness demonstrated exactly that. What must hold is that an unresolved
        pairing says which contract and which term it asserted, whether there are two of
        them today or none tomorrow.
        """
        read = neutrality.read(ROOT)
        for entry in read["unresolved"]:
            self.assertIn("is paired with", entry)
            self.assertRegex(entry, r"as `[a-z]+`")
        for primitive in read["generic_primitives"]:
            self.assertIn(primitive, neutrality.PRIMITIVES)

    def test_the_live_reading_grades_every_predicate(self) -> None:
        result = recurrence.run(ROOT)
        self.assertEqual(sorted(result["grades"]), sorted(recurrence.PREDICATES))

    def test_no_reported_closure_sits_in_a_contract_a_primitive_names(self) -> None:
        """Pins the split, not the count, and can actually fail.

        The first version asserted that no `closed_elsewhere` entry contained the string
        "is governed by", which the reported branch never writes: it passed under the direct
        inverse of the repair it claimed to pin. The second rebuilt the governed set here but
        recovered each address by splitting the reader's sentence on "/properties", so an
        identical leak passed whenever the closure sat under "/definitions". A sixth witness
        found both. Both directions are checked now, and the addresses come from the reader as
        data rather than from its prose.
        """
        governed: set[str] = set()
        for relative, _ in neutrality.PRIMITIVES.values():
            document = json.loads((ROOT / relative).read_text(encoding="utf-8"))
            governed.update(reference for reference in document.get("governed_by") or []
                            if isinstance(reference, str))
        bound = {relative for relative, _ in neutrality.PRIMITIVES.values()}
        read = neutrality.read(ROOT)
        for address in read["reported_closure_addresses"]:
            self.assertNotIn(address, governed - bound)
        for address in read["governed_closure_addresses"]:
            self.assertIn(address, governed - bound)

    def test_the_basis_is_drawn_only_from_settled_members(self) -> None:
        gathered = experience.gather(ROOT)
        self.assertEqual(gathered["defects"], [])
        self.assertTrue(gathered["sources"], "no settled experience found to cite")


if __name__ == "__main__":
    unittest.main()
