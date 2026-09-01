---
name: sdlc-qa
description: QA domain competence for the SDLC loop - both verification stances. The Blue lane proves declared positive and defeating cases; the Red lane adversarially seeks undeclared defeats under a scoped grant. Use when verifying, witnessing, or challenging built work.
---

# QA Domain Skill

Standing: the loop is accepted as the operating shape (`decisions/0024-open-decision-drain.md`,
O13) and read through `decisions/0023-acceptance-not-approval.md`: `RIGHT` is owner
acceptance over an evidenced result, not permission to begin. The implementation is a
skeleton.

`SDLC.md` owns the Red/Blue dyad and the release gate. One operator holds
one stance per engagement; the lanes must not merge.
`contracts/repository-candidate-lifecycle.json` declares the repository
candidate subject that evidence must address.

## Blue lane

1. Prove every consequential behavior with at least one positive case and
   one declared defeating case, per `AGENTS.md` testing rules.
2. Run unit tests beside the service, semantic cases in `conformance/`, and
   `python scripts/verify.py` from a clean root within its budget.
3. Evidence intended to survive construction binds an exact `FROZEN`
   repository candidate: candidate commit, tree, and base. A mutable working
   tree may guide repair but is not a stable qualification subject.
4. Distinguish attempted, reported, observed, and settled outcomes. A green
   run establishes `BUILT` evidence only.

## Red lane

1. Operate only under a typed grant naming target surfaces, effect class,
   budget, and exit criterion.
2. Work from the contract, claimed invariants, and exact frozen built artifact —
   never from the builder's tests, plan, or assumptions as evidence, and never
   importing participant implementation into the oracle.
3. Hunt undeclared defeats: refusal bypasses, authority escalation,
   stale-source use, provenance gaps, evidence-subject substitution, retraction
   that erases history, and executor-only success.
4. File findings as proposals with exact reproduction inputs and the candidate
   identity they concern. A finding counts only after independent reproduction;
   confirmed findings become permanent defeating fixtures.
5. If the candidate is repaired, rebased, squashed, amended, or otherwise
   replaced after freeze, treat the replacement as a new subject. Do not transfer
   findings, witness, or qualification by patch equivalence.
6. Stop at dry-run convergence: the declared number of consecutive rounds
   with no new confirmed finding.

## Refusals

Refuse to weaken a fixture to admit a participant, to witness work you built,
to qualify a mutable or mismatched repository subject, to fabricate or inflate
findings, and to exceed the engagement grant.
