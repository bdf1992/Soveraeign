from __future__ import annotations

from pathlib import Path
import sys
import unittest

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

from sovenv.model import (
    EnvironmentRefused,
    admit_crossing,
    instantiate_environment,
    instantiate_trunk,
    land_crossing,
    load_json,
    new_state,
    propose_crossing,
    resolve_selector,
    validate_pattern,
)

FIXTURES = ROOT / "conformance" / "fixtures" / "environment"


def software() -> tuple[dict[str, object], dict[str, object]]:
    pattern = load_json(FIXTURES / "software-delivery.json")
    state = new_state(pattern)
    for definition, instance in (
        ("FEAT", "feat:a"),
        ("FEAT", "feat:b"),
        ("DEV", "dev"),
        ("RC", "rc"),
        ("PRODUCTION", "prod"),
    ):
        instantiate_environment(state, pattern, definition, instance)
    instantiate_trunk(state, pattern, "release", "release:main")
    return pattern, state


class PatternTests(unittest.TestCase):
    def test_both_patterns_are_generic_and_valid(self) -> None:
        for path in FIXTURES.glob("*.json"):
            self.assertEqual([], validate_pattern(load_json(path)), path.name)

    def test_names_are_not_engine_enums(self) -> None:
        pattern = load_json(FIXTURES / "pilot-delivery.json")
        state = new_state(pattern)
        instantiate_environment(state, pattern, "LOCAL", "local:7")
        instantiate_environment(state, pattern, "UAT", "uat:customer-a")
        self.assertEqual("UAT", state["environment_instances"][1]["definition_id"])

    def test_many_and_one_cardinality(self) -> None:
        pattern, state = software()
        instantiate_environment(state, pattern, "FEAT", "feat:c")
        with self.assertRaisesRegex(
            EnvironmentRefused, "ENVIRONMENT_MULTIPLICITY_EXCEEDED"
        ):
            instantiate_environment(state, pattern, "DEV", "dev:other")


class CrossingTests(unittest.TestCase):
    def proposal(self) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
        pattern, state = software()
        record = propose_crossing(
            state,
            pattern,
            trunk_instance="release:main",
            source_instance="feat:a",
            target_instance="dev",
            revision="abc123",
            artifact_digest="sha256:candidate",
            config_digest="sha256:dev-config",
            actor="builder",
            integration_base="base1",
            evidence=["tests"],
        )
        return pattern, state, record

    def test_stale_base_revalidated_and_receipted(self) -> None:
        pattern, state, record = self.proposal()
        refused = admit_crossing(
            state,
            pattern,
            record["crossing_id"],
            current_integration_base="base2",
            witness="qa",
            authority="VERIFICATION",
        )
        self.assertEqual("REFUSED", refused["status"])
        self.assertEqual("STALE_ADMISSION_BASE", refused["receipt"]["reason"])
        self.assertEqual("abc123", refused["receipt"]["revision"])

    def test_builder_cannot_witness_self(self) -> None:
        pattern, state, record = self.proposal()
        refused = admit_crossing(
            state,
            pattern,
            record["crossing_id"],
            current_integration_base="base1",
            witness="builder",
            authority="VERIFICATION",
        )
        self.assertEqual("SELF_WITNESS_FORBIDDEN", refused["receipt"]["reason"])

    def test_green_evidence_does_not_self_admit(self) -> None:
        _, _, record = self.proposal()
        self.assertEqual("PROPOSED", record["status"])

    def test_environment_name_does_not_grant_authority(self) -> None:
        pattern, state, _ = self.proposal()
        record = propose_crossing(
            state,
            pattern,
            trunk_instance="release:main",
            source_instance="rc",
            target_instance="prod",
            revision="p1",
            artifact_digest="sha256:p1",
            config_digest="sha256:prod",
            actor="release",
            integration_base="base",
            evidence=["qualification", "acceptance"],
        )
        refused = admit_crossing(
            state,
            pattern,
            record["crossing_id"],
            current_integration_base="base",
            witness="qa",
            authority="VERIFICATION",
            accepted=True,
        )
        self.assertEqual("REQUIRED_AUTHORITY_MISSING", refused["receipt"]["reason"])

    def test_ci_green_cannot_fabricate_production_acceptance(self) -> None:
        pattern, state, _ = self.proposal()
        record = propose_crossing(
            state,
            pattern,
            trunk_instance="release:main",
            source_instance="rc",
            target_instance="prod",
            revision="p1",
            artifact_digest="sha256:p1",
            config_digest="sha256:prod",
            actor="release",
            integration_base="base",
            evidence=["qualification", "acceptance"],
        )
        refused = admit_crossing(
            state,
            pattern,
            record["crossing_id"],
            current_integration_base="base",
            witness="owner-witness",
            authority="JUDGEMENT",
            accepted=None,
        )
        self.assertEqual("EXPLICIT_ACCEPTANCE_REQUIRED", refused["receipt"]["reason"])

    def test_integration_crossing_is_serialized(self) -> None:
        pattern, state, first = self.proposal()
        admit_crossing(
            state,
            pattern,
            first["crossing_id"],
            current_integration_base="base1",
            witness="qa",
            authority="VERIFICATION",
        )
        second = propose_crossing(
            state,
            pattern,
            trunk_instance="release:main",
            source_instance="feat:b",
            target_instance="dev",
            revision="def456",
            artifact_digest="sha256:other",
            config_digest="sha256:dev-config",
            actor="builder2",
            integration_base="base1",
            evidence=["tests"],
        )
        refused = admit_crossing(
            state,
            pattern,
            second["crossing_id"],
            current_integration_base="base1",
            witness="qa2",
            authority="VERIFICATION",
        )
        self.assertEqual("INTEGRATION_CROSSING_BUSY", refused["receipt"]["reason"])

    def test_exact_candidate_identity_moves(self) -> None:
        pattern, state, record = self.proposal()
        admit_crossing(
            state,
            pattern,
            record["crossing_id"],
            current_integration_base="base1",
            witness="qa",
            authority="VERIFICATION",
        )
        refused = land_crossing(state, record["crossing_id"], landing_revision="rebuilt")
        self.assertEqual("CANDIDATE_IDENTITY_CHANGED", refused["receipt"]["reason"])

    def test_receipts_are_append_preserving(self) -> None:
        pattern, state, record = self.proposal()
        admitted = admit_crossing(
            state,
            pattern,
            record["crossing_id"],
            current_integration_base="base1",
            witness="qa",
            authority="VERIFICATION",
        )
        admission_receipt = admitted["receipt"]["receipt_id"]
        land_crossing(state, record["crossing_id"], landing_revision="abc123")
        self.assertEqual(2, len(state["receipts"]))
        self.assertEqual(admission_receipt, record["receipt_ids"][0])
        self.assertEqual(2, len(record["receipt_ids"]))

    def test_latest_prior_are_history_selectors(self) -> None:
        pattern, state = software()
        for revision in ("p1", "p2"):
            record = propose_crossing(
                state,
                pattern,
                trunk_instance="release:main",
                source_instance="rc",
                target_instance="prod",
                revision=revision,
                artifact_digest=f"sha256:{revision}",
                config_digest="sha256:prod",
                actor="release",
                integration_base="base",
                evidence=["qualification", "acceptance"],
            )
            admit_crossing(
                state,
                pattern,
                record["crossing_id"],
                current_integration_base="base",
                witness="owner-witness",
                authority="JUDGEMENT",
                accepted=True,
            )
            land_crossing(state, record["crossing_id"], landing_revision=revision)
        self.assertEqual("p2", resolve_selector(state, pattern, "LATEST")["revision"])
        self.assertEqual("p1", resolve_selector(state, pattern, "PRIOR")["revision"])


if __name__ == "__main__":
    unittest.main()
