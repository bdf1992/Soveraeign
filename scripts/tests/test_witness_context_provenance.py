"""Hold the harness to the rule that an evaluator never takes the builder's framing as its oracle.

`SDLC.md`, Release gate item 6, states it: a Red operator receives the contract, the
claimed invariants and the built artifact; the builder's tests and plan are part of that
artifact, readable and attackable, and never used as evidence or as the oracle. The rule
was written on day two and enforced nowhere, and `.claude/workflows/sov-loop.js` drifted
off it - both witness prompts opened with the Orchestrator's operation sentence, which is
the oracle position.

These cases read the workflow bytes. They cannot judge whether an evaluator obeys the
frame it is handed; what they refuse is the harness handing it a frame built from the
builder's account, which is the half a file can carry. Passing establishes `BUILT` for
the frame. It witnesses nothing.
"""

from __future__ import annotations

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
LOOP = ROOT / ".claude" / "workflows" / "sov-loop.js"
WORKFLOWS = ROOT / ".claude" / "workflows"

# The sentence that demotes the builder's account from oracle to artifact. Wording may be
# edited; the two ideas may not both disappear.
DEMOTION = ("artifact and never oracle", "may not derive your checks from them")


def loop_text() -> str:
    return LOOP.read_text(encoding="utf-8")


def frame_source() -> str:
    """The witnessFrame function's own source."""
    text = loop_text()
    return text[text.index("function witnessFrame"):text.index("// Every agent this workflow")]


def spoken(source: str) -> str:
    """What a prompt built from this source actually says.

    The frame is written as concatenated string literals wrapped to the line length, so a
    sentence is split across `' + '` joins in the bytes. Matching raw bytes would grade the
    wrapping rather than the words; this joins the pieces back before matching.
    """
    joined = re.sub(r"'\s*\+\s*'", "", source)
    return re.sub(r"\s+", " ", joined)


def witness_invocations(text: str) -> list[str]:
    """Every agent(...) call in this workflow that dispatches to a witness.

    Split on the call boundary rather than parsing JS: each chunk that names the witness
    agent type carries the prompt that reached it.
    """
    chunks = text.split("await agent(")[1:]
    return [chunk for chunk in chunks if "agentType: 'sov-witness'" in chunk]


class WitnessFrameIsWorkProvenance(unittest.TestCase):
    def test_the_loop_dispatches_to_a_witness_at_all(self):
        """A vacuous suite would pass every case below by finding nothing to grade."""
        self.assertGreaterEqual(len(witness_invocations(loop_text())), 2,
                                "expected the evidence-mode and ordinary witness paths")

    def test_every_witness_prompt_is_built_by_the_one_frame(self):
        """Two hand-written prompts drift apart; that is how one path kept the defect."""
        for chunk in witness_invocations(loop_text()):
            self.assertIn("witnessFrame(", chunk,
                          "a witness prompt assembled outside the shared frame")

    def test_the_frame_demotes_the_builder_account_rather_than_hiding_it(self):
        """Release gate 6 says readable and attackable, never the oracle. Not withheld."""
        source = frame_source()
        self.assertIn("plan.operation", source,
                      "the builder's framing is withheld; the rule demotes it, it does not hide it")
        said = spoken(source)
        for phrase in DEMOTION:
            self.assertIn(phrase, said, f"the frame no longer says {phrase!r}")

    def test_no_witness_prompt_takes_the_builder_framing_outside_the_frame(self):
        """The defeating case. Interpolating the operation sentence into a witness prompt
        is the exact drift: it puts the orchestrator's account where the contract belongs."""
        for chunk in witness_invocations(loop_text()):
            prompt = chunk.split("{ agentType:")[0]
            outside = prompt.replace("witnessFrame(selected, plan, built)", "")
            for banned in ("plan.operation", "built.summary", "built.changed_paths"):
                self.assertNotIn(banned, outside,
                                 f"{banned} reaches a witness outside the labelled frame")

    def test_the_frame_pins_a_subject_and_derives_its_own_scope(self):
        """Trap T6: several sessions write this tree. A verdict over a moving tree is
        unattestable, and a scope taken from the builder's list is not derived."""
        said = spoken(frame_source())
        self.assertIn("git rev-parse HEAD", said)
        self.assertIn("UNATTESTABLE", said)
        self.assertIn("git status", said)

    def test_the_frame_asks_for_the_state_that_will_land(self):
        """A green working tree can go red on commit, because several snapshot claims read
        committed bytes. Verifying the tree and landing the commit is not the same reading."""
        self.assertIn("committed bytes", spoken(frame_source()))

    def test_the_rule_is_cited_where_it_is_applied(self):
        """A restated rule is defective per SDLC.md Skill axes; a cited one is not."""
        self.assertIn("Release gate 6", loop_text())

    def test_no_other_workflow_hands_a_witness_an_unlabelled_builder_conclusion(self):
        """The loop is not the only file that can dispatch a witness."""
        for path in sorted(WORKFLOWS.glob("*.js")):
            text = path.read_text(encoding="utf-8")
            for chunk in witness_invocations(text):
                prompt = chunk.split("{ agentType:")[0]
                if "witnessFrame(" in prompt:
                    continue
                self.assertIsNone(
                    re.search(r"\bplan\.operation\b|\bbuilt\.summary\b", prompt),
                    f"{path.name} hands a witness the builder's account with no frame")


if __name__ == "__main__":
    unittest.main()
