"""Checks for the status-claim crosswalk and the refusals that grade it.

The crosswalk exists so that three kinds of claim about one subject stop sharing one key in
`STATUS.yaml`. Its own correctness therefore matters more than usual: a crosswalk a reader
would trust and should not is worse than none.

Three independent witnesses broke three drafts of a rule that tried to read an artifact
standing out of the value's prose. The first read it from prose outright and admitted
`WITNESSED` on a value reading `NOT_WITNESSED`. The second compared whole tokens and treated
`NOT` as denial, and fell to `NOT_YET`, `NEVER`, `AWAITING` and a hyphenated `NOT`. The third
asked only what the value led with, and fell to `WITNESSED_RETRACTED`, `RATIFIED_NOT` and
`-WITNESSED` - and also refused the correct entry on five live fields.

There is no fourth spelling. The extraction is gone, `scripts/sov_standing.py` owns standing
claims, and the tests below cover what remains: which subject a line is about, which kind of
claim it makes, and a closed set of keys. `WhatWasRemoved` exists so that reintroducing the
extraction fails loudly rather than quietly starting the cycle again.
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


def entry(**overrides) -> dict:
    """A well-formed entry, so a test changes exactly the one thing it is about."""
    base = {
        "field": "record_service_status",
        "value": "BUILT_SELF_TESTED_NOT_WITNESSED",
        "subject": "record-service",
        "claim_kind": "STATUS",
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
    """Splitting matters for the kind rule, which is the only rule left that reads a value."""

    def test_it_splits_on_every_non_alphanumeric_run(self):
        self.assertEqual(refusals.tokens("RULED-O19_X"), ["RULED", "O19", "X"])

    def test_it_upper_cases(self):
        self.assertEqual(refusals.tokens("ruled_open"), ["RULED", "OPEN"])

    def test_it_drops_empty_runs(self):
        self.assertEqual(refusals.tokens("__RULED__"), ["RULED"])


class Derivation(unittest.TestCase):
    """What an entry may not declare for itself."""

    def test_subject_is_the_hyphenated_field_stem(self):
        self.assertEqual(refusals.derived_subject("asset_service_status"), "asset-service")

    def test_kind_follows_the_value_prefix(self):
        self.assertEqual(refusals.expected_kind("RULED_O19"), "RULING")
        self.assertEqual(refusals.expected_kind("OWNER_ACCEPTED_A2_SPEC"), "OWNER_ACCEPTANCE")
        self.assertEqual(refusals.expected_kind("OWNER_ACCEPTED_PHASE_I_CONTRACT"), "STATUS")

    def test_the_kind_rule_is_case_insensitive(self):
        self.assertEqual(refusals.expected_kind("ruled_open_until_bdo"), "RULING")

    def test_the_kind_rule_is_not_separator_literal(self):
        """A witness found `RULED-O19` typing as a reversible STATUS, because the prefix was
        compared as raw bytes while everything else tokenised."""
        self.assertEqual(refusals.expected_kind("RULED-O19"), "RULING")
        self.assertEqual(refusals.expected_kind("OWNER-ACCEPTED-A2-SPEC"), "OWNER_ACCEPTANCE")

    def test_an_accepted_value_without_a_packet_digit_is_a_status(self):
        """`OWNER_ACCEPTED_ALPHA` is the document reporting an acceptance, not the record of
        one. Eighteen live fields turn on this reading; decisions/0074 records it as Bdo's."""
        self.assertEqual(refusals.expected_kind("OWNER_ACCEPTED_ALPHA"), "STATUS")
        self.assertEqual(refusals.expected_kind("OWNER_ACCEPTED"), "STATUS")


class WhatWasRemoved(unittest.TestCase):
    """The standing extraction is gone. These fail if anyone starts the cycle again."""

    def test_no_module_still_extracts_a_standing(self):
        for gone in ("leading_standing", "token_asserts", "standing_not_leading"):
            with self.subTest(gone=gone):
                self.assertFalse(hasattr(refusals, gone))

    def test_the_contract_declares_no_standing_vocabulary(self):
        contract = sov_status_claims.load_contract()
        for gone in ("artifact_standing_ladder", "artifact_standing_rule", "standing_sources",
                     "token_trap"):
            with self.subTest(gone=gone):
                self.assertNotIn(gone, contract)

    def test_no_entry_carries_a_standing_or_its_source(self):
        for candidate in sov_status_claims.load_contract()["crosswalk"]:
            with self.subTest(field=candidate["field"]):
                self.assertNotIn("artifact_standing", candidate)
                self.assertNotIn("standing_source", candidate)

    def test_the_values_that_defeated_all_three_drafts_now_earn_nothing(self):
        """Each of these got a false standing past one of the three rules. None of them can
        now, because nothing reads a standing out of a value."""
        for value in ("NOT_WITNESSED", "NOT_YET_WITNESSED", "NEVER_WITNESSED",
                      "BUILT-NOT_WITNESSED", "WITNESSED_RETRACTED", "RATIFIED_NOT",
                      "-WITNESSED", "¬WITNESSED", "PROPOSED_CONTRACT_BUILT"):
            with self.subTest(value=value):
                good = entry(field="x_status", value=value, subject="x")
                self.assertEqual(codes([good], f"x_status: {value}"), set())


class WitnessBypasses(unittest.TestCase):
    """Every case an independent witness got past a previous draft, in the part that remains."""

    def test_an_unknown_key_is_refused(self):
        """A witness added asserted_standing, settled_by, authority and a resurrected
        standing_source to live entries; all four passed a type check over named keys."""
        text = "record_service_status: BUILT_SELF_TESTED_NOT_WITNESSED"
        for extra in ("asserted_standing", "settled_by", "authority", "standing_source"):
            with self.subTest(extra=extra):
                bad = dict(entry(), **{extra: "RATIFIED"})
                self.assertEqual(codes([bad], text), {"ENTRY_UNKNOWN_KEY"})

    def test_a_renamed_subject_cannot_dissolve_a_collision(self):
        text = "byom_status: OWNER_ACCEPTED_PHASE_I_CONTRACT"
        bad = entry(field="byom_status", value="OWNER_ACCEPTED_PHASE_I_CONTRACT",
                    subject="byom-ruling")
        self.assertEqual(codes([bad], text), {"SUBJECT_NOT_DERIVED"})

    def test_a_mistyped_kind_cannot_disable_the_kind_rules(self):
        text = "byom_status: RULED_CONTRACT_STANDS_O12"
        bad = entry(field="byom_status", value="RULED_CONTRACT_STANDS_O12", subject="byom",
                    claim_kind="RULLING")
        self.assertEqual(codes([bad], text), {"CLAIM_KIND_UNDECLARED"})

    def test_an_owner_acceptance_cannot_be_demoted_to_a_status(self):
        value = "OWNER_ACCEPTED_A2_PHASE_I_LOGICAL_SPEC"
        bad = entry(field="specification_status", value=value, subject="specification",
                    claim_kind="STATUS", reference="A2")
        self.assertEqual(codes([bad], f"specification_status: {value}"),
                         {"CLAIM_KIND_CONTRADICTS_VALUE"})

    def test_the_same_field_and_value_cannot_be_typed_twice(self):
        text = "record_service_status: BUILT_SELF_TESTED_NOT_WITNESSED"
        self.assertEqual(codes([entry(), entry()], text), {"CLAIM_KIND_COLLISION"})

    def test_the_reader_names_the_class_of_line_it_cannot_parse(self):
        """Two drafts were each taught the previous witness's examples. A list item, a flow
        mapping, a dotted key and a path-like key walked past the second."""
        for line in ("- byom_status: OPEN", "{byom_status: OPEN}", "node.v1_status: OPEN",
                     "services/asset_status: OPEN", "ai-native_status: OPEN",
                     '"quoted_status": OPEN', "x_status : OPEN", "FOO_STATUS: OPEN",
                     "  indented_status: OPEN", "spaced_value_status: BUILT AND TESTED"):
            with self.subTest(line=line):
                self.assertEqual(codes([], line), {"FIELD_UNREADABLE"})

    def test_the_reader_does_not_cry_wolf(self):
        """A detector that fires on a line no entry could ever match is a defect too: the
        only repair would be editing STATUS.yaml, which this contract does not do."""
        for line in ("status: FOUNDING", "  status: OPEN", "phase: FOUNDING", "my status: x"):
            with self.subTest(line=line):
                self.assertEqual(codes([], line), set())

    def test_a_packet_reference_is_graded_in_both_directions(self):
        value = "OWNER_ACCEPTED_A2_PHASE_I_LOGICAL_SPEC"
        wrong = entry(field="specification_status", value=value, subject="specification",
                      claim_kind="OWNER_ACCEPTANCE", reference="A9")
        self.assertEqual(codes([wrong], f"specification_status: {value}"),
                         {"REFERENCE_CONTRADICTS_VALUE"})
        invented = entry(field="x_status", value="CHARTERED_BOUNDARY", subject="x",
                         reference="A3")
        self.assertEqual(codes([invented], "x_status: CHARTERED_BOUNDARY"),
                         {"REFERENCE_CONTRADICTS_VALUE"})

    def test_a_packet_reference_is_anchored(self):
        """`$` matches before a trailing newline; a witness got `A2\\n` past it."""
        value = "OWNER_ACCEPTED_A2_PHASE_I_LOGICAL_SPEC"
        bad = entry(field="specification_status", value=value, subject="specification",
                    claim_kind="OWNER_ACCEPTANCE", reference="A2\n")
        self.assertEqual(codes([bad], f"specification_status: {value}"),
                         {"REFERENCE_CONTRADICTS_VALUE"})

    def test_a_malformed_entry_refuses_rather_than_raising(self):
        text = "record_service_status: BUILT_SELF_TESTED_NOT_WITNESSED"
        for broken in (entry(subject=None), entry(detail=None)):
            with self.subTest(broken=broken):
                self.assertEqual(codes([broken], text), {"ENTRY_MALFORMED"})
        missing = entry()
        del missing["reference"]
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
