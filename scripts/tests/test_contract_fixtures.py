"""Execute the contract fixture pairs under ``contracts/fixtures/``.

Each ``*.fixtures.json`` file lists entries that name a contract under ``contracts/``
and a record with a declared ``expected_validity``. This module validates every record
with the bounded Draft 2020-12 validator and asserts the declaration, so a defeating
fixture is shown to defeat rather than merely declared to. A file that does not carry
one positive and one defeating entry for every contract it names fails outright; a
schema with only a positive case proves nothing about what it refuses.

Some records defeat a contract semantically while remaining schema-valid: a seat
graph that cycles, an owner chain with two roots. JSON Schema cannot express those,
so such an entry declares ``expected_validity: VALID`` alongside a further
``expected_*`` field naming the check that does catch it. That combination is
admitted here only when the entry states both that field and what it defeats, so
the gap in the schema is recorded rather than silently tolerated.

A passing run establishes at most ``BUILT`` for the fixture pair; it does not witness or
ratify the contract.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovkernel.jsonschema import validate  # noqa: E402

CONTRACTS = ROOT / "contracts"
FIXTURES = CONTRACTS / "fixtures"
REQUIRED_KEYS = ("id", "contract", "polarity", "expected_validity", "record")
POLARITY_BY_VALIDITY = {"VALID": "positive", "INVALID": "defeating"}
# A schema-valid record can still defeat the contract semantically. Such an entry must
# name the check that catches it, so the schema's blind spot is stated, not implied.
SEMANTIC_MARKER = "expected_"
# Defects of these shapes mean the validator could not check the constraint at all; an
# INVALID verdict built on them would let a defeating fixture pass for the wrong reason.
UNCHECKABLE_MARKERS = ("unsupported", "unresolvable")


def _load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        try:
            return json.load(handle)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path.relative_to(ROOT)}: not valid JSON ({exc})") from exc


def _fixture_files() -> list[Path]:
    return sorted(FIXTURES.glob("*.fixtures.json"))


def _observed_validity(record: Any, schema: Any) -> tuple[str, list[str]]:
    """Validate ``record`` and report VALID iff the validator found no defect."""
    defects = validate(record, schema)
    return ("VALID" if not defects else "INVALID"), defects


class ContractFixtureTests(unittest.TestCase):
    """Run every fixture entry against the contract it names."""

    def test_fixture_directory_is_not_vacuous(self) -> None:
        self.assertTrue(_fixture_files(), f"no *.fixtures.json under {FIXTURES}")

    def test_entries_are_well_formed(self) -> None:
        for path in _fixture_files():
            entries = _load_json(path)
            with self.subTest(file=path.name):
                self.assertIsInstance(entries, list, "fixture file must be a JSON array")
            for index, entry in enumerate(entries):
                with self.subTest(file=path.name, index=index):
                    self.assertIsInstance(entry, dict)
                    for key in REQUIRED_KEYS:
                        self.assertIn(key, entry, f"entry lacks {key!r}")
                    self.assertIn(entry["expected_validity"], POLARITY_BY_VALIDITY)
                    expected = POLARITY_BY_VALIDITY[entry["expected_validity"]]
                    if entry["polarity"] == expected:
                        pass
                    elif entry["polarity"] == "defeating":
                        self._assert_semantic_defeat_is_declared(entry)
                    else:
                        self.fail(
                            f"{entry['id']}: polarity {entry['polarity']!r} disagrees with "
                            f"expected_validity {entry['expected_validity']!r}"
                        )
                    contract = CONTRACTS / entry["contract"]
                    self.assertEqual(
                        contract.parent, CONTRACTS, "contract must be a bare file name"
                    )
                    self.assertTrue(contract.is_file(), f"missing contract {entry['contract']}")

    def _assert_semantic_defeat_is_declared(self, entry: dict) -> None:
        """A defeating entry the schema accepts must name what does reject it."""
        checks = [
            key for key in entry
            if key.startswith(SEMANTIC_MARKER) and key != "expected_validity"
        ]
        self.assertTrue(
            checks,
            f"{entry['id']}: declared defeating but schema-valid, and names no "
            f"expected_* check that catches it",
        )
        self.assertTrue(
            str(entry.get("defeats", "")).strip(),
            f"{entry['id']}: a semantic defeat must say what it defeats",
        )
        for key in checks:
            self.assertIsNotNone(entry[key], f"{entry['id']}: {key} declares nothing")

    def test_a_schema_valid_defeating_entry_without_a_named_check_fails(self) -> None:
        """The exception above must not become a way to declare anything defeating."""
        with self.assertRaises(AssertionError):
            self._assert_semantic_defeat_is_declared(
                {"id": "SYNTHETIC", "polarity": "defeating", "expected_validity": "VALID",
                 "defeats": "nothing names the check"})

    def test_a_schema_valid_defeating_entry_without_a_reason_fails(self) -> None:
        with self.assertRaises(AssertionError):
            self._assert_semantic_defeat_is_declared(
                {"id": "SYNTHETIC", "polarity": "defeating", "expected_validity": "VALID",
                 "expected_rooted_tree": False})

    def test_a_schema_valid_defeating_entry_naming_a_check_is_admitted(self) -> None:
        self._assert_semantic_defeat_is_declared(
            {"id": "SYNTHETIC", "polarity": "defeating", "expected_validity": "VALID",
             "expected_rooted_tree": False, "defeats": "a cycle the schema cannot see"})

    def test_every_named_contract_has_a_positive_and_a_defeating_entry(self) -> None:
        for path in _fixture_files():
            seen: dict[str, set[str]] = {}
            for entry in _load_json(path):
                seen.setdefault(entry["contract"], set()).add(entry["expected_validity"])
            for contract, validities in sorted(seen.items()):
                with self.subTest(file=path.name, contract=contract):
                    self.assertEqual(
                        validities,
                        set(POLARITY_BY_VALIDITY),
                        f"{contract} needs one VALID and one INVALID entry",
                    )

    def test_each_record_meets_its_declared_validity(self) -> None:
        schemas: dict[str, Any] = {}
        for path in _fixture_files():
            for entry in _load_json(path):
                name = entry["contract"]
                with self.subTest(file=path.name, id=entry["id"]):
                    self.assertTrue((CONTRACTS / name).is_file(), f"missing contract {name}")
                    schema = schemas.setdefault(name, _load_json(CONTRACTS / name))
                    observed, defects = _observed_validity(entry["record"], schema)
                    uncheckable = [
                        d for d in defects if any(m in d for m in UNCHECKABLE_MARKERS)
                    ]
                    self.assertFalse(uncheckable, f"validator could not check: {uncheckable}")
                    self.assertEqual(
                        observed,
                        entry["expected_validity"],
                        f"{entry['id']} declared {entry['expected_validity']}; defects: {defects}",
                    )


if __name__ == "__main__":
    unittest.main()
