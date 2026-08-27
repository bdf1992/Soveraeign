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
import contextlib
import dataclasses
import importlib
import json
import os
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
from sovsnapshot import committed  # noqa: E402
from sovsnapshot import grading  # noqa: E402
from sovsnapshot import selfcheck  # noqa: E402
from sovsnapshot import shape  # noqa: E402
from sovverify import checks  # noqa: E402


#: The seven claims that count a committed source, which is the set Bdo's ruling on
#: acceptance packet A5 moved onto the commit at HEAD - six derivations, with the
#: manifest count stated twice on the page. `commits` is deliberately outside it: it
#: is a claim about history rather than about a source, it already read git before
#: the ruling, and it carries the only tolerance in the table.
SOURCE_CLAIMS = ("decision records", "service boundaries", "manifests",
                 "agent definitions", "skills", "workflows", "reports")

#: Everything the commit answers, which is those seven plus the history count.
COMMITTED_CLAIMS = SOURCE_CLAIMS + ("commits",)

#: The two the same ruling left on the working tree, because each counts something
#: the repository already computes and reading it out of the commit would be a
#: second implementation rather than a change of referent. Listed here so the cases
#: below can assert what they cost as well as what they are.
WORKING_TREE_CLAIMS = ("verification checks", "declared operations")


def write_tree(root: Path, files: dict[str, str]) -> None:
    """Lay a fixture tree out on disk, creating whatever parents it needs."""
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def fixture_git(root: Path, *argv: str) -> str:
    """Git inside a throwaway fixture repository, with an identity of its own.

    `-c` rather than `git config`, so a fixture never reads and never writes the
    machine's own settings. The identity is its own, and `core.excludesFile` is
    emptied because a global ignore rule on the host would otherwise decide what
    this fixture counts as untracked - which is the one thing the fixture is about.

    A non-zero exit is raised here rather than returned: a fixture that half-built
    itself makes every assertion after it a report on the fixture.
    """
    done = subprocess.run(["git", "-c", "user.name=snapshot fixture",
                           "-c", "user.email=fixture@example.invalid",
                           "-c", "core.excludesFile=", *argv],
                          cwd=root, capture_output=True, text=True)
    if done.returncode != 0:
        raise AssertionError(f"fixture git {argv[0]} failed: {done.stderr.strip()}")
    return done.stdout.strip()


def fixture_commit(root: Path, message: str) -> str:
    """Land everything the fixture has written, and return the new HEAD.

    `add -A` is the point inside a fixture repository whose entire contents this
    test wrote a moment ago; AGENTS.md's rule against it is about the shared
    working tree, where another session's file could be swept in.
    """
    fixture_git(root, "add", "-A")
    fixture_git(root, "commit", "-q", "-m", message)
    return fixture_git(root, "rev-parse", "HEAD")


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
    """A `SyntaxError` out of the check table is a bad checkout, not a bad page.

    `_verification_checks` caught `ImportError` only, and a witness replaced
    `checks.py` with an unclosed parenthesis - which is what this shared working
    tree looks like while a sibling session is mid-edit, and `checks.py` was being
    edited at the time. The traceback escaped `derive_all` entirely.

    This claim imports the table rather than reading it out of the commit, which is
    where Bdo's ruling on acceptance packet A5 left it, so the fixture is a working
    tree holding a broken one. It is a repository as well, so the eight committed
    claims answer and this refusal is reported beside them rather than being the
    only thing the run could say.
    """

    def test_check_refuses_and_does_not_traceback_on_an_unparseable_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "broken"
            write_tree(root, {
                "CLAUDE.md": "runs 40 checks",
                "scripts/sovverify/__init__.py": "",
                "scripts/sovverify/checks.py": "CHECKS = (\n",
            })
            (root / "scripts" / "sovsnapshot").mkdir(parents=True)
            (root / "scripts" / "sov_snapshot.py").write_bytes(
                (ROOT / "scripts" / "sov_snapshot.py").read_bytes())
            for path in (ROOT / "scripts" / "sovsnapshot").glob("*.py"):
                (root / "scripts" / "sovsnapshot" / path.name).write_bytes(path.read_bytes())
            fixture_git(root, "init", "-q")
            fixture_commit(root, "commit a check table that does not parse")
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


class TheRecordIsTheCommitAtHead(unittest.TestCase):
    """The referent ruling, in both directions, over every claim that counts a source.

    Bdo accepted acceptance packet A5 on 2026-08-26 and ruled with it that the
    snapshot's counts are counts of committed state. The defect that closes was
    reproducible and had already fired for real: one untracked directory under
    `.claude/skills/`, HEAD unmoved, turned the required gate red for every session
    on the branch - and printed an instruction to correct `CLAUDE.md`, a file
    `grant:standing-landing-loop` excludes from its scope, so the landing loop
    could not make the edit the gate demanded.

    Both directions live in one method and in this order, because the positive case
    moves HEAD and the defeating case only means something while HEAD stands still.
    """

    #: What the fixture repository holds at its first commit. The three files that
    #: match no pattern are there on purpose: without them a count that had stopped
    #: filtering would still agree with the expected numbers below.
    SEED = {
        "decisions/0001-one.md": "one\n",
        "decisions/0002-two.md": "two\n",
        "decisions/README.md": "not a numbered record\n",
        "reports/one.md": "one\n",
        "reports/observations/nested.md": "not a direct child\n",
        ".claude/agents/one.md": "one\n",
        ".claude/skills/alpha/SKILL.md": "alpha\n",
        ".claude/skills/beta/SKILL.md": "beta\n",
        ".claude/skills/loose.md": "a file, not a skill\n",
        ".claude/workflows/one.js": "// one\n",
        ".claude/workflows/notes.md": "not a workflow\n",
        "services/alpha/contracts/service.json": "{}\n",
        "services/alpha/README.md": "not a manifest\n",
    }

    FIRST = {"commits": 1, "decision records": 2, "service boundaries": 1,
             "manifests": 1, "agent definitions": 1, "skills": 2, "workflows": 1,
             "reports": 1}

    #: One change per claim, so a claim that quietly kept globbing the tree is named
    #: individually rather than hidden behind a sibling that did not move. All of
    #: them are untracked additions, because that is the shape that turned the gate
    #: red on an unmoved HEAD.
    PLANT = {
        ".claude/skills/gamma/SKILL.md": "a sibling session mid-create of something else\n",
        "decisions/0003-three.md": "three\n",
        "reports/two.md": "two\n",
        ".claude/agents/two.md": "two\n",
        ".claude/workflows/two.js": "// two\n",
        "services/beta/contracts/service.json": "{}\n",
    }

    SECOND = {"commits": 2, "decision records": 3, "service boundaries": 2,
              "manifests": 2, "agent definitions": 2, "skills": 3, "workflows": 2,
              "reports": 2}

    def _committed_only(self, answered: dict[str, int]) -> dict[str, int]:
        """The fixture's own counts, with the two working-tree claims set aside.

        Those two read `claims.ROOT`, which the fixture does not move, so they
        answer about this checkout throughout. Asserted rather than dropped, in
        `test_the_working_tree_claims_answer_about_this_checkout` below.
        """
        return {name: value for name, value in answered.items()
                if name in COMMITTED_CLAIMS}

    def test_the_working_tree_claims_answer_about_this_checkout(self):
        """The cost of the ruling's other half, in the fixture that proves its first.

        The fixture repository holds no check table and no capability projection, so
        a claim reading it would refuse. These two answer, and they answer this
        repository's numbers - which is the referent Bdo left them on, stated as a
        case rather than only in `claims.UNCHECKED`.
        """
        reference = ROOT / "contracts" / "fixtures" / "capability-map.reference.json"
        expected = {"verification checks": len(checks.CHECKS),
                    "declared operations": len(json.loads(
                        reference.read_text(encoding="utf-8"))["capabilities"])}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "fixture"
            write_tree(root, self.SEED)
            fixture_git(root, "init", "-q")
            fixture_commit(root, "seed the fixture")
            with unittest.mock.patch.object(committed, "ROOT", root):
                answered = claims.derive_all().values
        self.assertEqual({name: answered[name] for name in WORKING_TREE_CLAIMS}, expected)

    def test_uncommitted_work_moves_no_count_and_landing_the_same_work_moves_them_all(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "fixture"
            write_tree(root, self.SEED)
            fixture_git(root, "init", "-q")
            head = fixture_commit(root, "seed the fixture")
            page = selfcheck.page(**self.FIRST).text

            with unittest.mock.patch.object(committed, "ROOT", root):
                with self.subTest("the commit answers every claim it owns"):
                    self.assertEqual(self._committed_only(claims.derive_all().values),
                                     self.FIRST)

                write_tree(root, self.PLANT)
                self.assertEqual(fixture_git(root, "rev-parse", "HEAD"), head,
                                 "the plant moved HEAD, so the defeating case below "
                                 "would prove nothing")
                self.assertNotEqual(fixture_git(root, "status", "--porcelain"), "",
                                    "the plant left the tree clean, so there is no "
                                    "untracked work for this case to be about")
                with self.subTest("untracked work moves no count"):
                    unmoved = self._committed_only(claims.derive_all().values)
                    self.assertEqual(unmoved, self.FIRST)
                with self.subTest("and the page stating those counts is still not drifted"):
                    # The counts above are the mechanism; this is the verdict, at the
                    # level the gate actually failed on for every session on the branch.
                    self.assertEqual(grading.drift(grading.grade(page, unmoved)), [])

                landed = fixture_commit(root, "land the same work")
                self.assertNotEqual(landed, head)
                with self.subTest("landing the same work moves every count"):
                    moved = self._committed_only(claims.derive_all().values)
                    self.assertEqual(moved, self.SECOND)
                with self.subTest("and the same page is now reported as drifted"):
                    # The control. Refusing to see untracked work must not have made
                    # the check blind to the landed kind. Every committed source claim
                    # moves by one and is reported; `commits` moves by one too and is
                    # not, because its declared tolerance of 25 absorbs it - which is
                    # the tolerance doing exactly its job and is why it is named here
                    # rather than counted. The two working-tree claims are absent from
                    # `moved`, so the page's placeholder for them is unanswerable
                    # rather than drift, which is the split under test.
                    reported = sorted(f.claim for f in grading.drift(
                        grading.grade(page, moved)))
                    self.assertEqual(reported, sorted(SOURCE_CLAIMS))


class OneDerivationPassReadsTheCommitOnce(unittest.TestCase):
    """Seven claims read one listing, so a pass has to ask git for it exactly once.

    Not a performance note. Seven separate listings can disagree with each other if
    HEAD moves between them, which reports the check as broken when the record has
    simply moved - the same failure `derive_all` was already one-shot to avoid.
    The hold is scoped to the pass, and the fixture above is the case that fails if
    it is ever widened to the process: it derives, lands a commit, and derives again
    expecting different numbers.
    """

    def test_a_pass_lists_the_commit_once_and_the_hold_does_not_outlive_it(self):
        listings = []
        real = committed._git

        def counted(*argv):
            if argv[:1] == ("ls-tree",):
                listings.append(argv)
            return real(*argv)

        with unittest.mock.patch.object(committed, "_git", counted):
            claims.derive_all()
            self.assertEqual(len(listings), 1, "one pass listed the commit more than once")
            committed.tracked_paths()
        self.assertEqual(len(listings), 2, "the hold outlived the pass that opened it")
        self.assertEqual(committed._HELD, [], "a pass left its hold standing")

    def test_the_hold_is_keyed_on_the_repository_it_read(self):
        """Held for a pass is not enough; it has to be held for a repository.

        Unkeyed, this was demonstrated returning the first repository's 982 paths
        after `ROOT` moved inside the pass - a confident answer about the wrong
        tree, which is the same class of failure as a stale count and harder to see.
        """
        listings = {"one": b"a/x\0", "two": b"b/y\0"}

        def by_root(*argv):
            if argv[:1] == ("ls-tree",):
                return subprocess.CompletedProcess(argv, 0, listings[committed.ROOT.name], b"")
            return subprocess.CompletedProcess(argv, 1, b"", b"not asked for here")

        with unittest.mock.patch.object(committed, "_git", by_root):
            with committed.one_reading():
                with unittest.mock.patch.object(committed, "ROOT", Path("one")):
                    self.assertEqual(committed.tracked_paths(), ["a/x"])
                with unittest.mock.patch.object(committed, "ROOT", Path("two")):
                    self.assertEqual(committed.tracked_paths(), ["b/y"],
                                     "the hold answered about the previous repository")


class GitIsNeverAllowedToAnswerWithSomethingElse(unittest.TestCase):
    """Every way git can fail to answer has to arrive as `Underivable`.

    A `check` spawns six git processes where it spawned four - `rev-parse`,
    `rev-list` and `ls-tree`, twice over the two derivation passes - so each of
    these is likelier to be reached than it was, and each of them escaped
    `derive_all`, which catches `Underivable` and nothing else, as a traceback.
    The figure is measured rather than remembered: an independent reading counted
    the spawns and found this sentence said ten against two.
    """

    def test_every_git_call_carries_a_timeout(self):
        """A process that never returns never fails, and this gate's wall time is graded."""
        seen = {}

        def record(*argv, **keywords):
            seen.update(keywords)
            return subprocess.CompletedProcess(argv[0], 0, b"", b"")

        with unittest.mock.patch.object(subprocess, "run", record):
            committed._git("rev-parse", "--is-shallow-repository")
        self.assertEqual(seen.get("timeout"), committed.GIT_TIMEOUT_SECONDS)

    def test_a_shallow_checkout_refuses_the_commit_count(self):
        """CI is the only place this fires, and nothing protected it.

        `actions/checkout@v4` defaults to depth 1 and three workflows run `verify.py`
        after it, so without this guard `commits` reads the clone's depth against a
        page stating hundreds and reports a correct page as drifted. An independent
        reading cut the guard to `if False:` and left 55 tests green - and so did
        comparing git's bytes against the string `"true"`, which is silently always
        False now that this module runs git in bytes mode.
        """
        def answer(argv, **_keywords):
            payload = b"true" if argv[1] == "rev-parse" else b"3"
            return subprocess.CompletedProcess(argv, 0, payload, b"")

        with unittest.mock.patch.object(subprocess, "run", answer):
            with self.assertRaises(committed.Underivable) as refused:
                committed.commits()
        self.assertIn("shallow", str(refused.exception))

    def test_a_full_checkout_answers_the_commit_count(self):
        """The positive half. A guard that refused every checkout would pass the case
        above while breaking the claim in every environment there is."""
        def answer(argv, **_keywords):
            payload = b"false" if argv[1] == "rev-parse" else b"373"
            return subprocess.CompletedProcess(argv, 0, payload, b"")

        with unittest.mock.patch.object(subprocess, "run", answer):
            self.assertEqual(373, committed.commits())

    def test_an_undeclared_vector_is_refused_rather_than_run(self):
        """The reach a second reading demonstrated, closed at the source.

        `_git` takes `*argv`, so before this the subcommand was chosen at the call
        site and nothing read it. A claim calling
        `committed._git("ls-files", "--others", "--exclude-standard", "--cached", ...)`
        passed the shape guard, passed selfcheck, and turned the gate red on one
        untracked directory - the original defect back verbatim, through a call that
        satisfied "reaches the record".
        """
        for argv in (
            ("ls-files",),
            ("ls-files", "--others", "--exclude-standard", "--cached", "--",
             ".claude/skills"),
            ("grep", "--no-index", "x"),
            ("hash-object", "-w", "CLAUDE.md"),
            ("ls-tree", "-r", "-z", "--full-name", "--name-only", "HEAD~1"),
            ("show", "HEAD:CLAUDE.md"),
        ):
            with self.subTest(argv=argv):
                spawned = []

                def record(*called, **_keywords):
                    spawned.append(called)
                    return subprocess.CompletedProcess(called[0], 0, b"", b"")

                with unittest.mock.patch.object(subprocess, "run", record):
                    with self.assertRaises(committed.NotADeclaredReading):
                        committed._git(*argv)
                self.assertEqual([], spawned, f"git {argv} was spawned before refusing")

    def test_a_declared_vector_is_refused_by_nothing(self):
        """The positive half. A guard that refused everything would pass the case above
        and break every claim, so the three declared vectors are asserted to run."""
        for argv in sorted(committed.PERMITTED_ARGV):
            with self.subTest(argv=argv):
                with unittest.mock.patch.object(
                        subprocess, "run",
                        lambda *a, **k: subprocess.CompletedProcess(a[0], 0, b"", b"")):
                    self.assertEqual(0, committed._git(*argv).returncode)

    def test_every_vector_the_module_runs_is_declared(self):
        """The allowlist against the source, so a fourth call site cannot be added and
        left undeclared - which would fail at runtime rather than here."""
        tree = ast.parse(Path(committed.__file__).read_text(encoding="utf-8"))
        found = set()
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id == "_git"):
                self.assertTrue(
                    all(isinstance(a, ast.Constant) for a in node.args),
                    "a git call site builds its vector, so the allowlist cannot read it")
                found.add(tuple(a.value for a in node.args))
        self.assertEqual(set(committed.PERMITTED_ARGV), found)

    def test_a_git_that_does_not_return_refuses(self):
        def blocked(*_argv, **keywords):
            raise subprocess.TimeoutExpired(cmd="git", timeout=keywords.get("timeout", 0))

        with unittest.mock.patch.object(subprocess, "run", blocked):
            with self.assertRaises(claims.Underivable):
                committed.tracked_paths()

    def test_a_commit_count_git_will_not_spell_refuses_rather_than_raising(self):
        """`int("")` is a `ValueError`, which `derive_all` does not catch."""
        def silent(*argv):
            if argv[:1] == ("rev-parse",):
                return subprocess.CompletedProcess(argv, 0, b"false\n", b"")
            return subprocess.CompletedProcess(argv, 0, b"\n", b"")

        with unittest.mock.patch.object(committed, "_git", silent):
            with self.assertRaises(claims.Underivable) as refused:
                committed.commits()
        self.assertIn("the commit count could not be read", str(refused.exception))

    def test_a_directory_prefix_is_matched_by_exact_case(self):
        """`core.ignorecase` is true in this repository, so git will record `Decisions/`.

        The old glob matched the prefix case-insensitively on Windows and
        case-sensitively in CI. This refuses rather than picking one, which is the
        answer a reader can act on.
        """
        with unittest.mock.patch.object(committed, "tracked_paths",
                                        lambda: ["Decisions/0001-a.md"]):
            with self.assertRaises(claims.Underivable):
                claims._decision_records()


class MatchingIsBySegmentAndByCase(unittest.TestCase):
    """Two deliberate choices in `committed.matches`, each pinned by the case for it.

    Segment-wise, so `*` never crosses a `/`. A flat fnmatch over a whole path would
    count a manifest nested two directories below
    `services/*/contracts/service.json`, which `Path.glob` never did.

    Case-sensitive, which is a measured change from the old derivation rather than
    an accident of it. `Path.glob` is case-insensitive on Windows and case-sensitive
    on POSIX, so `reports/A.MD` counted on this machine and not in CI - one count
    with two values depending on which platform ran it. Measured on this tree the
    nine counts are identical either way, which is exactly why the choice needs a
    case: nothing else would notice it changing.
    """

    def test_a_star_does_not_cross_a_separator(self):
        self.assertTrue(committed.matches("services/a/contracts/service.json",
                                          "services/*/contracts/service.json"))
        self.assertFalse(committed.matches("services/a/b/contracts/service.json",
                                           "services/*/contracts/service.json"))

    def test_the_match_is_case_sensitive_on_every_platform(self):
        self.assertTrue(committed.matches("a.md", "*.md"))
        self.assertFalse(committed.matches("A.MD", "*.md"))

    def test_a_dotted_entry_is_matched_the_way_the_old_derivation_matched_it(self):
        """`Path.glob('*')` yields names beginning with a dot; so must this.

        The `glob` module skips them and `pathlib` does not, and the skills count
        globs `*`. Reading the wrong one of those two would have silently changed a
        count while every test in this file went on passing.
        """
        self.assertTrue(committed.matches(".hidden", "*"))


class DerivationsRefuseRatherThanRaise(unittest.TestCase):
    """A source that cannot answer is `Underivable`, never a traceback and never a zero.

    A directory that is not there once counted as zero, which turns "I cannot see
    the record" into a claim that the page is wrong by the whole count. Since the
    referent ruling that discipline has a second edge: where git cannot answer,
    nothing may quietly fall back to a working-tree read, because a fallback is the
    defect the ruling closes wearing a guard.
    """

    def test_every_source_claim_refuses_where_git_cannot_answer(self):
        """The sources are on disk and invisible to git, so a fallback would show up.

        A tree that is not a repository, carrying a populated `decisions/`,
        `reports/`, `.claude/skills/` and `services/`: the pre-ruling code counted
        exactly these and answered confidently. Every one must refuse instead.
        `commits` is not in the set - it is a claim about history, and a temporary
        directory that happened to sit inside some other repository would let it
        answer, failing this case for a reason that is not its subject. Nor are the
        two claims the ruling left on the working tree, which are supposed to answer
        from disk and are graded for that a few classes down.
        """
        on_disk = {
            "decisions/0001-a.md": "a\n",
            "reports/a.md": "a\n",
            ".claude/agents/a.md": "a\n",
            ".claude/skills/alpha/SKILL.md": "a\n",
            ".claude/workflows/a.js": "// a\n",
            "services/a/contracts/service.json": "{}\n",
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "notarepo"
            write_tree(root, on_disk)
            # Every one of them, not one of them. Asserting a single file left the
            # others free to be absent, and an absent source refuses for a reason
            # that has nothing to do with git - which would satisfy every case
            # below while proving none of them.
            missing = sorted(name for name in on_disk if not (root / name).is_file())
            self.assertEqual(missing, [], "the fixture did not write itself, so a "
                                          "refusal here would be about the fixture")
            with unittest.mock.patch.object(committed, "ROOT", root):
                for claim in claims.CLAIMS:
                    if claim.name not in SOURCE_CLAIMS:
                        continue
                    with self.subTest(claim=claim.name):
                        with self.assertRaises(claims.Underivable) as refused:
                            claim.derive()
                        # And refused for this reason. `assertRaises` alone is
                        # satisfied by a refusal for any reason at all.
                        self.assertIn("git", str(refused.exception).lower())

    def test_a_directory_the_commit_does_not_hold_is_underivable_not_zero(self):
        """The original case, moved onto the commit: absent is not an answer of zero.

        The listing is planted rather than committed, because git answering fine
        about a commit that simply holds none of these directories is the whole
        situation. Building a repository for it would spend a second on proving
        that git works, which the fixture above already proves.
        """
        with unittest.mock.patch.object(committed, "tracked_paths", lambda: ["seed.txt"]):
            for deriver in (claims._decision_records, claims._reports, claims._skills,
                            claims._agent_definitions, claims._workflows,
                            claims._service_manifests):
                with self.subTest(deriver=deriver.__name__):
                    with self.assertRaises(claims.Underivable):
                        deriver()

    def test_git_missing_from_the_path_refuses_rather_than_raising_oserror(self):
        """`commits` was the only git caller once and let this escape as a traceback."""
        def absent(*_args, **_kwargs):
            raise FileNotFoundError(2, "No such file or directory", "git")

        with unittest.mock.patch.object(subprocess, "run", absent):
            with self.assertRaises(claims.Underivable) as refused:
                committed.tracked_paths()
            self.assertIn("git could not be run here", str(refused.exception))


class TheGitCallIsRootedAtTheRepository(unittest.TestCase):
    """Not at the process working directory.

    `verify.py` launches its checks from several cwds and several sessions run from
    their own worktrees. A git call anchored on the caller's cwd would answer about
    whichever repository the caller happened to be standing in, and would answer
    confidently, which is worse than failing.
    """

    def test_the_answer_does_not_depend_on_where_the_process_stands(self):
        here = claims._skills()
        was = os.getcwd()
        try:
            os.chdir(tempfile.gettempdir())
            elsewhere = claims._skills()
        finally:
            os.chdir(was)
        self.assertEqual(elsewhere, here)


class TheTwoWorkingTreeClaimsReadTheTree(unittest.TestCase):
    """The half of the referent ruling that did not move, and what it costs.

    Bdo's ruling on acceptance packet A5 left `verification checks` and `declared
    operations` where they were: each counts something the repository already
    computes, so pulling the same bytes out of `git show HEAD:...` would be a
    second implementation of an existing count rather than a change of referent -
    the failure that made a draft of this check report 9 conformance cases against
    the suite's own 20.

    The cost of leaving them is the mirror of the cost of moving the other eight,
    and it is graded here rather than only stated in `claims.UNCHECKED`: these two
    see work that has not landed.
    """

    def test_the_check_count_is_the_table_verify_itself_runs(self):
        """No parse and no second count: `len` of the tuple `verify.py` imports."""
        self.assertEqual(claims._verification_checks(), len(checks.CHECKS))

    def test_both_are_named_in_unchecked(self):
        """"Say so in UNCHECKED" is half the ruling, and nothing else holds it.

        Deleting that entry was tried against this file and the suite stayed green:
        the numbers are still right and the check still passes, so which half a
        reader is looking at would be carried by a paragraph no case pins. The names
        are matched rather than the sentence, because the sentence should be free to
        be reworded and the claims should not.
        """
        said = " ".join(claims.UNCHECKED)
        for name in WORKING_TREE_CLAIMS:
            with self.subTest(claim=name):
                self.assertIn(name, said,
                              f"{name} reads the working tree and UNCHECKED does not "
                              "name it, so the run reports more than it checked")

    def test_the_capability_projection_moves_before_anything_is_committed(self):
        """A `sov_capability.py build` that has not landed moves this number.

        HEAD is not even a repository here, which is the point: nothing about this
        claim consults it. The eight committed claims have the opposite case a few
        classes up, and between them they are the whole of the ruling.
        """
        first = {"contracts/fixtures/capability-map.reference.json":
                 '{"capabilities": [1, 2, 3]}\n'}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "tree"
            write_tree(root, first)
            with unittest.mock.patch.object(claims, "ROOT", root):
                self.assertEqual(claims._declared_operations(), 3)
                write_tree(root, {"contracts/fixtures/capability-map.reference.json":
                                  '{"capabilities": [1, 2, 3, 4]}\n'})
                self.assertEqual(claims._declared_operations(), 4)

    def test_an_absent_projection_refuses_and_says_what_builds_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            with unittest.mock.patch.object(claims, "ROOT", Path(tmp)):
                with self.assertRaises(claims.Underivable) as refused:
                    claims._declared_operations()
        self.assertIn("sov_capability.py build", str(refused.exception))

    def test_an_unreadable_projection_refuses_rather_than_raising(self):
        """Half-written JSON is the environment failing to answer, not a wrong page."""
        for content in ("{not json", '{"nothing here": 1}'):
            with self.subTest(content=content):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp) / "tree"
                    write_tree(root, {
                        "contracts/fixtures/capability-map.reference.json": content})
                    with unittest.mock.patch.object(claims, "ROOT", root):
                        with self.assertRaises(claims.Underivable):
                            claims._declared_operations()


class EveryClaimReadsTheCommit(unittest.TestCase):
    """The structural guard that keeps the referent ruling from being quietly undone.

    Nothing in the grader can tell a committed count from a working-tree one - the
    number looks identical, which is how the defect survived nine review rounds. So
    the invariant is structural, re-read from the bytes of `claims.py` on every run,
    and like every guard here it needs the case that proves it fires.
    """

    STRAY = '''
from pathlib import Path

from sovsnapshot import committed

ROOT = Path(".")
SNAPSHOT = ROOT / "CLAUDE.md"


def _skills() -> int:
    return len(list((ROOT / ".claude" / "skills").glob("*")))


def _peek() -> str:
    return SNAPSHOT.read_text(encoding="utf-8")


CLAIMS = (
    Claim("skills", r"(\\d+)\\s+skills", _skills),
)
'''

    #: Doctored sources for `claims.py`, and the phrase the guard owes each one.
    #: An independent reading planted the first four against an earlier version of
    #: the guard and every one of them returned None - including the first, which is
    #: a silent fall back to a working-tree glob wearing the name of the module the
    #: invariant is about, and which therefore defeated the invariant itself rather
    #: than merely escaping it. A second reading planted the three after them, which
    #: reach the record module for a `Path` and glob it.
    FOOLED = {
        "a local variable named committed": ('''
from pathlib import Path

from sovsnapshot import committed

ROOT = Path(".")


def _skills() -> int:
    committed = ROOT / ".claude" / "skills"
    return len(list(committed.glob("*")))


CLAIMS = (Claim("skills", r"(\\d+)\\s+skills", _skills),)
''', "rebound or shadowed"),
        "a table that is not read at module level": ('''
from sovsnapshot import committed


def _build():
    CLAIMS = (1, 2, 3)
    return CLAIMS


def _skills() -> int:
    return committed.count(".claude/skills", "*", "skills", dirs=True)
''', "no claim table could be read from"),
        "the page reached by name rather than through SNAPSHOT": ('''
from pathlib import Path

from sovsnapshot import committed

ROOT = Path(".")


def _skills() -> int:
    return committed.count(".claude/skills", "*", "skills", dirs=True)


def _peek() -> str:
    return (ROOT / "CLAUDE.md").read_text(encoding="utf-8")


CLAIMS = (Claim("skills", r"(\\d+)\\s+skills", _skills),)
''', "_peek"),
        "committed named but never imported": ('''
def _skills() -> int:
    return committed.count(".claude/skills", "*", "skills", dirs=True)


CLAIMS = (Claim("skills", r"(\\d+)\\s+skills", _skills),)
''', "is not imported at module level"),
        # The second reading's shape: `committed.ROOT` is a `Path` the record module
        # exports, so taking it and globbing satisfied every rule here while reading
        # the working tree. Three spellings, because closing only the one that was
        # demonstrated is the narrowness L-0007 names.
        "a glob through committed.ROOT": ('''
from sovsnapshot import committed


def _skills() -> int:
    return len(list((committed.ROOT / ".claude" / "skills").glob("*")))


CLAIMS = (Claim("skills", r"(\\d+)\\s+skills", _skills),)
''', "committed.ROOT"),
        "a pathlib glob built from committed.ROOT": ('''
from pathlib import Path

from sovsnapshot import committed


def _skills() -> int:
    return len(list(Path(committed.ROOT, ".claude", "skills").glob("*")))


CLAIMS = (Claim("skills", r"(\\d+)\\s+skills", _skills),)
''', "committed.ROOT"),
        # This one is why the take is looked for across the whole source rather than
        # inside each derivation: the deriver reaches a real answer and passes the
        # reach rule, and the glob is built from a module-level binding.
        "committed.ROOT bound at module level and globbed from a deriver": ('''
from sovsnapshot import committed

SKILLS = committed.ROOT / ".claude" / "skills"


def _skills() -> int:
    committed.tracked_paths()
    return len(list(SKILLS.glob("*")))


CLAIMS = (Claim("skills", r"(\\d+)\\s+skills", _skills),)
''', "committed.ROOT"),
    }

    #: The keyword spelling is legal Python and must be read, not skipped. Skipping
    #: it reported "the source declares 0 claims", which sends a reader looking for
    #: a broken table when the table is fine and the reader is not.
    KEYWORD = '''
from sovsnapshot import committed


def _skills() -> int:
    return committed.count(".claude/skills", "*", "skills", dirs=True)


CLAIMS = (Claim("skills", r"(\\d+)\\s+skills", derive=_skills),)
'''

    #: A claim that reaches the record and is nonetheless named as reading the tree,
    #: which is the exception outliving what it was for.
    STALE_EXCEPTION = '''
from sovsnapshot import committed


def _skills() -> int:
    return committed.count(".claude/skills", "*", "skills", dirs=True)


CLAIMS = (Claim("skills", r"(\\d+)\\s+skills", _skills),)
'''

    #: The same claim globbing the tree, which is what a working-tree exception is
    #: supposed to permit - and, with nothing else declared, leaves the guard
    #: grading nothing.
    ONLY_EXCEPTIONS = '''
from pathlib import Path


def _skills() -> int:
    return len(list(Path(".claude/skills").glob("*")))


CLAIMS = (Claim("skills", r"(\\d+)\\s+skills", _skills),)
'''

    @staticmethod
    @contextlib.contextmanager
    def _doctored(source: str, claim_count: int = 1,
                  working_tree: tuple[str, ...] = ()):
        """Grade the guard against a planted `claims.py` instead of the real one.

        `working_tree` is empty by default and not inherited from `shape`: a planted
        table declares one claim of its own, and leaving the real exception names in
        place would report them absent from it in every case below, which is a
        finding about the fixture rather than about the shape under test.
        """
        with tempfile.TemporaryDirectory() as tmp:
            planted = Path(tmp) / "claims.py"
            planted.write_text(source, encoding="utf-8")
            with unittest.mock.patch.object(claims, "__file__", str(planted)), \
                    unittest.mock.patch.object(shape, "WORKING_TREE", working_tree), \
                    unittest.mock.patch.object(claims, "CLAIMS",
                                               claims.CLAIMS[:claim_count]):
                yield

    def test_the_declared_table_reads_the_commit(self):
        self.assertIsNone(selfcheck.derivations_read_the_commit())

    def test_each_shape_that_fooled_the_guard_is_now_reported(self):
        for label, (source, phrase) in self.FOOLED.items():
            with self.subTest(shape=label):
                with self._doctored(source):
                    said = selfcheck.derivations_read_the_commit()
                self.assertIsNotNone(said, label)
                self.assertIn(phrase, said)

    def test_an_empty_table_is_reported_rather_than_satisfying_the_guard(self):
        """The guard's own vacuity: finding nothing is not finding nothing wrong."""
        with self._doctored("CLAIMS = ()\n", claim_count=0):
            said = selfcheck.derivations_read_the_commit()
        self.assertIsNotNone(said)
        self.assertIn("graded nothing", said)

    def test_a_derivation_passed_by_keyword_is_read_rather_than_skipped(self):
        with self._doctored(self.KEYWORD):
            self.assertIsNone(selfcheck.derivations_read_the_commit())

    def test_a_working_tree_exception_that_reaches_the_record_is_reported(self):
        """An exception is a claim about a derivation, and derivations move.

        Nothing fails when a claim named here quietly starts reading the commit -
        the number is right either way - so the guard stops grading it and nobody
        finds out that the exception is now a hole with no reason behind it.
        """
        with self._doctored(self.STALE_EXCEPTION, working_tree=("skills",)):
            said = shape.derivations_read_the_commit()
        self.assertIsNotNone(said)
        self.assertIn("outlived its reason", said)

    def test_an_exception_naming_a_claim_the_table_does_not_declare_is_reported(self):
        with self._doctored(self.STALE_EXCEPTION, working_tree=("renamed since",)):
            said = shape.derivations_read_the_commit()
        self.assertIsNotNone(said)
        self.assertIn("grades nothing", said)

    def test_a_table_that_is_all_exceptions_is_reported_rather_than_passing(self):
        """The exceptions' own vacuity, one layer under the empty table's."""
        with self._doctored(self.ONLY_EXCEPTIONS, working_tree=("skills",)):
            said = shape.derivations_read_the_commit()
        self.assertIsNotNone(said)
        self.assertIn("guard graded nothing", said)

    def test_the_declared_exceptions_are_the_claims_the_ruling_named(self):
        """The allowlist is the soft spot, so the names are pinned where a diff shows.

        A third name added to `shape.WORKING_TREE` would silently stop grading a
        third claim, and the guard cannot tell a legitimate exception from a
        convenient one. This is the pin: widening it means editing this line, which
        is Bdo's ruling on acceptance packet A5 being changed rather than drifted.
        """
        self.assertEqual(shape.WORKING_TREE, WORKING_TREE_CLAIMS)

    def test_the_declared_readers_are_the_ones_the_claims_module_imports(self):
        """A reader named here and absent there would widen the invariant silently."""
        source = ast.parse(Path(claims.__file__).read_text(encoding="utf-8"))
        imported = {(alias.asname or alias.name) for node in source.body
                    if isinstance(node, ast.ImportFrom) for alias in node.names}
        self.assertTrue(set(shape.READERS) <= imported,
                        f"{sorted(set(shape.READERS) - imported)} are declared readers "
                        "that claims.py does not import")

    def test_the_source_claims_named_in_this_file_are_the_ones_the_table_declares(self):
        """A stale list here would quietly shrink every case that iterates it.

        Several cases loop over `SOURCE_CLAIMS` and filter on `COMMITTED_CLAIMS`,
        and a claim renamed or added in `claims.py` and not here would drop out of
        all of them while they went on reporting success - the vacuity this file has
        had to repair three times. The two halves are asserted as a partition, so a
        claim cannot be quietly moved from one to the other either.
        """
        self.assertEqual(set(COMMITTED_CLAIMS) | set(WORKING_TREE_CLAIMS),
                         {claim.name for claim in claims.CLAIMS})
        self.assertEqual(set(COMMITTED_CLAIMS) & set(WORKING_TREE_CLAIMS), set())
        self.assertEqual(set(COMMITTED_CLAIMS) - set(SOURCE_CLAIMS), {"commits"})

    def test_a_claim_that_globs_the_tree_and_a_stray_page_read_are_both_reported(self):
        with self._doctored(self.STRAY):
            said = selfcheck.derivations_read_the_commit()
        self.assertIsNotNone(said)
        self.assertIn("_skills reaches none of", said)
        self.assertIn("_peek", said)

    def test_the_selfcheck_fails_on_it_rather_than_only_computing_it(self):
        """A guard computed and never consulted is the failure this module keeps having.

        The derivation is stubbed: what is under test is whether `run` acts on the
        guard, and reading the real repository to find that out would spend a fifth
        of a second answering a question the case does not ask.
        """
        answered = claims.Derived({claim.name: 1 for claim in claims.CLAIMS}, {})
        with unittest.mock.patch.object(claims, "derive_all", lambda: answered), \
                unittest.mock.patch.object(selfcheck, "derivations_read_the_commit",
                                           lambda: "planted: a claim globs the tree"):
            self.assertEqual(selfcheck.run(), 1)


if __name__ == "__main__":
    unittest.main()
