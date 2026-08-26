"""Pin the distinction between a reachable Host read and independent observation."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovnode.bindings import resolve  # noqa: E402
from sovnode.interface_inputs import rebuild  # noqa: E402


class HostObservationClaim(unittest.TestCase):
    def test_reachable_host_read_remains_explicitly_unobserved(self) -> None:
        document, defects = rebuild()
        self.assertEqual(defects, [])

        record = resolve(document, "host.read-health")
        self.assertTrue(record["facts"]["reachable"])
        self.assertFalse(record["facts"]["observed"])
        self.assertEqual(record["observation_ids"], [])
        self.assertIn(
            "host.read-health",
            document["seams"]["reachable_not_observed"],
        )


if __name__ == "__main__":
    unittest.main()
