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
  nothing, recomputes nothing, names the same address twice, or points outside
  the repository is not weak evidence; it is unmeasurable while looking
  measurable, which is the defect this module exists to catch.
- `STALE_PROBE` — an address under `witness/` moved. The witness digested its own
  probe into the receipt, so when that byte range changes the receipt no longer
  describes the code that produced its results. Subject drift ages a record;
  probe drift voids it.

Known residual, recorded rather than fixed: `artifact_revision` is checked for
being a non-empty string and nothing more. Nothing ties the recorded digests to
that commit, so `CURRENT` means "the tree matches what this file says", not "this
witness computed these digests at that revision". Reading the revision out of git
would make the receipt falsifiable and is the obvious next move; it needs a
subprocess per receipt and was not paid for here. The address set is likewise the
receipt author's own choice, so a witness that observed nothing can name files it
knows will not move. Neither gap is closed by this module.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any
import json

DIGEST_PREFIX = "sha256:"
DIGEST_LENGTH = 64
HEX_DIGITS = frozenset("0123456789abcdef")
# The first path segment that marks an address as the witness's own machinery.
WITNESS_SEGMENT = "witness"
# Win32 resolves these to a device wherever they appear, so `nul` exists in every
# directory and reads as an empty file. A receipt naming one would digest zero
# bytes and grade CURRENT forever, having measured nothing.
RESERVED_NAMES = frozenset(
    ["con", "prn", "aux", "nul"]
    + [f"com{digit}" for digit in range(1, 10)]
    + [f"lpt{digit}" for digit in range(1, 10)])
CURRENT, STALE_SUBJECT, STALE_PROBE, INVALID = (
    "CURRENT", "STALE_SUBJECT", "STALE_PROBE", "INVALID")
FAILING_VERDICTS = frozenset({STALE_PROBE, INVALID})


class ReceiptError(ValueError):
    """The receipt cannot be graded at all, which is a defect and not subject drift."""


def digest_of(path: Path) -> str:
    """The recorded digest shape: `sha256:` over the file's exact bytes."""
    return DIGEST_PREFIX + sha256(path.read_bytes()).hexdigest()


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


def _resolve(address: str, root: Path) -> Path:
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


def _witness_owned(candidate: Path, root: Path) -> bool:
    """Whether a resolved address is the witness's own machinery.

    Classified on the resolved path and never on the declared string: `./witness/x`
    and `subject/../witness/x` name the same file, and reading the raw prefix let a
    receipt downgrade its own probe drift to subject drift by respelling one field.
    """
    try:
        relative = candidate.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return bool(relative.parts) and relative.parts[0].lower() == WITNESS_SEGMENT


def grade(path: Path, root: Path) -> dict[str, Any]:
    """Recompute every digest a receipt declares and name what moved."""
    result: dict[str, Any] = {"receipt": path.name, "verdict": CURRENT,
                              "moved": [], "defects": [], "graded": 0}

    def invalid(detail: str) -> dict[str, Any]:
        result.update(verdict=INVALID, defects=result["defects"] + [detail])
        return result

    try:
        document = json.loads(path.read_text(encoding="utf-8"),
                              object_pairs_hook=_no_duplicate_keys)
        pairs = _pairs(document)
    except json.JSONDecodeError as broken:
        return invalid(f"unreadable JSON: {broken}")
    except (ReceiptError, OSError, ValueError, UnicodeDecodeError) as broken:
        return invalid(str(broken))

    result["revision"] = document["artifact_revision"]
    probe_drift = False
    subject_drift = False
    for address, recorded in pairs:
        try:
            target = _resolve(address, root)
            missing = not target.exists()
            directory = not missing and target.is_dir()
        except (ReceiptError, OSError, ValueError) as broken:
            return invalid(str(broken))
        if directory:
            return invalid(f"address is a directory: {address}")
        is_witness_owned = _witness_owned(target, root)
        if missing:
            result["moved"].append(f"{address}: gone from the tree")
        else:
            try:
                live = digest_of(target)
            except (OSError, ValueError) as broken:
                return invalid(f"{address} could not be read: {broken}")
            result["graded"] += 1
            if live == recorded:
                continue
            result["moved"].append(
                f"{address}: recorded {recorded[len(DIGEST_PREFIX):][:16]}, "
                f"tree reads {live[len(DIGEST_PREFIX):][:16]}")
        probe_drift = probe_drift or is_witness_owned
        subject_drift = subject_drift or not is_witness_owned

    if not result["graded"]:
        return invalid("no address could be recomputed, so the receipt measures nothing "
                       "against this tree")
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


def receipts(root: Path) -> list[Path]:
    """Every receipt under the directory, at any depth, in a stable order.

    The walk is recursive and case-folded because a non-recursive `*.json` let a
    receipt hide in a subdirectory, and `Path.glob` is case-insensitive on Windows
    and not on the Linux runner that gates the merge.
    """
    directory = observations_dir(root)
    if not directory.is_dir():
        return []
    return sorted(path for path in directory.rglob("*")
                  if path.is_file() and path.suffix.lower() == ".json")


def grade_all(root: Path) -> list[dict[str, Any]]:
    """Grade every receipt, in a stable order."""
    return [grade(path, root) for path in receipts(root)]
