#!/usr/bin/env python3
"""Run the infrastructure witness protocol without importing its implementations."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from typing import Any

from witness_observe import (
    canonical_bytes,
    independent_activation_defects,
    independent_bundle_defects,
    independent_local_defects,
)


ROOT = Path(__file__).resolve().parents[1]
PINNED_IMAGE = "registry.example/soveraeign@sha256:" + "a" * 64
CUSTODY_CLAIM = "witness-owned-custody"


class WitnessRefused(RuntimeError):
    """The requested witness run cannot establish its declared preconditions."""


def _run(command: list[str], *, cwd: Path = ROOT, expected: int = 0) -> dict[str, Any]:
    result = subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True)
    if result.returncode != expected:
        raise WitnessRefused(
            f"COMMAND_OUTCOME:{' '.join(command[:3])}:{result.returncode}!={expected}"
        )
    return {
        "returncode": result.returncode,
        "stdout_digest": sha256(result.stdout.encode("utf-8")).hexdigest(),
        "stderr_digest": sha256(result.stderr.encode("utf-8")).hexdigest(),
        "stdout": result.stdout,
    }


def _git_preconditions(expected_commit: str) -> dict[str, Any]:
    commit = _run(["git", "rev-parse", "HEAD"])["stdout"].strip()
    if commit != expected_commit:
        raise WitnessRefused(f"COMMIT_MISMATCH:{commit}")
    status_result = _run(["git", "status", "--porcelain", "--untracked-files=all"])
    if status_result["stdout"]:
        raise WitnessRefused("CHECKOUT_NOT_CLEAN")
    return {"commit": commit, "clean": True}


def _expect_refusal(command: list[str], reason: str) -> dict[str, Any]:
    observation = _run(command, expected=2)
    if reason not in observation["stdout"]:
        raise WitnessRefused(f"REFUSAL_REASON_MISSING:{reason}")
    observation.pop("stdout")
    return observation


def _exercise_local(temporary: Path) -> list[dict[str, Any]]:
    manifest_path = ROOT / "infrastructure" / "phase-i.local.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    node = temporary / "node"
    plan = _run([sys.executable, "scripts/infrastructure.py", "plan", "--root", str(node)])
    if node.exists() or '"disposition": "CREATE"' not in plan["stdout"]:
        raise WitnessRefused("PLAN_MUTATED_OR_MISREPORTED")
    apply = _run([sys.executable, "scripts/infrastructure.py", "apply", "--root", str(node)])
    defects = independent_local_defects(node, manifest)
    if defects:
        raise WitnessRefused("LOCAL_OBSERVATION:" + ",".join(defects))

    unmanaged = temporary / "unmanaged"
    unmanaged.mkdir()
    (unmanaged / "foreign.txt").write_text("foreign\n", encoding="utf-8")
    unmanaged_result = _expect_refusal(
        [sys.executable, "scripts/infrastructure.py", "apply", "--root", str(unmanaged)],
        "UNMANAGED_OR_UNSAFE_ROOT",
    )
    drift = json.loads((node / ".soveraeign-infrastructure.json").read_text(encoding="utf-8"))
    drift["manifest_digest"] = "0" * 64
    (node / ".soveraeign-infrastructure.json").write_text(json.dumps(drift), encoding="utf-8")
    drift_result = _run(
        [sys.executable, "scripts/infrastructure.py", "verify", "--root", str(node)], expected=1
    )
    if "MANIFEST_DIGEST_MISMATCH" not in drift_result["stdout"]:
        raise WitnessRefused("RECEIPT_DRIFT_NOT_OBSERVED")
    symlink_node = temporary / "symlink"
    _run([sys.executable, "scripts/infrastructure.py", "apply", "--root", str(symlink_node)])
    (symlink_node / "work").rmdir()
    (symlink_node / "work").symlink_to(symlink_node / "record", target_is_directory=True)
    symlink_result = _run(
        [sys.executable, "scripts/infrastructure.py", "verify", "--root", str(symlink_node)],
        expected=1,
    )
    if "CUSTODY_PATH_MISSING_OR_UNSAFE:work" not in symlink_result["stdout"]:
        raise WitnessRefused("SYMLINK_NOT_OBSERVED")

    permission_node = temporary / "permission"
    _run([sys.executable, "scripts/infrastructure.py", "apply", "--root", str(permission_node)])
    os.chmod(permission_node / "record", 0o755)
    permission_result = _run(
        [sys.executable, "scripts/infrastructure.py", "verify", "--root", str(permission_node)],
        expected=1,
    )
    if "CUSTODY_PERMISSIONS_UNSAFE:record" not in permission_result["stdout"]:
        raise WitnessRefused("PERMISSION_DRIFT_NOT_OBSERVED")

    changed_manifest = json.loads(json.dumps(manifest))
    changed_manifest["custody"]["paths"]["work"] = "alternate-work"
    manifest_path = temporary / "changed-manifest.json"
    manifest_path.write_text(json.dumps(changed_manifest), encoding="utf-8")
    manifest_result = _run([
        sys.executable, "scripts/infrastructure.py", "verify", "--root", str(permission_node),
        "--manifest", str(manifest_path),
    ], expected=1)
    if "MANIFEST_DIGEST_MISMATCH" not in manifest_result["stdout"]:
        raise WitnessRefused("MANIFEST_DRIFT_NOT_OBSERVED")

    concurrency = _run([
        sys.executable, "-m", "unittest", "discover", "-s", "scripts/tests",
        "-p", "test_infrastructure.py", "-v",
    ])
    for result in (plan, apply, drift_result, symlink_result, permission_result,
                   manifest_result, concurrency):
        result.pop("stdout")
    return [
        {"case": "local-plan-no-effect", **plan},
        {"case": "local-apply-independent-inspection", **apply},
        {"case": "unmanaged-root-refusal", **unmanaged_result},
        {"case": "receipt-drift-observed", **drift_result},
        {"case": "symlink-substitution-observed", **symlink_result},
        {"case": "permission-drift-observed", **permission_result},
        {"case": "manifest-drift-observed", **manifest_result},
        {"case": "concurrent-apply-fixture", **concurrency},
    ]


def _exercise_deployment() -> list[dict[str, Any]]:
    render = _run([
        sys.executable, "scripts/deployment.py", "render", "--target", "customer-kubernetes",
        "--image", PINNED_IMAGE, "--custody-claim", CUSTODY_CLAIM,
    ])
    bundle = json.loads(render["stdout"])
    local_manifest = json.loads((ROOT / "infrastructure" / "phase-i.local.json").read_text(
        encoding="utf-8"))
    runtime_contract = json.loads((ROOT / "infrastructure" / "phase-i.runtime-image.json").read_text(
        encoding="utf-8"))
    defects = independent_bundle_defects(
        bundle, CUSTODY_CLAIM, local_manifest, runtime_contract
    )
    if defects:
        raise WitnessRefused("BUNDLE_OBSERVATION:" + ",".join(defects))
    render.pop("stdout")
    cases = [{"case": "kubernetes-independent-inspection", **render}]
    defeating = [
        (["--image", "soveraeign:latest", "--custody-claim", CUSTODY_CLAIM], "IMAGE_DIGEST_REQUIRED"),
        (["--image", PINNED_IMAGE, "--custody-claim", "Not_Valid"], "CUSTODY_CLAIM_REQUIRED"),
        (["--image", PINNED_IMAGE, "--custody-claim", CUSTODY_CLAIM, "--replicas", "2"], "MULTI_WRITER"),
        (["--image", PINNED_IMAGE, "--custody-claim", CUSTODY_CLAIM, "--service-type", "LoadBalancer"], "PUBLIC_SERVICE"),
        (["--image", PINNED_IMAGE, "--custody-claim", CUSTODY_CLAIM, "--federation"], "FEDERATION"),
    ]
    for index, (arguments, reason) in enumerate(defeating, start=1):
        command = [sys.executable, "scripts/deployment.py", "render", "--target",
                   "customer-kubernetes", *arguments]
        cases.append({"case": f"deployment-refusal-{index}", **_expect_refusal(command, reason)})
    return cases


def _exercise_activation(temporary: Path) -> list[dict[str, Any]]:
    manifest = json.loads((ROOT / "infrastructure" / "phase-i.local.json").read_text(
        encoding="utf-8"))
    node = temporary / "activation"
    identity_args = ["--expected-uid", str(os.geteuid()), "--expected-gid", str(os.getegid())]
    empty = _expect_refusal([
        sys.executable, "scripts/custody_activation.py", "--root", str(node), *identity_args,
    ], "EMPTY_CUSTODY_NOT_ACTIVATED")
    initialized = _run([
        sys.executable, "scripts/custody_activation.py", "--root", str(node),
        "--policy", "VERIFY_OR_INITIALIZE_EMPTY", *identity_args,
    ])
    first_receipt = json.loads(initialized["stdout"])
    defects = independent_activation_defects(node, manifest, first_receipt)
    if defects:
        raise WitnessRefused("ACTIVATION_OBSERVATION:" + ",".join(defects))
    restarted = _run([
        sys.executable, "scripts/custody_activation.py", "--root", str(node), *identity_args,
    ])
    second_receipt = json.loads(restarted["stdout"])
    if (second_receipt.get("custody_id") != first_receipt.get("custody_id") or
            second_receipt.get("continuity") != "PRESERVED"):
        raise WitnessRefused("CUSTODY_CONTINUITY_NOT_PRESERVED")
    infrastructure_receipt = node / ".soveraeign-infrastructure.json"
    stale = json.loads(infrastructure_receipt.read_text(encoding="utf-8"))
    stale["manifest_digest"] = "0" * 64
    infrastructure_receipt.write_text(json.dumps(stale), encoding="utf-8")
    stale_result = _expect_refusal([
        sys.executable, "scripts/custody_activation.py", "--root", str(node), *identity_args,
    ], "CUSTODY_PRECONDITION_DRIFT")
    defeating = _run([
        sys.executable, "-m", "unittest", "discover", "-s", "scripts/tests",
        "-p", "test_custody_activation.py", "-v",
    ])
    for result in (initialized, restarted, defeating):
        result.pop("stdout")
    return [
        {"case": "empty-custody-default-refusal", **empty},
        {"case": "explicit-custody-initialization-independent-inspection", **initialized},
        {"case": "custody-restart-continuity", **restarted},
        {"case": "stale-infrastructure-receipt-refusal", **stale_result},
        {"case": "custody-defeating-fixtures", **defeating},
    ]


def _exercise_secret_gate(temporary: Path) -> dict[str, Any]:
    fixture = temporary / "secret-gate"
    (fixture / "scripts").mkdir(parents=True)
    shutil.copy2(ROOT / "scripts" / "lint.py", fixture / "scripts" / "lint.py")
    _run(["git", "init", "--quiet"], cwd=fixture)
    (fixture / ".gitignore").write_text(".env\n", encoding="utf-8")
    synthetic = "gh" + "p_" + "a" * 36
    (fixture / ".env").write_text(f"TOKEN={synthetic}\n", encoding="utf-8")
    _run(["git", "add", ".gitignore"], cwd=fixture)
    _run(["git", "add", "-f", ".env"], cwd=fixture)
    result = _run([sys.executable, "scripts/lint.py"], cwd=fixture, expected=1)
    if ".env" not in result["stdout"] or "possible GitHub token" not in result["stdout"]:
        raise WitnessRefused("FORCE_ADDED_SECRET_NOT_OBSERVED")
    result.pop("stdout")
    return {"case": "force-added-ignored-secret-refusal", **result}


def run_witness(witness_id: str, expected_commit: str) -> dict[str, Any]:
    """Execute the clean-room protocol and return an addressed candidate receipt."""
    started = datetime.now(timezone.utc).isoformat()
    git = _git_preconditions(expected_commit)
    repository = _run([sys.executable, "scripts/verify.py"])
    repository.pop("stdout")
    with TemporaryDirectory() as raw_temporary:
        temporary = Path(raw_temporary)
        observations = _exercise_local(temporary)
        observations.extend(_exercise_activation(temporary))
        observations.extend(_exercise_deployment())
        observations.append(_exercise_secret_gate(temporary))
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
