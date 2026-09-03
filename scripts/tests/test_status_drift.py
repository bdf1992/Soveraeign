"""Checks for `scripts/sov_status_drift.py`: derivation from a fixture tree, and the
drift classification against a `STATUS.yaml`-shaped fragment.

This reporter never writes `STATUS.yaml`; these tests only prove what it reads and
what it prints, over a throwaway directory tree rather than the real `services/`.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import sov_status_drift  # noqa: E402


def make_service(root: Path, name: str, *, src_files=(), test_files=(), conformance_files=()) -> Path:
    """A `services/<name>/` directory carrying exactly the files named."""
    service_dir = root / "services" / name
    for rel, content in src_files:
        path = service_dir / "src" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    for rel, content in test_files:
        path = service_dir / "tests" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    for rel, content in conformance_files:
        path = service_dir / "conformance" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    if not (src_files or test_files or conformance_files):
        service_dir.mkdir(parents=True, exist_ok=True)
    return service_dir


class ReadStatusFields(unittest.TestCase):
    def test_reads_a_status_field(self):
        text = "gateway_service_status: CHARTERED_BOUNDARY_NOT_IMPLEMENTED\n"
        self.assertEqual(
            sov_status_drift.read_status_fields(text),
            {"gateway_service_status": "CHARTERED_BOUNDARY_NOT_IMPLEMENTED"},
        )

    def test_ignores_non_status_lines(self):
        text = "phase: phase:1-5\nasset_service_status: BUILT\n  indented_status: X\n"
        self.assertEqual(
            sov_status_drift.read_status_fields(text),
            {"asset_service_status": "BUILT"},
        )

    def test_last_duplicate_wins(self):
        text = "proofing_service_status: FIRST\nproofing_service_status: SECOND\n"
        self.assertEqual(
            sov_status_drift.read_status_fields(text),
            {"proofing_service_status": "SECOND"},
        )


class DeriveServiceState(unittest.TestCase):
    def test_empty_service_has_nothing(self):
        with TemporaryDirectory() as raw:
            root = Path(raw)
            service_dir = make_service(root, "empty")
            state = sov_status_drift.derive_service_state(service_dir)
            self.assertEqual(state, {"has_src": False, "has_tests": False, "has_conformance": False})

    def test_readme_only_src_does_not_count(self):
        with TemporaryDirectory() as raw:
            root = Path(raw)
            service_dir = make_service(root, "boundary", src_files=[("README.md", "boundary only\n")])
            state = sov_status_drift.derive_service_state(service_dir)
            self.assertFalse(state["has_src"])

    def test_a_real_module_counts_as_src(self):
        with TemporaryDirectory() as raw:
            root = Path(raw)
            service_dir = make_service(
                root, "built",
                src_files=[("pkg/core.py", "def f():\n    return 1\n")],
            )
            state = sov_status_drift.derive_service_state(service_dir)
            self.assertTrue(state["has_src"])

    def test_empty_test_file_does_not_count(self):
        with TemporaryDirectory() as raw:
            root = Path(raw)
            service_dir = make_service(root, "hollow", test_files=[("test_hollow.py", "")])
            state = sov_status_drift.derive_service_state(service_dir)
            self.assertFalse(state["has_tests"])

    def test_nonempty_test_file_counts(self):
        with TemporaryDirectory() as raw:
            root = Path(raw)
            service_dir = make_service(
                root, "covered",
                test_files=[("test_covered.py", "def test_it():\n    assert True\n")],
            )
            state = sov_status_drift.derive_service_state(service_dir)
            self.assertTrue(state["has_tests"])

    def test_conformance_fixtures_count(self):
        with TemporaryDirectory() as raw:
            root = Path(raw)
            service_dir = make_service(
                root, "proofed",
                conformance_files=[("001-case.yaml", "case: 1\n")],
            )
            state = sov_status_drift.derive_service_state(service_dir)
            self.assertTrue(state["has_conformance"])


class ClassifyDrift(unittest.TestCase):
    def test_built_but_stated_not_implemented_is_understated(self):
        derived = {"has_src": True, "has_tests": True, "has_conformance": False}
        self.assertEqual(
            sov_status_drift.classify_drift(derived, "CHARTERED_BOUNDARY_NOT_IMPLEMENTED"),
            "UNDERSTATED",
        )

    def test_unbuilt_but_stated_built_is_overstated(self):
        derived = {"has_src": False, "has_tests": False, "has_conformance": False}
        self.assertEqual(
            sov_status_drift.classify_drift(derived, "BUILT_SELF_TESTED_NOT_WITNESSED"),
            "OVERSTATED",
        )

    def test_agreement_is_not_drift(self):
        derived = {"has_src": True, "has_tests": True, "has_conformance": True}
        self.assertIsNone(
            sov_status_drift.classify_drift(derived, "BUILT_SELF_TESTED_NOT_WITNESSED"),
        )
        derived_unbuilt = {"has_src": False, "has_tests": False, "has_conformance": False}
        self.assertIsNone(
            sov_status_drift.classify_drift(derived_unbuilt, "CHARTERED_BOUNDARY_NOT_IMPLEMENTED"),
        )

    def test_no_status_field_is_not_drift(self):
        derived = {"has_src": True, "has_tests": True, "has_conformance": True}
        self.assertIsNone(sov_status_drift.classify_drift(derived, None))

    def test_partial_build_with_not_implemented_is_not_flagged(self):
        # src only, no tests yet: not "built" by this reporter's own bar, so a stated
        # NOT_IMPLEMENTED is not contradicted.
        derived = {"has_src": True, "has_tests": False, "has_conformance": False}
        self.assertIsNone(
            sov_status_drift.classify_drift(derived, "CHARTERED_BOUNDARY_NOT_IMPLEMENTED"),
        )


class CollectReport(unittest.TestCase):
    def test_finds_the_known_gateway_shaped_case(self):
        with TemporaryDirectory() as raw:
            root = Path(raw)
            services_dir = root / "services"
            make_service(
                root, "gateway",
                src_files=[("soveraeign_gateway_service/core.py", "class Core:\n    pass\n")],
                test_files=[("test_gateway_slice.py", "def test_it():\n    assert True\n")],
            )
            make_service(
                root, "asset",
                src_files=[("soveraeign_asset_service/core.py", "class Core:\n    pass\n")],
                test_files=[("test_walking_skeleton.py", "def test_it():\n    assert True\n")],
                conformance_files=[("BASELINE.md", "baseline\n")],
            )
            status_text = (
                "gateway_service_status: CHARTERED_BOUNDARY_NOT_IMPLEMENTED\n"
                "asset_service_status: BUILT_SELF_TESTED_NOT_WITNESSED\n"
            )
            rows = sov_status_drift.collect_report(services_dir, status_text)
            by_name = {row["service"]: row for row in rows}
            self.assertEqual(by_name["gateway"]["drift"], "UNDERSTATED")
            self.assertIsNone(by_name["asset"]["drift"])

    def test_missing_status_field_reports_none_not_a_crash(self):
        with TemporaryDirectory() as raw:
            root = Path(raw)
            services_dir = root / "services"
            make_service(root, "registry", src_files=[("core.py", "x = 1\n")])
            rows = sov_status_drift.collect_report(services_dir, "")
            self.assertEqual(rows[0]["status_value"], None)
            self.assertIsNone(rows[0]["drift"])


class CommandLine(unittest.TestCase):
    def test_check_exits_zero_even_with_drift(self):
        # Drift is the point of the report, not a failure: the command's own exit
        # code must stay 0 regardless of what it finds, only non-zero if it errors.
        self.assertEqual(sov_status_drift.main(["check"]), 0)

    def test_default_command_is_check(self):
        self.assertEqual(sov_status_drift.main([]), 0)


if __name__ == "__main__":
    unittest.main()
