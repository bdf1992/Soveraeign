"""A declared custody closure check must be a command somebody can actually run."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_closure_checks as closure_checks  # noqa: E402


def custody(expression: str | None, judgement_seat: str | None = "seat:root") -> dict:
    """One custody carrying exactly the closure route under test."""
    check = None if expression is None else {"kind": "COMMAND", "expression": expression}
    return {
        "custody_id": "custody:fixture/under-test",
        "closure": {"check": check, "judgement_seat": judgement_seat,
                    "defeated_by": "the fixture stops discriminating"},
    }


def codes(record: dict) -> list[str]:
    return [defect["code"] for defect in closure_checks.grade_check(record)]


class ClosureCheckResolution(unittest.TestCase):
    """The refusals the module declares, one case each."""

    def test_a_runnable_script_is_admitted(self) -> None:
        self.assertEqual(codes(custody("python scripts/sov_closure_checks.py check")), [])

    def test_a_module_with_no_entry_point_is_mute(self) -> None:
        self.assertEqual(codes(custody("python scripts/sovverify/shape.py")),
                         ["CLOSURE_CHECK_MUTE"])

    def test_the_phase_1_5_opening_defect_is_caught(self) -> None:
        """The exact expression the Phase 1.5 opening act declared for P15-X4.

        It resolved, exited 0, and printed nothing, so the clause read closed
        because its check could not speak.
        """
        self.assertEqual(codes(custody("python conformance/commissioning.py")),
                         ["CLOSURE_CHECK_MUTE"])

    def test_a_missing_target_is_refused(self) -> None:
        self.assertEqual(codes(custody("python scripts/sov_no_such_reader.py")),
                         ["CLOSURE_CHECK_TARGET_MISSING"])

    def test_a_non_python_expression_is_unresolved(self) -> None:
        self.assertEqual(codes(custody("make closure")), ["CLOSURE_CHECK_UNRESOLVED"])

    def test_an_unbalanced_expression_is_unresolved(self) -> None:
        self.assertEqual(codes(custody('python "scripts/sov_closure_checks.py')),
                         ["CLOSURE_CHECK_UNRESOLVED"])

    def test_a_custody_with_no_check_and_no_seat_can_never_close(self) -> None:
        self.assertEqual(codes(custody(None, judgement_seat=None)),
                         ["CLOSURE_CHECK_UNSETTLEABLE"])

    def test_a_seat_settles_what_no_command_can(self) -> None:
        self.assertEqual(codes(custody(None)), [])


class ModuleFormResolution(unittest.TestCase):
    """`python -m` must resolve wherever the repository lays the package out."""

    def test_a_service_package_under_src_resolves(self) -> None:
        found = closure_checks._module_path("soveraeign_record_service.cli")
        self.assertIsNotNone(found)
        self.assertEqual(found.relative_to(ROOT).as_posix(),
                         "services/record/src/soveraeign_record_service/cli.py")

    def test_an_absent_package_does_not_resolve(self) -> None:
        self.assertIsNone(closure_checks._module_path("soveraeign_no_such_service.cli"))

    def test_a_module_expression_grades_through_the_same_route(self) -> None:
        self.assertEqual(codes(custody("python -m soveraeign_no_such_service.cli verify")),
                         ["CLOSURE_CHECK_TARGET_MISSING"])


class DeclaredRefusalsAreWired(unittest.TestCase):
    """A refusal named in the module docstring but never fired is a claim, not a check."""

    def test_every_declared_refusal_has_a_firing_fixture(self) -> None:
        exercised = {expected for expected, _ in closure_checks._fixtures()}
        self.assertEqual(set(closure_checks.REFUSALS), exercised)

    def test_the_checked_in_collections_carry_no_unrunnable_check(self) -> None:
        self.assertEqual(closure_checks.grade(), [])


if __name__ == "__main__":
    unittest.main()
