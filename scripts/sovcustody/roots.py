"""What a root is, and whether it resolves.

A custody's roots are the join between work and the product intent that
justifies it, so "does this resolve" is the question the whole layer rests on.
It lives here rather than inside the grader because the answer differs by root
kind and one of those kinds - PREDICATE - is not resolvable by reading a
document at all.

Also holds the orphan reading: declared work no custody collects. A custody set
that covers everything is not the goal; knowing what it misses is.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

#: Documents that own an identifier-shaped reference, by root kind.
OWNERS = {
    "GROUND": "contracts/product-ground.json",
    "CANON": "contracts/product-canon.json",
    "REQUIREMENT": "PRD.md",
    "PHASE": "ROADMAP.md",
    "SEAM": "OPEN-SEAMS.md",
}


def predicate_ids() -> set[str]:
    """Every normative predicate identifier, from the module that derives them.

    `PRED-I-1.1`, `TRANS-admit` and `PARITY-1` are synthesised from SPEC.md prose
    by the F2 gate rather than written literally in the document. Resolving them
    against a substring search of SPEC.md would therefore fail on every one, so
    the deriver is asked instead. It is the authority for these identifiers, and
    a predicate the gate no longer derives is a root that genuinely no longer
    resolves.
    """
    try:
        import sov_f2_gate  # noqa: PLC0415
        spec = (ROOT / "SPEC.md").read_bytes().decode("utf-8")
        return {row["id"] for row in sov_f2_gate.normative_predicates(spec)}
    except (ImportError, OSError, KeyError):
        return set()


def root_resolves(root: dict[str, Any]) -> bool:
    """Whether a declared root names something this repository actually holds.

    GROUND, CANON and REQUIREMENT roots are identifier references into contracts
    and PRD.md rather than paths; a path-shaped reference is checked as a path,
    and an identifier is checked by substring against the document that owns it.
    PREDICATE is the exception and is resolved through the deriver, see above.
    """
    reference = str(root.get("reference") or "")
    kind = str(root.get("root_kind") or "")
    if kind == "PREDICATE":
        return reference in predicate_ids()
    bare = reference.split("#", 1)[0]
    if bare and ("/" in bare or bare.endswith(".md")):
        return (ROOT / bare).exists()
    relative = OWNERS.get(kind)
    owner = ROOT / relative if relative else None
    if owner is None or not owner.exists():
        return False
    return reference.split("#")[-1] in owner.read_bytes().decode("utf-8")



def orphans(custodies, kind: str | None = None) -> list[str]:
    """Declared work this collection does not collect, by member kind.

    A custody set that covers everything is not the goal; knowing what it misses
    is. Today this reads the open seam register, because a seam carried as prose
    is the clearest case of work nobody holds.
    """
    held = {
        str(member.get("address"))
        for custody in custodies
        for member in custody.get("members") or []
    }
    missing: list[str] = []
    if kind in (None, "SEAM"):
        text = (ROOT / "OPEN-SEAMS.md").read_bytes().decode("utf-8")
        for line in text.splitlines():
            if line.startswith("## S") and "closed" not in line.lower():
                identifier = line.split("·")[0].replace("##", "").strip()
                address = f"OPEN-SEAMS.md#{identifier}"
                if address not in held:
                    missing.append(address)
    return missing
