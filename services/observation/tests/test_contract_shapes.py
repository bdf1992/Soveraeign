"""Drive the Observation Service fixture corpora against the schemas it declares.

The schemas here were written before the implementation existed and are not edited to fit it;
nothing in this module exercises the service (`test_thin_slice.py` does). It proves the
contracts themselves: that each declared positive record is
admitted, that each declared defeat is refused, and that a record labelled schema-valid but
semantically wrong really is schema-valid, so the gap is recorded rather than mistaken for
coverage.

One check reads `CHARTER.md` at check time and compares the direct-edge vocabulary the charter
documents against the enum the schema enforces. The edge set is the whole enforcement surface
of the service (`decisions/0041-the-observation-service.md`, Ruling 2); a charter and a contract
that disagree about it would leave two descriptions of what "direct" means.

A passing run establishes `BUILT` for the contracts and their fixture pairs. It witnesses
nothing: the service's own tests are self-tests, and nothing independent has observed it.
"""

from __future__ import annotations

from pathlib import Path
import json
import re
import sys
import unittest

SERVICE = Path(__file__).resolve().parents[1]
ROOT = SERVICE.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sovkernel.jsonschema import validate  # noqa: E402

CONTRACTS = SERVICE / "contracts"
FIXTURE_FILES = sorted((CONTRACTS / "fixtures").glob("*.fixtures.json"))
CHARTER = (SERVICE / "CHARTER.md").read_text(encoding="utf-8")
MANIFEST = json.loads((CONTRACTS / "service.json").read_text(encoding="utf-8"))

SEMANTIC_MARKER = "expected_inference_check"


def _entries():
    for path in FIXTURE_FILES:
        for entry in json.loads(path.read_text(encoding="utf-8")):
            yield path.name, entry


def _schema(entry):
    return json.loads((CONTRACTS / entry["contract"]).read_text(encoding="utf-8"))


class FixtureCorpus(unittest.TestCase):
    """Every entry behaves the way it declares it will."""

    def test_the_corpus_is_not_vacuous(self) -> None:
        self.assertTrue(FIXTURE_FILES, f"no *.fixtures.json under {CONTRACTS / 'fixtures'}")

    def test_every_entry_is_well_formed(self) -> None:
        for name, entry in _entries():
            with self.subTest(file=name, entry=entry.get("id")):
                for key in ("id", "contract", "status", "polarity", "expected_validity",
                            "description", "record"):
                    self.assertIn(key, entry)
                self.assertIn(entry["expected_validity"], ("VALID", "INVALID"))
                self.assertTrue((CONTRACTS / entry["contract"]).is_file())

    def test_every_entry_validates_as_declared(self) -> None:
        for name, entry in _entries():
            with self.subTest(file=name, entry=entry["id"]):
                defects = validate(entry["record"], _schema(entry), _schema(entry), "/")
                observed = "INVALID" if defects else "VALID"
                self.assertEqual(entry["expected_validity"], observed,
                                 f"{entry['id']}: {defects[:2]}")

    def test_every_contract_has_a_positive_and_a_defeating_entry(self) -> None:
        seen: dict[str, set[str]] = {}
        for _, entry in _entries():
            seen.setdefault(entry["contract"], set()).add(entry["polarity"])
        for contract in sorted(CONTRACTS.glob("*.schema.json")):
            with self.subTest(contract=contract.name):
                self.assertEqual({"positive", "defeating"}, seen.get(contract.name, set()),
                                 f"{contract.name} lacks a positive and a defeating entry")

    def test_no_two_entries_share_an_id(self) -> None:
        ids = [entry["id"] for _, entry in _entries()]
        self.assertEqual(len(ids), len(set(ids)))


class SemanticGaps(unittest.TestCase):
    """A defeat the schema admits must name what catches it, and prove the schema misses it."""

    def _semantic(self):
        return [(name, entry) for name, entry in _entries() if SEMANTIC_MARKER in entry]

    def test_the_corpus_records_at_least_one_semantic_gap(self) -> None:
        self.assertTrue(self._semantic())

    def test_every_semantic_entry_is_genuinely_schema_valid(self) -> None:
        """If the schema already caught it, the entry is mislabelled and hides a real gap."""
        for name, entry in self._semantic():
            with self.subTest(file=name, entry=entry["id"]):
                self.assertEqual("VALID", entry["expected_validity"])
                self.assertEqual([], validate(entry["record"], _schema(entry), _schema(entry), "/"))

    def test_every_semantic_entry_names_the_check_and_what_it_defeats(self) -> None:
        for name, entry in self._semantic():
            with self.subTest(file=name, entry=entry["id"]):
                self.assertTrue(entry[SEMANTIC_MARKER].strip())
                self.assertTrue(str(entry.get("defeats", "")).strip())

    def test_a_defeating_entry_the_schema_admits_must_declare_a_check(self) -> None:
        """The exception above must not become a way to label anything defeating."""
        for name, entry in _entries():
            if entry["polarity"] != "defeating" or entry["expected_validity"] != "VALID":
                continue
            with self.subTest(file=name, entry=entry["id"]):
                self.assertIn(SEMANTIC_MARKER, entry,
                              f"{entry['id']} is defeating and schema-valid but names no check")


class EdgeVocabulary(unittest.TestCase):
    """The charter and the contract must agree on what a direct relation is."""

    def _schema_edges(self) -> list[str]:
        schema = json.loads((CONTRACTS / "relation-inference.schema.json").read_text("utf-8"))
        return list(schema["$defs"]["edge"]["enum"])

    def test_every_edge_the_schema_enforces_appears_in_the_charter(self) -> None:
        for edge in self._schema_edges():
            with self.subTest(edge=edge):
                self.assertIn(edge, CHARTER,
                              f"{edge} is enforced by the contract and undocumented in CHARTER.md")

    def test_the_charter_documents_no_edge_the_schema_omits(self) -> None:
        # An edge name always carries an internal underscore, which keeps document names
        # like KNOWN-GAPS.md and AI-NATIVE.md out of the comparison.
        documented = set(re.findall(r"\b[A-Z]{2,}_[A-Z_]+\b", CHARTER))
        enforced = set(self._schema_edges())
        refusals = {code for entry in MANIFEST["operations"] for code in entry["refusals"]}
        vocabulary = enforced | refusals | {"DIRECT", "INDEPENDENT", "UNDETERMINED", "COMPLETE",
                                            "INCOMPLETE", "REPRODUCED", "DISSENTED", "BUILT",
                                            "WITNESSED", "PROPOSED", "RATIFIED", "SYSTEM",
                                            "OBSERVATION", "CHARTER", "SPEC", "PROD"}
        stray = {word for word in documented if word not in vocabulary}
        self.assertEqual(set(), stray,
                         f"CHARTER.md names {sorted(stray)} in edge-shaped case; either the "
                         f"contract should enforce them or the charter should not imply them")

    def test_the_examination_must_cover_the_whole_set(self) -> None:
        """A narrowed examination reaches INDEPENDENT by not looking."""
        schema = json.loads((CONTRACTS / "relation-inference.schema.json").read_text("utf-8"))
        self.assertEqual(len(self._schema_edges()),
                         schema["properties"]["edges_examined"]["minItems"])


class ManifestAgreement(unittest.TestCase):
    """The contracts on disk are the ones the manifest's operations claim to act on."""

    def test_every_refusal_a_fixture_relies_on_is_declared_by_an_operation(self) -> None:
        declared = {code for entry in MANIFEST["operations"] for code in entry["refusals"]}
        for expected in ("OBSERVER_NOT_INDEPENDENT", "RELATION_UNDETERMINED", "RUN_NOT_TERMINAL"):
            with self.subTest(refusal=expected):
                self.assertIn(expected, declared)

    def test_the_service_declares_the_records_these_contracts_describe(self) -> None:
        for record in ("relation-inference", "observation-request"):
            with self.subTest(record=record):
                self.assertIn(record, MANIFEST["owns"])


if __name__ == "__main__":
    unittest.main()
