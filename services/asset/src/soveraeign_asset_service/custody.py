"""Reading custody back out, and refusing when the world moved underneath.

`services/asset/contracts/service.json` has always declared a `read-version`
operation. Nothing implemented it, so `PROD-I-2` - "a source rereads
byte-identical by digest" - was declared, fixtured for field presence, and never
actually performed on real bytes.

This module performs it. It lives beside `core.py` rather than inside it because
`lint.py` carries that module as known debt with the instruction to split
storage, receipts and lifecycle before adding behavior.

Both operations here are receipted, including their refusals. A refusal that
leaves no receipt is indistinguishable from an operation that never happened.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname


class DigestMismatch(RuntimeError):
    """Stored custody no longer matches the digest recorded for it."""


class SourceChanged(RuntimeError):
    """The external source no longer matches the digest recorded at capture."""


class UnknownRecord(KeyError):
    """The named version or source is not held."""


def _path_from_locator(locator: str) -> Path | None:
    """Resolve a file locator back to a path, or None if it is not a local file."""
    parsed = urlparse(locator)
    if parsed.scheme != "file":
        return None
    return Path(url2pathname(unquote(parsed.path)))


def read_version(service: Any, version_id: str, actor: str) -> dict[str, Any]:
    """Return the exact bytes held for a version, or refuse.

    Custody is content addressed, so the stored digest is recomputed from the
    bytes actually on disk rather than trusted. A mismatch means the payload
    corrupted under us, which `SPEC.md` requires the reading to refuse.
    """
    row = service.db.execute(
        "SELECT * FROM versions WHERE id=?", (version_id,)
    ).fetchone()
    if row is None:
        raise UnknownRecord(version_id)

    blob = Path(row["blob_path"])
    if not blob.is_file():
        service._receipt("REFUSED", "version.read", "version", version_id, actor,
                         {"reason": "PAYLOAD_ABSENT"})
        service.db.commit()
        raise DigestMismatch(f"{version_id}: payload absent from custody")

    data = blob.read_bytes()
    digest = sha256(data).hexdigest()
    if digest != row["digest"]:
        service._receipt("REFUSED", "version.read", "version", version_id, actor,
                         {"reason": "DIGEST_MISMATCH", "recorded": row["digest"],
                          "observed": digest})
        service.db.commit()
        raise DigestMismatch(f"{version_id}: recorded {row['digest']}, read {digest}")

    service._receipt("COMMITTED", "version.read", "version", version_id, actor,
                     {"digest": digest, "size": len(data)})
    service.db.commit()
    return {
        "version_id": version_id,
        "asset_id": row["asset_id"],
        "source_id": row["source_id"],
        "digest": digest,
        "mime": row["mime"],
        "role": row["role"],
        "size": len(data),
        "bytes": data,
    }


def reread_source(service: Any, source_id: str, actor: str) -> dict[str, Any]:
    """Re-read an external source and refuse if it moved since capture.

    `SPEC.md`'s `read_source` transition commits only while the source digest
    still verifies, and refuses `SOURCE_CHANGED` otherwise. Returning either the
    old bytes or the new ones without saying so is the defeat this prevents.
    """
    row = service.db.execute(
        "SELECT * FROM sources WHERE id=?", (source_id,)
    ).fetchone()
    if row is None:
        raise UnknownRecord(source_id)

    path = _path_from_locator(row["locator"])
    if path is None or not path.is_file():
        service._receipt("REFUSED", "source.reread", "source", source_id, actor,
                         {"reason": "SOURCE_UNREACHABLE", "locator": row["locator"]})
        service.db.commit()
        raise SourceChanged(f"{source_id}: source is no longer reachable")

    data = path.read_bytes()
    digest = sha256(data).hexdigest()
    if digest != row["digest"]:
        service._receipt("REFUSED", "source.reread", "source", source_id, actor,
                         {"reason": "SOURCE_CHANGED", "captured": row["digest"],
                          "observed": digest})
        service.db.commit()
        raise SourceChanged(f"{source_id}: captured {row['digest']}, now {digest}")

    service._receipt("COMMITTED", "source.reread", "source", source_id, actor,
                     {"digest": digest})
    service.db.commit()
    return {"source_id": source_id, "digest": digest, "locator": row["locator"],
            "size": len(data)}
