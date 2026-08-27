"""Grade every witness receipt against the bytes it says it observed.

`witness/observations/` holds one JSON receipt per observation. Each carries an
`artifact_revision` and, under `observed`, a list of addresses paired with the
`sha256:` digest the witness computed over each one. Until this existed, nothing
recomputed them, so a receipt kept reading as evidence about the working tree
long after the tree had moved underneath it.

This recomputes each digest from the file's bytes at the moment of the check. It
reads no field in which a receipt states its own freshness, and it never asks the
subject whether it changed.

Grading settles nothing. A receipt is an observation of a named commit and it
never claimed to describe the present, so a subject that has legitimately moved
is reported as drift rather than failed. Two things are failed, because neither
is a subject changing:

- `INVALID` — the receipt's own shape cannot be graded. A receipt that digests
  nothing, names a count of digests that does not match its addresses, or points
  outside the repository is not weak evidence; it is unmeasurable while looking
  measurable, which is the defect this module exists to catch.
- `STALE_PROBE` — an address under `witness/` moved. The witness digested its own
  probe into the receipt, so when that byte range changes the receipt no longer
  describes the code that produced its results. Subject drift ages a record;
  probe drift voids it.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any
import json

DIGEST_PREFIX = "sha256:"
DIGEST_LENGTH = 64
HEX_DIGITS = frozenset("0123456789abcdef")
# An address under this prefix is the witness's own machinery, not the subject.
WITNESS_PREFIX = "witness/"
CURRENT, STALE_SUBJECT, STALE_PROBE, INVALID = (
    "CURRENT", "STALE_SUBJECT", "STALE_PROBE", "INVALID")
FAILING_VERDICTS = frozenset({STALE_PROBE, INVALID})


class ReceiptError(ValueError):
    """The receipt cannot be graded at all, which is a defect and not subject drift."""


def digest_of(path: Path) -> str:
    """The recorded digest shape: `sha256:` over the file's exact bytes."""
    return DIGEST_PREFIX + sha256(path.read_bytes()).hexdigest()


def _well_formed(digest: Any) -> bool:
    """A digest string this module is willing to compare against."""
    if not isinstance(digest, str) or not digest.startswith(DIGEST_PREFIX):
        return False
    body = digest[len(DIGEST_PREFIX):]
    return len(body) == DIGEST_LENGTH and set(body) <= HEX_DIGITS


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
        raise ReceiptError(
            f"{len(addresses)} address(es) against {len(digests)} digest(s)")
    for address in addresses:
        if not isinstance(address, str) or not address.strip():
            raise ReceiptError(f"address is not a non-empty string: {address!r}")
    for digest in digests:
        if not _well_formed(digest):
            raise ReceiptError(f"digest is not a sha256 hex string: {digest!r}")
    return list(zip(addresses, digests))


def _resolve(address: str, root: Path) -> Path:
    """Resolve an address inside the repository, refusing anything that escapes it.

    A receipt that reaches outside the tree is not gradeable evidence about the
    tree, so containment is checked before any byte is read.
    """
    if address.startswith("/") or address.startswith("\\") or ":" in address:
        raise ReceiptError(f"address is not repository-relative: {address!r}")
    if "\\" in address:
        raise ReceiptError(f"address is not slash-separated: {address!r}")
    candidate = (root / address).resolve()
    if candidate != root.resolve() and root.resolve() not in candidate.parents:
        raise ReceiptError(f"address escapes the repository: {address!r}")
    return candidate


def grade(path: Path, root: Path) -> dict[str, Any]:
    """Recompute every digest a receipt declares and name what moved."""
    result: dict[str, Any] = {"receipt": path.name, "verdict": CURRENT,
                              "moved": [], "defects": [], "graded": 0}
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
        pairs = _pairs(document)
    except json.JSONDecodeError as broken:
        result.update(verdict=INVALID, defects=[f"unreadable JSON: {broken}"])
        return result
    except (ReceiptError, OSError, UnicodeDecodeError) as broken:
        result.update(verdict=INVALID, defects=[str(broken)])
        return result

    result["revision"] = document["artifact_revision"]
    probe_drift = False
    subject_drift = False
    for address, recorded in pairs:
        try:
            target = _resolve(address, root)
        except ReceiptError as broken:
            result.update(verdict=INVALID, defects=result["defects"] + [str(broken)])
            return result
        is_witness_owned = address.startswith(WITNESS_PREFIX)
        if not target.exists():
            result["moved"].append(f"{address}: gone from the tree")
        elif target.is_dir():
            result.update(verdict=INVALID,
                          defects=result["defects"] + [f"address is a directory: {address}"])
            return result
        else:
            result["graded"] += 1
            live = digest_of(target)
            if live == recorded:
                continue
            result["moved"].append(
                f"{address}: recorded {recorded[len(DIGEST_PREFIX):][:16]}, "
                f"tree reads {live[len(DIGEST_PREFIX):][:16]}")
        probe_drift = probe_drift or is_witness_owned
        subject_drift = subject_drift or not is_witness_owned

    if probe_drift:
        result["verdict"] = STALE_PROBE
        result["defects"].append(
            "an address under witness/ moved: the receipt no longer describes the code "
            "that produced its results")
    elif subject_drift:
        result["verdict"] = STALE_SUBJECT
    return result


def observations_dir(root: Path) -> Path:
    return root / "witness" / "observations"


def grade_all(root: Path) -> list[dict[str, Any]]:
    """Grade every receipt, in a stable order."""
    directory = observations_dir(root)
    if not directory.is_dir():
        return []
    return [grade(path, root) for path in sorted(directory.glob("*.json"))]
