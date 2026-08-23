# 0024 · Drain the founding decision queue

Status: `OWNER-DIRECTED OPERATING RULINGS · ACCEPTANCE POLICY APPLIES`

This record resolves the open decision queue that was preventing autonomous bounded work. The
rulings are intentionally conservative: they choose a testable Phase-I path, preserve evidence and
owner acceptance, and prefer reversible implementation over further pre-approval.

The owner gate follows decision 0023: agents may work toward these rulings without asking for
intermediate approval. Owner acceptance is requested only over evidenced results.

## Rulings

### O1 · Name collision screening

**Ruling:** `Soveraeign` remains the accepted working product/repository name for development and
private/local operation. No agent may claim legal clearance. Public commercial release that depends
on trademark/domain/legal clearance is an external acceptance item, not a blocker on Phase-I
engineering.

**Standing:** resolved for implementation; external/publication clearance remains a separate
pre-release obligation.

### O2 · Phase-I engineering baseline

**Ruling:** accept Python 3.11+, SQLite for the local operational record, filesystem content-addressed
payload custody, JSON/JSON Schema Draft 2020-12 at machine boundaries, dependency-light unittest,
and local-process/CLI-first operation as the Phase-I reference baseline. These are mechanisms, not
semantic authority, and may be replaced behind proved contracts.

### O3 · Bootstrap authority for the first attestor

**Ruling:** bootstrap trust is explicit, local, and finite. The first attestor is admitted by a
founding `BootstrapGrant` accepted by the owner and pinned to an exact attestor identity, validator
version, capability, scope, validity, and artifact revision. It may attest verification-typed claims
only and cannot ratify judgement. Every later attestor must resolve through ordinary authority and
identity lineage; bootstrap is not ambient root permission.

### O4 · Historical reproduction versus present applicability

**Ruling:** represent them separately. An `Attestation` is immutable historical evidence about an
exact claim/input/run. `CurrentEffectiveness` is a rebuildable evaluation over the ratified claim,
latest applicable attestations, supersession, expiry, retraction, and policy. A historical
`REPRODUCED` result is never rewritten when applicability changes.

### O5 · Gauge governance and authority

**Ruling:** Gauge may measure and project governance state, authority pressure, unresolved rights,
coverage, and evidence strength, but it owns none of them. Gauge reads typed authority/evidence
records and reports dimensions with provenance. A Gauge score cannot grant authority, standing, or
admission and cannot collapse evidence strength into right-to-act.

### O6 · Unattestable claims in effective state

**Ruling:** when a claim's effectiveness policy requires runtime attestation, `UNATTESTABLE` blocks
that claim from becoming or remaining `EFFECTIVE` while preserving historical `RATIFIED` standing.
Claims whose policy does not require attestation may remain effective for non-executable semantics,
but the absence of attestation must remain visible. No silent degrade from required to optional.

### O7 · External effects and compensation

**Ruling:** Phase I refuses real `EXTERNAL_WORLD` effects. Isolated test doubles are allowed only
when their observable effect is record-local. Later phases use forward compensation/counteraction:
record the external occurrence, the attempted remedy, what remains changed or consumed, and the
resulting evidence. Never claim world rollback.

### O8 · Semantic cold-start observation

**Ruling:** accept the chosen semantic cold-start observation shape: a fresh participant must perform
a named domain task against exact held data, produce attributable outputs/receipts, and demonstrate
that it understood enough semantics to operate without oral history. Schema validity alone is
insufficient. The existing FOUND-010 execution is admissible evidence; future qualification should
measure time, interventions, refusals, and corrections.

### O9 · Classification vocabulary

**Ruling:** accept `CLASSIFICATION.md` as the canonical vocabulary contract for the current phase,
subject to normal versioned change. System/Federation/Node/Service/Component, role distinctions,
Binding/Adapter/Worker/Witness, authoritative record versus Projection, and runtime semantics are
canonical unless defeated by evidence.

### O10 · Phase-I logical specification

**Ruling:** accept `SPEC.md` as the Phase-I logical specification **with the sovereignty
interpretation from decision 0023**. Judgement is not forbidden to models. A participant may decide
for its own bounded participation; binding another participant, owner-held product intent, or shared
authoritative state as judgement requires the applicable right. Existing typed authority gates
remain required at consequential shared-state transitions.

### O11 · Proofing Service boundary

**Ruling:** accept Proofing as the second service boundary after Asset. Proofing owns sessions,
rounds, annotations, comparisons, assignments, requested changes, decision proposals, authorized
decisions, dissent, and history. It references exact Asset versions and never becomes payload
custody or a second asset authority.

### O12 · BYOM contract

**Ruling:** accept the current exact ModelBinding dimensions and the two-model Phase-I proof shape:
binding, adapter, provider, provider kind, model/version, runtime/version, host, interface contract,
capabilities, data boundary, input projection/omissions, usage, cost, fallback policy, and created-at
must remain attributable. `LOCAL_ONLY`, `REDACTED_REMOTE`, and `REMOTE_ALLOWED` are accepted Phase-I
data-boundary modes. Fallback is explicit and separately receipted. One owner-supplied model and one
materially different model must attempt the same named operation through the same kernel semantics.

### O13 · SDLC operating loop

**Ruling:** accept the three tiers, stance dyads, concern-registry derivation, and Red-gated release
requirement, modified by decision 0023: `RIGHT` is owner **acceptance**, not pre-approval of work.
Control may sequence and execute bounded work without a fresh owner grant for each implementation
choice. Blue still cannot witness itself; Red still cannot accept owner judgement.

### O16 · Typed ticket workflow and outward coordination

**Ruling:** accept `contracts/ticket-transitions.json` as the typed ticket workflow. Authorize normal
repository-local coordination needed to operate it: branch/PR creation, issue metadata maintenance,
labels, project-field synchronization, and proposed branch-protection configuration. Changes that
could lock the owner out, destroy history, expose secrets, publish externally, or materially alter
repository access remain protected owner boundaries and must be presented for acceptance before
application when not safely reversible.

### O17 · Sov agency envelope

**Ruling:** accept Sov as the default operating profile and Control candidate. Sov owns its bounded
participation: attention, context selection, sequencing, reversible implementation choices,
proposal, execution within available capabilities/effect envelope, refusal, repair, and handoff. Sov
does not own Bdo, owner acceptance, public product intent, another participant, or shared authority.
It need not escalate merely because a choice involves judgement; it escalates when the choice would
bind an owner-held boundary rather than itself.

### O19 · Verification-engagement ticket kind

**Ruling:** accept `verification-engagement` as a ticket kind with stable `engagement_id`, pinned
target PR/revision, declared scope/effect/budget, independent operator identity, findings,
reproduction path, convergence criterion, and settlement receipt. Construction identity cannot
satisfy the independent Red role for the same artifact.

### O20 · Compiled kernel transition contract

**Ruling:** accept `contracts/kernel-transitions.json` as the compiled machine-readable statement of
`SPEC.md` transition semantics. Ticket workflow, Asset, Proofing, workers, bindings, and later
services must converge onto this shared transition contract rather than retain private standing or
settlement semantics. The compiled form is subordinate to the logical specification and cannot add
new authority by encoding it.

## Reserved O14, O15, O18

The current `STATUS.yaml` explicitly says these identifiers were reserved for questions on
concurrent branches and does not state their questions. They are therefore **not open decisions in
the current authoritative record** and no ruling is invented here. If those branches introduce a
material decision later, it enters as a new attributed question and is handled under the
acceptance-not-approval policy.

## Operating consequence

After this record lands, unresolved owner judgement should not be used as a generic blocker on
ordinary Phase-I implementation. Controllers should:

1. turn the ruling into a contract/fixture or bounded implementation;
2. create observable evidence;
3. run Blue and, where standing requires it, independent Red/witness work;
4. package a concise acceptance presentation when an owner-held outcome is genuinely reached;
5. continue with another eligible concern while acceptance is pending.

## Demotion

Any ruling is revisable when a defeating observation shows that it violates a stronger invariant,
creates hidden authority, loses reconstructability, or makes the product less locally sovereign.
Revision adds a new decision; it does not rewrite this history.
