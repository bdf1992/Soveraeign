"""Checks for the standing gate.

The gate exists because a rule that is only written down does not fire. Its own
correctness therefore matters more than usual: a gate that refuses honest work,
or passes dishonest work, is worse than no gate because it is trusted.

Every positive case here has a defeating twin, per `AGENTS.md`. The defeating
case that matters most is the negation: `NOT_WITNESSED` contains the token
`WITNESSED`, so a substring implementation passes this file's positive cases and
still reports every unwitnessed subject in the repository as witnessed.
"""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import sov_standing  # noqa: E402


def _status(body: str) -> Path:
    handle = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8", newline="\n")
    handle.write(body)
    handle.close()
    return Path(handle.name)


class ClaimedStanding(unittest.TestCase):
    def test_a_bare_claim_is_read(self):
        self.assertEqual(sov_standing.claimed_standing("WITNESSED"), "WITNESSED")
        self.assertEqual(sov_standing.claimed_standing("RATIFIED"), "RATIFIED")

    def test_a_compound_claim_is_read(self):
        self.assertEqual(sov_standing.claimed_standing("BUILT_WITNESSED_OWNER_PENDING"), "WITNESSED")

    def test_a_negated_claim_is_not_a_claim(self):
        """The defeating case: NOT_WITNESSED contains WITNESSED and asserts the opposite."""
        self.assertIsNone(sov_standing.claimed_standing("BUILT_SELF_TESTED_NOT_WITNESSED"))
        self.assertIsNone(sov_standing.claimed_standing("NOT_RATIFIED"))

    def test_every_negated_spelling_live_in_the_repository_reads_as_no_claim(self):
        """Grounded in the real values, not invented ones."""
        for value in (
            "BUILT_SELF_TESTED_NOT_WITNESSED",
            "BUILT_SELF_TESTED_NOT_WITNESSED_BASELINE_PROPOSED",
            "OWNER_DIRECTED_CONTEXT_PROFILE_BUILT_SELF_TESTED_NOT_WITNESSED",
        ):
            self.assertIsNone(sov_standing.claimed_standing(value), value)

    def test_a_token_that_merely_contains_a_standing_is_not_a_claim(self):
        self.assertIsNone(sov_standing.claimed_standing("UNWITNESSED"))
        self.assertIsNone(sov_standing.claimed_standing("PRERATIFIED"))

    def test_an_unrelated_value_claims_nothing(self):
        self.assertIsNone(sov_standing.claimed_standing("CHARTERED_NOT_IMPLEMENTED"))


class SubjectNaming(unittest.TestCase):
    def test_a_field_maps_to_its_subject(self):
        self.assertEqual(sov_standing.subject_of("asset_service_status"), "asset-service")
        self.assertEqual(sov_standing.subject_of("sov_operating_agent_status"), "sov-operating-agent")


class GateBehaviour(unittest.TestCase):
    def test_a_claim_without_a_record_is_refused(self):
        path = _status("asset_service_status: BUILT_WITNESSED\n")
        with tempfile.TemporaryDirectory() as empty:
            gaps = sov_standing.unsupported(path, Path(empty))
        self.assertEqual([c.field for c in gaps], ["asset_service_status"])

    def test_a_claim_with_a_record_is_supported(self):
        path = _status("asset_service_status: BUILT_WITNESSED\n")
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "asset-service.md").write_text("observation", encoding="utf-8", newline="\n")
            gaps = sov_standing.unsupported(path, Path(tmp))
        self.assertEqual(gaps, [])

    def test_an_unwitnessed_subject_needs_no_record(self):
        """The whole repository is in this state; the gate must stay quiet about it."""
        path = _status("asset_service_status: BUILT_SELF_TESTED_NOT_WITNESSED\n")
        with tempfile.TemporaryDirectory() as empty:
            self.assertEqual(sov_standing.unsupported(path, Path(empty)), [])

    def test_a_record_for_a_different_subject_does_not_satisfy_the_claim(self):
        """The defeating case for the record lookup: any file must not satisfy any claim."""
        path = _status("asset_service_status: BUILT_WITNESSED\n")
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "console-service.md").write_text("observation", encoding="utf-8", newline="\n")
            gaps = sov_standing.unsupported(path, Path(tmp))
        self.assertEqual(len(gaps), 1)

    def test_a_missing_witness_directory_refuses_rather_than_passing(self):
        path = _status("asset_service_status: BUILT_RATIFIED\n")
        gaps = sov_standing.unsupported(path, Path(tempfile.gettempdir()) / "no-such-witness-dir")
        self.assertEqual(len(gaps), 1)

    def test_non_status_lines_are_ignored(self):
        path = _status("phase: FOUNDING\nnote: WITNESSED appears here as prose\n")
        with tempfile.TemporaryDirectory() as empty:
            self.assertEqual(sov_standing.unsupported(path, Path(empty)), [])


class LiveRepository(unittest.TestCase):
    def test_the_repository_currently_claims_no_standing(self):
        """If this ever fails, something advanced standing - and it must carry a record."""
        self.assertEqual(sov_standing.read_claims(), [])


if __name__ == "__main__":
    unittest.main()
