"""Read-only, source-addressed Registry resolution over a derived index."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any, Callable

from soveraeign_record_service import RecordService

from .index import build_operation_index

DigestReader = Callable[[str], str | None]


class RegistryService:
    """Resolve derived entries; never persist or silently repair the index."""

    def __init__(self, record: RecordService, repository_root: str | Path,
                 closure: dict[str, Any], manifests: dict[str, dict[str, Any]],
                 policy: dict[str, Any], source_digests: list[dict[str, str]], *,
                 digest_reader: DigestReader | None = None) -> None:
        self.record = record
        self.repository_root = Path(repository_root).resolve()
        self.source_digests = list(source_digests)
        self._expected = {item["address"]: item["digest"] for item in source_digests}
        self._digest_reader = digest_reader or self._read_digest
        self._index, self.input_state_digest = build_operation_index(
            closure, manifests, policy, source_digests)

    def _read_digest(self, address: str) -> str | None:
        relative = Path(address)
        if relative.is_absolute() or ".." in relative.parts:
            return None
        path = (self.repository_root / relative).resolve()
        if self.repository_root not in path.parents or not path.is_file():
            return None
        return sha256(path.read_bytes()).hexdigest()

    def _source_drift(self) -> list[dict[str, str | None]]:
        drift = []
        for address, expected in sorted(self._expected.items()):
            actual = self._digest_reader(address)
            if actual != expected:
                drift.append({"address": address, "expected": expected, "actual": actual})
        return drift

    def _receipt(self, outcome: str, actor: str, name: str,
                 detail: dict[str, Any]) -> dict[str, Any]:
        return self.record.receipt(
            outcome, "registry.resolve", name, actor,
            {"index_input_state_digest": self.input_state_digest, **detail})

    def resolve(self, name: str, actor: str) -> dict[str, Any]:
        """Return a terminal receipt for one fresh lookup, refusal included."""
        drift = self._source_drift()
        if drift:
            return self._receipt("REFUSED", actor, name, {
                "reason_code": "INDEX_STALE", "source_drift": drift,
            })
        entry = self._index.get(name)
        if entry is None:
            return self._receipt("REFUSED", actor, name, {
                "reason_code": "NAME_UNKNOWN",
            })
        return self._receipt("COMMITTED", actor, name, {
            "resolution": dict(entry),
            "commit_semantics": "DERIVED",
            "standing_effect": "NONE",
        })


__all__ = ["RegistryService"]
