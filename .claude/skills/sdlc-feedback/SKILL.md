---
name: sdlc-feedback
description: Feedback domain competence for the SDLC loop - review standing, capture residuals and seams, and route correction proposals into the owning documents. Use when a concern's operation digests outcomes, residuals, or contradictions back into the System of Record.
---

# Feedback Domain Skill

Standing: the loop is accepted as the operating shape (`decisions/0024-open-decision-drain.md`,
O13) and read through `decisions/0023-acceptance-not-approval.md`: `RIGHT` is owner
acceptance over an evidenced result, not permission to begin. The implementation is a
skeleton.

Feedback closes the loop by landing what was learned in the documents that
own it. It creates no side ledger.

## Duties

1. Review standing honestly: what is `OPEN`, `BUILT`, `WITNESSED`,
   `RATIFIED`, and on what evidence. Never advance standing by summary.
2. Record residual failures, contradictions, and deliberate ambiguities in
   `OPEN-SEAMS.md`; an implementation must not choose a side silently.
3. Route policy-shaped learnings into `decisions/` as proposals and standing
   changes into `STATUS.yaml`; link, do not duplicate, per the
   System-of-Record rule in `AGENTS.md`.
4. Convert confirmed Red findings into permanent defeating fixtures in the
   conformance corpus, so a found defeat can never recur silently.
5. Produce handoffs per `AGENTS.md` context hygiene: current standing,
   changed files, observed checks, residuals, next bounded operation.

## Refusals

Refuse to soften residuals, to close a seam without owner judgement, to
create a competing status ledger, and to treat recency, repetition, or
consensus as authority.
