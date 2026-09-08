from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts import disposition_store as storelib

ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_PATH = ROOT / ".claude" / "drafts" / "disposition-lab" / "surface-taxonomy.json"
ALLOWED_SUBJECT_KINDS = {"human", "agent", "model", "code", "mechanism"}


def load_taxonomy() -> dict[str, Any]:
    return storelib.load_json(TAXONOMY_PATH)


def label_bank() -> dict[str, dict[str, Any]]:
    return {row["id"]: row for row in load_taxonomy()["labels"]}


def validate_prediction(
    prediction: dict[str, Any], *, minimum_confidence: float = 0.60
) -> dict[str, Any]:
    required = {
        "subject_kind",
        "observation_ref",
        "labels",
        "model_id",
        "model_revision",
        "taxonomy_version",
        "inference_revision",
    }
    missing = sorted(required - prediction.keys())
    if missing:
        raise ValueError(f"surface prediction missing fields: {', '.join(missing)}")
    if prediction["subject_kind"] not in ALLOWED_SUBJECT_KINDS:
        raise ValueError(f"unknown subject kind: {prediction['subject_kind']}")
    if prediction["taxonomy_version"] != load_taxonomy()["schema"]:
        raise ValueError("surface prediction taxonomy version mismatch")
    if not prediction["model_id"] or not prediction["model_revision"]:
        raise ValueError("surface prediction requires pinned model identity and revision")
    if not prediction["inference_revision"]:
        raise ValueError("surface prediction requires inference revision")
    if not isinstance(prediction["labels"], list):
        raise ValueError("surface prediction labels must be a list")

    bank = label_bank()
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in prediction["labels"]:
        if not isinstance(item, dict) or "label" not in item or "confidence" not in item:
            raise ValueError("each surface label requires label and confidence")
        label = item["label"]
        if label == load_taxonomy()["abstention_label"]:
            continue
        if label not in bank:
            raise ValueError(f"unknown surface label: {label}")
        if label in seen:
            raise ValueError(f"duplicate surface label: {label}")
        seen.add(label)
        confidence = float(item["confidence"])
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("surface confidence must be within [0, 1]")
        row = {"label": label, "confidence": confidence}
        if confidence >= minimum_confidence:
            accepted.append(row)
        else:
            rejected.append({**row, "reason": "BELOW_CONFIDENCE_THRESHOLD"})

    standing = "ABSTAIN" if not accepted else "CANDIDATE_SURFACE_EVIDENCE"
    return {
        "schema": "soveraeign-disposition-surface-prediction/v0.1",
        "standing": standing,
        "subject_kind": prediction["subject_kind"],
        "observation_ref": prediction["observation_ref"],
        "taxonomy_version": prediction["taxonomy_version"],
        "taxonomy_digest": storelib.digest_obj(load_taxonomy()),
        "model_id": prediction["model_id"],
        "model_revision": prediction["model_revision"],
        "inference_revision": prediction["inference_revision"],
        "calibration_revision": prediction.get("calibration_revision"),
        "minimum_confidence": minimum_confidence,
        "accepted_labels": sorted(accepted, key=lambda row: row["label"]),
        "rejected_labels": sorted(rejected, key=lambda row: row["label"]),
        "direct_construct_update": "NOT_ADMITTED",
    }


def candidate_construct_evidence(surface: dict[str, Any]) -> list[dict[str, Any]]:
    if surface.get("standing") != "CANDIDATE_SURFACE_EVIDENCE":
        return []
    bank = label_bank()
    result = []
    for item in surface["accepted_labels"]:
        label = bank[item["label"]]
        result.append(
            {
                "surface_label": label["id"],
                "construct_id": label["candidate_construct"],
                "candidate_value": round(
                    float(label["candidate_polarity"]) * float(item["confidence"]), 6
                ),
                "standing": "UNVALIDATED_MAPPING",
            }
        )
    return sorted(result, key=lambda row: (row["construct_id"], row["surface_label"]))


def append_prediction(
    store: Path, prediction: dict[str, Any], *, minimum_confidence: float = 0.60
) -> dict[str, Any]:
    surface = validate_prediction(prediction, minimum_confidence=minimum_confidence)
    payload = {
        **surface,
        "candidate_construct_evidence": candidate_construct_evidence(surface),
    }
    record = storelib.append_record(
        storelib.ledger_path(store, "surface-observations"), "surface-prediction", payload
    )
    return {"surface_prediction": payload, "record_digest": record["digest"]}
