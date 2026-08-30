from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class QueuedClarityCustodyTests(unittest.TestCase):
    def test_full_clarity_remainder_is_custodied_outside_phase_i(self) -> None:
        collection = json.loads((ROOT / "contracts" / "custodies.json").read_text(encoding="utf-8"))
        custody = next(
            row for row in collection["custodies"]
            if row["custody_id"] == "custody:clarity/current-prose"
        )
        self.assertIsNone(custody["phase"])
        self.assertIsNone(custody["serves_exit"])
        self.assertTrue(custody["outside_phase_exit"])
        self.assertEqual("python scripts/sov_clarity.py gate", custody["closure"]["check"]["expression"])
        ticket = next(row for row in custody["members"] if row["member_kind"] == "TICKET")
        self.assertEqual("issue:#186", ticket["address"])
        self.assertEqual("READY", ticket["work_state"])
        self.assertIn("takes no lease", ticket["note"])


if __name__ == "__main__":
    unittest.main()
