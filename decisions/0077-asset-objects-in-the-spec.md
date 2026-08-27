# 0077 · An asset is a governed identity, and a file is not one

Status: `OWNER-DIRECTED · PROPOSED`

## Decision

Bdo directed on 2026-08-26 that the Asset be specified, and named the
requirements over two correction passes: constituents carry their own version
history, storage form must not reach the asset contract, a diff between two
versions must distinguish a rename from a delete-plus-add, and file-shaped facts
must not become asset facts.

`SPEC.md` gains six governed Information objects — `Asset`, `AssetType`,
`AssetVersion`, `AssetPart`, `AssetPartVersion`, `AssetVersionDiff` — plus
`SourceObservation` on the source plane, and one `Operation granularity`
subsection under Interface parity. `CLASSIFICATION.md` gains five vocabulary
terms and a note fixing what a part is and where custody sits.

Nothing was built. No operation became reachable through any binding, and no
standing entry moved.

## What was missing

`SPEC.md` declared fourteen Information objects and none of them was the Asset;
the word did not occur in the file. The central object of the Asset Service was
defined only in the `CLASSIFICATION.md` vocabulary table and in Python, so no
conformance case had a checkable statement to grade a participant against. A
search of the tracked repository returned zero occurrences of `asset type`,
`typed asset`, `composite asset` and `multi-file`; the only typing that existed
was `collection-type`, which types a collection, so an asset was typed
transitively by being filed into one.

## Ruling 1 — the asset layer is not the file layer

A fact belongs to the narrowest identity for which it stays true. Five planes
carry the distinctions the reference participant had collapsed:

| Plane | Answers |
| --- | --- |
| Governed | what the thing is and what constitutes its state |
| Representation | what kind of content state this is |
| Placement | where a constituent appears in one whole state |
| Source | where a thing was observed or obtained |
| Custody | where the exact bytes are |

A file is a representation and a placement, not an identity every asset must
hold. It earns first-class objects only when a file needs its own version
history, its own permissions, or its own participation in relationships, and
none of those is true today.

Metadata is not an object class. A metadata statement targets the narrowest
governed or observed subject for which it remains true, and governed
descriptions keep travelling through `submit_proposal` and `ratify` rather than
through a generic bag. No `AssetMetadata` object exists and none is proposed.

## Ruling 2 — an asset holds no bytes, and no count is bounded at one

Every byte an asset carries is reached through an `AssetPartVersion` and that
version's custody reference. An `AssetVersion` names which constituents it
contained, the exact content state of each, and where each was placed; the entry
count is not bounded at one and no transition may assume a single payload.

`payload_address` and `content_digest` are a custody reference and nothing more.
Whether that address resolves to a single blob, a manifest of chunks, or a later
content-addressed form is decided below this contract and never changes an asset
version. This is why chunking is absent from the objects: putting it there would
have made a storage decision able to mint a new governed state.

Placement belongs to the version entry and never to the part version. Where a
constituent sits is a fact about one composition, not about a content state, so
a rename produces a new asset version over the same part version — same part,
same content state, different composition state. Putting a path on the part
version instead would make a pure rename mint a new *content state* for content
that had not changed, contradicting that object's own definition.

## Ruling 3 — identity is never constituted by a path, a locator, or bytes

`AssetPart` is a constituent identity — the source, the printable, the
transcript — carrying `part_role`, the stable slot its `AssetType` declares. A
filename, a logical path, a locator and a source address are placement or
observation; none is identity (`CONTRACT.md` C10). A part identity is preserved
across a known rename.

Byte equality is not identity either. Two content states may legitimately hold
identical bytes, so an equal `payload_address` never establishes that two
entries are the same thing moving. Every `AssetVersionDiff` kind is therefore
decided by identity: `MOVED` is the same `part_version_id` under a different
placement, `CHANGED` a different `part_version_id` under the same placement.

Resolution binds captured bytes to a part as an attributed act, never a
derivation. A matching digest, an unchanged locator and a source observation are
evidence a resolution may cite. Where the evidence does not make one part
unique, resolution takes a declared default, records the evidence it used, never
blocks the operation, and never becomes a judgement claim; a counter-record
overrides it. `decisions/0063` refused to route filing through ratification
because two hundred filings would mint two hundred judgement claims, and four
hundred resolved parts have the same shape.

A source is provenance, not state. Many `SourceObservation` records may point at
one part version: the same bytes reached through a local path, an archive, an
object store and another asset's import are four observations of one content
state, not four content states. A source that moves, renames, disappears or
mutates changes no part version, no part and no asset.

A media type, a filename suffix and a magic-number reading are evidence an
`AssetType` declaration may cite. None is authority and none may stand in for a
declared type.

## Ruling 4 — one act over many subjects is one operation

An operation's subject count is not bounded at one. One declared act over four
hundred subjects is one plan, one authority check, and one terminal receipt
carrying four hundred emitted record addresses. An interface requiring a
separate confirmation per subject for a single declared act has not met parity,
whichever binding it serves, and a model given one instruction is held to the
same rule as a human working one surface.

The kernel already admitted this shape: `OperationPlan`, `EventEnvelope` and
`Receipt` all carry plural inputs and outputs. Nothing was added to the
transition contract.

## What the current implementation does against these rulings

Twenty invariants probed against the reference participant by execution and
record-shape inspection. Three verdicts, because contradiction and absence are
different facts:

- **HOLDS** — the code has what the invariant names and satisfies it.
- **CONTRADICTED** — the code has the concept and does the opposite. A defect.
- **ABSENT** — the concept does not exist, so there is nothing to contradict.

Six hold, six are contradicted, eight are absent.

| Verdict | Invariant | What was observed |
| --- | --- | --- |
| CONTRADICTED | an asset holds no payload of its own | the `versions` row carries digest, mime, size and `blob_path` directly, so an asset state *is* a payload rather than reaching one |
| CONTRADICTED | a version may reference more than one constituent | the row holds one digest and one `blob_path`; structurally singular, not merely unimplemented |
| CONTRADICTED | lineage and derivation are orthogonal | `role` is one exclusive value assigned `REVISION if held is not None else ORIGINAL`, so a derived version that also supersedes cannot say both |
| CONTRADICTED | a locator does not constitute identity | `identity.by_locator` resolves by file URI, so a rename minted a second identity. Tested at asset level; not a part-continuity test, because parts do not exist |
| CONTRADICTED | custody form is below the asset contract | the row stores `blob_path`, a filesystem path, while `store.py` already returns a portable `cas:sha256:` address the lifecycle never uses |
| CONTRADICTED | a source observation is provenance, never constitutive | the row carries a singular `source_id`, so a content state names exactly one origin and a second sighting of the same bytes cannot be recorded without minting another version |
| HOLDS | descriptive facts attach to the governed identity | propose/ratify records a title against the asset id, not against a payload |
| HOLDS | a media type is evidence, never authority | `mimetypes.guess_type` is stored and nothing reads it as authority |
| HOLDS | a change makes a new state, predecessor resolves | one identity, two states, the earlier payload still verifies |
| HOLDS | byte equality does not constitute identity | two identities over one stored payload |
| HOLDS | a content state resolves to a verifiable payload | read refused on digest mismatch, at version level |
| HOLDS | a shared payload is not a shared record | one stored payload, two independent records |
| ABSENT | an asset naming no declared type is refused | no asset carries a type |
| ABSENT | a type is declared before use; redeclaring refuses | no asset type exists |
| ABSENT | `content_digest` over the entry set | no entry set; the digest is of a single payload |
| ABSENT | a version is judged against its type when recorded | no type to judge against |
| ABSENT | a part is a constituent identity, not a file | no constituent layer at all |
| ABSENT | resolution is attributed and records its evidence | the locator lookup cites no evidence and records no default |
| ABSENT | placement belongs to the entry, not the content state | no entry and no placement; where a payload sits is the source locator, a different plane |
| ABSENT | a diff is derivable from entries and part identities | no diff, and nothing for one to read |

Meanwhile the participant passes all seventeen of its own identity tests. That
green is the point and it is trap T2 in the flesh: green means unchanged, not
correct.

## Effect class and rollback

`RECORD_LOCAL`. Two governing documents, one decision record, and the generated
projections that read them. Reverting this commit removes every object, every
vocabulary term and this record. No code changed and no participant behaviour
changed, so nothing can have consumed a resource or reached the outside world on
the strength of it.

## What would defeat this

- An asset type for which a plain rename genuinely should mint a new part rather
  than move the existing one. Ruling 3 would then have to be type-dependent
  rather than uniform.
- A real need for `File` as a governed identity — a file appearing in several
  assets, holding its own version history, or carrying permissions independent
  of its asset. Ruling 1 keeps `File` a representation only until one of those
  is true.
- A partial-result semantic a plan-level declaration cannot express, which would
  mean Ruling 4 needs a new terminal outcome rather than an `OperationPlan`
  field.
- Measured evidence that separating part from part version costs more than it
  saves at the scale this node holds. `ENGINEERING.md` forbids generalized
  infrastructure for imagined scale, and the constituent layer is the part of
  this most exposed to that rule.

## Defaults taken

- `part_role` rather than `part_key`, with `AssetType.spec` declaring
  `part_roles` so the slot is type-governed rather than free description.
- `placement` carries `logical_path` only. No separate `filename`: it is the
  last segment, and carrying both invites them to disagree.
- `SourceObservation` references `source_id` rather than restating a locator.
  `SPEC.md` already defines `Source` with `source_address`, and duplicating it
  would create the synonym `AGENTS.md` forbids.
- `ORIGINAL`, `REVISION` and `DERIVATIVE` survive as a derived read off
  `predecessor_version_id` and `derivation` rather than as a stored exclusive
  role. Collection types already admit assets by role, so deleting the words
  would break `decisions/0063`.
- No kernel transitions were added. `decisions/0063` introduced collection
  records with no `kernel_transition` at all, and that precedent was followed
  rather than widening the kernel grammar.
- The `Chunk` vocabulary term was not added to `CLASSIFICATION.md`. Chunking is
  custody, below this contract, and naming it as asset vocabulary is what this
  record exists to prevent.

## Residuals

- No independent witness. This session wrote the objects, wrote the probe and
  ran it, so this is `BUILT` and self-tested; the standing is capped below
  `WITNESSED`.
- No conformance fixture exists. `SPEC.md`'s own conformance boundary requires a
  positive and a defeating fixture per normative predicate, and those are owed
  before the oracle can grade any of this.
- No service operation is declared in `services/asset/contracts/service.json`
  for any object, so none is reachable through the CLI, the Gateway or MCP. The
  AI-native reachability score is unmoved.
- `OperationPlan` carries no field declaring what a partial result means.
  `refusal_behavior` is already a structured object in
  `contracts/operation-plan.schema.json` and overloading it would break that
  schema; repairing it crosses into the contracts boundary.
- Six contradictions are unrepaired. `identity.py`, which resolves identity by
  locator, is the first code change any of them implies.
- The `SPEC.md` traceability table gained no row. Existing rows cite `SUBSTRATE`
  and `ANCHOR` clauses in `lineage/`, and inventing a ground for asset identity
  would be fabricated.

## What still waits on Bdo

One judgement: whether these six governed objects are the asset he means.
`acceptance/A9.json` presents it, and rejecting it is a revert of one commit.

Nothing else here waits on him. The conformance fixtures, the repair of
`identity.py` against Ruling 3, and the five remaining contradictions are
reversible record-local work that proceeds without asking
(`decisions/0023-acceptance-not-approval.md`).

## Standing

`PROPOSED`. The objects inherit the `PROPOSED` standing `SPEC.md` already
carries. Nothing here is ratified and no `STATUS.yaml` entry moved.
