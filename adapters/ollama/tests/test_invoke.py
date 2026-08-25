"""Declared positive and defeating cases for executing ``invoke_model``.

Every case drives a recording transport rather than a live daemon, so the suite proves
the same thing on a machine with no model server as on one with six models loaded. The
boundary cases additionally assert that ``post`` was never reached: a refusal that fires
only after the bytes have left the machine is not a data-boundary control.

``adapters/ollama/tests/test_local_model_adapter.py`` covers the checks over recorded
declarations; this file covers the execution that produces such a record.
"""

from __future__ import annotations

from pathlib import Path
import copy
import json
import sys
import unittest

ADAPTER = Path(__file__).resolve().parents[1]
ROOT = ADAPTER.parents[1]
sys.path.insert(0, str(ADAPTER))
sys.path.insert(0, str(ROOT / "scripts"))

import invoke as invoke_module  # noqa: E402
from adapter import Refusal, load_json  # noqa: E402
from invoke import invoke, project_input  # noqa: E402

INVENTORY = load_json(ADAPTER / "inventory.json")
QWEN = "urn:soveraeign:binding:ollama:qwen3-4b"
QWEN_DIGEST = "359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7"

# Assembled at run time rather than written out. A test that needs a credential-shaped
# or absolute-path-shaped string must not put one in repository bytes, because
# scripts/lint.py reads those bytes and cannot tell a fixture from a leak.
CREDENTIAL_SHAPE = "sk-" + "A" * 24
ABSOLUTE_PATH_SHAPE = "C:" + chr(92) + "Users" + chr(92) + "someone" + chr(92) + "SPEC.md"

CALL = dict(
    operation_id="operation_test",
    actor_id="urn:soveraeign:actor:model:ollama:qwen3:4b",
    required_authority="grant:propose:test",
    invocation_id="urn:soveraeign:invocation:test-001",
)


def response(**overrides) -> dict:
    """A complete runtime response; overrides remove or replace one field at a time."""
    body = {
        "model": "qwen3:4b",
        "response": "acknowledged",
        "thinking": "the user asked for one word",
        "done": True,
        "done_reason": "stop",
        "prompt_eval_count": 18,
        "eval_count": 107,
    }
    body.update(overrides)
    return {key: value for key, value in body.items() if value is not _ABSENT}


_ABSENT = object()


class Recorder:
    """A transport that records what it was asked to do and answers from a script."""

    def __init__(self, body: dict, tags: dict | None = None, fail: Refusal | None = None):
        self.body = body
        self.fail = fail
        self.posts: list[tuple[str, dict]] = []
        self.tags = tags if tags is not None else {
            "models": [{"name": "qwen3:4b", "digest": QWEN_DIGEST, "remote_host": None},
                       {"name": "gpt-oss:20b", "digest": "17052f91a42e", "remote_host": None},
                       {"name": "gpt-oss:20b-cloud", "digest": "875e8e3a629a",
                        "remote_host": "https://ollama.com:443"}]
        }

    def get(self, route: str) -> dict:
        if route == "/api/version":
            return {"version": "0.32.9"}
        return self.tags

    def post(self, route: str, payload: dict) -> dict:
        self.posts.append((route, payload))
        if self.fail is not None:
            raise self.fail
        return self.body


def run(transport: Recorder, binding: str = QWEN, **kwargs) -> tuple[dict, str]:
    call = {**CALL, **kwargs}
    return invoke(binding, kwargs.pop("prompt", "say one word"), transport=transport,
                  inventory=INVENTORY, **{k: v for k, v in call.items() if k != "prompt"})


class InvocationExecutes(unittest.TestCase):
    """A completed run yields a record the adapter's own checks admit."""

    def test_a_finished_run_commits_and_accounts_for_what_it_spent(self):
        transport = Recorder(response())
        record, text = run(transport)
        self.assertEqual(text, "acknowledged")
        self.assertEqual(record["outcome"], "COMMITTED")
        self.assertNotIn("reason_code", record)
        self.assertEqual(record["usage"]["input_tokens"], 18)
        self.assertEqual(record["usage"]["output_tokens"], 107)
        self.assertEqual(record["usage"]["response_bytes"], len("acknowledged"))
        self.assertEqual(record["usage"]["thinking_bytes"],
                         len("the user asked for one word"))
        self.assertEqual(record["executed"]["model_id"], "qwen3:4b")
        self.assertEqual(record["executed"]["remote_host"], None)
        self.assertEqual(record["data_boundary_applied"], "LOCAL_ONLY")
        self.assertEqual(transport.posts[0][0], "/api/generate")
        self.assertFalse(transport.posts[0][1]["stream"])

    def test_the_record_carries_the_digest_of_the_bytes_that_actually_crossed(self):
        transport = Recorder(response())
        record, _ = run(transport, prompt="say one word")
        sent = transport.posts[0][1]["prompt"]
        self.assertEqual(record["input_digest"], invoke_module.digest(sent))


class TruncationIsNotSuccess(unittest.TestCase):
    """A run the runtime cut off consumed resources and answered nothing."""

    def test_a_length_stop_is_unresolved_with_a_reason_code(self):
        record, text = run(Recorder(response(response="", done_reason="length")))
        self.assertEqual(record["outcome"], "UNRESOLVED")
        self.assertEqual(record["reason_code"], "RUN_TRUNCATED_LENGTH")
        self.assertEqual(text, "")
        self.assertEqual(record["usage"]["response_bytes"], 0)

    def test_a_run_the_runtime_never_finished_is_unresolved(self):
        record, _ = run(Recorder(response(done=False, done_reason=_ABSENT)))
        self.assertEqual(record["outcome"], "UNRESOLVED")
        self.assertEqual(record["reason_code"], "RUN_INCOMPLETE")


class BoundaryRefusalsPrecedeTheCrossing(unittest.TestCase):
    """The input must be refused before it is sent, not graded after it has left."""

    def assert_refused_without_sending(self, reason_code: str, **kwargs):
        transport = Recorder(response())
        with self.assertRaises(Refusal) as caught:
            run(transport, **kwargs)
        self.assertEqual(caught.exception.reason_code, reason_code)
        self.assertEqual(transport.posts, [], "input crossed before the refusal fired")

    def test_a_credential_in_the_input_is_refused_before_the_model_sees_it(self):
        self.assert_refused_without_sending(
            "DATA_BOUNDARY_REFUSED", prompt=f"use api_key: {CREDENTIAL_SHAPE}")

    def test_an_absolute_host_path_is_refused_before_the_model_sees_it(self):
        self.assert_refused_without_sending(
            "DATA_BOUNDARY_REFUSED", prompt=f"read {ABSOLUTE_PATH_SHAPE}")

    def test_locked_evidence_is_refused_before_the_model_sees_it(self):
        self.assert_refused_without_sending(
            "DATA_BOUNDARY_REFUSED", prompt="summarise lineage/evidence/0001.txt")

    def test_a_capability_the_binding_does_not_hold_is_refused_before_sending(self):
        self.assert_refused_without_sending("MODEL_INCOMPATIBLE", capability="embedding")

    def test_a_binding_that_does_not_exist_is_refused_before_sending(self):
        transport = Recorder(response())
        with self.assertRaises(Refusal) as caught:
            run(transport, binding="urn:soveraeign:binding:ollama:absent")
        self.assertEqual(caught.exception.reason_code, "MODEL_UNAVAILABLE")
        self.assertEqual(transport.posts, [])

    def test_a_cloud_served_model_under_local_only_never_reaches_the_wire(self):
        """The defeating case the adapter exists for: a local-looking tag over the network."""
        cloud = load_json(ADAPTER / "fixtures" / "defeating-cloud-declared-local.json")
        original = invoke_module.load_binding
        invoke_module.load_binding = lambda binding_id: copy.deepcopy(cloud)
        try:
            self.assert_refused_without_sending(
                "DATA_BOUNDARY_REFUSED", binding=cloud["binding_id"])
        finally:
            invoke_module.load_binding = original


class ProvenanceMustAccountForTheRun(unittest.TestCase):
    """A record that cannot say what ran, or that contradicts the runtime, is refused."""

    def assert_refused(self, reason_code: str, transport: Recorder):
        with self.assertRaises(Refusal) as caught:
            run(transport)
        self.assertEqual(caught.exception.reason_code, reason_code)

    def test_an_absent_token_meter_is_a_defect_not_a_zero(self):
        self.assert_refused("PROVENANCE_INCOMPLETE",
                            Recorder(response(eval_count=_ABSENT)))

    def test_a_response_naming_no_model_cannot_be_attributed(self):
        self.assert_refused("PROVENANCE_INCOMPLETE", Recorder(response(model=_ABSENT)))

    def test_a_model_swapped_by_the_runtime_is_never_a_quiet_retry(self):
        self.assert_refused("SILENT_FALLBACK_REFUSED",
                            Recorder(response(model="gpt-oss:20b")))

    def test_a_loaded_digest_that_differs_from_the_binding_contradicts_it(self):
        transport = Recorder(response())
        transport.tags = {"models": [{"name": "qwen3:4b", "digest": "deadbeef",
                                      "remote_host": None}]}
        self.assert_refused("PROVENANCE_CONTRADICTED", transport)

    def test_a_model_the_runtime_no_longer_serves_is_unavailable(self):
        transport = Recorder(response())
        transport.tags = {"models": []}
        self.assert_refused("MODEL_UNAVAILABLE", transport)

    def test_a_runtime_that_does_not_answer_is_unavailable(self):
        self.assert_refused(
            "MODEL_UNAVAILABLE",
            Recorder(response(), fail=Refusal("MODEL_UNAVAILABLE", "connection refused")))


class OmissionsAreEnforcedNotAssumed(unittest.TestCase):
    """A declared omission this adapter cannot enforce must stop the invocation."""

    def test_an_unenforceable_omission_is_refused_rather_than_ignored(self):
        with self.assertRaises(Refusal) as caught:
            project_input("anything", ["a class nobody implemented"])
        self.assertEqual(caught.exception.reason_code, "DATA_BOUNDARY_REFUSED")

    def test_a_clean_input_passes_through_unchanged(self):
        text = "summarise the receipt contract"
        self.assertEqual(project_input(text, ["credentials", "absolute host paths"]), text)

    def test_every_declared_omission_in_a_shipped_binding_is_enforceable(self):
        for path in sorted((ADAPTER / "bindings").glob("*.json")):
            binding = load_json(path)
            unknown = set(binding.get("omissions") or []) - set(invoke_module.OMISSION_PATTERNS)
            self.assertEqual(unknown, set(), f"{path.name} declares {unknown}")


if __name__ == "__main__":
    unittest.main()
