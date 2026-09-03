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
import re
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


FENCE = chr(96) * 3
CANONICAL = re.compile(FENCE + r"witness\n(.*?)\n" + FENCE, re.DOTALL)


def _body(declaration: str = "standing_supported  WITNESSED", tail: str = "") -> str:
    """A record in the shape the gate reads: heading, block, then anything.

    `tail` is whatever the record says afterwards. It exists because the point
    of the declared position is that the tail cannot matter, and a case that
    never supplies one would not be testing that.
    """
    opening = f"# Witness record{LF}{LF}{FENCE}witness{LF}"
    return f"{opening}{declaration}{LF}{FENCE}{LF}{tail}"


def _readme_example() -> str:
    """The declaration witness/README.md instructs an author to write.

    Read out of the README's own `witness` block, so this is an address rather
    than a search through prose. A README with no such block fails loudly here:
    a document that stops instructing the shape is the defect this case exists
    to catch.
    """
    text = (sov_standing.WITNESS_DIR / "README.md").read_text(encoding="utf-8")
    found = CANONICAL.search(text)
    assert found is not None, "witness/README.md has no standing-supported example"
    return found.group(1).strip()


def _record(directory: Path, name: str, supports: str = "WITNESSED") -> None:
    """A record that says what it supports, which is what the gate now reads.

    The default was `BUILT -> WITNESSED` while the gate scanned a value for a
    standing token. The gate now compares the whole value, so the default is
    the exact spelling `witness/README.md` documents.
    """
    (directory / name).write_text(
        _body(f"standing_supported  {supports}"), encoding="utf-8", newline=LF)


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
                    "# observation" + LF * 2 + "It will not say what it supports.",
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
        self.assertEqual(self._gap_fields("BUILT_WITNESSED", "WITNESSED"), [])

    def test_the_directory_readme_is_still_not_a_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            _record(Path(tmp), "README.md")
            self.assertEqual(sov_standing.witness_records(Path(tmp)), {})


class LiveRepository(unittest.TestCase):
    def test_every_live_claim_carries_a_record(self):
        """The first version of this asserted that nothing claimed standing, which was
        true of that afternoon. The invariant is that a claim without a record is
        refused: `observation_service_status` claimed WITNESSED on 2026-09-03 with
        `witness/observation-service.md` behind it, and that is what is checked."""
        claims = sov_standing.read_claims()
        self.assertEqual([claim.field for claim in sov_standing.unsupported()], [],
                         "a status field claims standing that no witness record supports")
        for claim in claims:
            with self.subTest(field=claim.field):
                self.assertIsNone(sov_standing.refusal(claim))

    def test_a_deposited_record_does_not_advance_standing(self):
        """Records are what witness/ is for, and depositing one moves no status field.

        The invariant is the one `witness/README.md` states: a record makes
        advancing standing possible and never performs it. So records with no
        claim behind them must exist alongside any claim that has one; the day
        every record on file is matched by a claim, deposit has become promotion.
        """
        records = sov_standing.witness_records()
        self.assertNotIn("readme", records,
                         "the convention document is not an observation of anything")
        live = sov_standing.read_claims()
        with tempfile.TemporaryDirectory() as tmp:
            # With no record at all, every live claim is refused: the claim does not
            # carry itself.
            self.assertEqual([claim.field for claim in sov_standing.unsupported(witness_dir=Path(tmp))],
                             [claim.field for claim in live])
            # A record deposited for a subject no field claims changes neither the claims
            # read from STATUS.yaml nor the refusal of the claims it does not name.
            _record(Path(tmp), "asset-service.md")
            self.assertEqual(sov_standing.read_claims(), live)
            self.assertEqual([claim.field for claim in sov_standing.unsupported(witness_dir=Path(tmp))],
                             [claim.field for claim in live])


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
        return _body(f"standing_supported  {value}")

    def test_the_prose_label_no_longer_declares_anything(self):
        """`**Standing supported:**` in prose was the whole input contract for
        three rounds of this gate, and every round was defeated through it. It
        is now prose and nothing else: the declaration lives in the block. A
        record carrying only the prose form declares nothing, whatever it says.
        """
        for prose in ("**Standing supported:**" + LF + "WITNESSED.",
                      "**Standing supported: WITNESSED.**",
                      "**Standing supported: none.**"):
            with self.subTest(prose=prose):
                self.assertFalse(self._promotes(f"# observation{LF}{LF}{prose}{LF}"))

    def test_not_witnessed_inside_a_record_is_a_denial(self):
        """T3 reproduced at the site the first repair created. The whole-token
        discipline lived in `claimed_standing()` and was not carried across."""
        self.assertFalse(self._promotes(self._observation("NOT_WITNESSED.")))

    def test_a_value_naming_no_standing_supports_nothing(self):
        for value in ("OPEN -> BUILT.", "n/a", "BUILT.", "see the findings below."):
            with self.subTest(value=value):
                self.assertFalse(self._promotes(self._observation(value)))

    def test_a_denial_after_the_standing_still_denies_it(self):
        """`WITNESSED is refused` names a standing and refuses it in three words.

        This once needed a hand-written denial list. It does not any more: the
        value is compared whole and this is not the word. The case is kept
        because the behaviour it pins is still required, and because a future
        rewrite that reintroduces scanning has to defeat it again.
        """
        self.assertFalse(self._promotes(self._observation("WITNESSED is refused.")))
        self.assertFalse(self._promotes(self._observation("RATIFIED is refused.")))

    def test_naming_both_standings_is_ambiguous_and_supports_nothing(self):
        """Asserted on the reading rather than the verdict, deliberately.

        Under the scanning implementation this went through `unsupported()`,
        where a two-element set resolved arbitrarily and the over-reach rule
        caught roughly half the runs - so the case passed by set ordering rather
        than by the rule. A mutation run found that. Asserting on the reading is
        deterministic under any implementation.
        """
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "asset-service.md"
            path.write_text(self._observation("WITNESSED and RATIFIED."),
                            encoding="utf-8", newline=LF)
            self.assertIsNone(sov_standing.supported_standing(path))
        self.assertFalse(self._promotes(self._observation("WITNESSED and RATIFIED.")))

    def test_an_honest_record_still_supports_the_claim(self):
        self.assertTrue(self._promotes(self._observation("WITNESSED")))
        self.assertTrue(self._promotes(_body()))

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
                self._observation("RATIFIED"), encoding="utf-8", newline=LF)
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
        """The record body here is READ OUT of witness/README.md, not restated.

        The previous version of this case asserted a literal that also appeared
        in the README, which is two constants that happen to agree and no data
        flow between them. A witness proved it: it rewrote the README to instruct
        a shape the gate cannot read, and all thirty-one cases stayed green
        because the literal survived elsewhere in the file. Now the documented
        example IS the record under test, so misinstructing an author fails here.
        """
        example = _readme_example()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "asset-service.md"
            path.write_text(_body(example), encoding="utf-8", newline=LF)
            self.assertEqual(
                sov_standing.supported_standing(path), "WITNESSED",
                f"witness/README.md instructs {example!r}, which the gate cannot read")


class TheValueIsAStandingOrItIsNot(unittest.TestCase):
    """A third independent reading defeated the scanning implementation again.

    Three readings, three repairs, and each closed exactly the cases it was shown
    while leaving the class open. The class is scanning: any rule that looks for a
    standing *inside* a value has a tail of spellings that carry the token and
    mean something else, and the tail is not enumerable. The value is now compared
    whole against a closed set, which has no tail.
    """

    def _reading(self, value: str) -> str | None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "asset-service.md"
            path.write_text(_body(f"standing_supported  {value}"),
                            encoding="utf-8", newline=LF)
            return sov_standing.supported_standing(path)

    def test_a_self_witness_is_not_a_witness(self):
        """The sharpest of them. `AGENTS.md` exists in part to forbid this exact
        inversion - a build report cannot witness itself - and a token scan splits
        SELF_WITNESSED into SELF and WITNESSED and reads the second half as
        support for it. The gate would have promoted a record announcing the one
        thing the contract most plainly refuses."""
        self.assertIsNone(self._reading("SELF_WITNESSED."))
        self.assertIsNone(self._reading("BUILDER_WITNESSED."))

    def test_a_compound_spelling_is_not_the_word(self):
        for value in ("PRE-WITNESSED.", "PARTIALLY_WITNESSED.", "WITNESSED_IN_PART."):
            with self.subTest(value=value):
                self.assertIsNone(self._reading(value))

    def test_a_qualified_verdict_supports_nothing(self):
        """Each of these defeated a different hand-written denial list, which is
        the argument against having one. `subject to conditions` is not invented:
        it is reachable from README's own RATIFIABLE-WITH-CONDITIONS verdict."""
        for value in ("WITNESSED (retracted).", "WITNESSED - withdrawn.",
                      "WITNESSED subject to conditions.", "WITNESSED, pending repair."):
            with self.subTest(value=value):
                self.assertIsNone(self._reading(value))

    def test_a_lookalike_that_case_folds_onto_the_word_is_refused(self):
        """Case folding is not identity. The Turkish dotless i upper-cases to `I`,
        so this spelling passes an exact uppercase comparison. ASCII is required
        before the comparison, which is why it does not."""
        dotless = "W" + chr(0x131) + "TNESSED"
        self.assertEqual(dotless.upper(), "WITNESSED",
                         "the fold this case exists to catch no longer happens")
        self.assertNotEqual(dotless, "WITNESSED")
        self.assertIsNone(self._reading(dotless))

    def test_the_bare_word_is_read(self):
        self.assertEqual(self._reading("WITNESSED"), "WITNESSED")
        self.assertEqual(self._reading("witnessed"), "WITNESSED")

    def test_a_footnote_marker_is_not_the_word(self):
        """`WITNESSED*` with a qualifying footnote read as plain WITNESSED while
        markdown emphasis was stripped from the value. Inside a plain text block
        there is no emphasis to strip, so the marker is simply part of a word
        that is not this one."""
        for value in ("WITNESSED*", "WITNESSED.", "*WITNESSED*", "_WITNESSED_"):
            with self.subTest(value=value):
                self.assertIsNone(self._reading(value))


class NothingAfterTheBlockIsRead(unittest.TestCase):
    """The gate reads a position, and enumerating quotation forms is what failed.

    The previous repair stripped fenced blocks, inline spans and HTML comments and
    searched what was left. A fourth reading walked four quotation forms past it -
    a nested four-backtick fence, an unterminated fence, a blockquoted label, and
    an indented one - each on a complete record whose own verdict was NOT-YET, and
    each promoting a status field. The finding generalised: there is no finite list
    of ways markdown can quote, so stripping what looks like quotation is
    enumeration wearing structure's clothes.

    Position has no such tail. Each case below carries the defeat in its tail, on a
    record declaring `none`, and the tail cannot reach the verdict because nothing
    after the block is read.
    """

    FENCE4 = chr(96) * 4

    def _reading(self, tail: str, declaration: str = "standing_supported  none") -> str | None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "asset-service.md"
            path.write_text(_body(declaration, tail), encoding="utf-8", newline=LF)
            return sov_standing.supported_standing(path)

    def test_a_nested_fence_does_not_speak_for_the_record(self):
        """The shape the README itself now produces. Quoting the documented block
        verbatim needs an outer four-backtick fence, so the record most likely to
        trip this was a record about this gate."""
        inner = f"{FENCE}witness{LF}standing_supported  WITNESSED{LF}{FENCE}"
        self.assertIsNone(self._reading(f"{LF}{self.FENCE4}{LF}{inner}{LF}{self.FENCE4}{LF}"))

    def test_an_unterminated_fence_does_not_speak_for_the_record(self):
        self.assertIsNone(self._reading(f"{LF}{FENCE}{LF}standing_supported  WITNESSED{LF}"))

    def test_a_blockquoted_label_does_not_speak_for_the_record(self):
        self.assertIsNone(self._reading(f"{LF}> standing_supported  WITNESSED{LF}"))

    def test_an_indented_label_does_not_speak_for_the_record(self):
        self.assertIsNone(self._reading(f"{LF}    standing_supported  WITNESSED{LF}"))

    def test_a_second_block_does_not_speak_for_the_record(self):
        """The most direct attack on a position rule: declare it again, correctly,
        further down. The first block is the record; later ones are text."""
        later = f"{LF}{FENCE}witness{LF}standing_supported  WITNESSED{LF}{FENCE}{LF}"
        self.assertIsNone(self._reading(later))

    def test_the_record_still_speaks_when_it_quotes_the_example(self):
        """The honest shape, and the reason the position rule is worth having: a
        record may quote the documented block and still declare its own verdict.
        A gate that refused this would make a record about itself unwritable."""
        quoted = f"{LF}{FENCE}witness{LF}standing_supported  none{LF}{FENCE}{LF}"
        self.assertEqual(self._reading(quoted, "standing_supported  WITNESSED"), "WITNESSED")


class TheBlockMustBeWhereItSaysItIs(unittest.TestCase):
    """A position rule is only a rule if being out of position fails closed."""

    def _reading(self, text: str) -> str | None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "asset-service.md"
            path.write_text(text, encoding="utf-8", newline=LF)
            return sov_standing.supported_standing(path)

    def test_prose_before_the_block_means_there_is_no_block(self):
        text = (f"# observation{LF}{LF}A sentence first.{LF}{LF}"
                f"{FENCE}witness{LF}standing_supported  WITNESSED{LF}{FENCE}{LF}")
        self.assertIsNone(self._reading(text))

    def test_an_unterminated_block_is_not_a_block(self):
        text = f"# observation{LF}{LF}{FENCE}witness{LF}standing_supported  WITNESSED{LF}"
        self.assertIsNone(self._reading(text))

    def test_a_differently_labelled_fence_is_not_the_block(self):
        text = (f"# observation{LF}{LF}{FENCE}text{LF}"
                f"standing_supported  WITNESSED{LF}{FENCE}{LF}")
        self.assertIsNone(self._reading(text))

    def test_declaring_the_field_twice_inside_the_block_is_ambiguous(self):
        text = (f"# observation{LF}{LF}{FENCE}witness{LF}"
                f"standing_supported  WITNESSED{LF}standing_supported  none{LF}{FENCE}{LF}")
        self.assertIsNone(self._reading(text))

    def test_a_block_with_no_such_field_declares_nothing(self):
        text = f"# observation{LF}{LF}{FENCE}witness{LF}verdict  NOT-YET{LF}{FENCE}{LF}"
        self.assertIsNone(self._reading(text))

    def test_the_title_heading_and_blank_lines_may_precede_the_block(self):
        text = (f"{LF}# Witness record{LF}{LF}{FENCE}witness{LF}"
                f"standing_supported  WITNESSED{LF}{FENCE}{LF}")
        self.assertEqual(self._reading(text), "WITNESSED")

    def test_a_second_heading_before_the_block_means_there_is_no_block(self):
        """This case previously asserted the opposite and blessed a defect. The
        skip admitted an unbounded run of headings, so `## Example only:` above a
        quoted block promoted over the record's own declaration further down. One
        title heading is the bound; a record declares before it explains."""
        text = (f"# Witness record{LF}## Example only{LF}{LF}{FENCE}witness{LF}"
                f"standing_supported  WITNESSED{LF}{FENCE}{LF}")
        self.assertIsNone(self._reading(text))


class AnUnclosedBlockDoesNotRunOn(unittest.TestCase):
    """The open was a position and the close was an unbounded forward search.

    A fifth reading proved that on a shipped record: remove `witness/host-service.md`'s
    closing fence, paste `witness/README.md` where a record would naturally quote
    it, and the block ran to the README's own fence, swallowing the document and
    reading the quoted value as the record's declaration. The record still said
    Verdict NOT-YET and Standing supported: none, and the gate promoted it.

    The body is now bounded by what it may contain and by how much: field lines
    only, and few of them. Both halves are needed - a field line is a weak shape,
    since `some prose here` matches it, and a cap alone would not stop a short
    run-on.

    The witness's own construction - break `witness/host-service.md`'s fence and
    paste `witness/README.md` below it - did not reproduce here, on 91bd7ab or
    now: the record's own field line and the quoted one are two declarations, and
    two is ambiguous, so that shape was already refused for a different reason.
    The class is real regardless, and the two cases below promote at 91bd7ab and
    are refused here. What could not be reproduced is said rather than implied.
    """

    def _reading(self, text: str) -> str | None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "asset-service.md"
            path.write_text(text, encoding="utf-8", newline=LF)
            return sov_standing.supported_standing(path)

    def test_an_unclosed_block_does_not_reach_a_later_fence(self):
        """The defeat as reported: the record declares none, forgets its fence,
        and quotes a block far below whose value is WITNESSED."""
        text = (f"# Witness record{LF}{LF}{FENCE}witness{LF}"
                f"standing_supported  none{LF}{LF}"
                f"## Findings{LF}{LF}Every finding is written out at length here."
                f"{LF}{LF}{FENCE}witness{LF}standing_supported  WITNESSED{LF}{FENCE}{LF}")
        self.assertIsNone(self._reading(text))

    def test_prose_inside_the_body_ends_it(self):
        text = (f"# Witness record{LF}{LF}{FENCE}witness{LF}"
                f"standing_supported  WITNESSED{LF}Some prose.{LF}{FENCE}{LF}")
        self.assertIsNone(self._reading(text))

    def test_a_blank_line_inside_the_body_ends_it(self):
        text = (f"# Witness record{LF}{LF}{FENCE}witness{LF}"
                f"standing_supported  WITNESSED{LF}{LF}{FENCE}{LF}")
        self.assertIsNone(self._reading(text))

    def test_a_body_past_the_cap_is_not_a_declaration(self):
        fields = LF.join(f"field_{n}  value" for n in range(sov_standing.MAX_BLOCK_LINES))
        text = (f"# Witness record{LF}{LF}{FENCE}witness{LF}{fields}{LF}"
                f"standing_supported  WITNESSED{LF}{FENCE}{LF}")
        self.assertIsNone(self._reading(text))

    def test_the_cap_leaves_room_for_a_real_declaration(self):
        text = (f"# Witness record{LF}{LF}{FENCE}witness{LF}verdict  NOT-YET{LF}"
                f"observed  2026-08-27{LF}standing_supported  WITNESSED{LF}{FENCE}{LF}")
        self.assertEqual(self._reading(text), "WITNESSED")

    def test_an_empty_unclosed_block_does_not_adopt_a_quoted_one(self):
        """Verified against 91bd7ab, the commit the finding was raised on: this
        returns WITNESSED there and nothing here. It is the minimal form of the
        defect - the open never closes, so the scan runs to the quoted block's
        fence and adopts the quoted value as the record's own."""
        text = (f"# Witness record{LF}{LF}{FENCE}witness{LF}{LF}## Findings{LF}{LF}"
                f"{FENCE}witness{LF}standing_supported  WITNESSED{LF}{FENCE}{LF}")
        self.assertIsNone(self._reading(text))

    def test_an_unclosed_block_does_not_run_through_prose_to_a_field(self):
        """Also verified as WITNESSED at 91bd7ab. Forty lines of prose then a
        field line: the distance is the point, and no distance is now enough."""
        prose = f"prose line{LF}" * 40
        text = (f"# Witness record{LF}{LF}{FENCE}witness{LF}{prose}"
                f"standing_supported  WITNESSED{LF}{FENCE}{LF}")
        self.assertIsNone(self._reading(text))


class TheClaimSideMustNotUnderRead(unittest.TestCase):
    """The direction this gate's own argument names as the unsafe one.

    `claimed_standing()` is liberal on purpose: over-reading a status value only
    asks for a witness record that may not be needed, while under-reading lets a
    claim reach the tree with nobody asking for evidence. The suite had one case
    on the liberal axis and none on this one, and the implementation did not meet
    the principle - a quoted value and a trailing comment are STATUS.yaml's own
    idiom and both hid a claim completely.
    """

    def _claims(self, line: str) -> list[str]:
        path = _status(line + LF)
        return [claim.standing for claim in sov_standing.read_claims(path)]

    def test_a_quoted_value_is_still_a_claim(self):
        self.assertEqual(self._claims('asset_service_status: "BUILT_WITNESSED"'), ["WITNESSED"])
        self.assertEqual(self._claims("asset_service_status: 'BUILT_RATIFIED'"), ["RATIFIED"])

    def test_a_trailing_comment_does_not_hide_the_claim(self):
        self.assertEqual(
            self._claims("asset_service_status: BUILT_WITNESSED  # see witness/asset-service.md"),
            ["WITNESSED"])

    def test_an_indented_field_is_still_a_claim(self):
        """The live file carries nested mappings, and an anchored pattern could
        not see into them at all."""
        self.assertEqual(self._claims("  asset_service_status: BUILT_WITNESSED"), ["WITNESSED"])

    def test_a_negation_survives_every_one_of_those_forms(self):
        """Over-reading is safe here; reading a denial as a claim is merely noisy
        but reading it wrong in the other direction is not. T3 stays checked."""
        for line in ('asset_service_status: "BUILT_SELF_TESTED_NOT_WITNESSED"',
                     "asset_service_status: BUILT_SELF_TESTED_NOT_WITNESSED  # nothing yet",
                     "  asset_service_status: BUILT_SELF_TESTED_NOT_WITNESSED"):
            with self.subTest(line=line):
                self.assertEqual(self._claims(line), [])

    def test_the_live_status_file_is_read_the_same_way_by_both_paths(self):
        """A control, so this class cannot pass vacuously: the real file is read
        through the same entry point as the planted lines, and yields exactly the
        claims a line-by-line read of it yields."""
        live = sov_standing.read_claims()
        text = sov_standing.STATUS.read_text(encoding="utf-8")
        planted = [standing for line in text.splitlines() for standing in self._claims(line)]
        self.assertEqual([claim.standing for claim in live], planted)
        self.assertEqual([claim.field for claim in live], ["observation_service_status"])


class TheTwoSidesFailInOppositeDirections(unittest.TestCase):
    """`claimed_standing()` still scans tokens, and that is not the inconsistency
    it looks like.

    A witness asked why the record side abandoned token scanning as having an
    unenumerable tail while the STATUS.yaml side kept it. The answer is that the
    two sides fail in opposite directions, and only one of them can promote.

    On the record side, over-reading a value grants standing that was never
    declared, so it must be exact. On the claim side, over-reading a value only
    demands a witness record for a field that may not have needed one - the
    conservative error. Under-reading is what would be unsafe there, because a
    claim nobody detects is a claim nobody asks for evidence of. So the claim side
    is deliberately liberal and the record side deliberately strict.
    """

    def test_a_compound_claim_is_detected_and_therefore_needs_a_record(self):
        """`SELF_WITNESSED` supports nothing as a record and still counts as a
        claim here, which is the asymmetry stated as a case: the same spelling
        grants nothing and demands evidence."""
        self.assertEqual(sov_standing.claimed_standing("BUILT_SELF_WITNESSED"), "WITNESSED")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "asset-service.md"
            path.write_text(_body("standing_supported  SELF_WITNESSED"),
                            encoding="utf-8", newline=LF)
            self.assertIsNone(sov_standing.supported_standing(path))

    def test_a_negated_claim_is_still_not_a_claim(self):
        """The one direction the claim side may not err in: reading NOT_WITNESSED
        as a claim would be noise, but reading it as no claim when it is one would
        let a field advance unasked. T3 is why this is checked whole-token."""
        self.assertIsNone(sov_standing.claimed_standing("BUILT_SELF_TESTED_NOT_WITNESSED"))
