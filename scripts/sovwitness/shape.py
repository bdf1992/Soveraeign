"""Decide whether a witness receipt is a well-formed, conformant, containable document.

Split from `sovwitness/records.py`, which decides whether a receipt still matches
the tree. The boundary is worth keeping: nothing here reads a byte of any subject,
and everything here is a refusal the subject changing cannot produce. That is why
every failure raised in this module grades `INVALID` rather than stale.

`witness/observations/README.md` says receipts conform to
`contracts/participant-observation.schema.json`, and until this module that claim
was unchecked while a second, weaker shape contract lived in the grader.
`AGENTS.md` forbids exactly that: the schema owns the shape, and this defers to it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from sovkernel.jsonschema import validate

SCHEMA_PATH = Path("contracts") / "participant-observation.schema.json"
# One slot, filled on first read: None means the schema is not in this tree.
_SCHEMA_CACHE: list[dict | None] = []

DIGEST_PREFIX = "sha256:"
DIGEST_LENGTH = 64
HEX_DIGITS = frozenset("0123456789abcdef")
# Win32 resolves these to a device wherever they appear, so `nul` exists in every
# directory and reads as an empty file. A receipt naming one would digest zero
# bytes and grade CURRENT forever, having measured nothing.
RESERVED_NAMES = frozenset(
    ["con", "prn", "aux", "nul"]
    + [f"com{digit}" for digit in range(1, 10)]
    + [f"lpt{digit}" for digit in range(1, 10)])


class ReceiptError(ValueError):
    """The receipt cannot be graded at all, which is a defect and not subject drift."""


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict:
    """Refuse a JSON object that states the same key twice.

    Python keeps the last such key and a person reads the first, so a receipt
    could carry an honest `observed` block above a lying one and grade off the
    lie while reading as honest.
    """
    seen: set[str] = set()
    for key, _ in pairs:
        if key in seen:
            raise ReceiptError(f"duplicate JSON key: {key!r}")
        seen.add(key)
    return dict(pairs)


def _well_formed(digest: Any) -> bool:
    """A digest string this module is willing to compare against."""
    if not isinstance(digest, str) or not digest.startswith(DIGEST_PREFIX):
        return False
    body = digest[len(DIGEST_PREFIX):]
    return len(body) == DIGEST_LENGTH and set(body) <= HEX_DIGITS


def _schema() -> dict[str, Any] | None:
    """The declared observation schema, read once from the repository this module is in.

    Resolved against the module's own repository and not against the tree being
    graded: the schema is a contract of this code, so pointing the grader at a
    scratch tree with `--root` must not quietly switch the shape contract off.
    """
    if _SCHEMA_CACHE:
        return _SCHEMA_CACHE[0]
    path = Path(__file__).resolve().parents[2] / SCHEMA_PATH
    loaded: dict[str, Any] | None = None
    if path.is_file():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            loaded = None
    _SCHEMA_CACHE.append(loaded)
    return loaded


def _conforms(document: Any) -> None:
    """Refuse a receipt the declared schema rejects.

    `witness/observations/README.md` says receipts conform to
    `contracts/participant-observation.schema.json`. Nothing checked it, so this
    module was a second and weaker shape contract for the same records, which
    `AGENTS.md` forbids. The schema requires `participant_id` — the field naming
    who observed, which is the whole subject of builder/witness separation — and
    a receipt was grading `CURRENT` without one.
    """
    schema = _schema()
    if schema is None:
        return
    errors = validate(document, schema, schema)
    if errors:
        raise ReceiptError(f"does not conform to {SCHEMA_PATH.as_posix()}: {errors[0]}")
    if not str(document.get("participant_id", "")).strip():
        raise ReceiptError("participant_id is empty, so the receipt names no observer")


def _pairs(document: Any) -> list[tuple[str, str]]:
    """The address/digest pairs a receipt declares, or a refusal naming the defect.

    Every refusal here is about the receipt's own shape. None of them can be
    produced by the subject changing, which is why they are graded `INVALID`
    rather than stale.
    """
    if not isinstance(document, dict):
        raise ReceiptError("receipt is not a JSON object")
    if not isinstance(document.get("artifact_revision"), str) \
            or not document["artifact_revision"].strip():
        raise ReceiptError("no artifact_revision, so the receipt names no commit")
    observed = document.get("observed")
    if not isinstance(observed, dict):
        raise ReceiptError("no observed object")
    addresses = observed.get("observed_state_addresses")
    digests = observed.get("observed_state_digests")
    if not isinstance(addresses, list) or not isinstance(digests, list):
        raise ReceiptError("observed_state_addresses and observed_state_digests must be lists")
    if not addresses:
        raise ReceiptError("receipt digests nothing, so it measures nothing")
    if len(addresses) != len(digests):
        raise ReceiptError(f"{len(addresses)} address(es) against {len(digests)} digest(s)")
    for address in addresses:
        if not isinstance(address, str) or not address.strip():
            raise ReceiptError(f"address is not a non-empty string: {address!r}")
    if len(set(addresses)) != len(addresses):
        raise ReceiptError("the same address is named twice, which inflates what was measured")
    for digest in digests:
        if not _well_formed(digest):
            raise ReceiptError(f"digest is not a sha256 hex string: {digest!r}")
    return list(zip(addresses, digests))


def resolve_address(address: str, root: Path) -> Path:
    """Resolve an address inside the repository, refusing anything that escapes it.

    A receipt that reaches outside the tree is not gradeable evidence about the
    tree, so containment is checked before any byte is read. Windows normalisation
    is refused rather than accommodated: a trailing space or dot is stripped by
    Win32, so the file opened would not be the address the receipt recorded, and
    the same receipt would grade differently on Linux.
    """
    if address.startswith("/") or address.startswith("\\") or ":" in address:
        raise ReceiptError(f"address is not repository-relative: {address!r}")
    if "\\" in address:
        raise ReceiptError(f"address is not slash-separated: {address!r}")
    if "\x00" in address:
        raise ReceiptError(f"address contains a null byte: {address!r}")
    for part in address.split("/"):
        if part in (".", ".."):
            raise ReceiptError(
                f"address is not canonical: {address!r} carries a {part!r} segment")
        if part.rstrip(". ") != part:
            raise ReceiptError(f"address segment {part!r} is normalised away by the host")
        if part.split(".")[0].lower() in RESERVED_NAMES:
            raise ReceiptError(f"address names the reserved device {part!r}")
    candidate = (root / address).resolve()
    if candidate != root.resolve() and root.resolve() not in candidate.parents:
        raise ReceiptError(f"address escapes the repository: {address!r}")
    return candidate


def verify_shape(path: Path) -> tuple[dict[str, Any], list[tuple[str, str]]]:
    """Read one receipt and return it with its address/digest pairs, or refuse it.

    The single entry point `sovwitness/records.py` uses. Every refusal it can raise
    is about the document; none can be produced by a subject changing.
    """
    document = json.loads(path.read_text(encoding="utf-8"),
                          object_pairs_hook=_no_duplicate_keys)
    _conforms(document)
    return document, _pairs(document)
