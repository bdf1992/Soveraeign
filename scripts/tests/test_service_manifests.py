"""Prove the service-manifest check admits what it must and refuses what it must not.

``contracts/fixtures/service-manifest.fixtures.json`` follows the repository fixture
convention: every entry names the contract it tests and carries a whole manifest record.
``scripts/tests/test_contract_fixtures.py`` already proves each record against the schema.
This module proves the half a schema cannot express - that an endpoint matches its own
operation, that a refusal maps to the kernel, that a read does not commit, and that a record
written by one operation can be read back by another - by driving the checker over each
semantic entry and requiring the defect that entry declared.

The checked-in manifests are judged here too, so a service that stops telling the truth about
its own surface fails the build rather than drifting quietly.

Passing establishes ``BUILT`` for the contract and its checker. It witnesses nothing: no
operation declared in any manifest is served, and no actor holds a grant any of them names.
"""

from __future__ import annotations

from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovkernel import manifests  # noqa: E402

ENTRIES = json.loads(
    (ROOT / "contracts" / "fixtures" / "service-manifest.fixtures.json").read_text("utf-8"))
POSITIVE = [entry for entry in ENTRIES if entry["polarity"] == "positive"]
SEMANTIC = [entry for entry in ENTRIES if entry.get("expected_manifest_defects")]
SCHEMA_DEFEATS = [entry for entry in ENTRIES
                  if entry["polarity"] == "defeating" and not entry.get("expected_manifest_defects")]

KERNEL = manifests.kernel_refusals()
TRANSITIONS = manifests.kernel_transition_ids()
REQUIREMENTS = manifests.prd_requirements()


def judge(manifest: dict) -> list[str]:
    """Every defect the checker finds in one manifest."""
    return manifests.defects(manifest, KERNEL, TRANSITIONS, REQUIREMENTS)


class AdmissibleCase(unittest.TestCase):
    """The positive control. A checker that refuses everything proves nothing."""

    def test_the_fixture_carries_a_positive_case(self) -> None:
        self.assertTrue(POSITIVE)

    def test_every_positive_case_passes_with_no_defect(self) -> None:
        for entry in POSITIVE:
            with self.subTest(fixture=entry["id"]):
                self.assertEqual([], judge(entry["record"]))

    def test_the_positive_case_exercises_every_write_verb(self) -> None:
        verbs = {op["crud"] for entry in POSITIVE for op in entry["record"]["operations"]}
        self.assertEqual({"CREATE", "READ", "SUPERSEDE", "COUNTER"}, verbs)


class SemanticDefeats(unittest.TestCase):
    """Each schema-valid defeat must fail by the manifest check it named."""

    def test_the_fixture_carries_semantic_defeats(self) -> None:
        self.assertTrue(SEMANTIC)

    def test_every_semantic_entry_is_defeated_by_its_declared_check(self) -> None:
        for entry in SEMANTIC:
            with self.subTest(fixture=entry["id"]):
                found = judge(entry["record"])
                self.assertTrue(found, f"{entry['id']} produced no defect at all")
                joined = " | ".join(found)
                for expected in entry["expected_manifest_defects"]:
                    self.assertIn(expected, joined,
                                  f"{entry['id']} failed, but not by {expected!r}: {joined}")

    def test_every_semantic_entry_says_what_it_defeats(self) -> None:
        for entry in SEMANTIC:
            with self.subTest(fixture=entry["id"]):
                self.assertTrue(str(entry.get("defeats", "")).strip())

    def test_schema_defeats_are_caught_before_the_semantic_checks_run(self) -> None:
        """A record the schema rejects must report that, not a downstream symptom."""
        for entry in SCHEMA_DEFEATS:
            with self.subTest(fixture=entry["id"]):
                found = judge(entry["record"])
                self.assertTrue(found, f"{entry['id']} produced no defect at all")
                self.assertTrue(all(defect.startswith("schema:") for defect in found),
                                f"{entry['id']} reported past the schema: {found}")

    def test_no_two_entries_share_an_id(self) -> None:
        ids = [entry["id"] for entry in ENTRIES]
        self.assertEqual(len(ids), len(set(ids)))


class CheckedInManifests(unittest.TestCase):
    """The manifests on disk, judged by the same checker as the fixtures."""

    def test_every_manifest_passes(self) -> None:
        total, findings = manifests.check_all()
        self.assertEqual([], findings)
        self.assertGreater(total, 0)

    def test_every_service_declares_at_least_one_read(self) -> None:
        for row in manifests.crud_coverage():
            with self.subTest(service=row["service_id"]):
                self.assertIn("READ", row["verbs"],
                              f"{row['service_id']} declares no way to read anything back")

    def test_every_logical_endpoint_is_unique_across_all_services(self) -> None:
        addresses = [row["logical_endpoint"] for row in manifests.endpoints()]
        self.assertEqual(len(addresses), len(set(addresses)))

    def test_no_manifest_declares_an_operation_twice(self) -> None:
        for path in manifests.manifest_paths():
            manifest = manifests.load(path)
            names = [entry["operation"] for entry in manifest["operations"]]
            with self.subTest(service=manifest["service_id"]):
                self.assertEqual(len(names), len(set(names)))

    def test_every_operation_acts_on_a_record_its_service_owns(self) -> None:
        for path in manifests.manifest_paths():
            manifest = manifests.load(path)
            owns = set(manifest["owns"])
            for entry in manifest["operations"]:
                with self.subTest(endpoint=entry["logical_endpoint"]):
                    self.assertIn(entry["subject"], owns)


class CrudVocabulary(unittest.TestCase):
    """The append-preserving verb set is a closed vocabulary, not an open one."""

    def test_erasure_is_not_an_admissible_verb(self) -> None:
        self.assertNotIn("DELETE", manifests.COMMIT_BY_CRUD)
        self.assertNotIn("UPDATE", manifests.COMMIT_BY_CRUD)

    def test_a_read_may_only_derive(self) -> None:
        self.assertEqual({"DERIVED"}, manifests.COMMIT_BY_CRUD["READ"])

    def test_a_counter_may_only_counter(self) -> None:
        self.assertEqual({"COUNTERED"}, manifests.COMMIT_BY_CRUD["COUNTER"])


if __name__ == "__main__":
    unittest.main()
