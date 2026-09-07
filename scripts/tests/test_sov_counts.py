"""Tests for the counted-populations check.

The properties worth holding are the ones that decide whether this check can be
trusted to stay useful rather than merely stay green. A number word must parse to
the number it says. A scoped anchor must beat an unscoped one, because that is
what keeps `declared operations` inside `services/gateway/` meaning that
manifest. An unscoped anchor must not be caged by its population's scope, which
was this module's first defect and let a stale count of the Record Service's
operations sit ungraded outside `services/record/`. A subset qualifier must
suppress grading, because grading `the other fifteen declared operations` against
a manifest of seventeen reports a correct sentence as wrong. And a historical
exemption must stop applying the moment its stated value moves, or it covers
whatever is edited into its place.

The contract itself is exercised against this repository: every declared
population must derive, and none may derive zero.
"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovcounts import grading  # noqa: E402
from sovcounts import populations as pops  # noqa: E402
from sovcounts import scan  # noqa: E402


def _population(**overrides) -> pops.Population:
    fields = {
        "id": "p", "counts": "things", "derivation": {"kind": "files", "glob": "x"},
        "anchors": (), "scoped_anchors": (), "scope": (),
    }
    fields.update(overrides)
    return pops.Population(**fields)


class NumberWords(unittest.TestCase):
    def test_digits_words_and_compounds(self):
        for token, expected in (("23", 23), ("eight", 8), ("twenty", 20),
                                ("forty-nine", 49), ("thirty-one", 31)):
            self.assertEqual(scan.value_of(token), expected, token)

    def test_a_non_number_states_no_number(self):
        for token in ("twentyish", "ninety-hundred", "elevenses"):
            self.assertIsNone(scan.value_of(token))


class Binding(unittest.TestCase):
    def test_an_unscoped_anchor_binds_outside_the_scope(self):
        """The defect this test exists for: a named anchor caged by scope."""
        population = _population(anchors=("declared Record operations",),
                                 scoped_anchors=("declared operations",),
                                 scope=("services/record/",))
        self.assertTrue(population.binds(".claude/epic/NARRATIVE.md",
                                         "declared Record operations"))

    def test_a_scoped_anchor_binds_only_inside_the_scope(self):
        population = _population(scoped_anchors=("declared operations",),
                                 scope=("services/record/",))
        self.assertTrue(population.binds("services/record/JOURNEYS.md",
                                         "declared operations"))
        self.assertFalse(population.binds("PRD.md", "declared operations"))

    def test_a_scoped_anchor_outranks_an_unscoped_one(self):
        wide = _population(id="wide", anchors=("declared operations",))
        narrow = _population(id="narrow", scoped_anchors=("declared operations",),
                             scope=("services/gateway/",))
        claims, _ = scan.scan(ROOT, [], [wide, narrow], ())
        self.assertEqual(claims, [])
        ordered = [entry[0] for entry in scan._anchors([wide, narrow])]
        self.assertEqual(ordered[0], "declared operations")
        self.assertTrue(scan._anchors([wide, narrow])[0][3], "the scoped anchor must sort first")


class SubsetGuard(unittest.TestCase):
    GUARD = ("other", "remaining", "of the")

    def test_a_subset_qualifier_is_read(self):
        for before in ("The other", "and the remaining", "four of the"):
            self.assertTrue(scan._subset(before, self.GUARD), before)

    def test_an_ordinary_clause_is_not_a_subset(self):
        for before in ("the service declares", "Today the harness has", ""):
            self.assertFalse(scan._subset(before, self.GUARD), before)


class Grading(unittest.TestCase):
    class _Claim:
        def __init__(self, stated, path="X.md", anchor="workflows"):
            self.path, self.line, self.stated = path, 1, stated
            self.anchor, self.population, self.text = anchor, "p", ""

    def test_disagreement_is_drift_and_agreement_is_not(self):
        self.assertEqual(grading.grade([self._Claim(20)], {"p": 23}, {}, [])[0].kind,
                         grading.DRIFT)
        self.assertEqual(grading.grade([self._Claim(23)], {"p": 23}, {}, [])[0].kind,
                         grading.MATCH)

    def test_an_unanswered_population_is_not_graded_as_drift(self):
        found = grading.grade([self._Claim(20)], {}, {"p": "absent"}, [])
        self.assertEqual(found[0].kind, grading.UNDERIVABLE)
        self.assertEqual(grading.drifted(found), [])

    def test_an_exemption_dies_with_the_value_it_was_written_for(self):
        exemptions = [{"path": "X.md", "anchor": "workflows", "stated": 20,
                       "reason": "history"}]
        self.assertEqual(
            grading.grade([self._Claim(20)], {"p": 23}, {}, exemptions)[0].kind,
            grading.HISTORICAL)
        self.assertEqual(
            grading.grade([self._Claim(21)], {"p": 23}, {}, exemptions)[0].kind,
            grading.DRIFT)


class TheContractAgainstThisRepository(unittest.TestCase):
    def test_every_declared_population_derives_something(self):
        populations, paths = pops.load()
        self.assertTrue(populations, "the contract declares no populations")
        for population in populations:
            with self.subTest(population.id):
                value = pops.derive(population.derivation, paths)
                self.assertGreater(value, 0, "a population that counts nothing "
                                             "agrees with every number written")

    def test_the_template_expands_over_every_service_manifest(self):
        populations, paths = pops.load()
        expanded = {p.id for p in populations if p.id.startswith("service-operations:")}
        manifests = {p.split("/")[1] for p in paths
                     if p.startswith("services/") and p.endswith("/contracts/service.json")}
        self.assertEqual(expanded, {f"service-operations:{name}" for name in manifests})


if __name__ == "__main__":
    unittest.main()
