# Open Seams

These seams are carried deliberately. An implementation must not choose a side
silently.

## S1 · Corpus revision alignment

`HANDOFF-SPEC.md` and introductory text in `SEAM-REGISTER.md` refer to earlier
PRD revisions, while the evidence corpus contains a rev-6 Phase-I amendment and
PROD-I-8. Canonical references must be rechecked against the exact source
digests before freeze.

## S2 · Reproduction versus applicability

An attestation needs enough stable input to reproduce a historical run while
also representing whether the claim applies to current source state. These are
not one predicate and may need separate outcomes or linked attestations.

## S3 · Authority in the Gauge

The existing Gauge emphasizes reachability, commitment, provenance, and
retraction. It can still describe a reachable and traceable surface whose
authority is unsafe. Governance must influence the verdict without becoming a
confidence score or merging evidence with authority.

## S4 · Unattestable effectiveness

The seam register allows non-executable ratified claims to become effective on
their hands while marked unattestable. The exact conditions, visibility,
expiration, and operational consequences remain unspecified.

## S5 · Cold-start semantics

Structural completeness and schema validity are measurable but do not establish
semantic competence. Phase I needs a watched task whose success a fresh witness
can determine independently.

## S6 · Correction measurement

Some source language calls for a correction rate while the current spec records
a count. The denominator, interval, and interpretation must be fixed before the
metric can govern a gate.

## S7 · Definition and Gauge operator bindings

Earlier subsystem proposals describe Claude-left/Bdo-right behavior directly. They must be
re-derived through typed hands, machine verification, owner judgement, and
runtime attestation so a named model or person is not hardcoded into the law.

## S8 · Evidence portability

The corpus is readable but some cited raw finds, reviews, and conformance seeds
are not present as individual source files. Missing sources must be recovered,
or dependent claims must be marked unverifiable rather than silently trusted.

## S9 · External effects

Record-local retraction is defined. Irreversible resource consumption and
external-world mutation need explicit Phase-I refusal/isolation rules. World
rollback or compensation remains later work.

## S10 · Product boundary

The system is currently described as an enterprise operating environment. The
boundary between a primary enterprise application and a constitutional runtime
over existing applications must be tested through the first real subsystem rather
than decided by metaphor alone.

## S11 · Red-lane inputs — closed 2026-08-23

`SDLC.md` rule 6 said Red operators receive the contract, the claimed
invariants, and the built artifact, not the builder's tests, plan, or
assumptions, while `.github/workflows/qa-lanes.yml` handed the Red action the
whole pull-request diff. Bdo chose the independent-verification reading: the
builder's tests are part of the artifact under attack, readable and never the
oracle. `SDLC.md` rule 6 now says so; the workflow already did.

## S12 · Ratification mechanism

`decisions/0016` and `.github/CODEOWNERS` say ratification enters the
repository through code-owner review on `STATUS.yaml`, `decisions/`, and the
governing set. `AGENTS.md` requires a typed, scoped, live grant at the
operation boundary and says only Bdo ratifies judgement. Whether a CODEOWNERS
approval is that grant, or an explicit recorded decision is required, is
unsettled; 0016 is still `PROPOSED`.

Owner input, 2026-08-23: Bdo will rarely interact with GitHub directly, so a
code-owner review click cannot be the owner's ratification surface. The
surface has to be a Human Binding the owner actually uses; the Console
Service charter (`services/console/CHARTER.md`, judgement requests) is the
chartered home for it. 0016's mechanism stands as a proposal until a decision
amends it. This seam stays open on the mechanism, not on the direction.

## S13 · Retraction in the Soveraeign bar

`AI-NATIVE.md` requires `FULL` on reachability, commitment, provenance, and
the admitted effect envelope for `SOVERAEIGN_QUALIFIED`, and omits retraction,
while the same document and `decisions/0006` call it "the all-`FULL`
Soveraeign bar". Whether retraction must be `FULL` within the phase's effect
envelope is a tightening only the owner can make.

## S14 · Two owners of the asset projections

`services/asset/CHARTER.md` line 74 names an "SQLite FTS projection" and a
`graph-projection` port inside the Asset Service, while
`services/projection/CHARTER.md` charters a sibling service that owns text,
graph, and vector projections over the same records. Until `decisions/0021`
is ruled, the Asset Service's `search` and `neighbors` are a compatibility
path, not a second retrieval surface. Which service keeps `rebuild-projection`
for the Asset Service's own two tables after ratification is Bdo's call.

## S15 · Judgement request and unblock request

`services/console/CHARTER.md` charters a judgement request: a queued request
for an owner-held right, `IN_LOOP` or `ON_LOOP`, resolved only under a live
`JUDGEMENT` grant. `contracts/issue-metadata.schema.json` now admits an
`unblock` ticket whose `requested_provision` is `judgement`, addressed to the
owner. These are one record seen from two surfaces: the coordination registrar
and the operator console. One must project from the other; neither may become
a second queue of owner rights. Which is the source is a charter question for
the Console Service, carried here until it is written down.

## S16 · Decision-number allocation across branches

Decision records mint their numbers on the branch that drafts them, and no
mechanism reserves a number across branches. Observed 2026-08-23: `0014` and
`0015` each name different decisions on `feat/federation-harness-and-hardening`
(console boundary, scheduled runs) and PR #38 (local infrastructure, deployment
pattern); `0019` names three decisions (kernel transition contract, settled on
`main`; verification channels on this branch; shared kernel reference on PR
#61); `0020` names three more (federation harness, this branch; owner seat
topology, PR #68; verification channels again, PR #64 — the same decision this
branch carries as `0019`, under a second number). Governing text cites
decisions by number, so a collision silently redirects a citation when the
other branch lands. Numbers already on `main` are settled; every other claimant
renumbers at rebase. The open choice is the allocation mechanism — reservation
through the `decisions/0016` coordination registrar, or a
next-free-number-at-rebase rule — and which surviving record keeps each
contested number is Bdo's.

Movement 2026-08-23: `0020-owner-seat-topology` landed on `main` via pull
request #68 and settled that number; this branch renumbered its claimants to
`0025` (verification channels) and `0026` (federation harness). Still open:
PR #38's `0014`/`0015`, PR #61's `0019`, PR #64's duplicate copy of the
verification-channels record, and the allocation mechanism itself.

Two further claimants observed 2026-08-23 by reading the branches directly, both
still unmerged and both certain to redirect a citation if they land unchanged:
`docs/principal-identity` (pushed) carries `0021-principal-identity` and
`0022-stack-durability-row`, while this branch already spends `0021` on the
semantic cold-start task and `0022` on the story ticket kind — a double
collision on one branch. `feat/acceptance-gate` (pushed, fifteen commits ahead
of `main`) carries the acceptance decision under two numbers at once,
`0023-acceptance-not-approval` and `0028-acceptance-not-approval`, and this
branch spends `0028` on history-as-lineage. Neither branch is wrong to have
minted a number; the seam is that nothing told them the number was taken.

## S17 · A kernel refusal code the evaluator cannot emit

`contracts/kernel-transitions.json` lists `INCOMPLETE_PROPOSAL` under
`submit_proposal`, and `SPEC.md` defines it. Nothing produces it:
`scripts/sovkernel/transitions.py` refuses every absent precondition with
`MISSING_PRECONDITION` and emits `INCOMPLETE_PROPOSAL` nowhere. Observed
2026-08-23 while registering the Console Service in `contracts/kernel-parity.json`,
where the correspondence had to be declared against the refusal the kernel
actually returns rather than the one the table advertises.

Three readings, and which one holds is not this seam's to settle:
`INCOMPLETE_PROPOSAL` is a finer refusal the evaluator has not yet implemented;
or it is a synonym `MISSING_PRECONDITION` has since absorbed and the table
should drop it; or `submit_proposal` needs a completeness check distinct from
precondition presence. `decisions/0034-spec-transition-refusal-codes.md` already
moved this vocabulary once and is the nearest owner. Until it is settled, a
declared refusal code no participant can be graded against is a gap in the
contract, not in the participants.

## S18 · Two layers named gateway

`bindings/mcp/gateway.py` carries the name for the local tool-surface binding.
`services/gateway/` now carries it for the node's door
(`decisions/0040-the-declared-service-surface.md`, Ruling 5). Observed 2026-08-23 while
wiring the service manifest check into `scripts/verify.py`, where the check named "MCP
gateway binding" and the new service both appeared in one run.

The two are not the same thing. The service resolves a logical endpoint, checks a grant, and
records what crossed; the binding translates one transport's calls into whatever it reaches.
Read one way the binding is a transport into the service and the shared word is accurate; read
another way one of them should be renamed before either is built, because an operator reading
a receipt cannot tell which gateway refused.

`NAMING.md` owns the collision screen and Bdo owns naming. Nothing is renamed here.

## S19 · Who publishes: an operator or a seat

`contracts/public-projection.schema.json` requires every published entry to name a
`published_by` seat, because publishing is an outward effect and `decisions/0039`
rules it attributable to a seat the node holds. `services/console/contracts/publication.schema.json`
records `published_by` as an operator id, because that is what every other console
record carries and the Console Service has no seat model. Observed 2026-08-23 while
building the publication record the projection was written to read.

Nothing bridges them. `contracts/fixtures/seat-topology.reference.json` does carry
`occupant.actor_id`, so the mapping exists as data, but it is a kernel fixture and no
service reads it; a service that did would be reaching past a contract into another
layer's reference file.

Three readings, and this seam does not settle which: the console should carry a seat
alongside its operator id, and something must then check the operator occupies it; or
the projection builder is a kernel-tier component that holds both and resolves the
mapping there; or operator id and seat are the same identity at different altitudes and
one of the two contracts is naming it wrongly. `decisions/0020` owns seat topology and
`decisions/0039` owns the outward surface; neither has been asked.

Until it is settled, a public projection built from console records cannot fill
`published_by` honestly, and the fixtures that exercise it supply the seat by hand.

## S20 · The gate counts its checks and never says which

`scripts/verify.py` reports a check count and `scripts/verify_bootstrap.py` pins
the files that must exist, but nothing compares the *set* of checks between two
runs. A check removed and a check added in one edit leaves the count unchanged
and the gate green, so coverage can move without anything noticing.

Observed 2026-08-23. An uncommitted edit to `scripts/verify.py` removed the
`node registry` check and added `operation surface page` in the same diff. The
count went 21 to 21. `python scripts/sov_node.py validate` still passed, the
script and its fixture both still existed, and nothing in the repository would
have reported that the node registry had stopped being checked. It was noticed
because a session reading the diff by hand asked why two hunks were paired, not
because any gate said so.

Three readings, and this seam does not settle which: the check set is itself a
projection and should be checked in and diffed like `contracts/kernel-parity.json`
is; or each check should declare the artifact it defends so a removal is visible
as an undefended artifact rather than as an absent name; or this is properly a
review responsibility and a repository that lints its own gate is checking the
checker without end. `decisions/0025-verification-channels-and-merge-authority.md`
owns what verification is allowed to claim and is the nearest owner.

Numbering note: minted on `test/mcp-gateway-observation` off `c296c25`.
`OPEN-SEAMS.md` S16 carries the allocation seam that makes this note necessary;
a concurrent branch may hold its own S20.
