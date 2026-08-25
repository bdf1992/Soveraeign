"""Prove one expenditure stays one expenditure however many intentions contain it.

This is the case that matters before any resource rollup becomes real. A run serves one
capability; that capability is crossed by journeys; those journeys serve promises; some of
those promises are composed by a compound promise; all of them derive from ground claims.
Every one of those is a true statement about the run, and the run happened once.

The failure mode is arithmetic, not vocabulary: sum the promise views and the node reports
spending several times what it spent. The cases below fix the measured total to the set of
distinct units, prove that summing a view exceeds it, and refuse a total reached that way.

Nothing here touches money. No case converts a token into a second or a second into a
dollar, because that conversion is policy and this repository has not declared one.

Passing establishes `BUILT` for the rollup. It witnesses nothing, and no unit below is a
record of anything that happened.
"""

from __future__ import annotations

from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovkernel import attribution  # noqa: E402

CANON = json.loads((ROOT / "contracts" / "product-canon.json").read_text("utf-8"))
EXAMPLE = json.loads(
    (ROOT / "contracts" / "fixtures" / "usage-attribution.example.json").read_text("utf-8"))


def _unit(unit_id: str, capability: str, **consumed: float) -> dict:
    return {"unit_id": unit_id, "directly_serves": capability, "consumed": consumed}


class AncestorTest(unittest.TestCase):
    """What contains one capability, at each level."""

    def test_a_capability_resolves_up_through_every_level(self) -> None:
        ancestors = attribution.capability_ancestors(CANON, "asset.read-version")
        self.assertEqual(ancestors["capability"], ["asset.read-version"])
        self.assertIn("JOURNEY-04", ancestors["journey"])
        self.assertIn("JOURNEY-11", ancestors["journey"])
        self.assertTrue(ancestors["ground"])

    def test_a_compound_promise_is_a_true_ancestor(self) -> None:
        """PROMISE-01 contains what it composes, so a run below a part is below it too."""
        ancestors = attribution.capability_ancestors(CANON, "console.discover-operations")
        self.assertIn("PROMISE-03", ancestors["promise"])
        self.assertIn("PROMISE-01", ancestors["promise"])

    def test_an_ancestor_reached_by_two_paths_is_listed_once(self) -> None:
        ancestors = attribution.capability_ancestors(CANON, "asset.read-version")
        self.assertEqual(len(ancestors["promise"]), len(set(ancestors["promise"])))
        self.assertEqual(len(ancestors["ground"]), len(set(ancestors["ground"])))

    def test_a_capability_no_journey_crosses_has_no_journey_ancestor(self) -> None:
        ancestors = attribution.capability_ancestors(CANON, "asset.rebuild-projection")
        self.assertEqual(ancestors["journey"], [])


class MeasuredOnceTest(unittest.TestCase):
    """The whole point: measured once, viewed many times."""

    def test_the_measured_total_is_the_distinct_units(self) -> None:
        result = attribution.rollup(CANON, EXAMPLE["units"])
        self.assertEqual(result["measured"]["tokens"], 4100 + 900 + 15000)
        self.assertEqual(result["unit_count"], 3)

    def test_summing_the_promise_views_exceeds_what_was_spent(self) -> None:
        """Not a defect - a fact about views. Reporting the sum as a total is the defect."""
        result = attribution.rollup(CANON, EXAMPLE["units"])
        gap = attribution.overlap(result, "promise")
        self.assertGreater(gap["tokens"], 0)
        summed = sum(bucket["consumed"]["tokens"]
                     for bucket in result["views"]["promise"].values())
        self.assertGreater(summed, result["measured"]["tokens"])

    def test_a_claimed_total_reached_by_summing_a_view_is_refused(self) -> None:
        result = attribution.rollup(CANON, EXAMPLE["units"])
        summed = {"tokens": sum(bucket["consumed"]["tokens"]
                                for bucket in result["views"]["promise"].values())}
        defects = attribution.double_counting_defects(result, summed, "promise")
        self.assertEqual([d.split(":")[0] for d in defects], ["DOUBLE_COUNTED_USAGE"])

    def test_the_measured_total_itself_is_accepted(self) -> None:
        result = attribution.rollup(CANON, EXAMPLE["units"])
        self.assertEqual(
            attribution.double_counting_defects(result, result["measured"], "promise"), [])

    def test_one_unit_serving_two_journeys_counts_once_in_a_shared_promise(self) -> None:
        result = attribution.rollup(
            CANON, [_unit("u1", "asset.read-version", tokens=100)])
        for level in attribution.LEVELS:
            for identifier, bucket in result["views"][level].items():
                with self.subTest(level=level, identifier=identifier):
                    self.assertEqual(bucket["units"], ["u1"])
                    self.assertEqual(bucket["consumed"]["tokens"], 100)
        self.assertEqual(result["measured"]["tokens"], 100)

    def test_a_capability_view_never_over_counts(self) -> None:
        """A unit serves exactly one capability, so this level always partitions."""
        result = attribution.rollup(CANON, EXAMPLE["units"])
        self.assertEqual(set(attribution.overlap(result, "capability").values()), {0})

    def test_work_below_no_journey_is_reported_rather_than_dropped(self) -> None:
        result = attribution.rollup(
            CANON, [_unit("u1", "asset.rebuild-projection", tokens=50)])
        self.assertEqual(result["unattributed"], ["u1"])
        self.assertEqual(result["attributed"], 0)
        self.assertEqual(result["measured"]["tokens"], 50)


class DimensionTest(unittest.TestCase):
    """The seven resource words stay seven, and no dimension converts into another."""

    def test_an_unknown_dimension_is_refused(self) -> None:
        with self.assertRaises(attribution.UnknownDimension):
            attribution.rollup(CANON, [_unit("u1", "asset.read-version", effort=3)])

    def test_cost_is_not_a_usage_dimension(self) -> None:
        """COST is a valuation of usage. A usage record does not carry one."""
        with self.assertRaises(attribution.UnknownDimension):
            attribution.rollup(CANON, [_unit("u1", "asset.read-version", cost=1.5)])

    def test_a_local_run_records_real_usage_at_zero_charge(self) -> None:
        """RECORD_LOCAL and zero money do not make consumption disappear."""
        result = attribution.rollup(
            CANON, [_unit("u1", "asset.read-version", tokens=8000,
                          wallclock_seconds=41.0, usd=0)])
        self.assertEqual(result["measured"]["usd"], 0)
        self.assertEqual(result["measured"]["tokens"], 8000)
        self.assertEqual(result["measured"]["wallclock_seconds"], 41.0)

    def test_dimensions_are_never_combined(self) -> None:
        result = attribution.rollup(
            CANON, [_unit("u1", "asset.read-version", tokens=10, wallclock_seconds=2)])
        self.assertEqual(result["measured"], {"tokens": 10, "wallclock_seconds": 2})

    def test_the_same_unit_twice_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            attribution.rollup(CANON, [_unit("u1", "asset.read-version", tokens=1),
                                       _unit("u1", "asset.read-version", tokens=1)])


if __name__ == "__main__":
    unittest.main()
