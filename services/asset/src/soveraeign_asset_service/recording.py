"""Reader declaration and reconstruction refusal types."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any, Mapping

from .store import PayloadIntegrityError, Store


_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")


class ReconstructionError(RuntimeError):
    """Base class for a recording that cannot resolve its declared materials."""

    reason_code = "RECONSTRUCTION_FAILED"


class ReaderUndeclared(ValueError):
    """Raised when a derivative lacks a complete, coherent reader declaration."""

    reason_code = "READER_UNDECLARED"


class SourceChanged(ReconstructionError):
    """Raised when a recording's addressed source no longer verifies."""

    reason_code = "SOURCE_CHANGED"


class RecordingChanged(ReconstructionError):
    """Raised when a recording's deposited output no longer verifies."""

    reason_code = "RECORDING_CHANGED"


class ReaderChanged(ReconstructionError):
    """Raised when a recording's addressed reader material no longer verifies."""

    reason_code = "READER_CHANGED"


class ConfigurationChanged(ReconstructionError):
    """Raised when a recording's addressed configuration no longer verifies."""

    reason_code = "CONFIGURATION_CHANGED"


def digest_configuration(configuration: Mapping[str, Any]) -> str:
    """Digest one canonical, JSON-compatible replay configuration."""
    encoded = _configuration_bytes(configuration)
    return f"sha256:{sha256(encoded).hexdigest()}"


def _configuration_bytes(configuration: Mapping[str, Any]) -> bytes:
    return json.dumps(
        configuration,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


@dataclass(frozen=True)
class ReaderDeclaration:
    """Versioned interpretation identity plus replay-safe input materials."""

    reader_id: str
    reader_version: str
    configuration_digest: str
    fidelity: str
    omissions: tuple[str, ...] = ()
    output_role: str = "RECORDING"
    reader_artifact: bytes = field(default=b"", repr=False)
    configuration: Mapping[str, Any] | None = field(
        default=None, repr=False, compare=False
    )

    @classmethod
    def from_materials(
        cls,
        reader_id: str,
        reader_version: str,
        reader_artifact: bytes,
        configuration: Mapping[str, Any],
        fidelity: str,
        omissions: tuple[str, ...] = (),
        output_role: str = "RECORDING",
    ) -> ReaderDeclaration:
        """Declare reader artifact bytes and secret-free replay configuration."""
        return cls(
            reader_id=reader_id,
            reader_version=reader_version,
            configuration_digest=digest_configuration(configuration),
            fidelity=fidelity,
            omissions=omissions,
            output_role=output_role,
            reader_artifact=reader_artifact,
            configuration=configuration,
        )

    def validate(self) -> None:
        """Refuse incomplete readers and incoherent fidelity declarations."""
        declared = (
            ("reader_id", self.reader_id),
            ("reader_version", self.reader_version),
            ("configuration_digest", self.configuration_digest),
            ("output_role", self.output_role),
        )
        missing = [
            name
            for name, value in declared
            if not isinstance(value, str) or not value.strip()
        ]
        if missing:
            raise ReaderUndeclared(f"missing reader fields: {', '.join(missing)}")
        if not _SHA256.fullmatch(self.configuration_digest):
            raise ReaderUndeclared("configuration_digest must be sha256:<64 lowercase hex>")
        if not isinstance(self.reader_artifact, bytes) or not self.reader_artifact:
            raise ReaderUndeclared("reader_artifact must contain versioned bytes")
        if not isinstance(self.configuration, Mapping):
            raise ReaderUndeclared("configuration must be a replay-safe mapping")
        try:
            observed_configuration_digest = digest_configuration(self.configuration)
        except (TypeError, ValueError) as error:
            raise ReaderUndeclared("configuration must be canonical JSON") from error
        if observed_configuration_digest != self.configuration_digest:
            raise ReaderUndeclared("configuration does not match configuration_digest")
        if not isinstance(self.fidelity, str) or self.fidelity not in {"EXACT", "LOSSY"}:
            raise ReaderUndeclared("fidelity must be EXACT or LOSSY")
        if not isinstance(self.omissions, tuple):
            raise ReaderUndeclared("omissions must be an immutable tuple")
        if any(
            not isinstance(omission, str) or not omission.strip()
            for omission in self.omissions
        ):
            raise ReaderUndeclared("omission identifiers must be non-empty")
        if len(set(self.omissions)) != len(self.omissions):
            raise ReaderUndeclared("omission identifiers must be unique")
        if self.fidelity == "EXACT" and self.omissions:
            raise ReaderUndeclared("EXACT readers cannot declare omissions")
        if self.fidelity == "LOSSY" and not self.omissions:
            raise ReaderUndeclared("LOSSY readers require recoverable omissions")


class ReaderMaterials:
    """Materialize and resolve immutable reader and configuration artifacts."""

    def __init__(self, store: Store):
        self.store = store

    def materialize(self, declaration: ReaderDeclaration) -> dict[str, str]:
        """Deposit exact reader materials and return their stable addresses."""
        declaration.validate()
        try:
            artifact_address, artifact_digest = self.store.store_addressed_blob(
                declaration.reader_artifact
            )
        except PayloadIntegrityError as error:
            raise ReaderChanged(declaration.reader_id) from error
        manifest = {
            "artifact_address": artifact_address,
            "artifact_digest": artifact_digest,
            "reader_id": declaration.reader_id,
            "reader_version": declaration.reader_version,
        }
        manifest_bytes = json.dumps(
            manifest, separators=(",", ":"), sort_keys=True
        ).encode("utf-8")
        try:
            reader_address, reader_digest = self.store.store_addressed_blob(manifest_bytes)
        except PayloadIntegrityError as error:
            raise ReaderChanged(declaration.reader_id) from error
        try:
            configuration_address, configuration_digest = self.store.store_addressed_blob(
                _configuration_bytes(declaration.configuration or {})
            )
        except PayloadIntegrityError as error:
            raise ConfigurationChanged(declaration.reader_id) from error
        if configuration_digest != declaration.configuration_digest:
            raise ConfigurationChanged(declaration.reader_id)
        return {
            "configuration_address": configuration_address,
            "configuration_digest": configuration_digest,
            "reader_address": reader_address,
            "reader_artifact_address": artifact_address,
            "reader_artifact_digest": artifact_digest,
            "reader_digest": reader_digest,
        }

    def resolve(self, record: Mapping[str, Any]) -> dict[str, str]:
        """Verify a reader manifest, its exact artifact, and its configuration."""
        try:
            subject = str(record["reader_id"])
        except (IndexError, KeyError, TypeError):
            subject = "reader"
        try:
            manifest_bytes = self.store.verified_address(
                record["reader_address"], record["reader_digest"]
            )
            manifest = json.loads(manifest_bytes.decode("utf-8"))
            if (
                not isinstance(manifest, dict)
                or manifest.get("reader_id") != record["reader_id"]
                or manifest.get("reader_version") != record["reader_version"]
            ):
                raise ReaderChanged(record["reader_id"])
            artifact_address = manifest.get("artifact_address")
            artifact_digest = manifest.get("artifact_digest")
            self.store.verified_address(artifact_address, artifact_digest)
        except (
            IndexError,
            KeyError,
            TypeError,
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as error:
            raise ReaderChanged(subject) from error
        except PayloadIntegrityError as error:
            raise ReaderChanged(subject) from error
        try:
            self.store.verified_address(
                record["configuration_address"], record["configuration_digest"]
            )
        except (IndexError, KeyError, TypeError, PayloadIntegrityError) as error:
            raise ConfigurationChanged(subject) from error
        return {
            "reader_artifact_address": artifact_address,
            "reader_artifact_digest": artifact_digest,
        }
