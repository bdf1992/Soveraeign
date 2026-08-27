"""Grade the fixture set: does breaking a check make any declared case fail?

`selfcheck` reports "N refusal(s) all proven". A seventh witness instrumented the corpus
checks and found they returned early on all thirty-four cases - the base record's digest is
sixty-four zeros, so nothing bound the real corpus and the code that stops a record naming
its own referent was never executed. The oracle said everything was proven while a whole
family of checks was unreachable from it.

That is the same defect the whole contract exists to refuse, one level up: a check that
cannot see what it grades. "Every refusal has a case that fires it" is necessary and not
sufficient, because a refusal can fire from one branch while three others never run.

So each case here disables one check and asserts the declared corpus notices. If a mutation
survives, the fixture set is not exercising that check and `selfcheck` is reporting a
coverage it does not have. This is finite where an eighth adversarial pass is not: the
witness that found the gap recommended spending the next pass's budget here instead, and
this is that.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable
import contextlib
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovcoldstart import attribution, records, refusals, report  # noqa: E402
from sovcoldstart.oracle import cmd_selfcheck  # noqa: E402


class _Args:
    corpus = ROOT / "scripts" / "sovcoldstart" / "corpus.json"


@contextlib.contextmanager
def _disabled(module: object, name: str, replacement: Callable):
    """Replace one function for the duration of a case, then put it back."""
    original = getattr(module, name)
    setattr(module, name, replacement)
    try:
        yield
    finally:
        setattr(module, name, original)


def _selfcheck() -> int:
    """Run the declared oracle, silently."""
    import io

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        return cmd_selfcheck(_Args())


#: (module, function name, a replacement that checks nothing). Each entry is one check the
#: fixture set claims to exercise.
#: Patched in the module that *calls* the function, not the one that defines it. `refusals`
#: does `from ... import derive`, so it holds its own reference and patching the definition
#: is a no-op - which made three mutations look like they survived when the test was simply
#: aiming at the wrong name.
MUTATIONS = (
    (refusals, "_counts_disagree", lambda record, canonical: []),
    (refusals, "_identity_defects", lambda record: []),
    (refusals, "_competence_defects", lambda record: []),
    (refusals, "derive", lambda table: ("ADMISSIBLE", "mutated")),
    (refusals, "grade_row", lambda tier, asked, scored, hit, unmeasured: {
        "tier": tier, "asked": asked, "scored": scored, "hit": hit,
        "unmeasured": unmeasured, "gate": report.GATES[tier],
        "result": "PASS" if report.GATES[tier] is not None else "INFO"}),
    (attribution, "_grader_defects", lambda grader, verdicts: []),
    (attribution, "_file_defects", lambda code, field, rel, digest: []),
    (attribution, "_answers_shape", lambda rel, record: []),
    (attribution, "canonical_corpus", lambda record: None),
    (attribution, "_manual_in_corpus", lambda record: None),
)


class TheOracleIsClean(unittest.TestCase):
    def test_selfcheck_passes_unmutated(self) -> None:
        """Everything below is worthless if the baseline is not green."""
        self.assertEqual(_selfcheck(), 0)


class EveryCheckIsReachedBySomeCase(unittest.TestCase):
    """Disable one check; the declared corpus must notice."""

    def test_no_mutation_survives(self) -> None:
        survived = []
        for module, name, replacement in MUTATIONS:
            with self.subTest(check=f"{module.__name__}.{name}"):
                with _disabled(module, name, replacement):
                    result = _selfcheck()
                if result == 0:
                    survived.append(f"{module.__name__}.{name}")
                self.assertEqual(
                    result, 1,
                    f"disabling {module.__name__}.{name} changed nothing: no case in "
                    f"conformance/fixtures/coldstart/run-cases.json exercises it, so "
                    f"selfcheck reports a coverage it does not have")
        self.assertEqual(survived, [])


class TheCanonicalBindingIsReached(unittest.TestCase):
    """The specific gap the witness found, asserted directly rather than by mutation."""

    def test_some_case_binds_the_live_corpus(self) -> None:
        import json

        from sovcoldstart.oracle import _apply, _bind_canonical, _canonical_digest

        corpus = json.loads(records.CASES.read_text(encoding="utf-8"))
        bound = [case["case_id"] for case in corpus["cases"]
                 if (_bind_canonical(_apply(corpus["base_record"], case["patch"]))
                     .get("corpus") or {}).get("digest") == _canonical_digest()]
        self.assertTrue(bound, "no case binds the canonical corpus, so every check that "
                               "reads it is unreachable from the declared oracle")

    def test_the_corpus_is_pinned_by_the_system_and_not_by_the_record(self) -> None:
        """The generator behind six passes of findings: the record chose its own referent."""
        self.assertEqual(refusals.CANONICAL_CORPUS, "scripts/sovcoldstart/corpus.json")
        record = {"corpus": {"path": "anything/else.json", "digest": "sha256:" + "0" * 64,
                             "questions": 1, "selected": 1}}
        self.assertIsNone(attribution.canonical_corpus(record))


if __name__ == "__main__":
    unittest.main()
