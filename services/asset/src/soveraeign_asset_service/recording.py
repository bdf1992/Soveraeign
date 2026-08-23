"""Reader declaration and reconstruction refusal types."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Mapping


_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")


class ReaderUndeclared(ValueError):
    """Raised when a derivative lacks a complete, coherent reader declaration."""


class SourceChanged(RuntimeError):
    """Raised when a recording's addressed source no longer verifies."""


class RecordingChanged(RuntimeError):
    """Raised when a recording's deposited output no longer verifies."""


class StaleLease(RuntimeError):
    """Raised after stale or expired worker settlement is refused."""


def digest_configuration(configuration: Mapping[str, Any]) -> str:
    """Digest a JSON-compatible reader configuration without retaining secrets."""
    encoded = json.dumps(
        configuration,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"sha256:{sha256(encoded).hexdigest()}"


@dataclass(frozen=True)
class ReaderDeclaration:
    """Versioned interpretation identity for one derivative recording."""

    reader_id: str
    reader_version: str
    configuration_digest: str
    fidelity: str
    omissions: tuple[str, ...] = ()
    output_role: str = "RECORDING"

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
