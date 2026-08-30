from __future__ import annotations

import unittest

from scripts.sovcustody import lifecycle


class CustodyLifecycleTests(unittest.TestCase):
    def test_declared_lifecycle_is_admissible(self) -> None:
        self.assertEqual([], lifecycle.defects())

    def test_custody_and_lease_are_separate_roles(self) -> None:
        model = lifecycle.read()
        roles = model["roles"]
        self.assertIn("Durable accountability", roles["CUSTODY"]["means"])
        self.assertIn("Temporary active possession", roles["LEASE"]["means"])
        self.assertNotEqual(roles["CUSTODY"]["owned_by"], roles["LEASE"]["owned_by"])

    def test_lifecycle_keeps_integration_before_settlement(self) -> None:
        steps = [row["step"] for row in lifecycle.read()["flow"]]
        self.assertEqual(
            ["ADMIT", "TAKE", "WORK", "INTEGRATE", "RECONCILE", "RELEASE_ATTENTION"],
            steps,
        )

    def test_queue_is_projection_not_owner(self) -> None:
        queue = lifecycle.read()["queue_projection"]
        self.assertFalse(queue["owns_work"])
        self.assertFalse(queue["selection_is_authority"])

    def test_wake_preserves_focus_and_responsibility(self) -> None:
        wake = lifecycle.read()["wake_policy"]
        self.assertEqual(
            {"same_service", "same_effect_class", "same_authority"},
            set(wake["absorb_when"]),
        )
        self.assertIn("does not take a work lease", wake["separate_rule"])
        self.assertIn("under valid custody", wake["close_rule"])

    def test_future_features_are_explicitly_not_all_current(self) -> None:
        potentials = {row["id"]: row["status"] for row in lifecycle.read()["potential_extensions"]}
        self.assertEqual("CHARTED", potentials["STATE_PINNED_PROMISE"])
        self.assertEqual("PARTIAL", potentials["CAUSAL_CUSTODY_EDGES"])
        self.assertEqual("CHARTED", potentials["UNCUSTODIED_WAKE_CHECK"])


if __name__ == "__main__":
    unittest.main()
