# Proofing Service Charter

Status: `RULED_SECOND_BOUNDARY_O11_CHARTERED_NOT_IMPLEMENTED` — the boundary exists; no Proofing Service operation is implemented.

## Role

The Proofing Service is a sibling of the Asset Service inside a local
Soveraeign Node. It governs the review-and-approval lifecycle for exact asset
versions. It does not own asset payload custody and does not create an
independent source of asset truth.

## Owned domain records

- proofing session;
- review round;
- participant assignment and required authority;
- version-pinned annotation;
- comparison request and comparison recording;
- requested change;
- approval or rejection proposal;
- authorized decision;
- proofing receipt and history.

Proposed initial lifecycle:

```text
OPEN → IN_REVIEW → DECISION_PENDING → CLOSED
```

This lifecycle is service policy awaiting owner ratification. It does not
replace the shared `RECORDED`, `ADMITTED`, `RATIFIED`, and `EFFECTIVE`
standing distinctions.

## Asset Service integration

The Proofing Service:

1. opens a proofing session against an immutable `asset_id` + `version_id`;
2. resolves bytes and technical provenance from the Asset Service;
3. stores annotations against that exact version and a declared coordinate
   scheme;
4. asks the Asset Service for comparison or display derivatives through a
   declared operation rather than direct storage writes;
5. emits decisions and receipts through the shared kernel;
6. requests a revised asset version through the Asset Service when changes are
   required;
7. marks earlier annotations stale or carried when a new version enters;
8. never rewrites an annotation as if it had been made against another version.

The Asset Service remains authoritative for asset identity, payloads, versions,
and derivation lineage. The Proofing Service remains authoritative for proofing
sessions, rounds, annotations, and decision history. The local node's shared
record and kernel prevent either service from becoming an authority island.

## Human and model participation

Humans and models operate the same proofing session through different bindings:

- a model may locate versions, compare representations, and propose findings;
- a human may do the same and may ratify judgement when holding the required
  authority;
- machine verification authority may settle checkable properties but cannot
  ratify aesthetic, business, or customer judgement;
- every proposal, refusal, decision, and operation returns a receipt;
- a worker's render or comparison report is not independent observation.

## Current implementation boundary

The Proofing Service is not implemented. The lifecycle and integration rules above define the boundary; the cases below remain defeating constraints and grant no built standing.

## Defeating cases

- proofing silently reviews “latest” instead of an exact version;
- an annotation moves to a new version without a declared carry operation;
- a model ratifies judgement-typed approval;
- a render worker's success report settles the comparison;
- approval mutates Asset Service storage directly;
- rejection erases the reviewed version or prior decision;
- a projection or external proofing integration becomes authoritative;
- a missing external renderer is reported as success instead of refusal or
  `UNATTESTABLE`.

## Deferred

Customer invitations, email delivery, public share links, real-time cursors,
external-world notifications, production media rendering, and federation are not implemented in current standing. Any declared interfaces remain inactive, and their effects must remain refused or isolated until separately admitted.
