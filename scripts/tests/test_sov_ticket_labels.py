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
            "kind_to_scope",
            "provision_to_label",
            "serve_to_label",
        ):
            emitted.update(value for value in self.projection[key].values() if value)
        undeclared = emitted - self.catalogue
        self.assertEqual(undeclared, set(), f"projected labels missing from .github/labels.yml: {undeclared}")

    def test_the_standing_ramp_covers_every_declared_standing(self) -> None:
        """Every standing in the issue schema projects to at most one label, and none is unmapped."""
        import json as _json

        path = ROOT / "contracts" / "issue-metadata.schema.json"
        schema = _json.loads(path.read_text(encoding="utf-8"))
        declared = set(schema["properties"]["standing"]["enum"])
        self.assertEqual(declared, set(self.projection["standing_to_label"]))
        for standing in declared:
            labels, unmapped = labelmod.project({"standing": standing}, self.projection)
            self.assertEqual(unmapped, [], f"{standing} is unmapped")
            standing_labels = {name for name in labels if name.startswith("standing:")}
            self.assertLessEqual(len(standing_labels), 1, f"{standing} projects to {standing_labels}")

    def test_a_retired_axis_label_reads_as_drift(self) -> None:
        """A surviving witness: label is unexpected, not invisible."""
        for prefix in self.projection["retired_label_prefixes"]:
            self.assertIn(prefix, self.projection["unprojected_label_prefixes"])
        metadata = {"kind": "bit", "village": "ground-and-evidence", "horizon": "NOW", "standing": "WITNESSED"}
        live = ["type: bit", "village: ground", "horizon: now", "standing: witnessed", "witness: witnessed"]
        drift = labelmod.compare("#7", metadata, live, self.projection)
        self.assertEqual(drift.unexpected, ("witness: witnessed",))
        self.assertEqual(drift.missing, ())

    def test_no_retired_label_remains_in_the_catalogue(self) -> None:
        for prefix in self.projection["retired_label_prefixes"]:
            surviving = {name for name in self.catalogue if name.startswith(prefix)}
            self.assertEqual(surviving, set(), f"{prefix} is retired but still declared: {surviving}")

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
