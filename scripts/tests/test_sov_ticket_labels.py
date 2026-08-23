"""Unit tests for the ticket label projection.

Labels are a projection of issue metadata (``CONTRIBUTING.md``). These tests keep the
declared projection, the canonical catalogue, and the drift detector from parting ways.
"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovticket import labels as labelmod  # noqa: E402


class LabelProjectionTests(unittest.TestCase):
    """Every label the projection can emit is declared in the canonical catalogue."""

    def setUp(self) -> None:
        self.projection = labelmod.load_projection(ROOT)
        self.catalogue = labelmod.load_catalogue(ROOT)

    def test_catalogue_is_not_empty(self) -> None:
        self.assertGreater(len(self.catalogue), 20)

    def test_every_projectable_label_is_declared(self) -> None:
        emitted = set()
        for key in (
            "kind_to_type",
            "village_to_label",
            "horizon_to_label",
            "effect_to_label",
            "standing_to_label",
            "standing_to_witness_label",
            "kind_to_scope",
            "provision_to_label",
            "serve_to_label",
        ):
            emitted.update(value for value in self.projection[key].values() if value)
        undeclared = emitted - self.catalogue
        self.assertEqual(undeclared, set(), f"projected labels missing from .github/labels.yml: {undeclared}")

    def test_record_local_is_the_omitted_default(self) -> None:
        self.assertIsNone(self.projection["effect_to_label"]["RECORD_LOCAL"])

    def test_drift_is_detected_in_both_directions(self) -> None:
        metadata = {"kind": "bit", "village": "ground-and-evidence", "horizon": "NOW", "standing": "OPEN"}
        drift = labelmod.compare("#9", metadata, ["type: village", "horizon: now"], self.projection)
        self.assertIn("type: bit", drift.missing)
        self.assertIn("type: village", drift.unexpected)
        self.assertFalse(drift.clean)

    def test_unmapped_metadata_is_reported_not_ignored(self) -> None:
        _, unmapped = labelmod.project({"effect_class": "EXTERNAL_WORLD"}, self.projection)
        self.assertIn("effect_class=EXTERNAL_WORLD", unmapped)

    def test_unblock_request_projects_its_provision_and_serving_tier(self) -> None:
        metadata = {
            "kind": "unblock", "village": "trust-and-control", "horizon": "NOW",
            "standing": "PROPOSED", "effect_class": "REQUEST_ONLY",
            "requested_provision": "judgement", "requested_from": "owner",
        }
        labels, unmapped = labelmod.project(metadata, self.projection)
        self.assertEqual(unmapped, [])
        self.assertIn("type: unblock", labels)
        self.assertIn("provision: judgement", labels)
        self.assertIn("serve: owner", labels)

    def test_unblock_request_projects_its_provision_and_serving_tier(self) -> None:
        metadata = {
            "kind": "unblock", "village": "trust-and-control", "horizon": "NOW",
            "standing": "PROPOSED", "effect_class": "REQUEST_ONLY",
            "requested_provision": "judgement", "requested_from": "owner",
        }
        labels, unmapped = labelmod.project(metadata, self.projection)
        self.assertEqual(unmapped, [])
        self.assertIn("type: unblock", labels)
        self.assertIn("provision: judgement", labels)
        self.assertIn("serve: owner", labels)


if __name__ == "__main__":
    unittest.main()
