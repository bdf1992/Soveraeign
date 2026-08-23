"""Cases for the invocation command line.

The command is thin; ``test_invoke.py`` carries the execution cases. What is tested here
is the behaviour the command adds on top: how an invocation names itself, that an input
must be supplied rather than defaulted, and the parity rule that two cut-off runs prove
no portability. No case reaches the runtime.
"""

from __future__ import annotations

from pathlib import Path
import io
import json
import sys
import unittest
import unittest.mock

ADAPTER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ADAPTER))
sys.path.insert(0, str(ADAPTER.parents[1] / "scripts"))

import run as run_module  # noqa: E402
from adapter import Refusal  # noqa: E402

QWEN = "urn:soveraeign:binding:ollama:qwen3-4b"
GPT = "urn:soveraeign:binding:ollama:gpt-oss-20b"
BASE = ["--operation", "operation_test", "--authority", "grant:propose:test",
        "--prompt", "say one word"]


FIXTURES = ADAPTER / "fixtures"
#: The declared positive invocations. Using them rather than a hand-built stand-in keeps
#: the parity path in these cases the real ``check_parity``, not a mock of it.
POSITIVE = {"qwen3:4b": "invocation-qwen3-4b", "gpt-oss:20b": "invocation-gpt-oss-20b"}


def record(model: str, outcome: str = "COMMITTED", **extra) -> dict:
    """One declared positive invocation, with only the named fields overridden."""
    path = FIXTURES / f"{POSITIVE[model]}.json"
    body = json.loads(path.read_text(encoding="utf-8"))
    body["outcome"] = outcome
    body.update(extra)
    return body


class Capture:
    """Run the command with stdout captured, returning the exit code and the text."""

    def __init__(self, argv: list[str]):
        self.argv = argv

    def __enter__(self):
        self.buffer = io.StringIO()
        self.saved, sys.stdout = sys.stdout, self.buffer
        return self

    def __exit__(self, *unused):
        sys.stdout = self.saved
        return False

    def run(self) -> int:
        return run_module.main(self.argv)


class InvocationIdentity(unittest.TestCase):
    """An invocation is addressed by what it is, not by when it happened."""

    def test_the_same_run_names_itself_the_same_way_twice(self):
        first = run_module._identity("op", QWEN, "hello")
        self.assertEqual(first, run_module._identity("op", QWEN, "hello"))

    def test_a_different_binding_is_a_different_invocation(self):
        self.assertNotEqual(run_module._identity("op", QWEN, "hello"),
                            run_module._identity("op", GPT, "hello"))

    def test_a_different_input_is_a_different_invocation(self):
        self.assertNotEqual(run_module._identity("op", QWEN, "hello"),
                            run_module._identity("op", QWEN, "goodbye"))


class InputMustBeSupplied(unittest.TestCase):
    """An absent input is refused rather than defaulted to something the caller did not write."""

    def test_neither_prompt_nor_prompt_file_is_a_failure(self):
        parser = run_module.build_parser()
        args = parser.parse_args(["run", QWEN, "--operation", "o", "--authority", "a"])
        with self.assertRaises(SystemExit):
            run_module._prompt(args)

    def test_a_prompt_file_is_read_as_utf8(self):
        parser = run_module.build_parser()
        with unittest.mock.patch.object(Path, "read_text", return_value="from a file"):
            args = parser.parse_args(
                ["run", QWEN, "--operation", "o", "--authority", "a", "--prompt-file", "p"])
            self.assertEqual(run_module._prompt(args), "from a file")


class ParityNeedsTwoCompletedRuns(unittest.TestCase):
    """A portability claim resting on two cut-off runs reports the harness, not the models."""

    def _with(self, first: dict, second: dict) -> tuple[int, str]:
        answers = iter([(first, "a"), (second, "b")])
        with unittest.mock.patch.object(run_module, "_one",
                                        side_effect=lambda *a, **k: next(answers)):
            with Capture(["parity", QWEN, GPT, *BASE]) as captured:
                code = captured.run()
                return code, captured.buffer.getvalue()

    def test_a_truncated_run_refuses_the_parity_claim(self):
        code, text = self._with(record("qwen3:4b"),
                                record("gpt-oss:20b", outcome="UNRESOLVED"))
        self.assertEqual(code, 2)
        emitted = json.loads(text)
        self.assertEqual(emitted["outcome"], "REFUSED")
        self.assertEqual(emitted["reason_code"], "PROVENANCE_INCOMPLETE")
        self.assertIn("did not reach COMMITTED", emitted["detail"])

    def test_two_completed_runs_of_different_models_are_accepted(self):
        code, text = self._with(record("qwen3:4b"), record("gpt-oss:20b"))
        self.assertEqual(code, 0)
        emitted = json.loads(text)
        self.assertEqual(emitted["parity"]["outcome"], "ACCEPTED")
        self.assertFalse(emitted["parity"]["authority_changed_with_model"])
        self.assertEqual(emitted["parity"]["models"], ["gpt-oss:20b", "qwen3:4b"])

    def test_one_model_run_twice_is_not_parity(self):
        code, text = self._with(record("qwen3:4b"), record("qwen3:4b"))
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(text)["reason_code"], "MODEL_INCOMPATIBLE")

    def test_a_refusal_on_the_first_run_never_reaches_the_second(self):
        calls: list[str] = []

        def once(args, binding_id, prompt):
            calls.append(binding_id)
            raise Refusal("DATA_BOUNDARY_REFUSED", "input carries a credential")

        with unittest.mock.patch.object(run_module, "_one", side_effect=once):
            with Capture(["parity", QWEN, GPT, *BASE]) as captured:
                code = captured.run()
                emitted = json.loads(captured.buffer.getvalue())
        self.assertEqual(code, 2)
        self.assertEqual(emitted["reason_code"], "DATA_BOUNDARY_REFUSED")
        self.assertEqual(calls, [QWEN], "the second model ran after the first was refused")


class SingleRunReporting(unittest.TestCase):
    """One run prints the record it produced, and a refusal prints its reason code."""

    def test_a_completed_run_prints_its_record_and_exits_zero(self):
        with unittest.mock.patch.object(run_module, "_one",
                                        return_value=(record("qwen3:4b"), "Paris")):
            with Capture(["run", QWEN, *BASE]) as captured:
                code = captured.run()
                emitted = json.loads(captured.buffer.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(emitted["outcome"], "COMMITTED")

    def test_a_refused_run_prints_the_reason_code_and_exits_two(self):
        with unittest.mock.patch.object(
                run_module, "_one",
                side_effect=Refusal("MODEL_UNAVAILABLE", "runtime did not answer")):
            with Capture(["run", QWEN, *BASE]) as captured:
                code = captured.run()
                emitted = json.loads(captured.buffer.getvalue())
        self.assertEqual(code, 2)
        self.assertEqual(emitted["reason_code"], "MODEL_UNAVAILABLE")
        self.assertEqual(emitted["subject"], QWEN)


if __name__ == "__main__":
    unittest.main()
