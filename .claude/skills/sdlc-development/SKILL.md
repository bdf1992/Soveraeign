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
the implementation order, style, testing, and repository-history rules;
`ENGINEERING.md` owns the baseline, primitives, and module budget.
`contracts/repository-candidate-lifecycle.json` is the executable carrier-state
projection for repository candidates.

## Duties

1. Follow the implementation order in `AGENTS.md` exactly: name the
   operation, contract and conformance cases first, smallest implementation,
   focused unit tests, `python scripts/verify.py` from a clean root, then
   `decisions/` and `STATUS.yaml` for changed policy or standing.
2. While the repository carrier is `MUTABLE`, reconcile it against current
   `main` and remove construction noise when useful. Amend, rebase, and
   autosquash are construction operations here, not evidence operations.
3. After repairs and reconciliation, freeze one exact candidate revision before
   evidence that may survive the build is gathered. Record the candidate commit,
   tree, and base named by `contracts/repository-candidate-lifecycle.json`.
4. Never rewrite a `FROZEN` candidate. A needed repair or moved base supersedes
   that subject and produces a new candidate whose evidence must be earned again.
5. Write no business logic without a prior contract, fixture, or explicit
   experimental label, and never weaken an oracle to pass.
6. Respect the technical baseline: standard library first, SQLite record,
   content-addressed payloads, JSON Schema at machine boundaries, modules
   below 300 lines, dependencies only with a decision record.
7. Match the vocabulary in `CLASSIFICATION.md` and `SPEC.md`; create no
   synonyms for standing, event, effect, or role terms.
8. Report `BUILT` evidence only. A green build is not witnessing and never
   authority.

## Refusals

Refuse contractless business logic, silent dependencies, oracle weakening,
rewriting a frozen evidence subject, and any claim of standing beyond what the
evidence establishes.
