#!/usr/bin/env python3
"""Produce a candidate observation of the exact Gateway-to-Asset crossing."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
from typing import Any

from gateway_observe import canonical, crossing_defects, semantic_signature


ROOT = Path(__file__).resolve().parents[1]
SERVICE_SOURCES = ("gateway", "asset", "console", "record")


class WitnessRefused(RuntimeError):
    """The requested observation cannot establish its preconditions."""


def _git_preconditions(expected_commit: str) -> None:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    if commit != expected_commit:
        raise WitnessRefused(f"COMMIT_MISMATCH:{commit}")
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"], cwd=ROOT, check=True,
        capture_output=True, text=True
    ).stdout
    if status:
        raise WitnessRefused("CHECKOUT_NOT_CLEAN")


def _environment() -> dict[str, str]:
    env = dict(os.environ)
    paths = [str(ROOT / "services" / service / "src") for service in SERVICE_SOURCES]
    if env.get("PYTHONPATH"):
        paths.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(paths)
    return env


def run_driver(state: Path, actor: str, actor_kind: str) -> dict[str, Any]:
    """Run the participant in a child process; return the caller-visible JSON."""
    result = subprocess.run(
        [sys.executable, "scripts/gateway_witness_driver.py", "--state", str(state),
         "--actor", actor, "--actor-kind", actor_kind],
        cwd=ROOT, env=_environment(), check=False, capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise WitnessRefused(f"DRIVER_FAILED:{result.returncode}")
    try:
        return json.loads(result.stdout)
    except ValueError as error:
        raise WitnessRefused("DRIVER_OUTPUT_INVALID") from error


def _tamper_journal(source: Path, target: Path) -> None:
    shutil.copytree(source, target)
    database = target / "record" / "record-service.sqlite3"
    connection = sqlite3.connect(database)
    try:
        row = connection.execute(
            "SELECT seq,payload_json FROM journal WHERE payload_json LIKE ?",
            ('%"record_kind":"gateway-returned-receipt"%',),
        ).fetchone()
        if row is None:
            raise WitnessRefused("TAMPER_TARGET_ABSENT")
        payload = json.loads(row[1])
        payload["terminal_outcome"] = "REFUSED"
        connection.execute("UPDATE journal SET payload_json=? WHERE seq=?",
                           (canonical(payload), row[0]))
        connection.commit()
    finally:
        connection.close()


def run_witness(witness_id: str, expected_commit: str) -> dict[str, Any]:
    """Run two bindings, independent durable inspection, and observer self-defeats."""
    _git_preconditions(expected_commit)
    started = datetime.now(timezone.utc).isoformat()
    observations: list[dict[str, Any]] = []
    signatures: list[dict[str, Any]] = []
    with TemporaryDirectory() as temporary:
        workspace = Path(temporary)
        outputs: dict[str, dict[str, Any]] = {}
        states: dict[str, Path] = {}
        for actor_kind in ("HUMAN", "MODEL"):
            actor = f"gateway-witness-{actor_kind.lower()}"
            state = workspace / actor_kind.lower()
            output = run_driver(state, actor, actor_kind)
            defects = crossing_defects(ROOT, state, output, actor, actor_kind)
            if defects:
                raise WitnessRefused(f"{actor_kind}_OBSERVATION:" + ",".join(defects))
            outputs[actor_kind], states[actor_kind] = output, state
            signature = semantic_signature(ROOT, state, output)
            signatures.append(signature)
            observations.append({
                "case": f"{actor_kind.lower()}-exact-gateway-crossing",
                "observer_relation": "CALLER_RETURN_PLUS_DIRECT_DURABLE_INSPECTION",
                "caller_output_digest": sha256(canonical(output).encode("utf-8")).hexdigest(),
                "semantic_signature": signature,
                "outcome": "PASS",
            })
        if signatures[0] != signatures[1]:
            raise WitnessRefused("HUMAN_MODEL_PARITY_DIVERGED")

        spoofed = json.loads(json.dumps(outputs["HUMAN"]))
        spoofed["returned_receipt"]["actor"] = "mallory"
        spoofed_defects = crossing_defects(
            ROOT, states["HUMAN"], spoofed, "gateway-witness-human", "HUMAN"
        )
        if "TERMINAL_RECEIPT_MISMATCH" not in spoofed_defects:
            raise WitnessRefused("OBSERVER_ACCEPTED_SPOOFED_RETURN")

        tampered = workspace / "tampered"
        _tamper_journal(states["HUMAN"], tampered)
        tamper_defects = crossing_defects(
            ROOT, tampered, outputs["HUMAN"], "gateway-witness-human", "HUMAN"
        )
        if "JOURNAL_CHAIN_INVALID" not in tamper_defects:
            raise WitnessRefused("OBSERVER_ACCEPTED_TAMPERED_JOURNAL")
        observations.extend([
            {"case": "spoofed-caller-return", "outcome": "REFUSED",
             "reason": "TERMINAL_RECEIPT_MISMATCH"},
            {"case": "tampered-gateway-journal", "outcome": "REFUSED",
             "reason": "JOURNAL_CHAIN_INVALID"},
        ])

    receipt = {
        "schema": "soveraeign-gateway-observation-candidate/v1",
        "witness_id": witness_id,
        "artifact_commit": expected_commit,
        "effect_class": "RECORD_LOCAL",
        "started_at": started,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "outcome": "PASS",
        "observations": observations,
        "standing_claim": "OBSERVATION_CANDIDATE_SETTLES_NOTHING",
        "owner_acceptance": "PENDING_BDO",
    }
    receipt["receipt_digest"] = sha256(canonical(receipt).encode("utf-8")).hexdigest()
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--witness-id", required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        if not args.witness_id.strip():
            raise WitnessRefused("WITNESS_ID_REQUIRED")
        if args.output:
            output = args.output.resolve()
            if output == ROOT or ROOT in output.parents:
                raise WitnessRefused("OUTPUT_MUST_BE_OUTSIDE_REPOSITORY")
        receipt = run_witness(args.witness_id.strip(), args.expected_commit)
        encoded = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.write_text(encoded, encoding="utf-8")
        else:
            print(encoded, end="")
        return 0
    except (WitnessRefused, OSError, ValueError, subprocess.SubprocessError) as error:
        print(json.dumps({"outcome": "REFUSED", "reason": str(error)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
