"""Independent observations for the infrastructure witness protocol."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import stat
from typing import Any


LOCAL_PATHS = {"record", "payloads", "projections", "receipts", "work"}


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
    root = node.resolve()
    for name, relative in paths.items():
        path = node / relative
        resolved = path.resolve(strict=False)
        if path.is_symlink() or not path.is_dir():
            defects.append(f"PATH_UNSAFE:{name}")
        elif root not in resolved.parents or stat.S_IMODE(path.stat().st_mode) != 0o700:
            defects.append(f"PATH_BOUNDARY:{name}")
    return defects


def independent_bundle_defects(bundle: dict[str, Any], custody_claim: str) -> list[str]:
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
    pod = spec.get("template", {}).get("spec", {})
    containers = pod.get("containers", [])
    if spec.get("replicas") != 1 or spec.get("strategy", {}).get("type") != "Recreate":
        defects.append("MULTI_WRITER")
    if len(containers) != 1:
        return defects + ["CONTAINER_COUNT"]
    container = containers[0]
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
    policies = [item for item in items if item.get("kind") == "NetworkPolicy"]
    if not any(policy.get("spec", {}).get("egress") == [] for policy in policies):
        defects.append("EGRESS_NOT_DENIED")
    return defects
