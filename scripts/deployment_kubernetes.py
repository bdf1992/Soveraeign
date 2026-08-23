"""Pure Kubernetes rendering and verification for the portable topology."""

from __future__ import annotations

from hashlib import sha256
import json
import re
from typing import Any


PINNED_IMAGE = re.compile(r"^[^\s@]+@sha256:[0-9a-f]{64}$")
RESOURCE_NAME = re.compile(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$")
CUSTODY_ROOT = "/var/lib/soveraeign"
CONTRACT_PATH = "/etc/soveraeign/custody/phase-i.local.json"


class DeploymentRefused(RuntimeError):
    """The requested deployment crosses the admitted customer-owned boundary."""


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _metadata(name: str, namespace: str | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {"name": name, "labels": {"app.kubernetes.io/part-of": "soveraeign"}}
    if namespace:
        value["namespace"] = namespace
    return value


def render_bundle(manifest: dict[str, Any], binding: dict[str, Any], image: str,
                  custody_claim: str, *, replicas: int = 1,
                  service_type: str = "ClusterIP", federation: bool = False,
                  custody_activation_policy: str = "VERIFY_ONLY") -> dict[str, Any]:
    """Render provider-neutral Kubernetes JSON; never contact or mutate a cluster."""
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
    if custody_activation_policy not in {"VERIFY_ONLY", "VERIFY_OR_INITIALIZE_EMPTY"}:
        raise DeploymentRefused("CUSTODY_ACTIVATION_POLICY_UNSUPPORTED")
    settings = manifest["deployment"]["customer_kubernetes"]
    activation = manifest["node"]["custody_activation"]
    namespace = settings["namespace"]
    labels = {"app.kubernetes.io/name": "soveraeign", "app.kubernetes.io/component": "node"}
    pod_security = {"runAsNonRoot": True, "runAsUser": 65532, "runAsGroup": 65532,
                    "seccompProfile": {"type": "RuntimeDefault"}, "fsGroup": 65532}
    container_security = {"allowPrivilegeEscalation": False, "capabilities": {"drop": ["ALL"]},
                          "readOnlyRootFilesystem": True, "runAsNonRoot": True,
                          "runAsUser": 65532, "runAsGroup": 65532}
    config = {
        "SOVERAEIGN_GATEWAY_MODE": "POLICY_GUARDED_TERMINAL_PULL",
        "SOVERAEIGN_GATEWAY_MAX_INFLIGHT": "1",
        "SOVERAEIGN_GATEWAY_PATROL_MODE": "OBSERVE_ONLY",
        "SOVERAEIGN_BROKER_MODE": "IN_PROCESS_NON_AUTHORITATIVE",
        "SOVERAEIGN_QUEUE_MODE": "IN_PROCESS_NON_AUTHORITATIVE",
        "SOVERAEIGN_FEDERATION_MODE": "DISABLED",
        "SOVERAEIGN_CUSTODY_ROOT": CUSTODY_ROOT,
        "SOVERAEIGN_CUSTODY_MANIFEST_DIGEST": binding["manifest_digest"],
        "SOVERAEIGN_CUSTODY_PATHS": json.dumps(binding["paths"], sort_keys=True,
                                                separators=(",", ":")),
        "SOVERAEIGN_CUSTODY_ACTIVATION_POLICY": custody_activation_policy,
        "SOVERAEIGN_CUSTODY_ACTIVATION_RECEIPTS": f"{CUSTODY_ROOT}/{activation['receipt_directory']}",
        "phase-i.local.json": json.dumps(binding["manifest"], indent=2, sort_keys=True) + "\n",
    }
    mounts = [{"name": "custody", "mountPath": CUSTODY_ROOT},
              {"name": "custody-contract", "mountPath": "/etc/soveraeign/custody", "readOnly": True}]
    init = {
        "name": "custody-activation", "image": image, "imagePullPolicy": "IfNotPresent",
        "command": ["python", activation["script"]],
        "args": ["--manifest", CONTRACT_PATH, "--root", CUSTODY_ROOT, "--policy",
                 custody_activation_policy,
                 "--expected-uid", str(activation["expected_uid"]),
                 "--expected-gid", str(activation["expected_gid"])],
        "securityContext": container_security, "volumeMounts": mounts,
    }
    node = {
        "name": "node", "image": image, "imagePullPolicy": "IfNotPresent",
        "ports": [{"name": "gateway", "containerPort": settings["gateway_port"]}],
        "envFrom": [{"configMapRef": {"name": "soveraeign-topology"}}],
        "securityContext": container_security, "volumeMounts": mounts,
    }
    items = [
        {"apiVersion": "v1", "kind": "Namespace", "metadata": {
            "name": namespace, "labels": {"app.kubernetes.io/part-of": "soveraeign",
            "pod-security.kubernetes.io/enforce": "restricted"}}},
        {"apiVersion": "v1", "kind": "ServiceAccount",
         "metadata": _metadata("soveraeign-node", namespace), "automountServiceAccountToken": False},
        {"apiVersion": "v1", "kind": "ConfigMap",
         "metadata": _metadata("soveraeign-topology", namespace), "data": config},
        {"apiVersion": "apps/v1", "kind": "Deployment",
         "metadata": _metadata("soveraeign-node", namespace), "spec": {
             "replicas": 1, "strategy": {"type": "Recreate"}, "selector": {"matchLabels": labels},
             "template": {"metadata": {"labels": labels, "annotations": {
                 "soveraeign.io/custody-manifest-digest": binding["manifest_digest"]}}, "spec": {
                     "serviceAccountName": "soveraeign-node", "automountServiceAccountToken": False,
                     "securityContext": pod_security, "initContainers": [init], "containers": [node],
                     "volumes": [
                         {"name": "custody", "persistentVolumeClaim": {"claimName": custody_claim}},
                         {"name": "custody-contract", "configMap": {"name": "soveraeign-topology",
                          "items": [{"key": "phase-i.local.json", "path": "phase-i.local.json"}]}},
                     ]}}}},
        {"apiVersion": "v1", "kind": "Service", "metadata": _metadata("soveraeign-gateway", namespace),
         "spec": {"type": "ClusterIP", "selector": labels, "ports": [{"name": "gateway",
                  "port": settings["gateway_port"], "targetPort": "gateway"}]}},
        {"apiVersion": "networking.k8s.io/v1", "kind": "NetworkPolicy",
         "metadata": _metadata("soveraeign-default-deny", namespace),
         "spec": {"podSelector": {}, "policyTypes": ["Ingress", "Egress"], "ingress": [], "egress": []}},
        {"apiVersion": "networking.k8s.io/v1", "kind": "NetworkPolicy",
         "metadata": _metadata("soveraeign-gateway-clients", namespace), "spec": {
             "podSelector": {"matchLabels": labels}, "policyTypes": ["Ingress"], "ingress": [{
                 "from": [{"namespaceSelector": {"matchLabels": {"soveraeign.io/gateway-client": "true"}}}],
                 "ports": [{"protocol": "TCP", "port": settings["gateway_port"]}]}]}},
    ]
    return {"apiVersion": "v1", "kind": "List", "items": items}


def verify_bundle(bundle: dict[str, Any]) -> list[str]:
    """Observe safety and local-contract binding properties of a rendered bundle."""
    defects: list[str] = []
    items = bundle.get("items") if bundle.get("kind") == "List" else None
    if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
        return ["BUNDLE_NOT_KUBERNETES_LIST"]
    kinds = [item.get("kind") for item in items]
    if any(kind in {"Secret", "Ingress", "PersistentVolumeClaim"} for kind in kinds):
        defects.append("UNADMITTED_RESOURCE_KIND")
    services = [item for item in items if item.get("kind") == "Service"]
    if len(services) != 1 or services[0].get("spec", {}).get("type") != "ClusterIP":
        defects.append("GATEWAY_EXPOSURE_UNSAFE")
    deployments = [item for item in items if item.get("kind") == "Deployment"]
    if len(deployments) != 1:
        return defects + ["NODE_DEPLOYMENT_MISSING"]
    spec = deployments[0].get("spec", {})
    template = spec.get("template", {})
    pod = template.get("spec", {})
    containers, inits = pod.get("containers", []), pod.get("initContainers", [])
    if len(containers) != 1 or len(inits) != 1:
        return defects + ["CUSTODY_ACTIVATION_GATE_MISSING"]
    container, init = containers[0], inits[0]
    if spec.get("replicas") != 1 or spec.get("strategy", {}).get("type") != "Recreate":
        defects.append("MULTI_WRITER_SAFETY_LOST")
    if not PINNED_IMAGE.fullmatch(container.get("image", "")) or init.get("image") != container.get("image"):
        defects.append("IMAGE_NOT_IMMUTABLE")
    if pod.get("automountServiceAccountToken") is not False:
        defects.append("SERVICE_ACCOUNT_TOKEN_MOUNTED")
    for candidate in (container, init):
        security = candidate.get("securityContext", {})
        if security.get("readOnlyRootFilesystem") is not True or security.get("runAsUser") != 65532:
            defects.append("CONTAINER_SECURITY_UNSAFE")
        if security.get("capabilities", {}).get("drop") != ["ALL"]:
            defects.append("CONTAINER_CAPABILITIES_NOT_DROPPED")
    claims = [v.get("persistentVolumeClaim", {}).get("claimName") for v in pod.get("volumes", [])
              if v.get("name") == "custody"]
    if len(claims) != 1 or not RESOURCE_NAME.fullmatch(claims[0] or ""):
        defects.append("CUSTOMER_CUSTODY_CLAIM_MISSING")
    configs = [item for item in items if item.get("kind") == "ConfigMap"]
    data = configs[0].get("data", {}) if len(configs) == 1 else {}
    if data.get("SOVERAEIGN_FEDERATION_MODE") != "DISABLED":
        defects.append("FEDERATION_NOT_DISABLED")
    try:
        local = json.loads(data["phase-i.local.json"])
        digest = sha256(_canonical(local)).hexdigest()
        paths = json.loads(data["SOVERAEIGN_CUSTODY_PATHS"])
    except (KeyError, TypeError, ValueError):
        defects.append("CUSTODY_CONTRACT_NOT_EMBEDDED")
        digest, paths, local = "", {}, {}
    declared_digest = data.get("SOVERAEIGN_CUSTODY_MANIFEST_DIGEST")
    annotation = template.get("metadata", {}).get("annotations", {}).get(
        "soveraeign.io/custody-manifest-digest")
    if digest != declared_digest or digest != annotation:
        defects.append("CUSTODY_MANIFEST_DIGEST_UNBOUND")
    if paths != local.get("custody", {}).get("paths") or set(paths) != {
            "record", "payloads", "projections", "receipts", "work"}:
        defects.append("CUSTODY_PATH_MAPPING_UNBOUND")
    args = init.get("args", [])
    configured_policy = data.get("SOVERAEIGN_CUSTODY_ACTIVATION_POLICY")
    if (init.get("name") != "custody-activation" or init.get("command") != [
            "python", "/opt/soveraeign/scripts/custody_activation.py"] or
            configured_policy not in {"VERIFY_ONLY", "VERIFY_OR_INITIALIZE_EMPTY"} or
            configured_policy not in args or CONTRACT_PATH not in args or CUSTODY_ROOT not in args):
        defects.append("CUSTODY_ACTIVATION_GATE_MISSING")
    if data.get("SOVERAEIGN_CUSTODY_ACTIVATION_RECEIPTS") != (
            CUSTODY_ROOT + "/receipts/custody-activations"):
        defects.append("CUSTODY_ACTIVATION_RECEIPT_UNBOUND")
    policies = [item for item in items if item.get("kind") == "NetworkPolicy"]
    if not any(policy.get("spec", {}).get("egress") == [] for policy in policies):
        defects.append("DEFAULT_DENY_EGRESS_MISSING")
    return list(dict.fromkeys(defects))
