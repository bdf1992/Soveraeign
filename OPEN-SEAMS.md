# Open Seams

These seams are carried deliberately. An implementation must not choose a side
silently.

## S1 · Corpus revision alignment

`HANDOFF-SPEC.md` and introductory text in `SEAM-REGISTER.md` refer to earlier
PRD revisions, while the evidence corpus contains a rev-6 Phase-I amendment and
PROD-I-8. Canonical references must be rechecked against the exact source
digests before freeze.

## S2 · Reproduction versus applicability

An attestation needs enough stable input to reproduce a historical run while
also representing whether the claim applies to current source state. These are
not one predicate and may need separate outcomes or linked attestations.

## S3 · Authority in the Gauge

The existing Gauge emphasizes reachability, commitment, provenance, and
retraction. It can still describe a reachable and traceable surface whose
authority is unsafe. Governance must influence the verdict without becoming a
confidence score or merging evidence with authority.

## S4 · Unattestable effectiveness

The seam register allows non-executable ratified claims to become effective on
their hands while marked unattestable. The exact conditions, visibility,
expiration, and operational consequences remain unspecified.

## S5 · Cold-start semantics

Structural completeness and schema validity are measurable but do not establish
semantic competence. Phase I needs a watched task whose success a fresh witness
can determine independently.

## S6 · Correction measurement

Some source language calls for a correction rate while the current spec records
a count. The denominator, interval, and interpretation must be fixed before the
metric can govern a gate.

## S7 · Definition and Gauge operator bindings

Earlier subsystem proposals describe Claude-left/Bdo-right behavior directly. They must be
re-derived through typed hands, machine verification, owner judgement, and
runtime attestation so a named model or person is not hardcoded into the law.

## S8 · Evidence portability

The corpus is readable but some cited raw finds, reviews, and conformance seeds
are not present as individual source files. Missing sources must be recovered,
or dependent claims must be marked unverifiable rather than silently trusted.

## S9 · External effects

Record-local retraction is defined. Irreversible resource consumption and
external-world mutation need explicit Phase-I refusal/isolation rules. World
rollback or compensation remains later work.

## S10 · Product boundary

The system is currently described as an enterprise operating environment. The
boundary between a primary enterprise application and a constitutional runtime
over existing applications must be tested through the first real subsystem rather
than decided by metaphor alone.

## S11 · Red-lane inputs — closed 2026-08-23

`SDLC.md` rule 6 said Red operators receive the contract, the claimed
invariants, and the built artifact, not the builder's tests, plan, or
assumptions, while `.github/workflows/qa-lanes.yml` handed the Red action the
whole pull-request diff. Bdo chose the independent-verification reading: the
builder's tests are part of the artifact under attack, readable and never the
oracle. `SDLC.md` rule 6 now says so; the workflow already did.

## S12 · Ratification mechanism

`decisions/0016` and `.github/CODEOWNERS` say ratification enters the
repository through code-owner review on `STATUS.yaml`, `decisions/`, and the
governing set. `AGENTS.md` requires a typed, scoped, live grant at the
operation boundary and says only Bdo ratifies judgement. Whether a CODEOWNERS
approval is that grant, or an explicit recorded decision is required, is
unsettled; 0016 is still `PROPOSED`.

Owner input, 2026-08-23: Bdo will rarely interact with GitHub directly, so a
code-owner review click cannot be the owner's ratification surface. The
surface has to be a Human Binding the owner actually uses; the Console
Service charter (`services/console/CHARTER.md`, judgement requests) is the
chartered home for it. 0016's mechanism stands as a proposal until a decision
amends it. This seam stays open on the mechanism, not on the direction.

## S13 · Retraction in the Soveraeign bar

`AI-NATIVE.md` requires `FULL` on reachability, commitment, provenance, and
the admitted effect envelope for `SOVERAEIGN_QUALIFIED`, and omits retraction,
while the same document and `decisions/0006` call it "the all-`FULL`
Soveraeign bar". Whether retraction must be `FULL` within the phase's effect
envelope is a tightening only the owner can make.
