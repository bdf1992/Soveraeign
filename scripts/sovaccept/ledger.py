"""Serialize decisions and durably preserve the exact existing ledger prefix.

OS locks release on process exit. Replacement is atomic on the local filesystem:
the old ledger or the old ledger plus one complete decision is visible. This is
logical append-only recording; no historical byte is changed or discarded.
"""

from __future__ import annotations

import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

from sovaccept.review import AcceptanceError, canonical, digest


@contextmanager
def locked(root: Path):
    """Hold the acceptance lock across replay lookup, validation and recording."""
    directory = root / ".local" / "acceptance"
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "ledger.lock").open("a+b") as handle:
        if os.name == "nt":
            import msvcrt

            # Windows permits locking a byte beyond EOF, so no racy lock-file
            # initialization is needed. A stale file carries no stale ownership.
            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            except OSError as error:
                raise AcceptanceError("ACCEPTANCE_BUSY: another decision is recording; retry") from error
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield directory / "ledger.ndjson"
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def read(path: Path) -> tuple[bytes, list[dict]]:
    """Read legacy and current entries; a damaged ledger never becomes an empty one."""
    original = path.read_bytes() if path.exists() else b""
    if original and not original.endswith(b"\n"):
        raise AcceptanceError("ACCEPTANCE_LEDGER_INVALID: incomplete final record")
    try:
        entries = [json.loads(line) for line in original.splitlines()]
        if any(not isinstance(row, dict) or not isinstance(row.get("packet_id"), str)
               or row.get("action") not in ("ACCEPT", "REJECT", "STRIKE", "REDIRECT")
               for row in entries):
            raise ValueError("unrecognized decision")
        for row in entries:
            if "review" not in row:
                continue  # Legacy identity is unknown, never reconstructed.
            identity = row["review"]
            snapshot = row.get("packet")
            if (not isinstance(identity, dict) or not isinstance(snapshot, dict)
                    or not isinstance(identity.get("subject"), dict)
                    or identity.get("packet_id") != row["packet_id"]
                    or snapshot.get("packet_id") != row["packet_id"]
                    or identity.get("packet_digest") != digest(canonical(snapshot))):
                raise ValueError("invalid reviewed decision")
            basis = {key: value for key, value in identity.items() if key != "review_digest"}
            if identity.get("review_digest") != digest(canonical(basis)):
                raise ValueError("damaged review identity")
    except (ValueError, UnicodeError) as error:
        raise AcceptanceError("ACCEPTANCE_LEDGER_INVALID: cannot read every decision") from error
    return original, entries


def append(path: Path, original: bytes, entry: dict) -> None:
    """Commit one complete entry before acknowledging it; keep prior bytes verbatim."""
    suffix = (json.dumps(entry, sort_keys=True, ensure_ascii=False, allow_nan=False)
              + "\n").encode("utf-8")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix="decision-", suffix=".tmp",
                                         delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(original + suffix)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        if os.name != "nt":
            descriptor = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
