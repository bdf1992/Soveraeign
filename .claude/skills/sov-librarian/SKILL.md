---
name: sov-librarian
description: Curate the asset library - declare collection types, open typed collections, file and unfile assets, and report conformance of every member against the schema its type declares. Load when the task mentions "sov-librarian", "librarian", "asset library", "collection type", "asset collection", "typed collection", "file an asset", "organize assets", "DAM", "metadata schema", "controlled vocabulary", "unfiled assets", "library conformance", or names organization.py, librarian.py, or the asset CLI commands declare-type, declare-collection, add-member, remove-member, conformance. Not for the Asset Projection Service retrieval collections, the root conformance oracle, or asset capture and derivation - those are sov-projection, sov-conformance, and sov-asset.
---

## Purpose

Hold the asset library to its own declared schema. The librarian curates and
reports; it settles nothing. Its work is filing assets correctly, recording the
metadata a type requires, and producing a report an operator can act on.

## What exists

Six declared operations on the Asset Service
(`services/asset/contracts/service.json`), all `RECORD_LOCAL`:

| Operation | CLI | Grant |
| --- | --- | --- |
| `declare-collection-type` | `declare-type` | `declare:collection-type` |
| `declare-collection` | `declare-collection` | `declare:asset-collection` |
| `add-member` | `add-member` | `organize:asset` |
| `remove-member` | `remove-member` | `retract:record` |
| `read-collection` | `collection` | `read:asset-collection` |
| `read-library-conformance` | `conformance` | `read:asset-collection` |

Run them through `python -m soveraeign_asset_service.cli --root <state> <command>`
from `services/asset/src`, or in process through `service.organization` and
`service.librarian`. A refusal exits 2 and prints its declared code.

## The three verdicts, which are the whole point

- `CONFORMING` - a **ratified** description carries the required field with a
  permitted value.
- `CLAIMED_UNRATIFIED` - somebody recorded the field and nobody ratified it.
  The metadata exists as a claim and is not conformance.
- `MISSING_FIELD` - nothing in the record carries it.

Never report the second as the first, and never describe a library as clean
because its claims are complete. `VOCABULARY_REFUSED`, `MEMBER_KIND_REFUSED`,
`EMPTY_COLLECTION`, and `UNFILED` are the other four defects.

## Owns / Must not

Owns: `organization.py`, `librarian.py`, their tests, the six declared
operations, and the collection types this node declares.

Must not:

- **ratify its own descriptions.** A librarian records a description under
  `propose:description`; `ratify:judgement` is Bdo's. A model that ratified its
  own metadata would make `CLAIMED_UNRATIFIED` a formality
  (`decisions/0063-asset-collections-and-the-librarian.md`, Ruling 3).
- **invent a value outside a declared vocabulary.** An asset whose real state
  the vocabulary cannot express is a finding against the type, not a licence to
  widen it. Say so; do not pick the nearest permitted value.
- **widen a type to make members pass.** That is the oracle-weakening refusal in
  `AGENTS.md`, Implementation order, applied to schemas.
- **file an asset to clear an `UNFILED` finding.** An asset belongs in a
  collection because it belongs there. An empty collection full of strays is a
  worse report than an honest pile.
- **touch the Asset Projection Service.** Its `declare-collection` builds an
  index and is a different record (seam S22).

## Working a library

1. Read the current state: `conformance --markdown`. Do not plan against a
   report you did not just run.
2. Take the largest verdict class first. `MISSING_FIELD` across many members
   usually means one describe pass; `VOCABULARY_REFUSED` across many usually
   means the type is wrong, and that is a finding for the owner, not a fix.
3. Record descriptions with `service.propose(asset_id, actor, payload)`. Leave
   them unratified and say in the report how many are waiting.
4. Re-run the report and quote the before and after counts.
5. Report `defects`, `counts`, and the unfiled list verbatim. A librarian's
   summary is checkable against the same command the reader can run.

## Standing and blockers

The implementation is `BUILT` and self-tested; `decisions/0057` is `PROPOSED`.
A run here establishes `BUILT` evidence only. Independent witnessing comes from
`sov-witness` or `sov-qa`, never from the participant that filed the assets.

Nothing in this domain waits on Bdo except ratifying descriptions and settling
seam S22 (two records named collection). Neither blocks curation or reporting.
