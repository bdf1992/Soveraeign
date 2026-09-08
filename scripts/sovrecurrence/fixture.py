"""A fixture basis for the definition-recurrence self-check, and the variants that defeat it.

Everything is built under a temporary root: a fixture custody collection whose clauses carry
fixture members, the ten contracts that declare the primitives, and one contract a bound
primitive names as governing it. Nothing here reads or writes the real repository, names a
real principal, or witnesses anything.

The collection deliberately carries a member at `BUILT` and one at `NOT_WITNESSED` as well
as members at `WITNESSED`. A basis that admitted either would be citing work nobody
independently judged - the second is worse, because an observation refused it by name - so
the positive variant is checked for their *absence* as well as for passing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
import json

from sovrecurrence import neutrality, recurrence

COLLECTION = "contracts/custodies/phase-1-5.json"
SETTLED = ("P15-F1", "P15-F2")
BUILT_ONLY_ADDRESS = "scripts/fixture_unwitnessed.py"
REFUSED_ADDRESS = "scripts/fixture_not_witnessed.py"
"""A member at `NOT_WITNESSED`, which contains the token `WITNESSED` (`CLAUDE.md`, trap T3).
The reader compares whole tokens, and until a sixth witness said so nothing proved it: a
substring comparison passed every variant and every test while admitting this member."""
GOVERNING_STUB = "contracts/fixture-governing.json"
"""A contract the `settlement` stub names in its own `governed_by`. Open by default, so the
graded-governance path is exercised in both directions rather than only when it fires."""
OPEN_ROLES = ("procurement-steward", "supplier-liaison", "worker")
"""One proving-role name and two an alternate institution uses: not a closed vocabulary."""
CLOSED_ROLES = ("worker", "orchestrator", "controller", "owner")
"""The vocabulary a third witness found in this repository: closed without being four-of-four."""
INSTANCE_KEYS = ("examples", "example", "fixtures")
"""Keys the mispaired variant fills with instance data that declares its term.

Written out rather than taken from `declaration.EXAMPLE_KEYS`, and that is the whole point.
The first version of this variant did read the constant, so emptying the constant emptied the
variant too and the self-check stayed green under the exact regression it exists to refuse: a
fixture derived from the rule under test cannot refuse a narrowing of that rule. It must
name exactly the excluded keys - one the rule legitimately reads would make the variant
resolve for the right reason under the right rule - and a unit test pins the equality, so a
key added to `EXAMPLE_KEYS` and not here fails there rather than passing silently."""


def _mispaired(term: str) -> dict[str, Any]:
    """A contract that says `term` everywhere prose is allowed and declares it nowhere.

    This is the whole excluded set, not one key of it.

    A sixth witness reintroduced `description` reading and watched the self-check stay green,
    because the variant carried its term in a title alone: the fixture certified one prose
    key out of five while its docstring claimed the class. A seventh found the same shape one
    level down - `EXAMPLE_KEYS` had three members and the variant exercised one, so narrowing
    it to `("examples",)` passed the whole gate and an `example` block then took the live
    reading from nine of ten to ten. It also showed that the restriction to
    `DECLARED_NAME_KEYS` had no refusal case at all: harvesting every dict key in the document
    left the self-check green.

    So every prose key says the term at the root and again below it, every example key carries
    an instance that declares it, and `sections` holds it as an ordinary dict key that no
    schema keyword reaches. A reader that reads any of those resolves this contract, the
    declared defeat does not fire, and `selfcheck` fails by name.
    """
    said = f"Fixture {term} declaration"
    prose = {"title": said, "name": said, "description": said, "note": said,
             "$comment": said, "warrant": said}
    instance = {"properties": {f"{term}_id": {"type": "string"}}}
    stub: dict[str, Any] = {
        "$id": "https://soveraeign.local/contracts/fixture-unrelated.schema.json",
        "properties": {"actor_id": dict({"type": "string", "enum": [said]}, **prose)},
        "sections": {term: {"kind": "string"}},
        "elsewhere": dict(prose),
    }
    stub.update(prose)
    for key in INSTANCE_KEYS:
        stub[key] = [instance] if key.endswith("s") else dict(instance)
    return stub


def _stub(term: str, **extra: Any) -> dict[str, Any]:
    """A fixture contract that declares `term` the way a real one does: in its own identity.

    The declaration lives in `$id` and not in a comment or a title, because both are prose
    and the reader stopped reading prose.

    The title deliberately names no primitive. A fifth witness showed why it must: while
    every stub's title carried its own term, reintroducing the exact title-reading defect
    this branch repaired left `selfcheck` at exit 0, because the mispaired stub's title said
    `unrelated` and a title-reading reader refused it for the right verdict by the wrong
    rule. `primitive-mispaired` now carries a title that names the term it is *not* paired
    with, so a reader that reads titles resolves it, the declared defeat does not fire, and
    the self-check goes red.
    """
    stub: dict[str, Any] = {
        "$id": f"https://soveraeign.local/contracts/fixture-{term}.schema.json",
        "title": "Fixture contract, whose title names no primitive",
        "properties": {"actor_id": {"type": "string"}},
    }
    stub.update(extra)
    return stub

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
    "primitive-mispaired": {
        "P15-Q4.3": ["institution-neutral composition lacks governed primitives",
                     "alternate institution cannot compose the same primitives"]},
    "role-vocabulary-closed": {
        "P15-Q4.3": ["composition depends on fixed proving-role names",
                     "alternate institution cannot compose the same primitives"]},
    "governed-vocabulary-closed": {
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

`primitive-mispaired` and `governed-vocabulary-closed` cover the two rules a fourth witness
changed, so the self-check refuses a regression of either rather than leaving it to the unit
tests alone. Both routes reach `scripts/verify.py`: it runs this self-check as the
"definition recurrence slice" and it runs `scripts/tests/test_sov_recurrence.py` inside
"repository tooling tests". Two commit messages on this branch and an earlier draft of the
custody note said otherwise, on a claim carried forward from a third witness that a sixth
one disproved by planting the defect and watching `verify.py` exit 1. An earlier fixture
wrote `"$comment": "declares the {primitive} primitive"` into every stub,
which meant the fixture could never disagree with a binding: whatever path `PRIMITIVES`
named, the stub written there declared the term. A witness named that gap and it is closed
here - `primitive-mispaired` writes a contract that parses and declares structure that is
simply not the term it is paired with, which is the case a real mispairing produces, under a
title that names the term it is not paired with, so that a reader which reads titles fails
this self-check by name.
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
    _write(root / REFUSED_ADDRESS, '"""Fixture member an observation explicitly refused."""\n')
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
                             "stage_observed_by": None},
                            {"member_kind": "ITEM", "address": REFUSED_ADDRESS,
                             "standing": "NOT_WITNESSED", "work_state": "LANDED",
                             "stage_observed_by": "fixture refusal"}]),
        _custody("P15-F4", []),
    ]
    _write(root / COLLECTION, {"collection_schema": "soveraeign-custody-collection/v1",
                               "phase": "phase:fixture", "custodies": custodies})
    _write(root / "STATUS.yaml", "phase: phase:fixture\n")
    _write(root / "contracts/phases.json", {"phases": [{"phase_id": "phase:fixture"}]})
    for primitive, (relative, term) in neutrality.PRIMITIVES.items():
        extra = {"governed_by": [GOVERNING_STUB]} if primitive == "settlement" else {}
        _write(root / relative, _stub(term, **extra))
    _write(root / GOVERNING_STUB, {"$id": "https://soveraeign.local/contracts/fixture-governing",
                                   "properties": {"filled_by": {"enum": list(OPEN_ROLES)}}})
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
        (root / neutrality.PRIMITIVES["custody"][0]).unlink()
    elif variant == "primitive-mispaired":
        _write(root / neutrality.PRIMITIVES["custody"][0], _mispaired("custody"))
    elif variant == "role-vocabulary-closed":
        _write(root / neutrality.PRIMITIVES["finding"][0],
               _stub("finding", properties={"evaluator_role": {
                   "enum": ["CONTROLLER", "ORCHESTRATOR", "WORKER", "WITNESS"]}}))
    elif variant == "governed-vocabulary-closed":
        _write(root / GOVERNING_STUB,
               {"$id": "https://soveraeign.local/contracts/fixture-governing",
                "properties": {"filled_by": {"enum": list(CLOSED_ROLES)}}})


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
