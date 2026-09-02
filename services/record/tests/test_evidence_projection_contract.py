"""Prove ``evidence_projection()`` and ``record-projection.schema.json`` agree.

The code derives a projection; the schema declares what one must be. Nothing else
in the repository checks the two against each other, so this validates a produced
projection against the schema and recomputes its digest by the same rule the code
uses, from outside the module, without importing a private helper.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from sovkernel.jsonschema import validate  # noqa: E402

from soveraeign_record_service import RecordService, UnknownEntry  # noqa: E402

SCHEMA = json.loads((ROOT / "contracts" / "record-projection.schema.json").read_text("utf-8"))


class EvidenceProjectionContract(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.service = RecordService(Path(self.tmp.name) / "record")
        self.first = self.service.append("EVENT", "work:81", "worker:17", {"step": "build"})
        self.second = self.service.append(
            "OBSERVATION", "work:81", "witness:4", {"verdict": "CONFIRMED"})
        self.third = self.service.append(
            "RECEIPT", "work:81", "worker:17", {"outcome": "done"})
        self.other = self.service.append("EVENT", "work:99", "worker:8", {"step": "other"})

    def tearDown(self) -> None:
        self.service.close()
        self.tmp.cleanup()

    def project(self, **kwargs):
        return self.service.evidence_projection(
            ["work:81"], "principal:witness-4", "witness", "independent work review",
            **kwargs,
        )

    def test_projection_validates_against_the_schema(self) -> None:
        projected = self.project()
        defects = validate(projected, SCHEMA)
        self.assertEqual(defects, [])

    def test_authority_effect_and_digest_shape(self) -> None:
        projected = self.project()
        self.assertEqual(projected["authority_effect"], "NONE")
        self.assertRegex(projected["projection_digest"], r"^sha256:[0-9a-f]{64}$")

    def test_digest_is_independently_reproducible(self) -> None:
        projected = self.project()
        basis = {key: value for key, value in projected.items()
                  if key not in ("projection_id", "projection_digest")}
        encoded = json.dumps(basis, sort_keys=True, separators=(",", ":"),
                              ensure_ascii=False).encode("utf-8")
        recomputed = "sha256:" + sha256(encoded).hexdigest()
        self.assertEqual(recomputed, projected["projection_digest"])
        self.assertEqual(
            projected["projection_id"],
            "urn:soveraeign:record-projection:" + recomputed.removeprefix("sha256:"),
        )

    def test_exclude_kind_absent_from_journal_yields_no_omission(self) -> None:
        projected = self.project(exclude_kinds=["COUNTER"])
        self.assertEqual(projected["omissions"], [])
        defects = validate(projected, SCHEMA)
        self.assertEqual(defects, [])

    def test_empty_inclusion_refuses_instead_of_emitting_a_bad_shape(self) -> None:
        with self.assertRaises(UnknownEntry):
            self.project(exclude_kinds=["EVENT", "OBSERVATION", "RECEIPT"])


if __name__ == "__main__":
    unittest.main()
