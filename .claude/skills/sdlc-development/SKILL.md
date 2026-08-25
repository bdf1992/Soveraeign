---
name: sdlc-development
description: Development domain competence for the SDLC loop - implement changes under the repository's implementation order, technical baseline, and style rules. Use when a concern's operation writes or changes code, contracts, or fixtures.
---

# Development Domain Skill

Standing: the loop is accepted as the operating shape (`decisions/0024-open-decision-drain.md`,
O13) and read through `decisions/0023-acceptance-not-approval.md`: `RIGHT` is owner
acceptance over an evidenced result, not permission to begin. The implementation is a
skeleton.

The rules are owned elsewhere; this skill sequences them. `AGENTS.md` owns
the implementation order, style, and testing rules; `ENGINEERING.md` owns
the baseline, primitives, and module budget.

## Duties

1. Follow the implementation order in `AGENTS.md` exactly: name the
   operation, contract and conformance cases first, smallest implementation,
   focused unit tests, `python scripts/verify.py` from a clean root, then
   `decisions/` and `STATUS.yaml` for changed policy or standing.
2. Write no business logic without a prior contract, fixture, or explicit
   experimental label, and never weaken an oracle to pass.
3. Respect the technical baseline: standard library first, SQLite record,
   content-addressed payloads, JSON Schema at machine boundaries, modules
   below 300 lines, dependencies only with a decision record.
4. Match the vocabulary in `CLASSIFICATION.md` and `SPEC.md`; create no
   synonyms for standing, event, effect, or role terms.
5. Report `BUILT` evidence only. A green build is not witnessing and never
   authority.

## Refusals

Refuse contractless business logic, silent dependencies, oracle weakening,
and any claim of standing beyond what the evidence establishes.
