# Witnessing from inside the builder's lineage is admissible only as a crossing check

Status: PROPOSED · transcribed from a verbal ruling by Bdo, 2026-08-26.
The ruling is Bdo's; this wording is a transcription by the campaign
coordination session and is not accepted until Bdo accepts it.

## Question

Raised by `reports/2026-08-26-bravo-kernel-walk.md` (branch
`feat/work-coordination-kernel-participant`): can a subagent of a builder's
session ever witness that session's build, given that
`services/observation/contracts/relation-inference.schema.json` grades
same-session lineage `DIRECT`?

## Ruling as transcribed

A witness that descends from the builder's session may witness only what is
mechanically evident from the system and its tooling: a crossing check that
any fresh participant can re-derive from the records alone — digests,
receipts, kernel-evaluator request/verdict pairs, git objects, and store
contents, using the exact commands the observation names.

A claim whose confirmation requires the builder's interpretation, intent, or
narrative cannot be witnessed from inside the builder's lineage. For such a
claim, `DIRECT` relation disqualifies the observer, and the claim waits for
an observer outside the builder's session.

## Consequences

- `DIRECT` relation stops being a blanket disqualifier and becomes a
  claim-type gate: mechanical re-derivation admissible, judgement-type
  observation refused.
- An observation offered under this ruling must carry the exact commands and
  inputs that reproduce it, or it is not a crossing check and the ruling does
  not apply to it.
- Applied to the BRAVO walk: the digest, byte-identity, refusal-reproduction,
  and absence claims are crossing checks and were re-derived by a
  builder-descended witness; the walk's standing beyond `BUILT` still waits
  on the standing owner recording it, and an outside-session observation
  (commander ECHO's, in flight) strengthens it regardless.

## What would defeat this ruling

- A case in which a claimed crossing check smuggles builder judgement — for
  example, the check's evaluator or fixtures are themselves the builder's
  unreviewed work, so re-derivation reproduces the builder's assumption
  rather than testing it.
- A `DIRECT`-lineage observation whose named commands an outside participant
  cannot in fact reproduce.

## Residual

How this maps into the Observation Service contract — whether
`relation-inference` output should carry a claim-type field so `DIRECT` plus
crossing-check grades admissible mechanically — is contracts work owned by
the Observation concern, not settled here.
