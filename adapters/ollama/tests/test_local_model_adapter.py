"""Declared positive and defeating cases for the local model adapter.

Every case names its fixture, its check, and the exact outcome or reason code it must
produce. The suite fails while any refusal code the adapter can raise has no fixture
exercising it, so a code cannot be added and left unproven.

These tests read ``inventory.json``. They never contact the runtime: a check that needed
a live daemon would pass on a machine where one happens to be running and say nothing
about the binding it was meant to check.
"""

from __future__ import annotations

from pathlib import Path
import json
import sys
import unittest

ADAPTER = Path(__file__).resolve().parents[1]
ROOT = ADAPTER.parents[1]
sys.path.insert(0, str(ADAPTER))
sys.path.insert(0, str(ROOT / "scripts"))

import adapter as adapter_module  # noqa: E402
from adapter import Refusal, check_binding, check_invocation, check_parity  # noqa: E402

FIXTURES = ADAPTER / "fixtures"
POSITIVE_A = "invocation-qwen3-4b"
POSITIVE_B = "invocation-gpt-oss-20b"

BINDING_CASES = (
    ("defeating-cloud-declared-local", "DATA_BOUNDARY_REFUSED"),
    ("defeating-absent-model", "MODEL_UNAVAILABLE"),
    ("defeating-stale-model-version", "MODEL_UNAVAILABLE"),
    ("defeating-capability-not-held", "MODEL_INCOMPATIBLE"),
    ("defeating-remote-declared-for-local", "PROVENANCE_CONTRADICTED"),
    ("defeating-foreign-adapter", "PROVENANCE_CONTRADICTED"),
)
INVOCATION_CASES = (
    ("defeating-silent-fallback", "SILENT_FALLBACK_REFUSED"),
    ("defeating-provenance-omitted", "PROVENANCE_INCOMPLETE"),
    ("defeating-meter-absent", "PROVENANCE_INCOMPLETE"),
    ("defeating-authoritative-role", "PROVENANCE_CONTRADICTED"),
    ("defeating-crossed-under-local-only", "DATA_BOUNDARY_REFUSED"),
    ("defeating-unbound-capability", "MODEL_INCOMPATIBLE"),
)
PARITY_CASES = (
    ("defeating-parity-same-model", "MODEL_INCOMPATIBLE"),
    ("defeating-parity-authority-differs", "PROVENANCE_CONTRADICTED"),
)
DECLARED_CODES = frozenset({"MODEL_UNAVAILABLE", "MODEL_INCOMPATIBLE", "DATA_BOUNDARY_REFUSED",
                            "SILENT_FALLBACK_REFUSED", "PROVENANCE_INCOMPLETE",
                            "PROVENANCE_CONTRADICTED"})


def fixture(stem: str) -> dict:
    return json.loads((FIXTURES / f"{stem}.json").read_text(encoding="utf-8"))


class DeclaredBindingTests(unittest.TestCase):
    def test_every_declared_binding_is_accepted(self) -> None:
        paths = sorted(adapter_module.BINDINGS_DIR.glob("*.json"))
        self.assertGreaterEqual(len(paths), 2,
                                "PROD-I-9 needs at least two declared bindings to prove parity")
        for path in paths:
            with self.subTest(binding=path.name):
                result = check_binding(json.loads(path.read_text(encoding="utf-8")))
                self.assertEqual(result["outcome"], "ACCEPTED")
                self.assertEqual(result["provider_kind"], "LOCAL")
                self.assertEqual(result["data_boundary"], "LOCAL_ONLY")
                self.assertFalse(result["authority_granted"])

    def test_every_binding_names_a_materially_different_model(self) -> None:
        """No two declared bindings may name the same model.

        PROD-I-9 needs two materially different bindings; it does not cap the
        count. Requiring every binding to name a distinct model keeps that proof
        intact as bindings are added, and is stricter than checking a fixed pair:
        a duplicate anywhere in the set now fails.
        """
        paths = sorted(adapter_module.BINDINGS_DIR.glob("*.json"))
        models = [json.loads(path.read_text(encoding="utf-8"))["model_id"] for path in paths]
        self.assertGreaterEqual(len(set(models)), 2, models)
        self.assertEqual(len(set(models)), len(models),
                         f"two bindings name the same model: {models}")

    def test_no_two_bindings_share_a_model_version(self) -> None:
        """A digest repeated across bindings means one of them records a lie."""
        paths = sorted(adapter_module.BINDINGS_DIR.glob("*.json"))
        versions = [json.loads(path.read_text(encoding="utf-8"))["model_version"]
                    for path in paths]
        self.assertEqual(len(set(versions)), len(versions),
                         f"two bindings record the same model_version: {versions}")

    def test_binding_refusals(self) -> None:
        for stem, code in BINDING_CASES:
            with self.subTest(fixture=stem):
                with self.assertRaises(Refusal) as caught:
                    check_binding(fixture(stem))
                self.assertEqual(caught.exception.reason_code, code)


class InvocationTests(unittest.TestCase):
    def test_both_positive_invocations_are_accepted(self) -> None:
        for stem in (POSITIVE_A, POSITIVE_B):
            with self.subTest(fixture=stem):
                result = check_invocation(fixture(stem))
                self.assertEqual(result["outcome"], "ACCEPTED")
                self.assertEqual(result["information_role"], "PROPOSAL")
                self.assertFalse(result["authority_granted"])

    def test_invocation_refusals(self) -> None:
        for stem, code in INVOCATION_CASES:
            with self.subTest(fixture=stem):
                with self.assertRaises(Refusal) as caught:
                    check_invocation(fixture(stem))
                self.assertEqual(caught.exception.reason_code, code)

    def test_an_explicit_fallback_policy_still_refuses_substitution_in_place(self) -> None:
        """EXPLICIT permits a replacement binding, never a quiet swap inside one invocation."""
        record = fixture("defeating-silent-fallback")
        record["fallback_from_binding_id"] = "urn:soveraeign:binding:ollama:qwen3-4b"
        binding = dict(adapter_module.load_binding(record["binding_id"]))
        binding["fallback_policy"] = "EXPLICIT"
        with self.assertRaises(Refusal) as caught:
            adapter_module._check_no_substitution(record, binding, record["executed"])
        self.assertEqual(caught.exception.reason_code, "SILENT_FALLBACK_REFUSED")
        self.assertIn("new invocation", caught.exception.detail)

    def test_an_invocation_may_not_name_an_undeclared_binding(self) -> None:
        record = fixture(POSITIVE_A)
        record["binding_id"] = "urn:soveraeign:binding:ollama:never-declared"
        with self.assertRaises(Refusal) as caught:
            check_invocation(record)
        self.assertEqual(caught.exception.reason_code, "MODEL_UNAVAILABLE")


class ParityTests(unittest.TestCase):
    def test_two_models_run_one_operation_without_moving_authority(self) -> None:
        result = check_parity(fixture(POSITIVE_A), fixture(POSITIVE_B))
        self.assertEqual(result["outcome"], "ACCEPTED")
        self.assertEqual(result["models"], ["gpt-oss:20b", "qwen3:4b"])
        self.assertFalse(result["authority_changed_with_model"])

    def test_parity_refusals(self) -> None:
        for stem, code in PARITY_CASES:
            with self.subTest(fixture=stem):
                with self.assertRaises(Refusal) as caught:
                    check_parity(fixture(POSITIVE_A), fixture(stem))
                self.assertEqual(caught.exception.reason_code, code)


class InventoryTests(unittest.TestCase):
    def test_a_tag_cannot_settle_custody(self) -> None:
        """The recorded runtime serves two models that differ only in where they execute."""
        models = {model["model_id"]: model
                  for model in adapter_module.load_json(adapter_module.INVENTORY)["models"]}
        local, cloud = models["gpt-oss:20b"], models["gpt-oss:20b-cloud"]
        compared = ("family", "parameter_size", "quantization_level", "context_length",
                    "capabilities")
        self.assertEqual([local[field] for field in compared],
                         [cloud[field] for field in compared])
        self.assertIsNone(local["remote_host"])
        self.assertTrue(cloud["remote_host"])

    def test_the_inventory_is_a_projection_and_claims_no_standing(self) -> None:
        record = adapter_module.load_json(adapter_module.INVENTORY)
        self.assertEqual(record["information_role"], "PROJECTION")
        self.assertEqual(record["standing"], "PROPOSED")
        self.assertEqual(record["source"]["effect_class"], "RECORD_LOCAL")


class CoverageTests(unittest.TestCase):
    def test_every_declared_refusal_code_has_a_fixture(self) -> None:
        exercised = {code for _, code in BINDING_CASES + INVOCATION_CASES + PARITY_CASES}
        self.assertEqual(exercised, set(DECLARED_CODES),
                         f"unexercised: {sorted(DECLARED_CODES - exercised)}")

    def test_every_defeating_fixture_is_declared_by_a_case(self) -> None:
        on_disk = {path.stem for path in FIXTURES.glob("defeating-*.json")}
        declared = {stem for stem, _ in BINDING_CASES + INVOCATION_CASES + PARITY_CASES}
        self.assertEqual(on_disk, declared, f"undeclared: {sorted(on_disk ^ declared)}")


if __name__ == "__main__":
    unittest.main()
