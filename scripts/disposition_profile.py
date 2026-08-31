from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Iterable

from scripts import disposition_store as storelib

ROOT = Path(__file__).resolve().parents[1]
CONSTRUCTS_PATH = ROOT / "research" / "disposition" / "constructs.json"
PROBES_PATH = ROOT / "research" / "disposition" / "probes.json"
PROJECTIONS_PATH = ROOT / "research" / "disposition" / "projections.json"
EQUIVALENCE_PATH = ROOT / "research" / "disposition" / "equivalence.json"


def load_bank() -> dict[str, dict[str, Any]]:
    data = storelib.load_json(CONSTRUCTS_PATH)
    return {row["id"]: row for row in data["constructs"]}


def load_probes() -> dict[str, dict[str, Any]]:
    data = storelib.load_json(PROBES_PATH)
    return {row["id"]: row for row in data["probes"]}


def load_projections() -> dict[str, dict[str, Any]]:
    data = storelib.load_json(PROJECTIONS_PATH)
    return {row["id"]: row for row in data["projections"]}


def active_subjects(store: Path) -> dict[tuple[str, str], dict[str, Any]]:
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for row in storelib.read_ledger(storelib.ledger_path(store, "subjects")):
        payload = row["payload"]
        key = (payload["subject_id"], payload["revision"])
        if key in result:
            raise ValueError(f"duplicate immutable subject revision: {key[0]}@{key[1]}")
        result[key] = payload
    return result


def subject_for(store: Path, subject_id: str, revision: str) -> dict[str, Any]:
    subject = active_subjects(store).get((subject_id, revision))
    if subject is None:
        raise ValueError(f"unknown subject/revision: {subject_id}@{revision}")
    return subject


def observations_for(store: Path, subject_id: str, revision: str) -> list[dict[str, Any]]:
    rows = storelib.read_ledger(storelib.ledger_path(store, "observations"))
    return [
        row["payload"]
        for row in rows
        if row["payload"]["subject_id"] == subject_id
        and row["payload"]["subject_revision"] == revision
    ]


def admitted_observations(store: Path, subject_id: str, revision: str) -> list[dict[str, Any]]:
    return [
        row
        for row in observations_for(store, subject_id, revision)
        if row.get("admission") == "ADMITTED"
    ]


def assert_trial_is_new(store: Path, subject_id: str, revision: str, trial_id: str) -> None:
    for observation in observations_for(store, subject_id, revision):
        if observation.get("trial_id") == trial_id:
            raise ValueError(f"duplicate trial_id for subject revision: {trial_id}")


def validate_probe(probe_id: str, construct_id: str) -> dict[str, Any]:
    probe = load_probes().get(probe_id)
    if probe is None:
        raise ValueError(f"unknown probe: {probe_id}")
    if probe["construct_id"] != construct_id:
        raise ValueError(
            f"probe {probe_id} measures {probe['construct_id']}, not {construct_id}"
        )
    return probe


def construct_profile(values: list[float], contexts: Iterable[str]) -> dict[str, Any]:
    n = len(values)
    if n == 0:
        return {
            "status": "INSUFFICIENT_EVIDENCE",
            "n": 0,
            "center": None,
            "spread": None,
            "standard_error": None,
            "contexts": [],
        }
    center = sum(values) / n
    spread = math.sqrt(sum((value - center) ** 2 for value in values) / n)
    standard_error = spread / math.sqrt(n) if n > 1 else None
    return {
        "status": "EXPERIMENTAL_ESTIMATE" if n >= 3 else "INSUFFICIENT_EVIDENCE",
        "n": n,
        "center": round(center, 6),
        "spread": round(spread, 6),
        "standard_error": None if standard_error is None else round(standard_error, 6),
        "minimum": round(min(values), 6),
        "maximum": round(max(values), 6),
        "contexts": sorted(set(contexts)),
    }


def build_profile(store: Path, subject_id: str, revision: str) -> dict[str, Any]:
    subject = subject_for(store, subject_id, revision)
    bank = load_bank()
    observations = admitted_observations(store, subject_id, revision)
    by_construct: dict[str, list[dict[str, Any]]] = {key: [] for key in bank}
    for observation in observations:
        by_construct[observation["construct_id"]].append(observation)

    constructs: dict[str, Any] = {}
    for construct_id in sorted(bank):
        applicable = subject["kind"] in bank[construct_id]["applicable_subject_kinds"]
        if not applicable:
            constructs[construct_id] = {
                "status": "NOT_APPLICABLE",
                "n": 0,
                "center": None,
                "spread": None,
                "standard_error": None,
                "contexts": [],
            }
            continue
        rows = by_construct[construct_id]
        constructs[construct_id] = construct_profile(
            [float(row["value"]) for row in rows],
            [row["context"] for row in rows],
        )

    evidence_basis = sorted(
        observations,
        key=lambda row: (
            row["construct_id"],
            row["probe_id"],
            row["trial_id"],
            row["adapter"],
            row["context"],
            row["evidence_digest"],
        ),
    )
    equivalence = storelib.load_json(EQUIVALENCE_PATH)
    profile = {
        "schema": "soveraeign-disposition-profile/v0.1",
        "standing": "EXPERIMENTAL",
        "subject": subject,
        "construct_bank_digest": storelib.digest_obj(storelib.load_json(CONSTRUCTS_PATH)),
        "probe_bank_digest": storelib.digest_obj(storelib.load_json(PROBES_PATH)),
        "equivalence_bank_digest": storelib.digest_obj(equivalence),
        "evidence_digest": storelib.digest_obj(evidence_basis),
        "observation_count": len(observations),
        "constructs": constructs,
        "comparison": {
            "standing": "NOT_COMPARABLE_ACROSS_ADAPTERS_OR_SUBJECT_KINDS",
            "reason": equivalence["default"]["reason"],
        },
    }
    profile["profile_digest"] = storelib.digest_obj(profile)
    return profile


def mapped_score(profile: dict[str, Any], weights: dict[str, float]) -> dict[str, Any]:
    available: list[tuple[float, float]] = []
    missing: list[str] = []
    for construct_id, weight in weights.items():
        row = profile["constructs"].get(construct_id)
        if row is None or row.get("center") is None:
            missing.append(construct_id)
            continue
        available.append((float(row["center"]), float(weight)))
    if missing or not available:
        return {"status": "INSUFFICIENT_EVIDENCE", "score": None, "missing": sorted(missing)}
    denominator = sum(abs(weight) for _, weight in available)
    score = sum(value * weight for value, weight in available) / denominator
    return {"status": "EXPERIMENTAL_PROJECTION", "score": round(score, 6), "missing": []}


def build_report(profile: dict[str, Any], projection_id: str, allow_unvalidated: bool) -> dict[str, Any]:
    projections = load_projections()
    if projection_id not in projections:
        raise ValueError(f"unknown projection: {projection_id}")
    projection = projections[projection_id]
    standing = projection["calibration_standing"]
    if standing == "UNVALIDATED" and not allow_unvalidated:
        raise ValueError("projection is UNVALIDATED; pass --allow-unvalidated to render it explicitly")

    mapping = projection["mapping"]
    if mapping == "identity":
        outputs = profile["constructs"]
    else:
        outputs = {axis: mapped_score(profile, weights) for axis, weights in sorted(mapping.items())}

    report = {
        "schema": "soveraeign-disposition-report/v0.1",
        "standing": "PROJECTION",
        "subject_id": profile["subject"]["subject_id"],
        "subject_revision": profile["subject"]["revision"],
        "source_profile_digest": profile["profile_digest"],
        "projection_id": projection["id"],
        "projection_bank_digest": storelib.digest_obj(storelib.load_json(PROJECTIONS_PATH)),
        "calibration_standing": standing,
        "intended_use": projection["intended_use"],
        "loss": projection["loss"],
        "cohort_comparison": "NOT_ADMITTED",
        "outputs": outputs,
    }
    report["report_digest"] = storelib.digest_obj(report)
    return report
