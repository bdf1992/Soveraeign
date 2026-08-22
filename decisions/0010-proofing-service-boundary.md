# 0010 · Proofing Service boundary

Status: `PROPOSED · OWNER RATIFICATION PENDING`

## Decision

Define Proofing as a sibling service integrated with the Asset Service through
exact asset-version references and shared-kernel transitions. The Proofing
Service owns review sessions and decision history; the Asset Service owns asset
identity, payload custody, versions, and derivation lineage.

## Evidence

- `CLASSIFICATION.md`
- `CONTRACT.md` C1-C10
- `PRD.md` PROD-I-2 through PROD-I-5 and the two-binding proof
- `services/asset/CHARTER.md`
- `lineage/evidence/core/SUBSTRATE.md` V1, R1, R3-R6

## Open authority

The source corpus establishes shared-system and service constraints but does not
ratify Proofing as the second service. That product-boundary choice remains
Bdo's judgement.
