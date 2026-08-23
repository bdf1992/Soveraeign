"""Cases for the three-tier loop and its separation rules.

Every rule has a run that satisfies it and a run that defeats it. The model call
is injected everywhere, so no case reaches a network, and the live binding is
exercised only through its refusals.
"""

from __future__ import annotations

from pathlib import Path
import copy
import json
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sovloop import ollama  # noqa: E402
from sovloop import rules  # noqa: E402
from sovloop import run as loop  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "conformance" / "fixtures" / "loop" / "tier-cases.json"

RECEIPT_REQUIRED = ("receipt_id", "event_id", "event_type", "actor_id", "interface_id",
                    "input_addresses", "input_state_digest", "authority_grant_ids",
                    "precondition_results", "effect_class", "outcome",
                    "emitted_record_addresses", "observed_evidence_addresses",
                    "created_at", "receipt_digest")

GPT = "urn:soveraeign:binding:ollama:gpt-oss-20b"
QWEN = "urn:soveraeign:binding:ollama:qwen3-4b"


def recorded(binding_id: str, prompt: str, *, purpose: str) -> dict:
    """A recorded invocation standing in for a model call."""
    model = {GPT: "gpt-oss:20b", QWEN: "qwen3:4b"}[binding_id]
    return {
        "invocation_id": f"urn:soveraeign:invocation:{purpose.lower()}", "purpose": purpose,
        "binding_id": binding_id, "adapter_id": "urn:soveraeign:adapter:ollama",
        "provider_id": "urn:soveraeign:provider:ollama:local-node", "model_id": model,
        "model_version": "sha256:recorded", "runtime_id": "ollama",
        "host_id": "urn:soveraeign:host:local-node",
        "input_projection_id": "urn:soveraeign:projection:operation-input:redacted-local",
        "data_boundary": "LOCAL_ONLY", "omissions": ["credentials"],
        "usage": {"input_tokens": 8, "output_tokens": 4, "wall_clock_seconds": 0.1},
        "cost": {"unit": "USD", "amount": 0, "basis": "OWNER_OWNED_HARDWARE"},
        "output_text": f"recorded {purpose} output",
    }


class Corpus(unittest.TestCase):
    """The declared positive and defeating corpus, case by case."""

    def setUp(self):
        self.table = rules.load_table(ROOT)
        self.cases = json.loads(CORPUS.read_bytes().decode("utf-8"))["cases"]

    def test_every_case_refuses_exactly_as_declared(self):
        for case in self.cases:
            with self.subTest(case=case["case_id"]):
                observed = sorted({d.split(":", 1)[0]
                                   for d in rules.audit(case["run"], self.table)})
                self.assertEqual(observed, sorted(case["expect_refusals"]))

    def test_the_corpus_exercises_every_rule(self):
        declared = set(self.table["refusal_codes"])
        exercised = {code for case in self.cases for code in case["expect_refusals"]}
        self.assertEqual(declared - exercised, set(),
                         "a declared refusal code no case proves is enforced")

    def test_at_least_one_case_passes_and_one_fails(self):
        outcomes = [bool(case["expect_refusals"]) for case in self.cases]
        self.assertIn(True, outcomes)
        self.assertIn(False, outcomes)


class Loop(unittest.TestCase):
    """Executing the loop end to end against a recorded model."""

    def setUp(self):
        self.table = rules.load_table(ROOT)
        self.run = loop.execute("an objective", self.table, recorded, "1970-01-01T00:00:00Z")

    def test_a_clean_run_carries_no_defect_and_settles(self):
        self.assertEqual(self.run["defects"], [])
        self.assertEqual(self.run["settlement"]["outcome"], "COMMITTED")

    def test_the_chain_is_exactly_three_tiers_in_order(self):
        self.assertEqual([s["tier"] for s in self.run["chain"]],
                         ["CONTROL", "ORCHESTRATION", "WORK"])

    def test_the_observer_is_not_the_binding_that_produced_the_output(self):
        self.assertNotEqual(self.run["observation"]["observer_binding_id"],
                            self.run["observation"]["observed_binding_id"])

    def test_the_controller_settles_and_the_worker_does_not(self):
        self.assertNotEqual(self.run["settlement"]["settled_by"],
                            self.run["report"]["produced_by"])

    def test_every_step_emits_a_receipt_with_the_required_fields(self):
        self.assertEqual(len(self.run["receipts"]), 4)
        for receipt in self.run["receipts"]:
            for field in RECEIPT_REQUIRED:
                self.assertIn(field, receipt)

    def test_a_defective_run_settles_unresolved_rather_than_committed(self):
        table = copy.deepcopy(self.table)
        table["observation"]["observer_binding_id"] = table["tiers"]["WORK"]["binding_id"]
        defective = loop.execute("an objective", table, recorded, "1970-01-01T00:00:00Z")
        self.assertTrue(defective["defects"])
        self.assertEqual(defective["settlement"]["outcome"], "UNRESOLVED")

    def test_scope_narrows_strictly_at_every_step(self):
        scopes = [step["scope"] for step in self.run["chain"]]
        for parent, child in zip(scopes, scopes[1:]):
            self.assertTrue(child.startswith(parent + "/"), f"{child} not inside {parent}")


class LiveBinding(unittest.TestCase):
    """The live Ollama binding, exercised through its refusals only."""

    def test_an_undeclared_binding_refuses(self):
        with self.assertRaises(ollama.Refusal) as caught:
            ollama.load_binding("urn:soveraeign:binding:ollama:not-declared")
        self.assertIn("MODEL_INCOMPATIBLE", str(caught.exception))

    def test_a_declared_binding_loads(self):
        self.assertEqual(ollama.load_binding(QWEN)["model_id"], "qwen3:4b")

    def test_the_projection_withholds_declared_omissions(self):
        projected = ollama.project_input("keep this\ncredentials: secret\nkeep that",
                                         ["credentials"])
        self.assertEqual(projected, "keep this\nkeep that")
        self.assertNotIn("secret", projected)

    def test_an_unreachable_runtime_refuses_rather_than_substituting(self):
        original = ollama._post
        try:
            ollama._post = lambda *a, **k: (_ for _ in ()).throw(OSError("connection refused"))
            with self.assertRaises(ollama.Refusal) as caught:
                ollama.invoke(QWEN, "anything", purpose="WORK")
        finally:
            ollama._post = original
        self.assertIn("MODEL_UNAVAILABLE", str(caught.exception))

    def test_a_non_local_boundary_refuses(self):
        original = ollama.load_binding
        try:
            ollama.load_binding = lambda _: {"data_boundary": "REMOTE", "model_id": "x"}
            with self.assertRaises(ollama.Refusal) as caught:
                ollama.invoke(QWEN, "anything", purpose="WORK")
        finally:
            ollama.load_binding = original
        self.assertIn("DATA_BOUNDARY_REFUSED", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
