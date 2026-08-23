"""Execute the contract fixture pairs under ``contracts/fixtures/``.

Each ``*.fixtures.json`` file lists entries that name a contract under ``contracts/``
and a record with a declared ``expected_validity``. This module validates every record
with the bounded Draft 2020-12 validator and asserts the declaration, so a defeating
fixture is shown to defeat rather than merely declared to. A file that does not carry
one positive and one defeating entry for every contract it names fails outright; a
schema with only a positive case proves nothing about what it refuses.

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

from sovticket.jsonschema import validate  # noqa: E402

CONTRACTS = ROOT / "contracts"
FIXTURES = CONTRACTS / "fixtures"
REQUIRED_KEYS = ("id", "contract", "polarity", "expected_validity", "record")
POLARITY_BY_VALIDITY = {"VALID": "positive", "INVALID": "defeating"}
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
                    self.assertEqual(
                        entry["polarity"],
                        POLARITY_BY_VALIDITY[entry["expected_validity"]],
                        "polarity disagrees with expected_validity",
                    )
                    contract = CONTRACTS / entry["contract"]
                    self.assertEqual(
                        contract.parent, CONTRACTS, "contract must be a bare file name"
                    )
                    self.assertTrue(contract.is_file(), f"missing contract {entry['contract']}")

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
