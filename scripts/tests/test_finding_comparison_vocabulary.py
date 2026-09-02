"""The comparison classification vocabulary must not drift from its two sources.

``contracts/finding-comparison.json`` is a projection of the classification codes
literally declared in ``.claude/workflows/sov-loop.js`` and
``.claude/agents/sov-controller.md``. Parsing those two files rather than
hardcoding the code list is the point: a hardcoded list cannot detect drift when
either source changes.
"""

from __future__ import annotations

from pathlib import Path
import json
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sovfinding import comparison  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "contracts" / "finding-comparison.json"
LOOP_JS_PATH = ROOT / ".claude" / "workflows" / "sov-loop.js"
CONTROLLER_MD_PATH = ROOT / ".claude" / "agents" / "sov-controller.md"

_CODE_TOKEN = r"[A-Z][A-Z_]*"


def _contract_codes() -> set[str]:
    return {entry["code"] for entry in json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))["classifications"]}


def _loop_js_codes() -> set[str]:
    text = LOOP_JS_PATH.read_text(encoding="utf-8")
    match = re.search(r"Use only these classifications: ([^.]+)\.", text)
    codes = re.findall(_CODE_TOKEN, match.group(1))
    return set(codes)


def _controller_md_codes() -> set[str]:
    text = CONTROLLER_MD_PATH.read_text(encoding="utf-8")
    match = re.search(
        r"Classify what the evidence establishes using only:\s*(.+?)\.\s", text, re.DOTALL
    )
    codes = re.findall(_CODE_TOKEN, match.group(1))
    return set(codes)


class FindingComparisonVocabularyTest(unittest.TestCase):
    def test_contract_matches_both_loose_sources(self) -> None:
        contract_codes = _contract_codes()
        loop_js_codes = _loop_js_codes()
        controller_md_codes = _controller_md_codes()

        self.assertTrue(loop_js_codes, "no classification codes parsed out of sov-loop.js")
        self.assertTrue(controller_md_codes, "no classification codes parsed out of sov-controller.md")
        self.assertEqual(contract_codes, loop_js_codes)
        self.assertEqual(contract_codes, controller_md_codes)

    def test_glossed_entries_carry_a_non_empty_meaning(self) -> None:
        for entry in comparison.CLASSIFICATIONS:
            if entry["meaning"] is not None:
                self.assertIsInstance(entry["meaning"], str)
                self.assertNotEqual(entry["meaning"].strip(), "")


if __name__ == "__main__":
    unittest.main()
