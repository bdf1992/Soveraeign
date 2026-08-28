#!/usr/bin/env python3
"""Check that precedent policy stays inherited, explicit, and mechanically grounded."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable
import json
import sys


ROOT = Path(__file__).resolve().parent.parent
DIALECT = "https://json-schema.org/draft/2020-12/schema"
SCHEMA_ROOTS = ("contracts", "bindings", "services", ".claude/schedules")
REQUIRED_TEXT = {
    "CONTRACT.md": (
        "## C16 · Precedent before invention",
        "adopt,\nprofile, defer, deviate, or monitor",
        "MUST NOT silently define Soveraeign's persistent, cryptographic,",
        "BCP 14 meanings of RFC 2119 and RFC 8174",
    ),
    "ENGINEERING.md": (
        "## Precedent and host-language profile",
        "`ADOPT`, `PROFILE`, `DEFER`, `DEVIATE`, or\n`MONITOR`",
        "SOV-RFC3339-1",
        "soveraeign-record-chain/v2",
        "soveraeign-record-chain/v3",
        "DEFER** RFC 8785 JCS",
    ),
    "services/record/src/soveraeign_record_service/digest.py": (
        'LEGACY_DIGEST_PROFILE = "soveraeign-record-chain/v1"',
        'DIGEST_PROFILE = "soveraeign-record-chain/v2"',
        "[DIGEST_PROFILE, previous, kind, subject, actor, payload]",
        'BOUND_DIGEST_PROFILE = "soveraeign-record-chain/v3"',
        "[BOUND_DIGEST_PROFILE, previous, entry_id, kind, subject, actor,",
        "source_address, float(recorded_at), payload]",
    ),
    "services/record/src/soveraeign_record_service/core.py": (
        "digest_profile TEXT NOT NULL",
    ),
    "scripts/sovkernel/jsonschema.py": (
        "RFC3339_PROFILE = re.compile(",
        'value.endswith("-00:00")',
    ),
}


def schema_paths(root: Path) -> Iterable[Path]:
    """Yield authored JSON Schema documents, never ordinary JSON instances."""
    for relative in SCHEMA_ROOTS:
        base = root / relative
        if base.exists():
            yield from sorted(base.rglob("*.schema.json"))


def check(root: Path = ROOT) -> list[str]:
    """Return every drift from the small inherited precedent profile."""
    defects: list[str] = []
    for relative, required in REQUIRED_TEXT.items():
        path = root / relative
        if not path.is_file():
            defects.append(f"{relative}: missing")
            continue
        text = path.read_text(encoding="utf-8")
        defects.extend(f"{relative}: missing {clause!r}" for clause in required if clause not in text)

    profile_path = root / "bindings/sov/profile.json"
    if not profile_path.is_file():
        defects.append("bindings/sov/profile.json: missing")
    else:
        try:
            sources = json.loads(profile_path.read_text(encoding="utf-8"))["governing_sources"]
        except (KeyError, json.JSONDecodeError) as error:
            defects.append(f"bindings/sov/profile.json: unreadable governing sources: {error}")
        else:
            for source in ("CONTRACT.md", "ENGINEERING.md"):
                if source not in sources:
                    defects.append(f"bindings/sov/profile.json: Sov does not inherit {source}")

    found = list(schema_paths(root))
    if not found:
        defects.append("no *.schema.json documents found")
    for path in found:
        relative = path.relative_to(root).as_posix()
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            defects.append(f"{relative}: invalid JSON: {error}")
            continue
        if schema.get("$schema") != DIALECT:
            defects.append(f"{relative}: must declare JSON Schema Draft 2020-12")
    return defects


def main() -> int:
    defects = check()
    if defects:
        print("FAIL: precedent profile")
        for defect in defects:
            print(f"  {defect}")
        return 1
    print(f"PASS: precedent profile ({len(list(schema_paths(ROOT)))} schemas, one inherited rule)")
    print("Precedent informs design; it grants no authority or standing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
