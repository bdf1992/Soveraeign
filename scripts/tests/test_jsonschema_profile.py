from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovkernel.jsonschema import DIALECT, validate  # noqa: E402


class Rfc3339ProfileTests(unittest.TestCase):
    schema = {"$schema": DIALECT, "type": "string", "format": "date-time"}

    def test_declared_machine_instants_pass(self) -> None:
        for value in (
            "2026-08-26T05:21:20Z",
            "2026-08-26T05:21:20.123456Z",
            "2026-08-26T00:21:20-05:00",
            "2026-08-26T10:51:20+05:30",
        ):
            with self.subTest(value=value):
                self.assertEqual(validate(value, self.schema), [])

    def test_python_iso_extensions_do_not_become_protocol(self) -> None:
        for value in (
            "2026-08-26 05:21:20+00:00",
            "20260826T052120+00:00",
            "2026-08-26t05:21:20+00:00",
            "2026-08-26T05:21:20z",
            "2026-08-26T05:21:20",
        ):
            with self.subTest(value=value):
                self.assertTrue(validate(value, self.schema))

    def test_unknown_offset_and_unrepresentable_values_are_refused(self) -> None:
        for value in (
            "2026-08-26T05:21:20-00:00",
            "2026-08-26T05:21:60Z",
            "2026-02-30T05:21:20Z",
            "2026-08-26T05:21:20+24:00",
            "2026-08-26T05:21:20+05:60",
            "2026-08-26T05:21:20-05:60",
        ):
            with self.subTest(value=value):
                self.assertTrue(validate(value, self.schema))


class DialectAndReferenceTests(unittest.TestCase):
    def test_top_level_dialect_is_exact(self) -> None:
        for schema in (
            {"type": "string"},
            {"$schema": "http://json-schema.org/draft-07/schema#", "type": "string"},
        ):
            with self.subTest(schema=schema):
                self.assertTrue(validate("value", schema))

    def test_explicit_root_cannot_bypass_dialect(self) -> None:
        schema = {"type": "string"}
        self.assertTrue(validate("value", schema, schema, "/"))

    def test_ref_siblings_are_applied(self) -> None:
        schema = {
            "$schema": DIALECT,
            "$defs": {"text": {"type": "string"}},
            "$ref": "#/$defs/text",
            "minLength": 3,
        }
        self.assertTrue(validate("x", schema))
        self.assertEqual(validate("long", schema), [])


if __name__ == "__main__":
    unittest.main()
