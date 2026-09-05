"""The commissioning instrument must tell "nothing omitted" from "omissions undeclared".

The first thin circuit (`reports/2026-09-05-thin-circuit-1.md` (eff1a68), fizzle 2) produced a
RecordProjection with `omissions: []` and `check_q22` graded it as missing the field, because an
empty list was read as absent. `SPEC.md` `RecordProjection` says an empty omission list is an
explicit claim that no class was withheld. These cases pin that reading and keep every other
Q2.2 defect firing.
"""

from __future__ import annotations

from pathlib import Path
import copy
import importlib.util
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures/commissioning/qualification-cases.json"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


commissioning = _load("commissioning")


def observed() -> dict:
    template = json.loads(FIXTURE.read_text(encoding="utf-8"))["templates"]["P15-Q2.2"]
    return copy.deepcopy(template)


class Q22OmissionsAreDeclaredNotCounted(unittest.TestCase):
    def test_the_fixture_template_passes(self) -> None:
        self.assertEqual([], commissioning.check_q22(observed()))

    def test_an_empty_omission_list_is_a_declaration(self) -> None:
        case = observed()
        case["projection"]["omissions"] = []
        self.assertEqual([], commissioning.check_q22(case))

    def test_an_absent_omission_field_is_a_defect(self) -> None:
        case = observed()
        del case["projection"]["omissions"]
        self.assertEqual(["RecordProjection missing omissions"], commissioning.check_q22(case))

    def test_a_null_omission_field_is_a_defect(self) -> None:
        case = observed()
        case["projection"]["omissions"] = None
        self.assertEqual(["RecordProjection missing omissions"], commissioning.check_q22(case))

    def test_a_non_list_omission_field_is_a_defect(self) -> None:
        case = observed()
        case["projection"]["omissions"] = "none"
        self.assertEqual(["RecordProjection missing omissions"], commissioning.check_q22(case))

    def test_every_other_required_field_still_fires_when_absent(self) -> None:
        for field in ("projection_id", "subject_addresses", "recipient_relation", "as_of",
                      "included_records", "projection_digest"):
            with self.subTest(field=field):
                case = observed()
                del case["projection"][field]
                self.assertEqual([f"RecordProjection missing {field}"],
                                 commissioning.check_q22(case))

    def test_an_empty_included_records_list_is_still_missing_evidence(self) -> None:
        case = observed()
        case["projection"]["included_records"] = []
        self.assertEqual(["RecordProjection missing included_records"],
                         commissioning.check_q22(case))

    def test_authority_and_reconstruction_defects_still_fire(self) -> None:
        case = observed()
        case["projection"]["authority_effect"] = "GRANTED"
        case["reconstructable"] = False
        self.assertEqual(["RecordProjection changed authority",
                          "RecordProjection cannot be reconstructed"],
                         commissioning.check_q22(case))


if __name__ == "__main__":
    unittest.main()
