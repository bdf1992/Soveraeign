#!/usr/bin/env python3
"""Plan and render the provisional customer-owned deployment topology."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "infrastructure" / "phase-i.topology.json"
ROLES = {"gateway", "broker", "queue", "federation"}
PINNED_IMAGE = re.compile(r"^[^\s@]+@sha256:[0-9a-f]{64}$")
RESOURCE_NAME = re.compile(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$")


class DeploymentRefused(RuntimeError):
    """The requested deployment crosses the admitted customer-owned boundary."""


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
    if set(roles) != ROLES:
        defects.append("ROLE_SET_INVALID")
    for name in ROLES:
        role = roles.get(name) or {}
        if role.get("placement") != "IN_NODE":
            defects.append(f"ROLE_PREMATURELY_DISTRIBUTED:{name}")
        if role.get("authority") != "NONE":
            defects.append(f"ROLE_AUTHORITY_INFLATED:{name}")
    queue = roles.get("queue") or {}
    if queue.get("system_of_record") is not False:
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
    expected = {
        "provider_required": False,
        "external_effects": "REFUSE",
        "public_exposure": "FORBID",
        "embedded_secrets": "FORBID",
        "mutable_images": "FORBID",
    }
    for key, value in expected.items():
        if policy.get(key) != value:
            defects.append(f"POLICY_WIDENED:{key}")
    return defects


def plan(manifest: dict[str, Any], target: str) -> dict[str, Any]:
    """Describe one deployment profile without filesystem or cluster effects."""
    defects = validate_manifest(manifest)
    if defects:
        raise DeploymentRefused("; ".join(defects))
    if target not in {"local", "customer-kubernetes"}:
        raise DeploymentRefused("TARGET_UNSUPPORTED")
    roles = manifest["node"]["roles"]
    return {
        "schema": "soveraeign-deployment-plan/v1",
        "target": target,
        "replicas": 1,
        "custody_manifest": manifest["node"]["custody_manifest"],
        "gateway": {
            "exposure": "LOOPBACK" if target == "local" else roles["gateway"]["exposure"],
            "guard_policy": roles["gateway"]["guard_policy"],
            "max_inflight": roles["gateway"]["capacity"]["max_inflight"],
            "patrol": roles["gateway"]["patrol"]["mode"],
            "terminal_pull": roles["gateway"]["terminal_pull"],
        },
        "broker": "IN_PROCESS_NON_AUTHORITATIVE",
        "queue": "IN_PROCESS_NON_AUTHORITATIVE",
        "federation": "DISABLED",
        "cluster_effect": "NONE" if target == "local" else "EXTERNAL_OWNER_ACTION",
    }


def _metadata(name: str, namespace: str | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {"name": name, "labels": {"app.kubernetes.io/part-of": "soveraeign"}}
    if namespace:
        value["namespace"] = namespace
    return value


def render_kubernetes(
    manifest: dict[str, Any], image: str, custody_claim: str, *, replicas: int = 1,
    service_type: str = "ClusterIP", federation: bool = False,
) -> dict[str, Any]:
    """Render provider-neutral Kubernetes JSON; never contact or mutate a cluster."""
    plan(manifest, "customer-kubernetes")
    if not PINNED_IMAGE.fullmatch(image):
        raise DeploymentRefused("IMAGE_DIGEST_REQUIRED")
    if len(custody_claim) > 63 or not RESOURCE_NAME.fullmatch(custody_claim):
        raise DeploymentRefused("CUSTOMER_CUSTODY_CLAIM_REQUIRED")
    if replicas != 1:
        raise DeploymentRefused("MULTI_WRITER_NOT_ADMITTED")
    if service_type != "ClusterIP":
        raise DeploymentRefused("PUBLIC_SERVICE_NOT_ADMITTED")
    if federation:
        raise DeploymentRefused("FEDERATION_PREMATURELY_ENABLED")

    settings = manifest["deployment"]["customer_kubernetes"]
    namespace = settings["namespace"]
    labels = {"app.kubernetes.io/name": "soveraeign", "app.kubernetes.io/component": "node"}
    pod_security = {"runAsNonRoot": True, "seccompProfile": {"type": "RuntimeDefault"}, "fsGroup": 65532}
    container_security = {
        "allowPrivilegeEscalation": False,
        "capabilities": {"drop": ["ALL"]},
        "readOnlyRootFilesystem": True,
        "runAsNonRoot": True,
        "runAsUser": 65532,
    }
    config = {
        "SOVERAEIGN_GATEWAY_MODE": "POLICY_GUARDED_TERMINAL_PULL",
        "SOVERAEIGN_GATEWAY_MAX_INFLIGHT": "1",
        "SOVERAEIGN_GATEWAY_PATROL_MODE": "OBSERVE_ONLY",
        "SOVERAEIGN_BROKER_MODE": "IN_PROCESS_NON_AUTHORITATIVE",
        "SOVERAEIGN_QUEUE_MODE": "IN_PROCESS_NON_AUTHORITATIVE",
        "SOVERAEIGN_FEDERATION_MODE": "DISABLED",
        "SOVERAEIGN_CUSTODY_ROOT": "/var/lib/soveraeign",
    }
    items = [
        {"apiVersion": "v1", "kind": "Namespace", "metadata": {
            "name": namespace,
            "labels": {"app.kubernetes.io/part-of": "soveraeign",
                       "pod-security.kubernetes.io/enforce": "restricted"}}},
        {"apiVersion": "v1", "kind": "ServiceAccount", "metadata": _metadata("soveraeign-node", namespace),
         "automountServiceAccountToken": False},
        {"apiVersion": "v1", "kind": "ConfigMap", "metadata": _metadata("soveraeign-topology", namespace),
         "data": config},
        {"apiVersion": "apps/v1", "kind": "Deployment", "metadata": _metadata("soveraeign-node", namespace),
         "spec": {"replicas": 1, "strategy": {"type": "Recreate"}, "selector": {"matchLabels": labels},
                  "template": {"metadata": {"labels": labels}, "spec": {
                      "serviceAccountName": "soveraeign-node", "automountServiceAccountToken": False,
                      "securityContext": pod_security,
                      "containers": [{"name": "node", "image": image, "imagePullPolicy": "IfNotPresent",
                                      "ports": [{"name": "gateway", "containerPort": settings["gateway_port"]}],
                                      "envFrom": [{"configMapRef": {"name": "soveraeign-topology"}}],
                                      "securityContext": container_security,
                                      "volumeMounts": [{"name": "custody", "mountPath": "/var/lib/soveraeign"}]}],
                      "volumes": [{"name": "custody", "persistentVolumeClaim": {"claimName": custody_claim}}]}}}},
        {"apiVersion": "v1", "kind": "Service", "metadata": _metadata("soveraeign-gateway", namespace),
         "spec": {"type": "ClusterIP", "selector": labels,
                  "ports": [{"name": "gateway", "port": settings["gateway_port"],
                             "targetPort": "gateway"}]}},
        {"apiVersion": "networking.k8s.io/v1", "kind": "NetworkPolicy",
         "metadata": _metadata("soveraeign-default-deny", namespace),
         "spec": {"podSelector": {}, "policyTypes": ["Ingress", "Egress"], "ingress": [], "egress": []}},
        {"apiVersion": "networking.k8s.io/v1", "kind": "NetworkPolicy",
         "metadata": _metadata("soveraeign-gateway-clients", namespace),
         "spec": {"podSelector": {"matchLabels": labels}, "policyTypes": ["Ingress"],
                  "ingress": [{"from": [{"namespaceSelector": {"matchLabels": {
                      "soveraeign.io/gateway-client": "true"}}}],
                      "ports": [{"protocol": "TCP", "port": settings["gateway_port"]}]}]}},
    ]
    return {"apiVersion": "v1", "kind": "List", "items": items}


def verify_bundle(bundle: dict[str, Any]) -> list[str]:
    """Independently observe the safety properties of a rendered bundle."""
    defects: list[str] = []
    items = bundle.get("items") if bundle.get("kind") == "List" else None
    if not isinstance(items, list):
        return ["BUNDLE_NOT_KUBERNETES_LIST"]
    kinds = [item.get("kind") for item in items if isinstance(item, dict)]
    if any(kind in {"Secret", "Ingress", "PersistentVolumeClaim"} for kind in kinds):
        defects.append("UNADMITTED_RESOURCE_KIND")
    services = [item for item in items if item.get("kind") == "Service"]
    if len(services) != 1 or services[0].get("spec", {}).get("type") != "ClusterIP":
        defects.append("GATEWAY_EXPOSURE_UNSAFE")
    deployments = [item for item in items if item.get("kind") == "Deployment"]
    if len(deployments) != 1:
        defects.append("NODE_DEPLOYMENT_MISSING")
        return defects
    spec = deployments[0]["spec"]
    pod = spec["template"]["spec"]
    container = pod["containers"][0]
    security = container.get("securityContext", {})
    if spec.get("replicas") != 1 or spec.get("strategy", {}).get("type") != "Recreate":
        defects.append("MULTI_WRITER_SAFETY_LOST")
    if not PINNED_IMAGE.fullmatch(container.get("image", "")):
        defects.append("IMAGE_NOT_IMMUTABLE")
    if pod.get("automountServiceAccountToken") is not False:
        defects.append("SERVICE_ACCOUNT_TOKEN_MOUNTED")
    if security.get("readOnlyRootFilesystem") is not True or security.get("runAsNonRoot") is not True:
        defects.append("CONTAINER_SECURITY_UNSAFE")
    if security.get("capabilities", {}).get("drop") != ["ALL"]:
        defects.append("CONTAINER_CAPABILITIES_NOT_DROPPED")
    claims = [volume.get("persistentVolumeClaim", {}).get("claimName")
              for volume in pod.get("volumes", []) if volume.get("name") == "custody"]
    if len(claims) != 1 or not RESOURCE_NAME.fullmatch(claims[0] or ""):
        defects.append("CUSTOMER_CUSTODY_CLAIM_MISSING")
    configs = [item for item in items if item.get("kind") == "ConfigMap"]
    if len(configs) != 1 or configs[0].get("data", {}).get("SOVERAEIGN_FEDERATION_MODE") != "DISABLED":
        defects.append("FEDERATION_NOT_DISABLED")
    policies = [item for item in items if item.get("kind") == "NetworkPolicy"]
    if not any(policy.get("spec", {}).get("egress") == [] for policy in policies):
        defects.append("DEFAULT_DENY_EGRESS_MISSING")
    return defects


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("validate", "plan", "render", "verify"))
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--target", choices=("local", "customer-kubernetes"), default="local")
    parser.add_argument("--image")
    parser.add_argument("--custody-claim")
    parser.add_argument("--replicas", type=int, default=1)
    parser.add_argument("--service-type", default="ClusterIP")
    parser.add_argument("--federation", action="store_true")
    args = parser.parse_args(argv)
    try:
        manifest = load_manifest(args.manifest)
        if args.operation == "validate":
            result: object = {"outcome": "PASS", "profile": manifest["profile"]}
        elif args.operation == "plan":
            result = plan(manifest, args.target)
        else:
            if args.target != "customer-kubernetes" or args.image is None or args.custody_claim is None:
                raise DeploymentRefused("KUBERNETES_TARGET_IMAGE_AND_CUSTODY_REQUIRED")
            bundle = render_kubernetes(manifest, args.image, args.custody_claim, replicas=args.replicas,
                                       service_type=args.service_type, federation=args.federation)
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
