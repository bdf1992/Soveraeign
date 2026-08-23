"""The journal exposes bypasses, and every emitted record meets the shared contracts."""

from __future__ import annotations

from pathlib import Path
import json
import sys

from support import BDO, REPO_ROOT, KernelCase

sys.path.insert(0, str(REPO_ROOT / "scripts"))

from sovticket.jsonschema import validate  # noqa: E402

CONTRACTS = REPO_ROOT / "contracts"


def schema(name: str) -> dict:
    return json.loads((CONTRACTS / name).read_text(encoding="utf-8"))


class JournalAudit(KernelCase):
    def full_walk(self) -> str:
        record_id = self.ratified()
        self.attested(record_id)
        self.kernel.make_effective(record_id, actor_id=BDO, actor_kind="HUMAN",
                                   expected_state=self.kernel.state_digest(record_id))
        run_id = self.begun()
        self.reported(run_id)
        self.observed(run_id)
        self.settled(run_id)
        self.kernel.retract(record_id, actor_id=BDO, actor_kind="HUMAN", grant_id="g-retract",
                            reason="walk complete")
        return record_id

    def test_clean_walk_audits_clean(self) -> None:
        self.full_walk()
        self.assertEqual(self.kernel.audit(), [])

    def test_one_receipt_per_attempt(self) -> None:
        self.full_walk()
        self.submit(cost_record=None)  # a refusal is an attempt too
        events = self.kernel.journal.bodies("EVENT")
        receipts = self.kernel.journal.bodies("RECEIPT")
        self.assertEqual(len(events), len(receipts))
        self.assertEqual({e["receipt_id"] for e in events}, {r["receipt_id"] for r in receipts})
        self.assertEqual({e["event_id"] for e in events}, {r["event_id"] for r in receipts})

    def test_emitted_records_meet_contracts(self) -> None:
        self.full_walk()
        self.submit(cost_record=None)
        receipt_schema = schema("receipt.schema.json")
        envelope_schema = schema("event-envelope.schema.json")
        for receipt in self.kernel.journal.bodies("RECEIPT"):
            self.assertEqual(validate(receipt, receipt_schema), [], receipt["event_type"])
        for event in self.kernel.journal.bodies("EVENT"):
            self.assertEqual(validate(event, envelope_schema), [], event["reason"])

    def test_service_edit_around_kernel_is_exposed(self) -> None:
        record_id = self.recorded()
        self.kernel.records[record_id].standing_history.append("RATIFIED")  # a private rule
        defects = self.kernel.audit()
        self.assertTrue(any("standing projection diverges" in d for d in defects), defects)

    def test_service_effectiveness_around_kernel_is_exposed(self) -> None:
        record_id = self.ratified()
        self.kernel.records[record_id].effective = True
        defects = self.kernel.audit()
        self.assertTrue(any("effectiveness diverges" in d for d in defects), defects)

    def test_raw_append_breaks_chain(self) -> None:
        self.recorded()
        rogue = {"sequence": 99, "kind": "RECORD", "body": {}, "prior_digest": "sha256:x",
                 "entry_digest": "sha256:y"}
        self.kernel.journal._entries.append(rogue)
        defects = self.kernel.journal.audit()
        self.assertTrue(any("chain link" in d for d in defects), defects)

    def test_unreceipted_event_is_exposed(self) -> None:
        self.kernel.journal.append("EVENT", {"event_id": "e-rogue", "receipt_id": None})
        self.assertIn("event e-rogue: no receipt", self.kernel.journal.audit())

    def test_retraction_that_erases_is_exposed(self) -> None:
        record_id = self.full_walk()
        journal = self.kernel.journal
        journal._entries = [e for e in journal._entries
                            if not (e["kind"] == "RECORD" and e["body"]["record_id"] == record_id)]
        defects = journal.audit()
        self.assertTrue(any("original record is not on record" in d for d in defects), defects)

    def test_legal_transitions_are_discoverable(self) -> None:
        listed = self.kernel.transitions()
        self.assertEqual(len(listed["legal"]), 14)
        self.assertTrue(set(listed["realized_by_kernel"]) <= set(listed["legal"]))
        for name in listed["realized_by_kernel"]:
            self.assertTrue(callable(getattr(self.kernel, name)), name)

    def test_fixture_file_is_well_formed(self) -> None:
        path = Path(__file__).resolve().parents[1] / "fixtures" / "transition-matrix.json"
        matrix = json.loads(path.read_text(encoding="utf-8"))
        ids = [case["id"] for case in matrix["cases"]]
        self.assertEqual(len(ids), len(set(ids)), "duplicate case id")
        for case in matrix["cases"]:
            self.assertIn(case["polarity"], ("positive", "defeating"))
            if case["polarity"] == "defeating":
                self.assertTrue(case.get("defeats"), case["id"])
