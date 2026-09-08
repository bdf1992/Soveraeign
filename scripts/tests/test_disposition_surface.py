from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts import disposition_surface as surface


class DispositionSurfaceTests(unittest.TestCase):
    def prediction(self, **changes):
        value = {
            "subject_kind": "human",
            "observation_ref": "fixture:001",
            "labels": [{"label": "requests-evidence", "confidence": 0.91}],
            "model_id": "example/small-classifier",
            "model_revision": "0123456789abcdef",
            "taxonomy_version": "soveraeign-disposition-surface-taxonomy/v0.1",
            "inference_revision": "surface-json-v0.1",
            "calibration_revision": "uncalibrated",
        }
        value.update(changes)
        return value

    def test_model_output_cannot_directly_update_construct(self):
        result = surface.validate_prediction(self.prediction())
        self.assertEqual("NOT_ADMITTED", result["direct_construct_update"])
        self.assertEqual("CANDIDATE_SURFACE_EVIDENCE", result["standing"])

    def test_unknown_or_latent_label_refuses(self):
        prediction = self.prediction(labels=[{"label": "invariant-fidelity", "confidence": 0.9}])
        with self.assertRaisesRegex(ValueError, "unknown surface label"):
            surface.validate_prediction(prediction)

    def test_low_confidence_becomes_abstention(self):
        prediction = self.prediction(labels=[{"label": "requests-evidence", "confidence": 0.59}])
        result = surface.validate_prediction(prediction, minimum_confidence=0.60)
        self.assertEqual("ABSTAIN", result["standing"])
        self.assertEqual([], result["accepted_labels"])
        self.assertEqual("BELOW_CONFIDENCE_THRESHOLD", result["rejected_labels"][0]["reason"])

    def test_model_revision_is_required(self):
        with self.assertRaisesRegex(ValueError, "pinned model identity"):
            surface.validate_prediction(self.prediction(model_revision=""))

    def test_taxonomy_version_mismatch_refuses(self):
        with self.assertRaisesRegex(ValueError, "taxonomy version mismatch"):
            surface.validate_prediction(self.prediction(taxonomy_version="v999"))

    def test_candidate_mapping_is_explicitly_unvalidated(self):
        result = surface.validate_prediction(self.prediction())
        mapped = surface.candidate_construct_evidence(result)
        self.assertEqual("evidence-threshold", mapped[0]["construct_id"])
        self.assertEqual(0.91, mapped[0]["candidate_value"])
        self.assertEqual("UNVALIDATED_MAPPING", mapped[0]["standing"])

    def test_surface_prediction_persists_with_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = surface.append_prediction(Path(tmp), self.prediction())
            self.assertTrue(first["record_digest"])
            payload = first["surface_prediction"]
            self.assertEqual("example/small-classifier", payload["model_id"])
            self.assertEqual("0123456789abcdef", payload["model_revision"])
            self.assertTrue(payload["taxonomy_digest"])


if __name__ == "__main__":
    unittest.main()
