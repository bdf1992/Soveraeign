"""Drive the proposal corpus: what this code does with an answer a model gave.

The model is not the subject and is never invoked here. Its output is not deterministic
and pinning it would be pinning a 4-billion-parameter model's mood; what these cases pin
is the boundary around it - which answers become a proposal, which become a refusal, and
that neither becomes a write.

`P-002` is the one that matters. A model that could propose `enabled` into a form the
owner then saves has routed around the whole authority split by making the owner the one
who clicks.

A passing run establishes `BUILT`. It witnesses nothing, and no test here touches the
network.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import shutil
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovschedule import authoring, intent  # noqa: E402

CORPUS = json.loads(
    (ROOT / "conformance" / "fixtures" / "automation-control" / "cases.json")
    .read_bytes().decode("utf-8"))
CASES = CORPUS["proposal_cases"]

EXISTING = {
    "name": "code-review", "description": "review the branch", "enabled": False,
    "target": {"kind": "workflow", "name": "sov-review", "args": {}},
    "cron": "0 2 * * *", "mode": "observe", "effect_class": "RESOURCE_CONSUMPTION",
    "isolation": "tree", "preconditions": {"clean_tree": False},
    "limits": {"max_budget_usd": 3, "timeout_seconds": 2700},
}


BINDING = json.loads(
    (ROOT / "adapters" / "ollama" / "bindings" / "qwen3-4b.json")
    .read_bytes().decode("utf-8"))


class FakeTransport:
    """Answers one canned body. The adapter takes a transport, so no socket is opened.

    It answers the tags route the way the runtime does, digest included, because the
    adapter refuses a binding whose model version does not match what is actually
    loaded. A fake that skipped that would be testing a check the real path does not
    take - the digest is read from the binding rather than pasted, so a re-pulled model
    fails here the way it would fail live.
    """

    def __init__(self, answer: str) -> None:
        self.answer = answer
        self.prompts: list[str] = []

    def post(self, route: str, payload: dict) -> dict:
        self.prompts.append(payload["prompt"])
        return {"response": self.answer, "done": True, "done_reason": "stop",
                "model": BINDING["model_id"], "prompt_eval_count": 100,
                "eval_count": 20, "total_duration": 1_000_000}

    def get(self, route: str) -> dict:
        if route.endswith("/version"):
            return {"version": BINDING["runtime_version"]}
        return {"models": [{"name": BINDING["model_id"],
                            "digest": BINDING["model_version"].removeprefix("sha256:")}]}


class Tree(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        schedules = self.root / ".claude" / "schedules"
        schedules.mkdir(parents=True)
        shutil.copy(ROOT / ".claude" / "schedules" / "schedule.schema.json", schedules)
        workflows = self.root / ".claude" / "workflows"
        workflows.mkdir()
        for name in ("sov-review", "sov-qa"):
            (workflows / f"{name}.js").write_text("// stub\n", encoding="utf-8")
        (schedules / "code-review.json").write_text(
            json.dumps(EXISTING, indent=2) + "\n", encoding="utf-8", newline="\n")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def ask(self, answer: str, request: str = "change it"):
        return intent.interpret(self.root, "code-review", request,
                                transport=FakeTransport(answer))


class DeclaredCorpus(Tree):
    """Every proposal case, run against the real interpreter."""

    def test_every_case_decides_what_it_declares(self) -> None:
        for case in CASES:
            with self.subTest(case=case["case_id"]):
                proposal = self.ask(case["model_answer"], case["request"])
                self.assertEqual(proposal.refusal_code, case["expect_refusal"],
                                 proposal.detail)
                if case["expect_changes"] is not None:
                    self.assertEqual(proposal.changes, case["expect_changes"])

    def test_every_declared_proposal_refusal_has_a_case(self) -> None:
        declared = json.loads(
            (ROOT / "contracts" / "automation-control.json").read_bytes().decode("utf-8"))
        reached = {case["expect_refusal"] for case in CASES} - {None}
        for code in declared["refusal_layer"]["proposal"]:
            with self.subTest(code=code):
                if code == "MODEL_UNAVAILABLE":
                    continue  # covered by TheModelIsNotTrusted, which has no answer to give
                self.assertIn(code, reached)

    def test_every_refusal_has_a_case_that_does_not_fire_it(self) -> None:
        for code in {c["expect_refusal"] for c in CASES} - {None}:
            with self.subTest(code=code):
                self.assertTrue([c["case_id"] for c in CASES
                                 if c["expect_refusal"] != code])


class NothingIsWritten(Tree):
    """The property the whole design rests on."""

    def test_no_answer_however_shaped_changes_the_declaration(self) -> None:
        before = (self.root / ".claude" / "schedules" / "code-review.json").read_bytes()
        for case in CASES:
            with self.subTest(case=case["case_id"]):
                self.ask(case["model_answer"], case["request"])
                after = (self.root / ".claude" / "schedules"
                         / "code-review.json").read_bytes()
                self.assertEqual(after, before)

    def test_a_proposal_carries_no_route_to_the_write(self) -> None:
        """Structural, not incidental: the proposal is data and holds no callable."""
        proposal = self.ask('{"changes": {"mode": "build"}, "why": "asked"}')
        self.assertTrue(proposal.usable)
        for value in vars(proposal).values():
            self.assertFalse(callable(value))


class TheModelIsNotTrusted(Tree):
    """What is checked after the answer comes back, and what is never sent."""

    def test_an_unreachable_model_is_a_refusal_not_a_fallback(self) -> None:
        class Dead:
            def post(self, route, payload):
                raise OSError("connection refused")

            def get(self, route):
                raise OSError("connection refused")

        proposal = intent.interpret(self.root, "code-review", "anything",
                                    transport=Dead())
        self.assertEqual(proposal.refusal_code, "MODEL_UNAVAILABLE")
        self.assertEqual(proposal.changes, {})

    def test_a_schedule_that_does_not_exist_never_reaches_the_model(self) -> None:
        transport = FakeTransport('{"changes": {"mode": "build"}, "why": "x"}')
        proposal = intent.interpret(self.root, "ghost", "change it", transport=transport)
        self.assertEqual(proposal.refusal_code, "UNKNOWN_SCHEDULE")
        self.assertEqual(transport.prompts, [], "a missing schedule still spent a run")

    def test_an_empty_request_never_reaches_the_model(self) -> None:
        transport = FakeTransport('{"changes": {}, "why": "x"}')
        proposal = intent.interpret(self.root, "code-review", "   ", transport=transport)
        self.assertEqual(proposal.refusal_code, "NOTHING_UNDERSTOOD")
        self.assertEqual(transport.prompts, [])

    def test_the_declaration_shown_to_the_model_omits_what_it_may_not_change(self) -> None:
        """Showing `enabled` would invite the one proposal that must never be made.

        The check is on the declaration the prompt quotes, not on the whole prompt: the
        rules below it name `enabled` on purpose, to forbid it. An earlier version of
        this test searched the whole string and failed on that prohibition, which is the
        prompt working.
        """
        transport = FakeTransport('{"changes": {"mode": "build"}, "why": "x"}')
        intent.interpret(self.root, "code-review", "make it build", transport=transport)
        prompt = transport.prompts[0]
        shown = prompt.split("The declaration now:")[1].split("Available targets")[0]
        # The top-level keys, parsed. A substring search reads the target's own `name`
        # as the declaration's and fails on a document that is correct.
        keys = set(json.loads(shown.strip()))
        self.assertEqual(keys, set(authoring.EDITABLE) & set(EXISTING))
        self.assertNotIn("enabled", keys)
        self.assertNotIn("name", keys)
        self.assertIn("sov-review", prompt, "the target list was not offered")
        self.assertIn("sov-qa", prompt)

    def test_the_editable_set_the_prompt_states_is_the_one_the_operation_enforces(self):
        """Two lists of editable fields would drift, and the drift would be silent."""
        transport = FakeTransport('{"changes": {"mode": "build"}, "why": "x"}')
        intent.interpret(self.root, "code-review", "make it build", transport=transport)
        for field in authoring.EDITABLE:
            with self.subTest(field=field):
                self.assertIn(field, transport.prompts[0])


class TheAnswerIsAttributed(Tree):
    """An unattributed suggestion is the thing this avoids."""

    def test_the_record_names_the_model_the_boundary_and_the_cost(self) -> None:
        proposal = self.ask('{"changes": {"mode": "build"}, "why": "asked"}')
        summary = intent.summary(proposal.record)
        self.assertEqual(summary["boundary"], "LOCAL_ONLY")
        self.assertIn("qwen3", summary["model"])
        self.assertIsNotNone(summary["seconds"])

    def test_a_proposal_with_no_record_summarises_to_nothing(self) -> None:
        """A refusal that never reached the model must not imply one ran."""
        proposal = intent.interpret(self.root, "ghost", "x",
                                    transport=FakeTransport("{}"))
        self.assertEqual(intent.summary(proposal.record), {})


if __name__ == "__main__":
    unittest.main()
