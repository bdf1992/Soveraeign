#!/usr/bin/env python3
"""Activate an existing local custody contract before starting a node runtime."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
from typing import Any
from uuid import uuid4

import infrastructure


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "infrastructure" / "phase-i.local.json"
DEFAULT_ROOT = Path("/var/lib/soveraeign")
IDENTITY_NAME = ".soveraeign-custody-identity.json"
ACTIVATION_LOCK = ".soveraeign-custody-activation.lock"
POLICIES = {"VERIFY_ONLY", "VERIFY_OR_INITIALIZE_EMPTY"}


class CustodyActivationRefused(RuntimeError):
    """The volume cannot be proven as this node's admitted custody."""


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _atomic_write(path: Path, value: dict[str, Any], mode: int = 0o600) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(_canonical(value) + b"\n")
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


def _require_identity(path: Path, expected_uid: int, expected_gid: int, label: str) -> None:
    info = path.stat()
    if info.st_uid != expected_uid or info.st_gid != expected_gid:
        raise CustodyActivationRefused(f"CUSTODY_OWNERSHIP_UNWRITABLE:{label}")
    if stat.S_IMODE(info.st_mode) & 0o077:
        raise CustodyActivationRefused(f"CUSTODY_PERMISSIONS_UNSAFE:{label}")


def _prove_write(path: Path) -> None:
    probe = path / f".custody-write-probe-{uuid4().hex}"
    descriptor: int | None = None
    try:
        descriptor = os.open(probe, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.write(descriptor, b"probe")
        os.fsync(descriptor)
    except OSError as error:
        raise CustodyActivationRefused(f"CUSTODY_WRITE_PROBE_FAILED:{path.name}") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)
        probe.unlink(missing_ok=True)


def _load_or_create_identity(root: Path, digest: str,
                             paths: dict[str, str]) -> tuple[dict[str, Any], bool]:
    identity_path = root / IDENTITY_NAME
    if identity_path.exists():
        if identity_path.is_symlink() or not identity_path.is_file():
            raise CustodyActivationRefused("CUSTODY_IDENTITY_UNSAFE")
        try:
            identity = json.loads(identity_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise CustodyActivationRefused("CUSTODY_IDENTITY_INVALID") from error
        if (identity.get("manifest_digest") != digest or identity.get("paths") != paths or
                identity.get("schema") != "soveraeign-custody-identity/v1"):
            raise CustodyActivationRefused("CUSTODY_IDENTITY_DRIFT")
        return identity, False
    identity = {"schema": "soveraeign-custody-identity/v1", "custody_id": str(uuid4()),
                "manifest_digest": digest, "paths": paths}
    _atomic_write(identity_path, identity)
    return identity, True


def _verify_prior_receipts(directory: Path, identity: dict[str, Any], digest: str,
                           paths: dict[str, str]) -> None:
    if not directory.exists():
        return
    if directory.is_symlink() or not directory.is_dir():
        raise CustodyActivationRefused("CUSTODY_ACTIVATION_RECEIPT_DIRECTORY_UNSAFE")
    for receipt_path in directory.iterdir():
        if receipt_path.is_symlink() or not receipt_path.is_file() or receipt_path.suffix != ".json":
            raise CustodyActivationRefused("CUSTODY_ACTIVATION_RECEIPT_STALE")
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise CustodyActivationRefused("CUSTODY_ACTIVATION_RECEIPT_STALE") from error
        if (receipt.get("schema") != "soveraeign-custody-activation-receipt/v1" or
                receipt.get("activation_id") != receipt_path.stem or
                receipt.get("custody_id") != identity["custody_id"] or
                receipt.get("manifest_digest") != digest or receipt.get("paths") != paths or
                receipt.get("effect_class") != "RECORD_LOCAL"):
            raise CustodyActivationRefused("CUSTODY_ACTIVATION_RECEIPT_STALE")


def activate(root: Path, manifest: dict[str, Any], policy: str,
             expected_uid: int, expected_gid: int) -> dict[str, Any]:
    """Verify or explicitly initialize custody and append an activation receipt."""
    if policy not in POLICIES:
        raise CustodyActivationRefused("ACTIVATION_POLICY_UNSUPPORTED")
    if os.geteuid() != expected_uid or os.getegid() != expected_gid:
        raise CustodyActivationRefused("EFFECTIVE_IDENTITY_MISMATCH")
    proposal = infrastructure.plan(root, manifest)
    disposition = proposal["disposition"]
    initialized = False
    if disposition == "CREATE":
        if policy == "VERIFY_ONLY":
            raise CustodyActivationRefused("EMPTY_CUSTODY_NOT_ACTIVATED")
        try:
            infrastructure.apply(root, manifest)
        except (infrastructure.InfrastructureRefused, OSError) as error:
            raise CustodyActivationRefused(f"CUSTODY_INITIALIZATION_REFUSED:{error}") from error
        initialized = True
    elif disposition != "NOOP":
        raise CustodyActivationRefused(f"CUSTODY_PRECONDITION_{disposition}")
    defects = infrastructure.verify(root, manifest)
    if defects:
        raise CustodyActivationRefused("CUSTODY_VERIFY_FAILED:" + ",".join(defects))
    paths = infrastructure.resolved_paths(root, manifest)
    _require_identity(root, expected_uid, expected_gid, "root")
    for name, path in paths.items():
        _require_identity(path, expected_uid, expected_gid, name)
    _require_identity(root / infrastructure.RECEIPT_NAME, expected_uid, expected_gid,
                      "infrastructure-receipt")
    _prove_write(root)
    _prove_write(paths["work"])
    lock = root / ACTIVATION_LOCK
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise CustodyActivationRefused("ACTIVATION_ALREADY_IN_PROGRESS") from error
    try:
        os.close(descriptor)
        digest = infrastructure.manifest_digest(manifest)
        relative_paths = manifest["custody"]["paths"]
        identity, identity_created = _load_or_create_identity(root, digest, relative_paths)
        _require_identity(root / IDENTITY_NAME, expected_uid, expected_gid, "custody-identity")
        receipt_directory = paths["receipts"] / "custody-activations"
        _verify_prior_receipts(receipt_directory, identity, digest, relative_paths)
        receipt_directory.mkdir(mode=0o700, exist_ok=True)
        os.chmod(receipt_directory, 0o700)
        activation_id = str(uuid4())
        infrastructure_receipt = root / infrastructure.RECEIPT_NAME
        receipt = {
            "schema": "soveraeign-custody-activation-receipt/v1",
            "activation_id": activation_id,
            "activated_at": datetime.now(timezone.utc).isoformat(),
            "custody_id": identity["custody_id"],
            "manifest_digest": digest,
            "paths": relative_paths,
            "root": str(root.resolve()),
            "infrastructure_receipt_digest": sha256(infrastructure_receipt.read_bytes()).hexdigest(),
            "effective_uid": os.geteuid(), "effective_gid": os.getegid(), "policy": policy,
            "outcome": "INITIALIZED_AND_VERIFIED" if initialized else "VERIFIED_EXISTING",
            "continuity": "ESTABLISHED" if identity_created else "PRESERVED",
            "effect_class": "RECORD_LOCAL",
        }
        _atomic_write(receipt_directory / f"{activation_id}.json", receipt)
        return receipt
    finally:
        lock.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--policy", choices=sorted(POLICIES), default="VERIFY_ONLY")
    parser.add_argument("--expected-uid", type=int, default=65532)
    parser.add_argument("--expected-gid", type=int, default=65532)
    args = parser.parse_args(argv)
    try:
        manifest = infrastructure.load_manifest(args.manifest)
        receipt = activate(args.root, manifest, args.policy, args.expected_uid, args.expected_gid)
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return 0
    except (CustodyActivationRefused, infrastructure.InfrastructureRefused, OSError, ValueError) as error:
        print(json.dumps({"outcome": "REFUSED", "reason": str(error)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
