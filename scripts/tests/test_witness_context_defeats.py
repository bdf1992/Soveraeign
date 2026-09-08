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


if __name__ == "__main__":
    unittest.main()
