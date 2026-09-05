"""Each kernel-predicate rule, held one at a time.

The first witness pass over commit 169182f deleted nine of ten sampled oracle rules and the
control suite still read `SUITE PASS`: a control fails on its first defect, so a rule with
company is a rule nothing guards. These cases pin every rule to the exact defect it names, so
deleting one fails here even when the control it lives in would still fail for another reason.
"""

from __future__ import annotations

from pathlib import Path
import copy
import importlib.util
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


kernel = _load("kernel_predicates")
requirements = _load("requirements")
CONTROLS = {case["id"]: case for case in
            json.loads((ROOT / "oracle-controls.json").read_text(encoding="utf-8"))}


def positive(control_id: str) -> dict:
    return copy.deepcopy(CONTROLS[control_id]["observed"])


class EveryRuleNamesItsDefect(unittest.TestCase):
    def assertOnly(self, defects: list[str], expected: str) -> None:
        self.assertEqual([expected], defects)

    # PROD-I-2 reread (PRED-I-2.1)
    def test_reread_absent(self) -> None:
        observed = positive("CONF-I2-POS"); del observed["reread"]
        self.assertOnly(requirements.check_i2(observed), "source was never reread")

    def test_reread_differs(self) -> None:
        observed = positive("CONF-I2-POS"); observed["reread"]["digest"] = "sha256:other"
        self.assertOnly(requirements.check_i2(observed),
                        "source did not reread byte-identical by digest")

    # capture_source
    def test_capture_unreadable(self) -> None:
        observed = positive("CONF-CAPTURE-POS"); observed["capture"]["readable"] = False
        self.assertOnly(kernel.check_capture(observed),
                        "unreadable bytes were captured as a source")

    def test_capture_digest_mismatch(self) -> None:
        observed = positive("CONF-CAPTURE-POS"); observed["capture"]["computed_digest"] = "sha256:x"
        self.assertOnly(kernel.check_capture(observed),
                        "source captured under a digest its bytes do not carry")

    def test_capture_refused_without_reason(self) -> None:
        observed = positive("CONF-CAPTURE-POS")
        observed["capture"].update({"outcome": "REFUSED", "refusal": "BECAUSE"})
        self.assertIn("capture refused without a declared reason", kernel.check_capture(observed))

    def test_refused_capture_creating_a_source(self) -> None:
        observed = positive("CONF-CAPTURE-POS")
        observed["capture"].update({"outcome": "REFUSED", "refusal": "UNREADABLE"})
        self.assertOnly(kernel.check_capture(observed), "refused capture still created a source")

    # make_effective
    def test_effective_without_ratification(self) -> None:
        observed = positive("CONF-EFFECTIVE-POS"); observed["claim"]["standing"] = "ADMITTED"
        self.assertOnly(kernel.check_effective(observed),
                        "claim made effective without RATIFIED standing")

    def test_effective_with_policy_unmet(self) -> None:
        observed = positive("CONF-EFFECTIVE-POS"); observed["attestations"] = []
        self.assertOnly(kernel.check_effective(observed),
                        "attestation policy unmet yet claim made effective")

    def test_effective_over_dissent(self) -> None:
        observed = positive("CONF-EFFECTIVE-POS")
        observed["attestations"][0]["outcome"] = "DISSENTED"
        self.assertEqual(["attestation policy unmet yet claim made effective",
                          "claim made effective over a DISSENTED attestation"],
                         kernel.check_effective(observed))

    def test_effective_over_a_counter(self) -> None:
        observed = positive("CONF-EFFECTIVE-POS"); observed["current_counter_present"] = True
        self.assertOnly(kernel.check_effective(observed),
                        "claim made effective over a current counter")

    def test_effective_without_receipt(self) -> None:
        observed = positive("CONF-EFFECTIVE-POS"); del observed["transition"]["receipt_id"]
        self.assertOnly(kernel.check_effective(observed),
                        "effective transition left no event or receipt")

    def test_refusal_without_declared_reason(self) -> None:
        observed = positive("CONF-EFFECTIVE-POS")
        observed["transition"] = {"outcome": "REFUSED", "refusal": "MEH", "receipt_id": "r"}
        self.assertOnly(kernel.check_effective(observed),
                        "effectiveness refused without a declared reason")

    # begin_run
    def test_begin_past_failed_gate(self) -> None:
        observed = positive("CONF-RUN-POS"); observed["begin"]["gates"]["effect"] = "FAIL"
        self.assertOnly(kernel.check_run(observed), "run began past a failed gate: effect")

    def test_delegated_begin_without_lease(self) -> None:
        observed = positive("CONF-RUN-POS"); observed["begin"]["lease"] = {}
        observed["report"]["lease_fence"] = 1
        self.assertIn("delegated run began without a complete lease", kernel.check_run(observed))

    # report_run
    def test_report_under_stale_lease(self) -> None:
        observed = positive("CONF-RUN-POS"); observed["report"]["lease_fence"] = 2
        self.assertOnly(kernel.check_run(observed), "report accepted under a stale lease")

    def test_report_after_expiry(self) -> None:
        observed = positive("CONF-RUN-POS"); observed["report"]["reported_at"] = 9000
        self.assertOnly(kernel.check_run(observed), "report accepted after the lease expired")

    def test_report_that_settles(self) -> None:
        observed = positive("CONF-RUN-POS"); observed["report"]["settled"] = True
        self.assertOnly(kernel.check_run(observed), "executor report settled the run")

    def test_report_with_other_standing(self) -> None:
        observed = positive("CONF-RUN-POS"); observed["report"]["standing"] = "OBSERVATION"
        self.assertOnly(kernel.check_run(observed),
                        "executor output entered with a standing other than REPORT")

    def test_report_without_standing(self) -> None:
        observed = positive("CONF-RUN-POS"); del observed["report"]["standing"]
        self.assertEqual(["report missing standing",
                          "executor output entered with a standing other than REPORT"],
                         kernel.check_run(observed))

    # observe_run
    def test_executor_observing_itself(self) -> None:
        observed = positive("CONF-RUN-POS"); observed["observation"]["observer_id"] = "worker-a"
        self.assertOnly(kernel.check_run(observed), "executor observed its own run")

    def test_observation_without_independent_inference(self) -> None:
        observed = positive("CONF-RUN-POS")
        observed["observation"]["relation_inference"]["outcome"] = "UNDETERMINED"
        observed["observation"]["relation_inference"]["record_completeness"] = "INCOMPLETE"
        self.assertEqual(["observation admitted without an INDEPENDENT inference (UNDETERMINED)",
                          "independence read over an incomplete record"],
                         kernel.check_run(observed))

    def test_observation_with_a_direct_edge(self) -> None:
        observed = positive("CONF-RUN-POS")
        inference = observed["observation"]["relation_inference"]
        inference["edges_found"] = [{"edge": "HOLDS_RUN_LEASE"}]
        self.assertOnly(kernel.check_run(observed),
                        "observation admitted with a direct edge to the run")

    def test_predicates_declared_late(self) -> None:
        observed = positive("CONF-RUN-POS")
        observed["observation"]["predicates_declared_at"] = 1800
        self.assertOnly(kernel.check_run(observed), "predicates declared after the looking")

    def test_observer_read_nothing_of_the_run(self) -> None:
        observed = positive("CONF-RUN-POS")
        observed["observation"]["observed_state_addresses"] = ["x"]
        self.assertOnly(kernel.check_run(observed),
                        "observer read none of the run's durable outputs")

    def test_digests_misaligned(self) -> None:
        observed = positive("CONF-RUN-POS")
        observed["observation"]["observed_state_digests"] = ["sha256:one", "sha256:two"]
        self.assertOnly(kernel.check_run(observed),
                        "observed digests do not align with observed addresses")

    def test_observation_with_other_standing(self) -> None:
        observed = positive("CONF-RUN-POS"); observed["observation"]["standing"] = "REPORT"
        self.assertOnly(kernel.check_run(observed),
                        "observation entered with a standing other than OBSERVATION")

    # settle_run
    def test_settlement_citing_no_observation(self) -> None:
        observed = positive("CONF-RUN-POS"); observed["settlement"]["observation_id"] = "obs-none"
        self.assertOnly(kernel.check_run(observed), "settlement cites no observation of this run")

    def test_settlement_against_stale_state(self) -> None:
        observed = positive("CONF-RUN-POS")
        observed["settlement"]["current_state_digest"] = "sha256:z"
        self.assertOnly(kernel.check_run(observed), "run settled against a stale state")

    def test_settlement_on_another_input_state(self) -> None:
        observed = positive("CONF-RUN-POS")
        observed["settlement"]["input_state_digest"] = "sha256:q"
        observed["settlement"]["current_state_digest"] = "sha256:q"
        self.assertOnly(kernel.check_run(observed),
                        "settlement input state is not the state the run began on")

    def test_settlement_with_non_terminal_outcome(self) -> None:
        observed = positive("CONF-RUN-POS"); observed["settlement"]["outcome"] = "REPORTED"
        self.assertOnly(kernel.check_run(observed),
                        "settlement outcome is not a terminal receipt outcome")

    def test_commit_against_failed_predicate(self) -> None:
        observed = positive("CONF-RUN-POS")
        observed["observation"]["predicate_results"]["output-digest-declared"] = False
        self.assertOnly(kernel.check_run(observed), "run committed against a failed predicate")

    def test_participant_settling_its_own_run(self) -> None:
        observed = positive("CONF-RUN-POS"); observed["settlement"]["settled_by"] = "witness-z"
        self.assertOnly(kernel.check_run(observed), "a participant in the run settled it")

    def test_settlement_without_receipt(self) -> None:
        observed = positive("CONF-RUN-POS"); del observed["settlement"]["receipt_id"]
        self.assertOnly(kernel.check_run(observed), "settlement missing receipt_id")

    # PARITY-1
    def test_discovery_of_different_operations(self) -> None:
        observed = positive("CONF-DISCOVERY-POS"); observed["model"]["operations"].pop()
        self.assertOnly(kernel.check_discovery(observed),
                        "bindings do not discover the same legal operations: record.read-entry")

    def test_discovery_of_different_inputs(self) -> None:
        observed = positive("CONF-DISCOVERY-POS")
        observed["human"]["operations"][0]["required_inputs"] = ["source_address"]
        self.assertOnly(kernel.check_discovery(observed),
                        "bindings do not discover the same required inputs: asset.capture-source")

    def test_discovery_from_another_interface(self) -> None:
        observed = positive("CONF-DISCOVERY-POS"); observed["model"]["interface_id"] = "other/v1"
        self.assertOnly(kernel.check_discovery(observed),
                        "model binding discovered from a different interface")

    def test_discovery_naming_no_interface(self) -> None:
        observed = positive("CONF-DISCOVERY-POS"); del observed["interface_id"]
        self.assertEqual(["discovery names no interface",
                          "human binding discovered from a different interface",
                          "model binding discovered from a different interface"],
                         kernel.check_discovery(observed))

    def test_discovery_binding_missing_a_field(self) -> None:
        observed = positive("CONF-DISCOVERY-POS"); del observed["human"]["discovery_receipt_id"]
        self.assertOnly(kernel.check_discovery(observed),
                        "human binding missing discovery_receipt_id")

    def test_discovery_of_an_operation_without_id_or_inputs(self) -> None:
        observed = positive("CONF-DISCOVERY-POS")
        operation = observed["model"]["operations"][0]
        del operation["required_inputs"]
        self.assertEqual(["model binding discovered an operation without id or inputs",
                          f"bindings do not discover the same legal operations: "
                          f"{operation['operation_id']}"],
                         kernel.check_discovery(observed))


class EveryDeclaredPredicateIsExercised(unittest.TestCase):
    """The defeat `custody:oracle-predicate-join` names: a control claiming a predicate its
    defects never touch. Each defeating control's defects must name the transition it claims."""

    #: Defect prefixes each rule family emits, so a control is credited for a predicate only
    #: when one of that predicate's own rules fired: "cites no observation" is a settlement
    #: defect and must not credit observe_run.
    WORDS = {
        "TRANS-capture_source": ("unreadable bytes were captured", "source captured under",
                                 "committed capture created", "capture refused",
                                 "refused capture still", "capture outcome"),
        "TRANS-make_effective": ("claim made effective", "attestation policy unmet",
                                 "effective transition left", "effectiveness refused",
                                 "refused claim reads", "make_effective outcome"),
        "TRANS-begin_run": ("run began past", "delegated run began", "begin refused",
                            "begin event is"),
        "TRANS-report_run": ("report accepted", "executor output entered",
                             "executor report settled"),
        "TRANS-observe_run": ("executor observed", "observation admitted",
                              "independence read over", "predicates declared after",
                              "observer read none", "observed digests do not align",
                              "observation entered"),
        "TRANS-settle_run": ("settlement cites", "run settled against", "settlement input state",
                             "settlement outcome", "run committed against",
                             "a participant in the run settled"),
        "PARITY-1": ("bindings do not discover", "binding discovered from"),
        "PRED-I-2.1": ("source was never reread", "source did not reread"),
    }

    def test_defeating_controls_defeat_what_they_claim(self) -> None:
        for control in CONTROLS.values():
            if control["polarity"] != "defeating":
                continue
            defects = " ".join(requirements.CHECKS[control["requirement"]](control["observed"]))
            for predicate in control["predicates"]:
                words = self.WORDS.get(predicate)
                if words is None:
                    continue
                with self.subTest(control=control["id"], predicate=predicate):
                    self.assertTrue(any(word in defects for word in words),
                                    f"{control['id']} claims {predicate}; defects: {defects}")


if __name__ == "__main__":
    unittest.main()
