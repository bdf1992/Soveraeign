from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from soveraeign_record_service import RecordService, UnknownEntry  # noqa: E402


class EvidenceProjection(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.service = RecordService(Path(self.tmp.name) / "record")
        self.first = self.service.append("EVENT", "work:81", "worker:17", {"step": "build"})
        self.second = self.service.append(
            "OBSERVATION", "work:81", "witness:4", {"verdict": "CONFIRMED"})
        self.other = self.service.append("EVENT", "work:99", "worker:8", {"step": "other"})

    def tearDown(self) -> None:
        self.service.close()
        self.tmp.cleanup()

    def project(self, **kwargs):
        return self.service.evidence_projection(
            ["work:81"], "principal:witness-4", "witness", "independent work review",
            **kwargs,
        )

    def test_projection_is_scoped_addressed_and_non_authoritative(self) -> None:
        projected = self.project()
        self.assertEqual(projected["subject_addresses"], ["work:81"])
        self.assertEqual(projected["authority_effect"], "NONE")
        self.assertEqual(
            [item["address"] for item in projected["included_records"]],
            ["record:" + self.first["entry_id"], "record:" + self.second["entry_id"]],
        )
        self.assertNotIn("record:" + self.other["entry_id"],
                         [item["address"] for item in projected["included_records"]])

    def test_same_basis_rebuilds_the_same_projection_identity(self) -> None:
        first = self.project()
        second = self.project()
        self.assertEqual(first, second)
        self.assertEqual(first["projection_id"].removeprefix("urn:soveraeign:record-projection:"),
                         first["projection_digest"].removeprefix("sha256:"))

    def test_cutoff_excludes_later_records_without_guessing(self) -> None:
        projected = self.project(as_of_entry=self.first["entry_id"])
        self.assertEqual(projected["as_of"], "record:" + self.first["entry_id"])
        self.assertEqual(len(projected["included_records"]), 1)
        self.assertEqual(projected["record_head"], "sha256:" + self.first["entry_digest"])

    def test_requested_omission_is_explicit(self) -> None:
        projected = self.project(exclude_kinds=["OBSERVATION"])
        self.assertEqual([item["record_class"] for item in projected["omissions"]],
                         ["OBSERVATION"])
        self.assertEqual(len(projected["included_records"]), 1)

    def test_unknown_cutoff_refuses(self) -> None:
        with self.assertRaises(UnknownEntry):
            self.project(as_of_entry="entry_missing")

    def test_no_matching_subject_refuses_instead_of_returning_empty_evidence(self) -> None:
        with self.assertRaises(UnknownEntry):
            self.service.evidence_projection(
                ["work:404"], "principal:witness-4", "witness", "review")

    def test_invalid_omission_class_refuses(self) -> None:
        with self.assertRaises(ValueError):
            self.project(exclude_kinds=["OPINION"])


if __name__ == "__main__":
    unittest.main()
