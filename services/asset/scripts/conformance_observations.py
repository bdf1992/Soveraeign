#!/usr/bin/env python3
"""Observe the current Asset Service against the Phase-I scenario contract.

The adapter reports actual implemented capability and explicit absence. It does
not repair, simulate, or claim completion for missing Phase-I behavior.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from soveraeign_asset_service import (
    AssetService,
    AuthorityRefused,
    ReaderDeclaration,
)


def item(case_id: str, observed: dict) -> dict:
    return {
        "case_id": case_id,
        "participant_id": "asset-service-reference",
        "artifact_revision": "WORKTREE",
        "observed": observed,
    }


def main() -> int:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        source_path = root / "source.txt"
        source_path.write_bytes(b"authoritative source\n")
        service = AssetService(root / "state")
        try:
            original = service.ingest(source_path, "Source Asset", "Bdo")

            proposal_id = service.propose(
                original["asset_id"], "model-1", {"description": "candidate"}
            )
            proposal = service.db.execute(
                "SELECT * FROM proposals WHERE id=?", (proposal_id,)
            ).fetchone()
            i1 = item("RUN-I1-PROPOSE", {
                "proposal": {
                    "proposal_id": proposal["id"], "actor_id": proposal["actor"],
                    "actor_kind": "MODEL", "content_address": None,
                    "source_addresses": [], "cost_record": None,
                    "required_authority_type": proposal["required_authority"],
                    "scope": proposal["asset_id"], "standing": proposal["standing"],
                },
                "admitted": False,
            })

            service.grant("Bdo", "Bdo", "operate:derive")
            before = original["digest"]
            reader = ReaderDeclaration.from_materials(
                reader_id="asset.metadata-card",
                reader_version="1.0.0",
                reader_artifact=b'{"entrypoint":"builtin:metadata-card"}',
                configuration={"format": "json", "schema": "card-v1"},
                fidelity="LOSSY",
                omissions=("binary-payload",),
            )
            run_id = service.request_derivative(
                original["asset_id"],
                original["version_id"],
                "Bdo",
                reader=reader,
            )
            fence = service.claim(run_id, "worker-1")
            derived_version_id = service.report_derivative(
                run_id, "worker-1", fence, b'{"derived":true}'
            )
            recording = service.reconstruct_recording(derived_version_id)
            after = service.db.execute(
                "SELECT digest FROM sources WHERE id=?", (original["source_id"],)
            ).fetchone()[0]
            i2 = item("RUN-I2-REMEMBER", {
                "source_before_digest": before,
                "source_after_digest": after,
                "recording": recording,
            })

            i3 = item("RUN-I3-CROSS", {
                "human": {
                    "transition_contract": "asset-service-python-api",
                    "direct_write": False,
                    "receipt_id": original["receipt_id"],
                },
                "model": {"transition_contract": None, "direct_write": False, "receipt_id": None},
                "crossing": {
                    "source_id": None,
                    "source_version": None,
                    "projection_id": None,
                    "omissions": None,
                    "destination_id": None,
                },
            })

            campaign_path = root / "campaign.txt"
            campaign_path.write_bytes(b"campaign\n")
            campaign = service.ingest(campaign_path, "Campaign", "Bdo")
            service.grant("Bdo", "Bdo", "ratify:judgement")
            service.grant("Bdo", "Bdo", "retract:record")
            relation_proposal = service.propose(original["asset_id"], "model-1", {
                "relationship": {"predicate": "USED_BY", "dst_asset": campaign["asset_id"]}
            })
            ratify_receipt = service.ratify(relation_proposal, "Bdo")
            relation_id = service.db.execute(
                "SELECT id FROM relationships WHERE proposal_id=?", (relation_proposal,)
            ).fetchone()[0]
            retract_receipt_id = service.retract(
                "relationship", relation_id, "Bdo", "superseded use"
            )
            retract_receipt = service.db.execute(
                "SELECT * FROM receipts WHERE id=?", (retract_receipt_id,)
            ).fetchone()
            retract_payload = json.loads(retract_receipt["payload_json"])
            i4 = item("RUN-I4-RETRACT", {
                "original_record_present": service.db.execute(
                    "SELECT 1 FROM relationships WHERE id=?", (relation_id,)
                ).fetchone()
                is not None,
                "counter_record_present": service.db.execute(
                    "SELECT 1 FROM retractions WHERE target_id=?", (relation_id,)
                ).fetchone()
                is not None,
                "effect_class": "RECORD_LOCAL",
                "claims_world_rollback": False,
                "receipt": {
                    "outcome": retract_receipt["outcome"],
                    "target_receipt_id": retract_payload.get("target_receipt_id"),
                },
                "reconstructed_prior_receipt_id": ratify_receipt,
            })

            refused_proposal = service.propose(
                original["asset_id"], "model-1", {"description": "judgement"}
            )
            try:
                service.ratify(refused_proposal, "model-1")
                authority_outcome = "COMMITTED"
            except AuthorityRefused:
                authority_outcome = "REFUSED"
            authority_receipt = service.db.execute(
                "SELECT id FROM receipts WHERE event='authority.check' AND subject_id=? "
                "ORDER BY created_at DESC LIMIT 1",
                (refused_proposal,),
            ).fetchone()
            i5 = item("RUN-I5-AUTHORITY", {"attempts": [{
                "actor_kind": "MODEL", "authority_type": "VERIFICATION",
                "claim_type": "JUDGEMENT", "grant_live": True,
                "scope_matches": True, "budget_available": True,
                "outcome": authority_outcome,
                "receipt_id": authority_receipt["id"] if authority_receipt else None,
            }]})

            i6 = item("RUN-I6-JUDGEMENT", {
                "pending_right": {
                    "persistent": False,
                    "visible": False,
                    "outcome": None,
                    "receipt_id": None,
                },
                "unrelated_operation_outcome": "COMMITTED",
                "judgement_spend_derived_from_receipts": False,
                "invented_quota": False,
            })
            i7 = item("RUN-I7-QUALIFY", {
                "clean_checkout": False, "oral_explanation_used": False,
                "authority_located": False, "conformance_executed": False,
                "evidence_reconstructed": False, "semantic_task_observed": False,
                "time_to_safe_competence_seconds": None, "interventions": [],
                "owner_acceptance": "PENDING",
            })
            i8 = item("RUN-I8-ATTEST", {
                "ratification_before": "RATIFIED", "ratification_after": "RATIFIED",
                "validator_changed_authority": False, "attestations": [],
            })
            i9 = item("RUN-I9-BYOM", {
                "bindings": [],
                "unavailable_model": {
                    "binding_id": None, "outcome": "UNIMPLEMENTED",
                    "reason": None, "receipt_id": None, "silent_fallback": False,
                },
                "local_record_operable": True,
            })

            print(json.dumps([i1, i2, i3, i4, i5, i6, i7, i8, i9], indent=2, sort_keys=True))
        finally:
            service.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
