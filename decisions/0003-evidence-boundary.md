# 0003 · Evidence boundary

Status: `PROPOSED FOR BDO RATIFICATION`

## Decision

Preserve the supplied core definition and product documents byte-for-byte under
`lineage/evidence/core/`. Treat them as attributed evidence rather than the
canonical layer. Retain digests for the larger census and collection-method
inputs in `lineage/EXTERNAL-SOURCES.lock` without making those derived files
part of the initial repository.

## Rules

- `lineage/SOURCES.lock` identifies every preserved source by SHA-256.
- Corrections to historical material are new records, never in-place edits.
- Canonical claims cite a source and standing or declare themselves proposals.
- A missing cited dependency makes the dependent claim unattestable.
- Large derived census files and collection prompts remain in the founding
  packet and are addressable by digest; they do not become repository law or
  runtime fixtures by presence alone.

## Why

This lets the project honor its history without importing every historical
assumption as current law.
