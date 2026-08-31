from __future__ import annotations

from pathlib import Path
import json
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

from sovenv.model import (
    EnvironmentRefused,
    StateStore,
    bind_workspace,
    load_json,
    new_state,
    release_workspace,
)

FIXTURES = ROOT / "conformance" / "fixtures" / "environment"


def lease(
    lease_id: str = "lease:one",
    principal: str = "urn:soveraeign:principal:agent:one",
    fence: int = 1,
    state: str = "HELD",
    relation: str = "PARENT",
    parent_lease: str | None = None,
) -> dict[str, object]:
    record: dict[str, object] = {
        "lease_schema": "soveraeign-work-lease/v1",
        "status": "RATIFIED",
        "lease_id": lease_id,
        "concern": {"kind": "ticket", "reference": "#191"},
        "holder": {
            "principal_id": principal,
            "relation": relation,
            "parent_lease": parent_lease if relation != "PARENT" else None,
            "controller_principal": (
                None
                if relation == "PARENT"
                else "urn:soveraeign:principal:agent:controller"
            ),
            "definition": {
                "definition_id": "test-agent",
                "definition_kind": "agent",
                "provenance": "SYSTEM_AUTHORED",
                "version": "1",
            },
        },
        "grant": {
            "grant_id": None,
            "authority_type": None,
            "capabilities": [],
            "effect_ceiling": "RECORD_LOCAL",
        },
        "budget": {"consumption": [], "emission": []},
        "closure": {
            "condition": "the bounded Environment operation is complete",
            "defeating_evidence": "the operation escaped its declared workspace",
        },
        "fence": fence,
        "granted_at": "2026-08-30T00:00:00Z",
        "expires_at": "2099-01-01T00:00:00Z",
        "state": state,
    }
    if state == "COMPLETED":
        record["closure_evidence"] = {
            "receipt_id": "receipt:environment-built",
            "standing_reached": "BUILT",
            "evidence_addresses": ["scripts/tests/test_sov_env_store.py"],
        }
    return record


def software_state() -> dict[str, object]:
    return new_state(load_json(FIXTURES / "software-delivery.json"))


class LeaseSafetyTests(unittest.TestCase):
    def test_two_workers_cannot_share_workspace(self) -> None:
        state = software_state()
        bind_workspace(
            state, lease(), workspace="/tmp/w", branch="feat/a", base_revision="a"
        )
        with self.assertRaisesRegex(EnvironmentRefused, "WORKSPACE_ALREADY_LEASED"):
            bind_workspace(
                state,
                lease("lease:two", "urn:soveraeign:principal:agent:two"),
                workspace="/tmp/w",
                branch="feat/b",
                base_revision="a",
            )

    def test_work_lease_schema_is_consumed_not_reimplemented(self) -> None:
        state = software_state()
        malformed = lease()
        del malformed["budget"]
        with self.assertRaisesRegex(EnvironmentRefused, "missing required property 'budget'"):
            bind_workspace(
                state, malformed, workspace="/tmp/w", branch="feat/a", base_revision="a"
            )

    def test_work_lease_semantic_refusal_is_preserved(self) -> None:
        state = software_state()
        helper = lease(relation="HELPER", parent_lease="lease:parent")
        with self.assertRaisesRegex(EnvironmentRefused, "HELPER_WITHOUT_PARENT"):
            bind_workspace(
                state, helper, workspace="/tmp/w", branch="feat/a", base_revision="a"
            )

    def test_newer_fence_supersedes_old_binding(self) -> None:
        state = software_state()
        first = bind_workspace(
            state, lease(fence=1), workspace="/tmp/a", branch="feat/a", base_revision="a"
        )
        second = bind_workspace(
            state, lease(fence=2), workspace="/tmp/b", branch="feat/a", base_revision="b"
        )
        self.assertEqual("SUPERSEDED", first["status"])
        self.assertEqual("ACTIVE", second["status"])
        self.assertEqual(2, first["superseded_by_fence"])

    def test_stale_fence_is_refused(self) -> None:
        state = software_state()
        bind_workspace(
            state, lease(fence=2), workspace="/tmp/w", branch="feat/a", base_revision="a"
        )
        with self.assertRaisesRegex(EnvironmentRefused, "STALE_LEASE"):
            bind_workspace(
                state, lease(fence=1), workspace="/tmp/w2", branch="feat/a", base_revision="a"
            )

    def test_terminal_lease_releases_binding_projection(self) -> None:
        state = software_state()
        bind_workspace(
            state, lease(fence=2), workspace="/tmp/w", branch="feat/a", base_revision="a"
        )
        released = release_workspace(
            state, lease(fence=2, state="COMPLETED"), reason="lease completed"
        )
        self.assertEqual("RELEASED", released["status"])
        self.assertEqual("lease completed", released["release_reason"])

    def test_held_lease_cannot_claim_release(self) -> None:
        state = software_state()
        bind_workspace(
            state, lease(), workspace="/tmp/w", branch="feat/a", base_revision="a"
        )
        with self.assertRaisesRegex(EnvironmentRefused, "WORK_LEASE_STILL_HELD"):
            release_workspace(state, lease(), reason="not done")


class StoreTests(unittest.TestCase):
    def test_busy_state_write_refuses(self) -> None:
        state = software_state()
        with tempfile.TemporaryDirectory() as directory:
            store = StateStore(Path(directory) / "state.json")
            store.lock_path.write_text("other", encoding="utf-8")
            with self.assertRaisesRegex(EnvironmentRefused, "STATE_WRITE_BUSY"):
                store.write(state)

    def test_update_holds_lock_across_read_decision_and_write(self) -> None:
        state = software_state()
        with tempfile.TemporaryDirectory() as directory:
            store = StateStore(Path(directory) / "state.json")
            store.write(state)

            def mutate(current: dict[str, object]) -> None:
                with self.assertRaisesRegex(EnvironmentRefused, "STATE_WRITE_BUSY"):
                    store.update(lambda nested: nested.update({"sequence": 99}))
                current["sequence"] = 7

            store.update(mutate)
            self.assertEqual(7, store.read()["sequence"])

    def test_failed_update_does_not_publish_partial_state(self) -> None:
        state = software_state()
        with tempfile.TemporaryDirectory() as directory:
            store = StateStore(Path(directory) / "state.json")
            store.write(state)

            def fail(current: dict[str, object]) -> None:
                current["sequence"] = 99
                raise EnvironmentRefused("DEFEAT")

            with self.assertRaisesRegex(EnvironmentRefused, "DEFEAT"):
                store.update(fail)
            self.assertEqual(0, store.read()["sequence"])


class StateContractTests(unittest.TestCase):
    def test_state_contract_names_append_preserving_receipts(self) -> None:
        path = ROOT / "contracts" / "environment-state.schema.json"
        contract = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(
            "soveraeign-local-environment-state/v1",
            contract["properties"]["schema"]["const"],
        )
        self.assertIn("receipts", contract["required"])
        self.assertIn("workspace_bindings", contract["required"])


if __name__ == "__main__":
    unittest.main()
