"""Unit tests for the unblock draft filer.

A stall that cannot prove itself is refused before it becomes a queued
request; a proven one round-trips through the registrar's own parser.
"""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_unblock  # noqa: E402
from sovticket.yamlblock import load_ticket  # noqa: E402

GOOD = [
    "draft",
    "--held", "#41",
    "--village", "trust-and-control",
    "--village-issue", "#3",
    "--parent", "#3",
    "--blocked-transition", "projection.ratify_boundary",
    "--missing-precondition", "a live JUDGEMENT grant naming the boundary",
    "--governing-rule", "STATUS.yaml O21 gates",
    "--provision", "judgement",
    "--requested-by", "controller",
    "--requested-from", "owner",
    "--unblock-condition", "decisions/0021 standing reads RATIFIED with an owner receipt",
]


class DraftTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.drafts = Path(self.tmp.name) / "unblocks"
        self.patch = mock.patch.object(sov_unblock, "DRAFTS", self.drafts)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.addCleanup(self.tmp.cleanup)

    def test_valid_claim_writes_a_parseable_draft(self) -> None:
        self.assertEqual(sov_unblock.main(GOOD), 0)
        paths = list(self.drafts.glob("*.md"))
        self.assertEqual(len(paths), 1)
        metadata = load_ticket(paths[0].read_text(encoding="utf-8"))
        self.assertEqual(metadata["kind"], "unblock")
        self.assertEqual(metadata["held"], "#41")
        self.assertEqual(metadata["reachable_alternative"], "NONE")
        self.assertEqual(metadata["requested_from"], "owner")

    def test_judgement_asked_of_a_lesser_tier_is_refused(self) -> None:
        argv = list(GOOD)
        argv[argv.index("--requested-from") + 1] = "controller"
        self.assertEqual(sov_unblock.main(argv), 1)
        self.assertEqual(list(self.drafts.glob("*.md")), [])

    def test_existing_draft_is_not_silently_replaced(self) -> None:
        self.assertEqual(sov_unblock.main(GOOD), 0)
        self.assertEqual(sov_unblock.main(GOOD), 1)
        self.assertEqual(sov_unblock.main(GOOD + ["--force"]), 0)

    def test_malformed_held_ref_is_refused(self) -> None:
        argv = list(GOOD)
        argv[argv.index("--held") + 1] = "issue 41"
        self.assertEqual(sov_unblock.main(argv), 1)


if __name__ == "__main__":
    unittest.main()
