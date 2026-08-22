# 0008 · Classification contract

Status: `PROPOSED · OWNER RATIFICATION PENDING`

## Decision

Adopt `CLASSIFICATION.md` as the single proposed vocabulary for architectural
scale, execution roles, information roles, standing, interfaces, and deployment
choices.

Use `Service` for a bounded executable enterprise capability and `Component`
for its replaceable internal mechanisms. Treat deployment mechanisms as
orthogonal to semantic identity. Retire metaphorical subsystem terminology from
canonical documents while leaving historical evidence byte-identical.

## Evidence

- `lineage/evidence/core/ANCHOR.md` A1 and A8
- `lineage/evidence/core/SUBSTRATE.md` V1-V5 and R1-R6
- `lineage/evidence/core/PRD-PRODUCT(1).md` §§2b, 3, 8, 11
- `lineage/evidence/core/PRODUCT(1).md` §§1 and 5
- `lineage/evidence/core/GLOSSARY(20260822-185710).md`, explicitly unratified

## Consequence

The Asset Service and Proofing Service are sibling services inside a local
Soveraeign Node. The Proofing Service references exact Asset Service versions;
neither may create a separate authority island or silently promote a projection
to authoritative state.
