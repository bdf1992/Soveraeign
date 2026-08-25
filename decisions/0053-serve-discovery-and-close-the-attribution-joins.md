# 0053 · Serve discovery, and close the two attribution joins

Status: `BUILT · SELF-TESTED · NOT WITNESSED`

Bdo directed both pieces on 2026-08-24, in order: make `JOURNEY-02` the next bounded
product slice, then complete the two small attribution contracts and prove one end-to-end
trace. `decisions/0052` records the ruling; this records what was built under it.

## 1 · Discovery is served, from the projection

`console.discover-operations` was `BUILT` and reachable in process only, and its answer
came from a hand-written tuple of nine console operations in `continuity.py`. That tuple
is gone. The answer is now read from
`contracts/fixtures/capability-map.reference.json` - the projection the repository already
rebuilds and checks - so discovery cannot drift from what the node declares.

```text
capability map  ->  console.discover-operations  ->  bindings/mcp  ->  participant
```

No HTTP and no new transport. The two that carry it are the CLI and MCP, both of which
already existed. `console.discover-operations` now reads `IN_PROCESS`, `CLI` and `MCP`
`ACTIVE`.

**The capability map grew a `shape` block.** Reachability was already there; what a
participant needs beyond it - the logical endpoint, what the operation acts on, its CRUD
verb, its product requirement, its kernel transition, its preconditions, what it commits
and how it refuses - was in the service manifests. Copying it into the map at build time
means one projection answers the whole question. A discovery surface that read the map for
reachability and the manifests for shape would have been the second list again, one layer
down.

A fresh participant now gets, per capability: identity and logical endpoint; every
transport and its activation; required authority; effect class; actor kinds; office;
preconditions; refusal codes; commit; and the `PROD-I` requirement it serves.

### Authority is answered honestly, and the answer is bad news

Two readings, named in the response so they cannot be mistaken for each other:

```text
available   what exists on this node
permitted   what this participant may currently do
```

They are not the same reading, and the second one has edges the response states per row:

| Reading | Means |
| --- | --- |
| `HELD` | a live grant in this journal names this authority |
| `NOT_HELD` | this service governs the capability and no live grant covers it |
| `NOT_KNOWN_HERE` | another service's authority store governs it; this console reads one store and will not guess |
| `UNDETERMINABLE` | this service declares one authority name and enforces another, so no grant can be matched against it |

**Building the honest reading found that 96 of 102 capabilities read `NOT_KNOWN_HERE`.**
The node has more than one authority store, so no single reading of "what may I do" is
complete today. That is a real finding and it is reported rather than smoothed over.

**It also found that the console declared one authority vocabulary and enforced another.**
`contracts/capability-offices.json` said `post:message`, `open:thread`, `open:channel`,
`publish:thread`; `core.py` checked `post`, `open-thread`, `open-channel`, `publish`. Six
capabilities, all diverging, which made `permitted` unanswerable for every one of them.

Five were pure renames and are aligned: the declared name is policy and older, so the
implementation moved to it. The sixth is not a rename. `console.archive-thread` declares
`archive:thread` and enforces `open:thread` - whoever may open a thread may archive it -
which is a policy question rather than a name. **It is left diverging and visible**;
narrowing it silently would have removed an ability from anyone holding `open:thread`
today. `services/console/tests/test_discovery.py` counts the divergence against the office
table so a second one cannot appear unnoticed.

`ENFORCED_AUTHORITY` in `authority.py` now names what each operation actually checks,
rather than leaving it at the call sites where nothing could compare it to policy.

### The observation

`python bindings/mcp/observe_journey_02.py` walks the journey through the real binding: a
participant with no session and no grant asks what it can do, gets 102 declared and 34
reachable, then reads the journal back through a different endpoint and finds the two
entries the crossing left. `bindings/mcp/observations/journey-02-discovery.json` records
it, with both entry digests.

`console_operations` is `observe` tier rather than `read`, so the crossing is journalled.
A participant asking what it may do is an act the node should be able to account for
afterwards (`GROUND-007`).

**The observation is not independent and says so.** It calls the gateway to observe the
gateway; reading the journal back is a second endpoint, not a second observer. Settling
that needs the Observation Service, which is a charter (`GROUND-010`).

## 2 · The two attribution joins

Both were named in `reports/2026-08-24-product-canon-attribution-discovery.md` and
unblocked by Bdo's Q2, Q5 and Q6 rulings.

**`contracts/issue-metadata.schema.json` gained an optional `capability` array.** A
referent, never an identity: the ticket points at capability identifiers the repository
already names and carries no second definition of them. Validated offline against the
projection. Three conformance cases, one positive and two defeating - a referent that is
not shaped like an identifier, and a repeated one.

**`contracts/receipt.schema.json` gained an optional `consumed` array and a
`serves_capability`.** Usage carries four dimensions and only four:
`wallclock_seconds`, `tokens`, `tool_calls`, `usd`. A fifth needs a decision record rather
than a new string.

The rules the schema states rather than implies:

- Usage is independent of effect class. A `RECORD_LOCAL` operation still spends wall
  clock, tokens and electricity.
- `BUDGET` is an intended envelope, `COST` is a valuation of usage, `EFFORT` is activity
  attributable to an objective. None of the three belongs in a usage record.
- No conversion between dimensions exists. A `usd` amount of zero on a local run is a
  valuation, not an absence of usage.
- `consumed` is optional, so a receipt for an operation that measured nothing does not
  have to invent a number.
- `serves_capability` is exactly one capability. What a run directly served is measured
  once; every broader intention containing it is a view.

## 3 · One end-to-end trace, from a real measured execution

`python scripts/sov_trace.py up --tickets conformance/fixtures/tickets/metadata-cases.json`
reads `bindings/mcp/observations/journey-02-receipt.json` - a schema-valid receipt for the
crossing above, measured with `time.perf_counter` around the call - and walks it up:

```text
receipt_748fcb…  COMMITTED, through bindings/mcp:console_operations
  spent       0.006 wallclock_seconds, 1 tool_calls, 0 usd
  CAPABILITY  console.discover-operations           [BUILT]
  OPERATION   sov://console/discover-operations     requires read:session, RECORD_LOCAL
  REQUIREMENT PROD-I-6
  WORK ITEM   RED-CHARTING-001
  JOURNEY     JOURNEY-02, JOURNEY-14
  PROMISE     PROMISE-01, PROMISE-03, PROMISE-04, PROMISE-05, PROMISE-10
  GROUND      GROUND-001, 002, 004, 005, 006, 007, 013, 014
```

Every edge Bdo named resolves, from a real execution rather than an example written to
agree with the chain.

**And the double counting is visible rather than avoided.** The same six milliseconds
appear in two journey views, five promise views and eight ground views. Summing the ground
views would report 0.042 seconds where 0.006 were spent. The measured total is computed
from the distinct receipts and never from a view, and `overlap()` prints what a naive sum
would have invented:

```text
MEASURED ONCE across 1 receipt(s): 1 tool_calls, 0 usd, 0.006 wallclock_seconds
  summing the capability views would invent nothing
  summing the journey views would invent 1 tool_calls, 0.006 wallclock_seconds
  summing the promise views would invent 4 tool_calls, 0.024 wallclock_seconds
  summing the ground views would invent 7 tool_calls, 0.042 wallclock_seconds
```

## What this establishes, and what it does not

`BUILT` and self-tested. 72 console cases, 22 gateway cases, 19 trace cases, and the
repository gate passes everything it did before.

It does **not** establish that `JOURNEY-02` is walkable: four of its five crossings -
`gateway.list-endpoints`, `gateway.resolve-capability`, `registry.resolve`,
`registry.read-index` - are still declared and unreachable. One participant can now ask one
node what it can do; the Gateway and Registry surfaces that would answer the same question
their own way are unbuilt.

It does not establish `WITNESSED` for anything. The observation was taken by calling the
thing it observes.

## Defaults taken

- The capability map carries a `shape` block, and it is required. A capability whose
  manifest declares nothing gets `{}`, so the absence is visible rather than missing.
- `console_operations` is `observe` tier, so the crossing leaves a journal record.
- The gateway's console is wired to the gateway's own `RecordService`, so console records
  and gateway events land in one journal. One node, one journal.
- Five console authority names were aligned to the office table; the sixth was left
  diverging because changing it would narrow an ability rather than rename one.
- `sov_trace.py --tickets` reads the conformance corpus directly, so the work-item join is
  demonstrated against fixtures the repository already checks.

## Open, and Bdo's

**`console.archive-thread`: does archiving a thread need its own grant?** Policy says
`archive:thread`, the code says whoever may open a thread may archive it. Either is
defensible - archiving is reversible in the sense that the record survives, and it does
stop a thread conditioning what happens next. One line either way.

**Ruled 2026-08-24.** It does: archiving a thread for yourself would not, archiving the
thread does, and this operation is the second one. The code moved to `archive:thread`,
which narrows the ability on purpose, and the last declared/enforced divergence is closed.
`decisions/0054` records the ruling and what followed from it. The observation below was
retaken, because it recorded the divergence that no longer exists.

## Residuals

- 96 of 102 capabilities cannot be answered for by any single authority reading. One node
  with several authority stores is the cause, and no contract yet says which store governs
  what.
- `capability_map_fresh` is a declared precondition that nothing verifies on the serving
  path. The answer reports `verified: null` rather than implying somebody checked.
- The receipt shape the gateway journals is not `contracts/receipt.schema.json`. The
  measured receipt is written beside the journal rather than being the journal entry, and
  reconciling the two shapes is unfinished work.
- Nothing joins a work item to a run. The trace above joins a ticket to a capability and a
  receipt to a capability; the two meet at the capability rather than at the run.
