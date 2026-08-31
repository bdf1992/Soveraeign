"""Prove a measured execution resolves upward to the intention that justified it.

`GROUND-014` is the claim under test: any meaningful expenditure can be traced up to what
justified it. Until 2026-08-24 nothing could, because no receipt recorded what it served
or what it spent. `bindings/mcp/observations/journey-02-receipt.json` is the first one
that does, taken from a real crossing through the MCP binding rather than written by hand
to agree with this file.

The second thing under test is the arithmetic. One expenditure that serves five promises
and eight ground claims is still one expenditure, and the cases below fix the measured
total to the distinct receipts while proving that summing any view exceeds it.

Passing establishes `BUILT`. It witnesses nothing: the receipt was produced by calling the
gateway, and reading it back here is not an independent observation of that call.
"""

from __future__ import annotations

from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovkernel import attribution  # noqa: E402
from sovkernel.jsonschema import validate  # noqa: E402

import sov_trace  # noqa: E402

RECEIPT = json.loads((ROOT / "bindings" / "mcp" / "observations"
                      / "journey-02-receipt.json").read_text("utf-8"))
DISCOVERY = json.loads((ROOT / "bindings" / "mcp" / "observations"
                        / "journey-02-discovery.json").read_text("utf-8"))
SCHEMA = json.loads((ROOT / "contracts" / "receipt.schema.json").read_text("utf-8"))
CANON = json.loads((ROOT / "contracts" / "product-canon.json").read_text("utf-8"))
GROUND = json.loads((ROOT / "contracts" / "product-ground.json").read_text("utf-8"))
MAP = json.loads((ROOT / "contracts" / "fixtures"
                  / "capability-map.reference.json").read_text("utf-8"))
TICKETS = json.loads((ROOT / "conformance" / "fixtures" / "tickets"
                      / "metadata-cases.json").read_text("utf-8"))


class MeasuredReceiptTest(unittest.TestCase):
    """The receipt a real crossing produced."""

    def test_it_satisfies_the_receipt_contract(self) -> None:
        self.assertEqual(validate(RECEIPT, SCHEMA), [])

    def test_it_names_the_capability_it_served(self) -> None:
        self.assertEqual(RECEIPT["serves_capability"], "console.discover-operations")

    def test_it_records_what_it_actually_consumed(self) -> None:
        dimensions = {entry["dimension"] for entry in RECEIPT["consumed"]}
        self.assertIn("wallclock_seconds", dimensions)
        self.assertIn("tool_calls", dimensions)
        self.assertLessEqual(dimensions, attribution.DIMENSIONS)

    def test_a_record_local_operation_still_spent_something(self) -> None:
        """Effect class and consumption are different dimensions (Bdo, Q2 2026-08-24)."""
        self.assertEqual(RECEIPT["effect_class"], "RECORD_LOCAL")
        spent = {entry["dimension"]: entry["amount"] for entry in RECEIPT["consumed"]}
        self.assertEqual(spent["usd"], 0)
        self.assertGreater(spent["wallclock_seconds"], 0)

    def test_zero_money_is_a_valuation_and_says_so(self) -> None:
        usd = next(entry for entry in RECEIPT["consumed"] if entry["dimension"] == "usd")
        self.assertIn("valuation", usd["note"])

    def test_it_pins_the_state_this_observation_read(self) -> None:
        self.assertEqual(RECEIPT["input_state_digest"], DISCOVERY["capability_revision"])

    def test_it_records_the_precondition_it_could_not_verify(self) -> None:
        """`capability_map_fresh` was declared and not checked; the receipt says so."""
        results = {entry["precondition"]: entry
                   for entry in RECEIPT["precondition_results"]}
        self.assertEqual(results["capability_map_fresh"]["result"], "UNVERIFIED")


class ResolvesUpwardTest(unittest.TestCase):
    """The chain Bdo asked to see end to end."""

    def setUp(self) -> None:
        self.ancestors = attribution.capability_ancestors(
            CANON, RECEIPT["serves_capability"])

    def test_the_capability_is_one_the_node_declares(self) -> None:
        declared = {row["capability_id"] for row in MAP["capabilities"]}
        self.assertIn(RECEIPT["serves_capability"], declared)

    def test_the_operation_carries_a_product_requirement(self) -> None:
        row = next(row for row in MAP["capabilities"]
                   if row["capability_id"] == RECEIPT["serves_capability"])
        self.assertTrue(row["shape"]["requirement"].startswith("PROD-I-"))

    def test_a_work_item_names_the_capability(self) -> None:
        items = sov_trace._work_items(RECEIPT["serves_capability"],
                                      sov_trace.tickets(TICKETS))
        self.assertTrue(items, "no checked ticket fixture names this capability")

    def test_it_reaches_a_journey_a_promise_and_a_ground_claim(self) -> None:
        self.assertIn("JOURNEY-02", self.ancestors["journey"])
        self.assertIn("PROMISE-03", self.ancestors["promise"])
        self.assertIn("GROUND-006", self.ancestors["ground"])

    def test_every_ground_claim_it_reaches_is_declared(self) -> None:
        declared = {claim["ground_id"] for claim in GROUND["claims"]}
        self.assertLessEqual(set(self.ancestors["ground"]), declared)

    def test_the_whole_chain_resolves(self) -> None:
        """The acceptance test, as one assertion."""
        for level in attribution.LEVELS:
            with self.subTest(level=level):
                self.assertTrue(self.ancestors[level])


class CountedOnceTest(unittest.TestCase):
    """One expenditure, many true readings, one measurement."""

    def setUp(self) -> None:
        self.rollup = attribution.rollup(CANON, sov_trace.units([RECEIPT]))

    def test_the_measured_total_is_the_receipt(self) -> None:
        spent = {entry["dimension"]: entry["amount"] for entry in RECEIPT["consumed"]}
        self.assertEqual(self.rollup["measured"], spent)
        self.assertEqual(self.rollup["unit_count"], 1)

    def test_summing_the_ground_views_would_invent_time_that_was_never_spent(self) -> None:
        gap = attribution.overlap(self.rollup, "ground")
        self.assertGreater(gap["wallclock_seconds"], 0)
        summed = sum(bucket["consumed"]["wallclock_seconds"]
                     for bucket in self.rollup["views"]["ground"].values())
        self.assertGreater(summed, self.rollup["measured"]["wallclock_seconds"])

    def test_a_total_reached_by_summing_a_view_is_refused(self) -> None:
        summed = {"tool_calls": sum(bucket["consumed"]["tool_calls"]
                                    for bucket in self.rollup["views"]["promise"].values())}
        defects = attribution.double_counting_defects(self.rollup, summed, "promise")
        self.assertEqual([d.split(":")[0] for d in defects], ["DOUBLE_COUNTED_USAGE"])

    def test_a_receipt_that_measured_nothing_is_not_entered_as_a_zero(self) -> None:
        """An absence is not a measurement."""
        unmeasured = dict(RECEIPT)
        unmeasured.pop("consumed")
        self.assertEqual(sov_trace.units([unmeasured]), [])


class CommandTest(unittest.TestCase):
    """The command runs against the checked-in artifacts."""

    def test_the_trace_command_succeeds(self) -> None:
        self.assertEqual(sov_trace.main(["up"]), 0)

    def test_a_receipt_that_fails_its_contract_is_refused(self) -> None:
        import tempfile
        broken = dict(RECEIPT)
        broken["effect_class"] = "INVENTED"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broken.json"
            path.write_text(json.dumps(broken), encoding="utf-8")
            self.assertEqual(sov_trace.main(["up", str(path)]), 1)


if __name__ == "__main__":
    unittest.main()
