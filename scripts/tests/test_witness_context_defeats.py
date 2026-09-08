"""Run every construction that ever defeated the witness-context check, and require it to fail.

Twenty-nine cases from seven independent readings. Until this module existed they were
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
        self.assertGreaterEqual(len(cases), 29)
        seen = set()
        for case in cases:
            for field in ("id", "found_by_reading", "shows", "file"):
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
    def test_each_recorded_defeat_is_refused(self):
        """The case that matters. Each of these passed the check when it was found."""
        cases = json.loads(CORPUS.read_text(encoding="utf-8"))["cases"]
        survived = []
        for case in cases:
            if not violations(mutated(case)):
                survived.append(f"{case['id']} (reading {case['found_by_reading']}): "
                                f"{case['shows']}")
        self.assertEqual(survived, [], "constructions the check no longer refuses:\n  "
                                       + "\n  ".join(survived))


if __name__ == "__main__":
    unittest.main()
