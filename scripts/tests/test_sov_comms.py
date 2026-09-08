"""Cases for the Communications claim grader.

The grader's own `selfcheck` proves its refusals fire from cases it carries. These
cases press the boundaries that selfcheck does not: the proximity rule that
separates a quantified claim from a grammatical collision, the source marker that
distinguishes a producer from a citation, and trap T3.
"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sovcomms.kinds import (check_unglossed_token, check_unsourced_number,
                            check_unsupported_standing)


class UnsourcedFigure(unittest.TestCase):
    """A behavioural figure must name what derives it, in its own paragraph."""

    def test_a_measurement_with_no_producer_is_refused(self):
        text = "Measured against 379 of his turns: five were genuine owner rulings."
        self.assertEqual(1, len(check_unsourced_number("t", text)))

    def test_a_runnable_command_in_the_paragraph_clears_it(self):
        text = ("102 commits sat on branches that never reached the trunk.\n"
                "Before you finish, run `python scripts/sov_strand.py`.")
        self.assertEqual([], check_unsourced_number("t", text))

    def test_a_cited_document_is_not_a_producer(self):
        """Naming `verify.py` does not derive how many times it ran."""
        text = "`verify.py` was run about 1,768 times across the measured sessions."
        self.assertEqual(1, len(check_unsourced_number("t", text)))

    def test_a_pronoun_beside_a_verb_is_not_a_measurement(self):
        text = "When you write one, make it re-derive from bytes at the moment it runs."
        self.assertEqual([], check_unsourced_number("t", text))

    def test_an_ordinary_count_carries_no_measurement_marker(self):
        text = "Its budget is 60 agent invocations per exercise and it expires 2026-11-23."
        self.assertEqual([], check_unsourced_number("t", text))

    def test_a_recorded_historical_sentence_is_exempt(self):
        text = 'A rule quoted "379 of his turns" to record what was removed.'
        self.assertEqual([], check_unsourced_number("t", text,
                                                    frozenset({"379 of his turns"})))

    def test_the_exemption_does_not_clear_the_rest_of_the_surface(self):
        text = ('A rule quoted "379 of his turns" to record it.\n\n'
                "Across 68 measured sessions the pattern held.")
        self.assertEqual(1, len(check_unsourced_number("t", text,
                                                       frozenset({"379 of his turns"}))))


class UnglossedToken(unittest.TestCase):
    """A machine type may be used in front of a person once it has been explained."""

    def test_a_bare_first_use_is_refused(self):
        found = check_unglossed_token("t", "The slice is WITNESSED.")
        self.assertEqual(["UNGLOSSED_TOKEN"], [d.kind for d in found])

    def test_a_glossed_first_use_passes(self):
        """Progressive disclosure: teaching the vocabulary beats forbidding it."""
        self.assertEqual([], check_unglossed_token(
            "t", "The slice is WITNESSED (someone who did not build it confirmed it)."))

    def test_later_bare_uses_are_free_once_the_first_was_glossed(self):
        text = "It is WITNESSED (independently confirmed).\nStill WITNESSED today."
        self.assertEqual([], check_unglossed_token("t", text))

    def test_plain_english_is_not_refused(self):
        self.assertEqual([], check_unglossed_token(
            "t", "Someone who didn't build it confirmed it works."))

    def test_each_token_is_reported_once(self):
        self.assertEqual(2, len(check_unglossed_token("t", "WITNESSED here, and UNATTESTABLE too.")))


class UnsupportedStanding(unittest.TestCase):
    """A witnessed claim is graded against the witness records, not itself."""

    def test_an_unsupported_subject_is_refused(self):
        found = check_unsupported_standing("t", "proofing_service_status is WITNESSED", set())
        self.assertEqual(["UNSUPPORTED_STANDING"], [d.kind for d in found])

    def test_a_supported_subject_passes(self):
        found = check_unsupported_standing("t", "observation_service_status is WITNESSED",
                                           {"observation_service_status"})
        self.assertEqual([], found)

    def test_a_denial_is_not_a_claim(self):
        """NOT_WITNESSED contains WITNESSED; a substring reading inverts the tree."""
        found = check_unsupported_standing("t", "proofing_service_status is NOT_WITNESSED",
                                           set())
        self.assertEqual([], found)


if __name__ == "__main__":
    unittest.main()
