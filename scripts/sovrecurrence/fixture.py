"""A fixture basis for the definition-recurrence self-check, and the variants that defeat it.

Everything is built under a temporary root: a fixture custody collection whose clauses carry
fixture members, fixture witness records and receipts that observe them, and the ten
contracts that declare the primitives. Nothing here reads or writes the real repository,
names a real principal, or witnesses anything.

The collection deliberately carries a member at `BUILT` as well as members at `WITNESSED`.
A basis that admitted the built one would be citing work nobody independently judged, so
the positive variant is checked for its *absence* as well as for passing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
import json

from sovrecurrence import neutrality, recurrence

COLLECTION = "contracts/custodies/phase-1-5.json"
SETTLED = ("P15-F1", "P15-F2")
BUILT_ONLY_ADDRESS = "scripts/fixture_unwitnessed.py"

EXPECTED_FAILURES: dict[str, dict[str, list[str]]] = {
    "basis-dropped": {
        "P15-Q4.1": ["candidate Definition did not preserve its settled evidence basis"]},
    "no-sources": {
        "P15-Q4.1": ["candidate Definition lacks proposal identity or cited sources",
                     "candidate Definition did not preserve its settled evidence basis"]},
    "standing-taken": {"P15-Q4.2": ["candidate acquired standing from experience"]},
    "authority-taken": {"P15-Q4.2": ["candidate acquired authority from evidence"]},
    "policy-moved": {"P15-Q4.2": ["successful experience automatically changed policy",
                                  "successful experience automatically changed phase"]},
    "primitive-undeclared": {
        "P15-Q4.3": ["institution-neutral composition lacks governed primitives",
                     "alternate institution cannot compose the same primitives"]},
    "role-vocabulary-closed": {
        "P15-Q4.3": ["composition depends on fixed proving-role names",
                     "alternate institution cannot compose the same primitives"]},
}
"""Which predicates each defeating variant must fail, with the exact defects each must give;
every other predicate must hold.

A candidate that drops one settled address still has sources, so only the basis test fails;
a candidate that cites none fails both halves of Q4.1, because an identity over an empty
basis is not an identity. Moving a governing record fails policy and phase together: the
reader cannot tell which record's movement mattered and does not guess. Removing a
primitive's declaration and closing its vocabulary both defeat the alternate institution,
because a primitive that cannot be resolved and one that only the proving roles may fill
are equally uncomposable by an institution the founder did not predict.
"""


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = payload if isinstance(payload, str) else json.dumps(payload, indent=2, sort_keys=True)
    path.write_text(text + ("" if text.endswith("\n") else "\n"), encoding="utf-8", newline="\n")


def _custody(clause: str, members: list[dict[str, Any]]) -> dict[str, Any]:
    return {"custody_schema": "soveraeign-custody/v1", "status": "PROPOSED",
            "custody_id": f"custody:fixture/{clause.lower()}", "custody_kind": "EXIT",
            "phase": "phase:fixture", "exit_clause": clause, "members": members}


def build(root: Path) -> Path:
    """Write the fixture basis under `root` and return the root it was written to."""
    for index, clause in enumerate(SETTLED, start=1):
        _write(root / f"scripts/fixture_member_{index}.py", f'"""Fixture member {index}."""\n')
        _write(root / f"witness/fixture-{index}.md",
               f"# Fixture witness record {index}\n\nsubject: scripts/fixture_member_{index}.py\n"
               f"standing_supported: WITNESSED\n")
        _write(root / f"witness/observations/fixture-{index}.json",
               {"observer": f"principal:fixture-witness-{index}", "contributed_to_build": False,
                "subject": f"scripts/fixture_member_{index}.py",
                "standing_supported": "WITNESSED"})
    _write(root / BUILT_ONLY_ADDRESS, '"""Fixture member nobody independently observed."""\n')
    custodies = [
        _custody(SETTLED[0], [{"member_kind": "ITEM", "address": "scripts/fixture_member_1.py",
                               "standing": "WITNESSED", "work_state": "LANDED",
                               "stage_observed_by": "fixture pass 1 (witness/fixture-1.md; "
                                                    "witness/observations/fixture-1.json)"}]),
        _custody(SETTLED[1], [{"member_kind": "ITEM", "address": "scripts/fixture_member_2.py",
                               "standing": "WITNESSED", "work_state": "LANDED",
                               "stage_observed_by": "fixture pass 1 (witness/fixture-2.md; "
                                                    "witness/observations/fixture-2.json)"}]),
        _custody("P15-F3", [{"member_kind": "ITEM", "address": BUILT_ONLY_ADDRESS,
                             "standing": "BUILT", "work_state": "LANDED",
                             "stage_observed_by": None}]),
        _custody("P15-F4", []),
    ]
    _write(root / COLLECTION, {"collection_schema": "soveraeign-custody-collection/v1",
                               "phase": "phase:fixture", "custodies": custodies})
    _write(root / "STATUS.yaml", "phase: phase:fixture\n")
    _write(root / "contracts/phases.json", {"phases": [{"phase_id": "phase:fixture"}]})
    for primitive, relative in neutrality.PRIMITIVES.items():
        _write(root / relative, {"title": f"Fixture {primitive} declaration",
                                 "$comment": f"declares the {primitive} primitive",
                                 "properties": {"actor_id": {"type": "string"}}})
    return root


def _drop_source(observed: dict[str, Any]) -> dict[str, Any]:
    observed["candidate"]["source_addresses"] = observed["candidate"]["source_addresses"][1:]
    return observed


def _no_sources(observed: dict[str, Any]) -> dict[str, Any]:
    observed["candidate"]["source_addresses"] = []
    return observed


def _set(field: str, value: Any) -> Callable[[dict[str, Any]], dict[str, Any]]:
    def mutate(observed: dict[str, Any]) -> dict[str, Any]:
        observed["candidate"][field] = value
        return observed
    return mutate


MUTATIONS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "basis-dropped": _drop_source,
    "no-sources": _no_sources,
    "standing-taken": _set("standing", "RATIFIED"),
    "authority-taken": _set("authority_effect", "BINDING"),
}
"""Variants that defeat the candidate itself, applied to the observation the oracle grades.
The reading that produced it was sound; what the oracle must catch is the candidate."""


def _defeat_root(root: Path, variant: str) -> None:
    """Variants that defeat the basis rather than the candidate, applied to the fixture root."""
    if variant == "primitive-undeclared":
        (root / neutrality.PRIMITIVES["custody"]).unlink()
    elif variant == "role-vocabulary-closed":
        _write(root / neutrality.PRIMITIVES["finding"],
               {"title": "Fixture finding declaration",
                "properties": {"evaluator_role": {"enum": ["CONTROLLER", "ORCHESTRATOR",
                                                           "WORKER", "WITNESS"]}}})


def run_variant(root: Path, variant: str) -> dict[str, Any]:
    """One reading of the fixture basis under `variant`; `positive` defeats nothing."""
    if variant == "policy-moved":
        def mutate(observed: dict[str, Any]) -> dict[str, Any]:
            """Move a governing record and declare nothing; the reader must notice."""
            _write(root / "STATUS.yaml", "phase: phase:fixture\nedited_by_synthesis: true\n")
            return observed
        return recurrence.run(root, COLLECTION, mutate)
    _defeat_root(root, variant)
    return recurrence.run(root, COLLECTION, MUTATIONS.get(variant))
