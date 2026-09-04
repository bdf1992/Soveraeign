"""The carried bdos cores must still match the digests their decision records.

The decision is the provenance source. This test derives its expectations from that
existing table rather than creating a second registry of copied skill digests.
"""

from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DECISION = ROOT / "decisions/0103-carry-two-bdos-cores.md"
ROW = re.compile(
    r"^\| `(?P<skill>[a-z0-9-]+)` \| `(?P<digest>[0-9a-f]{64})` \|$",
    re.MULTILINE,
)


class CarriedBdosCoreProvenance(unittest.TestCase):
    """A byte copy that drifts without a decision defeats the carry ruling."""

    def test_every_recorded_copy_matches_its_decision_digest(self):
        text = DECISION.read_bytes().decode("utf-8")
        rows = {match.group("skill"): match.group("digest") for match in ROW.finditer(text)}
        self.assertTrue(rows, "decisions/0103 carries no parseable bdos digest rows")

        for skill, expected in rows.items():
            path = ROOT / ".claude" / "skills" / skill / "SKILL.md"
            with self.subTest(skill=skill):
                self.assertTrue(path.is_file(), f"recorded bdos core is absent: {path}")
                observed = hashlib.sha256(path.read_bytes()).hexdigest()
                self.assertEqual(expected, observed)


if __name__ == "__main__":
    unittest.main()
