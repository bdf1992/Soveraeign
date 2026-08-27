"""Grade the glob matcher against git, not against what it was meant to do.

`_pinned_glob` exists because `git ls-files` reads the index rather than a commit, so every
probe that used it reached around `pin()` and could answer for a different tree than its
neighbours - the failure trap T6 names. Replacing it meant writing `:(glob)` semantics by
hand, and the first attempt delegated to `PurePosixPath.match`, which is not those
semantics: it treats `**` as one non-crossing `*` and matches from the right rather than
from the repository root.

Nobody noticed until a fifth witness compared it to git. Corpus question C07 asks how many
files sit under `reports/` and the matcher answered 23 where git answers 47, so that
question reported drift about the world in every run, and a rebase would have written the
matcher's error into the answer key as the truth.

So these cases do not assert counts. They ask git the same question and compare, which is
the only check that can catch an independently written matcher being confidently wrong.
"""

from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovcoldstart.probes import _glob_regex, _pinned_glob, pin  # noqa: E402
from sovcoldstart.source import tracked_paths  # noqa: E402

#: The grammar, not the corpus. A sixth witness pointed out that grading only the patterns
#: the corpus uses today reads a declaration where the matcher's own grammar could be
#: enumerated: it had seven disagreements with git, none of them in a shipped pattern, and
#: one raised `re.error` out of the probe loop rather than recording ERROR.
SHAPES = (
    # plain segments and single stars
    "decisions/*.md", "scripts/*.py", "contracts/*.json", "*.md", "AGENTS.md",
    "services/*/contracts/service.json", "conformance/fixtures/*/*.json",
    # double stars, in every position
    "reports/**/*", "services/**", "scripts/**/*.py", "**/*.md", "**", "a/**/b",
    # directory prefixes and empty patterns, which git reads as whole subtrees
    "reports/", "a/", "scripts/sovcoldstart/", "",
    # normalisation
    "./decisions/*.md", ".//decisions/*.md", "a//x.py", "  decisions/*.md  ",
    # `/` alone is not in this list: git refuses it as outside the repository,
    # so there is no answer to compare against.
    # bracket expressions, including the awkward ones
    "decisions/[0-9][0-9][0-9][0-9]*.md", "decisions/[!0]*.md", "br[ack].md",
    "d[!]0].md", "[[:digit:]]", "decisions/[]]*.md", "decisions/[0-9.md",
    "decisions/[^0]*.md",
    # question marks and literals that look like regex
    "decisions/00??-*.md", "contracts/*.json", "scripts/sov_coldstart.py",
    "a.b/c.d", "no+such|file.md", "(paren).md",
    # patterns that match nothing
    "nowhere/at/all/*.txt", "decisions/*.md/deeper",
    # wildcard directory prefixes: git matches nothing, because a wildcard segment before
    # the slash names no directory. Generalising the literal-prefix rule to these matched
    # the whole tree.
    "**/", "*/", "scripts/**/", "reports/*/",
    # `.` as an interior segment
    "scripts/./lint.py", "./scripts/./sovcoldstart/./probes.py",
)


def _git(args: list[str]) -> str:
    done = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                          check=False)
    if done.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {done.stderr.strip()}")
    return done.stdout


def _corpus_patterns() -> list[str]:
    doc = json.loads((ROOT / "scripts" / "sovcoldstart" / "corpus.json")
                     .read_text(encoding="utf-8"))
    out = set()
    for question in doc["questions"]:
        spec = question.get("probe")
        if isinstance(spec, dict) and isinstance(spec.get("pattern"), str):
            if spec.get("kind") in ("glob_count", "git_ls_count", "number_gaps"):
                out.add(spec["pattern"])
    return sorted(out)


class TheMatcherAgreesWithGit(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.commit = pin()
        cls.tree = set(tracked_paths())

    def _git_glob(self, pattern: str) -> set[str]:
        """What git matches for this pathspec over the same commit."""
        listed = _git(["ls-files", f"--with-tree={self.commit}", "--", f":(glob){pattern}"])
        return {line for line in listed.splitlines() if line.strip()} & self.tree

    def test_every_declared_shape_matches_git(self) -> None:
        for pattern in SHAPES:
            with self.subTest(pattern=pattern):
                self.assertEqual(set(_pinned_glob(pattern)), self._git_glob(pattern))

    def test_no_pattern_in_the_grammar_raises(self) -> None:
        """`re.error` is not a ValueError, so a bad class raised out of the probe loop."""
        for pattern in SHAPES + ("[", "]", "[]", "[!", "*[", "a[b"):
            with self.subTest(pattern=pattern):
                _glob_regex(pattern)

    def test_a_backslash_is_refused_rather_than_guessed(self) -> None:
        """git on Windows and git on Linux disagree, so no count from one is comparable."""
        from sovcoldstart.source import ProbeError

        with self.assertRaises(ProbeError):
            _glob_regex("AGENTS\.md")

    def test_every_pattern_the_corpus_uses_matches_git(self) -> None:
        patterns = _corpus_patterns()
        self.assertGreater(len(patterns), 5, "the corpus should carry several glob probes")
        for pattern in patterns:
            with self.subTest(pattern=pattern):
                self.assertEqual(set(_pinned_glob(pattern)), self._git_glob(pattern))


class TheSemanticsAreTheOnesGitMeans(unittest.TestCase):
    """Stated directly, so a reader can see the rule without running git."""

    def test_a_single_star_does_not_cross_a_slash(self) -> None:
        matcher = _glob_regex("scripts/*.py")
        self.assertTrue(matcher.match("scripts/lint.py"))
        self.assertFalse(matcher.match("scripts/sovcoldstart/probes.py"))

    def test_a_double_star_crosses_slashes(self) -> None:
        matcher = _glob_regex("scripts/**/*.py")
        self.assertTrue(matcher.match("scripts/sovcoldstart/probes.py"))
        self.assertTrue(matcher.match("scripts/lint.py"), "`**` matches zero segments too")

    def test_a_trailing_double_star_takes_everything_below(self) -> None:
        matcher = _glob_regex("services/**")
        self.assertTrue(matcher.match("services/asset/contracts/service.json"))
        self.assertFalse(matcher.match("scripts/lint.py"))

    def test_matching_is_anchored_at_the_repository_root(self) -> None:
        """PurePosixPath.match matches from the right, which this must not do."""
        matcher = _glob_regex("decisions/*.md")
        self.assertTrue(matcher.match("decisions/0001-founding.md"))
        self.assertFalse(matcher.match("vendor/decisions/0001-founding.md"))

    def test_a_leading_dot_slash_is_the_same_pattern(self) -> None:
        self.assertEqual(_glob_regex("./decisions/*.md").pattern,
                         _glob_regex("decisions/*.md").pattern)

    def test_a_question_mark_is_one_character_and_not_a_slash(self) -> None:
        matcher = _glob_regex("decisions/00??-*.md")
        self.assertTrue(matcher.match("decisions/0078-a.md"))
        self.assertFalse(matcher.match("decisions/0/78-a.md"))

    def test_a_dot_in_a_pattern_is_a_literal_dot(self) -> None:
        matcher = _glob_regex("contracts/*.json")
        self.assertTrue(matcher.match("contracts/principals.json"))
        self.assertFalse(matcher.match("contracts/principalsXjson"))


if __name__ == "__main__":
    unittest.main()
