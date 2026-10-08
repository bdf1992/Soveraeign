"""Positive and defeating contract cases for the identity a decision retains."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sovaccept import review
from sovkernel.jsonschema import validate

ROOT = Path(__file__).resolve().parents[2]


class ReviewContract(unittest.TestCase):
    """Schema shape is separate from actual packet and subject hashing."""

    def test_both_polarities(self) -> None:
        corpus = json.loads((ROOT / "conformance/fixtures/acceptance/review-cases.json")
                            .read_text("utf-8"))
        schema = json.loads((ROOT / corpus["contract"]).read_text("utf-8"))
        self.assertEqual(validate(corpus["positive"], schema), [])
        for case in corpus["defeating"]:
            with self.subTest(case=case["remove"]):
                subject = copy.deepcopy(corpus["positive"])
                del subject[case["remove"]]
                self.assertTrue(validate(subject, schema), case["reason"])

    def test_capture_matches_schema_and_refuses_escape(self) -> None:
        schema = json.loads((ROOT / "contracts/acceptance-review.schema.json").read_text("utf-8"))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "result.txt").write_bytes(b"result")
            packet = {"packet_id": "A1", "subject": {"artifact": "result.txt"}}
            captured = review.capture(root, packet)
            self.assertEqual(validate(captured, schema), [])
            self.assertEqual(captured["subject"]["digest"], review.digest(b"result"))
            for path in (str(ROOT / "GROUND.md"), "../result.txt", "."):
                with self.subTest(path=path):
                    packet["subject"]["artifact"] = path
                    with self.assertRaisesRegex(review.AcceptanceError, "REVIEW_SUBJECT_UNAVAILABLE"):
                        review.capture(root, packet)


if __name__ == "__main__":
    unittest.main()
