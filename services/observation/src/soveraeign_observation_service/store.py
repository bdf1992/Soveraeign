"""A file store for the service's own records, so state outlives one process.

`ObservationService` keeps requests, declarations, inferences, observations, and receipts in
memory. That proved the semantics and nothing more (`KNOWN-GAPS.md`, Durable state): a
predicate declared in one process was gone before a later process could observe against it.
This store writes each record as one JSON file under a directory per kind, named by the
record's id, and rebuilds the service from those files on the next invocation.

It is a service-owned store, not the journal and not standing. Nothing here is authoritative:
the journal the Record Service owns is, and the observation this service emits is handed back
to it as an entry payload rather than written here. The store is append-only in the same
sense the service is: a record, once written, is never rewritten by `save`.

Records are replayed in the order of the moment they were recorded, which every record kind
carries under its own field, then by id. The clock the service is built with must therefore
produce moments that sort as strings; `cli.py`'s does.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from .service import ObservationService

#: Service attribute -> (directory name, id field, moment field), in replay order.
KINDS: tuple[tuple[str, str, str, str], ...] = (
    ("requests", "requests", "request_id", "requested_at"),
    ("declarations", "declarations", "declaration_id", "declared_at"),
    ("inferences", "inferences", "inference_id", "inferred_at"),
    ("observations", "observations", "observation_id", "observed_at"),
    ("receipts", "receipts", "receipt_id", "recorded_at"),
)


def _identifier(record: dict[str, Any], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value:
        raise ValueError(f"record carries no {field}")
    return value


def file_name(identifier: str) -> str:
    """The file a record lives in: its id, with the characters a host filesystem refuses."""
    return "".join("_" if char in ':/\\' else char for char in identifier) + ".json"


class FileStore:
    """One directory per record kind, one file per record, replayed in recorded order."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def _directory(self, kind: str) -> Path:
        return self.root / kind

    def _read_all(self, kind: str, moment_field: str) -> list[dict[str, Any]]:
        directory = self._directory(kind)
        if not directory.is_dir():
            return []
        records: list[dict[str, Any]] = []
        for path in directory.glob("*.json"):
            document = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(document, dict):
                raise ValueError(f"{path} does not hold a record object")
            records.append(document)
        records.sort(key=lambda record: (str(record.get(moment_field, "")),
                                         json.dumps(record, sort_keys=True)))
        return records

    def load(self, clock) -> ObservationService:
        """Rebuild the service from every record on disk, in recorded order."""
        service = ObservationService(clock)
        for attribute, kind, _, moment_field in KINDS:
            getattr(service, attribute).extend(self._read_all(kind, moment_field))
        return service

    def save(self, service: ObservationService) -> list[Path]:
        """Write every record the service holds that is not yet on disk; return what was written."""
        written: list[Path] = []
        for attribute, kind, id_field, _ in KINDS:
            directory = self._directory(kind)
            for record in getattr(service, attribute):
                path = directory / file_name(_identifier(record, id_field))
                if path.exists():
                    continue
                directory.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n",
                                encoding="utf-8")
                written.append(path)
        return written

    def count(self) -> dict[str, int]:
        """How many records of each kind are on disk; a projection, never authority."""
        return {kind: len(list(self._directory(kind).glob("*.json")))
                if self._directory(kind).is_dir() else 0
                for _, kind, _, _ in KINDS}


__all__ = ["FileStore", "KINDS", "file_name"]
