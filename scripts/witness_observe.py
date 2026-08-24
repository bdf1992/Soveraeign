"""Independent observations for the infrastructure witness protocol."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import stat
from typing import Any


LOCAL_PATHS = {"record", "payloads", "projections", "receipts", "work"}
RUNTIME_PATHS = {
    "/opt/soveraeign/scripts/custody_activation.py",
    "/opt/soveraeign/scripts/node_runtime.py",
}


def canonical_bytes(value: object) -> bytes:
    """Encode a value for stable receipt addressing."""
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def independent_local_defects(node: Path, manifest: dict[str, Any]) -> list[str]:
    """Inspect materialized custody without calling the implementation verifier."""
    defects: list[str] = []
    receipt_path = node / ".soveraeign-infrastructure.json"
    if not node.is_dir() or node.is_symlink():
        return ["ROOT_UNSAFE"]
    if stat.S_IMODE(node.stat().st_mode) != 0o700:
        defects.append("ROOT_MODE")
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        defects.append("RECEIPT_INVALID")
        receipt = {}
    digest = sha256(canonical_bytes(manifest)).hexdigest()
    if receipt.get("manifest_digest") != digest:
        defects.append("RECEIPT_DIGEST")
    if receipt.get("effect_class") != "RECORD_LOCAL":
        defects.append("RECEIPT_EFFECT")
    paths = manifest.get("custody", {}).get("paths", {})
    if set(paths) != LOCAL_PATHS:
        defects.append("PATH_SET")
        return defects
    expected_paths = {name: str(node.resolve() / relative) for name, relative in paths.items()}
    if (receipt.get("schema") != "soveraeign-infrastructure-receipt/v1" or
            receipt.get("root") != str(node.resolve()) or receipt.get("paths") != expected_paths):
        defects.append("RECEIPT_BINDING")
    root = node.resolve()
    for name, relative in paths.items():
        path = node / relative
        resolved = path.resolve(strict=False)
        if path.is_symlink() or not path.is_dir():
            defects.append(f"PATH_UNSAFE:{name}")
        elif root not in resolved.parents or stat.S_IMODE(path.stat().st_mode) != 0o700:
            defects.append(f"PATH_BOUNDARY:{name}")
    return defects


def independent_activation_defects(node: Path, manifest: dict[str, Any],
                                   receipt: dict[str, Any]) -> list[str]:
    """Inspect custody continuity and an activation receipt without implementation imports."""
    defects: list[str] = []
    digest = sha256(canonical_bytes(manifest)).hexdigest()
    try:
        identity_path = node / ".soveraeign-custody-identity.json"
        identity = json.loads(identity_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ["CUSTODY_IDENTITY_INVALID"]
    if identity.get("manifest_digest") != digest or identity.get("paths") != manifest["custody"]["paths"]:
        defects.append("CUSTODY_IDENTITY_UNBOUND")
    if receipt.get("custody_id") != identity.get("custody_id"):
        defects.append("CUSTODY_CONTINUITY_LOST")
    if receipt.get("manifest_digest") != digest or receipt.get("paths") != manifest["custody"]["paths"]:
        defects.append("ACTIVATION_RECEIPT_UNBOUND")
    receipt_path = node / "receipts" / "custody-activations" / (
        str(receipt.get("activation_id")) + ".json")
    try:
        stored = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        defects.append("ACTIVATION_RECEIPT_MISSING")
    else:
        if stored != receipt or receipt.get("effect_class") != "RECORD_LOCAL":
            defects.append("ACTIVATION_RECEIPT_INVALID")
    return defects


def independent_bundle_defects(bundle: dict[str, Any], custody_claim: str,
                               expected_manifest: dict[str, Any] | None = None,
                               expected_runtime_contract: dict[str, Any] | None = None) -> list[str]:
    """Inspect Kubernetes objects without calling the deployment renderer verifier."""
    defects: list[str] = []
    items = bundle.get("items") if bundle.get("kind") == "List" else None
    if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
        return ["BUNDLE_SHAPE"]
    kinds = [item.get("kind") for item in items]
    if any(kind in {"Secret", "Ingress", "PersistentVolumeClaim"} for kind in kinds):
        defects.append("UNOWNED_RESOURCE")
    services = [item for item in items if item.get("kind") == "Service"]
    if len(services) != 1 or services[0].get("spec", {}).get("type") != "ClusterIP":
        defects.append("PUBLIC_GATEWAY")
    deployments = [item for item in items if item.get("kind") == "Deployment"]
    if len(deployments) != 1:
        return defects + ["DEPLOYMENT_COUNT"]
    spec = deployments[0].get("spec", {})
    template = spec.get("template", {})
    pod = template.get("spec", {})
    containers = pod.get("containers", [])
    if spec.get("replicas") != 1 or spec.get("strategy", {}).get("type") != "Recreate":
        defects.append("MULTI_WRITER")
    if len(containers) != 1:
        return defects + ["CONTAINER_COUNT"]
    container = containers[0]
    initializers = pod.get("initContainers", [])
    if len(initializers) != 1:
        defects.append("CUSTODY_ACTIVATION_GATE")
        initializer = {}
    else:
        initializer = initializers[0]
    security = container.get("securityContext", {})
    if "@sha256:" not in container.get("image", ""):
        defects.append("IMAGE_MUTABLE")
    if pod.get("automountServiceAccountToken") is not False:
        defects.append("TOKEN_MOUNT")
    if security.get("readOnlyRootFilesystem") is not True:
        defects.append("WRITABLE_ROOT")
    if security.get("runAsNonRoot") is not True:
        defects.append("ROOT_USER")
    if security.get("capabilities", {}).get("drop") != ["ALL"]:
        defects.append("CAPABILITIES")
    claims = [
        volume.get("persistentVolumeClaim", {}).get("claimName")
        for volume in pod.get("volumes", [])
        if volume.get("name") == "custody"
    ]
    if claims != [custody_claim]:
        defects.append("CUSTODY_CLAIM")
    configs = [item for item in items if item.get("kind") == "ConfigMap"]
    data = configs[0].get("data", {}) if len(configs) == 1 else {}
    if data.get("SOVERAEIGN_FEDERATION_MODE") != "DISABLED":
        defects.append("FEDERATION_ACTIVE")
    if data.get("SOVERAEIGN_GATEWAY_PATROL_MODE") != "OBSERVE_ONLY":
        defects.append("PATROL_AUTHORITY")
    try:
        carried = json.loads(data["phase-i.local.json"])
        carried_paths = json.loads(data["SOVERAEIGN_CUSTODY_PATHS"])
        carried_digest = sha256(canonical_bytes(carried)).hexdigest()
    except (KeyError, TypeError, ValueError):
        defects.append("CUSTODY_CONTRACT_ABSENT")
        carried, carried_paths, carried_digest = {}, {}, ""
    declared_digest = data.get("SOVERAEIGN_CUSTODY_MANIFEST_DIGEST")
    annotated_digest = template.get("metadata", {}).get("annotations", {}).get(
        "soveraeign.io/custody-manifest-digest")
    if carried_digest != declared_digest or carried_digest != annotated_digest:
        defects.append("CUSTODY_DIGEST_NOMINAL")
    if carried_paths != carried.get("custody", {}).get("paths") or set(carried_paths) != LOCAL_PATHS:
        defects.append("CUSTODY_PATHS_NOMINAL")
    if expected_manifest is not None and carried != expected_manifest:
        defects.append("LOCAL_CONTRACT_SUBSTITUTED")
    args = initializer.get("args", [])
    if (initializer.get("name") != "custody-activation" or
            initializer.get("image") != container.get("image") or
            "VERIFY_ONLY" not in args or "/var/lib/soveraeign" not in args or
            "/etc/soveraeign/custody/phase-i.local.json" not in args):
        defects.append("CUSTODY_ACTIVATION_GATE")
    init_security = initializer.get("securityContext", {})
    if init_security.get("runAsUser") != 65532 or init_security.get("runAsGroup") != 65532:
        defects.append("CUSTODY_ACTIVATION_IDENTITY")
    if data.get("SOVERAEIGN_CUSTODY_ACTIVATION_RECEIPTS") != (
            "/var/lib/soveraeign/receipts/custody-activations"):
        defects.append("ACTIVATION_RECEIPT_PATH")

    try:
        runtime = json.loads(data["phase-i.runtime-image.json"])
        runtime_digest = sha256(canonical_bytes(runtime)).hexdigest()
        runtime_gateway = runtime["gateway"]
        health = runtime_gateway["health"]
    except (KeyError, TypeError, ValueError):
        defects.append("RUNTIME_CONTRACT_ABSENT")
        runtime, runtime_gateway, health, runtime_digest = {}, {}, {}, ""
    runtime_declared = data.get("SOVERAEIGN_RUNTIME_IMAGE_CONTRACT_DIGEST")
    runtime_annotated = template.get("metadata", {}).get("annotations", {}).get(
        "soveraeign.io/runtime-image-contract-digest")
    if runtime_digest != runtime_declared or runtime_digest != runtime_annotated:
        defects.append("RUNTIME_DIGEST_NOMINAL")
    if (runtime.get("python_min") != "3.11" or
            set(runtime.get("required_paths") or []) != RUNTIME_PATHS):
        defects.append("RUNTIME_REQUIREMENTS")
    if expected_runtime_contract is not None and runtime != expected_runtime_contract:
        defects.append("RUNTIME_CONTRACT_SUBSTITUTED")
    if (container.get("command") != runtime.get("entrypoint") or
            container.get("args") != ["--bind", runtime_gateway.get("bind"), "--port",
                                      str(runtime_gateway.get("port"))]):
        defects.append("RUNTIME_ENTRYPOINT")
    if (not container.get("ports") or container["ports"][0].get("containerPort") != 8080 or
            runtime_gateway.get("unactivated_response") != "REFUSE"):
        defects.append("RUNTIME_LISTENER")
    for probe_name, health_name in (("startupProbe", "startup"),
                                    ("readinessProbe", "readiness"),
                                    ("livenessProbe", "liveness")):
        probe = container.get(probe_name, {}).get("httpGet", {})
        if probe.get("path") != health.get(health_name) or probe.get("port") != "gateway":
            defects.append("RUNTIME_HEALTH")
            break
    policies = [item for item in items if item.get("kind") == "NetworkPolicy"]
    if not any(policy.get("spec", {}).get("egress") == [] for policy in policies):
        defects.append("EGRESS_NOT_DENIED")
    return list(dict.fromkeys(defects))
