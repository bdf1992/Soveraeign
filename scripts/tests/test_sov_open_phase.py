"""Prove the Phase 1.5 opening packet, its custodies, and the opener script.

`sov_open_phase.py` never writes unless `--apply` is passed, and `--apply
--dry-run` must compute the exact write without touching a byte on disk. That
last claim is only trustworthy if something outside the script proves it, so
this suite digests the two target files before and after a dry run and
compares them, rather than trusting the script's own report.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import shutil
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_open_phase  # noqa: E402
from sovkernel.jsonschema import validate  # noqa: E402

RELATIVE_FILES = (
    "STATUS.yaml",
    "archives/PRD-PHASE-1-5-OPENING.txt",
    "archives/SPEC-PHASE-1-5-OPENING.txt",
    "archives/HORIZON-PHASE-1-5-OPENING.txt",
    "contracts/phase-1-5-opening.json",
    "contracts/custodies-phase-1-5.json",
    "contracts/phases.json",
    "contracts/custodies.json",
)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stage(tmp: str) -> Path:
    """Copy the target files into a fresh root, normalized to unopened standing.

    The live tree may already carry the opened phase, so this fixture is
    forced back to the pre-opening state rather than trusting the working
    tree's current phase reading. That keeps these cases asserting the
    script's own behaviour, not the repository's current standing.
    """
    root = Path(tmp)
    for relative in RELATIVE_FILES:
        source = ROOT / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    status_path = root / "STATUS.yaml"
    lines = status_path.read_text(encoding="utf-8").splitlines()
    lines = ["phase: NONE_ACTIVE" if line.startswith("phase:")
             else "next_gate: SUCCESSOR_PHASE_OPENING" if line.startswith("next_gate:")
             else line
             for line in lines]
    status_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    phases_path = root / "contracts/phases.json"
    phases_doc = json.loads(phases_path.read_text(encoding="utf-8"))
    phases_doc["phases"] = [item for item in phases_doc.get("phases") or []
                             if item.get("phase_id") != "phase:1-5"]
    for item in phases_doc["phases"]:
        if item.get("phase_id") == "phase:i":
            item["succeeded_by"] = None
    phases_path.write_text(json.dumps(phases_doc, indent=2) + "\n", encoding="utf-8")

    custodies_path = root / "contracts/custodies.json"
    custodies_doc = json.loads(custodies_path.read_text(encoding="utf-8"))
    custodies_doc["custodies"] = [item for item in custodies_doc.get("custodies") or []
                                   if not str(item.get("custody_id", "")).startswith(
                                       "custody:phase-1-5/")]
    custodies_path.write_text(json.dumps(custodies_doc, indent=2) + "\n", encoding="utf-8")

    return root


class PacketValidatesAgainstSchema(unittest.TestCase):
    def test_phase_record_validates_against_phase_schema(self) -> None:
        packet = sov_open_phase.load_packet(ROOT)
        schema = json.loads((ROOT / "contracts/phase.schema.json").read_text(encoding="utf-8"))
        errors = validate(packet["phase"], schema)
        self.assertEqual(errors, [])

    def test_packet_carries_the_contracted_fields(self) -> None:
        packet = sov_open_phase.load_packet(ROOT)
        self.assertEqual(packet["status"], "PROPOSED")
        phase = packet["phase"]
        self.assertEqual(phase["phase_id"], "phase:1-5")
        self.assertEqual(phase["title"], "Phase 1.5 - Operational Commissioning")
        self.assertEqual(phase["execution_status"], "OPEN")
        self.assertEqual(phase["acceptance_status"], "NOT_EARNED")
        self.assertEqual(phase["terminal"], "IN_FLIGHT")
        self.assertEqual(phase["settled_by"], "seat:root")
        self.assertIsNone(phase["succeeded_by"])

    def test_exactly_four_exit_clauses_named_x1_through_x4(self) -> None:
        packet = sov_open_phase.load_packet(ROOT)
        clause_ids = [clause["clause_id"] for clause in packet["phase"]["exit_clauses"]]
        self.assertEqual(clause_ids,
                         ["PHASE-1-5-X1", "PHASE-1-5-X2", "PHASE-1-5-X3", "PHASE-1-5-X4"])
        for clause in packet["phase"]["exit_clauses"]:
            self.assertEqual(clause["verdict"], "NOT_EARNED")
            self.assertTrue(clause["held_by"].startswith("custody:phase-1-5/"))


class CustodiesValidateAgainstSchema(unittest.TestCase):
    def test_four_custodies_validate_against_custody_schema(self) -> None:
        custodies_packet = sov_open_phase.load_custodies_packet(ROOT)
        schema = json.loads((ROOT / "contracts/custody.schema.json").read_text(encoding="utf-8"))
        custodies = custodies_packet["custodies"]
        self.assertEqual(len(custodies), 4)
        for custody in custodies:
            errors = validate(custody, schema)
            self.assertEqual(errors, [], msg=f"{custody.get('custody_id')}: {errors}")
            self.assertEqual(custody["status"], "PROPOSED")
            self.assertEqual(custody["custody_kind"], "EXIT")
            self.assertEqual(custody["phase"], "phase:1-5")

    def test_every_exit_clause_holder_resolves_to_a_staged_custody(self) -> None:
        packet = sov_open_phase.load_packet(ROOT)
        custodies_packet = sov_open_phase.load_custodies_packet(ROOT)
        custody_ids = {item["custody_id"] for item in custodies_packet["custodies"]}
        holders = {clause["held_by"] for clause in packet["phase"]["exit_clauses"]}
        self.assertEqual(holders, custody_ids)


class NoArgumentsPreviewWritesNothing(unittest.TestCase):
    def test_preview_against_an_unopened_fixture_matches_and_writes_nothing(self) -> None:
        with TemporaryDirectory() as tmp:
            root = _stage(tmp)
            before = {relative: _digest(root / relative)
                      for relative in ("contracts/phases.json", "STATUS.yaml",
                                       "contracts/custodies.json")}
            code, defects, plan = sov_open_phase.run(root, apply=False, dry_run=False)
            after = {relative: _digest(root / relative)
                     for relative in ("contracts/phases.json", "STATUS.yaml",
                                      "contracts/custodies.json")}
            self.assertEqual(code, 0)
            self.assertEqual(defects, [])
            self.assertIn("contracts/phases.json", plan)
            self.assertIn("STATUS.yaml", plan)
            self.assertEqual(before, after)


class ApplyDryRunIsByteIdentical(unittest.TestCase):
    def test_apply_dry_run_leaves_the_two_target_files_byte_identical(self) -> None:
        with TemporaryDirectory() as tmp:
            root = _stage(tmp)
            before = {relative: _digest(root / relative)
                      for relative in ("contracts/phases.json", "STATUS.yaml")}
            code, defects, _plan = sov_open_phase.run(root, apply=True, dry_run=True)
            after = {relative: _digest(root / relative)
                     for relative in ("contracts/phases.json", "STATUS.yaml")}
            self.assertEqual(code, 0)
            self.assertEqual(defects, [])
            self.assertEqual(before, after)


class ApplyWrites(unittest.TestCase):
    def test_apply_records_the_phase_repoints_the_predecessor_and_flips_status(self) -> None:
        with TemporaryDirectory() as tmp:
            root = _stage(tmp)
            code, defects, _plan = sov_open_phase.run(root, apply=True, dry_run=False)
            self.assertEqual(code, 0)
            self.assertEqual(defects, [])

            phases = json.loads((root / "contracts/phases.json").read_text(encoding="utf-8"))
            ids = [item["phase_id"] for item in phases["phases"]]
            self.assertIn("phase:1-5", ids)
            predecessor = next(item for item in phases["phases"] if item["phase_id"] == "phase:i")
            self.assertEqual(predecessor["succeeded_by"], "phase:1-5")

            status_text = (root / "STATUS.yaml").read_text(encoding="utf-8")
            self.assertIn("phase: phase:1-5", status_text)
            self.assertNotIn("phase: NONE_ACTIVE", status_text)
            self.assertIn("next_gate: PHASE_1_5_OPERATIONAL_ACCEPTANCE", status_text)
            self.assertNotIn("next_gate: SUCCESSOR_PHASE_OPENING", status_text)

            custodies = json.loads((root / "contracts/custodies.json").read_text(encoding="utf-8"))
            recorded_ids = {item["custody_id"] for item in custodies["custodies"]}
            self.assertTrue({
                "custody:phase-1-5/fresh-participation",
                "custody:phase-1-5/evidenced-judgement",
                "custody:phase-1-5/discovery-reuse",
                "custody:phase-1-5/definition-recurrence",
            }.issubset(recorded_ids))


class RefusesOnMismatch(unittest.TestCase):
    def test_refuses_when_a_pinned_document_no_longer_matches(self) -> None:
        with TemporaryDirectory() as tmp:
            root = _stage(tmp)
            (root / "archives/PRD-PHASE-1-5-OPENING.txt").write_text(
                "tampered\n", encoding="utf-8")
            code, defects, plan = sov_open_phase.run(root, apply=False, dry_run=False)
            self.assertEqual(code, 1)
            self.assertEqual(plan, {})
            self.assertTrue(any(defect.code == "UNPINNED_DEFINITION" for defect in defects))

    def test_refuses_when_a_pinned_document_is_missing(self) -> None:
        with TemporaryDirectory() as tmp:
            root = _stage(tmp)
            (root / "archives/SPEC-PHASE-1-5-OPENING.txt").unlink()
            code, defects, _plan = sov_open_phase.run(root, apply=False, dry_run=False)
            self.assertEqual(code, 1)
            self.assertTrue(any(defect.code == "MISSING_DEFINITION_DOCUMENT" for defect in defects))

    def test_refuses_when_phase_1_5_already_recorded(self) -> None:
        with TemporaryDirectory() as tmp:
            root = _stage(tmp)
            phases_path = root / "contracts/phases.json"
            phases = json.loads(phases_path.read_text(encoding="utf-8"))
            packet = sov_open_phase.load_packet(root)
            phases["phases"].append(packet["phase"])
            phases_path.write_text(json.dumps(phases, indent=2), encoding="utf-8")

            code, defects, _plan = sov_open_phase.run(root, apply=False, dry_run=False)
            self.assertEqual(code, 1)
            self.assertTrue(any(defect.code == "PHASE_ALREADY_RECORDED" for defect in defects))

    def test_refuses_when_status_is_not_none_active(self) -> None:
        with TemporaryDirectory() as tmp:
            root = _stage(tmp)
            status_path = root / "STATUS.yaml"
            text = status_path.read_text(encoding="utf-8")
            status_path.write_text(text.replace("phase: NONE_ACTIVE", "phase: PHASE_1_5_OPEN"),
                                   encoding="utf-8")

            code, defects, _plan = sov_open_phase.run(root, apply=False, dry_run=False)
            self.assertEqual(code, 1)
            self.assertTrue(any(defect.code == "STATUS_PHASE_NOT_NONE_ACTIVE"
                               for defect in defects))


if __name__ == "__main__":
    unittest.main()
