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


class ThresholdGuard(unittest.TestCase):
    """A bound the population must stay inside is not a census of it."""

    GUARD = ((("other",), "subset"), (("past", "more than"), "threshold"))

    def _read(self, line: str):
        population = _population(id="ground", anchors=("claims",))
        claims: list = []
        candidates: list = []
        scan._read_line("GROUND.md", 1, line, scan._anchors([population]),
                        self.GUARD, claims, candidates)
        return claims, candidates

    def test_a_threshold_is_not_graded(self):
        """GROUND.md names growing past twenty claims as its own defeating signal.

        Graded against a record of sixteen it reports a correct sentence as drift,
        which is what this check did on the day the population was declared.
        """
        claims, candidates = self._read("Ground growing past twenty claims is the signal.")
        self.assertEqual(claims, [])
        self.assertEqual([c.noun for c in candidates], ["claims (threshold)"])

    def test_a_subset_and_a_threshold_are_told_apart(self):
        _, subset = self._read("The other sixteen claims are elsewhere.")
        _, threshold = self._read("more than sixteen claims would be a defect.")
        self.assertEqual([c.noun for c in subset], ["claims (subset)"])
        self.assertEqual([c.noun for c in threshold], ["claims (threshold)"])

    def test_a_plain_total_is_still_graded(self):
        claims, _ = self._read("GROUND.md owns the sixteen claims that say what it is.")
        self.assertEqual([(c.stated, c.population) for c in claims], [(16, "ground")])


class Derivations(unittest.TestCase):
    def test_matches_counts_a_document_the_repository_enumerates(self):
        """GROUND.md is the only record of how many claims there are.

        The expected value is counted here rather than written here. An earlier
        draft asserted the literal 16, which an independent witness named for what
        it was: a hand-written count with no counter, inside the suite built to
        eliminate them. Adding a legitimate `GROUND-017` would have failed this
        test for the wrong reason, on top of the eight restatements it correctly
        fails. Counting the identifiers a different way keeps the derivation
        honest without pinning it to today's number.
        """
        text = (pops.ROOT / "GROUND.md").read_text(encoding="utf-8")
        identifiers = {line.split("`")[1] for line in text.splitlines()
                       if line.startswith("### `GROUND-")}
        found = pops.derive({"kind": "matches", "path": "GROUND.md",
                             "pattern": r"^### `GROUND-[0-9]+`"}, [])
        self.assertEqual(found, len(identifiers))
        self.assertGreater(found, 0, "the pattern matches nothing, so it counts nothing")

    def test_an_absent_or_unreadable_source_refuses_rather_than_answering_zero(self):
        for derivation in ({"kind": "matches", "path": "nothing-here.md", "pattern": "^x"},
                           {"kind": "matches", "path": "GROUND.md", "pattern": "([unclosed"},
                           {"kind": "nonexistent-kind"}):
            with self.subTest(derivation), self.assertRaises(pops.Underivable):
                pops.derive(derivation, [])


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

    def test_no_guard_word_suppresses_a_sentence_that_states_a_total(self):
        """Every guard word must prevent a false drift or cost nothing. Nothing else.

        This is the generalisation of a defect an independent witness found by
        hand. `of the` sat in `subset_qualifiers` and suppressed three sentences
        stating a manifest total exactly - gateway, host, observation - while
        preventing no false drift at all. Nothing in the repository noticed,
        because the guard lists were the one part of this check graded by nobody:
        a word that hides a true sentence produces silence, and silence is what a
        passing check looks like.

        Two scans settle it rather than one per word. Everything the guards
        suppress is the difference between grading with them and grading without,
        and a suppressed sentence that would have MATCHed was a real total the
        guard was hiding. Only those lines are then asked which word did it, so
        the cost is two passes over the corpus and not one pass per word.

        A word that suppresses a DRIFT is load-bearing and is why the lists exist.
        A word that suppresses nothing is harmless and stays until it costs
        something. A word added tomorrow is graded the day it is added.
        """
        declared = pops.contract()
        populations, paths = pops.load()
        values = {}
        for population in populations:
            try:
                values[population.id] = pops.derive(population.derivation, paths)
            except pops.Underivable:
                continue
        files = scan.live_files(paths, tuple(declared["frozen_paths"]["paths"]))
        exemptions = declared["historical_claims"]["claims"]
        lists = {name: tuple(declared[name]["words"])
                 for name in ("subset_qualifiers", "threshold_qualifiers")}
        guard = ((lists["subset_qualifiers"], "subset"),
                 (lists["threshold_qualifiers"], "threshold"))

        def matched(active) -> dict:
            claims, _ = scan.scan(pops.ROOT, files, populations, active)
            found = grading.grade(claims, values, {}, exemptions)
            return {(f.path, f.line, f.stated, f.population): f.kind for f in found}

        with_guards = matched(guard)
        without_guards = matched(())
        # A suppressed sentence that would have graded MATCH is a real total the
        # guard hid. One that would have DRIFTed is the false positive the guard
        # exists to prevent, and is left alone.
        hidden = [key for key, kind in without_guards.items()
                  if kind == grading.MATCH and key not in with_guards]

        # Only the hidden lines are asked which word hid them, and only the files
        # holding them are re-read. Attribution never drove the verdict - `hidden`
        # already is the verdict - so a word this fails to name still fails the
        # test, under `unattributed`. An earlier draft attributed by slicing the
        # line at the stated value and found nothing, because the value was
        # written `sixteen` and searched for as `16`.
        blamed: dict[str, list] = {}
        affected = sorted({key[0] for key in hidden})
        for name, words in lists.items():
            for word in words:
                thinner = []
                for other, label in guard:
                    keep = tuple(w for w in other if w != word or label != name[:len(label)])
                    thinner.append((keep, label))
                claims, _ = scan.scan(pops.ROOT, affected, populations, tuple(thinner))
                found = grading.grade(claims, values, {}, exemptions)
                gained = {(f.path, f.line, f.stated, f.population)
                          for f in found if f.kind == grading.MATCH} & set(hidden)
                if gained:
                    blamed.setdefault(f"{name}:{word}", []).extend(sorted(gained))
        unnamed = set(hidden) - {k for keys in blamed.values() for k in keys}
        if unnamed:
            blamed["unattributed"] = sorted(unnamed)
        self.assertEqual({}, blamed,
                         "these guard words hide sentences that state a population "
                         "total exactly; each would grade MATCH if the word were "
                         "dropped, so the word buys nothing and costs coverage")

    def test_the_template_expands_over_every_service_manifest(self):
        populations, paths = pops.load()
        expanded = {p.id for p in populations if p.id.startswith("service-operations:")}
        manifests = {p.split("/")[1] for p in paths
                     if p.startswith("services/") and p.endswith("/contracts/service.json")}
        self.assertEqual(expanded, {f"service-operations:{name}" for name in manifests})


if __name__ == "__main__":
    unittest.main()
