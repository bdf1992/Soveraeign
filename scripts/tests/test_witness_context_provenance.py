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
    derives_from_agent_result, dispatches, interpolated, prompt_of, resolved_prompt, roots,
)
from sovprompts.lexer import broken_concatenation, unreadable  # noqa: E402
from sovprompts.render import blocks, rendered  # noqa: E402

WORKFLOWS = ROOT / ".claude" / "workflows"
LOOP = WORKFLOWS / "sov-loop.js"

# The two ideas that demote the builder's account. Wording may change; both may not go.
DEMOTION = ("artifact and never oracle", "may not derive your checks from them")
# A label that marks builder-supplied text as artifact wherever it appears in a prompt.
LABEL = "artifact and never oracle"
#: The bindings that carry the builder's own account of the work. An expression that
#: resolves to one of these is the builder's account however it has been renamed.
ACCOUNT = frozenset({"plan", "built", "orchestrationReview"})


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
        """A wrapper prepended to the frame puts the builder's account first again.

        This resolves every expression spliced in ahead of the frame back to the binding
        it derives from. The first form of this case banned the literal strings `plan.`,
        `built.` and `orchestrationReview` in the source text before `witnessFrame(`, and
        an independent reading defeated it with one line:

            const acct = built
            'THE BUILD REPORT, which is your oracle: ' + acct.summary + ... +
            witnessFrame(selected, plan, built) +

        None of the banned substrings appear, the builder's account is handed over as the
        oracle, and the case passed. Renaming a variable defeating a check is the exact
        defect this module exists to refuse, so the check follows the binding instead.
        """
        source = loop()
        for call in dispatches(source, "sov-witness"):
            prompt = prompt_of(call)
            before = prompt[:prompt.index("witnessFrame(")]
            for expression in interpolated(before):
                leaked = sorted(roots(source, expression, ACCOUNT) & ACCOUNT)
                self.assertFalse(
                    leaked,
                    f"{expression!r} reaches a witness ahead of the frame and derives "
                    f"from {leaked}, which is the builder's account in the oracle position")

    def test_the_subject_is_the_first_thing_the_evaluator_reads(self):
        """Deleting SUBJECT, or moving it below the builder's account, both leave a frame
        that still contains every required phrase. Presence is not position, and the rule
        is that the evaluator pins its own subject before it reads anyone's account."""
        heads = [block.split(".")[0].strip() for block in blocks(loop(), "witnessFrame")]
        self.assertEqual(heads[0], "SUBJECT",
                         f"the frame now opens on {heads[0]!r}; the subject must come first")

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
            if not any(derives_from_agent_result(source, expression)
                       for expression in interpolated(prompt)):
                continue
            self.assertIn(LABEL, prompt,
                          f"{name}: a witness prompt splices in the builder's account unlabelled")

    def test_every_workflow_is_readable_javascript(self):
        """Two documented launch paths shipped unparseable and a hand-run check called them
        clean, because `node --check` returns zero on these files whatever they contain:
        they open with `export`. They also carry a top-level `return`, so
        `--input-type=module --check` rejects all twenty-three, and neither node mode reads
        this format. `sovprompts.lexer` does, and until this case it had no caller anywhere
        in the tree - the repair for those two files shipped with its guard uncalled.

        A grammar error whose tokens are all well formed still passes here. That is the
        reader's stated ceiling, not a claim it is complete.
        """
        for path in sorted(WORKFLOWS.glob("*.js")):
            defect = unreadable(path.read_text(encoding="utf-8"))
            self.assertIsNone(defect, f"{path.name} is not readable JavaScript: {defect}")

    def test_no_workflow_carries_a_concatenation_that_yields_NaN(self):
        """`'a' + + 'b'` parses clean and puts NaN in the middle of a prompt. Nothing lints
        these files, and this shape bit while repairing them."""
        for path in sorted(WORKFLOWS.glob("*.js")):
            self.assertFalse(broken_concatenation(path.read_text(encoding="utf-8")),
                             f"{path.name}: a concatenation that evaluates to NaN")


if __name__ == "__main__":
    unittest.main()
