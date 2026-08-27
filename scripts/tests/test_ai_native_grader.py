"""Prove the AI-native grader derives its verdict and cannot be told one.

`scripts/sov_ainative.py selfcheck` grades the declared corpus in
`conformance/fixtures/ai-native/assessment-cases.json`, where every refusal the table
declares fires at least once. This module proves the half the corpus cannot: that the
record shape has no verdict field to set, that the table is read as data rather than
restated by the evaluator, that the reviewer check actually consults the principal
registry, and that every recorded assessment still grades.

Passing establishes `BUILT` for the table, the shape and the grader. It witnesses nothing:
the participant that wrote them also wrote this module.
"""

from __future__ import annotations

from pathlib import Path
import copy
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_ainative  # noqa: E402
from sovainative import standard  # noqa: E402
from sovainative.grade import grade  # noqa: E402
from sovkernel import jsonschema  # noqa: E402
from sovsession import principals  # noqa: E402

TABLE = standard.load_table()
SCHEMA = json.loads(standard.SCHEMA.read_text("utf-8"))
CORPUS = json.loads(standard.CORPUS.read_text("utf-8"))
PRINCIPAL_SCHEMA = json.loads(
    (ROOT / "contracts" / "principal.schema.json").read_text("utf-8"))


def _positive() -> dict:
    """The corpus case that earns the target bar, as a working copy."""
    return copy.deepcopy(
        next(c for c in CORPUS if c["id"] == "AINAT-POS-QUALIFIED")["record"])


class DeclaredCorpus(unittest.TestCase):
    """The corpus grades exactly as it declares."""

    def test_selfcheck_reports_no_failure(self) -> None:
        self.assertEqual(sov_ainative.selfcheck(), [])

    def test_every_declared_refusal_has_a_case(self) -> None:
        expected = {code for case in CORPUS for code in case["expected"]["defects"]}
        self.assertEqual(set(TABLE["refusals"]) - expected, set())


class VerdictIsDerived(unittest.TestCase):
    """The verdict is computed from the scores and is not a field anyone can set."""

    def test_shape_declares_no_verdict_property(self) -> None:
        self.assertNotIn("verdict", SCHEMA["properties"])

    def test_a_stated_verdict_is_refused(self) -> None:
        record = _positive()
        record["verdict"] = "SOVERAEIGN_QUALIFIED"
        result = grade(record, TABLE, SCHEMA, {}, None)
        self.assertEqual([d["code"] for d in result["defects"]], ["VERDICT_DECLARED"])
        self.assertIsNone(result["verdict"])

    def test_dropping_one_qualification_drops_the_bar(self) -> None:
        record = _positive()
        record["qualifications"]["effect_honesty"]["result"] = "UNPROVEN"
        record["qualifications"]["effect_honesty"]["evidence"] = []
        result = grade(record, TABLE, SCHEMA, {}, _registry())
        self.assertEqual(result["verdict"], "AI_NATIVE")
        self.assertIn("effect_honesty is not PASS", result["held_by"])

    def test_an_axis_short_of_full_holds_the_bar(self) -> None:
        record = _positive()
        record["axes"]["retraction"]["score"] = "PARTIAL"
        result = grade(record, TABLE, SCHEMA, {}, _registry())
        self.assertEqual(result["verdict"], "AI_NATIVE")
        self.assertIn("retraction is not FULL", result["held_by"])


def _registry() -> dict:
    """The node's principal registry, which the reviewer check resolves against."""
    registry, reason = principals.load(ROOT)
    if registry is None:
        raise AssertionError(reason)
    return registry


class ReviewerIsResolved(unittest.TestCase):
    """The substantive-operation judgement is a human judgement the node can attribute."""

    def test_registry_validates_and_every_chain_reaches_the_root(self) -> None:
        registry = _registry()
        self.assertEqual(
            jsonschema.validate(registry, PRINCIPAL_SCHEMA, PRINCIPAL_SCHEMA), [])
        for entry in registry["principals"]:
            _, defects = principals.chain(registry, entry["principal_id"])
            self.assertEqual(defects, [], entry["principal_id"])

    def test_a_model_principal_cannot_make_the_judgement(self) -> None:
        registry = _registry()
        model = next(p["principal_id"] for p in registry["principals"]
                     if p["kind"] == "MODEL")
        record = _positive()
        record["earn_it"]["reviewer"] = model
        result = grade(record, TABLE, SCHEMA, {}, registry)
        self.assertEqual([d["code"] for d in result["defects"]], ["REVIEWER_NOT_HUMAN"])

    def test_the_root_principal_can(self) -> None:
        registry = _registry()
        record = _positive()
        record["earn_it"]["reviewer"] = registry["root_principal"]
        self.assertEqual(grade(record, TABLE, SCHEMA, {}, registry)["defects"], [])


class TableIsData(unittest.TestCase):
    """The evaluator reads the compiled standard rather than restating it."""

    def test_scenario_status_is_read_from_the_scenario_files(self) -> None:
        statuses = standard.scenario_status(ROOT, TABLE)
        declared = {c for entry in TABLE["qualifications"].values()
                    for c in entry["evidenced_by"]}
        self.assertEqual(declared - set(statuses), set(),
                         "a qualification cites a founding scenario that does not exist")

    def test_no_cited_scenario_is_executable_yet(self) -> None:
        statuses = standard.scenario_status(ROOT, TABLE)
        executable = set(TABLE["executable_scenario_status"])
        ready = sorted(i for i, s in statuses.items() if s in executable)
        self.assertEqual(ready, [], "a scenario became executable; the assessments that "
                                    "cite it may now claim evidence they could not before")

    def test_narrowing_the_executable_status_changes_nothing_silently(self) -> None:
        table = copy.deepcopy(TABLE)
        table["executable_scenario_status"] = ["SEED"]
        record = _positive()
        record["qualifications"]["two_binding_proof"]["evidence"] = [
            {"kind": "scenario", "reference": "FOUND-006", "observed": "as written"}]
        statuses = standard.scenario_status(ROOT, table)
        self.assertEqual(grade(record, table, SCHEMA, statuses, _registry())["defects"], [])


class RecordedAssessments(unittest.TestCase):
    """Every assessment kept in the repository still grades against the current standard."""

    def test_each_recorded_assessment_is_free_of_defects(self) -> None:
        table, schema, statuses, registry = standard.context()
        for path in sorted(standard.ASSESSMENTS.glob("*.json")):
            with self.subTest(assessment=path.name):
                result = grade(standard.read(path), table, schema, statuses, registry)
                self.assertEqual(result["defects"], [])

    def test_at_least_one_assessment_is_recorded(self) -> None:
        self.assertTrue(sorted(standard.ASSESSMENTS.glob("*.json")))


if __name__ == "__main__":
    unittest.main()
