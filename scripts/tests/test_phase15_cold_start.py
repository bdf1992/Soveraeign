"""Focused cold-start cases for the prepared Phase 1.5 operating substrate."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_next  # noqa: E402
from sovsession import brief  # noqa: E402


def lease(lease_id: str, session: str, state: str = "HELD", effect: str = "RECORD_LOCAL") -> dict:
    return {
        "lease_id": lease_id,
        "state": state,
        "concern": {"kind": "concern", "reference": "concern:test",
                    "capability": "record.project-evidence"},
        "holder": {"session": session, "principal_id": f"principal:{session}",
                   "relation": "PARENT"},
        "grant": {"grant_id": None, "effect_ceiling": effect},
    }


class SessionLeaseProjection(unittest.TestCase):
    def test_only_live_leases_held_by_this_session_are_projected(self) -> None:
        projected = {
            "lease:a": lease("lease:a", "alpha"),
            "lease:b": lease("lease:b", "beta"),
            "lease:c": lease("lease:c", "alpha", state="COMPLETED"),
        }
        rows = brief.session_leases(projected, "alpha", "principal:alpha")
        self.assertEqual([row["lease_id"] for row in rows], ["lease:a"])

    def test_principal_join_recovers_a_lease_without_session_field(self) -> None:
        row = lease("lease:a", "alpha")
        row["holder"]["session"] = None
        rows = brief.session_leases({"lease:a": row}, "different", "principal:alpha")
        self.assertEqual([item["lease_id"] for item in rows], ["lease:a"])

    def test_brief_renders_actual_capability_grant_and_effect_from_lease(self) -> None:
        lines: list[str] = []
        brief._lease_context(lines, {"leases": [lease("lease:a", "alpha")]})
        rendered = "\n".join(lines)
        self.assertIn("record.project-evidence", rendered)
        self.assertIn("grant NONE", rendered)
        self.assertIn("effect ceiling RECORD_LOCAL", rendered)


class NextWorkPrecedence(unittest.TestCase):
    def test_prepared_horizon_is_discovered_without_becoming_phase_state(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "contracts").mkdir()
            (root / "contracts" / "phase-1-5-phase-ii-horizon.md").write_text("prepared\n")
            self.assertEqual(sov_next.prepared_horizons(root),
                             ["contracts/phase-1-5-phase-ii-horizon.md"])

    def test_active_custody_members_preserve_arbitrary_member_kinds(self) -> None:
        custodies = [{
            "custody_id": "custody:test",
            "members": [
                {"member_kind": "TICKET", "address": "issue:#7", "stage": "ROOT_POINT",
                 "standing": "OPEN", "work_state": "READY"},
                {"member_kind": "OPERATION", "address": "sov://new/do-thing",
                 "stage": "VERTICAL_SLICE", "standing": "BUILT",
                 "work_state": "IN_PROGRESS"},
            ],
        }]
        ready = [{"number": "7", "title": "ticket", "standing": "OPEN", "horizon": "NOW"}]
        rows = sov_next.active_custody_members(custodies, ready)
        self.assertEqual([row["address"] for row in rows], ["issue:#7", "sov://new/do-thing"])
        self.assertTrue(rows[0]["epic_reachable"])
        self.assertFalse(rows[1]["epic_reachable"])

    def test_terminal_custody_and_retired_member_do_not_appear_as_active_work(self) -> None:
        custodies = [
            {"custody_id": "custody:terminal", "terminal": {"outcome": "SETTLED"},
             "members": [{"address": "issue:#1", "work_state": "READY"}]},
            {"custody_id": "custody:live", "members": [
                {"member_kind": "ITEM", "address": "thing:old", "stage": "ROOT_POINT",
                 "standing": "OPEN", "work_state": "RETIRED"}]},
        ]
        self.assertEqual(sov_next.active_custody_members(custodies, []), [])


class RepositoryContract(unittest.TestCase):
    def test_agent_contract_does_not_hardcode_current_phase(self) -> None:
        text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertNotIn("No phase is active.", text)
        self.assertIn("Never hardcode an assumed active phase", text)

    def test_sov_orders_context_before_operation(self) -> None:
        text = (ROOT / "SOV.md").read_text(encoding="utf-8")
        order = [text.index(token) for token in (
            "**Session.**", "**Phase authority.**", "**Assigned work.**",
            "**Capability.**", "**Authority and effect.**", "**Record context.**",
            "**Operation.**")]
        self.assertEqual(order, sorted(order))


if __name__ == "__main__":
    unittest.main()
