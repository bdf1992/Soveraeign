# 0077 · An asset is a pointer with parts, and its parts are versioned

Status: `OWNER-DIRECTED · PROPOSED`

## Decision

Bdo directed on 2026-08-26 that the Asset be specified, and named three
requirements in the same session: file version, content-addressable version
chunks, and a diff between two versions of one asset.

`SPEC.md` gains six Information objects — `Asset`, `AssetType`, `AssetVersion`,
`AssetPart`, `AssetPartVersion`, `AssetVersionDiff` — and one `Operation
granularity` subsection under Interface parity. `CLASSIFICATION.md` gains four
vocabulary rows: chunk, asset type, asset part, asset part version. Nothing was
built, no operation became reachable, and no standing moved.

## What was missing

`SPEC.md` declared fourteen Information objects and none of them was the Asset.
The word did not occur in the file. The central object of the Asset Service was
defined only in the `CLASSIFICATION.md` vocabulary table and in Python, so no
conformance case had a checkable statement to grade a participant against.

A search of the tracked repository returned zero occurrences of `asset type`,
`typed asset`, `asset kind`, `composite asset`, and `multi-file`. The only
typing that existed was `collection-type`, which types a collection; an asset
was typed transitively, by being filed into one.

## Ruling 1 — an asset holds no bytes

An asset is a governed identity. Every byte it carries is reached through a part
version, and a part version's bytes are reached through addressed chunks. This
restates what `CLASSIFICATION.md` already settled — "an asset is not its
payload" — at the level where a fixture can defeat it.

The chunk count and the entry count are each unbounded at one. A version
carrying one part and a version carrying a thousand are the same object, and no
transition may assume a single payload. How bytes are divided into chunks is a
storage choice this specification does not make, because `SPEC.md` is
stack-neutral by its own header.

## Ruling 2 — a part identity is separate from the path that names it

`AssetPart` carries identity; `part_path` is a label on the version entry and
may differ between two versions of the same part. A part identity therefore
survives a rename, and a rename is not a removal plus an addition.

This is what the diff requires. `MOVED` and `CHANGED` are distinguishable from
`ADDED` and `REMOVED` only because identity is not the path, and a diff that
reports a rename as a removal plus an addition is wrong rather than coarse.

It also repairs an undeclared equivalence. `CONTRACT.md` C10 permits identity
and address to share a value only under an intentional declared equivalence.
The current implementation resolves asset identity by file locator, which is
that equivalence, undeclared.

Bdo ruled the resolution on 2026-08-26: a plain rename is decided, and only a
rename combined with an edit is uncertain. Resolution is exact when the captured
bytes match exactly one part version the asset already holds, whatever path they
arrived under, and nobody is asked. Where several parts carry identical bytes an
unchanged path settles which. Only when the path and the bytes both changed, or
when neither match is unique, is resolution inexact - and an inexact resolution
takes a declared default, records its evidence, never blocks the operation, and
is overridden by a counter-record rather than by a question. `AssetVersionDiff`
carries this on the change: `MOVED_AND_CHANGED` is the only kind that may report
`resolution: DEFAULTED`.

## Ruling 3 — one act over many subjects is one operation

An operation's subject count is not bounded at one. One declared act over four
hundred subjects is one plan, one authority check, and one terminal receipt
carrying four hundred emitted record addresses. An interface requiring a
separate confirmation per subject for a single declared act has not met parity,
whichever binding it serves, and a model given one instruction is held to the
same rule as a human working one surface.

The kernel already admitted this shape: `OperationPlan`, `EventEnvelope`, and
`Receipt` all carry plural inputs and outputs. Nothing was added to the
transition contract.

## What the current implementation does against these rulings

Thirteen predicates were probed against the running participant rather than
read off the source. Four pass, five fail, four name a concept the code does not
have:

| Verdict | Predicate |
| --- | --- |
| PASS | identity never follows bytes; a change makes a new version with the predecessor resolvable; a tampered payload is refused before serving; shared custody is not shared identity |
| FAIL | bytes only via a part version; a type is never inferred from a suffix; the entry count is not bounded at one; a part identity survives a rename; the chunk count is not bounded at one |
| ABSENT | an undeclared type is refused; redeclaring a type is refused; a version is judged against its type; a diff between two versions |

The rename failure is demonstrated, not inferred: ingesting a file, renaming it
on disk, and ingesting again yields two asset identities.

## Effect class and rollback

`RECORD_LOCAL`. Two governing documents and nine declared diagram source pins.
`git checkout SPEC.md CLASSIFICATION.md diagrams/` reverses it completely. No
code changed and no participant behaviour changed, so nothing can have consumed
a resource or reached the outside world on the strength of it.

## What would defeat this

- An asset type for which a plain rename genuinely should mint a new part rather
  than move the existing one. Ruling 2 would then have to be type-dependent
  rather than uniform.
- A corpus in which unique-digest resolution is wrong often enough that the
  default costs more than a prompt would. The measured duplicate rates on this
  node argue the other way - 173,467 byte-identical files on one directory
  tree - but that is an argument about scale, not about correctness.
- Measured evidence that chunk addressing costs more than it saves at the scale
  this node actually holds. `ENGINEERING.md` forbids generalized infrastructure
  for imagined scale, and the chunk layer is the part of this record most
  exposed to that rule.
- A partial-result semantic that a plan-level declaration cannot express, which
  would mean Ruling 3 needs a new terminal outcome rather than a plan field.

## Defaults taken

- Part identity was made separate from part path. Merging them is simpler and
  makes the diff unable to distinguish a rename, which is the requirement.
- The chunking algorithm is unspecified. Naming one would put a storage choice
  in a stack-neutral document.
- `AssetVersionDiff` is declared a projection, not a record, under the existing
  Projection rule. Storing a diff would create a value that goes stale the
  moment either version is superseded.
- No kernel transitions were added. `decisions/0063` introduced collection
  records with no `kernel_transition` at all, and that precedent was followed
  rather than widening the kernel grammar.
- Rename resolution is an act under a capability grant, reversible by
  counter-record, not a judgement. `decisions/0063` refused to route filing
  through ratification because two hundred filings would mint two hundred
  judgement claims; four hundred moved files have the same shape.

## Residuals

- `OperationPlan` carries no field declaring what a partial result means, so a
  multi-subject plan cannot state its own terms. `refusal_behavior` is already a
  structured object in `contracts/operation-plan.schema.json` and overloading it
  would break that schema. Repairing this crosses into the contracts boundary
  and is a separate concern.
- `services/asset/src/soveraeign_asset_service/identity.py` resolves identity by
  locator and contradicts Ruling 2. It is unrepaired.
- No service operation is declared in `services/asset/contracts/service.json`
  for any of the six objects, so none is reachable through any binding.
- The `SPEC.md` traceability table gained no row. The existing rows cite
  `SUBSTRATE` and `ANCHOR` clauses in `lineage/`, and inventing a citation for
  asset identity would be a fabricated ground.

## Standing

`PROPOSED`. Bdo has not ruled. The objects inherit the `PROPOSED` standing
`SPEC.md` already carries; no entry in `STATUS.yaml` moved.
