# 0033 · Close the founding docket

Status: `OWNER-DIRECTED · RULED AT CONTROL RESOLUTION`

Bdo, 2026-08-23: "O1-O22 should never have existed in the way they do now. You
should be working toward acceptance and validation of request by having
witnessed evidence, not by raising and only escalating. The idea is controller
can make decisions at their resolution, all the way to workers."

`decisions/0023-acceptance-not-approval.md` already said the owner gate is
acceptance over evidenced results, and `decisions/0024-open-decision-drain.md`
already ruled seventeen of the docket's questions on `main`. This branch kept
the queue anyway and produced `reports/2026-08-23-ratification-docket.md`, which
answered a direct instruction to ratify with "NOT MET for every surface" and a
list of things only Bdo could supply. That report is the defect this record
closes.

## What went wrong

The docket had three failures, and they compound.

**Escalation was cheaper than evidence.** Registering `O21` cost one YAML entry.
Proving the projection boundary needed a charter, a parity ledger, and fixtures.
The queue rewarded the cheap move, so the queue grew.

**The identifiers were not stable.** `O20` names the verification-channel
projection on this branch and the compiled kernel transition contract on `main`.
Two branches minted the same identifier for different questions, and nothing
detected it, because an open decision is prose, not a checked record. An
identifier that two branches can define differently cannot carry standing.

**Every question routed to one person regardless of its resolution.** Whether
Console is the third service boundary is a sequencing question that a controller
can rule and a fixture can defeat. It sat in the same queue as public naming
clearance, which genuinely is Bdo's. Mixing them made the whole queue read as
owner-blocked, which made "blocked" the default posture.

## Ruling 1 — resolution rule

A decision is settled at the lowest tier that can produce evidence defeating the
alternatives.

- **Work** rules implementation questions: data structures, module layout,
  algorithms, test shape, error handling. Defeated by a failing test.
- **Orchestration** rules sequencing and decomposition within one operation.
  Defeated by an operation that cannot be completed as sequenced.
- **Control** rules boundary, internal-naming, contract-shape, and scheduling
  questions across operations. Defeated by a conformance fixture, a parity
  failure, or a contract that cannot be satisfied.
- **Bdo** rules owner-held product intent, public product naming, external
  commitment, irreversible external-world effect, secrets, destructive
  repository administration, and the acceptance standing itself.

A tier that can rule must rule. Escalating a decision that the escalating tier
could have defeated with available evidence is itself a defect, reportable the
same way a failing check is.

## Ruling 2 — the O-space is retired, not reserved

`O1` through `O22` are retired identifiers. `STATUS.yaml` records which decision
ruled each. No new `O<n>` may be minted.

A ruling is revised by a **defeating observation recorded in a new decision**,
never by reopening an identifier. This is the same demotion rule as
`decisions/0024-open-decision-drain.md`, applied to the identifier space itself:
history is added to, not rewritten.

Genuinely owner-held questions live in `owner_holds` in
`STATUS.yaml`, which states what the hold blocks *and what it does not block*.
`PUBLIC-CLEARANCE` is the only one today.

## Ruling 3 — the remaining docket questions

`decisions/0024-open-decision-drain.md` ruled O1-O13, O16, O17, O19 and O20 (its
own reading of O20). The questions that stood on this branch are ruled here.
Each ruling is conservative, testable, and carries the observation that would
defeat it.

### O14 / O18 · Console Service boundary — ACCEPT

`decisions/0014-console-service-boundary.md` stands: Console is the third
sibling service inside a local Node, owning operator sessions, channels,
threads, posts, notifications, judgement requests, operator settings, and
declared dashboard and activity projections. The threaded operator interface is
a Human Binding over that service; a Model Binding reads the same records as
typed structure. Console surfaces pending rights and spent judgement; it never
holds them.

The provisional Human Binding target is authorized. `SPEC.md` is accepted
(0024, O10), so the "ahead of O10" caveat in the original question no longer
applies.

**Defeated by:** a Console record that can only be produced through the human
interface, which would prove the interface is authority rather than a binding.

**Standing:** `OWNER_ACCEPTED_BOUNDARY_NOT_IMPLEMENTED`. Accepting the boundary
is not building the service.

### O15 · Scheduled runs — ACCEPT the pattern, every schedule stays disabled

`decisions/0015-scheduled-runs.md` stands: schedule declarations are the
schedule analogue of an operation plan, gates refuse before invocation with a
visible reason code, and a run is one headless session with mode-scoped tool
rights.

Every shipped schedule remains disabled. That is not a hedge pending acceptance
— it is the pattern working. `EXTERNAL_WORLD` is never schedulable in Phase I,
and enabling a specific schedule that consumes resources unattended is a
separate, per-schedule decision with its own evidence.

**Defeated by:** any schedule firing without a ledger entry, or any gate that
refuses without a reason code.

### O21 · Asset Projection Service boundary — ACCEPT

`decisions/0030-asset-projection-service-boundary.md` stands, under that name, as
the fourth service boundary. Its parity target and lane scope were defaults taken
in that record and remain defaults: they are the cheapest thing to counter with a
fixture, which is exactly why they do not need a ruling from Bdo.

**Defeated by:** a retrieval result the projection can produce that the Asset
Service cannot reconstruct from authoritative records, which would make the
projection a second authority.

### O22 · Story as a ticket kind — ACCEPT

`decisions/0022-story-ticket-kind.md` stands: a story is an actor in a
`CLASSIFICATION.md` role crossing a counter and asking the substrate for
adjustments, bound to a conformance scenario, never dispatched. The teller is
`actor_kind` plus `role`.

Owner is read as a context that sets an operator's Binding and Projection, not as
a role. This is consistent with `decisions/0020-owner-seat-topology.md`, which
makes Owner a relational seat rather than a classification role.

**Defeated by:** a story that dispatches work, or an Owner reading that requires
a new role value in `CLASSIFICATION.md`.

### Unblock request as a ticket kind — ACCEPT

`decisions/0032-unblock-ticket-kind.md` stands. It is the mechanism that makes
`BLOCKED` provable rather than assertable, and this record makes it
load-bearing: under Ruling 1, a tier that claims `BLOCKED` files an unblock
ticket naming the held ticket, the provision, and the tier asked. A `BLOCKED`
claim without an unblock ticket is an unproven claim.

**Defeated by:** an unblock ticket whose named provision was already available to
the filing tier.

### Verification channels and the GREEN collision — ACCEPT, and the channel renames

`decisions/0025-verification-channels-and-merge-authority.md` stands: three
orthogonal channels, the third not self-generable, and the best grade reachable
in Phase I is build-plus-attack with the third channel pinned at zero.

The collision that record queued is ruled here: **`SDLC.md` `GREEN` keeps the
name.** It is the older term, it is a derived go-state, and it is referenced
across the loop documentation. The channel renames to **`world`** — contact with
the world outside the repository, which is what the channel actually measures and
what makes it non-self-generable. The channels are therefore `blue`, `red`, and
`world`.

**Defeated by:** any place `world` reads worse than the old channel name in the
projection, or an `SDLC.md` `GREEN` computation that turns out to depend on the
channel.

### Federation harness — ACCEPT as host plumbing

`decisions/0026-federation-harness.md` stands. The harness holds no standing and
no authority, its runs may propose at most `BUILT -> WITNESSED`, and a build
claim is always witnessed by a different agent than its builder.

The open judgement in `.claude/README.md` — whether executable workflows are
admissible before their defeating fixtures exist — is ruled at Control: **yes,
for harness plumbing only.** The harness is not a participant and produces no
authoritative state, so the no-runtime-code-before-fixtures boundary in
`STATUS.yaml` binds services, contracts, and adapters, not the host tooling that
launches them. A harness workflow that writes authoritative state is not harness
plumbing and the boundary applies to it in full.

**Defeated by:** a harness workflow observed writing a record that a service
contract owns.

### Local model adapter — ACCEPT the boundary, standing unchanged

`decisions/0027-local-model-adapter.md` stands as the adapter boundary. The
adapter grades declared bindings and invocation records against a recorded
runtime inventory rather than a live daemon, so `python scripts/verify.py`
cannot depend on whether a model server happens to be running.

Accepting the boundary does not witness the implementation.
`local_model_adapter_status` stays `BUILT_SELF_TESTED_NOT_WITNESSED`; the
fourteen defeating fixtures establish `BUILT`, not `WITNESSED`.

**Defeated by:** an adapter path that reaches a provider without a receipt, or a
fallback that is not separately receipted.

### History as lineage, and the lessons loop — ACCEPT

`decisions/0028-history-as-lineage.md` and `decisions/0029-lessons-loop.md`
stand. Prior work enters as attributed evidence verified against
`lineage/SOURCES.lock`, never as policy by implication, and residuals route to
`LESSONS.md` instead of accumulating in reports nobody reads.

**Defeated by:** a lesson closed without a change to a governing document, a
contract, or a fixture.

## What this record does not do

It does not witness anything. Every `*_status` field that read
`BUILT_SELF_TESTED_NOT_WITNESSED` still reads that way. Accepting a boundary, a
contract shape, or a vocabulary is a different act from observing that an
implementation satisfies it, and this record performs only the first.

It does not touch `PUBLIC-CLEARANCE`. No agent may claim legal, trademark, or
domain clearance, and this record claims none.

It does not grant authority to the tier that wrote it. Ruling 1 assigns
decisions to tiers; it does not let a tier widen its own scope, ratify owner
judgement, or witness its own build. `AGENTS.md` is unchanged on every one of
those points.

## Demotion

Bdo may `REJECT`, `STRIKE`, or `REDIRECT` any ruling here. A rejection of one
ruling does not reopen the docket; it produces a new decision that supersedes
that ruling and names what defeated it.

## Sources

- Bdo's direction, 2026-08-23, quoted above.
- `decisions/0023-acceptance-not-approval.md` — the acceptance gate.
- `decisions/0024-open-decision-drain.md` — the seventeen prior rulings.
- `reports/2026-08-23-ratification-docket.md` — the failure mode, preserved.
- `AGENTS.md`, Authority; Self-direction is not delegation; Blocked edge is not
  blocked frontier.
