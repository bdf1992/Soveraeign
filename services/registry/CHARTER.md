# Registry Service Charter

Standing: `PROPOSED`. Chartered and contracted; nothing here is implemented.

## Role in Soveraeign

The Registry Service is the node's named place to look something up. Given a name it
returns what that name is, which document owns it, what standing it holds, and what it is
related to — for participants, operations and their logical endpoints, vocabulary terms,
documents, external systems, and the owner accountable for a domain.

Today that answer is smeared across at least eight hand-maintained tables: the service
table in `services/README.md`, the domain table in `.claude/README.md`, routing in
`.claude/epic/villages.json`, standing in `STATUS.yaml`, vocabulary in `CLASSIFICATION.md`,
seats in `contracts/fixtures/seat-topology.reference.json`, nodes in
`contracts/fixtures/node-registry.reference.json`, and offices in
`contracts/capability-offices.json`. Each is authored by hand and nothing checks any of
them against the others, so they drift silently and a reader has no single place to start.

One part of the answer is already computed rather than authored:
`contracts/fixtures/capability-map.reference.json` joins all six service manifests with the
offices table into capability, service, operation, office, standing, required authority and
endpoints, and carries an `input_state_digest` so staleness is detectable. That is the
Registry's first projection, built before the Registry had a name.

Eighteen open issues in `.claude/epic/tree.json` declare `requires: #14`, more than any
other bit in the tree — Gateway, Relay, Workflow, Automation, the Capability Broker,
Workers, Adapters, Proofing and Phase-I Qualification among them. This is the boundary
most other work is waiting behind.

## What it is not

The Registry resolves; it does not define. `CLASSIFICATION.md` still owns vocabulary, each
`contracts/service.json` still owns its operations, `STATUS.yaml` still owns standing, and
`decisions/` still owns policy. Every registry entry names the document that owns its
subject and carries that document's address and digest. An entry whose source cannot be
resolved is refused, not stored.

The index is a projection and must be rebuildable from its declared sources alone. If the
index and a source disagree, the source wins and the disagreement is recorded as a drift
finding rather than repaired in place.

## Owned domain records

- `registry-entry` — one versioned entry for a named thing, with its kind, its owning
  document address and digest, and its standing as that document declares it;
- `entry-relation` — a typed edge between two entries, such as an operation belonging to a
  service, a term used by a contract, or a document governing a domain;
- `owner-record` — the participant accountable for a domain, the mandate given to them, the
  requirements they answer, their resource budget, their deadline, and the separate
  participant that witnesses their work;
- `registry-index` — the rebuildable projection over every declared source;
- `resolution` — the answer to one lookup: the entry, its relations, and the source that
  owns it;
- `drift-finding` — a recorded disagreement between the index and one of its sources;
- `registry-receipt` — the terminal receipt for any registry operation.

## Owner records

An owner record answers a question no document currently answers: who is accountable for
this domain, what were they asked to do, what may they spend, by when, and who checks it.
The authored table is `contracts/domain-owners.json`, validated by
`contracts/domain-owners.schema.json` and checked by `python scripts/sov_owners.py check`.
The `declare-owner` operation is the built path that would later replace hand-authoring;
until then the table is policy input and the Registry reads it.

Two constraints are load-bearing and checked today:

1. an owner and its witness may never be the same participant, because a build report
   cannot witness itself (`AGENTS.md`, Evidence and standing);
2. a budget and a deadline are required fields, so an owner without a resource envelope or
   a date cannot be declared at all.

Neither constraint grants anything. An owner record names the authority an owner would
need; it never holds it.

## Proving narrative

From a clean local checkout:

1. rebuild the index from the declared sources and record its input state digest;
2. resolve `sov://asset/ingest-asset` and get back the operation, its owning service, its
   manifest address, its office, and its required authority;
3. resolve the term `Observation` and get back `CLASSIFICATION.md` as its owning document,
   not a restatement of the definition;
4. resolve the domain `record` and get back its owner, mandate, budget, deadline, and
   witness;
5. change one service manifest without rebuilding, then observe the index refuse to answer
   as fresh and emit a drift finding naming the source that moved;
6. rebuild and observe the same lookup answer correctly;
7. attempt to register an entry whose owning document address does not resolve, and observe
   the refusal;
8. attempt to declare an owner whose witness is itself, and observe the refusal.

## Defeating cases

- a lookup answers from the index while a declared source has changed underneath it;
- an entry is stored without an owning document address, or with one that does not resolve;
- the Registry restates a definition instead of pointing at the document that owns it;
- two entries claim the same name and both resolve;
- the index is repaired in place instead of rebuilt when it disagrees with a source;
- an owner record is declared with the same participant as owner and witness;
- an owner record is declared with no budget or no deadline;
- a registry entry is treated as standing, authority, or permission to act;
- retiring an owner erases the earlier record instead of adding a counter-record.

## Deferred

Cross-node resolution, remote registries, a query language, a UI projection, and any
transport beyond in-process and CLI are outside the first proof. Their interfaces may be
declared; their effects stay refused until separately admitted.
