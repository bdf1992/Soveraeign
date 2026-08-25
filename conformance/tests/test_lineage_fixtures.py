"""Integrity checks for the lineage fixture corpora (CONF-HIST-3).

Prove that the two corpora under conformance/fixtures/lineage/ are well-formed
and genuinely defeating without importing any participant implementation code.
The repository secret oracle in scripts/lint.py is reused by loading it from
its file location (the test_oracle.py bootstrap pattern) rather than growing a
second secret oracle; scripts/lint.py is repository tooling, not participant
code, so loading it does not cross the /conformance boundary, which forbids
services/, bindings/, adapters/, and workers/. Contaminants are committed only
as split parts; this module joins them in memory only and never writes a
joined contaminant to disk.
"""

from __future__ import annotations

from pathlib import Path
import importlib.util
import json
import unittest


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "conformance" / "fixtures" / "lineage"
CORPUS_PATHS = {
    "reader": FIXTURES / "reader-cases.json",
    "lesson": FIXTURES / "lesson-cases.json",
}
# The defect label lint.py emits for its unnamed LOCAL_PATH_PATTERNS tuple; a
# path contaminant claims this class because those patterns carry no dict key.
LOCAL_PATH_CLASS = "local absolute user path"

SPEC = importlib.util.spec_from_file_location("repository_lint", ROOT / "scripts" / "lint.py")
assert SPEC and SPEC.loader
lint = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lint)


def load_corpus(name: str) -> dict:
    """Parse one committed corpus strictly; a parse failure is a corpus defect."""
    return json.loads(CORPUS_PATHS[name].read_text(encoding="utf-8"))


def defeating_reader_cases(corpus: dict) -> list[dict]:
    return [case for case in corpus["cases"] if case["expect"] == "LOSSY"]


def defeating_lesson_cases(corpus: dict) -> list[dict]:
    return [case for case in corpus["cases"] if case["expect"] == "REFUSED"]


class LineageCorpusIntegrityTests(unittest.TestCase):
    def test_both_corpora_parse_with_an_id_and_cases(self):
        for name in CORPUS_PATHS:
            corpus = load_corpus(name)
            self.assertTrue(corpus.get("corpus_id"), name)
            self.assertIsInstance(corpus["cases"], list, name)
            self.assertTrue(corpus["cases"], name)

    def test_case_ids_are_unique(self):
        case_ids = [
            case["case_id"] for name in CORPUS_PATHS for case in load_corpus(name)["cases"]
        ]
        self.assertTrue(all(isinstance(case_id, str) and case_id for case_id in case_ids))
        self.assertEqual(len(case_ids), len(set(case_ids)), case_ids)

    def test_each_corpus_carries_positive_and_defeating_cases(self):
        reader_expects = {case["expect"] for case in load_corpus("reader")["cases"]}
        self.assertLessEqual(reader_expects, {"EXACT", "LOSSY"})
        self.assertEqual(reader_expects, {"EXACT", "LOSSY"})
        lesson_expects = {case["expect"] for case in load_corpus("lesson")["cases"]}
        self.assertLessEqual(lesson_expects, {"VALID", "REFUSED"})
        self.assertEqual(lesson_expects, {"VALID", "REFUSED"})

    def test_defeating_reader_cases_split_every_contaminant(self):
        for case in defeating_reader_cases(load_corpus("reader")):
            self.assertTrue(case["contaminants"], case["case_id"])
            for contaminant in case["contaminants"]:
                parts = contaminant["parts"]
                label = f"{case['case_id']}/{contaminant['contaminant_id']}"
                self.assertIsInstance(parts, list, label)
                # Genuinely split: no committed byte run may hold the joined form.
                self.assertGreaterEqual(len(parts), 2, label)
                self.assertTrue(
                    all(isinstance(part, str) and part for part in parts), label
                )

    def test_defeating_lesson_cases_name_their_refusal_substring(self):
        for case in defeating_lesson_cases(load_corpus("lesson")):
            refuses = case.get("refuses")
            self.assertIsInstance(refuses, str, case["case_id"])
            self.assertTrue(refuses.strip(), case["case_id"])

    def test_planted_contaminants_occur_in_their_joined_input(self):
        # Drift guard at the corpus level: a defeating case whose contaminant
        # never occurs in its own input would not be genuinely defeating.
        for case in defeating_reader_cases(load_corpus("reader")):
            joined_input = "".join(case["input_parts"])
            for contaminant in case["contaminants"]:
                joined = "".join(contaminant["parts"])
                label = f"{case['case_id']}/{contaminant['contaminant_id']}"
                self.assertIn(joined, joined_input, label)

    def test_joined_contaminants_match_the_lint_shape_they_claim(self):
        # The planted defeat is real, not vacuous: every key or path
        # contaminant's joined form trips the exact lint shape it names.
        matched = 0
        for case in defeating_reader_cases(load_corpus("reader")):
            for contaminant in case["contaminants"]:
                lint_class = contaminant["lint_class"]
                if lint_class is None:
                    continue  # Owned by pii-v1; lint.py has no email shape.
                joined = "".join(contaminant["parts"])
                label = f"{case['case_id']}/{contaminant['contaminant_id']}"
                if lint_class in lint.SECRET_PATTERNS:
                    self.assertIsNotNone(
                        lint.SECRET_PATTERNS[lint_class].search(joined), label
                    )
                elif lint_class == LOCAL_PATH_CLASS:
                    self.assertTrue(
                        any(p.search(joined) for p in lint.LOCAL_PATH_PATTERNS), label
                    )
                else:
                    self.fail(f"{label}: unknown lint_class {lint_class!r}")
                matched += 1
        self.assertGreaterEqual(matched, 1)

    def test_committed_corpus_bytes_stay_lint_clean(self):
        # The split-parts scheme is only honest if no pattern matches the raw
        # committed fixture bytes.
        for name, path in CORPUS_PATHS.items():
            text = path.read_bytes().decode("utf-8")
            for shape, pattern in lint.SECRET_PATTERNS.items():
                self.assertIsNone(pattern.search(text), f"{name}: {shape}")
            for pattern in lint.LOCAL_PATH_PATTERNS:
                self.assertIsNone(pattern.search(text), f"{name}: {pattern.pattern}")


if __name__ == "__main__":
    unittest.main()
