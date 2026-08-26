from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovkernel.jsonschema import validate  # noqa: E402


class Rfc3339ProfileTests(unittest.TestCase):
    schema = {"type": "string", "format": "date-time"}

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
        ):
            with self.subTest(value=value):
                self.assertTrue(validate(value, self.schema))


if __name__ == "__main__":
    unittest.main()
