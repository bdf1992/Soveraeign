"""A declared custody closure check must be a command that actually dispatches.

Most cases here are ones an independent witness drove against the first version
of this reader, which resolved a path and searched for a substring. It reported
twenty-one closure checks runnable while seven of them exited 2 into a usage
message.
"""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_closure_checks as closure_checks  # noqa: E402
from sovcheckrun import dispatch, resolve  # noqa: E402

MUTE = "python scripts/sovcheckrun/fixtures/mute_docstring_guard.py"


def custody(expression: str | None, judgement_seat: str | None = "seat:root") -> dict:
    check = None if expression is None else {"kind": "COMMAND", "expression": expression}
    return {
        "custody_id": "custody:fixture/under-test",
        "closure": {"check": check, "judgement_seat": judgement_seat,
                    "defeated_by": "the fixture stops discriminating"},
    }


def codes(record: dict) -> list[str]:
    return [defect["code"] for defect in closure_checks.grade_check(record)]


class DeclaredRefusals(unittest.TestCase):

    def test_a_command_that_reaches_its_parser_is_admitted(self) -> None:
        self.assertEqual(codes(custody("python scripts/sov_closure_checks.py check")), [])

    def test_a_module_with_no_entry_point_is_mute(self) -> None:
        self.assertEqual(codes(custody(MUTE)), ["CLOSURE_CHECK_MUTE"])

    def test_the_phase_1_5_opening_defect_is_caught(self) -> None:
        """The exact expression the Phase 1.5 opening act declared for P15-X4."""
        self.assertEqual(codes(custody("python conformance/commissioning.py")),
                         ["CLOSURE_CHECK_MUTE"])

    def test_a_removed_subcommand_is_refused(self) -> None:
        """The finding that defeated the first reader: it exits 2, and read as runnable."""
        self.assertEqual(codes(custody("python scripts/sov_node.py admit --session current")),
                         ["CLOSURE_CHECK_REJECTED"])

    def test_a_removed_flag_is_refused(self) -> None:
        self.assertEqual(codes(custody("python conformance/run.py --scenario RUN-I9-BYOM")),
                         ["CLOSURE_CHECK_REJECTED"])

    def test_a_package_not_on_the_path_is_refused(self) -> None:
        self.assertEqual(
            codes(custody("python -m soveraeign_record_service.cli --root x verify")),
            ["CLOSURE_CHECK_UNIMPORTABLE"])

    def test_a_missing_target_is_refused(self) -> None:
        self.assertEqual(codes(custody("python scripts/sov_no_such_reader.py")),
                         ["CLOSURE_CHECK_TARGET_MISSING"])

    def test_a_non_python_expression_is_refused(self) -> None:
        self.assertEqual(codes(custody("make closure")), ["CLOSURE_CHECK_NOT_PYTHON"])

    def test_an_unbalanced_expression_is_refused(self) -> None:
        self.assertEqual(codes(custody('python "scripts/sov_closure_checks.py')),
                         ["CLOSURE_CHECK_UNPARSEABLE"])

    def test_a_custody_with_no_check_and_no_seat_can_never_close(self) -> None:
        self.assertEqual(codes(custody(None, judgement_seat=None)),
                         ["CLOSURE_CHECK_UNSETTLEABLE"])

    def test_a_seat_settles_what_no_command_can(self) -> None:
        self.assertEqual(codes(custody(None)), [])


class CompoundExpressions(unittest.TestCase):
    """Chaining hid the mute stage behind a passing one, in every operator form."""

    def test_and_chaining_is_refused(self) -> None:
        expression = f"python scripts/sov_closure_checks.py check && {MUTE}"
        self.assertEqual(codes(custody(expression)), ["CLOSURE_CHECK_COMPOUND"])

    def test_semicolon_chaining_is_refused(self) -> None:
        expression = f"python scripts/sov_closure_checks.py check ; {MUTE}"
        self.assertEqual(codes(custody(expression)), ["CLOSURE_CHECK_COMPOUND"])

    def test_a_pipe_is_refused(self) -> None:
        """`... | grep FAIL` is the shape that turns a refusal into a zero exit."""
        self.assertEqual(codes(custody("python scripts/sov_f2_gate.py | grep FAIL")),
                         ["CLOSURE_CHECK_COMPOUND"])


class EntryPointDetection(unittest.TestCase):
    """The substring test was fooled in both directions; this one is parsed."""

    def test_a_guard_only_in_a_docstring_is_not_an_entry_point(self) -> None:
        fixture = ROOT / "scripts/sovcheckrun/fixtures/mute_docstring_guard.py"
        self.assertIn('__name__ == "__main__"', fixture.read_text(encoding="utf-8"))
        self.assertFalse(resolve.has_entry_point(fixture))

    def test_a_single_quoted_guard_is_an_entry_point(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "single.py"
            path.write_text("if __name__ == '__main__':\n    print('run')\n", encoding="utf-8")
            self.assertTrue(resolve.has_entry_point(path))

    def test_this_reader_has_an_entry_point(self) -> None:
        self.assertTrue(resolve.has_entry_point(ROOT / "scripts/sov_closure_checks.py"))


class InvocationShapes(unittest.TestCase):
    """Forms the schema's COMMAND kind admits that the first reader turned away."""

    def test_a_leading_environment_assignment_is_part_of_the_invocation(self) -> None:
        target = resolve.resolve(ROOT, "PYTHONPATH=services/record/src python -m pkg.cli verify")
        self.assertEqual(target.mode, "module")
        self.assertEqual(target.target, "pkg.cli")

    def test_a_versioned_interpreter_is_accepted(self) -> None:
        target = resolve.resolve(ROOT, "python3.11 scripts/sov_closure_checks.py check")
        self.assertEqual(target.refusal, "")

    def test_env_is_accepted(self) -> None:
        target = resolve.resolve(ROOT, "env FOO=1 python scripts/sov_closure_checks.py check")
        self.assertEqual(target.refusal, "")


class ModuleResolution(unittest.TestCase):

    def test_an_ambiguous_dotted_name_is_refused_rather_than_guessed(self) -> None:
        """`-m cli` matched three files; picking the first was a decision to make."""
        self.assertGreater(len(resolve.module_paths(ROOT, "cli")), 1)
        self.assertEqual(codes(custody("python -m cli")), ["CLOSURE_CHECK_AMBIGUOUS"])

    def test_a_package_serves_m_only_through_its_main_module(self) -> None:
        """`python -m pkg` needs pkg/__main__.py; an __init__.py does not run."""
        self.assertEqual(resolve.module_paths(ROOT, "sovcheckrun"), [])

    def test_an_absent_package_does_not_resolve(self) -> None:
        self.assertEqual(resolve.module_paths(ROOT, "soveraeign_no_such_service.cli"), [])


class DispatchProbeStopsBeforeTheBody(unittest.TestCase):

    def test_the_probe_reports_a_parse_without_running_the_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / "ran"
            script = Path(tmp) / "cli.py"
            script.write_text(
                "import argparse, pathlib, sys\n"
                "p = argparse.ArgumentParser()\n"
                "p.add_argument('name')\n"
                "a = p.parse_args()\n"
                f"pathlib.Path({str(marker)!r}).write_text('body ran')\n",
                encoding="utf-8")
            code, _ = dispatch.probe(Path(tmp), "path", "cli.py", ["value"])
            self.assertEqual(code, dispatch.PARSED)
            self.assertFalse(marker.exists(), "the command body must not run")

    def test_the_probe_reports_a_rejected_argument(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "cli.py"
            script.write_text(
                "import argparse\n"
                "p = argparse.ArgumentParser()\n"
                "p.add_subparsers(dest='c', required=True).add_parser('known')\n"
                "p.parse_args()\n", encoding="utf-8")
            code, message = dispatch.probe(Path(tmp), "path", "cli.py", ["gone"])
            self.assertEqual(code, dispatch.REJECTED)
            self.assertIn("invalid choice", message)


class CarriedDebt(unittest.TestCase):
    """The debt list is evidence, and it must not outlive the breakage it records."""

    def test_the_checked_in_collections_carry_no_unattributed_failure(self) -> None:
        refusals, _ = closure_checks.grade()
        self.assertEqual(refusals, [])

    def test_every_carried_entry_still_fails(self) -> None:
        _, debt = closure_checks.grade()
        carried = closure_checks.debt_contract()["debt"]
        self.assertEqual(len(debt), len(carried))

    def test_every_carried_entry_names_a_declared_custody(self) -> None:
        from sovcustody import model as custody_model

        declared = {str(row.get("custody_id")) for row in custody_model.custodies()}
        for entry in closure_checks.debt_contract()["debt"]:
            with self.subTest(custody=entry["custody_id"]):
                self.assertIn(entry["custody_id"], declared)

    def test_every_carried_entry_names_a_seat_that_can_repair_it(self) -> None:
        for entry in closure_checks.debt_contract()["debt"]:
            with self.subTest(custody=entry["custody_id"]):
                self.assertTrue(entry.get("repair_seat"))
                self.assertTrue(entry.get("repair"))
                self.assertTrue(entry.get("observed"))

    def test_a_repaired_entry_left_on_the_list_is_refused(self) -> None:
        """The list must not outlive the breakage: a healed entry fails here."""
        working = "python scripts/sov_closure_checks.py check"
        record = custody(working)
        record["custody_id"] = "custody:fixture/healed"
        refusals, _ = closure_checks.grade(
            [record], entries=[{"custody_id": "custody:fixture/healed",
                                "expression": working}])
        self.assertEqual([d["code"] for d in refusals], ["CLOSURE_CHECK_DEBT_REPAIRED"])

    def test_an_entry_naming_no_declared_custody_is_refused(self) -> None:
        refusals, _ = closure_checks.grade(
            [], entries=[{"custody_id": "custody:fixture/vanished",
                          "expression": "python scripts/gone.py"}])
        self.assertEqual([d["code"] for d in refusals], ["CLOSURE_CHECK_DEBT_UNKNOWN"])

    def test_a_repointed_expression_leaves_its_entry_unknown(self) -> None:
        """Repointing a checked expression must not silently keep its debt cover."""
        record = custody("python scripts/sov_closure_checks.py check")
        record["custody_id"] = "custody:fixture/repointed"
        refusals, _ = closure_checks.grade(
            [record], entries=[{"custody_id": "custody:fixture/repointed",
                                "expression": "python scripts/old_name.py"}])
        self.assertEqual([d["code"] for d in refusals], ["CLOSURE_CHECK_DEBT_UNKNOWN"])


class DeclaredRefusalsAreWired(unittest.TestCase):

    def test_every_declared_refusal_has_a_firing_fixture(self) -> None:
        exercised = {expected for expected, _ in closure_checks._fixtures()}
        self.assertEqual(set(closure_checks.REFUSALS), exercised)

    def test_a_kind_this_reader_does_not_drive_is_counted_not_skipped(self) -> None:
        """Three of the schema's four kinds are not commands; silence would hide them."""
        census = closure_checks._kind_census([
            {"closure": {"check": {"kind": "STAGE_REACHED", "expression": "CAPABLE_NODE"}}},
            {"closure": {"check": None, "judgement_seat": "seat:root"}},
        ])
        self.assertEqual(census, {"STAGE_REACHED": 1, "NONE (settled by a seat)": 1})


if __name__ == "__main__":
    unittest.main()
