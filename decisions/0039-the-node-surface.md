# 0039 · The node surface: one suite, three membership models

Status: `PROPOSED · OWNER ACCEPTANCE OVER EVIDENCE`

Drafted at Bdo's direction (2026-08-23 conversation). Bdo named a missing
product front: a local user and their agents talking in channels and threads,
connecting to other Soveraeign nodes, with social-shaped surfaces as the way
external value leaves and feedback returns. He described it as Discord's
channel model, Slack's integration core, and social media at the endpoints.

Drafted under `decisions/0023-acceptance-not-approval.md` and the lowest-tier
rule of `decisions/0033-close-the-founding-docket.md`, Ruling 1.

## Decision

The suite is not a new structural level. `CLASSIFICATION.md` already types
**Node** as a locally sovereign operating instance and **Federation** as two or
more nodes joined by governed crossings, and forbids new levels between them.
This decision adds nothing to that vocabulary. It rules three things:

1. **The node surface is the Console Service's channel, thread, and post
   records, promoted.** `services/console/CHARTER.md` lists them as the
   experience projected over five operator surfaces. This decision makes them
   the node's primary interface for every actor, human and model, and leaves
   notifications, settings, dashboards, judgement requests, and activity views
   as views inside that interface rather than siblings of it.

2. **Federation is a governed crossing between two nodes, settled twice.**
   `SPEC.md` Traceability defers "Node and federation boundary" to a later
   phase and `SYSTEM.md` repeats the deferral. This decision opens the boundary
   at proposal standing and rules its shape, without admitting any crossing
   that leaves the machine in this phase.

3. **The public surface is a projection, never a record type.** Feeds,
   profiles, and follows are read models derived from threads an operator
   marked public. No post enters the node because a stranger wrote it.

### Three layers, three membership models

| Layer | Shape | Who a member is | Governing record |
| --- | --- | --- | --- |
| Inside one node | Slack | A seat occupant — human, model, or adapter — holding a grant in this node | `contracts/fixtures/seat-topology.reference.json` |
| Across nodes | Discord | An actor that holds seats in several nodes; identity travels, authority does not | proposed federation crossing |
| At the edge | Social | Nobody. There is no membership; there is a published projection and an inbound queue | proposed public projection |

The three do not compose into one membership table, and trying to make them
would be the defect. A remote actor is not a member of your node. It occupies a
seat your root seat granted, and that grant is the entire relationship. This is
the same rule `AGENTS.md` already states for local actors: authority arrives by
grant and never by successful operation.

### Adapters are members, not plumbing

Slack's distinguishing property over Discord is that an integration is a
first-class member with its own identity and its own permissions, not a webhook
bolted to a channel. That is already this repository's rule: `/adapters` owns
translation to a named external system and holds no standing. This decision
makes the consequence explicit. An adapter that posts into a thread posts as
itself, under its own grant, and its posts are attributable to it. There is no
anonymous system message.

## Why the public surface must be a projection

If a public post is a native record, the node inherits moderation, spam, abuse,
and inbound identity as kernel problems on the day the surface opens. As a
projection over threads the node already owns, they are a publishing policy over
records that already passed a grant. The asymmetry is the point: outbound is a
rebuildable view; inbound is an addressed input that queues for an operator and
becomes a record only when one admits it.

`SPEC.md`'s Projection rule already requires every projection value to resolve
to an authoritative record. A public feed satisfies it. A public post record
would not, because nothing in the node authorised the stranger who wrote it.

## Why federation here is cheaper than consensus

Federated chat systems spend their engineering on state resolution: two servers
disagree about a room, no server owns it, and the protocol must converge them.
Soveraeign does not have that problem, because every node has a root seat that
settles (`decisions/0020`, `contracts/fixtures/seat-topology.reference.json`).

Two nodes disagreeing is a crossing where each owner settles their own copy and
the disagreement is recorded rather than merged. The counter-record rule in
`AGENTS.md` — retraction adds a record and never erases the original — is
already the right primitive. Federation is therefore closer to mail than to
distributed consensus, and its cost sits in identity and transport, not in
convergence.

## Observed state at drafting

- `services/console/` holds ten contract schemas, nine conformance scenarios,
  and 814 lines of implementation across six modules. `STATUS.yaml` reads
  `console_service_status: BUILT_CONTINUITY_PATH_SELF_TESTED_REMAINDER_BOUNDARY`.
- `channel.schema.json` and `thread.schema.json` carry no node scope. Every
  console record is implicitly single-node.
- No contract under `contracts/` or any `services/*/contracts/` names a node
  address, a peer, or a crossing between nodes.
- GitHub reaches the repository through exactly one call, `gh issue list` in
  `scripts/sovepic/projection.py`, plus five workflow files under
  `.github/workflows/`. `scripts/sov_ticket.py` reads an export and never
  invokes `gh`.

## Constraints

- No new structural level between Node and Federation (`CLASSIFICATION.md`).
- No provider SDK type in a kernel or service contract (`AGENTS.md`).
- No external-world effect in this phase; a federation crossing may be
  contracted and fixtured but not carried.
- The Console remains a projection over authoritative records and never becomes
  a private authority system (`services/console/CHARTER.md`).

## Consequences

- `services/console/contracts/channel.schema.json` and `thread.schema.json`
  gain a node scope. The nine scenarios under `services/console/conformance/`
  are narrative seeds carrying `status: SEED` and are not executed, so they do
  not break; `services/console/tests/test_contract_shapes.py` does, because it
  validates emitted records against those schema files.
- `SPEC.md` Traceability stops reading "later phase" for the node and
  federation boundary and points here instead.
- A new contract set is owed: node identity, federation crossing, and public
  projection, each with a positive and a defeating case before implementation.
- GitHub is reclassified from coordination substrate to an adapter serving CI
  and off-machine durability. The single `gh issue list` read becomes one
  source among possible sources for the epic projection rather than the source.

## Defaults taken

Reversible choices made to keep moving; Bdo may overturn any of them without
defeating the ruling.

- **No voice, video, or realtime presence in this boundary.** The surface is
  text and artifact addresses. This is roughly half the total effort of the
  named references and none of it is required by any Phase-I requirement.
- **The public projection is local and read-only.** Publishing outward to an
  existing platform is a separate adapter and is deferred, not designed here.
- **A node address is an opaque local identifier.** No DNS, no key
  distribution, no discovery protocol is chosen. Federation fixtures use two
  local node identifiers and cross no machine boundary.
- **GitHub keeps CI.** Nothing in this decision proposes replacing
  `.github/workflows/`.
- **Federation stays at proposal standing.** No transport is admitted.

## What would defeat this ruling

- A conformance case where a public reply from a non-member must be settled by
  the node rather than queued as an addressed input. That would make the public
  surface a record type and defeat claim 3.
- Two nodes needing an agreed shared record that neither root seat may settle
  alone. That would reintroduce the consensus problem this decision claims to
  avoid.
- A federation membership requirement the seat model cannot express without a
  new structural level. That would defeat the claim that no vocabulary is added.
- Evidence that promoting channel, thread, and post to the node's primary
  interface forces the Console to hold authority rather than project it.

## Judgement queue for Bdo

1. Is voice, video, or realtime presence in this product boundary? The default
   taken says no, and that answer sizes roughly half the build.
2. Does "social media as endpoints" mean the node publishes outward to existing
   platforms, or that the node presents a social-shaped surface others browse?
   The default taken is the second, local and read-only.
3. Is the Console promoted from one of five operator surfaces to the node's
   primary interface? Claim 1 assumes yes; `services/console/CHARTER.md` today
   says otherwise.

## Residuals

- Node scope has landed on the console: `channel.schema.json` and
  `thread.schema.json` require `node_id`, `ConsoleService` takes the node it
  serves with no default, and `contract.foreign_records` names any record that
  belongs to another node or disagrees with its channel. The console suite is
  39 tests, up from 32.
- `ConsoleService` gained a required constructor argument, which is a breaking
  change to every caller. Six were updated; the CLI defaults `--node` to
  `node:local`, and that default is the one place a console can still run
  without naming its node.
- `SPEC.md` still reads "later phase" for the node and federation boundary and
  has not been edited.
- Node identity and the federation crossing are drafted:
  `contracts/node-identity.schema.json` and
  `contracts/federation-crossing.schema.json`, with
  `scripts/sovkernel/node_identity.py`, `scripts/sovkernel/federation.py`, their
  fixture pairs, and `scripts/tests/test_node_identity.py` and
  `scripts/tests/test_federation_crossing.py`. The public projection is drafted
  too: `contracts/public-projection.schema.json`,
  `scripts/sovkernel/publication.py`, its fixture pair, and
  `scripts/tests/test_public_projection.py`. All three contracts the Decision
  named as owed now exist at proposal standing with executable defeating cases.
- The crossing contract names an address and a digest and carries no bytes. How
  two nodes come to address the same content the same way is unspecified, and no
  transport is chosen. `decisions/0039` took the default that none is chosen in
  this phase; the crossing contract is what that default is holding open.
- The node registry has no storage, no CLI, and no read path. Nothing writes a
  node record; the contract is graded against fixtures only. Nothing yet checks
  that a console's `node_id` names a node in a registry, so the two contracts
  are consistent by convention rather than by check.
- `post` and `operator-session` carry no node scope. A post is reached through
  its thread, which now carries one, but a post record read alone still does
  not say which node it came from.
- Publication is now a console record: `publication.schema.json`,
  `ConsoleService.publish_thread` and `withdraw_publication` under a `publish`
  capability, `contract.published_threads`, and two CLI commands. Withdrawal
  appends, so a thread leaves the outward view without the record of it having
  been published going away.
- The two sides disagree about who publishes. `public-projection.schema.json`
  requires `published_by` to be a seat; the console records an operator id,
  because the console has no seat model and `seat-topology.reference.json` is a
  kernel fixture no service reads. Nothing bridges them, so a projection built
  from console records today cannot fill that field honestly. This is the first
  place the seat layer and the service layer have had to agree and could not.
- The inbound half of the public surface is a contract term
  (`inbound: QUEUED_AS_ADDRESSED_INPUT`) and nothing more. No queue, no
  addressed-input record, and no operator path for admitting one exists.
- This node now has a registry: `contracts/fixtures/node-registry.reference.json`
  names `node:local` rooted at `seat:root` with no peers, `scripts/sov_node.py`
  reads and grades it, and `scripts/tests/test_sov_node.py` runs that grading
  inside the existing tooling suite. The console's default node and the
  registry's holder are checked against each other, so a console writing for an
  unknown node fails the build.
- The registry grading is not a separate `verify.py` check. One was added and
  then removed: it cost 0.085s against a gate with about 11ms of headroom in the
  worst of eight measured runs, and `test_sov_node.py` already invokes
  `sov_node.main(["validate"])` in process. The budget itself is a separate
  defect, recorded below.
- `python scripts/verify.py` has almost no margin. Twenty checks fan out as
  twenty concurrent subprocesses; measured wall time is 2.55-2.99s against the
  3.000s budget `AGENTS.md` states, and one observed run reached 4.359s under
  load from another process working in the same tree. Clearing every
  `__pycache__` changed wall time by under 50ms, so bytecode compilation is not
  the cause; the cost is twenty simultaneous interpreter startups. Raising the
  budget is a policy change and reducing the fan-out is verification-domain
  work, and this decision does neither.
- The registry is a checked-in projection, like the seat topology. No transition
  admits a peer, so adding one is an edit to a file rather than a recorded
  judgement. That is the same shape `decisions/0020` left the seat registry in
  and is not worse than it, but it is not a settlement path.
- Crossings and public projections are still fixture-only. Nothing writes a
  crossing record, and no projection document is built from console records -
  the second is what S19 now blocks.
