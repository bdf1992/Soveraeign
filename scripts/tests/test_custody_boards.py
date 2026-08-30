"""Prove the custody set, the work circuit and the estimate registry hold as declared.

`scripts/sov_custody.py selfcheck` grades the declared corpus in
`conformance/fixtures/custody/circuit-cases.json`. This module proves the half
the corpus cannot: that the judges read their contracts as data rather than
restating them, that the circuit's order is the order refusals arrive in, and
that the shipped Phase-I custodies satisfy the same rules the fixtures do.

Passing establishes `BUILT` for the contracts and their evaluators. It witnesses
nothing: no participant here carried a concern, and a custody grants nothing.
"""

from __future__ import annotations

from pathlib import Path
import copy
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovcustody import board as boardmod  # noqa: E402
from sovcustody import circuit as circuitmod  # noqa: E402
from sovcustody import estimate as estimatemod  # noqa: E402
from sovcustody import model as modelmod  # noqa: E402
from sovcustody import phase as phasemod  # noqa: E402
from sovcustody import roots as rootsmod  # noqa: E402

CIRCUIT = json.loads((ROOT / "contracts" / "work-circuit.json").read_text("utf-8"))
REGISTRY = json.loads((ROOT / "contracts" / "estimation.json").read_text("utf-8"))
CORPUS = json.loads(
    (ROOT / "conformance" / "fixtures" / "custody" / "circuit-cases.json").read_text("utf-8"))


def case(case_id: str) -> dict:
    """A deep copy of one declared case, ready to mutate."""
    for record in CORPUS:
        if record["id"] == case_id:
            return copy.deepcopy(record)
    raise AssertionError(f"no case named {case_id}")


class CircuitOrder(unittest.TestCase):
    """The circuit is read as data, and its order is load-bearing."""

    def test_stages_are_contiguous_from_one(self) -> None:
        ordinals = [stage["ordinal"] for stage in circuitmod.stages()]
        self.assertEqual(ordinals, list(range(1, len(ordinals) + 1)))

    def test_stage_names_come_from_the_contract_not_the_module(self) -> None:
        self.assertEqual(
            circuitmod.stage_names(),
            [stage["stage"] for stage in
             sorted(CIRCUIT["stages"], key=lambda row: row["ordinal"])])

    def test_unknown_stage_is_ordinal_zero_and_never_compares_true(self) -> None:
        self.assertEqual(circuitmod.ordinal("SHIPPED"), 0)
        self.assertFalse(circuitmod.at_least("SHIPPED", "ROOT_POINT"))
        self.assertFalse(circuitmod.at_least("ROOT_POINT", "SHIPPED"))

    def test_every_stage_declares_a_defeating_case_with_a_fixture(self) -> None:
        identifiers = {record["id"] for record in CORPUS}
        for stage in circuitmod.stages():
            defeat = stage["defeated_by"]
            self.assertIn("why", defeat, stage["stage"])
            anchor = defeat["fixture"].split("#", 1)[-1]
            self.assertIn(anchor, identifiers, f"{stage['stage']} names a fixture that is absent")

    def test_advancing_two_stages_is_refused_however_good_the_evidence(self) -> None:
        admitted = case("capable-node-admitted")
        defects = circuitmod.judge_advance(
            "HORIZONTAL_SURFACE", "CAPABLE_NODE", admitted["evidence"])
        self.assertEqual({code for code, _ in defects}, {"SKIPPED_STAGE"})

    def test_falling_back_is_not_judged_here(self) -> None:
        defects = circuitmod.judge_advance("CAPABLE_NODE", "ROOT_POINT", {})
        self.assertEqual({code for code, _ in defects}, {"SKIPPED_STAGE"})


class ClosedPath(unittest.TestCase):
    """A path closes on evidence somebody else can re-run, and on nothing else."""

    def test_a_report_does_not_close_a_path(self) -> None:
        for emission in ("REPORT", "SUMMARY", "", "PASS"):
            with self.subTest(emission=emission):
                defects = circuitmod.judge_advance(
                    "ROOT_POINT", "VERTICAL_SLICE",
                    {"path": [{"layer": "service", "emits": emission}]})
                self.assertEqual({code for code, _ in defects}, {"OPEN_PATH"})

    def test_a_check_a_receipt_and_an_observation_all_close_it(self) -> None:
        for emission in sorted(circuitmod.CLOSING_EMISSIONS):
            with self.subTest(emission=emission):
                defects = circuitmod.judge_advance(
                    "ROOT_POINT", "VERTICAL_SLICE",
                    {"path": [{"layer": "service", "emits": emission}]})
                self.assertEqual(defects, [])

    def test_only_the_last_layer_decides_closure(self) -> None:
        defects = circuitmod.judge_advance("ROOT_POINT", "VERTICAL_SLICE", {"path": [
            {"layer": "a", "emits": "REPORT"},
            {"layer": "b", "emits": "CHECK"},
        ]})
        self.assertEqual(defects, [])


class SurfaceComposition(unittest.TestCase):
    """A surface is only as closed as the verticals under it."""

    def test_one_open_vertical_defeats_the_whole_surface(self) -> None:
        record = case("horizontal-surface-admitted")
        record["evidence"]["composes"][0]["stage"] = "ROOT_POINT"
        defects = circuitmod.judge_advance(
            record["from_stage"], record["to_stage"], record["evidence"],
            set(record.get("required_dimensions") or []))
        self.assertIn("SURFACE_OVER_OPEN_PATHS", {code for code, _ in defects})

    def test_a_single_vertical_is_not_a_surface(self) -> None:
        record = case("horizontal-surface-admitted")
        record["evidence"]["composes"] = record["evidence"]["composes"][:1]
        defects = circuitmod.judge_advance(
            record["from_stage"], record["to_stage"], record["evidence"],
            set(record.get("required_dimensions") or []))
        self.assertIn("SURFACE_OVER_OPEN_PATHS", {code for code, _ in defects})


class DiscoveryAndEnforcement(unittest.TestCase):
    """Both directions of the divergence are refused, not just the dangerous one."""

    def test_advertised_and_unenforced_is_refused(self) -> None:
        record = case("advertised-not-enforced")
        defects = circuitmod.judge_advance(
            record["from_stage"], record["to_stage"], record["evidence"])
        self.assertIn("ADVERTISED_NOT_ENFORCED", {code for code, _ in defects})

    def test_enforced_and_undiscoverable_is_refused_too(self) -> None:
        record = case("reachable-and-undiscoverable")
        defects = circuitmod.judge_advance(
            record["from_stage"], record["to_stage"], record["evidence"])
        self.assertIn("ADVERTISED_NOT_ENFORCED", {code for code, _ in defects})

    def test_an_operation_missing_any_declared_part_is_refused(self) -> None:
        for field in ("subject", "verb", "endpoint", "preconditions", "commit", "refusals"):
            with self.subTest(field=field):
                record = case("exploded-surface-admitted")
                record["evidence"]["operations"][0][field] = None
                defects = circuitmod.judge_advance(
                    record["from_stage"], record["to_stage"], record["evidence"])
                self.assertIn("ADVERTISED_NOT_ENFORCED", {code for code, _ in defects})


class NodeWitness(unittest.TestCase):
    """A node cannot supply its own observation, and cannot infer its own identity."""

    def test_a_build_relation_defeats_the_observation(self) -> None:
        record = case("capable-node-admitted")
        record["evidence"]["observation"]["build_relation"] = True
        defects = circuitmod.judge_advance("EXPLODED_SURFACE", "CAPABLE_NODE",
                                           record["evidence"])
        self.assertIn("SELF_WITNESSED_NODE", {code for code, _ in defects})

    def test_no_observation_at_all_is_the_same_refusal(self) -> None:
        record = case("capable-node-admitted")
        record["evidence"]["observation"] = {}
        defects = circuitmod.judge_advance("EXPLODED_SURFACE", "CAPABLE_NODE",
                                           record["evidence"])
        self.assertIn("SELF_WITNESSED_NODE", {code for code, _ in defects})

    def test_an_operation_without_a_receipt_is_refused(self) -> None:
        record = case("capable-node-admitted")
        record["evidence"]["operations"][0]["emits_receipt"] = False
        defects = circuitmod.judge_advance("EXPLODED_SURFACE", "CAPABLE_NODE",
                                           record["evidence"])
        self.assertIn("SELF_WITNESSED_NODE", {code for code, _ in defects})


class EstimateRegistry(unittest.TestCase):
    """Every declared dimension can be graded, or says plainly why it cannot."""

    def test_the_shipped_registry_is_admissible(self) -> None:
        self.assertEqual(estimatemod.grade_registry(), [])

    def test_a_graded_dimension_with_no_source_is_refused(self) -> None:
        graded = [row for row in REGISTRY["dimensions"] if row.get("graded")]
        self.assertTrue(graded)
        for row in graded:
            self.assertTrue(row.get("actual_source"), row["id"])

    def test_an_ungraded_dimension_states_why(self) -> None:
        for row in REGISTRY["dimensions"]:
            if not row.get("graded"):
                self.assertTrue(row.get("ungraded_because"), row["id"])
                self.assertIsNone(row.get("actual_source"), row["id"])

    def test_required_dimensions_accumulate_along_the_circuit(self) -> None:
        previous: set[str] = set()
        for name in circuitmod.stage_names():
            here = estimatemod.required_at(name, circuitmod.ordinal)
            self.assertTrue(previous <= here, f"{name} drops a dimension an earlier stage needed")
            previous = here

    def test_root_point_requires_only_the_governance_dimensions(self) -> None:
        required = estimatemod.required_at("ROOT_POINT", circuitmod.ordinal)
        self.assertEqual(required, {"judgement_units", "grants"})


class EstimateGrading(unittest.TestCase):
    """The four things the schema cannot see."""

    def test_an_unknown_dimension_is_reported_not_dropped(self) -> None:
        defects = estimatemod.grade({
            "estimated_by": "p", "dimensions": [{"dimension_id": "vibes", "low": 1, "high": 2}]})
        self.assertEqual({code for code, _ in defects}, {"UNKNOWN_DIMENSION"})

    def test_an_inverted_range_is_refused(self) -> None:
        defects = estimatemod.grade({
            "estimated_by": "p", "dimensions": [{"dimension_id": "points", "low": 9, "high": 2}]})
        self.assertEqual({code for code, _ in defects}, {"INVERTED_RANGE"})

    def test_equal_low_and_high_is_admissible(self) -> None:
        defects = estimatemod.grade({
            "estimated_by": "p", "dimensions": [{"dimension_id": "points", "low": 5, "high": 5}]})
        self.assertEqual(defects, [])

    def test_the_estimator_may_record_an_actual_but_not_observe_it(self) -> None:
        base = {"estimated_by": "principal:a", "maturity": "WIDE_RANGE", "dimensions": [
            {"dimension_id": "tokens", "low": 1, "high": 2, "actual": 9}]}
        self.assertEqual(estimatemod.grade(base), [])
        base["dimensions"][0]["actual_observed_by"] = "principal:a"
        self.assertEqual({code for code, _ in estimatemod.grade(base)},
                         {"SELF_SETTLED_VARIANCE"})
        base["dimensions"][0]["actual_observed_by"] = "principal:b"
        self.assertEqual(estimatemod.grade(base), [])

    def test_no_estimate_at_all_is_refused_only_when_something_is_required(self) -> None:
        self.assertEqual(estimatemod.grade(None), [])
        self.assertEqual({code for code, _ in estimatemod.grade(None, {"points"})},
                         {"MISSING_REQUIRED_DIMENSION"})

    def test_variance_reads_under_within_over_and_pending(self) -> None:
        rows = estimatemod.variance({"dimensions": [
            {"dimension_id": "tokens", "low": 10, "high": 20, "actual": 5},
            {"dimension_id": "tokens", "low": 10, "high": 20, "actual": 15},
            {"dimension_id": "tokens", "low": 10, "high": 20, "actual": 25},
            {"dimension_id": "tokens", "low": 10, "high": 20},
        ]})
        self.assertEqual([row["verdict"] for row in rows],
                         ["UNDER", "WITHIN", "OVER", "PENDING"])


class ShippedCustodies(unittest.TestCase):
    """The Phase-I set obeys the rules the fixtures state."""

    def setUp(self) -> None:
        self.records = modelmod.custodies()

    def test_the_collection_is_admissible(self) -> None:
        self.assertEqual(modelmod.grade_collection(self.records), [])

    def test_every_custody_can_close(self) -> None:
        for custody in self.records:
            closure = custody["closure"]
            with self.subTest(custody=custody["custody_id"]):
                self.assertTrue(closure.get("check") or closure.get("judgement_seat"))
                self.assertTrue(closure.get("defeated_by"))

    def test_no_custody_settles_its_own_closure(self) -> None:
        for custody in self.records:
            with self.subTest(custody=custody["custody_id"]):
                self.assertNotEqual(custody["held_by"], custody["closure"].get("judgement_seat"))

    def test_every_root_resolves(self) -> None:
        for custody in self.records:
            for root in custody["roots"]:
                with self.subTest(custody=custody["custody_id"], root=root["reference"]):
                    self.assertTrue(rootsmod.root_resolves(root))

    def test_dependencies_name_custodies_that_exist(self) -> None:
        known = {custody["custody_id"] for custody in self.records}
        for custody in self.records:
            for dependency in custody.get("depends_on") or []:
                self.assertIn(dependency, known, custody["custody_id"])

    def test_a_second_holder_of_one_member_is_refused(self) -> None:
        records = copy.deepcopy(self.records)
        stocked = [r for r in records if r.get("members")]
        borrowed = stocked[0]["members"][0]
        stocked[1]["members"].append(copy.deepcopy(borrowed))
        self.assertIn("MEMBER_IN_TWO_CUSTODIES",
                      {code for code, _ in modelmod.grade_collection(records)})


class CustodyTerminals(unittest.TestCase):
    """A closed campaign is history, not a live assignment surface."""

    def setUp(self) -> None:
        self.records = modelmod.custodies()

    def test_every_closed_phase_custody_has_a_terminal(self) -> None:
        historical = [row for row in self.records if row.get("phase") == "phase:i"]
        self.assertEqual(len(historical), 15)
        self.assertTrue(all(row.get("terminal") for row in historical))

    def test_exit_and_delivery_terminal_vocabularies_do_not_cross(self) -> None:
        exit_row = copy.deepcopy(next(row for row in self.records if row["custody_kind"] == "EXIT"))
        exit_row["terminal"]["outcome"] = "SETTLED"
        self.assertIn("INVALID_CUSTODY_TERMINAL", {code for code, _ in modelmod.grade(exit_row)})
        delivery = copy.deepcopy(next(row for row in self.records if row.get("phase") == "phase:i" and row["custody_kind"] == "DELIVERY"))
        delivery["terminal"]["outcome"] = "CLOSED_UNMET"
        self.assertIn("INVALID_CUSTODY_TERMINAL", {code for code, _ in modelmod.grade(delivery)})

    def test_a_closed_phase_custody_without_terminal_is_refused(self) -> None:
        row = copy.deepcopy(next(row for row in self.records if row.get("phase") == "phase:i"))
        row.pop("terminal")
        self.assertIn("CLOSED_PHASE_CUSTODY_LIVE", {code for code, _ in modelmod.grade(row)})

    def test_future_phase_null_custody_remains_live(self) -> None:
        row = next(row for row in self.records if row["custody_id"] == "custody:session-as-node")
        self.assertIsNone(row.get("phase"))
        self.assertIsNone(row.get("terminal"))
        self.assertNotIn("CLOSED_PHASE_CUSTODY_LIVE", {code for code, _ in modelmod.grade(row)})


class Hierarchy(unittest.TestCase):
    """Exit custodies hold clauses; delivery custodies name what they serve."""

    def setUp(self) -> None:
        self.records = modelmod.custodies()

    def test_every_phase_clause_is_held_by_exactly_one_exit_custody(self) -> None:
        holders: dict[str, list[str]] = {}
        for custody in self.records:
            if custody["custody_kind"] == "EXIT":
                holders.setdefault(custody["exit_clause"], []).append(custody["custody_id"])
        for phase in phasemod.phases():
            for clause in phase["exit_clauses"]:
                with self.subTest(clause=clause["clause_id"]):
                    self.assertEqual(len(holders.get(clause["clause_id"], [])), 1)

    def test_every_delivery_custody_is_parented_or_says_it_is_not(self) -> None:
        exits = {c["custody_id"] for c in self.records if c["custody_kind"] == "EXIT"}
        for custody in self.records:
            if custody["custody_kind"] != "DELIVERY":
                continue
            with self.subTest(custody=custody["custody_id"]):
                serves, outside = custody.get("serves_exit"), custody.get("outside_phase_exit")
                self.assertNotEqual(bool(serves), bool(outside))
                if serves:
                    self.assertIn(serves, exits)

    def test_an_exit_custody_never_serves_another(self) -> None:
        for custody in self.records:
            if custody["custody_kind"] == "EXIT":
                self.assertIsNone(custody.get("serves_exit"), custody["custody_id"])

    def test_every_member_carries_all_three_axes(self) -> None:
        for custody in self.records:
            for member in custody.get("members") or []:
                with self.subTest(address=member["address"]):
                    self.assertIn(member["stage"], circuitmod.stage_names())
                    self.assertIn(member["standing"],
                                  ["OPEN", "BUILT", "WITNESSED", "RATIFIED"])
                    self.assertIn(member["work_state"],
                                  ["CANDIDATE", "READY", "CLAIMED", "IN_PROGRESS",
                                   "PRESENTED", "LANDED", "RETIRED"])


class PhaseTerminal(unittest.TestCase):
    """A phase cannot end by narrowing its own definition."""

    def test_the_shipped_phase_record_is_admissible(self) -> None:
        ids = {custody["custody_id"] for custody in modelmod.custodies()}
        self.assertEqual(phasemod.grade_collection(custody_ids=ids), [])

    def test_the_pinned_definition_still_matches_the_documents(self) -> None:
        for phase in phasemod.phases():
            for pinned in phase["definition"]:
                with self.subTest(document=pinned["document"]):
                    self.assertEqual(phasemod._digest(ROOT / pinned["document"]),
                                     pinned["digest"])

    def test_earned_requires_every_clause_earned(self) -> None:
        phase = copy.deepcopy(phasemod.phases()[0])
        phase["acceptance_status"] = "EARNED"
        phase["terminal"] = "ACCEPTED"
        codes = {code for code, _ in phasemod.grade(phase)}
        self.assertIn("ACCEPTANCE_WITHOUT_CLAUSES", codes)

    def test_terminal_is_derived_not_written(self) -> None:
        self.assertEqual(phasemod.terminal_for("CLOSED", "NOT_EARNED"), "CLOSED_INCOMPLETE")
        self.assertEqual(phasemod.terminal_for("CLOSED", "EARNED"), "ACCEPTED")
        self.assertEqual(phasemod.terminal_for("OPEN", "NOT_EARNED"), "IN_FLIGHT")
        self.assertIsNone(phasemod.terminal_for("CLOSED", "MOSTLY"))

    def test_an_unmet_clause_must_name_a_custody_that_exists(self) -> None:
        phase = copy.deepcopy(phasemod.phases()[0])
        phase["exit_clauses"][0]["held_by"] = "custody:nobody"
        codes = {code for code, _ in phasemod.grade(phase, {"custody:real"})}
        self.assertIn("ORPHAN_EXIT_CLAUSE", codes)

    def test_phase_i_closed_without_earning_its_exit(self) -> None:
        phase = phasemod.by_id("phase:i")
        self.assertEqual(phase["execution_status"], "CLOSED")
        self.assertEqual(phase["acceptance_status"], "NOT_EARNED")
        self.assertEqual(phase["terminal"], "CLOSED_INCOMPLETE")
        verdicts = [clause["verdict"] for clause in phase["exit_clauses"]]
        self.assertEqual(verdicts.count("EARNED"), 0)


class EstimateMaturity(unittest.TestCase):
    """An estimate is only as firm as the stage of the thing it sizes."""

    def test_a_point_admits_only_a_discovery_envelope(self) -> None:
        self.assertEqual(estimatemod.admitted_maturity("ROOT_POINT"), "DISCOVERY_ENVELOPE")
        self.assertEqual(estimatemod.admitted_maturity("VERTICAL_SLICE"), "WIDE_RANGE")
        self.assertEqual(estimatemod.admitted_maturity("HORIZONTAL_SURFACE"),
                         "COMMITTED_RANGE")

    def test_committing_at_a_point_is_refused(self) -> None:
        estimate = {"estimated_by": "p", "maturity": "COMMITTED_RANGE",
                    "dimensions": [{"dimension_id": "tokens", "low": 1, "high": 2}]}
        codes = {code for code, _ in estimatemod.grade(estimate, None, "ROOT_POINT")}
        self.assertIn("OVERCOMMITTED_ESTIMATE", codes)

    def test_a_weaker_maturity_is_always_admissible(self) -> None:
        estimate = {"estimated_by": "p", "maturity": "DISCOVERY_ENVELOPE",
                    "dimensions": [{"dimension_id": "tokens", "low": 1, "high": 2}]}
        for stage in circuitmod.stage_names():
            with self.subTest(stage=stage):
                self.assertEqual(estimatemod.grade(estimate, None, stage), [])

    def test_every_shipped_estimate_is_within_its_stage(self) -> None:
        for custody in modelmod.custodies():
            with self.subTest(custody=custody["custody_id"]):
                ceiling = estimatemod.admitted_maturity(custody["entry_stage"])
                claimed = custody["estimate"]["maturity"]
                self.assertLessEqual(estimatemod.MATURITY_ORDER.index(claimed),
                                     estimatemod.MATURITY_ORDER.index(ceiling))

    def test_a_derived_dimension_is_refused(self) -> None:
        codes = {code for code, _ in estimatemod.grade_registry(
            {"velocity": {"graded": True, "actual_source": "computed",
                          "derived_from": ["points", "wall_clock_seconds"]}})}
        self.assertIn("SYNTHETIC_SCORE", codes)


class BoardDerivation(unittest.TestCase):
    """A board is computed, and progress is read from the least-drawn member."""

    def test_progress_reads_from_the_laggard_not_the_frontier(self) -> None:
        custody = copy.deepcopy(modelmod.by_id("custody:oracle-predicate-join"))
        built = boardmod.build(custody, with_derived=False)
        self.assertEqual(built["lowest_member_stage"], "ROOT_POINT")
        self.assertEqual(built["highest_member_stage"], "VERTICAL_SLICE")
        self.assertEqual(built["stages_to_target"], 2)

    def test_a_custody_with_no_members_falls_back_to_its_entry_stage(self) -> None:
        custody = copy.deepcopy(modelmod.by_id("custody:oracle-predicate-join"))
        custody["members"] = []
        built = boardmod.build(custody, with_derived=False)
        self.assertIsNone(built["lowest_member_stage"])
        self.assertEqual(built["stages_to_target"], 1)

    def test_the_worklist_join_matches_uri_and_dotted_addresses(self) -> None:
        custody = {"members": [{"address": "services/observation"},
                               {"address": "console.grant"}]}
        items = [
            {"item_id": "a", "subject": {"address": "sov://observation/observe-run",
                                         "service_id": "observation"}},
            {"item_id": "b", "subject": {"address": "sov://console/grant",
                                         "service_id": "console"}},
            {"item_id": "c", "subject": {"address": "sov://asset/put", "service_id": "asset"}},
        ]
        matched = {item["item_id"] for item in boardmod.attached(custody, items)}
        self.assertEqual(matched, {"a", "b"})

    def test_rendering_names_the_dimensions_a_board_is_missing(self) -> None:
        custody = copy.deepcopy(modelmod.by_id("custody:oracle-predicate-join"))
        custody["estimate"]["dimensions"] = [
            row for row in custody["estimate"]["dimensions"]
            if row["dimension_id"] != "judgement_units"]
        text = boardmod.render(boardmod.build(custody, with_derived=False))
        self.assertIn("MISSING_REQUIRED_DIMENSION", text)
        self.assertIn("judgement_units", text)


class SelfcheckInProcess(unittest.TestCase):
    """The declared corpus is graded here rather than in a second subprocess.

    `python scripts/sov_custody.py selfcheck` runs the same judges by hand.
    Calling it in process keeps the verify budget flat: process start is most of
    what a check costs, and this suite is already paying for one.
    """

    def test_every_declared_refusal_is_reached_by_a_case(self) -> None:
        declared = (set(circuitmod.declared_refusals())
                    | set(estimatemod.declared_refusals())
                    | set(modelmod.REFUSALS) | set(phasemod.REFUSALS))
        fired: set[str] = set()
        for record in CORPUS:
            judge = record["judge"]
            if judge == "circuit":
                defects = circuitmod.judge_advance(
                    record.get("from_stage", ""), record["to_stage"],
                    record.get("evidence") or {},
                    set(record.get("required_dimensions") or []))
            elif judge == "estimate":
                defects = estimatemod.grade(
                    record.get("estimate"), set(record.get("required") or []),
                    record.get("stage"))
            elif judge == "collection":
                defects = modelmod.grade_collection(record["custodies"])
            elif judge == "registry":
                defects = estimatemod.grade_registry(record["registry"])
            elif judge == "phase":
                defects = phasemod.grade(record["phase"],
                                         set(record.get("custody_ids") or []))
            else:
                defects = modelmod.grade(record["custody"], set(record.get("seats") or []))
            codes = {code for code, _ in defects}
            fired |= codes
            with self.subTest(case=record["id"]):
                if record["polarity"] == "positive":
                    self.assertEqual(codes, set(), f"{record['id']} refused an admissible case")
                else:
                    self.assertTrue(set(record["expect_refusals"]) <= codes,
                                    f"{record['id']} expected {record['expect_refusals']}, "
                                    f"got {sorted(codes)}")
        self.assertEqual(declared - fired, set(),
                         "a declared refusal no case proves fires is a refusal nobody can rely on")


class CorpusIntegrity(unittest.TestCase):
    """The corpus states what it claims to state."""

    def test_every_defeating_case_names_the_refusal_it_expects(self) -> None:
        for record in CORPUS:
            if record["polarity"] == "defeating":
                self.assertTrue(record.get("expect_refusals"), record["id"])

    def test_every_case_says_why_it_exists(self) -> None:
        for record in CORPUS:
            self.assertTrue(record.get("why"), record["id"])

    def test_both_polarities_are_present_for_every_judge(self) -> None:
        judges: dict[str, set[str]] = {}
        for record in CORPUS:
            judges.setdefault(record["judge"], set()).add(record["polarity"])
        for judge, polarities in judges.items():
            with self.subTest(judge=judge):
                self.assertIn("defeating", polarities)

    def test_no_expected_refusal_is_undeclared(self) -> None:
        declared = (set(circuitmod.declared_refusals())
                    | set(estimatemod.declared_refusals())
                    | set(modelmod.REFUSALS) | set(phasemod.REFUSALS))
        for record in CORPUS:
            for code in record.get("expect_refusals") or []:
                self.assertIn(code, declared, record["id"])


if __name__ == "__main__":
    unittest.main()
