"""Checks for the status-claim crosswalk and the refusals that grade it.

The crosswalk exists so that three kinds of claim about one subject stop sharing one key
in `STATUS.yaml`. Its own correctness therefore matters more than usual: a crosswalk that
admits a false standing is worse than no crosswalk, because a reader would trust it.

An independent witness defeated the first version of this check
(`reports/observations/2026-08-27-status-claims-typed-witness-observation.json`). The cases
it got past are here as tests rather than only as prose, because a defect that is only
described comes back.

The one that matters most is the negation: `NOT_WITNESSED` contains the token `WITNESSED`
(CLAUDE.md T3), so a substring implementation passes every positive case here and still
reads the whole repository as witnessed.
"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import sov_status_claims  # noqa: E402
from sovstatus import refusals  # noqa: E402

DENIED = "OWNER_ACCEPTED_CONTEXT_PROFILE_BUILT_SELF_TESTED_NOT_WITNESSED"


def entry(**overrides) -> dict:
    """A well-formed entry, so a test changes exactly the one thing it is about."""
    base = {
        "field": "record_service_status",
        "value": "BUILT_SELF_TESTED_NOT_WITNESSED",
        "subject": "record-service",
        "claim_kind": "STATUS",
        "artifact_standing": "BUILT",
        "standing_source": "TOKEN",
        "detail": "self-tested",
        "reference": None,
    }
    base.update(overrides)
    return base


def codes(entries: list[dict], text: str) -> set[str]:
    contract = sov_status_claims.load_contract()
    fields = sov_status_claims.read_fields(text)
    return {d.split(":", 1)[0]
            for d in sov_status_claims.grade(fields, entries, contract, text)}


class TokenAssertion(unittest.TestCase):
    """`token_asserts` is the T3-critical function; a substring test would pass wrongly."""

    def test_a_whole_undenied_token_asserts(self):
        self.assertTrue(refusals.token_asserts("BUILT_SELF_TESTED", "BUILT"))

    def test_a_leading_token_asserts(self):
        self.assertTrue(refusals.token_asserts("BUILT", "BUILT"))

    def test_a_token_preceded_by_not_is_a_denial(self):
        self.assertFalse(refusals.token_asserts("BUILT_SELF_TESTED_NOT_WITNESSED", "WITNESSED"))

    def test_a_substring_is_not_a_token(self):
        self.assertFalse(refusals.token_asserts("REBUILT_ALREADY", "BUILT"))

    def test_an_absent_token_does_not_assert(self):
        self.assertFalse(refusals.token_asserts("CHARTERED_BOUNDARY", "BUILT"))

    def test_a_second_undenied_occurrence_still_asserts(self):
        self.assertTrue(refusals.token_asserts("NOT_BUILT_THEN_BUILT", "BUILT"))


class Derivation(unittest.TestCase):
    """What an entry may not declare for itself."""

    def test_subject_is_the_hyphenated_field_stem(self):
        self.assertEqual(refusals.derived_subject("asset_service_status"), "asset-service")

    def test_kind_follows_the_value_prefix(self):
        self.assertEqual(refusals.expected_kind("RULED_O19"), "RULING")
        self.assertEqual(refusals.expected_kind("OWNER_ACCEPTED_A2_SPEC"), "OWNER_ACCEPTANCE")
        self.assertEqual(refusals.expected_kind("OWNER_ACCEPTED_PHASE_I_CONTRACT"), "STATUS")

    def test_an_accepted_value_without_a_packet_digit_is_a_status(self):
        """`OWNER_ACCEPTED_ALPHA` is prose, not packet A-something."""
        self.assertEqual(refusals.expected_kind("OWNER_ACCEPTED_ALPHA"), "STATUS")


class WitnessBypasses(unittest.TestCase):
    """Every case the independent witness got past the first version."""

    def test_a_standing_the_value_denies_is_refused_whatever_the_source(self):
        for source in ("READING", "NONE", "TOKEN"):
            with self.subTest(source=source):
                bad = entry(field="sov_operating_agent_status", value=DENIED,
                            subject="sov-operating-agent", artifact_standing="WITNESSED",
                            standing_source=source)
                self.assertTrue(codes([bad], f"sov_operating_agent_status: {DENIED}"))

    def test_a_renamed_subject_cannot_dissolve_a_collision(self):
        text = "byom_status: OWNER_ACCEPTED_PHASE_I_CONTRACT"
        bad = entry(field="byom_status", value="OWNER_ACCEPTED_PHASE_I_CONTRACT",
                    subject="byom-ruling", artifact_standing=None, standing_source="NONE")
        self.assertEqual(codes([bad], text), {"SUBJECT_NOT_DERIVED"})

    def test_a_mistyped_kind_cannot_disable_the_kind_rules(self):
        text = "byom_status: RULED_CONTRACT_STANDS_O12"
        bad = entry(field="byom_status", value="RULED_CONTRACT_STANDS_O12", subject="byom",
                    claim_kind="RULLING", artifact_standing=None, standing_source="NONE")
        self.assertEqual(codes([bad], text), {"CLAIM_KIND_UNDECLARED"})

    def test_an_owner_acceptance_cannot_be_demoted_to_a_status(self):
        value = "OWNER_ACCEPTED_A2_PHASE_I_LOGICAL_SPEC"
        text = f"specification_status: {value}"
        bad = entry(field="specification_status", value=value, subject="specification",
                    claim_kind="STATUS", artifact_standing=None, standing_source="NONE")
        self.assertEqual(codes([bad], text), {"CLAIM_KIND_CONTRADICTS_VALUE"})

    def test_the_same_field_and_value_cannot_be_typed_twice(self):
        text = "record_service_status: BUILT_SELF_TESTED_NOT_WITNESSED"
        self.assertEqual(codes([entry(), entry()], text), {"CLAIM_KIND_COLLISION"})

    def test_an_indented_field_is_named_rather_than_skipped(self):
        self.assertEqual(codes([], "  nested_thing_status: OWNER_ACCEPTED"),
                         {"FIELD_UNREADABLE"})

    def test_a_value_carrying_a_space_is_named_rather_than_skipped(self):
        self.assertEqual(codes([], "spaced_thing_status: BUILT AND TESTED"),
                         {"FIELD_UNREADABLE"})

    def test_a_malformed_entry_refuses_rather_than_raising(self):
        text = "record_service_status: BUILT_SELF_TESTED_NOT_WITNESSED"
        for broken in (entry(subject=None), entry(detail=None)):
            with self.subTest(broken=broken):
                self.assertEqual(codes([broken], text), {"ENTRY_MALFORMED"})
        missing = entry()
        del missing["artifact_standing"]
        self.assertEqual(codes([missing], text), {"ENTRY_MALFORMED"})


class LiveCrosswalk(unittest.TestCase):
    """The committed crosswalk against the committed document."""

    def setUp(self):
        self.contract = sov_status_claims.load_contract()
        self.text = sov_status_claims.STATUS.read_text(encoding="utf-8")

    def test_it_grades_clean(self):
        fields = sov_status_claims.read_fields(self.text)
        self.assertEqual(
            sov_status_claims.grade(fields, self.contract["crosswalk"], self.contract, self.text),
            [])

    def test_dropping_one_entry_is_caught(self):
        """Guards against a check that passes because it inspects nothing."""
        fields = sov_status_claims.read_fields(self.text)
        short = self.contract["crosswalk"][1:]
        found = sov_status_claims.grade(fields, short, self.contract, self.text)
        self.assertTrue(any(d.startswith("FIELD_UNTYPED") for d in found))

    def test_every_duplicated_key_resolves_to_two_kinds(self):
        seen: dict[str, list[str]] = {}
        for field, _ in sov_status_claims.read_fields(self.text):
            seen.setdefault(field, []).append(field)
        for field, hits in seen.items():
            if len(hits) < 2:
                continue
            kinds = [e["claim_kind"] for e in self.contract["crosswalk"] if e["field"] == field]
            with self.subTest(field=field):
                self.assertEqual(len(kinds), len(set(kinds)), "a duplicate the typing hides")

    def test_no_entry_declares_a_standing_without_a_token(self):
        for candidate in self.contract["crosswalk"]:
            with self.subTest(field=candidate["field"]):
                if candidate["artifact_standing"] is not None:
                    self.assertEqual(candidate["standing_source"], "TOKEN")
                    self.assertTrue(refusals.token_asserts(candidate["value"],
                                                           candidate["artifact_standing"]))


class Selfcheck(unittest.TestCase):
    """The corpus must prove each refusal alone, and cover the declared table exactly."""

    def test_the_corpus_proves_every_declared_refusal(self):
        self.assertEqual(sov_status_claims.selfcheck(), [])

    def test_each_defeating_case_names_a_declared_refusal(self):
        import json
        contract = sov_status_claims.load_contract()
        cases = json.loads(sov_status_claims.CORPUS.read_text(encoding="utf-8"))["cases"]
        named = {c["expect"] for c in cases if c["expect"] is not None}
        self.assertEqual(named, set(contract["refusals"]))
        self.assertEqual(len([c for c in cases if c["expect"] is None]), 1)


if __name__ == "__main__":
    unittest.main()
