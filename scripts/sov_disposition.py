#!/usr/bin/env python3
"""Experimental deterministic disposition profiler for Issue #200.

The local NDJSON store is participant research evidence, not a new Soveraeign
System of Record. Profiles and reports are derived projections and may be
recreated from the append-only ledgers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STORE = ROOT / ".local" / "disposition"
CONSTRUCTS_PATH = ROOT / "research" / "disposition" / "constructs.json"
PROJECTIONS_PATH = ROOT / "research" / "disposition" / "projections.json"
GENESIS = "0" * 64


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def digest_obj(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_bank() -> dict[str, dict[str, Any]]:
    data = load_json(CONSTRUCTS_PATH)
    return {row["id"]: row for row in data["constructs"]}


def load_projections() -> dict[str, dict[str, Any]]:
    data = load_json(PROJECTIONS_PATH)
    return {row["id"]: row for row in data["projections"]}


def ledger_path(store: Path, name: str) -> Path:
    return store / f"{name}.ndjson"


def read_ledger(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                rows.append(json.loads(raw))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
    return rows


def chained_record(kind: str, payload: dict[str, Any], previous: str) -> dict[str, Any]:
    body = {
        "schema": "soveraeign-disposition-ledger/v0.1",
        "kind": kind,
        "prev_digest": previous,
        "payload": payload,
    }
    return {**body, "digest": digest_obj(body)}


def append_record(path: Path, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
    rows = read_ledger(path)
    previous = rows[-1]["digest"] if rows else GENESIS
    record = chained_record(kind, payload, previous)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(canonical(record) + "\n")
    return record


def verify_ledger(path: Path) -> dict[str, Any]:
    rows = read_ledger(path)
    previous = GENESIS
    for index, row in enumerate(rows, start=1):
        if row.get("prev_digest") != previous:
            raise ValueError(f"{path}: row {index}: previous digest mismatch")
        body = {key: row[key] for key in ("schema", "kind", "prev_digest", "payload")}
        expected = digest_obj(body)
        if row.get("digest") != expected:
            raise ValueError(f"{path}: row {index}: digest mismatch")
        previous = expected
    return {"path": str(path), "records": len(rows), "head": previous, "valid": True}


def parse_json_object(raw: str | None, flag: str) -> dict[str, Any]:
    if raw is None:
        return {}
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError(f"{flag} must be a JSON object")
    return value


def active_subjects(store: Path) -> dict[tuple[str, str], dict[str, Any]]:
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for row in read_ledger(ledger_path(store, "subjects")):
        payload = row["payload"]
        result[(payload["subject_id"], payload["revision"])] = payload
    return result


def subject_for(store: Path, subject_id: str, revision: str) -> dict[str, Any]:
    subject = active_subjects(store).get((subject_id, revision))
    if subject is None:
        raise ValueError(f"unknown subject/revision: {subject_id}@{revision}")
    return subject


def admitted_observations(store: Path, subject_id: str, revision: str) -> list[dict[str, Any]]:
    rows = read_ledger(ledger_path(store, "observations"))
    return [
        row["payload"]
        for row in rows
        if row["payload"]["subject_id"] == subject_id
        and row["payload"]["subject_revision"] == revision
        and row["payload"].get("admission") == "ADMITTED"
    ]


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

    evidence_basis = [
        observation
        for observation in sorted(
            observations,
            key=lambda row: (
                row["construct_id"],
                row["probe_id"],
                row["adapter"],
                row["context"],
                row["evidence_digest"],
            ),
        )
    ]
    profile = {
        "schema": "soveraeign-disposition-profile/v0.1",
        "standing": "EXPERIMENTAL",
        "subject": subject,
        "construct_bank_digest": digest_obj(load_json(CONSTRUCTS_PATH)),
        "evidence_digest": digest_obj(evidence_basis),
        "observation_count": len(observations),
        "constructs": constructs,
        "comparison": {
            "standing": "NOT_COMPARABLE_ACROSS_ADAPTERS_OR_SUBJECT_KINDS",
            "reason": "v0.1 ships no admitted measurement-equivalence records",
        },
    }
    profile["profile_digest"] = digest_obj(profile)
    return profile


def write_projection(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical(value) + "\n", encoding="utf-8", newline="\n")


def cmd_init(args: argparse.Namespace) -> dict[str, Any]:
    store = Path(args.store).resolve()
    store.mkdir(parents=True, exist_ok=True)
    (store / "profiles").mkdir(exist_ok=True)
    (store / "reports").mkdir(exist_ok=True)
    return {
        "store": str(store),
        "initialized": True,
        "construct_bank_digest": digest_obj(load_json(CONSTRUCTS_PATH)),
        "projection_bank_digest": digest_obj(load_json(PROJECTIONS_PATH)),
    }


def cmd_subject_add(args: argparse.Namespace) -> dict[str, Any]:
    store = Path(args.store).resolve()
    config = parse_json_object(args.config_json, "--config-json")
    payload = {
        "subject_id": args.subject_id,
        "revision": args.revision,
        "kind": args.kind,
        "adapter": args.adapter,
        "configuration": config,
    }
    if args.kind in {"agent", "model"} and not config:
        raise ValueError("agent/model subject requires non-empty --config-json")
    record = append_record(ledger_path(store, "subjects"), "subject-declared", payload)
    return {"subject": payload, "record_digest": record["digest"]}


def cmd_observe(args: argparse.Namespace) -> dict[str, Any]:
    store = Path(args.store).resolve()
    subject = subject_for(store, args.subject_id, args.subject_revision)
    bank = load_bank()
    if args.construct not in bank:
        raise ValueError(f"unknown construct: {args.construct}")
    if subject["kind"] not in bank[args.construct]["applicable_subject_kinds"]:
        raise ValueError(f"construct {args.construct} is NOT_APPLICABLE to {subject['kind']}")
    value = float(args.value)
    if value < -1.0 or value > 1.0 or not math.isfinite(value):
        raise ValueError("--value must be finite and within [-1, 1]")
    evidence = parse_json_object(args.evidence_json, "--evidence-json")
    if not evidence:
        raise ValueError("--evidence-json must identify supplied or observed evidence")
    payload = {
        "subject_id": args.subject_id,
        "subject_revision": args.subject_revision,
        "subject_kind": subject["kind"],
        "construct_id": args.construct,
        "probe_id": args.probe,
        "adapter": args.adapter,
        "adapter_revision": args.adapter_revision,
        "context": args.context,
        "value": value,
        "evidence": evidence,
        "evidence_digest": digest_obj(evidence),
        "admission": "ADMITTED",
    }
    record = append_record(ledger_path(store, "observations"), "observation", payload)
    return {"observation": payload, "record_digest": record["digest"]}


def cmd_profile(args: argparse.Namespace) -> dict[str, Any]:
    store = Path(args.store).resolve()
    profile = build_profile(store, args.subject_id, args.revision)
    path = store / "profiles" / f"{args.subject_id}@{args.revision}.json"
    write_projection(path, profile)
    return {"profile": profile, "path": str(path)}


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


def cmd_report(args: argparse.Namespace) -> dict[str, Any]:
    store = Path(args.store).resolve()
    profile = build_profile(store, args.subject_id, args.revision)
    projections = load_projections()
    if args.projection not in projections:
        raise ValueError(f"unknown projection: {args.projection}")
    projection = projections[args.projection]
    standing = projection["calibration_standing"]
    if standing == "UNVALIDATED" and not args.allow_unvalidated:
        raise ValueError("projection is UNVALIDATED; pass --allow-unvalidated to render it explicitly")

    mapping = projection["mapping"]
    if mapping == "identity":
        outputs = profile["constructs"]
    else:
        outputs = {axis: mapped_score(profile, weights) for axis, weights in sorted(mapping.items())}

    report = {
        "schema": "soveraeign-disposition-report/v0.1",
        "standing": "PROJECTION",
        "subject_id": args.subject_id,
        "subject_revision": args.revision,
        "source_profile_digest": profile["profile_digest"],
        "projection_id": projection["id"],
        "projection_bank_digest": digest_obj(load_json(PROJECTIONS_PATH)),
        "calibration_standing": standing,
        "intended_use": projection["intended_use"],
        "loss": projection["loss"],
        "cohort_comparison": "NOT_ADMITTED",
        "outputs": outputs,
    }
    report["report_digest"] = digest_obj(report)
    path = store / "reports" / f"{args.subject_id}@{args.revision}.{args.projection}.json"
    write_projection(path, report)
    return {"report": report, "path": str(path)}


def cmd_verify(args: argparse.Namespace) -> dict[str, Any]:
    store = Path(args.store).resolve()
    ledgers = [
        verify_ledger(ledger_path(store, "subjects")),
        verify_ledger(ledger_path(store, "observations")),
    ]
    return {"valid": True, "ledgers": ledgers}


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--store", default=os.fspath(DEFAULT_STORE))
    commands = root.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init")
    init.set_defaults(func=cmd_init)

    subject = commands.add_parser("subject")
    subject_commands = subject.add_subparsers(dest="subject_command", required=True)
    add = subject_commands.add_parser("add")
    add.add_argument("--id", dest="subject_id", required=True)
    add.add_argument("--revision", required=True)
    add.add_argument("--kind", choices=["human", "agent", "model", "code", "mechanism"], required=True)
    add.add_argument("--adapter", required=True)
    add.add_argument("--config-json")
    add.set_defaults(func=cmd_subject_add)

    observe = commands.add_parser("observe")
    observe.add_argument("--subject", dest="subject_id", required=True)
    observe.add_argument("--subject-revision", required=True)
    observe.add_argument("--construct", required=True)
    observe.add_argument("--probe", required=True)
    observe.add_argument("--adapter", required=True)
    observe.add_argument("--adapter-revision", required=True)
    observe.add_argument("--context", required=True)
    observe.add_argument("--value", required=True, type=float)
    observe.add_argument("--evidence-json", required=True)
    observe.set_defaults(func=cmd_observe)

    profile = commands.add_parser("profile")
    profile.add_argument("--subject", dest="subject_id", required=True)
    profile.add_argument("--revision", required=True)
    profile.set_defaults(func=cmd_profile)

    report = commands.add_parser("report")
    report.add_argument("--subject", dest="subject_id", required=True)
    report.add_argument("--revision", required=True)
    report.add_argument("--projection", required=True)
    report.add_argument("--allow-unvalidated", action="store_true")
    report.set_defaults(func=cmd_report)

    verify = commands.add_parser("verify")
    verify.set_defaults(func=cmd_verify)
    return root


def main(argv: list[str] | None = None) -> int:
    try:
        args = parser().parse_args(argv)
        result = args.func(args)
        print(canonical(result))
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(canonical({"ok": False, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
