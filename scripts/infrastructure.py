#!/usr/bin/env python3
"""Plan, materialize, and verify the provisional Phase-I local node envelope."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path, PurePath
import stat
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "infrastructure" / "phase-i.local.json"
RECEIPT_NAME = ".soveraeign-infrastructure.json"
LOCK_NAME = ".soveraeign-infrastructure.lock"
REQUIRED_PATHS = {"record", "payloads", "projections", "receipts", "work"}


class InfrastructureRefused(RuntimeError):
    """The requested infrastructure transition is outside the admitted envelope."""


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def manifest_digest(manifest: dict[str, Any]) -> str:
    return sha256(canonical_bytes(manifest)).hexdigest()


def load_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise InfrastructureRefused("MANIFEST_NOT_OBJECT")
    defects = validate_manifest(value)
    if defects:
        raise InfrastructureRefused("; ".join(defects))
    return value


def _valid_relative_path(value: object) -> bool:
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    path = PurePath(value)
    return not path.is_absolute() and all(part not in {"", ".", ".."} for part in path.parts)


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    defects: list[str] = []
    if manifest.get("schema") != "soveraeign-local-node/v1":
        defects.append("SCHEMA_UNSUPPORTED")
    if manifest.get("profile") != "PERSONAL_LOCAL":
        defects.append("PROFILE_UNSUPPORTED")

    runtime = manifest.get("runtime") or {}
    if runtime.get("python_min") != "3.11":
        defects.append("PYTHON_BASELINE_MISMATCH")
    if runtime.get("dependency_policy") != "STANDARD_LIBRARY_FIRST":
        defects.append("DEPENDENCY_POLICY_WIDENED")
    if runtime.get("network_required") is not False:
        defects.append("NETWORK_DEPENDENCY_NOT_ADMITTED")

    custody = manifest.get("custody") or {}
    paths = custody.get("paths") or {}
    if set(paths) != REQUIRED_PATHS:
        defects.append("CUSTODY_PATH_SET_INVALID")
    path_values = list(paths.values()) if isinstance(paths, dict) else []
    if any(not _valid_relative_path(value) for value in path_values):
        defects.append("CUSTODY_PATH_UNSAFE")
    if len(path_values) != len(set(path_values)):
        defects.append("CUSTODY_PATHS_COLLIDE")
    if custody.get("directory_mode") != "0700":
        defects.append("DIRECTORY_MODE_UNSAFE")
    if custody.get("receipt_mode") != "0600":
        defects.append("RECEIPT_MODE_UNSAFE")

    policy = manifest.get("policy") or {}
    if policy.get("external_effects") != "REFUSE":
        defects.append("EXTERNAL_EFFECTS_NOT_ADMITTED")
    if policy.get("provider_required") is not False:
        defects.append("PROVIDER_DEPENDENCY_NOT_ADMITTED")
    if policy.get("projections_authoritative") is not False:
        defects.append("PROJECTION_AUTHORITY_INFLATION")
    return defects


def resolved_paths(root: Path, manifest: dict[str, Any]) -> dict[str, Path]:
    resolved_root = root.resolve(strict=False)
    result: dict[str, Path] = {}
    for name, relative in manifest["custody"]["paths"].items():
        candidate = resolved_root / relative
        resolved_candidate = candidate.resolve(strict=False)
        if resolved_candidate != resolved_root and resolved_root not in resolved_candidate.parents:
            raise InfrastructureRefused(f"PATH_ESCAPES_ROOT:{name}")
        result[name] = candidate
    return result


def _root_state(root: Path, digest: str) -> str:
    if not root.exists():
        return "CREATE"
    if root.is_symlink() or not root.is_dir():
        return "REFUSE"
    entries = list(root.iterdir())
    if not entries:
        return "CREATE"
    if (root / LOCK_NAME).exists():
        return "BUSY"
    receipt = root / RECEIPT_NAME
    if not receipt.is_file():
        return "REFUSE"
    try:
        recorded = json.loads(receipt.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "DRIFT"
    return "NOOP" if recorded.get("manifest_digest") == digest else "DRIFT"


def plan(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    digest = manifest_digest(manifest)
    state = _root_state(root, digest)
    return {
        "schema": "soveraeign-infrastructure-plan/v1",
        "root": str(root.resolve(strict=False)),
        "manifest_digest": digest,
        "disposition": state,
        "paths": {name: str(path) for name, path in resolved_paths(root, manifest).items()},
    }


def _atomic_write(path: Path, payload: bytes, mode: int) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        Path(temporary).unlink(missing_ok=True)
        raise


def apply(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    proposal = plan(root, manifest)
    if proposal["disposition"] == "BUSY":
        raise InfrastructureRefused("APPLY_ALREADY_IN_PROGRESS")
    if proposal["disposition"] == "REFUSE":
        raise InfrastructureRefused("UNMANAGED_OR_UNSAFE_ROOT")
    if proposal["disposition"] == "DRIFT":
        raise InfrastructureRefused("MANIFEST_DRIFT")
    if root.is_symlink():
        raise InfrastructureRefused("ROOT_IS_SYMLINK")

    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(root, 0o700)
    lock = root / LOCK_NAME
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise InfrastructureRefused("APPLY_ALREADY_IN_PROGRESS") from error
    try:
        os.close(descriptor)
        for path in resolved_paths(root, manifest).values():
            if path.exists() and (path.is_symlink() or not path.is_dir()):
                raise InfrastructureRefused(f"CUSTODY_PATH_INVALID:{path.name}")
            path.mkdir(parents=True, exist_ok=True, mode=0o700)
            os.chmod(path, 0o700)

        receipt = {
            "schema": "soveraeign-infrastructure-receipt/v1",
            "manifest_digest": proposal["manifest_digest"],
            "effect_class": "RECORD_LOCAL",
            "outcome": "COMMITTED" if proposal["disposition"] == "CREATE" else "NOOP",
            "root": proposal["root"],
            "paths": proposal["paths"],
        }
        _atomic_write(root / RECEIPT_NAME, canonical_bytes(receipt) + b"\n", 0o600)
        return receipt
    finally:
        lock.unlink(missing_ok=True)


def verify(root: Path, manifest: dict[str, Any]) -> list[str]:
    defects: list[str] = []
    digest = manifest_digest(manifest)
    receipt_path = root / RECEIPT_NAME
    if root.is_symlink() or not root.is_dir():
        return ["ROOT_MISSING_OR_UNSAFE"]
    if stat.S_IMODE(root.stat().st_mode) & 0o077:
        defects.append("ROOT_PERMISSIONS_UNSAFE")
    if (root / LOCK_NAME).exists():
        defects.append("INCOMPLETE_APPLY_LOCK_PRESENT")
    if not receipt_path.is_file() or receipt_path.is_symlink():
        defects.append("RECEIPT_MISSING_OR_UNSAFE")
    else:
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            defects.append("RECEIPT_INVALID")
        else:
            if receipt.get("manifest_digest") != digest:
                defects.append("MANIFEST_DIGEST_MISMATCH")
            if receipt.get("effect_class") != "RECORD_LOCAL":
                defects.append("RECEIPT_EFFECT_INVALID")
        if stat.S_IMODE(receipt_path.stat().st_mode) & 0o077:
            defects.append("RECEIPT_PERMISSIONS_UNSAFE")

    for name, path in resolved_paths(root, manifest).items():
        if path.is_symlink() or not path.is_dir():
            defects.append(f"CUSTODY_PATH_MISSING_OR_UNSAFE:{name}")
        elif stat.S_IMODE(path.stat().st_mode) & 0o077:
            defects.append(f"CUSTODY_PERMISSIONS_UNSAFE:{name}")
    return defects


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("validate", "plan", "apply", "verify"))
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--root", type=Path)
    args = parser.parse_args(argv)
    try:
        manifest = load_manifest(args.manifest)
        if args.operation == "validate":
            print(json.dumps({"outcome": "PASS", "manifest_digest": manifest_digest(manifest)}, sort_keys=True))
            return 0
        if args.root is None:
            raise InfrastructureRefused("ROOT_REQUIRED")
        if args.operation == "plan":
            print(json.dumps(plan(args.root, manifest), indent=2, sort_keys=True))
            return 0
        if args.operation == "apply":
            print(json.dumps(apply(args.root, manifest), indent=2, sort_keys=True))
            return 0
        defects = verify(args.root, manifest)
        print(json.dumps({"outcome": "FAIL" if defects else "PASS", "defects": defects}, indent=2, sort_keys=True))
        return 1 if defects else 0
    except (InfrastructureRefused, OSError, ValueError) as error:
        print(json.dumps({"outcome": "REFUSED", "reason": str(error)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
