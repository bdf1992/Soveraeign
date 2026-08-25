# 0041 · The Observation Service: independence has an owner, logging already had one

Status: `PROPOSED · OWNER ACCEPTANCE OVER EVIDENCE`

Drafted at Bdo's direction (2026-08-23 conversation). Reviewing the Gateway Service charter,
Bdo said the recording concern should be its own observation service rather than the door's
job, and named the feedback path: an operator pilots the node through the MCP tool surface,
and what happened comes back. Asked what makes an observer independent, he ruled:
independence is inferred when the relation is not direct.

Drafted under `decisions/0023-acceptance-not-approval.md` and the lowest-tier rule of
`decisions/0033-close-the-founding-docket.md`, Ruling 1. It narrows
`decisions/0040-the-declared-service-surface.md`, Ruling 5.

## Decision

### 1. `services/observation/` owns independent observation, and only that

`SPEC.md` defines an `Observation` as evidence carrying an observer, the addresses and digests
that observer looked at itself, the predicates that held, and an `observer_relation` stating
how it avoided relying solely on the executor's report. `settle_run` refuses with
`OBSERVATION_MISSING` when it is absent. `observe_run` is one of fourteen kernel transitions
and, before this decision, the only one with no service behind it.

That is the gap this service closes. Eight declared operations, all at proposal standing:
predicate declaration, an observation request and its listing, a relation inference, the
observation itself, a read, a counter, and an attestation.

### 2. Independence is inferred from the run's record, never declared by the observer

Nobody registers as an observer and nobody asserts their own independence. A declared relation
is the observer vouching for itself — the same shape as an executor's report standing in for an
observation, which this contract has refused since founding.

`infer-relation` walks the run's own record looking for a direct edge to the candidate
observer: it executed the run; it holds the lease, fence, or session the run ran under; its
grant descends from the run's grant chain; it produced the output it proposes to observe; or
the executor's report is the only evidence available to it. One edge found is
`OBSERVER_NOT_INDEPENDENT`. None found admits the observer.

That edge set is proposed, not settled. It is the entire enforcement surface of the service,
and a missing edge is a way past the check.

**The inference has three outcomes.** Absence of a recorded edge is not absence of a relation.
A record too thin to answer would otherwise read as independence, making the check worthless
exactly where it matters most — on runs that recorded too little. So `DIRECT`, `INDEPENDENT`,
and `UNDETERMINED`, with `RELATION_UNDETERMINED` refused by both `infer-relation` and
`observe-run`. Silence is not a pass. This third outcome is not something Bdo said; see
Defaults taken.

### 3. Logging is not this service's job, because logging already has two owners

The Record Service owns the append-preserving journal — that is the log. The Console Service's
`projection-view` is an operator's view over it. A third place recording what happened would
be the competing authority `AGENTS.md` forbids, and it would dilute a term the kernel uses
narrowly.

The distinction is worth stating plainly because it is easy to lose: the journal answers *what
occurred*; an observation answers *whether something that did not perform it checked, and
whether the predicates declared beforehand held*. Those are different questions and only the
second one is currently unanswerable.

### 4. The refusal is the service

`infer-relation` returning `DIRECT`, and `observe-run` refusing on it, is the operation the
whole boundary exists to perform. A service that only ever produces observations proves
nothing about whether it can tell an observer from an executor, and one that cannot say "I
don't know" will call every thin record independent. The charter's proving operation drives
both refusals before it drives a success.

### 5. This closes the loop the MCP surface opens

`bindings/mcp/manifest.json` already tiers its tools `read`, `act`, and `observe`, and its
`observe_verify` tool appends an `OBSERVATION` — but of the repository, not of a service run.
The shape is right and the subject is wrong. An operator acts through the tool surface, acts
land in the journal, and the observation path turns those into evidence about whether the act
did what it claimed. Without it the only evidence anything worked is the report of the thing
that did it, which this contract has refused since founding.

## Observed state at drafting

- Eight services, 100 declared operations. `python scripts/sov_service.py check` passes.
- The capability map is total over all 100 and not stale. The `inspectorate` counter held one
  capability before this decision and now holds nine.
- Check 3 on the `AI-NATIVE.md` bar — independent observation — reads `UNATTESTABLE` on every
  service assessment in the repository.
- `scripts/witness_observe.py` performs observation work outside any service boundary.
- A `registry` service and three further console operations appeared in the working tree from
  another session during this work; they are not this decision's and were not modified.

## Constraints

- Nothing is implemented. This decision moves a boundary, not behaviour.
- No new transport, effect class, or external effect. Every declared operation is
  `RECORD_LOCAL`.
- The Record Service keeps sole ownership of the journal. This service reads it and never
  writes it.

## Consequences

- `observe_run` gains an owner, so `settle_run` has a path to the observation it refuses
  without.
- The Gateway Service gets smaller in principle: observations are not its records. Its manifest
  is unchanged by this decision — see Residuals.
- `scripts/witness_observe.py` is now a script doing a service's work. Either it moves behind a
  declared operation or the repository states why it belongs in scripts.

## Defaults taken

Reversible choices; Bdo may overturn any without defeating the ruling.

- **`observation-receipt` is this service's own record**, matching the sibling pattern in
  console, proofing, and projection, rather than a `terminal-receipt` in the journal. Four
  private receipt types now exist and nothing says how they relate to the Record Service's.
- **Observer registration was removed rather than kept alongside inference.** Registration
  would be a place for the declared relation to survive.
- **`attest-observation` lives here rather than in a separate validation boundary.** The kernel
  `attest` transition needs an owner and this is the nearest one.
- **The `UNDETERMINED` outcome is mine, not Bdo's.** He ruled that independence is inferred
  from the absence of a direct relation. Taken literally that makes an unrecorded relation
  read as independence, so the inference refuses on an incomplete record instead. If this is
  wrong, it is wrong in the safe direction: it refuses rather than admits.
- **The five direct edges are proposed by me.** Bdo named the rule, not the edge set.
- **`request-observation` accepts a `SYSTEM` actor.** An executor asking for its own run to be
  observed is the common case, and asking is not observing.
- **No predicate language is chosen.** The manifest requires predicates be evaluable without
  the executor's report and does not say in what form.

## What would defeat this ruling

- A workable definition of observer independence that this service cannot check — for instance
  one requiring a separate machine or a separate operator organisation. That would make the
  boundary unenforceable rather than merely unbuilt.
- A run whose only durable output is the executor's report, so that no independent reading is
  possible. The service would then refuse everything, which is not a service.
- Evidence that separating observation from the journal forces two records of the same fact,
  which would collapse claim 2.
- An observation that must settle to be useful, which would defeat the claim that observation
  is evidence rather than settlement.

## Judgement queue for Bdo

1. ~~What makes an observer independent?~~ Settled 2026-08-23: inferred when the relation is
   not direct. What remains is the edge set that defines "direct", and whether refusing on
   an incomplete record is the behaviour you want.
2. Do private per-service receipt types stay, or does the Record Service's `terminal-receipt`
   absorb them? Four services now have one and the answer affects all of them.
3. Is the repository's own `verify.py` run an observation of this kind? The MCP surface already
   records it as one.

## Residuals

- No implementation, tests, contracts, or fixtures. The charter, the manifest, and this
  decision are the whole of it.
- No AI-native assessment record; scoring an unimplemented surface would claim evidence nobody
  gathered.
- The Gateway Service manifest still owns `gateway-receipt` and still declares
  `return-receipt` and `read-receipt`. Restructuring it around this decision is a separate
  operation and was not done here rather than done hastily.
- The recursion is unresolved: whatever observes this service cannot be this service, and the
  charter does not solve it. The first observation of it is Red work by a different agent.
- `OPEN-SEAMS.md` was not amended; the receipt-ownership question is recorded in two
  `KNOWN-GAPS.md` files and this decision's judgement queue instead.
