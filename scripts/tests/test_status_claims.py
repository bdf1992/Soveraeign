"""Checks for the status-claim crosswalk and the refusals that grade it.

The crosswalk exists so that three kinds of claim about one subject stop sharing one key in
`STATUS.yaml`. Its own correctness therefore matters more than usual: a crosswalk that
admits a false standing is worse than no crosswalk, because a reader would trust it.

Two independent witnesses defeated two drafts of this check, and both defeats had the same
shape - a guard written against the instance that was reported rather than the class it
named. The first got a standing past an unverifiable prose source. The second walked past a
NOT-aware token comparison using `NOT_YET`, `NEVER`, `AWAITING` and a hyphenated `NOT`, and
past a reader that had been taught two shapes of unparseable line rather than the class.

Every case either witness got through is a test here rather than only a note in a decision
record, because a defect that is only described comes back. The negator battery in
`LeadingStanding` is deliberately longer than the list of words either witness used: the
point of the current rule is that it asks a question with no vocabulary in it, and these
cases are what would fail loudly if someone reintroduced one.
"""

from __future__ import annotations

from pathlib import Path
import json
import sys
import unittest

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import sov_status_claims  # noqa: E402
from sovstatus import refusals  # noqa: E402

LADDER = {"OPEN", "BUILT", "WITNESSED", "RATIFIED"}


def entry(**overrides) -> dict:
    """A well-formed entry, so a test changes exactly the one thing it is about."""
    base = {
        "field": "record_service_status",
        "value": "BUILT_SELF_TESTED_NOT_WITNESSED",
        "subject": "record-service",
        "claim_kind": "STATUS",
        "artifact_standing": "BUILT",
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


class Tokenisation(unittest.TestCase):
    """Splitting on underscores alone hid a hyphenated negator from the previous rule."""

    def test_it_splits_on_every_non_alphanumeric_run(self):
        self.assertEqual(refusals.tokens("BUILT-NOT_WITNESSED"), ["BUILT", "NOT", "WITNESSED"])

    def test_it_upper_cases(self):
        self.assertEqual(refusals.tokens("built_and_tested"), ["BUILT", "AND", "TESTED"])

    def test_it_drops_empty_runs(self):
        self.assertEqual(refusals.tokens("__BUILT__"), ["BUILT"])


class LeadingStanding(unittest.TestCase):
    """A standing is the value's first token or nothing. No negation vocabulary."""

    def test_a_value_leading_with_a_rung_asserts_it(self):
        self.assertEqual(refusals.leading_standing("BUILT_SELF_TESTED", LADDER), "BUILT")

    def test_a_value_leading_with_anything_else_asserts_nothing(self):
        for value in ("PROPOSED_CONTRACT_BUILT", "OWNER_ACCEPTED_BUILT", "RULED_O17_BUILT"):
            with self.subTest(value=value):
                self.assertIsNone(refusals.leading_standing(value, LADDER))

    def test_no_negator_or_deferral_lets_a_trailing_rung_assert(self):
        """The battery. A vocabulary of negations is always short by one word; this is not
        a vocabulary, so every one of these fails for the same single reason."""
        for value in ("NOT_WITNESSED", "NOT_YET_WITNESSED", "NEVER_WITNESSED",
                      "NO_WITNESSED", "UN_WITNESSED", "PENDING_WITNESSED",
                      "AWAITING_WITNESSED", "BUILT-NOT_WITNESSED",
                      "SELF_TESTED_NOT-YET_WITNESSED", "NOT_NOT_WITNESSED",
                      "ALMOST_WITNESSED", "WOULD_HAVE_BEEN_WITNESSED"):
            with self.subTest(value=value):
                self.assertNotEqual(refusals.leading_standing(value, LADDER), "WITNESSED")

    def test_the_lowercase_form_of_a_rung_still_asserts_it(self):
        self.assertEqual(refusals.leading_standing("built_and_tested", LADDER), "BUILT")


class Derivation(unittest.TestCase):
    """What an entry may not declare for itself."""

    def test_subject_is_the_hyphenated_field_stem(self):
        self.assertEqual(refusals.derived_subject("asset_service_status"), "asset-service")

    def test_kind_follows_the_value_prefix(self):
        self.assertEqual(refusals.expected_kind("RULED_O19"), "RULING")
        self.assertEqual(refusals.expected_kind("OWNER_ACCEPTED_A2_SPEC"), "OWNER_ACCEPTANCE")
        self.assertEqual(refusals.expected_kind("OWNER_ACCEPTED_PHASE_I_CONTRACT"), "STATUS")

    def test_the_kind_rule_is_case_insensitive(self):
        """The previous draft compared raw bytes here and upper-cased elsewhere, so a
        lowercase value could be silently demoted from a ruling to a status."""
        self.assertEqual(refusals.expected_kind("ruled_open_until_bdo"), "RULING")

    def test_an_accepted_value_without_a_packet_digit_is_a_status(self):
        """`OWNER_ACCEPTED_ALPHA` is the document reporting an acceptance, not the record of
        one. Eighteen live fields turn on this reading; decisions/0074 records it as Bdo's."""
        self.assertEqual(refusals.expected_kind("OWNER_ACCEPTED_ALPHA"), "STATUS")


class WitnessBypasses(unittest.TestCase):
    """Every case either independent witness got past a previous draft."""

    def test_a_standing_the_value_does_not_lead_with_is_refused(self):
        for value in ("OWNER_ACCEPTED_BUILT_SELF_TESTED_NOT_WITNESSED", "NOT_YET_WITNESSED",
                      "NEVER_WITNESSED", "BUILT-NOT_WITNESSED", "AWAITING_WITNESSED"):
            with self.subTest(value=value):
                bad = entry(field="x_status", value=value, subject="x",
                            artifact_standing="WITNESSED")
                self.assertEqual(codes([bad], f"x_status: {value}"),
                                 {"STANDING_NOT_THE_LEADING_TOKEN"})

    def test_a_value_leading_with_a_rung_must_declare_it(self):
        bad = entry(field="x_status", value="BUILT_AND_TESTED", subject="x",
                    artifact_standing=None)
        self.assertEqual(codes([bad], "x_status: BUILT_AND_TESTED"),
                         {"STANDING_NOT_THE_LEADING_TOKEN"})

    def test_a_renamed_subject_cannot_dissolve_a_collision(self):
        text = "byom_status: OWNER_ACCEPTED_PHASE_I_CONTRACT"
        bad = entry(field="byom_status", value="OWNER_ACCEPTED_PHASE_I_CONTRACT",
                    subject="byom-ruling", artifact_standing=None)
        self.assertEqual(codes([bad], text), {"SUBJECT_NOT_DERIVED"})

    def test_a_mistyped_kind_cannot_disable_the_kind_rules(self):
        text = "byom_status: RULED_CONTRACT_STANDS_O12"
        bad = entry(field="byom_status", value="RULED_CONTRACT_STANDS_O12", subject="byom",
                    claim_kind="RULLING", artifact_standing=None)
        self.assertEqual(codes([bad], text), {"CLAIM_KIND_UNDECLARED"})

    def test_an_owner_acceptance_cannot_be_demoted_to_a_status(self):
        value = "OWNER_ACCEPTED_A2_PHASE_I_LOGICAL_SPEC"
        bad = entry(field="specification_status", value=value, subject="specification",
                    claim_kind="STATUS", artifact_standing=None, reference="A2")
        self.assertEqual(codes([bad], f"specification_status: {value}"),
                         {"CLAIM_KIND_CONTRADICTS_VALUE"})

    def test_the_same_field_and_value_cannot_be_typed_twice(self):
        text = "record_service_status: BUILT_SELF_TESTED_NOT_WITNESSED"
        self.assertEqual(codes([entry(), entry()], text), {"CLAIM_KIND_COLLISION"})

    def test_the_reader_names_the_class_of_line_it_cannot_parse(self):
        """A previous detector was taught the two shapes the first witness reported; the
        second walked past it with four more."""
        for line in ("ai-native_status: OPEN", '"quoted_status": OPEN', "x_status : OPEN",
                     "FOO_STATUS: OPEN", "  indented_status: OPEN",
                     "spaced_value_status: BUILT AND TESTED"):
            with self.subTest(line=line):
                self.assertEqual(codes([], line), {"FIELD_UNREADABLE"})

    def test_a_packet_reference_is_graded_not_declared(self):
        value = "OWNER_ACCEPTED_A2_PHASE_I_LOGICAL_SPEC"
        wrong = entry(field="specification_status", value=value, subject="specification",
                      claim_kind="OWNER_ACCEPTANCE", artifact_standing=None, reference="A9")
        self.assertEqual(codes([wrong], f"specification_status: {value}"),
                         {"REFERENCE_CONTRADICTS_VALUE"})
        invented = entry(field="x_status", value="CHARTERED_BOUNDARY", subject="x",
                         artifact_standing=None, reference="A3")
        self.assertEqual(codes([invented], "x_status: CHARTERED_BOUNDARY"),
                         {"REFERENCE_CONTRADICTS_VALUE"})

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
        self.fields = sov_status_claims.read_fields(self.text)

    def test_it_grades_clean(self):
        self.assertEqual(
            sov_status_claims.grade(self.fields, self.contract["crosswalk"],
                                    self.contract, self.text), [])

    def test_dropping_one_entry_is_caught(self):
        """Guards against a check that passes because it inspects nothing."""
        found = sov_status_claims.grade(self.fields, self.contract["crosswalk"][1:],
                                        self.contract, self.text)
        self.assertTrue(any(d.startswith("FIELD_UNTYPED") for d in found))

    def test_every_duplicated_key_resolves_to_two_kinds(self):
        seen: dict[str, int] = {}
        for field, _ in self.fields:
            seen[field] = seen.get(field, 0) + 1
        duplicated = [f for f, n in seen.items() if n > 1]
        self.assertEqual(len(duplicated), 8, "the eight this contract exists for")
        for field in duplicated:
            kinds = [e["claim_kind"] for e in self.contract["crosswalk"] if e["field"] == field]
            with self.subTest(field=field):
                self.assertEqual(len(kinds), len(set(kinds)), "a duplicate the typing hides")

    def test_no_entry_declares_a_standing_it_does_not_lead_with(self):
        ladder = set(self.contract["artifact_standing_ladder"])
        for candidate in self.contract["crosswalk"]:
            with self.subTest(field=candidate["field"]):
                self.assertEqual(candidate["artifact_standing"],
                                 refusals.leading_standing(candidate["value"], ladder))

    def test_no_entry_carries_a_removed_field(self):
        """`standing_source` was deleted rather than graded: a declared field the checker
        never read is the shape of defect this table exists to refuse."""
        for candidate in self.contract["crosswalk"]:
            self.assertNotIn("standing_source", candidate)


class Selfcheck(unittest.TestCase):
    """The corpus must prove each refusal alone, and cover the declared table exactly."""

    def test_the_corpus_proves_every_declared_refusal(self):
        self.assertEqual(sov_status_claims.selfcheck(), [])

    def test_each_defeating_case_names_a_declared_refusal(self):
        contract = sov_status_claims.load_contract()
        cases = json.loads(sov_status_claims.CORPUS.read_text(encoding="utf-8"))["cases"]
        named = {c["expect"] for c in cases if c["expect"] is not None}
        self.assertEqual(named, set(contract["refusals"]))

    def test_a_corpus_whose_positive_case_proves_nothing_is_refused(self):
        """An empty document against an empty crosswalk satisfies every rule."""
        import tempfile
        vacuous = {"cases": [{"id": "v", "expect": None, "status_lines": [], "crosswalk": []}]}
        handle = Path(tempfile.mkstemp(suffix=".json")[1])
        handle.write_text(json.dumps(vacuous), encoding="utf-8")
        self.assertTrue(sov_status_claims.selfcheck(handle,
                                                    sov_status_claims.load_contract()))


if __name__ == "__main__":
    unittest.main()
