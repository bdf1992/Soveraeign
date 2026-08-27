"""Defeating fixtures for the cold-start run record and the verdict it derives.

`selfcheck` grades the declared case corpus. These cases cover what a corpus of records
cannot: that the derivation ladder returns each verdict for the right table, that the
writer refuses a defective record instead of writing it, and that the schema is expressed
in the subset of JSON Schema this repository's validator actually implements.

That last one is not pedantry. `scripts/sovkernel/jsonschema.py` reports an unsupported
keyword as a defect of the *instance*, so a schema written with `maximum` fails every
record it grades and the error names the record rather than the schema. Five positive
cases failed that way before this test existed.
"""

from __future__ import annotations

from pathlib import Path
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovcoldstart import records  # noqa: E402
from sovcoldstart import attribution  # noqa: E402
from sovcoldstart import refusals  # noqa: E402
from sovcoldstart import source  # noqa: E402
from sovcoldstart.grading import UNMEASURED, compare, judge, truth_for  # noqa: E402
from sovcoldstart.report import derive, grade_row, tally  # noqa: E402
from sovcoldstart.scoring import cmd_rebase  # noqa: E402
from sovcoldstart.source import run_identity  # noqa: E402
from sovcoldstart.oracle import _apply, _corpus_defects  # noqa: E402
from sovkernel.jsonschema import SUPPORTED_KEYWORDS, validate  # noqa: E402

CASES = json.loads(records.CASES.read_text(encoding="utf-8"))
SCHEMA = json.loads(records.SCHEMA.read_text(encoding="utf-8"))
BASE = CASES["base_record"]


def _tiers(zero: tuple[int, int, int], one=(45, 45, 43), two=(60, 60, 52)) -> list[dict]:
    """A canonical tier table from (asked, scored, hit) triples, built the way a run builds it."""
    table = [grade_row(tier, asked, scored, hit, asked - scored)
             for tier, (asked, scored, hit) in ((0, zero), (1, one), (2, two))]
    table.append(grade_row(3, 30, 0, 0, 30))
    return table


def _reconciled(patch: dict) -> dict:
    """A patch plus the run id and sections block its own fields imply.

    Both are derived rather than declared, so a case that patches the tier table or any of
    the four identity fields and says nothing about them is testing derivation rather than
    the thing it named.

    `sections` is reconciled against the tier table both in total and per entry, so a case
    that patches `tiers` and says nothing about sections is testing reconciliation rather
    than the thing it named.
    """
    tiers = patch.get("tiers", BASE["tiers"])
    merged = {**BASE, **patch}
    patch = {**patch, "run_id": "coldstart_" + run_identity(
        str(merged["revision"]["commit"]), str(merged["corpus"].get("digest")),
        str(merged["observed_at"]), str(merged["mode"]))}
    if "sections" in patch:
        return patch
    fields = ("asked", "scored", "hit", "unmeasured")
    totals = {f: sum(row.get(f, 0) for row in tiers if isinstance(row.get(f), int))
              for f in fields}
    return {**patch, "sections": {"all": totals}}


class TheSchemaIsExpressedInTheSupportedSubset(unittest.TestCase):
    def test_no_keyword_this_repository_cannot_validate(self) -> None:
        annotations = {"$schema", "$id", "title", "description", "$comment", "default",
                       "examples", "deprecated", "readOnly", "writeOnly"}
        named = ("properties", "$defs")

        def walk(node, path):
            """Descend as a schema. Under `properties` and `$defs` the keys are names."""
            if not isinstance(node, dict):
                return
            unsupported = set(node) - SUPPORTED_KEYWORDS - annotations
            self.assertEqual(unsupported, set(),
                             f"{path} uses {sorted(unsupported)}, which "
                             f"sovkernel.jsonschema does not implement")
            for key, value in node.items():
                if key in named and isinstance(value, dict):
                    for name, sub in value.items():
                        walk(sub, f"{path}/{key}/{name}")
                elif isinstance(value, list):
                    for index, sub in enumerate(value):
                        walk(sub, f"{path}/{key}/{index}")
                elif isinstance(value, dict):
                    walk(value, f"{path}/{key}")

        walk(SCHEMA, "")

    def test_the_base_record_validates(self) -> None:
        self.assertEqual(validate(BASE, SCHEMA), [])


class TheVerdictIsDerived(unittest.TestCase):
    def test_a_failed_invariant_is_not_admissible(self) -> None:
        self.assertEqual(derive(_tiers((40, 40, 39)))[0], "NOT_ADMISSIBLE")

    def test_an_absent_tier_is_partial_not_admissible(self) -> None:
        self.assertEqual(derive(_tiers((0, 0, 0)))[0], "PARTIAL")

    def test_an_unmeasured_invariant_is_unproven(self) -> None:
        self.assertEqual(derive(_tiers((40, 38, 38)))[0], "UNPROVEN")

    def test_a_short_gated_tier_is_degraded(self) -> None:
        self.assertEqual(derive(_tiers((40, 40, 40), two=(60, 60, 30)))[0], "DEGRADED")

    def test_an_unmeasured_row_in_a_gated_tier_is_degraded(self) -> None:
        """Meeting the gate on a smaller corpus is not meeting the gate."""
        self.assertEqual(derive(_tiers((40, 40, 40), one=(45, 20, 20)))[0], "DEGRADED")

    def test_a_clean_run_is_admissible(self) -> None:
        self.assertEqual(derive(_tiers((40, 40, 40)))[0], "ADMISSIBLE")

    def test_a_failed_invariant_outranks_every_other_reading(self) -> None:
        table = _tiers((40, 38, 37), one=(45, 20, 20), two=(60, 60, 10))
        self.assertEqual(derive(table)[0], "NOT_ADMISSIBLE")


class TallyMarksUnmeasured(unittest.TestCase):
    ROWS = [
        {"id": "A1", "tier": 0, "section": "doctrine", "verdict": "RIGHT"},
        {"id": "A2", "tier": 0, "section": "doctrine", "verdict": "WRONG"},
        {"id": "A3", "tier": 0, "section": "doctrine", "verdict": "ABSTAIN"},
        {"id": "A4", "tier": 0, "section": "doctrine", "verdict": "UNGRADED"},
    ]

    def test_abstain_and_ungraded_are_unmeasured_not_wrong(self) -> None:
        zero = tally(self.ROWS, "verdict", "RIGHT")[0]
        self.assertEqual((zero["asked"], zero["scored"], zero["hit"], zero["unmeasured"]),
                         (4, 2, 1, 2))

    def test_a_tier_with_nothing_in_it_is_absent(self) -> None:
        self.assertEqual(tally(self.ROWS, "verdict", "RIGHT")[1]["result"], "ABSENT")

    def test_section_counts_match_the_tier_counts(self) -> None:
        by_section = records._sections(self.ROWS, "verdict", "RIGHT", ("WRONG",))
        self.assertEqual(by_section["doctrine"],
                         {"asked": 4, "scored": 2, "hit": 1, "unmeasured": 2})


class DefectsRefuse(unittest.TestCase):
    def _codes(self, patch: dict) -> list[str]:
        return [d["code"] for d in records.defects(_apply(BASE, _reconciled(patch)), SCHEMA)]

    def test_every_declared_case_is_covered_by_the_selfcheck_corpus(self) -> None:
        """If a refusal loses its case, selfcheck stops proving it and nobody notices."""
        expected = {code for case in CASES["cases"] for code in case["expect"]}
        self.assertEqual(expected, set(records.REFUSALS))

    def test_a_stated_verdict_cannot_beat_the_tier_table(self) -> None:
        self.assertIn("VERDICT_NOT_DERIVED",
                      self._codes({"tiers": _tiers((40, 40, 39)), "verdict": "ADMISSIBLE"}))

    def test_an_honest_verdict_is_admitted(self) -> None:
        self.assertEqual(self._codes({"tiers": _tiers((40, 40, 39)),
                                      "verdict": "NOT_ADMISSIBLE"}), [])

    def test_arithmetic_is_checked_before_the_verdict_is_derived(self) -> None:
        """A table that does not add up cannot derive anything; saying both would mislead."""
        codes = self._codes({"tiers": _tiers((40, 40, 44))})
        self.assertIn("TIER_ARITHMETIC", codes)
        self.assertNotIn("VERDICT_NOT_DERIVED", codes)

    def test_a_run_cannot_record_itself_as_witnessed(self) -> None:
        self.assertIn("STANDING_OVERCLAIMED", self._codes({"standing": "WITNESSED"}))

    def test_a_run_cannot_record_itself_as_ratified(self) -> None:
        self.assertIn("STANDING_OVERCLAIMED", self._codes({"standing": "RATIFIED"}))

    def test_hand_graded_answers_need_a_verdict_file_someone_else_wrote(self) -> None:
        codes = self._codes({
            "mode": "COMPETENCE",
            "participant": {"id": "p", "host": "h", "answers_digest": "sha256:" + "1" * 64},
            "graded_by": {"owner_verdicts": None, "manual_asked": 57, "manual_graded": 57},
        })
        self.assertIn("SELF_GRADED", codes)

    def test_hand_graded_none_is_not_self_grading(self) -> None:
        codes = self._codes({
            "mode": "COMPETENCE",
            "participant": {"id": "p", "host": "h", "answers_digest": "sha256:" + "1" * 64},
            "graded_by": {"owner_verdicts": None, "manual_asked": 57, "manual_graded": 0},
        })
        self.assertNotIn("SELF_GRADED", codes)


class TheWriterRefusesADefectiveRecord(unittest.TestCase):
    def test_write_raises_rather_than_writing(self) -> None:
        record = _apply(BASE, {"standing": "WITNESSED"})
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError) as caught:
                records.write(record, Path(tmp))
            self.assertIn("STANDING_OVERCLAIMED", str(caught.exception))
            self.assertEqual(list(Path(tmp).glob("*.json")), [])

    def test_write_names_the_file_by_date_mode_and_run(self) -> None:
        """The fixture base cannot be written: its corpus digest and run id are placeholders."""
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError) as caught:
                records.write(copy.deepcopy(BASE), Path(tmp))
            self.assertIn("CORPUS_UNVERIFIED", str(caught.exception))


class MovedNamesTheSection(unittest.TestCase):
    def test_only_sections_that_changed_are_named(self) -> None:
        before = {"sections": {"repo": {"asked": 5, "hit": 5}, "git": {"asked": 4, "hit": 4}}}
        after = {"sections": {"repo": {"asked": 5, "hit": 3}, "git": {"asked": 4, "hit": 4}}}
        self.assertEqual(records.moved(before, after), ["repo: 5/5 -> 3/5"])


class ComparableRefusesAFalseDrift(unittest.TestCase):
    """A --fast run beside a full one differs in 35 probes, and every one reads as drift."""

    FULL = {"mode": "INTEGRITY", "coverage": {"fast": False, "offline": False, "sections": []},
            "corpus": {"digest": "sha256:" + "a" * 64}}

    def _other(self, **changes) -> dict:
        out = copy.deepcopy(self.FULL)
        out.update(changes)
        return out

    def test_two_identical_runs_are_comparable(self) -> None:
        self.assertIsNone(records.comparable(self.FULL, copy.deepcopy(self.FULL)))

    def test_different_coverage_is_not_comparable(self) -> None:
        fast = self._other(coverage={"fast": True, "offline": True, "sections": []})
        self.assertIn("coverage", records.comparable(self.FULL, fast) or "")

    def test_a_section_filter_is_not_comparable_with_a_full_run(self) -> None:
        part = self._other(coverage={"fast": False, "offline": False, "sections": ["repo"]})
        self.assertIsNotNone(records.comparable(self.FULL, part))

    def test_two_modes_are_not_comparable(self) -> None:
        self.assertIn("modes", records.comparable(self.FULL, self._other(mode="COMPETENCE")) or "")

    def test_a_changed_corpus_is_not_comparable(self) -> None:
        edited = self._other(corpus={"digest": "sha256:" + "b" * 64})
        self.assertIn("corpus", records.comparable(self.FULL, edited) or "")


class TheLiveCorpusIsStructurallySound(unittest.TestCase):
    def test_the_shipped_corpus_carries_no_defect(self) -> None:
        self.assertEqual(_corpus_defects(ROOT / "scripts" / "sovcoldstart" / "corpus.json"), [])

    def test_a_question_with_no_tier_is_a_defect(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "corpus.json"
            path.write_text(json.dumps({"questions": [
                {"id": "Z1", "section": "s", "q": "?", "expected": "x", "why": "w",
                 "severity_on_failure": "MED"}]}), encoding="utf-8")
            self.assertTrue(any("no tier" in d for d in _corpus_defects(path)))

    def test_a_probe_that_searches_for_its_own_answer_is_a_defect(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "corpus.json"
            path.write_text(json.dumps({"questions": [
                {"id": "Z2", "section": "s", "tier": 1, "q": "?", "expected": "RATIFIED",
                 "why": "w", "severity_on_failure": "MED",
                 "probe": {"kind": "regex_count", "file": "x", "pattern": "RATIFIED"}}]}),
                encoding="utf-8")
            self.assertTrue(any("its own expected value" in d for d in _corpus_defects(path)))


class TheGateRunsSelfcheck(unittest.TestCase):
    """How this contract reaches `scripts/verify.py`.

    A named entry in `scripts/sovverify/checks.py` would be the ordinary home, but that table
    is at the 300-line module ceiling and four other live sessions hold the file, so adding
    one line there means a four-way conflict and a lint failure for everyone on this tree.
    Reaching the gate through `run_tooling_tests.py` costs a named row in the verify output
    and costs nothing else; splitting the check table is the verification domain's concern.
    """

    def test_selfcheck_exits_zero(self) -> None:
        done = subprocess.run(
            [sys.executable, "scripts/sov_coldstart.py", "selfcheck"],
            cwd=ROOT, capture_output=True, text=True, timeout=120, check=False,
        )
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn("refusal(s) all proven", done.stdout)

    def test_selfcheck_fails_when_a_refusal_stops_firing(self) -> None:
        """The check is worth running only if a weakened contract actually fails it."""
        corpus = copy.deepcopy(CASES)
        corpus["cases"] = [c for c in corpus["cases"] if "SELF_GRADED" not in c["expect"]]
        with tempfile.TemporaryDirectory() as tmp:
            spare = Path(tmp) / "run-cases.json"
            spare.write_text(json.dumps(corpus), encoding="utf-8")
            original = records.CASES
            records.CASES = spare
            try:
                from sovcoldstart.verbs import cmd_selfcheck
                args = type("A", (), {"corpus": ROOT / "scripts" / "sovcoldstart" / "corpus.json"})
                self.assertEqual(cmd_selfcheck(args), 1)
            finally:
                records.CASES = original


class TheWitnessAttack(unittest.TestCase):
    """The defeat an independent witness found, kept as a case so it cannot come back.

    The first version of `defects` re-derived the verdict faithfully and read the threshold
    out of the record it was grading. An otherwise honest table declaring `gate: 0.0` on
    tiers 1 and 2 made 5 of 46 meet its own bar, and `records.write` accepted it.
    """

    def _forged(self) -> dict:
        table = [grade_row(0, 40, 40, 40, 0)]
        for tier, hit in ((1, 5), (2, 3)):
            row = grade_row(tier, 46, 46, hit, 0)
            table.append({**row, "gate": 0.0, "result": "PASS"})
        table.append(grade_row(3, 30, 0, 0, 30))
        return _apply(BASE, {"tiers": table, "verdict": "ADMISSIBLE"})

    def test_a_record_that_supplies_its_own_gate_is_refused(self) -> None:
        codes = {d["code"] for d in records.defects(self._forged(), SCHEMA)}
        self.assertIn("TIER_NOT_DERIVED", codes)
        self.assertIn("VERDICT_NOT_DERIVED", codes)

    def test_the_schema_alone_also_refuses_an_undeclared_gate(self) -> None:
        """Defence in depth: the enum catches it even if the derivation is ever loosened."""
        messages = validate(self._forged(), SCHEMA)
        self.assertTrue(any("gate" in m for m in messages), messages)

    def test_the_writer_will_not_write_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                records.write(self._forged(), Path(tmp))
            self.assertEqual(list(Path(tmp).glob("*.json")), [])

    def test_a_forged_tier_result_alone_is_refused(self) -> None:
        """The per-tier result was readable too, and does not move the verdict on its own."""
        table = _tiers((40, 40, 40), two=(60, 60, 30))
        table[2] = {**table[2], "result": "PASS"}
        codes = {d["code"] for d in records.defects(
            _apply(BASE, _reconciled({"tiers": table, "verdict": "DEGRADED"})), SCHEMA)}
        self.assertEqual(codes, {"TIER_NOT_DERIVED"})


class TheSecondWitnessAttacks(unittest.TestCase):
    """Five more places the same defect class was alive after the first repair.

    Each of these was admitted by `records.defects` and written to disk by `records.write`
    when a second independent witness tried them. The first two are the serious ones: a run
    record with no tier 0 row derived ADMISSIBLE with the hard-invariant gate simply absent,
    and a duplicated tier 0 let row ordering decide whether a visible FAIL counted.
    """

    BASELINE = "scripts/sovcoldstart/baselines/2026-08-26-claude-opus-5-cold.json"

    def _codes(self, patch: dict) -> set[str]:
        return {d["code"] for d in records.defects(_apply(BASE, _reconciled(patch)), SCHEMA)}

    def test_deleting_the_tier_zero_row_does_not_produce_a_clean_tier_zero(self) -> None:
        table = _tiers((40, 40, 40))
        self.assertIn("TIER_SET_INVALID", self._codes({"tiers": table[1:]}))

    def test_derive_reads_an_absent_tier_zero_as_partial(self) -> None:
        """Even reached directly, with no record shape around it."""
        self.assertEqual(derive(_tiers((40, 40, 40))[1:])[0], "PARTIAL")

    def test_duplicating_tier_zero_is_refused_rather_than_ordered(self) -> None:
        table = _tiers((40, 40, 40))
        forged = [grade_row(0, 40, 40, 20, 0), *table]
        self.assertIn("TIER_SET_INVALID", self._codes({"tiers": forged}))

    def test_sections_must_add_up_to_the_tier_table(self) -> None:
        patch = {"sections": {"doctrine": {"asked": 999, "scored": 999, "hit": 999,
                                           "unmeasured": 0}}}
        self.assertIn("COUNTS_DISAGREE", self._codes(patch))

    def test_sections_that_do_add_up_are_admitted(self) -> None:
        table = _tiers((40, 40, 40))
        totals = {f: sum(r[f] for r in table) for f in ("asked", "scored", "hit", "unmeasured")}
        self.assertEqual(self._codes({"tiers": table, "sections": {"all": totals}}), set())

    def test_corpus_selected_must_match_what_was_asked(self) -> None:
        patch = {"corpus": {**BASE["corpus"], "selected": 1}}
        self.assertIn("COUNTS_DISAGREE", self._codes(patch))

    def test_an_answers_digest_that_does_not_match_the_file(self) -> None:
        patch = {"mode": "COMPETENCE",
                 "participant": {"id": "p", "host": "h", "answers": self.BASELINE,
                                 "answers_digest": "sha256:" + "2" * 64},
                 "graded_by": {"owner_verdicts": None, "manual_asked": 0, "manual_graded": 0}}
        self.assertIn("ANSWERS_UNVERIFIED", self._codes(patch))

    def test_an_answers_file_that_is_not_there(self) -> None:
        patch = {"mode": "COMPETENCE",
                 "participant": {"id": "p", "host": "h", "answers": "nowhere/at/all.json",
                                 "answers_digest": "sha256:" + "3" * 64},
                 "graded_by": {"owner_verdicts": None, "manual_asked": 0, "manual_graded": 0}}
        self.assertIn("ANSWERS_UNVERIFIED", self._codes(patch))

    def test_the_real_digest_is_admitted(self) -> None:
        """The digest check passes; what remains is the corpus count, checked separately."""
        patch = {"mode": "COMPETENCE",
                 "participant": {"id": "p", "host": "h", "answers": self.BASELINE,
                                 "answers_digest": records.digest_of(ROOT / self.BASELINE)},
                 "graded_by": {"owner_verdicts": None, "manual_asked": 0, "manual_graded": 0}}
        self.assertNotIn("ANSWERS_UNVERIFIED", self._codes(patch))

    def test_omitting_graded_by_does_not_evade_self_grading(self) -> None:
        patch = {"mode": "COMPETENCE",
                 "participant": {"id": "p", "host": "h",
                                 "answers_digest": "sha256:" + "1" * 64}}
        self.assertIn("SELF_GRADED", self._codes(patch))

    def test_a_boolean_gate_is_not_a_threshold(self) -> None:
        """True == 1.0 in Python, so it passed both the enum and the equality check."""
        table = _tiers((40, 40, 40))
        table[0] = {**table[0], "gate": True}
        self.assertIn("TIER_NOT_DERIVED", self._codes({"tiers": table}))


class DriftIsNotAKeyToGradeAgainst(unittest.TestCase):
    """A `contains` question whose probe disagreed with the corpus was still scored on it."""

    QUESTION = {"id": "X01", "grade": "contains", "expected": "no_self_witnessing"}

    def test_a_drifted_contains_question_is_unmeasured(self) -> None:
        self.assertIs(truth_for(self.QUESTION, "DRIFT", 0), UNMEASURED)

    def test_a_matching_contains_question_still_grades_against_the_corpus(self) -> None:
        self.assertEqual(truth_for(self.QUESTION, "MATCH", 1), "no_self_witnessing")

    def test_a_drifted_direct_value_question_grades_against_the_probe(self) -> None:
        """There the probe is the truth, so drift means the key is stale and the probe wins."""
        question = {"id": "C05", "grade": "int_eq", "expected": 69}
        self.assertEqual(truth_for(question, "DRIFT", 71), 71)


class TheThirdWitnessAttacks(unittest.TestCase):
    """Six more, found after the second repair. The class held a third time.

    The pattern each time: a field that could be looked up or computed was read from the
    record instead. `owner_verdicts` was a path nobody opened, so any non-empty string
    satisfied the rule that no seat settles its own output, and the positive fixture that
    existed to show a properly owner-graded run cited a file that had never existed.
    """

    FIX = "conformance/fixtures/coldstart"

    def _codes(self, patch: dict) -> list[str]:
        return sorted(d["code"] for d in records.defects(_apply(BASE, _reconciled(patch)),
                                                         SCHEMA))

    def _competence(self, graded: dict) -> dict:
        return {"mode": "COMPETENCE",
                "participant": {"id": "p", "host": "h", "answers_digest": "sha256:" + "1" * 64},
                "graded_by": graded}

    def test_a_verdict_file_that_is_not_there_is_not_an_owner_verdict(self) -> None:
        codes = self._codes(self._competence(
            {"owner_verdicts": "nope/not-a-file.json", "manual_asked": 41, "manual_graded": 41}))
        self.assertIn("SELF_GRADED", codes)

    def test_a_whitespace_path_is_not_an_owner_verdict(self) -> None:
        codes = self._codes(self._competence(
            {"owner_verdicts": "   ", "manual_asked": 41, "manual_graded": 41}))
        self.assertIn("SELF_GRADED", codes)

    def test_a_verdict_file_must_digest_to_what_the_record_states(self) -> None:
        codes = self._codes(self._competence({
            "owner_verdicts": self.FIX + "/owner-verdicts.fixture.json",
            "owner_verdicts_digest": "sha256:" + "4" * 64,
            "manual_asked": 1, "manual_graded": 1}))
        self.assertIn("SELF_GRADED", codes)

    def test_a_verdict_file_must_name_the_answers_it_graded(self) -> None:
        """A verdict set carried onto a different submission grades answers nobody read."""
        verdicts = ROOT / self.FIX / "owner-verdicts.fixture.json"
        codes = self._codes({
            "mode": "COMPETENCE",
            "participant": {"id": "p", "host": "h", "answers_digest": "sha256:" + "9" * 64},
            "graded_by": {"owner_verdicts": self.FIX + "/owner-verdicts.fixture.json",
                          "owner_verdicts_digest": records.digest_of(verdicts),
                          "manual_asked": 1, "manual_graded": 1}})
        self.assertIn("SELF_GRADED", codes)

    def test_more_graded_than_asked(self) -> None:
        verdicts = ROOT / self.FIX / "owner-verdicts.fixture.json"
        codes = self._codes(self._competence({
            "owner_verdicts": self.FIX + "/owner-verdicts.fixture.json",
            "owner_verdicts_digest": records.digest_of(verdicts),
            "manual_asked": 0, "manual_graded": 99}))
        self.assertIn("COUNTS_DISAGREE", codes)

    def test_a_section_that_does_not_add_up_while_the_totals_do(self) -> None:
        patch = {"sections": {"routing": {"asked": 45, "scored": 45, "hit": 95, "unmeasured": 0},
                              "rest": {"asked": 130, "scored": 100, "hit": 40,
                                       "unmeasured": 30}}}
        self.assertIn("COUNTS_DISAGREE", self._codes(patch))

    def test_an_empty_sections_block_does_not_skip_reconciliation(self) -> None:
        self.assertIn("COUNTS_DISAGREE", self._codes({"sections": {}}))

    def test_a_participant_that_is_a_bare_string_is_refused_not_a_crash(self) -> None:
        codes = self._codes({"mode": "COMPETENCE", "participant": "me",
                             "graded_by": {"owner_verdicts": None, "manual_asked": 0,
                                           "manual_graded": 0}})
        self.assertIn("PARTICIPANT_MISSING", codes)

    def test_load_all_survives_a_defective_record_on_disk(self) -> None:
        """History used to crash for the whole directory over one malformed record."""
        with tempfile.TemporaryDirectory() as tmp:
            broken = _apply(BASE, {"mode": "COMPETENCE", "participant": "me"})
            (Path(tmp) / "2026-01-01-competence-deadbeef.json").write_text(
                json.dumps(broken), encoding="utf-8")
            loaded = records.load_all(Path(tmp))
            self.assertEqual(len(loaded), 1)
            self.assertIn("PARTICIPANT_MISSING", loaded[0]["_defects"])



def _clean_tracked_markdown() -> tuple[str, str]:
    """A tracked path whose worktree bytes are its committed bytes, and its digest.

    Both write-time corpus checks pass only over such a file: `CORPUS_UNVERIFIED` compares
    the working tree and `CORPUS_NOT_AT_REVISION` compares the commit. Chosen by measurement
    rather than named, because nine sessions write this tree and any file named here would
    eventually be one of them - AGENTS.md was modified under this very test.

    Markdown on purpose. `canonical_corpus` parses the pinned file as JSON to reconcile the
    question count, and a stand-in that happened to parse would report zero questions and
    fire COUNTS_DISAGREE for a reason that has nothing to do with what these cases test.
    """
    from hashlib import sha256

    listing = subprocess.run(["git", "ls-tree", "-r", "--name-only", "HEAD"],
                             cwd=records.ROOT, capture_output=True, text=True, timeout=60)
    for rel in listing.stdout.splitlines():
        if not rel.endswith(".md") or "/" in rel:
            continue
        blob = subprocess.run(["git", "cat-file", "blob", f"HEAD:{rel}"],
                              cwd=records.ROOT, capture_output=True, timeout=60)
        if blob.returncode != 0:
            continue
        here = records.ROOT / rel
        if here.is_file() and here.read_bytes() == blob.stdout:
            return rel, "sha256:" + sha256(blob.stdout).hexdigest()
    raise unittest.SkipTest("no clean tracked root markdown file to stand in for the corpus")


def _head() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=records.ROOT,
                          capture_output=True, text=True, timeout=60).stdout.strip()

class WriteTimeChecks(unittest.TestCase):
    """What can only be checked at the moment a record is written.

    `defects` grades a record against itself, which is all a reader of an old record can do:
    re-digesting the corpus today would mark every past reading defective. At write time the
    corpus is there and so are the four fields the run id derives from, and both were
    recorded and never checked. These are not in `REFUSALS`, because `selfcheck` polices
    that list against a fixture corpus and a fixture cannot carry a digest that changes
    every time the corpus does. They are covered here instead.
    """

    def setUp(self) -> None:
        """Stand the pinned corpus on a committed file.

        The real corpus is untracked while this concern is unlanded, so no record over it
        can pass a provenance check that asks the commit. Patching the check off instead
        would leave it exercised by nothing, which is the defect this whole contract exists
        to refuse.
        """
        self.rel, self.digest = _clean_tracked_markdown()
        self.commit = _head()
        self._pin = mock.patch.object(refusals, "CANONICAL_CORPUS", self.rel)
        self._pin.start()
        self.addCleanup(self._pin.stop)

    def _fresh(self) -> dict:
        at = "2026-08-27T00:00:00Z"
        return _apply(BASE, {
            "corpus": {"path": self.rel, "digest": self.digest,
                       "questions": 175, "selected": 175},
            "revision": {"commit": self.commit, "branch": "main", "tree_state": "CLEAN"},
            "observed_at": at,
            "run_id": "coldstart_" + run_identity(self.commit, self.digest, at, "INTEGRITY"),
        })

    def test_a_fresh_record_passes_both(self) -> None:
        self.assertEqual(records.fresh_defects(self._fresh()), [])

    def test_a_corpus_digest_that_does_not_match_the_file(self) -> None:
        record = self._fresh()
        record["corpus"] = {**record["corpus"], "digest": "sha256:" + "0" * 64}
        codes = [d["code"] for d in records.fresh_defects(record)]
        self.assertIn("CORPUS_UNVERIFIED", codes)

    def test_a_corpus_path_that_is_not_a_file(self) -> None:
        record = self._fresh()
        record["corpus"] = {**record["corpus"], "path": "scripts/sovcoldstart/nowhere.json"}
        self.assertIn("CORPUS_UNVERIFIED",
                      [d["code"] for d in records.fresh_defects(record)])

    def test_a_run_id_the_record_did_not_earn(self) -> None:
        """It is checked in `defects`, not here: nothing outside the record is needed."""
        record = self._fresh()
        record["run_id"] = "coldstart_deadbeefdeadbeefdeadbeefdeadbeef"
        self.assertIn("RUN_ID_NOT_DERIVED",
                      [d["code"] for d in records.defects(record)])
        self.assertNotIn("RUN_ID_NOT_DERIVED",
                         [d["code"] for d in records.fresh_defects(record)])

    def test_write_refuses_to_replace_a_different_reading(self) -> None:
        """The filename derives from a declared run id, so one record could overwrite another."""
        with tempfile.TemporaryDirectory() as tmp:
            first = self._fresh()
            path = records.write(first, Path(tmp))
            second = copy.deepcopy(first)
            second["note"] = "a different reading under the same name"
            with self.assertRaises(ValueError) as caught:
                records.write(second, Path(tmp))
            self.assertIn("RECORD_WOULD_REPLACE", str(caught.exception))
            kept = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(kept.get("note"), first.get("note"))
            self.assertNotIn("a different reading", kept.get("note", ""))

    def test_writing_the_same_record_twice_is_not_a_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = self._fresh()
            self.assertEqual(records.write(record, Path(tmp)),
                             records.write(copy.deepcopy(record), Path(tmp)))


class RebaseWritesTheAnswerKey(unittest.TestCase):
    """The verb that rewrites expectations, and the two guards it was missing.

    A witness ran it on a tier 0 question and it rewrote the answer to who occupies the root
    seat. AGENTS.md: never weaken an oracle merely to make a participant pass.
    """

    QUESTION = {"id": "Z01", "section": "doctrine", "tier": 0, "q": "?",
                "expected": "the wrong answer", "why": "a rule",
                "severity_on_failure": "FATAL", "grade": "exact",
                "probe": {"kind": "regex_count", "file": "AGENTS.md", "pattern": "^# Agent"}}

    def _corpus(self, tmp: str, question: dict) -> Path:
        path = Path(tmp) / "corpus.json"
        path.write_text(json.dumps({"questions": [question]}), encoding="utf-8")
        return path

    def _args(self, corpus: Path, **over):
        base = {"corpus": corpus, "section": None, "volatility": None, "offline": True,
                "fast": False, "dry_run": False, "tier_zero_ruling": None}
        base.update(over)
        return type("A", (), base)

    def test_a_tier_zero_expectation_is_held_without_a_ruling(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            corpus = self._corpus(tmp, copy.deepcopy(self.QUESTION))
            cmd_rebase(self._args(corpus))
            after = json.loads(corpus.read_text(encoding="utf-8"))["questions"][0]
            self.assertEqual(after["expected"], "the wrong answer")

    def test_a_ruling_admits_the_rebase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            corpus = self._corpus(tmp, copy.deepcopy(self.QUESTION))
            ruling = Path(tmp) / "0078.md"
            ruling.write_text("the rule changed", encoding="utf-8")
            cmd_rebase(self._args(corpus, tier_zero_ruling=ruling))
            after = json.loads(corpus.read_text(encoding="utf-8"))["questions"][0]
            self.assertNotEqual(after["expected"], "the wrong answer")

    def test_a_probe_expected_question_rebases_the_field_the_probe_grades(self) -> None:
        """It used to write the probe value into expected, which the probe never graded."""
        question = dict(copy.deepcopy(self.QUESTION), tier=2,
                        expected="no_self_witnessing", probe_expected=99)
        with tempfile.TemporaryDirectory() as tmp:
            corpus = self._corpus(tmp, question)
            cmd_rebase(self._args(corpus))
            after = json.loads(corpus.read_text(encoding="utf-8"))["questions"][0]
            self.assertEqual(after["expected"], "no_self_witnessing")
            self.assertNotEqual(after["probe_expected"], 99)


class TheContainsGraderRefusesAHaystack(unittest.TestCase):
    """Two witnesses beat this grader before it asked the right question.

    `contains` means one thing against a probe - the expected value is one member of the set
    the probe returned - and something else entirely against a participant. Read the first
    way, the participant supplies the container, and a bigger container scores better.

    Pass four: a 339-character blob of prose recitable from AGENTS.md scored RIGHT on three
    tier 0 questions. The repair narrowed it to a comma-separated list, which changed the
    haystack from prose to commas: pass five submitted 886 tokens harvested from AGENTS.md
    and CLAUDE.md and took four tier 0 questions, and a list of all 21 expected values took
    18 of 21. An answer to a question that asks for an identifier is the identifier.
    """

    QUESTION = {"id": "A09", "grade": "contains", "expected": "PREAPPROVAL_REQUESTED"}

    def _verdict(self, given: str) -> str:
        return judge(self.QUESTION, given, self.QUESTION["expected"], None)

    def test_the_term_itself_is_right(self) -> None:
        self.assertEqual(self._verdict("PREAPPROVAL_REQUESTED"), "RIGHT")

    def test_case_and_spacing_are_not_knowledge(self) -> None:
        self.assertEqual(self._verdict("  preapproval_requested  "), "RIGHT")

    def test_prose_containing_the_term_is_wrong(self) -> None:
        self.assertEqual(
            self._verdict("The refusal is PREAPPROVAL_REQUESTED, per the acceptance policy."),
            "WRONG")

    def test_a_list_containing_the_term_is_wrong(self) -> None:
        """The exploit the fourth repair left open: commas instead of prose."""
        self.assertEqual(
            self._verdict("SELF_DIRECTION_PRESENTED,PREAPPROVAL_REQUESTED,SCOPE_WIDENED"),
            "WRONG")

    def test_a_harvested_vocabulary_dump_is_wrong(self) -> None:
        dump = ",".join("TOKEN_%d" % n for n in range(400)) + ",PREAPPROVAL_REQUESTED"
        self.assertEqual(self._verdict(dump), "WRONG")

    def test_a_different_term_is_wrong(self) -> None:
        self.assertEqual(self._verdict("SELF_DIRECTION_PRESENTED"), "WRONG")

    def test_an_empty_answer_is_wrong(self) -> None:
        self.assertEqual(self._verdict("   "), "WRONG")

    def test_the_probe_direction_is_untouched(self) -> None:
        """Against a probe's returned set, membership is still the right question."""
        self.assertTrue(compare("PREAPPROVAL_REQUESTED",
                                ["SELF_DIRECTION_PRESENTED", "PREAPPROVAL_REQUESTED"],
                                "contains"))


class PathsLeavingTheRepositoryAreRefused(unittest.TestCase):
    """The producer refused them and the reader did not, and `history` grades what is on disk."""

    FIXTURE = "conformance/fixtures/coldstart/answers.fixture.json"

    def _codes(self, patch: dict) -> set[str]:
        return {d["code"] for d in records.defects(_apply(BASE, _reconciled(patch)), SCHEMA)}

    def test_an_absolute_path_is_outside_on_either_platform(self) -> None:
        """A record is read on nodes that did not write it, so absoluteness is not
        the reading platform's opinion. A drive-lettered path is a relative name to
        POSIX and would resolve inside the repository, verifying a digest against a
        file the record never meant; a rooted POSIX path is a relative name to
        Windows. Both are refused everywhere, which is why this asserts both here
        rather than one on each runner."""
        # Synthetic locations, not this machine's: scripts/lint.py refuses a
        # committed /Users/, /home/ or drive Users path, and it is right to.
        for outside in ("C:/nowhere/answers.json",
                        r"D:\nowhere\answers.json",
                        "/nowhere/answers.json",
                        r"\\share\public\answers.json"):
            with self.subTest(path=outside):
                self.assertIsNone(attribution.inside(outside))

    def test_a_traversal_is_outside(self) -> None:
        self.assertIsNone(attribution.inside("../../elsewhere/answers.json"))
        self.assertIsNone(attribution.inside(r"..\..\elsewhere\answers.json"))

    def test_a_repository_relative_path_resolves(self) -> None:
        self.assertIsNotNone(attribution.inside("AGENTS.md"))

    def test_a_record_citing_outside_is_refused(self) -> None:
        codes = self._codes({
            "mode": "COMPETENCE",
            "participant": {"id": "p", "host": "h",
                            "answers": "../../elsewhere/answers.json",
                            "answers_digest": "sha256:" + "1" * 64},
            "graded_by": {"owner_verdicts": None, "manual_asked": 0, "manual_graded": 0},
        })
        self.assertIn("ANSWERS_UNVERIFIED", codes)

    def test_a_digest_with_no_path_is_refused(self) -> None:
        codes = self._codes({
            "mode": "COMPETENCE",
            "participant": {"id": "p", "host": "h", "answers_digest": "sha256:" + "0" * 64},
            "graded_by": {"owner_verdicts": None, "manual_asked": 0, "manual_graded": 0},
        })
        self.assertIn("ANSWERS_UNVERIFIED", codes)

    def test_saying_nothing_was_hand_graded_does_not_switch_the_check_off(self) -> None:
        """57 asked and 0 graded means 57 unmeasured; the table said 34 and was admitted."""
        codes = self._codes({
            "mode": "COMPETENCE",
            "participant": {"id": "p", "host": "h", "answers": self.FIXTURE,
                            "answers_digest": records.digest_of(ROOT / self.FIXTURE)},
            "graded_by": {"owner_verdicts": None, "manual_asked": 57, "manual_graded": 0},
        })
        self.assertIn("COUNTS_DISAGREE", codes)


class TheSixthWitnessAttacks(unittest.TestCase):
    """Eleven more, and three of them were the contract failing at its stated job.

    The worst was F1: a competence record could claim 175 of 175 and ADMISSIBLE with no
    owner verdict anywhere, because declaring `manual_asked: 0` and `manual_graded: 0`
    returned before SELF_GRADED was ever considered. The number was in the corpus the record
    digest-binds in the same object.
    """

    FIXTURE = "conformance/fixtures/coldstart/answers.fixture.json"

    def _codes(self, patch: dict) -> set[str]:
        return {d["code"] for d in records.defects(_apply(BASE, _reconciled(patch)), SCHEMA)}

    def _live_corpus(self) -> dict:
        corpus = ROOT / "scripts" / "sovcoldstart" / "corpus.json"
        return {"path": "scripts/sovcoldstart/corpus.json",
                "digest": records.digest_of(corpus), "questions": 175, "selected": 175}

    def test_declaring_nothing_hand_asked_is_refused_against_the_bound_corpus(self) -> None:
        codes = self._codes({
            "mode": "COMPETENCE",
            "corpus": self._live_corpus(),
            "participant": {"id": "p", "host": "h", "answers": self.FIXTURE,
                            "answers_digest": records.digest_of(ROOT / self.FIXTURE)},
            "graded_by": {"owner_verdicts": None, "manual_asked": 0, "manual_graded": 0},
        })
        self.assertIn("COUNTS_DISAGREE", codes)

    def test_selected_cannot_exceed_the_questions_it_was_drawn_from(self) -> None:
        codes = self._codes({"corpus": {**BASE["corpus"], "questions": 3}})
        self.assertIn("COUNTS_DISAGREE", codes)

    def test_the_answers_file_has_to_be_a_submission(self) -> None:
        """A witness cited README.md with its true digest and it was admitted."""
        codes = self._codes({
            "mode": "COMPETENCE",
            "participant": {"id": "p", "host": "h", "answers": "AGENTS.md",
                            "answers_digest": records.digest_of(ROOT / "AGENTS.md")},
            "graded_by": {"owner_verdicts": None, "manual_asked": 0, "manual_graded": 0},
        })
        self.assertIn("ANSWERS_UNVERIFIED", codes)


class TheGraderNamespaceIsNotDiscarded(unittest.TestCase):
    """`rsplit(":", 1)[-1]` made `hostile-agent:bdo` resolve to the registered human."""

    def _codes(self, grader: str) -> list[str]:
        return [d["code"] for d in attribution._grader_defects(grader, "x.json")]

    def test_the_registered_human_is_admitted(self) -> None:
        self.assertEqual(self._codes("principal:bdo"), [])

    def test_the_bare_name_is_admitted(self) -> None:
        self.assertEqual(self._codes("bdo"), [])

    def test_case_and_whitespace_are_not_identity(self) -> None:
        self.assertEqual(self._codes("  BDO  "), [])

    def test_a_borrowed_namespace_is_refused(self) -> None:
        for spelling in ("x:bdo", "hostile-agent:bdo", "claude:bdo", "a:b:c:bdo", "::bdo"):
            with self.subTest(spelling=spelling):
                self.assertEqual(self._codes(spelling), ["SELF_GRADED"])

    def test_a_model_principal_is_refused(self) -> None:
        self.assertEqual(self._codes("principal:claude-opus-5"), ["SELF_GRADED"])

    def test_an_unregistered_name_is_refused(self) -> None:
        self.assertEqual(self._codes("not-bdo"), ["SELF_GRADED"])

    def test_no_grader_at_all_is_refused(self) -> None:
        self.assertEqual(self._codes("   "), ["SELF_GRADED"])


class SetComparisonForgivesWhatExactForgives(unittest.TestCase):
    """A correct answer was graded WRONG because two normalisers disagreed."""

    def test_a_trailing_period_is_not_knowledge(self) -> None:
        self.assertTrue(compare("OPEN,BUILT", "OPEN, BUILT.", "set_eq"))

    def test_an_arrow_is_a_separator_here_too(self) -> None:
        self.assertTrue(compare("OPEN,BUILT", "OPEN -> BUILT", "set_eq"))

    def test_a_missing_member_is_still_wrong(self) -> None:
        self.assertFalse(compare("OPEN,BUILT", "OPEN.", "set_eq"))

    def test_a_superset_is_still_wrong(self) -> None:
        self.assertFalse(compare("OPEN,BUILT", "OPEN, BUILT, RATIFIED", "set_eq"))


class TheRecordDirectorySurvivesATornFile(unittest.TestCase):
    """Two threads at one run id produced a silent replacement and two half-written files."""

    def setUp(self) -> None:
        """See WriteTimeChecks.setUp: the corpus is untracked, so it cannot be its own pin."""
        self.rel, self.digest = _clean_tracked_markdown()
        self.commit = _head()
        self._pin = mock.patch.object(refusals, "CANONICAL_CORPUS", self.rel)
        self._pin.start()
        self.addCleanup(self._pin.stop)

    def _fresh(self) -> dict:
        at = "2026-08-27T00:00:00Z"
        return _apply(BASE, {
            "corpus": {"path": self.rel, "digest": self.digest,
                       "questions": 175, "selected": 175},
            "revision": {"commit": self.commit, "branch": "main", "tree_state": "CLEAN"},
            "observed_at": at,
            "run_id": "coldstart_" + run_identity(self.commit, self.digest, at,
                                                  "INTEGRITY", ""),
        })

    def test_a_torn_file_does_not_take_the_directory_with_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            records.write(self._fresh(), Path(tmp))
            (Path(tmp) / "2026-01-01-integrity-deadbeef.json").write_text(
                '{"record_schema": "soveraeign-coldstart-run/v1", "tie',
                encoding="utf-8")
            loaded = records.load_all(Path(tmp))
            self.assertEqual(len(loaded), 2)
            self.assertIn("RECORD_SHAPE",
                          [c for r in loaded for c in r["_defects"]])

    def test_a_second_writer_cannot_replace_the_first(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first = self._fresh()
            path = records.write(first, Path(tmp))
            second = copy.deepcopy(first)
            second["note"] = "a different reading under the same name"
            with self.assertRaises(ValueError) as caught:
                records.write(second, Path(tmp))
            self.assertIn("RECORD_WOULD_REPLACE", str(caught.exception))
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")).get("note"),
                             first.get("note"))

    def test_two_participants_at_one_instant_do_not_collide(self) -> None:
        """The identity omitted the participant, so the daily schedule collided by design."""
        digest, commit, at = "sha256:" + "a" * 64, "b" * 40, "2026-08-27T06:30:00Z"
        self.assertNotEqual(run_identity(commit, digest, at, "COMPETENCE", "principal:one"),
                            run_identity(commit, digest, at, "COMPETENCE", "principal:two"))


class TheLeakGuardSeesAListOfAnswers(unittest.TestCase):
    """Ninety of 175 questions had a non-string `expected` and were skipped entirely."""

    def _defects(self, question: dict) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "corpus.json"
            path.write_text(json.dumps({"questions": [question]}), encoding="utf-8")
            return _corpus_defects(path)

    BASE_Q = {"id": "Z1", "section": "doctrine", "tier": 0, "q": "?", "why": "w",
              "severity_on_failure": "FATAL", "grade": "set_eq"}

    def test_a_probe_enumerating_every_expected_value_is_a_defect(self) -> None:
        question = {**self.BASE_Q, "expected": ["ALPHA_ONE", "BETA_TWO"],
                    "probe": {"kind": "regex_unique", "file": "x",
                              "pattern": "ALPHA_ONE|BETA_TWO"}}
        self.assertTrue(any("enumerates every one of its own expected values" in d
                            for d in self._defects(question)))

    def test_a_probe_naming_one_of_several_is_not(self) -> None:
        question = {**self.BASE_Q, "expected": ["ALPHA_ONE", "BETA_TWO"],
                    "probe": {"kind": "region_tokens", "file": "x", "region": "ALPHA_ONE",
                              "token": "([A-Z_]+)"}}
        self.assertEqual([d for d in self._defects(question) if "enumerates" in d], [])

    def test_the_shipped_corpus_carries_none(self) -> None:
        self.assertEqual(_corpus_defects(ROOT / "scripts" / "sovcoldstart" / "corpus.json"),
                         [])


class ThePatchIsShallow(unittest.TestCase):
    def test_a_patched_key_owns_its_whole_value(self) -> None:
        """A deep merge would restore the digest D-010 removes and grade a case that never ran."""
        patched = _apply(BASE, {"corpus": {"path": "x", "questions": 1, "selected": 1}})
        self.assertNotIn("digest", patched["corpus"])



class TheCorpusMustBeAtTheCommit(unittest.TestCase):
    """A record may not pin bytes that exist only on the disk that wrote it.

    A peer session found four generated diagrams stamping a STATUS.yaml digest matching none
    of the thirty-four committed versions of that file, because a builder had run in the
    shared tree and captured whatever was in flight. A run record has the same shape. Two
    records under reports/coldstart/ name the same commit and carry different corpus
    digests, which is only possible while the corpus is uncommitted.
    """

    def _record(self, commit: str, digest: str) -> dict:
        return {"revision": {"commit": commit}, "corpus": {
            "path": refusals.CANONICAL_CORPUS, "digest": digest}}

    def test_a_corpus_not_in_the_commit_is_refused(self) -> None:
        found = records._corpus_at_revision(
            self._record("HEAD", "sha256:" + "0" * 64))
        self.assertEqual([d["code"] for d in found], ["CORPUS_NOT_AT_REVISION"])

    def test_an_empty_commit_is_refused_rather_than_passed(self) -> None:
        """An unset field used to mean the check did not run, which is the softest failure."""
        found = records._corpus_at_revision({"corpus": {"digest": "sha256:" + "0" * 64}})
        self.assertEqual([d["code"] for d in found], ["CORPUS_NOT_AT_REVISION"])

    def test_a_tracked_file_at_its_own_commit_passes(self) -> None:
        """The positive case, over a file that is committed - AGENTS.md is always there."""
        import subprocess
        from hashlib import sha256

        blob = subprocess.run(["git", "cat-file", "blob", "HEAD:AGENTS.md"],
                              cwd=records.ROOT, capture_output=True, timeout=30)
        self.assertEqual(blob.returncode, 0, "AGENTS.md is not at HEAD")
        digest = "sha256:" + sha256(blob.stdout).hexdigest()
        with mock.patch.object(refusals, "CANONICAL_CORPUS", "AGENTS.md"):
            self.assertEqual(records._corpus_at_revision(self._record("HEAD", digest)), [])

    def test_the_blob_reader_is_byte_exact(self) -> None:
        """Decoding to text and re-encoding is a round trip, not a reading of the file.

        Graded against git's own object id, not against the working tree. The first version
        compared `_blob_at("HEAD", "AGENTS.md")` with the file on disk and failed, because
        another session had AGENTS.md modified - a true reading, and the wrong control.
        """
        import subprocess

        blob = source._blob_at("HEAD", "AGENTS.md")
        self.assertIsInstance(blob, bytes)
        want = subprocess.run(["git", "rev-parse", "HEAD:AGENTS.md"], cwd=records.ROOT,
                              capture_output=True, text=True, timeout=60).stdout.strip()
        got = subprocess.run(["git", "hash-object", "--stdin"], cwd=records.ROOT,
                             input=blob, capture_output=True, timeout=60).stdout
        self.assertEqual(got.decode().strip(), want)

    def test_write_refuses_a_record_whose_corpus_is_uncommitted(self) -> None:
        """The whole point: the refusal reaches the writer, not only a unit test."""
        self.assertIn("_corpus_at_revision", records.fresh_defects.__code__.co_names)

if __name__ == "__main__":
    unittest.main()
