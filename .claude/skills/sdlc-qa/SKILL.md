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

## Blue lane

1. Prove every consequential behavior with at least one positive case and
   one declared defeating case, per `AGENTS.md` testing rules.
2. Run unit tests beside the service, semantic cases in `conformance/`, and
   `python scripts/verify.py` from a clean root within its budget.
3. Distinguish attempted, reported, observed, and settled outcomes. A green
   run establishes `BUILT` evidence only.

## Red lane

1. Operate only under a typed grant naming target surfaces, effect class
   (Phase I: `RECORD_LOCAL`, isolated environments, no authoritative
   writes), budget, and exit criterion.
2. Work from the contract, claimed invariants, and built artifact — never
   from the builder's tests, plan, or assumptions, and never importing the
   participant implementation.
3. Hunt undeclared defeats: refusal bypasses, authority escalation,
   stale-source use, provenance gaps, retraction that erases history,
   executor-only success.
4. File findings as proposals with exact reproduction inputs. A finding
   counts only after independent reproduction; confirmed findings become
   permanent defeating fixtures.
5. Stop at dry-run convergence: the declared number of consecutive rounds
   with no new confirmed finding.

## Refusals

Refuse to weaken a fixture to admit a participant, to witness work you
built, to fabricate or inflate findings, and to exceed the engagement grant.
