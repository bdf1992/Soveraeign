"""One definition-recurrence reading, graded by the independent commissioning oracle.

The reader gathers settled experience, synthesizes a candidate Definition from it, observes
whether synthesis moved any governing record, resolves the ten primitives, and hands the
resulting observation to `conformance/commissioning.py`. The predicates are graded there
and nowhere here: an instrument that scores itself proves nothing, and the oracle imports
no participant code by construction.

A passing run is a build claim about this reading. It is not a witness, and it does not
advance the clause by itself.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import sys

from sovrecurrence import candidate, experience, neutrality

CONFORMANCE = Path(__file__).resolve().parents[2] / "conformance"
if str(CONFORMANCE) not in sys.path:
    sys.path.insert(0, str(CONFORMANCE))

import commissioning  # noqa: E402

PREDICATES = ("P15-Q4.1", "P15-Q4.2", "P15-Q4.3")


def observe(root: Path, collection_path: str = experience.CUSTODY_COLLECTION,
            mutate: Any = None) -> dict[str, Any]:
    """Build the observation P15-Q4 is graded on, reading files under `root` and nothing else.

    `mutate` is the self-check's seam: a callable the fixture passes to defeat exactly one
    property of an otherwise sound reading. The live reading passes none, so nothing here
    can quietly alter what the repository is graded on.

    It runs *before* the governing records are read back, so a variant that moves one is
    caught by the comparison rather than by declaring its own verdict. A fixture that could
    set `automatic_policy_change` itself would be asserting the property this reader exists
    to measure, which is the defect an independent witness found in the first version.
    """
    trace: list[str] = []
    before = candidate.governing_digests(root)
    gathered = experience.gather(root, collection_path)
    trace.append(f"settled experience: {len(gathered['sources'])} source(s) across "
                 f"{len(gathered['clauses'])} clause(s) of {collection_path}")
    try:
        collection = json.loads((root / collection_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        collection = {}
    synthesized = candidate.synthesize(root, gathered, collection)
    trace.append(f"candidate synthesized: {synthesized['proposal_id']} citing "
                 f"{len(synthesized['source_addresses'])} address(es), standing "
                 f"{synthesized['standing']}, authority {synthesized['authority_effect']}")
    composition = neutrality.read(root)
    trace.append(f"primitives: {len(composition['generic_primitives'])} resolved, "
                 f"{len(composition['closed_vocabularies'])} closed vocabulary(ies); "
                 f"{composition['alternate_institution']} composes: "
                 f"{composition['alternate_institution_composes']}")
    observed: dict[str, Any] = {
        "candidate": synthesized,
        "settled_evidence_addresses": [source["address"] for source in gathered["sources"]],
        "generic_primitives": composition["generic_primitives"],
        "fixed_role_names_required": composition["fixed_role_names_required"],
        "alternate_institution_composes": composition["alternate_institution_composes"],
    }
    if mutate is not None:
        observed = mutate(observed)
    for elsewhere in composition["closed_elsewhere"]:
        trace.append(f"closed vocabulary outside the bound primitives, reported not graded: "
                     f"{elsewhere}")
    after = candidate.governing_digests(root)
    moved = sorted(name for name in before if before[name] != after[name])
    if moved:
        trace.append(f"governing records moved across synthesis: {', '.join(moved)}")
    observed["automatic_policy_change"] = bool(moved)
    observed["automatic_phase_transition"] = bool(moved)
    return {"observed": observed, "trace": trace, "composition": composition,
            "gathered_defects": gathered["defects"], "governing_moved": moved}


def run(root: Path, collection_path: str = experience.CUSTODY_COLLECTION,
        mutate: Any = None) -> dict[str, Any]:
    """One reading with every predicate graded by the oracle; `passed` is the whole of it."""
    reading = observe(root, collection_path, mutate)
    grades = {predicate: commissioning.evaluate(predicate, reading["observed"])
              for predicate in PREDICATES}
    other = list(reading["gathered_defects"])
    return {
        "passed": not any(grades.values()) and not other,
        "grades": grades,
        "other_defects": other,
        "trace": reading["trace"],
        "candidate": reading["observed"]["candidate"],
        "facts": {
            "settled_sources": len(reading["observed"]["settled_evidence_addresses"]),
            "primitives_resolved": len(reading["observed"]["generic_primitives"]),
            "closed_vocabularies": reading["composition"]["closed_vocabularies"],
            "governing_moved": reading["governing_moved"],
        },
    }
