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

- `INVALID` — the receipt's own shape cannot be graded: `sovwitness/shape.py`
  refused it. A receipt that digests nothing, names the same address twice,
  points outside the repository, or does not conform to
  `contracts/participant-observation.schema.json` is not weak evidence; it is
  unmeasurable while looking measurable, which is the defect this layer catches.
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

from sovwitness.shape import (
    DIGEST_PREFIX, ReceiptError, resolve_address, verify_shape)

# The first path segment that marks an address as the witness's own machinery.
WITNESS_SEGMENT = "witness"
CURRENT, STALE_SUBJECT, STALE_PROBE, INVALID = (
    "CURRENT", "STALE_SUBJECT", "STALE_PROBE", "INVALID")
FAILING_VERDICTS = frozenset({STALE_PROBE, INVALID})


def digest_of(path: Path) -> str:
    """The recorded digest shape: `sha256:` over the file's exact bytes."""
    return DIGEST_PREFIX + sha256(path.read_bytes()).hexdigest()


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
                              "moved": [], "defects": [], "debts": [], "graded": 0}

    def invalid(detail: str) -> dict[str, Any]:
        result.update(verdict=INVALID, defects=result["defects"] + [detail])
        return result

    try:
        document, pairs = verify_shape(path)
    except json.JSONDecodeError as broken:
        return invalid(f"unreadable JSON: {broken}")
    except (ReceiptError, OSError, ValueError, UnicodeDecodeError) as broken:
        return invalid(str(broken))

    result["revision"] = document["artifact_revision"]
    probe_drift = False
    subject_drift = False
    for address, recorded in pairs:
        try:
            target = resolve_address(address, root)
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

    # Probe drift is decided before the recomputed-nothing rule so that the verdict
    # does not depend on the host's filesystem. A case-variant address is a real file
    # on Windows and a missing one on the Linux runner; deciding drift first makes both
    # read STALE_PROBE instead of splitting between STALE_PROBE and INVALID. Either
    # would fail, but a check that names a different defect per platform is a check a
    # reader cannot use.
    if probe_drift:
        result["verdict"] = STALE_PROBE
        result["defects"].append(
            "an address under witness/ moved: the receipt no longer describes the code "
            "that produced its results")
        return result
    # Recomputing nothing is reported and not failed. An earlier version made it
    # INVALID, which meant a receipt naming one subject that was later renamed
    # turned the build red while the same rename inside a two-address receipt
    # passed as drift: the verdict turned on how many addresses the author listed
    # rather than on what happened to the subject. Renames are routine here, and
    # the repair for a red build would have been to pad the address list.
    if not result["graded"]:
        result["debts"].append(
            "no address could be recomputed, so the receipt covers nothing in this tree")
    if subject_drift:
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
