#!/usr/bin/env python3
"""Plan and render the provisional customer-owned deployment topology."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from deployment_kubernetes import DeploymentRefused, render_bundle, verify_bundle
from infrastructure import load_manifest as load_custody_manifest
from infrastructure import manifest_digest


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "infrastructure" / "phase-i.topology.json"
DEFAULT_CUSTODY_MANIFEST = ROOT / "infrastructure" / "phase-i.local.json"
ROLES = {"gateway", "broker", "queue", "federation"}


def load_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise DeploymentRefused("MANIFEST_NOT_OBJECT")
    defects = validate_manifest(value)
    if defects:
        raise DeploymentRefused("; ".join(defects))
    return value


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    """Return all topology defects without mutating the manifest."""
    defects: list[str] = []
    if manifest.get("schema") != "soveraeign-portable-topology/v1":
        defects.append("SCHEMA_UNSUPPORTED")
    if manifest.get("profile") != "CUSTOMER_OWNED_PORTABLE":
        defects.append("PROFILE_UNSUPPORTED")
    node = manifest.get("node") or {}
    roles = node.get("roles") or {}
    if node.get("replicas") != 1:
        defects.append("MULTI_WRITER_NOT_ADMITTED")
    if node.get("custody_manifest") != "phase-i.local.json":
        defects.append("LOCAL_CUSTODY_REFERENCE_LOST")
    expected_activation = {
        "policy": "VERIFY_ONLY",
        "expected_uid": 65532,
        "expected_gid": 65532,
        "script": "/opt/soveraeign/scripts/custody_activation.py",
        "receipt_directory": "receipts/custody-activations",
    }
    if node.get("custody_activation") != expected_activation:
        defects.append("CUSTODY_ACTIVATION_CONTRACT_WIDENED")
    if set(roles) != ROLES:
        defects.append("ROLE_SET_INVALID")
    for name in ROLES:
        role = roles.get(name) or {}
        if role.get("placement") != "IN_NODE":
            defects.append(f"ROLE_PREMATURELY_DISTRIBUTED:{name}")
        if role.get("authority") != "NONE":
            defects.append(f"ROLE_AUTHORITY_INFLATED:{name}")
    if (roles.get("queue") or {}).get("system_of_record") is not False:
        defects.append("QUEUE_AUTHORITY_INFLATION")
    federation = roles.get("federation") or {}
    if federation.get("state") != "DISABLED" or federation.get("exposure") != "NONE":
        defects.append("FEDERATION_PREMATURELY_ENABLED")
    gateway = roles.get("gateway") or {}
    if gateway.get("terminal_pull") is not True or gateway.get("guard_policy") != "REQUIRED":
        defects.append("GATEWAY_GUARD_MISSING")
    if gateway.get("capacity") != {"max_inflight": 1, "overflow": "REFUSE"}:
        defects.append("GATEWAY_CAPACITY_UNBOUNDED")
    if gateway.get("patrol") != {"mode": "OBSERVE_ONLY", "authority": "NONE"}:
        defects.append("GATEWAY_PATROL_AUTHORITY_INFLATED")
    deployment = manifest.get("deployment") or {}
    local = deployment.get("local") or {}
    kubernetes = deployment.get("customer_kubernetes") or {}
    if local.get("execution") != "LOCAL_PROCESS" or local.get("bind") != "127.0.0.1":
        defects.append("LOCAL_PROFILE_WIDENED")
    if kubernetes.get("service_type") != "ClusterIP":
        defects.append("PUBLIC_SERVICE_NOT_ADMITTED")
    if kubernetes.get("network_default") != "DENY":
        defects.append("NETWORK_DEFAULT_NOT_DENY")
    if kubernetes.get("custody_claim") != "REQUIRED_AT_RENDER":
        defects.append("CUSTOMER_CUSTODY_NOT_REQUIRED")
    if kubernetes.get("cluster_mutation") != "EXTERNAL_OWNER_ACTION":
        defects.append("CLUSTER_EFFECT_CONCEALED")
    policy = manifest.get("policy") or {}
    expected = {"provider_required": False, "external_effects": "REFUSE",
                "public_exposure": "FORBID", "embedded_secrets": "FORBID",
                "mutable_images": "FORBID"}
    for key, value in expected.items():
        if policy.get(key) != value:
            defects.append(f"POLICY_WIDENED:{key}")
    return defects


def custody_binding(custody_manifest: dict[str, Any]) -> dict[str, Any]:
    """Build the exact local-contract binding carried into a pod."""
    return {
        "manifest": custody_manifest,
        "manifest_digest": manifest_digest(custody_manifest),
        "paths": custody_manifest["custody"]["paths"],
        "directory_mode": custody_manifest["custody"]["directory_mode"],
        "receipt_mode": custody_manifest["custody"]["receipt_mode"],
    }


def plan(manifest: dict[str, Any], target: str,
         custody_manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    defects = validate_manifest(manifest)
    if defects:
        raise DeploymentRefused("; ".join(defects))
    if target not in {"local", "customer-kubernetes"}:
        raise DeploymentRefused("TARGET_UNSUPPORTED")
    custody_manifest = custody_manifest or load_custody_manifest(DEFAULT_CUSTODY_MANIFEST)
    binding = custody_binding(custody_manifest)
    roles = manifest["node"]["roles"]
    return {
        "schema": "soveraeign-deployment-plan/v1", "target": target, "replicas": 1,
        "custody_manifest": manifest["node"]["custody_manifest"],
        "custody_manifest_digest": binding["manifest_digest"], "custody_paths": binding["paths"],
        "custody_activation_policy": manifest["node"]["custody_activation"]["policy"],
        "gateway": {"exposure": "LOOPBACK" if target == "local" else roles["gateway"]["exposure"],
                    "guard_policy": roles["gateway"]["guard_policy"], "max_inflight": 1,
                    "patrol": roles["gateway"]["patrol"]["mode"], "terminal_pull": True},
        "broker": "IN_PROCESS_NON_AUTHORITATIVE", "queue": "IN_PROCESS_NON_AUTHORITATIVE",
        "federation": "DISABLED",
        "cluster_effect": "NONE" if target == "local" else "EXTERNAL_OWNER_ACTION",
    }


def render_kubernetes(manifest: dict[str, Any], image: str, custody_claim: str, *,
                      custody_manifest: dict[str, Any] | None = None, replicas: int = 1,
                      service_type: str = "ClusterIP", federation: bool = False,
                      custody_activation_policy: str = "VERIFY_ONLY") -> dict[str, Any]:
    custody_manifest = custody_manifest or load_custody_manifest(DEFAULT_CUSTODY_MANIFEST)
    plan(manifest, "customer-kubernetes", custody_manifest)
    return render_bundle(manifest, custody_binding(custody_manifest), image, custody_claim,
                         replicas=replicas, service_type=service_type, federation=federation,
                         custody_activation_policy=custody_activation_policy)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("validate", "plan", "render", "verify"))
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--custody-manifest", type=Path, default=DEFAULT_CUSTODY_MANIFEST)
    parser.add_argument("--target", choices=("local", "customer-kubernetes"), default="local")
    parser.add_argument("--image")
    parser.add_argument("--custody-claim")
    parser.add_argument("--replicas", type=int, default=1)
    parser.add_argument("--service-type", default="ClusterIP")
    parser.add_argument("--federation", action="store_true")
    parser.add_argument("--custody-activation-policy", default="VERIFY_ONLY")
    args = parser.parse_args(argv)
    try:
        manifest = load_manifest(args.manifest)
        local_manifest = load_custody_manifest(args.custody_manifest)
        if args.operation == "validate":
            result: object = {"outcome": "PASS", "profile": manifest["profile"],
                              "custody_manifest_digest": manifest_digest(local_manifest)}
        elif args.operation == "plan":
            result = plan(manifest, args.target, local_manifest)
        else:
            if args.target != "customer-kubernetes" or args.image is None or args.custody_claim is None:
                raise DeploymentRefused("KUBERNETES_TARGET_IMAGE_AND_CUSTODY_REQUIRED")
            bundle = render_kubernetes(manifest, args.image, args.custody_claim,
                                       custody_manifest=local_manifest, replicas=args.replicas,
                                       service_type=args.service_type, federation=args.federation,
                                       custody_activation_policy=args.custody_activation_policy)
            if args.operation == "render":
                result = bundle
            else:
                defects = verify_bundle(bundle)
                result = {"outcome": "FAIL" if defects else "PASS", "defects": defects}
                print(json.dumps(result, indent=2, sort_keys=True))
                return 1 if defects else 0
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (DeploymentRefused, OSError, ValueError) as error:
        print(json.dumps({"outcome": "REFUSED", "reason": str(error)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
