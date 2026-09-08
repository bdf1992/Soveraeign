"""Run every construction that ever defeated the witness-context check, and require it to fail.

Every case from every independent reading, ids running D1..Dn with no gaps. Until this module existed they were
prose in docstrings, and an independent reading observed the consequence: one defeat
reproduced across three candidates *after* it had been named, because what refused it was
a sentence. `SDLC.md` gate 3 and `AGENTS.md`, Testing and verification, require a
defeating case per consequential behaviour, and a check whose refusals are undemonstrated
is the defect this whole concern is about, arriving one level up.

Read in both directions from one predicate. The live tree must produce no violation, and
every case must produce at least one. Neither direction alone is worth much: a check that
cannot fail is not a check, and a check that convicts correct code is worse than the gap
it covers - a substring-parity guard was withdrawn from this package for exactly that.
"""

from __future__ import annotations

from pathlib import Path
import ast
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovprompts.audit import violations  # noqa: E402

WORKFLOWS = ROOT / ".claude" / "workflows"
CORPUS = Path(__file__).resolve().parent / "fixtures" / "witness-context-defeats.json"


def live() -> dict[str, str]:
    return {path.name: path.read_text(encoding="utf-8")
            for path in sorted(WORKFLOWS.glob("*.js"))}


def mutated(case: dict) -> dict[str, str]:
    """Just the one workflow a case mutates, with its mutation applied, in memory only.

    One file rather than the whole tree: every case is confined to a single workflow, and
    re-grading the twenty-two it does not touch cost forty seconds of the verification
    budget to reach the same answer. `TheLiveTreeIsClean` grades all of them.
    """
    sources = live()
    name = case["file"]
    source = sources[name]
    for key in ("also_replace", "replace"):
        patch = case.get(key)
        if not patch:
            continue
        if patch["old"] not in source:
            raise AssertionError(f"{case['id']}: anchor not found in {name}")
        source = source.replace(patch["old"], patch["new"], 1)
    if "append" in case:
        source = source + case["append"]
    return {name: source}


class TheCorpusIsWellFormed(unittest.TestCase):
    def test_every_case_is_declared_completely(self):
        cases = json.loads(CORPUS.read_text(encoding="utf-8"))["cases"]
        # Contiguous, not a floor. This asserted `len(cases) >= 29` while fifty-five
        # existed, so twenty-six could be deleted and the suite would still pass - a
        # check reading a declaration where it could measure, which is the defect this
        # whole concern is about. An independent reading found it. Ids run D1..Dn with
        # no gaps, so removing a case is visible whichever one goes.
        numbers = sorted(int(case["id"][1:]) for case in cases)
        self.assertEqual(numbers, list(range(1, len(cases) + 1)),
                         "case ids must run D1..Dn with no gaps; a deleted case shows here")
        seen = set()
        for case in cases:
            for field in ("id", "found_by_reading", "shows", "expects", "file"):
                self.assertIn(field, case, f"{case.get('id')}: missing {field}")
            self.assertNotIn(case["id"], seen, f"duplicate case id {case['id']}")
            seen.add(case["id"])
            self.assertTrue("append" in case or "replace" in case,
                            f"{case['id']} mutates nothing")
            self.assertIn(case["file"], live(), f"{case['id']} names a workflow that is gone")


class TheLiveTreeIsClean(unittest.TestCase):
    def test_no_workflow_breaks_the_rule(self):
        """The other direction. A corpus that only ever fires proves nothing about the
        tree it is supposed to protect."""
        self.assertEqual(violations(live()), [])


class EveryDefeatStillFails(unittest.TestCase):
    def test_each_recorded_defeat_is_refused_for_its_own_reason(self):
        """The case that matters, and it grades which refusal fires rather than how many.

        An earlier form asserted only that some violation appeared. An independent reading
        found the consequence: one case was not valid JavaScript, so it fired on the
        readability branch and `audit.violations` never reached the branch the case existed
        to demonstrate. It passed, and read as coverage of a refusal nothing exercised.
        Counting refusals instead of naming them is the same defect this whole concern is
        about - measuring a proxy for the thing rather than the thing.
        """
        cases = json.loads(CORPUS.read_text(encoding="utf-8"))["cases"]
        wrong = []
        for case in cases:
            found = violations(mutated(case))
            if not found:
                wrong.append(f"{case['id']} (reading {case['found_by_reading']}) is no "
                             f"longer refused at all: {case['shows']}")
            elif not any(case["expects"] in violation for violation in found):
                wrong.append(f"{case['id']} fires, but on the wrong refusal. Expected "
                             f"{case['expects']!r}; got {found}")
        self.assertEqual(wrong, [], "corpus cases not doing what they claim:\n  "
                                    + "\n  ".join(wrong))


#: Refusals `violations` cannot reach, each with the gate that pre-empts it. A refusal
#: belongs here only when an earlier check refuses the same source first, never because a
#: case was not written. An independent reading found eleven refusals in this package with
#: no case firing them, and no way to tell which were undemonstrated and which were
#: unreachable; that distinction is what this register records and the case below enforces.
UNREACHABLE = {
    "has no closing brace":
        "the body is balanced on the mask now, so a `{` inside a string is not a brace and "
        "a genuinely unbalanced one is refused by lexer.unreadable before any rule reads "
        "the function",
    "no function named":
        "`resolved_prompt` treats a name that is not a local function as an expression "
        "rather than as indirection, so the message never reaches a caller that reports it",
    "unterminated string literal":
        "lexer.unreadable refuses an unclosed string before `_literals` reads it",
    "unterminated comment":
        "lexer.unreadable refuses an unclosed block comment before `_literals` reads it",
    "cannot read expression at":
        "reached only from a prompt slice that opens on a delimiter, and `prompt_of` now "
        "returns whole arguments, so no slice can begin part-way through one",
    "what this prompt delivers cannot be read":
        "every way `_literals` refuses is pre-empted: an unclosed string, regex or comment "
        "is refused by lexer.unreadable, and its remaining refusal needs a slice that opens "
        "part-way through an expression, which `prompt_of` no longer produces now that it "
        "returns whole arguments. Kept as the fail-closed branch it is; a reading that "
        "reaches it defeats this entry, which is the point of recording it",
    "a regex literal opens and never closes":
        "an unclosed regex reaching the end of the file is refused one line earlier by the "
        "line-ended check inside the same reader, which the corpus fires as D64",
}

#: Message text this reads as a refusal. Matched against the literals in each module, so a
#: refusal added without a case is a build failure rather than something a reading has to
#: find again.
REFUSAL_SOURCES = ("audit.py", "bindings.py", "calls.py", "dispatch.py", "frames.py",
                   "lexer.py", "names.py", "render.py", "scan.py")


class EveryRefusalIsDemonstrated(unittest.TestCase):
    def test_no_refusal_ships_without_a_case_or_a_recorded_reason(self):
        """The rule this package states, applied to the package.

        Its own docstrings invoke `SDLC.md` gate 3 against undemonstrated refusals, and an
        independent reading counted eleven of its own. Prose could not tell an
        undemonstrated refusal from an unreachable one, so the distinction is recorded in
        `UNREACHABLE` with the gate that pre-empts each, and everything else must fire.

        Read from the syntax tree rather than by matching quoted text. A regex over the
        source collected constants, docstring sentences and a character class alongside the
        refusals, which is a check reading whatever its pattern happened to catch. This
        collects the literal parts of every string handed to `Unreadable(...)` or appended
        to a violation list, which is where a refusal in this package is written.
        """
        cases = json.loads(CORPUS.read_text(encoding="utf-8"))["cases"]
        fired: list[str] = []
        for case in cases:
            fired.extend(violations(mutated(case)))
        messages: list[str] = []
        for name in REFUSAL_SOURCES:
            module = ROOT / "scripts" / "sovprompts" / name
            messages.extend(_refusal_texts(module.read_text(encoding="utf-8")))
        # A register entry naming no refusal this package still states is an assertion
        # about nothing, and it silently exempts whatever it happens to match next. An
        # independent reading found five entries claiming a gate that did not exist.
        stale = [reason for reason in UNREACHABLE
                 if not any(reason in message for message in messages)]
        self.assertEqual(sorted(stale), [],
                         "UNREACHABLE names refusals this package no longer states:\n  "
                         + "\n  ".join(sorted(stale)))
        undemonstrated = []
        for name in REFUSAL_SOURCES:
            module = ROOT / "scripts" / "sovprompts" / name
            for fragment in _refusal_texts(module.read_text(encoding="utf-8")):
                if any(reason in fragment for reason in UNREACHABLE):
                    continue
                if not any(fragment in violation for violation in fired):
                    undemonstrated.append(f"{name}: {fragment[:70]}")
        self.assertEqual(sorted(undemonstrated), [],
                         "refusals with no case firing them, and no recorded reason they "
                         "cannot be reached:\n  " + "\n  ".join(sorted(undemonstrated)))


def _refusal_texts(source: str) -> list[str]:
    """Every message this module can refuse with, read out of its syntax tree.

    A refusal here is a string handed to `Unreadable(...)`, appended to a violation list,
    or returned - `lexer.unreadable` states its refusals as return values. Only the literal
    parts are returned, and only the ones long enough to identify a message: an f-string's
    interpolated values are runtime text and cannot be matched against a recorded
    violation.
    """
    out: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Return) and node.value is not None:
            out.extend(_literal_parts(node.value))
            continue
        if not isinstance(node, ast.Call):
            continue
        named = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
        if named not in {"Unreadable", "Broken", "append"}:
            continue
        for argument in node.args:
            out.extend(_literal_parts(argument))
    return [text for text in out if len(text) >= 16]


def _literal_parts(node: ast.AST) -> list[str]:
    """The parts of a string expression that are literal text, concatenation included."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value.strip()]
    if isinstance(node, ast.JoinedStr):
        return [part.value.strip() for part in node.values
                if isinstance(part, ast.Constant) and isinstance(part.value, str)]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _literal_parts(node.left) + _literal_parts(node.right)
    return []

if __name__ == "__main__":
    unittest.main()
