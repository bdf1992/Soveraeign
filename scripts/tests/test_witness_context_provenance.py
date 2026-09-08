"""Hold the harness to the rule that an evaluator never takes the builder's framing as its oracle.

`SDLC.md`, Release gate item 6: an evaluator receives the contract, the claimed invariants
and the built artifact; the builder's tests and plan are part of that artifact, readable
and attackable, and never used as evidence or as the oracle.

The first version of this module read the workflow's bytes and matched prose substrings.
An independent reading defeated it five ways, the worst being a frame replaced entirely by
the defect with the graded phrases left behind in a comment. That is the defect this
repository keeps finding in itself: a check that reads a declaration where it could
measure. These cases render what a witness is actually handed - `sovprompts.render`
joins the string literals a function returns, so a comment and a dead constant contribute
nothing - and grade the rendered text, its ordering, and every dispatch that reaches a
witness anywhere under `.claude/workflows/`.

What they still cannot do is judge whether an evaluator obeys the frame it is handed.
That is stated rather than implied. Passing establishes `BUILT` for the frame; it
witnesses nothing.
"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovprompts.dispatch import (  # noqa: E402
    dispatches, interpolated, prompt_of, resolved_prompt,
)
from sovprompts.lexer import broken_concatenation  # noqa: E402
from sovprompts.render import blocks, rendered  # noqa: E402

WORKFLOWS = ROOT / ".claude" / "workflows"
LOOP = WORKFLOWS / "sov-loop.js"

# The two ideas that demote the builder's account. Wording may change; both may not go.
DEMOTION = ("artifact and never oracle", "may not derive your checks from them")
# A label that marks builder-supplied text as artifact wherever it appears in a prompt.
LABEL = "artifact and never oracle"


def loop() -> str:
    return LOOP.read_text(encoding="utf-8")


class TheFrameIsRenderedAndGraded(unittest.TestCase):
    """Every case here reads what the frame produces, never the source around it."""

    def test_the_frame_renders_at_all(self):
        """A reader that cannot render reports so; it never passes by finding nothing."""
        self.assertGreaterEqual(len(blocks(loop(), "witnessFrame")), 6)

    def test_a_comment_cannot_satisfy_the_frame(self):
        """The defeat that broke the first version of this module."""
        source = loop().replace(
            "  return [",
            "  // artifact and never oracle: you may not derive your checks from them\n  return [", 1)
        gutted = source[:source.index("function witnessFrame")] + (
            "function witnessFrame(concern, plan, built) {\n"
            "  // artifact and never oracle - may not derive your checks from them\n"
            "  return ['THE WORK. Operation: ' + plan.operation + '. Confirm it.'].join('')\n}\n"
        ) + source[source.index("// Every agent this workflow"):]
        said = rendered(gutted, "witnessFrame")
        for phrase in DEMOTION:
            self.assertNotIn(phrase, said,
                             "a comment reached the rendered prompt; the reader is grading source")

    def test_the_rendered_frame_demotes_rather_than_hides(self):
        said = rendered(loop(), "witnessFrame")
        self.assertIn("<expr>", said, "the builder's account is withheld; the rule demotes it")
        for phrase in DEMOTION:
            self.assertIn(phrase, said, f"the rendered frame no longer says {phrase!r}")

    def test_the_builder_account_comes_after_the_contract_and_the_checks(self):
        """Relabelling it while leaving it first would satisfy a presence check and change
        nothing about what the reader acts on first."""
        heads = [block.split(".")[0].strip() for block in blocks(loop(), "witnessFrame")]
        account = next(i for i, h in enumerate(heads) if h.startswith("THE BUILDER"))
        for earlier in ("CONTRACT", "CHECKS"):
            self.assertLess(heads.index(earlier), account,
                            f"{earlier} must reach the evaluator before the builder's account")

    def test_the_frame_pins_a_subject_derives_scope_and_asks_for_the_landing_state(self):
        said = rendered(loop(), "witnessFrame")
        for required in ("git rev-parse HEAD", "UNATTESTABLE", "git status", "committed bytes"):
            self.assertIn(required, said)


class EveryWitnessDispatchIsFramed(unittest.TestCase):
    """The loop is not the only file that reaches a witness. Thirty calls do."""

    def all_dispatches(self):
        found = []
        for path in sorted(WORKFLOWS.glob("*.js")):
            source = path.read_text(encoding="utf-8")
            for call in dispatches(source, "sov-witness"):
                found.append((path.name, source, call))
        return found

    def test_the_sweep_finds_the_dispatches(self):
        """Vacuously passing by finding nothing is the failure mode of a repo-wide rule."""
        self.assertGreaterEqual(len(self.all_dispatches()), 20)

    def test_both_loop_paths_share_the_one_frame(self):
        calls = dispatches(loop(), "sov-witness")
        self.assertEqual(len(calls), 2, "expected the evidence-mode and ordinary paths")
        for call in calls:
            self.assertIn("witnessFrame(", prompt_of(call))

    def test_nothing_is_concatenated_before_the_frame(self):
        """A wrapper prepended to the frame puts the builder's account first again."""
        for call in dispatches(loop(), "sov-witness"):
            prompt = prompt_of(call)
            before = prompt[:prompt.index("witnessFrame(")]
            for banned in ("plan.", "built.", "orchestrationReview"):
                self.assertNotIn(banned, before,
                                 f"{banned} reaches a witness ahead of the frame")

    def test_no_witness_prompt_carries_an_unlabelled_builder_account(self):
        """The repo-wide rule. A prompt that splices in the builder's account must also
        carry the label that makes it artifact rather than oracle.

        The test reads what the prompt interpolates, not what its prose happens to say. An
        earlier form matched substrings and flagged a cold-start probe for containing the
        word "claims" in a sentence, which is grading prose rather than structure.
        """
        for name, source, call in self.all_dispatches():
            prompt = resolved_prompt(source, prompt_of(call))
            if "witnessFrame(" in prompt:
                continue
            spliced = " ".join(interpolated(prompt))
            carries = any(token in spliced for token in
                          ("plan.", "built.", "build.", "claimed", "claims", "disposable"))
            if not carries:
                continue
            self.assertIn(LABEL, prompt,
                          f"{name}: a witness prompt splices in the builder's account unlabelled")

    def test_no_workflow_carries_a_concatenation_that_yields_NaN(self):
        """`'a' + + 'b'` parses clean and puts NaN in the middle of a prompt. Nothing lints
        these files, and this shape bit while repairing them."""
        for path in sorted(WORKFLOWS.glob("*.js")):
            self.assertFalse(broken_concatenation(path.read_text(encoding="utf-8")),
                             f"{path.name}: a concatenation that evaluates to NaN")


if __name__ == "__main__":
    unittest.main()
