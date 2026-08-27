#!/usr/bin/env python3
"""Run the infrastructure witness protocol without importing its implementations.

This module owns the protocol run and its command line only. The stages it drives
live in ``witness_stages``, which reaches every participant through a subprocess and
inspects the result independently, so nothing here imports an implementation it is
supposed to be witnessing.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from typing import Any

from witness_observe import canonical_bytes
from witness_stages import (
    ROOT,
    WitnessRefused,
    exercise_activation,
    exercise_deployment,
    exercise_local,
    exercise_secret_gate,
    run_command,
)


def _git_preconditions(expected_commit: str) -> dict[str, Any]:
    commit = run_command(["git", "rev-parse", "HEAD"])["stdout"].strip()
    if commit != expected_commit:
        raise WitnessRefused(f"COMMIT_MISMATCH:{commit}")
    status_result = run_command(["git", "status", "--porcelain", "--untracked-files=all"])
    if status_result["stdout"]:
        raise WitnessRefused("CHECKOUT_NOT_CLEAN")
    return {"commit": commit, "clean": True}


def run_witness(witness_id: str, expected_commit: str) -> dict[str, Any]:
    """Execute the clean-room protocol and return an addressed candidate receipt."""
    started = datetime.now(timezone.utc).isoformat()
    git = _git_preconditions(expected_commit)
    repository = run_command([sys.executable, "scripts/verify.py"])
    repository.pop("stdout")
    with TemporaryDirectory() as raw_temporary:
        temporary = Path(raw_temporary)
        observations = exercise_local(temporary)
        observations.extend(exercise_activation(temporary))
        observations.extend(exercise_deployment())
        observations.append(exercise_secret_gate(temporary))
    receipt = {
        "schema": "soveraeign-infrastructure-witness-candidate/v1",
        "witness_id": witness_id,
        "independence_declared": True,
        "artifact_commit": git["commit"],
        "checkout_clean": git["clean"],
        "started_at": started,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "effect_class": "RECORD_LOCAL",
        "outcome": "PASS",
        "repository_verification": repository,
        "observations": observations,
        "standing_claim": "WITNESS_CANDIDATE_PENDING_REVIEW",
        "owner_acceptance": "PENDING_BDO",
    }
    receipt["receipt_digest"] = sha256(canonical_bytes(receipt)).hexdigest()
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--witness-id", required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--declare-independent", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        if not args.declare_independent:
            raise WitnessRefused("INDEPENDENCE_DECLARATION_REQUIRED")
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
    except (WitnessRefused, OSError, ValueError) as error:
        print(json.dumps({"outcome": "REFUSED", "reason": str(error)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
