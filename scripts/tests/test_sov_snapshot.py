"""Tests for the orientation snapshot check.

The module had none. It was split into `sov_snapshot.py` and `sovsnapshot/`
without one, which doubled the surface and left the seam unexercised — and a
witness then showed that `claims.Underivable`, named twice across that seam, is
reached only when a source fails. Misspelling it passes every gate on this
machine and raises `AttributeError` in CI, which is where the failing sources
are. That is the third time in one day a split left a caller behind, so the walk
that catches it lives here rather than in another concern's test file.
"""

from __future__ import annotations

from pathlib import Path
import ast
import builtins
import dataclasses
import importlib
import re
import subprocess
import sys
import tempfile
import types
import unittest
import unittest.mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_snapshot  # noqa: E402
from sovsnapshot import claims  # noqa: E402
from sovsnapshot import grading  # noqa: E402
from sovsnapshot import selfcheck  # noqa: E402


class EveryReferenceResolves(unittest.TestCase):
    """A name used only on a failure path still has to exist.

    `except claims.Underivable` runs when a source cannot answer, and no source
    fails on a developer machine. So a typo there is invisible to lint, to the
    selfcheck, to `verify.py`, and to every gate — and fires in CI, where the
    shallow checkout makes a source fail.
    """

    @staticmethod
    def modules() -> list[types.ModuleType]:
        """Derived, not listed, so the next split extends coverage by existing."""
        names = ["sov_snapshot"]
        for path in sorted((ROOT / "scripts" / "sovsnapshot").glob("*.py")):
            if path.stem != "__init__":
                names.append(f"sovsnapshot.{path.stem}")
        return [importlib.import_module(name) for name in names]

    def test_every_module_attribute_a_caller_names_exists(self):
        missing = []
        for module in self.modules():
            source = Path(module.__file__).read_text(encoding="utf-8")
            parsed = ast.parse(source)
            local = {n.asname or n.name.split(".")[-1]
                     for node in ast.walk(parsed)
                     if isinstance(node, (ast.Import, ast.ImportFrom))
                     for n in node.names}
            for node in ast.walk(parsed):
                if not isinstance(node, ast.Attribute) or not isinstance(node.value, ast.Name):
                    continue
                if node.value.id not in local:
                    continue
                target = getattr(module, node.value.id, None)
                if not isinstance(target, types.ModuleType):
                    continue
                if not hasattr(target, node.attr):
                    missing.append(f"{module.__name__}: {node.value.id}.{node.attr}")
        self.assertEqual(missing, [], "module attributes named but not defined")

    def test_no_bare_call_is_undefined(self):
        missing = []
        for module in self.modules():
            parsed = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
            known = {n.name for n in ast.walk(parsed)
                     if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
            known |= {n.asname or n.name.split(".")[0] for node in ast.walk(parsed)
                      if isinstance(node, (ast.Import, ast.ImportFrom)) for n in node.names}
            known |= set(dir(builtins))
            for node in ast.walk(parsed):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    if node.func.id not in known:
                        missing.append(f"{module.__name__}: {node.func.id}()")
        self.assertEqual(missing, [], "names called but neither defined nor imported")


class UnanswerableIsNotDrift(unittest.TestCase):
    """A claim this environment cannot derive says nothing about the page.

    The defect: a shallow checkout cannot count commits, and reporting that as
    drift failed `verify.py` in CI — the one environment where AGENTS.md makes it
    the required command — against a page that was correct.
    """

    def _grade(self, page: str, derived: dict) -> list:
        return grading.grade(page, derived)

    def test_an_underivable_claim_is_reported_but_does_not_fail(self):
        every = {claim.name: 5 for claim in claims.CLAIMS}
        without = {k: v for k, v in every.items() if k != "commits"}
        findings = self._grade(selfcheck.page(**every).text, without)
        kinds = {f.claim: f.kind for f in findings}
        self.assertEqual(kinds.get("commits"), grading.UNANSWERABLE)
        self.assertEqual(grading.drift(findings), [])

    def test_a_real_drift_alongside_an_underivable_claim_still_fails(self):
        """The control: refusing to fail on one must not silence the others."""
        every = {claim.name: 5 for claim in claims.CLAIMS}
        without = {k: 900 for k, v in every.items() if k != "commits"}
        drifted = grading.drift(
            self._grade(selfcheck.page(**every).text, without))
        self.assertEqual(len(drifted), len(claims.CLAIMS) - 1)


class TheSyntheticPageStatesEveryClaim(unittest.TestCase):
    """A page that states fewer claims than asked is how a selfcheck tests nothing."""

    def test_a_partial_call_still_states_all_of_them(self):
        page = selfcheck.page(commits=1).text
        for claim in claims.CLAIMS:
            with self.subTest(claim=claim.name):
                self.assertTrue(grading.read_claim(page, claim), claim.name)

    def test_shifting_moves_claims_that_were_never_derived(self):
        """Otherwise an underivable claim holds the placeholder on both sides."""
        shifted = selfcheck.shift({"commits": 10}, 7)
        self.assertEqual(shifted["commits"], 17)
        self.assertEqual(shifted["reports"], selfcheck.PLACEHOLDER + 7)


class TheExitCodeIsWhatFailedCI(unittest.TestCase):
    """The repair that mattered was `cmd_check` returning 0 on an unanswerable claim.

    Two rounds of it were tested only one layer down, on `grade`, while the exit
    code is what failed `verify.py` across three workflows against a correct page.
    A witness pointed out the regression had no test at the level it broke.
    """

    @staticmethod
    def _refuse():
        raise claims.Underivable("planted: this environment cannot answer")

    @staticmethod
    def _patched(**replacements):
        """CLAIMS with some derivations replaced. `Claim` is frozen, so rebuild it."""
        rebuilt = tuple(
            dataclasses.replace(claim, derive=replacements[claim.name])
            if claim.name in replacements else claim
            for claim in claims.CLAIMS)
        return unittest.mock.patch.object(claims, "CLAIMS", rebuilt)

    def test_check_exits_zero_when_a_claim_cannot_be_derived(self):
        with self._patched(commits=self._refuse):
            self.assertEqual(sov_snapshot.cmd_check(None), 0)

    def test_check_still_exits_one_on_a_real_drift(self):
        """The control: refusing to fail on the unanswerable must not mute the rest."""
        with self._patched(commits=self._refuse,
                           **{"verification checks": lambda: 999999}):
            self.assertEqual(sov_snapshot.cmd_check(None), 1)




class RenamingAClaimIsCaught(unittest.TestCase):
    """`page` addresses its slots by name, which a reference walk cannot see.

    The guard used to be `raise SystemExit` at import, which no test could ever
    fail: the mismatch made the module unimportable, so the test module could not
    load to run. A library that raises at import also decides the exit code of
    every importer, including the reference walk below that loads the package.
    """

    def test_the_page_slots_match_the_declared_claims(self):
        self.assertIsNone(selfcheck.slots_match_claims())

    def test_a_renamed_claim_makes_the_selfcheck_fail_rather_than_die(self):
        renamed = ("verification checks", "declared operations", "commits",
                   "decision records", "dispatches")
        with unittest.mock.patch.object(selfcheck, "PAGE_SLOTS", renamed):
            self.assertIsNotNone(selfcheck.slots_match_claims())
            self.assertEqual(selfcheck.run(), 1)


class EveryNumberOnThePageIsClassified(unittest.TestCase):
    """A count on the page is checked, or it is named as unchecked. Not neither.

    `UNCHECKED` was written from what someone remembered rather than from the page.
    A witness read every number against the claim table and found three that were
    neither claimed nor listed - two of them stale while the check printed PASS,
    which is L-0001 recurring inside the gate built to stop it.

    So the inversion is executable. A number added anywhere on the page fails this
    until it is made a claim or classified below with a reason, and the reason is
    tied to the section it was ruled in: the same figure means different things in
    the day-two paragraph and in the current snapshot.

    Two spellings are outside it and are stated rather than left to be discovered.
    A digit group joined by `-` to another token is read as a compound identifier,
    so `77-surface` escapes along with every date and version. And a number written
    as words escapes entirely; that is why the harness counts on the page were
    converted to digits rather than teaching this a word list.

    An independent witness planted ten spellings of one count against an earlier
    version that demanded digits, whitespace, then a letter: eight walked past.
    Eight of the ten are caught now, and the two above are the two that are not.
    """

    #: `(section heading, matched text) -> why it is not a claim`. Keyed by section
    #: because a value alone is position-blind: "8 reports" is the day-two count,
    #: and a witness planted a second "8 reports" in the live snapshot section that
    #: the unkeyed version waved through.
    CLASSIFIED = {
        ("Known traps", "0 does"): "an exit code in trap T2, not a count",
        ("Known traps", "404 while"): "an HTTP status in trap T4, not a count",
        ("Known traps", "404 has"): "trap T4 states it twice; the second is the same status",
        ("Repository snapshot (informational)", "1 Escalating"):
            "the ruling number in decisions/0033, an identifier",
        ("Where to look first", "1"): "the same ruling number in the table",
        ("Repository snapshot (informational)", "20 controlled"):
            "conformance cases, listed in claims.UNCHECKED",
        ("Historical orientation", "26 commits"): "day two, deliberately historical",
        ("Historical orientation", "17 decision"): "day two, deliberately historical",
        ("Historical orientation", "8 reports"): "day two, deliberately historical",
    }

    #: Nouns that are never counts anywhere. `12 s`, `3 s` are the graded wall-clock
    #: budget, already named in `claims.UNCHECKED`, and a timing is unchecked in
    #: whatever section it appears in - so this one is deliberately not keyed.
    CLASSIFIED_NOUNS = {"s": "wall-clock timings, listed in claims.UNCHECKED"}

    #: A standalone integer followed by a word. The lookbehind is what makes this
    #: whitespace-safe: an earlier version scrubbed ISO dates and decision filenames
    #: with contiguous-token regexes, and a decision reference wrapped across a line
    #: was reported as the unclassified count `0050-verification-budget-`. A digit
    #: inside a larger token is never a count, so it is excluded at the root rather
    #: than deleted beforehand.
    TOKEN = re.compile(r"(?<![\w./-])(\d+)\b")

    #: A digit group joined to another by `-` or `.` is one component of a compound
    #: identifier, not a count: `2026-08-25`, `5.1`, `0033-close-the-founding`. The
    #: lookbehind above already drops the trailing components; this drops the
    #: leading one. A rule about the shape, so a new date or version needs no entry
    #: in the table below - an earlier version deleted these with two scrubbing
    #: regexes and a witness broke both by wrapping a filename across a line.
    COMPOUND = re.compile(r"-|\.\d")

    #: How far past a number to look for the word that names it. `40 checks` is
    #: adjacent; `| 40 |` in a table and ``40 `services` `` are not, and an
    #: independent witness planted ten spellings of one count and watched eight
    #: walk past a pattern that demanded digits, whitespace, then a letter. The
    #: page's own style uses tables, backticks and parentheses, so the noun is
    #: found by skipping what is not a letter rather than by requiring a space.
    NOUN = re.compile(r"[^A-Za-z\n]{0,4}([A-Za-z][A-Za-z_.-]*)")

    @staticmethod
    def _prose_only(text: str) -> tuple[str, bool]:
        """The page with fenced blocks blanked, offsets preserved.

        A fenced block is an example, not a page claim - both for the headings it
        contains and the numbers. A witness planted a fenced markdown sample holding
        `## Historical orientation` just above a live count in the snapshot section:
        the count was waved through as historical, and the test failed naming an
        innocent line that had lost its own classification to the same shift. Loud,
        and pointing at the wrong line, which is worse than either alone.

        Same-length blanking rather than deletion, so every offset still lines up
        with the claim spans computed over the same string.
        """
        out, fenced = [], False
        for line in text.splitlines(keepends=True):
            blank = " " * (len(line.rstrip("\r\n"))) + line[len(line.rstrip("\r\n")):]
            if line.lstrip().startswith(("```", "~~~")):
                fenced = not fenced
                out.append(blank)
                continue
            out.append(blank if fenced else line)
        # The balance is returned rather than recomputed by the caller: an
        # unbalanced page is what makes the mask dangerous, and a second loop
        # applying the same toggle rule is how one reader of a fact gets updated
        # and its sibling does not.
        return "".join(out), not fenced

    @classmethod
    def _section_at(cls, text: str, position: int) -> str:
        """The `## ` heading the position sits under, or the preamble."""
        heading = ""
        for match in re.finditer(r"^## (.+)$", text, re.MULTILINE):
            if match.start() > position:
                break
            heading = match.group(1).strip()
        return heading

    def test_no_number_is_neither_claimed_nor_named_as_unchecked(self):
        raw = Path(claims.SNAPSHOT).read_text(encoding="utf-8")
        text, balanced = self._prose_only(raw)
        # An unpaired fence is a malformed page, not a mask instruction. This is the
        # general repair: the `eaten` guard below only proves no *claim* was
        # swallowed, and every claim lives in two sections, so one opening fence
        # anywhere below them blanks prose invisibly - measured at 26 lines hiding a
        # live plant that fails without the fence.
        self.assertTrue(balanced, "the page has an unpaired code fence, so masking "
                                  "would blank everything after it and this scan "
                                  "would pass over nothing")
        # A stray opening fence blanks everything after it, and the scan then finds
        # no numbers and passes having asserted nothing - the same vacuity as the
        # floor that once satisfied itself on an empty tree. One unbalanced fence
        # before `## Known traps` blanked 168 of 240 lines and waved through the
        # exact plant this test exists to catch. A claim is page prose by
        # definition, so a claim the page states and the mask ate is proof the
        # mask took prose with it. No fraction and no threshold.
        eaten = [claim.name for claim in claims.CLAIMS
                 if grading.read_claim(raw, claim) and not grading.read_claim(text, claim)]
        self.assertEqual(eaten, [], "fence masking removed page prose; an unbalanced "
                                    "fence blanks the rest of the page and this scan "
                                    "would then pass over nothing")
        captured = {m.span(1) for claim in claims.CLAIMS
                    for m in re.finditer(claim.pattern, text)}
        stray = []
        for match in self.TOKEN.finditer(text):
            if match.span(1) in captured or self.COMPOUND.match(text, match.end()):
                continue
            after = self.NOUN.match(text, match.end())
            noun = after.group(1).rstrip(".,;") if after else ""
            if noun in self.CLASSIFIED_NOUNS:
                continue
            section = self._section_at(text, match.start())
            key = (section, f"{match.group(1)} {noun}".strip())
            if key not in self.CLASSIFIED:
                stray.append(f"{section}: {match.group(1)} {noun}".rstrip())
        self.assertEqual(stray, [], "numbers on the page that nothing checks and "
                                    "nothing declares unchecked")


class TheTwoConstantsHaveABoundary(unittest.TestCase):
    """`MIN_CHECKABLE` and `MAX_TOLERANCE` had no test of any kind.

    An independent witness grepped for both names and for `tolerance` and found
    nothing. Both work; neither had the positive and defeating pair AGENTS.md
    requires, which means either could have been changed to any value without a
    gate noticing.
    """

    @staticmethod
    def _refuse():
        raise claims.Underivable("planted: this environment cannot answer")

    def _with_underivable(self, count: int):
        """CLAIMS with `count` of its derivations refusing."""
        rebuilt = tuple(
            dataclasses.replace(claim, derive=self._refuse) if index < count else claim
            for index, claim in enumerate(claims.CLAIMS))
        return unittest.mock.patch.object(claims, "CLAIMS", rebuilt)

    def test_exactly_half_the_claims_derivable_still_passes(self):
        """The boundary is `<`, so half is enough and the constant says so."""
        half = len(claims.CLAIMS) - int(len(claims.CLAIMS) * sov_snapshot.MIN_CHECKABLE)
        with self._with_underivable(half):
            self.assertEqual(sov_snapshot.cmd_check(None), 0)

    def test_one_below_half_refuses_rather_than_reporting_a_pass(self):
        half = len(claims.CLAIMS) - int(len(claims.CLAIMS) * sov_snapshot.MIN_CHECKABLE)
        with self._with_underivable(half + 1):
            self.assertEqual(sov_snapshot.cmd_check(None), 1)

    def test_a_tolerance_at_the_ceiling_is_allowed_and_one_past_it_is_not(self):
        """A tolerance wide enough to be vacuous is the failure the ceiling names.

        At 400 against a record of 356 the claim asserted nothing and nothing
        noticed, which is why the ceiling exists. The selfcheck reads it, so the
        boundary belongs here rather than in a comment.
        """
        for tolerance, expected in ((claims.MAX_TOLERANCE, 0),
                                    (claims.MAX_TOLERANCE + 1, 1)):
            with self.subTest(tolerance=tolerance):
                widened = tuple(
                    dataclasses.replace(claim, tolerance=tolerance)
                    if claim.name == "commits" else claim
                    for claim in claims.CLAIMS)
                with unittest.mock.patch.object(claims, "CLAIMS", widened):
                    self.assertEqual(selfcheck.run(), expected)


class ThePageIsASourceLikeAnyOther(unittest.TestCase):
    """A missing `CLAUDE.md` is a refusal, not a traceback out of the check.

    Every deriver in `claims.py` was taught to refuse. The page itself was not,
    because `grade` read it behind a default argument, so a tree where four of five
    claims derived fine still died with `FileNotFoundError` on the one file the
    check exists to read.
    """

    def test_check_refuses_and_does_not_raise_when_the_page_is_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            absent = Path(tmp) / "nopage" / "CLAUDE.md"
            with unittest.mock.patch.object(claims, "SNAPSHOT", absent):
                self.assertEqual(sov_snapshot.cmd_check(None), 1)

    def test_page_text_refuses_rather_than_raising_oserror(self):
        with tempfile.TemporaryDirectory() as tmp:
            with unittest.mock.patch.object(claims, "SNAPSHOT",
                                            Path(tmp) / "CLAUDE.md"):
                with self.assertRaises(claims.Underivable):
                    claims.page_text()

    def test_a_page_that_is_not_utf8_refuses_rather_than_raising(self):
        """Existence was guarded and readability was not.

        A Windows editor saving UTF-16 is a real way this file arrives, and it gave
        a `UnicodeDecodeError` traceback out of the check. The guard was built for
        the failure that had been demonstrated and not for the one beside it.
        """
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "CLAUDE.md"
            page.write_bytes("runs 40 checks".encode("utf-16"))
            with unittest.mock.patch.object(claims, "SNAPSHOT", page):
                with self.assertRaises(claims.Underivable) as refused:
                    claims.page_text()
                self.assertIn("cannot be read", str(refused.exception))
                self.assertEqual(sov_snapshot.cmd_check(None), 1)

    def test_a_directory_of_that_name_is_not_reported_as_absent(self):
        """Present and unreadable is a different sentence from absent."""
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "CLAUDE.md"
            page.mkdir()
            with unittest.mock.patch.object(claims, "SNAPSHOT", page):
                with self.assertRaises(claims.Underivable) as refused:
                    claims.page_text()
                self.assertIn("is not a file", str(refused.exception))
                self.assertNotIn("absent", str(refused.exception))


class AMalformedCheckTableIsTheEnvironment(unittest.TestCase):
    """A `SyntaxError` out of `sovverify.checks` is a bad checkout, not a bad page.

    `_verification_checks` caught `ImportError` only, and a witness replaced
    `checks.py` with an unclosed parenthesis - which is what this shared working
    tree looks like while a sibling session is mid-edit, and `checks.py` was being
    edited at the time. The traceback escaped `derive_all` entirely.
    """

    def test_check_refuses_and_does_not_traceback_on_an_unparseable_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "broken"
            (root / "scripts" / "sovsnapshot").mkdir(parents=True)
            (root / "scripts" / "sovverify").mkdir(parents=True)
            (root / "CLAUDE.md").write_text("runs 40 checks", encoding="utf-8")
            (root / "scripts" / "sov_snapshot.py").write_bytes(
                (ROOT / "scripts" / "sov_snapshot.py").read_bytes())
            for path in (ROOT / "scripts" / "sovsnapshot").glob("*.py"):
                (root / "scripts" / "sovsnapshot" / path.name).write_bytes(path.read_bytes())
            (root / "scripts" / "sovverify" / "__init__.py").write_text("", encoding="utf-8")
            (root / "scripts" / "sovverify" / "checks.py").write_text(
                "CHECKS = (\n", encoding="utf-8")
            done = subprocess.run([sys.executable, "scripts/sov_snapshot.py", "check"],
                                  cwd=root, capture_output=True, text=True)
        self.assertNotIn("Traceback", done.stderr)
        self.assertIn("the check table could not be read", done.stdout)
        self.assertEqual(done.returncode, 1)


class GradingCannotReachTheRepository(unittest.TestCase):
    """The seam is the signature, not the docstring.

    `grade` once defaulted both arguments, and with them omitted it read the page
    and ran every deriver - so the module docstring saying "nothing here reads a
    repository" was false, and `cmd_check` was the caller taking that path.
    """

    def test_grade_requires_the_derived_values(self):
        with self.assertRaises(TypeError):
            grading.grade(selfcheck.page(commits=1).text)

    def test_grading_touches_only_the_declared_shape_of_a_claim(self):
        """An allowlist, not a blocklist.

        A list of forbidden names - `read_text`, `subprocess`, `open` - is the
        narrowness L-0007 names: it catches the reach that was there and not the
        next one. `claims` holds the sources, so the honest invariant is that this
        module names only the shape of a claim and never a source.
        """
        permitted = {"CLAIMS", "Claim", "Underivable"}
        source = Path(grading.__file__).read_text(encoding="utf-8")
        reached = sorted({node.attr for node in ast.walk(ast.parse(source))
                          if isinstance(node, ast.Attribute)
                          and isinstance(node.value, ast.Name)
                          and node.value.id == "claims"} - permitted)
        self.assertEqual(reached, [], "grading reached into claims for a source")


class TheSyntheticPageCarriesItsOwnValues(unittest.TestCase):
    """A page graded against anything else reports drift against a placeholder."""

    def test_a_page_with_nothing_derived_is_unanswerable_not_drifted(self):
        page = selfcheck.page()
        findings = grading.grade(page.text, page.values)
        self.assertEqual(grading.drift(findings), [])
        self.assertEqual({f.kind for f in findings}, {grading.UNANSWERABLE})


class TheSelfcheckRefusesToProveNothing(unittest.TestCase):
    """With no source derivable, every case is satisfied by both sides saying nothing."""

    def test_a_tree_with_no_sources_fails_rather_than_passing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "bare"
            (root / "scripts" / "sovsnapshot").mkdir(parents=True)
            for name in ("sov_snapshot.py",):
                (root / "scripts" / name).write_bytes(
                    (ROOT / "scripts" / name).read_bytes())
            for path in (ROOT / "scripts" / "sovsnapshot").glob("*.py"):
                (root / "scripts" / "sovsnapshot" / path.name).write_bytes(path.read_bytes())
            done = subprocess.run([sys.executable, "scripts/sov_snapshot.py", "selfcheck"],
                                  cwd=root, capture_output=True, text=True)
        self.assertEqual(done.returncode, 1)
        self.assertIn("nothing was exercised", done.stdout)


class DerivationsRefuseRatherThanRaise(unittest.TestCase):
    """A missing source is `Underivable`, never a traceback and never a zero.

    A directory that is not there once counted as zero, which turns "I cannot see
    the record" into a claim that the page is wrong by the whole count.
    """

    def test_a_missing_directory_is_underivable_not_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            with unittest.mock.patch.object(claims, "ROOT", Path(tmp)):
                with self.assertRaises(claims.Underivable):
                    claims._decision_records()
                with self.assertRaises(claims.Underivable):
                    claims._reports()
                with self.assertRaises(claims.Underivable):
                    claims._declared_operations()


if __name__ == "__main__":
    unittest.main()
