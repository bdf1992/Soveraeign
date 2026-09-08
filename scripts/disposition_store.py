from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

GENESIS = "0" * 64


def canonical(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def digest_obj(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def ledger_path(store: Path, name: str) -> Path:
    return store / f"{name}.ndjson"


def read_ledger(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                rows.append(json.loads(raw))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
    return rows


def chained_record(kind: str, payload: dict[str, Any], previous: str) -> dict[str, Any]:
    body = {
        "schema": "soveraeign-disposition-ledger/v0.1",
        "kind": kind,
        "prev_digest": previous,
        "payload": payload,
    }
    return {**body, "digest": digest_obj(body)}


def verify_ledger(path: Path) -> dict[str, Any]:
    rows = read_ledger(path)
    previous = GENESIS
    for index, row in enumerate(rows, start=1):
        if row.get("prev_digest") != previous:
            raise ValueError(f"{path}: row {index}: previous digest mismatch")
        try:
            body = {key: row[key] for key in ("schema", "kind", "prev_digest", "payload")}
        except KeyError as exc:
            raise ValueError(f"{path}: row {index}: missing field {exc.args[0]}") from exc
        expected = digest_obj(body)
        if row.get("digest") != expected:
            raise ValueError(f"{path}: row {index}: digest mismatch")
        previous = expected
    return {"path": str(path), "records": len(rows), "head": previous, "valid": True}


def append_record(path: Path, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
    rows = read_ledger(path)
    if rows:
        verify_ledger(path)
    previous = rows[-1]["digest"] if rows else GENESIS
    record = chained_record(kind, payload, previous)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(canonical(record) + "\n")
    return record


def parse_json_object(raw: str | None, flag: str) -> dict[str, Any]:
    if raw is None:
        return {}
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError(f"{flag} must be a JSON object")
    return value


def write_projection(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical(value) + "\n", encoding="utf-8", newline="\n")
