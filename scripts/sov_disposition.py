#!/usr/bin/env python3
"""Experimental deterministic disposition profiler for Issue #200."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import disposition_profile as profilelib  # noqa: E402
from scripts import disposition_store as storelib  # noqa: E402

DEFAULT_STORE = ROOT / ".local" / "disposition"

canonical = storelib.canonical
ledger_path = storelib.ledger_path
verify_ledger = storelib.verify_ledger
build_profile = profilelib.build_profile


def cmd_init(args: argparse.Namespace) -> dict[str, Any]:
    store = Path(args.store).resolve()
    store.mkdir(parents=True, exist_ok=True)
    (store / "profiles").mkdir(exist_ok=True)
    (store / "reports").mkdir(exist_ok=True)
    return {
        "store": str(store),
        "initialized": True,
        "construct_bank_digest": storelib.digest_obj(storelib.load_json(profilelib.CONSTRUCTS_PATH)),
        "probe_bank_digest": storelib.digest_obj(storelib.load_json(profilelib.PROBES_PATH)),
        "projection_bank_digest": storelib.digest_obj(storelib.load_json(profilelib.PROJECTIONS_PATH)),
    }


def cmd_subject_add(args: argparse.Namespace) -> dict[str, Any]:
    store = Path(args.store).resolve()
    config = storelib.parse_json_object(args.config_json, "--config-json")
    if (args.subject_id, args.revision) in profilelib.active_subjects(store):
        raise ValueError(f"subject revision already declared: {args.subject_id}@{args.revision}")
    if args.kind in {"agent", "model"} and not config:
        raise ValueError("agent/model subject requires non-empty --config-json")
    payload = {
        "subject_id": args.subject_id,
        "revision": args.revision,
        "kind": args.kind,
        "adapter": args.adapter,
        "configuration": config,
    }
    record = storelib.append_record(
        storelib.ledger_path(store, "subjects"), "subject-declared", payload
    )
    return {"subject": payload, "record_digest": record["digest"]}


def cmd_observe(args: argparse.Namespace) -> dict[str, Any]:
    store = Path(args.store).resolve()
    subject = profilelib.subject_for(store, args.subject_id, args.subject_revision)
    bank = profilelib.load_bank()
    if args.construct not in bank:
        raise ValueError(f"unknown construct: {args.construct}")
    if subject["kind"] not in bank[args.construct]["applicable_subject_kinds"]:
        raise ValueError(f"construct {args.construct} is NOT_APPLICABLE to {subject['kind']}")
    profilelib.validate_probe(args.probe, args.construct)
    profilelib.assert_trial_is_new(store, args.subject_id, args.subject_revision, args.trial)

    value = float(args.value)
    if value < -1.0 or value > 1.0 or not math.isfinite(value):
        raise ValueError("--value must be finite and within [-1, 1]")
    evidence = storelib.parse_json_object(args.evidence_json, "--evidence-json")
    if not evidence:
        raise ValueError("--evidence-json must identify supplied or observed evidence")

    payload = {
        "subject_id": args.subject_id,
        "subject_revision": args.subject_revision,
        "subject_kind": subject["kind"],
        "construct_id": args.construct,
        "probe_id": args.probe,
        "trial_id": args.trial,
        "adapter": args.adapter,
        "adapter_revision": args.adapter_revision,
        "scorer_revision": "normalized-anchor-v0.1",
        "context": args.context,
        "value": value,
        "evidence": evidence,
        "evidence_digest": storelib.digest_obj(evidence),
        "admission": "ADMITTED",
    }
    record = storelib.append_record(
        storelib.ledger_path(store, "observations"), "observation", payload
    )
    return {"observation": payload, "record_digest": record["digest"]}


def cmd_profile(args: argparse.Namespace) -> dict[str, Any]:
    store = Path(args.store).resolve()
    profile = profilelib.build_profile(store, args.subject_id, args.revision)
    path = store / "profiles" / f"{args.subject_id}@{args.revision}.json"
    storelib.write_projection(path, profile)
    return {"profile": profile, "path": str(path)}


def cmd_report(args: argparse.Namespace) -> dict[str, Any]:
    store = Path(args.store).resolve()
    profile = profilelib.build_profile(store, args.subject_id, args.revision)
    report = profilelib.build_report(profile, args.projection, args.allow_unvalidated)
    path = store / "reports" / f"{args.subject_id}@{args.revision}.{args.projection}.json"
    storelib.write_projection(path, report)
    return {"report": report, "path": str(path)}


def cmd_verify(args: argparse.Namespace) -> dict[str, Any]:
    store = Path(args.store).resolve()
    ledgers = [
        storelib.verify_ledger(storelib.ledger_path(store, "subjects")),
        storelib.verify_ledger(storelib.ledger_path(store, "observations")),
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
    add.add_argument(
        "--kind",
        choices=["human", "agent", "model", "code", "mechanism"],
        required=True,
    )
    add.add_argument("--adapter", required=True)
    add.add_argument("--config-json")
    add.set_defaults(func=cmd_subject_add)

    observe = commands.add_parser("observe")
    observe.add_argument("--subject", dest="subject_id", required=True)
    observe.add_argument("--subject-revision", required=True)
    observe.add_argument("--construct", required=True)
    observe.add_argument("--probe", required=True)
    observe.add_argument("--trial", required=True)
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
        print(storelib.canonical(args.func(args)))
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(storelib.canonical({"ok": False, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
