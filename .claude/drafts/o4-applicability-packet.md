# O4 packet · reproduction versus applicability

Status: `PROPOSED · OWNER JUDGEMENT PENDING`

What open decision O4 must resolve before a staleness system can report more than "the source
moved", assembled for Bdo with observed evidence from 2026-08-23. This is a worker proposal.
It frames the question and its consequences; it does not answer it, and it witnesses nothing
it cites (`AGENTS.md` Authority).

## Owned scope

Owned: the O4 question verbatim, the seam it derives from, the sub-questions a sufficient
answer must close, one dated observation of the failure mode, and the consequences each
option directly entails. Not owned: the answer; any edit to `STATUS.yaml`, `OPEN-SEAMS.md`, or
`SPEC.md`; the attestation schema O4 blocks; and any judgement on O1 to O3 or O5 onward.

## The question

`STATUS.yaml`, verbatim, carrying `blocks: attestation_schema`:

> How are historical reproduction and present applicability represented separately?

Its seam, `OPEN-SEAMS.md` S2 · Reproduction versus applicability:

> An attestation needs enough stable input to reproduce a historical run while also
> representing whether the claim applies to current source state. These are not one predicate
> and may need separate outcomes or linked attestations.

## Why it now blocks more than attestation

O4 was registered against the attestation schema. The same predicate split governs every
derived artifact in the repository — diagrams, reports, projections, recordings — because all
of them are `LOSSY` readings that can outlive the source they read.

A digest comparison answers *reproduction*: these exact bytes produced this exact artifact.
It cannot answer *applicability*: whether the artifact's claims still hold. Building a
staleness system on digest alone ships an alarm that means one thing while reading as though
it means the other.

## Observed failure mode

`diagrams/` implements the digest half by hand today. Each view records a `source_digest` per
source, and `diagrams/README.md` states the intent: "a stale diagram is detectable rather than
merely suspected."

Run against current bytes on 2026-08-23, after one merge changed `CLASSIFICATION.md` and
`STATUS.yaml`:

```text
authority-typing.md         STALE  STATUS.yaml
event-outcomes.md           STALE  CLASSIFICATION.md
requirement-lifecycle.md    STALE  STATUS.yaml
service-map.md              STALE  CLASSIFICATION.md, STATUS.yaml
source-reader-recording.md  ok
standing-transition.md      STALE  CLASSIFICATION.md
```

Four flagged. Inspected individually:

- `service-map.md` is genuinely wrong — it renders Console as `chartered, not built — O14`,
  and the merge renumbered Console to O18.
- `standing-transition.md` reads `CLASSIFICATION.md` for the standing chain
  `RECORDED → ADMITTED → RATIFIED → EFFECTIVE`. The changed paragraph concerned the
  Asset/Proofing/Console service split. The diagram is flagged and correct.

The mechanism is not broken: `CONTRACT.md`, `SPEC.md`, and `PRD.md` digests all still match,
so this is real drift detection. The defect is that reproduction failure is being reported as
if it were applicability failure. An alarm with that ratio of false positives is one operators
learn to clear without reading, which is worse than no alarm.

## What a sufficient answer must close

Five sub-questions. An answer that leaves any of them open does not unblock the schema.

**1 · One record with two outcomes, or two linked records?** S2 admits either. One record with
`reproduction` and `applicability` fields keeps a single addressable object. Two linked records
lets applicability be re-asserted over time against one fixed reproduction, at the cost of a
resolution path between them.

**2 · What establishes applicability?** Reproduction has a mechanical test. Applicability has
no proposed one. Candidates: a declared dependency on named regions of a source rather than
the whole file; a re-derivation compared against the stored artifact; or an explicit assertion
by an operator holding the right authority type.

**3 · What authority type may assert it?** `PRD.md` PROD-I-5 splits `VERIFICATION` from
`JUDGEMENT`. Reproduction is verification-typed — a machine may settle it. If applicability is
judgement-typed, no machine may ever mark a drifted artifact "still applies", and every source
change queues a pending human right. If it is verification-typed, the mechanical test from
sub-question 2 must exist first. This is the sub-question with the largest operational cost
either way.

**4 · What is the default when applicability is unknown?** `SPEC.md` gives attestation
`UNATTESTABLE` for this position, and `OPEN-SEAMS.md` S4 records that the conditions,
visibility, expiration, and consequences of unattestable effectiveness remain unspecified.
A derived artifact needs the equivalent, and whether it may still be read while in that state.

**5 · At what granularity does a source declare its parts?** The observed failure is
whole-file granularity. Region-level dependency would have flagged only `service-map.md`, but
requires sources to carry addressable, stable regions — which no governing document currently
provides, and which changes what `source_address` must resolve.

## Consequences of deferring

Deferring is a position, not a non-answer. Its direct entailments:

- the `read_source` and `Recording` slice can still ship, reporting reproduction only, if the
  refusal vocabulary says so explicitly rather than implying applicability;
- `diagrams/` staleness stays a manual read, and `diagrams/README.md`'s deferral of the check
  to `scripts/lint.py` stays deferred;
- `PROD-I-8` joint sign remains unbuildable, since attestation needs the split O4 defines;
- four views stay flagged with no way to record that three of them are fine.

## Not decided here

This packet takes no position on any of the five sub-questions, proposes no schema, and
changes no standing. O4 remains open and owner-held.
