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

LF = "\n"


def _status(body: str) -> Path:
    handle = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8", newline=LF)
    handle.write(body)
    handle.close()
    return Path(handle.name)


def _record(directory: Path, name: str, supports: str = "BUILT -> WITNESSED") -> None:
    """A record that says what it supports, which is what the gate now reads."""
    body = f"# observation{LF}{LF}**Standing supported: {supports}.**{LF}"
    (directory / name).write_text(body, encoding="utf-8", newline=LF)


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
        path = _status("asset_service_status: BUILT_WITNESSED" + LF)
        with tempfile.TemporaryDirectory() as empty:
            gaps = sov_standing.unsupported(path, Path(empty))
        self.assertEqual([c.field for c in gaps], ["asset_service_status"])

    def test_a_claim_with_a_record_is_supported(self):
        path = _status("asset_service_status: BUILT_WITNESSED" + LF)
        with tempfile.TemporaryDirectory() as tmp:
            _record(Path(tmp), "asset-service.md")
            gaps = sov_standing.unsupported(path, Path(tmp))
        self.assertEqual(gaps, [])

    def test_an_unwitnessed_subject_needs_no_record(self):
        """The whole repository is in this state; the gate must stay quiet about it."""
        path = _status("asset_service_status: BUILT_SELF_TESTED_NOT_WITNESSED" + LF)
        with tempfile.TemporaryDirectory() as empty:
            self.assertEqual(sov_standing.unsupported(path, Path(empty)), [])

    def test_a_record_for_a_different_subject_does_not_satisfy_the_claim(self):
        """The defeating case for the lookup: any file must not satisfy any claim."""
        path = _status("asset_service_status: BUILT_WITNESSED" + LF)
        with tempfile.TemporaryDirectory() as tmp:
            _record(Path(tmp), "console-service.md")
            gaps = sov_standing.unsupported(path, Path(tmp))
        self.assertEqual(len(gaps), 1)

    def test_the_directory_readme_is_not_a_witness_record(self):
        """The file explaining the convention must not satisfy a claim made under it."""
        path = _status("readme_status: BUILT_WITNESSED" + LF)
        with tempfile.TemporaryDirectory() as tmp:
            _record(Path(tmp), "README.md")
            gaps = sov_standing.unsupported(path, Path(tmp))
        self.assertEqual(len(gaps), 1)

    def test_a_missing_witness_directory_refuses_rather_than_passing(self):
        path = _status("asset_service_status: BUILT_RATIFIED" + LF)
        gaps = sov_standing.unsupported(path, Path(tempfile.gettempdir()) / "no-such-witness-dir")
        self.assertEqual(len(gaps), 1)

    def test_non_status_lines_are_ignored(self):
        path = _status("phase: FOUNDING" + LF + "note: WITNESSED appears here as prose" + LF)
        with tempfile.TemporaryDirectory() as empty:
            self.assertEqual(sov_standing.unsupported(path, Path(empty)), [])


class RecordMustCarryTheStanding(unittest.TestCase):
    """A filename is a declaration; what the record says is the artifact.

    The gate built its record set from `p.stem.lower()` and read nothing else, so
    depositing `witness/record-service.md` was enough to let
    `record_service_status` claim WITNESSED however loudly the record refused it.
    Every record on file today states "Standing supported: none", and all three
    filenames map exactly onto status fields, so the branch that first filled the
    directory also handed a later commit three free promotions.
    """

    def _gap_fields(self, claim: str, supports: str | None) -> list[str]:
        path = _status(f"asset_service_status: {claim}" + LF)
        with tempfile.TemporaryDirectory() as tmp:
            if supports is None:
                (Path(tmp) / "asset-service.md").write_text(
                    "an observation that will not say what it supports",
                    encoding="utf-8", newline=LF)
            else:
                _record(Path(tmp), "asset-service.md", supports=supports)
            return [c.field for c in sov_standing.unsupported(path, Path(tmp))]

    def test_a_record_supporting_nothing_does_not_support_a_claim(self):
        self.assertEqual(self._gap_fields("BUILT_WITNESSED", "none"),
                         ["asset_service_status"])

    def test_the_refusal_survives_the_prose_that_follows_it(self):
        """Records write "none." mid-sentence; the gate must read the verdict."""
        self.assertEqual(
            self._gap_fields("BUILT_WITNESSED",
                             "none. This observation does not carry the subject"),
            ["asset_service_status"])

    def test_a_record_that_will_not_say_what_it_supports_supports_nothing(self):
        """Fail closed: silence is not support."""
        self.assertEqual(self._gap_fields("BUILT_WITNESSED", None),
                         ["asset_service_status"])

    def test_a_record_that_carries_the_standing_still_supports_it(self):
        self.assertEqual(self._gap_fields("BUILT_WITNESSED", "BUILT -> WITNESSED"), [])

    def test_the_directory_readme_is_still_not_a_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            _record(Path(tmp), "README.md")
            self.assertEqual(sov_standing.witness_records(Path(tmp)), {})


class LiveRepository(unittest.TestCase):
    def test_the_repository_currently_claims_no_standing(self):
        """If this ever fails, something advanced standing - and it must carry a record."""
        self.assertEqual(sov_standing.read_claims(), [])

    def test_a_deposited_record_does_not_advance_standing(self):
        """Records are what witness/ is for, and depositing one moves no status field.

        This asserted an empty directory when it was written, which was true of
        that afternoon rather than true in general. The invariant underneath it
        is the one `witness/README.md` states: a record makes advancing standing
        possible and never performs it. That is what is checked now, so the
        first record deposited does not read as a regression.
        """
        records = sov_standing.witness_records()
        self.assertNotIn("readme", records,
                         "the convention document is not an observation of anything")
        self.assertEqual(
            sov_standing.read_claims(), [],
            f"{len(records)} witness record(s) on file and a status field advanced anyway")


if __name__ == "__main__":
    unittest.main()


class WhatTheRecordSaysIsGraded(unittest.TestCase):
    """A second witness defeated the first repair five ways, all by the same slip.

    `supports_a_standing()` read a line and then tested it for truthiness, so any
    non-empty remainder counted as support. Each case below was reproduced
    against that implementation and promoted a WITNESSED claim. The honest record
    is here too, so the repair is not merely "refuse everything".
    """

    def _promotes(self, body: str, claim: str = "BUILT_WITNESSED") -> bool:
        path = _status(f"asset_service_status: {claim}{LF}")
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "asset-service.md").write_text(body, encoding="utf-8", newline=LF)
            return sov_standing.unsupported(path, Path(tmp)) == []

    def _observation(self, value: str) -> str:
        return f"# observation{LF}{LF}**Standing supported: {value}**{LF}"

    def test_a_label_line_with_its_verdict_below_supports_nothing(self):
        """The worst of the five: the line captured the literal `**`, which is not
        "none", so a record refusing in the loudest possible terms promoted.

        Both spellings are here on purpose. With `none.` below the label the
        denial scan would refuse the record even if the line break were not a
        boundary, so that case alone leaves the boundary untested - a mutation
        run proved it. With `WITNESSED.` below the label the boundary is the only
        rule standing between the record and a promotion it never declared.
        """
        for below in ("none.", "WITNESSED.", "RATIFIED."):
            with self.subTest(below=below):
                self.assertFalse(self._promotes(
                    f"# observation{LF}{LF}**Standing supported:**{LF}{below}{LF}"))

    def test_not_witnessed_inside_a_record_is_a_denial(self):
        """T3 reproduced at the site the first repair created. The whole-token
        discipline lived in `claimed_standing()` and was not carried across."""
        self.assertFalse(self._promotes(self._observation("NOT_WITNESSED.")))

    def test_a_value_naming_no_standing_supports_nothing(self):
        for value in ("OPEN -> BUILT.", "n/a", "BUILT.", "see the findings below."):
            with self.subTest(value=value):
                self.assertFalse(self._promotes(self._observation(value)))

    def test_a_denial_after_the_standing_still_denies_it(self):
        """`WITNESSED is refused` names a standing and refuses it in three words;
        a rule that only reads the token before the standing misses that. The
        spelling matters: with `RATIFIED` here the over-reach rule refuses the
        record anyway, and this case would pass while testing nothing."""
        self.assertFalse(self._promotes(self._observation("WITNESSED is refused.")))
        self.assertFalse(self._promotes(self._observation("RATIFIED is refused.")))

    def test_naming_both_standings_is_ambiguous_and_supports_nothing(self):
        """Asserted on the reading rather than the verdict, deliberately. Through
        `unsupported()` a two-element set resolves arbitrarily and the over-reach
        rule catches roughly half the runs, so the verdict passes by set ordering
        rather than by the rule. A mutation run found that; this is the repair."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "asset-service.md"
            path.write_text(self._observation("WITNESSED and RATIFIED."),
                            encoding="utf-8", newline=LF)
            self.assertIsNone(sov_standing.supported_standing(path))
        self.assertFalse(self._promotes(self._observation("WITNESSED and RATIFIED.")))

    def test_an_honest_record_still_supports_the_claim(self):
        self.assertTrue(self._promotes(self._observation("WITNESSED.")))
        self.assertTrue(self._promotes(f"# observation{LF}{LF}Standing supported: BUILT -> WITNESSED{LF}"))

    def test_a_record_may_not_declare_ratified(self):
        """`witness/README.md`: a record supports a transition at most as far as
        BUILT -> WITNESSED. A record declaring more has over-reached, for both
        kinds of claim, and the gate must not read the over-reach as support."""
        self.assertFalse(self._promotes(self._observation("RATIFIED.")))
        self.assertFalse(self._promotes(self._observation("RATIFIED."), claim="BUILT_RATIFIED"))

    def test_the_refusal_names_the_over_reach_rather_than_reporting_absence(self):
        """A record that is present and wrong must not be reported as missing."""
        path = _status(f"asset_service_status: BUILT_WITNESSED{LF}")
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "asset-service.md").write_text(
                self._observation("RATIFIED."), encoding="utf-8", newline=LF)
            reason = sov_standing.refusal(sov_standing.read_claims(path)[0], Path(tmp))
        self.assertIn("declares RATIFIED", reason)
        self.assertIn("the owner settles the rest", reason)

    def test_no_record_on_file_over_reaches(self):
        """Durable against the real directory: a record declares WITNESSED or
        nothing. This fails the day one declares a standing it may not carry."""
        allowed = (None, sov_standing.WITNESS_MAY_SUPPORT)
        over = [path.name for path in sorted(sov_standing.WITNESS_DIR.glob("*.md"))
                if path.stem.lower() not in sov_standing.NOT_A_RECORD
                and sov_standing.supported_standing(path) not in allowed]
        self.assertEqual(over, [])

    def test_the_shape_the_readme_documents_is_the_shape_the_gate_reads(self):
        """The input contract changed in the same commit that left the only
        document instructing its authors untouched, and the shape that document
        showed was one the gate could not read. They fail together now."""
        readme = (sov_standing.WITNESS_DIR / "README.md").read_text(encoding="utf-8")
        self.assertIn("`Standing supported: WITNESSED`", readme)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "asset-service.md"
            path.write_text(f"# observation{LF}{LF}Standing supported: WITNESSED{LF}",
                            encoding="utf-8", newline=LF)
            self.assertEqual(sov_standing.supported_standing(path), "WITNESSED")
