"""Typed collections, membership, and every refusal each of them declares."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from soveraeign_asset_service import AssetService, AuthorityRefused, OrganizationRefused

PROJECT_SPEC = {
    "required_fields": ["title", "owner", "status"],
    "optional_fields": ["due"],
    "vocabularies": {"status": ["PLANNED", "ACTIVE", "CLOSED"]},
    "admits_roles": ["ORIGINAL", "REVISION"],
}


class OrganizationCase(unittest.TestCase):
    """One service root with the curatorial grants a librarian would hold."""

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.service = AssetService(self.root / "state")
        self.org = self.service.organization
        for capability in ("declare:collection-type", "declare:asset-collection",
                           "organize:asset", "retract:record", "ratify:judgement"):
            self.service.grant("Bdo", "Bdo", capability)

    def tearDown(self):
        self.service.close()
        self.tmp.cleanup()

    def asset(self, name: str, body: bytes = b"payload\n") -> str:
        path = self.root / name
        path.write_bytes(body)
        return self.service.ingest(path, name, "Bdo")["asset_id"]

    def project(self) -> str:
        self.org.declare_type("project", "Project", PROJECT_SPEC, "Bdo")
        return self.org.declare_collection("project", "Autumn launch", "Bdo")["collection_id"]

    def refusal(self, call, *args, **kwargs) -> str:
        with self.assertRaises(OrganizationRefused) as caught:
            call(*args, **kwargs)
        return caught.exception.code


class DeclaringATypeTests(OrganizationCase):
    def test_a_declared_type_keeps_its_spec_in_a_stable_order(self):
        self.org.declare_type("project", "Project", PROJECT_SPEC, "Bdo")
        declared = self.org.type("project")
        self.assertEqual(declared["label"], "Project")
        self.assertEqual(declared["spec"]["required_fields"], ["title", "owner", "status"])
        self.assertEqual(declared["spec"]["admits_roles"], ["ORIGINAL", "REVISION"])
        self.assertEqual(declared["spec"]["vocabularies"]["status"],
                         ["ACTIVE", "CLOSED", "PLANNED"])

    def test_declaring_a_type_without_a_grant_is_refused(self):
        with self.assertRaises(AuthorityRefused):
            self.org.declare_type("project", "Project", PROJECT_SPEC, "stranger")
        self.assertIsNone(self.org.type("project"))

    def test_redeclaring_a_type_is_refused_rather_than_overwriting_it(self):
        self.org.declare_type("project", "Project", PROJECT_SPEC, "Bdo")
        code = self.refusal(self.org.declare_type, "project", "Other", PROJECT_SPEC, "Bdo")
        self.assertEqual(code, "STALE_STATE")
        self.assertEqual(self.org.type("project")["label"], "Project")

    def test_a_type_requiring_nothing_is_refused(self):
        self.assertEqual(
            self.refusal(self.org.declare_type, "loose", "Loose",
                         {"optional_fields": ["title"]}, "Bdo"),
            "INCOMPLETE_PROPOSAL")

    def test_a_field_declared_twice_is_refused(self):
        self.assertEqual(
            self.refusal(self.org.declare_type, "dupe", "Dupe",
                         {"required_fields": ["title"], "optional_fields": ["title"]}, "Bdo"),
            "INCOMPLETE_PROPOSAL")

    def test_a_spec_key_the_type_grammar_does_not_declare_is_refused(self):
        self.assertEqual(
            self.refusal(self.org.declare_type, "odd", "Odd",
                         {"required_fields": ["title"], "retention": "forever"}, "Bdo"),
            "INCOMPLETE_PROPOSAL")

    def test_a_vocabulary_over_a_field_the_spec_never_declared_is_refused(self):
        self.assertEqual(
            self.refusal(self.org.declare_type, "ghost", "Ghost",
                         {"required_fields": ["title"],
                          "vocabularies": {"status": ["ACTIVE"]}}, "Bdo"),
            "POLICY_REFUSED")

    def test_a_role_the_service_does_not_have_is_refused(self):
        self.assertEqual(
            self.refusal(self.org.declare_type, "alien", "Alien",
                         {"required_fields": ["title"], "admits_roles": ["SNAPSHOT"]}, "Bdo"),
            "POLICY_REFUSED")

    def test_a_refused_declaration_still_leaves_a_receipt(self):
        self.refusal(self.org.declare_type, "loose", "Loose", {"optional_fields": []}, "Bdo")
        refused = [r for r in self.service.receipts()
                   if r["event"] == "asset.declare-collection-type" and r["outcome"] == "REFUSED"]
        self.assertEqual(len(refused), 1)


class DeclaringACollectionTests(OrganizationCase):
    def test_a_collection_of_a_declared_type_opens_empty(self):
        collection_id = self.project()
        entry = self.org.collections()[0]
        self.assertEqual(entry["collection_id"], collection_id)
        self.assertEqual(entry["type_id"], "project")
        self.assertEqual(entry["members"], 0)

    def test_a_collection_of_an_undeclared_type_is_refused(self):
        self.assertEqual(
            self.refusal(self.org.declare_collection, "campaign", "Autumn", "Bdo"),
            "TYPE_UNDECLARED")
        self.assertEqual(self.org.collections(), [])

    def test_declaring_a_collection_without_a_grant_is_refused(self):
        self.org.declare_type("project", "Project", PROJECT_SPEC, "Bdo")
        with self.assertRaises(AuthorityRefused):
            self.org.declare_collection("project", "Autumn", "stranger")
        self.assertEqual(self.org.collections(), [])


class MembershipTests(OrganizationCase):
    def test_a_filed_asset_is_a_member_and_leaves_a_receipt(self):
        collection_id = self.project()
        asset_id = self.asset("brief.txt")
        filed = self.org.add_member(collection_id, asset_id, "Bdo")
        self.assertEqual(filed["role"], "ORIGINAL")
        self.assertEqual([m["asset_id"] for m in self.org.members(collection_id)], [asset_id])
        self.assertEqual(self.org.collections()[0]["members"], 1)
        receipts = [r for r in self.service.receipts() if r["event"] == "asset.add-member"]
        self.assertEqual([r["outcome"] for r in receipts], ["COMMITTED"])

    def test_filing_into_a_collection_that_does_not_exist_is_refused(self):
        self.project()
        asset_id = self.asset("brief.txt")
        self.assertEqual(self.refusal(self.org.add_member, "collection_absent", asset_id, "Bdo"),
                         "MISSING_PRECONDITION")

    def test_filing_an_asset_that_does_not_exist_is_refused(self):
        collection_id = self.project()
        self.assertEqual(self.refusal(self.org.add_member, collection_id, "asset_absent", "Bdo"),
                         "MISSING_PRECONDITION")

    def test_filing_the_same_asset_twice_is_refused(self):
        collection_id = self.project()
        asset_id = self.asset("brief.txt")
        self.org.add_member(collection_id, asset_id, "Bdo")
        self.assertEqual(self.refusal(self.org.add_member, collection_id, asset_id, "Bdo"),
                         "DUPLICATE_MEMBERSHIP")
        self.assertEqual(len(self.org.members(collection_id)), 1)

    def test_an_asset_whose_role_the_type_does_not_admit_is_refused(self):
        self.org.declare_type("derived-only", "Derived only",
                              {"required_fields": ["title"], "admits_roles": ["DERIVATIVE"]},
                              "Bdo")
        collection_id = self.org.declare_collection(
            "derived-only", "Renditions", "Bdo")["collection_id"]
        asset_id = self.asset("brief.txt")
        self.assertEqual(self.refusal(self.org.add_member, collection_id, asset_id, "Bdo"),
                         "MEMBER_KIND_REFUSED")
        self.assertEqual(self.org.members(collection_id), [])

    def test_filing_without_a_grant_is_refused(self):
        collection_id = self.project()
        asset_id = self.asset("brief.txt")
        with self.assertRaises(AuthorityRefused):
            self.org.add_member(collection_id, asset_id, "stranger")
        self.assertEqual(self.org.members(collection_id), [])

    def test_removing_a_member_counters_it_and_erases_no_filing(self):
        collection_id = self.project()
        asset_id = self.asset("brief.txt")
        membership_id = self.org.add_member(collection_id, asset_id, "Bdo")["membership_id"]
        self.org.remove_member(membership_id, "Bdo", "filed in error")
        self.assertEqual(self.org.members(collection_id), [])
        events = [(r["event"], r["outcome"]) for r in self.service.receipts()
                  if r["subject_type"] == "collection-membership"]
        self.assertIn(("asset.add-member", "COMMITTED"), events)
        self.assertIn(("asset.remove-member", "COUNTERED"), events)

    def test_a_countered_member_can_be_filed_again(self):
        collection_id = self.project()
        asset_id = self.asset("brief.txt")
        membership_id = self.org.add_member(collection_id, asset_id, "Bdo")["membership_id"]
        self.org.remove_member(membership_id, "Bdo", "filed in error")
        self.org.add_member(collection_id, asset_id, "Bdo")
        self.assertEqual(len(self.org.members(collection_id)), 1)

    def test_removing_a_member_without_a_grant_is_refused(self):
        collection_id = self.project()
        asset_id = self.asset("brief.txt")
        membership_id = self.org.add_member(collection_id, asset_id, "Bdo")["membership_id"]
        with self.assertRaises(AuthorityRefused):
            self.org.remove_member(membership_id, "stranger", "no standing")
        self.assertEqual(len(self.org.members(collection_id)), 1)

    def test_removing_a_membership_that_does_not_exist_raises(self):
        with self.assertRaises(KeyError):
            self.org.remove_member("member_absent", "Bdo", "nothing there")

    def test_an_asset_in_no_collection_is_unfiled(self):
        collection_id = self.project()
        filed = self.asset("brief.txt")
        loose = self.asset("stray.txt", b"stray\n")
        self.org.add_member(collection_id, filed, "Bdo")
        self.assertEqual(self.org.unfiled(), [loose])


if __name__ == "__main__":
    unittest.main()
