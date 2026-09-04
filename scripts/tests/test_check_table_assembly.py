"""No declared check group may fall out of the table the runner actually reads.

`sovverify/__init__.py` assembles `CHECKS` so the two machinery-integrity guards
cannot be removed by the path they grade. It used to assemble it by naming each
group, which meant a group added to `checks.py` was dropped from every run while
`checks.py` still read as though it composed the table. Five projection checks
were lost exactly that way, and the only symptom was a count that disagreed with
the orientation page.
"""

from __future__ import annotations

from pathlib import Path
import ast
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sovverify  # noqa: E402,F401  imported for the assembly side effect
from sovverify.checks import CHECKS  # noqa: E402

PACKAGE = ROOT / "scripts" / "sovverify"


def declared_groups() -> dict[str, int]:
    """Every module-level `*_CHECKS` tuple in the package, by source rather than import.

    Reading the source is the point: importing the package is what performs the
    assembly under test, so a reader that asked the package what it declares
    would be asking the thing that could have dropped a group.
    """
    groups: dict[str, int] = {}
    for path in sorted(PACKAGE.glob("*.py")):
        tree = ast.parse(path.read_bytes().decode("utf-8"))
        for node in tree.body:
            if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Tuple):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.endswith("_CHECKS"):
                    groups[f"{path.name}:{target.id}"] = len(node.value.elts)
    return groups


class EveryDeclaredGroupReachesTheRunner(unittest.TestCase):

    def test_the_package_declares_more_than_one_group(self) -> None:
        """A one-group reading would pass this file while proving nothing."""
        self.assertGreater(len(declared_groups()), 1)

    def test_the_table_holds_exactly_the_declared_entries(self) -> None:
        declared = sum(declared_groups().values())
        self.assertEqual(len(CHECKS), declared)

    def test_the_projection_group_is_in_the_table(self) -> None:
        """The group whose loss this test exists to catch."""
        from sovverify.projections import PROJECTION_CHECKS

        names = {check.name for check in CHECKS}
        for check in PROJECTION_CHECKS:
            with self.subTest(check=check.name):
                self.assertIn(check.name, names)

    def test_the_integrity_guards_survive_the_assembly(self) -> None:
        from sovverify.integrity import INTEGRITY_CHECKS

        names = {check.name for check in CHECKS}
        for check in INTEGRITY_CHECKS:
            with self.subTest(check=check.name):
                self.assertIn(check.name, names)

    def test_the_participant_group_stays_at_the_tail(self) -> None:
        """The assembly splices ahead of this tail; a moved tail would misplace the guards."""
        from sovverify.participants import PARTICIPANT_CHECKS

        tail = [check.name for check in CHECKS][-len(PARTICIPANT_CHECKS):]
        self.assertEqual(tail, [check.name for check in PARTICIPANT_CHECKS])

    def test_no_check_name_is_declared_twice(self) -> None:
        names = [check.name for check in CHECKS]
        self.assertEqual(sorted(names), sorted(set(names)))


if __name__ == "__main__":
    unittest.main()
