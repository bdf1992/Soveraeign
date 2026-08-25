# The ground under the console surface

A draft to cut up, not a plan to approve. It says what objects actually exist in
this node, what each primitive would have to do, and which of them have real
ground and which are a name with nothing under it. Read 2026-08-24 off the eight
service manifests and the working tree; where a claim is the repository's rather
than something checked here, it says so.

Nothing is designed yet. That is deliberate — the previous attempt dressed a
page without an object model and was refused.

## What is actually there

Eight services, 102 declared operations, 34 with an implementation.

| Service | Standing | Built | Objects it owns |
| --- | --- | --- | --- |
| `asset` | BUILT | 11 of 11 | asset, asset-version, payload-custody, asset-relationship, asset-use-record |
| `record` | BUILT | 8 of 8 | journal-entry, terminal-receipt, counter-record, digest-chain, subject-projection |
| `console` | BUILT | 15 of 26 | channel, thread, post, operator-session, authority-grant, publication — plus notification, judgement-request, operator-setting, console-receipt, projection-view, all proposed |
| `gateway` | PROPOSED | 0 of 9 | gateway-request, capability-resolution, authority-check, routing-record, transport-binding |
| `projection` | PROPOSED | 0 of 16 | projection-collection, text/vector/graph configuration, context-package, retrieval-receipt |
| `registry` | PROPOSED | 0 of 13 | registry-entry, owner-record, entry-relation, resolution, drift-finding |
| `observation` | PROPOSED | 0 of 8 | observation, observation-request, predicate-declaration, relation-inference |
| `proofing` | PROPOSED | 0 of 11 | proofing-session, review-round, version-pinned-annotation, decision-proposal |

Three services can be driven today. Five are contracts with nothing behind
them, so a surface over one of those is a surface over a promise.

## The primitives

In the order you named them. "Ground" is what exists to build on; "missing" is
what has to be decided or written before a surface can be honest.

### File lists and browsers

Listing assets with their versions, custody and use record; opening one.

- Ground: `asset` is fully built. `read-asset`, `read-version`,
  `read-version-history`, `read-use-record`, `read-shared-custody`, and a
  rebuildable search projection in `projections.py`.
- Missing: no list operation. Every read is by identifier, so a browser has
  nothing to enumerate from except the projection, which is derived and says so.
- Decides: whether "list" is an asset-service operation or a projection read.

### Thumbnail generation

- Ground: none. `custody.py` records a `mime` per payload and nothing else
  reads it.
- Missing: everything — derivation, storage, cache invalidation on new version.
  `request-derivative` exists and is built, which is the shape a thumbnail
  would take: a derived asset with lineage back to its source, not a cache.
- Decides: whether a thumbnail is an asset (with a version and a receipt) or a
  projection (rebuildable, never authoritative). The whole difference in cost.

### File injection

- Ground: `ingest-asset`, built, content-addressed, with a receipt.
- Missing: the surface. Drag-and-drop, paste, folder-at-a-time, and what
  happens when the same bytes arrive twice (the store is content-addressed, so
  it is the same asset — the surface has to say that rather than look broken).

### Document viewers

- Ground: bytes come back from `read-asset`. Nothing interprets them.
- Missing: the whole viewer layer, and the decision about which types get one.
- Decides: how many types. One viewer per type is a large surface; a fallback
  that shows the digest and offers download is small and honest.

### Automation screens

- Ground: `.claude/schedules/` holds six declarations and `sov_schedule.py`
  runs a tick. All six are `enabled: false` and nothing is registered with
  Windows.
- Missing: this is harness plumbing, not a service. It holds no standing and
  writes to `.local/schedules/ledger.ndjson`, not the journal.
- Decides: whether automation becomes a service with records, or stays harness
  and the surface is honest that it is showing a side file.

### Workflow scheduler

Same ground as above. The distinction worth keeping: a *schedule* says when, a
*workflow* says what. Today only the first exists as a declaration.

### Channel creation and browsing

- Ground: `open-channel` is built. `list-channels` is declared and proposed.
- Missing: enumeration, again. The experiment surface reads channels out of a
  rebuilt projection rather than asking the service, because the service has no
  answer yet.

### Post authorship and discovery

- Ground: `post` is built — content-addressed bytes, the journal keeps the
  address. `read-thread` is built.
- Missing: discovery entirely. No search over posts, no cross-thread read, no
  mentions index. `projection` service would own it and has nothing built.

### Thread tools

- Ground: `open-thread`, `archive-thread`, `publish-thread`,
  `withdraw-publication`, all built. A thread can be pinned to an exact address
  and digest.
- Missing: everything between opening and archiving — no move, no merge, no
  split, no rename, no reopen.

### Session interaction

- Ground: `open-session`, `close-session`, `session-context` built. A closed
  session leaves a read position, which is what continuity reads from.
- Missing: nothing structural. This is the most complete object in the node and
  has the least surface.

### SOV integration

- Ground: `bindings/sov/profile.json` validates with positive and defeating
  fixtures. `SOV.md` and `.claude/agents/sov.md` load it.
- Missing: no live activation. The profile is an accepted shape, not a running
  thing, so a surface showing "Sov" today is showing a document.

### BYOM support

- Ground: `contracts/model-binding.schema.json`, `adapters/ollama/`.
- Missing: `invoke_model` has no kernel implementation (PROD-I-9). The Ollama
  adapter grades declared bindings against a recorded inventory; it does not
  execute a model. A surface that offers to run one would be lying.

## The objects, and their states

Only the built ones have states worth designing against.

| Object | States | Verbs that exist |
| --- | --- | --- |
| asset | version history; retracted by counter-record | ingest, read, request-derivative, propose-description, ratify-proposal, retract |
| asset-version | supersedes the previous; never rewritten | read, read-history |
| channel | open (no close operation exists) | open |
| thread | OPEN, ARCHIVED; published or not | open, archive, publish, withdraw |
| post | RECORDED, always; addressed by digest | post, read-thread |
| operator-session | OPEN, CLOSED; closed carries a read cursor | open, close, read context |
| authority-grant | live, revoked | grant, revoke, list |
| journal-entry | appended, never amended; chained by digest | append, reconstruct, counter |

Everything a console record can be is `RECORDED`. Nothing on this surface
climbs above it, which means no surface here can show approval, admission or
ratification as a state — only as a post that says so.

## What is yours, not mine

- **Custom node setup.** What a node is configured *with* has no record type
  anywhere. `operator-setting` is proposed with one operation and no schema.
- **Integration cards.** I do not know what a card is to you: a live status
  tile per service, a connector you configure, or a launcher.
- **Inline human gestures.** Named but undefined. The nearest built thing is
  the answer bar in the console experiment, which is one gesture (post) in one
  place.
- **How much of the proposed half to surface at all.** Five services are
  contracts with no implementation. A surface can show them as chartered and
  empty, or not show them until they run. That choice sets the size of
  everything above.

## What this draft does not do

No layout, no components, no type. Those come after the objects and their
states are settled, not before — which was the previous attempt's mistake.
