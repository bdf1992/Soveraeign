# 0048 · Principal identity: requirements

Status: `PROPOSED · CONTRACT, FIXTURES, AND CHALLENGE RUNTIME BUILT`

Compiled by Claude from Bdo's direction (2026-08-23 conversation): identity is
principal-based, graded by the crossing it lives at, who or what controls it,
and how many hops it sits from human interfacing; instances first; claims
before keys; each model version its own principal; every identity linked to
something already in the system; recovery by normal practices expressed as
receipted transitions. Builds on `decisions/0020-owner-seat-topology.md`.
Requirements are proposals; nothing here is implemented or ratified.

## Definition

A **principal** is a registered identity that can be named as an actor. Every
`actor_id` in an event, receipt, occupancy claim, or grant resolves to exactly
one principal. Humans, model operators, model instances, workers, and system
processes are all principals; being one grants nothing (C3).

Every principal carries a derived **identity grade** with three axes:

- **controller** — the principal one step up that can act for it, re-key it,
  or revoke it. Only the root principal has none.
- **hop distance** — hops from human interfacing. The root human is hop 0;
  anything a human directly operates is hop 1; anything that launches is one
  more. Never asserted: always derived by walking the controller chain, so a
  lie about distance is visible rather than possible.
- **crossing class** — where the principal exists relative to the node
  boundary, using the existing crossing classes (`ENGINEERING.md`): in-node,
  or across a declared boundary to a provider or another node.

Authority remains grants-only. The grade gates **eligibility** — which seats,
capabilities, and effect classes a principal may even be granted — and
eligibility rules are predicates over the grade, checkable by machine.

## Requirements

Each requirement will need one positive and one defeating conformance case
before implementation (`AGENTS.md`, Implementation order). The defeating case
is named now so the requirement is testable before it is code.

**ID-1 · No orphan actors.** Every `actor_id` on a consequential record
resolves to a registered principal. *Defeat: a receipt naming an unregistered
actor is accepted without a named defect.*

**ID-2 · Anchored existence.** Every principal links to a record already in
the system — a decision for a human, a model binding for a model operator, a
launch or delegation event for an instance — and every anchor chain
terminates at the root principal. *Defeat: a free-floating principal with no
anchor chain participates anyway.*

**ID-3 · Derived distance.** Hop distance is computed from the controller
chain, never stored as a claim. *Defeat: a principal presents a hop count
lower than its chain derives and the difference goes unnamed.*

**ID-4 · Controlled and revocable.** Every non-root principal names its
controller; revocation is a receipted transition by the controller; a revoked
principal's history stays on record. *Defeat: revocation erases the
principal or its acts; or a principal with no controller is not the root.*

**ID-5 · Instances are principals.** Every session or launched agent gets an
ephemeral instance principal at mint time, carrying a delegation record to
the durable operator principal that launched it. Attribution reads: this
instance, of this operator, launched by that controller. *Defeat: two
sessions share one instance identity; or an instance acts after its lease or
session ends.*

**ID-6 · One principal per model version.** A model operator principal is
bound to an exact model identity and version; a different version is a
different principal, related by a lineage link. *Defeat: a version or
provider swap continues under the same principal without a new attributed
identity (the silent-fallback failure, `BYOM.md`).*

**ID-7 · Claims before keys.** Occupancy and identity claims are journaled
attributably with actor, basis, and time; verification status is explicit;
an unverified claim is never presented as verified. Cryptographic
verification is added when a conformance case demonstrates a forged claim,
not before (`ENGINEERING.md`, Selection rule). *Defeat: an unverified claim
is silently upgraded or displayed as verified.*

**ID-8 · Identity is never authority.** No grade, hop count, or verification
status confers a capability; every consequential transition still requires a
live typed grant. *Defeat: a hop-0 human acts without a grant and the act
commits.*

**ID-9 · Eligibility is a readable predicate.** Rules like "this seat's
settlement hand requires hop <= 2", "EXTERNAL_WORLD effects require hop-0
approval", or "a principal across a provider boundary may not hold
JUDGEMENT" are declared data, evaluated at the grant boundary, and their
refusals are receipted. *Defeat: a seat is occupied or a grant issued to a
principal failing its declared predicate, without a named defect.*

**ID-10 · Recovery is normal practice, receipted.** Credential loss is
revoke-and-reissue by the controller; support and administration are the
controller one hop up; escalation is the judgement queue; operations roles
are orchestration seats. All of them are ordinary receipted transitions.
*Defeat: a recovery path that bypasses receipts or the controller chain.*

**ID-11 · Root recovery is pre-declared.** The root principal has no
controller, so its recovery cannot be a support path. A break-glass
declaration — sealed successor, recovery quorum, or another form Bdo
chooses — must exist before verification (keys) makes loss possible.
*Defeat: root credential loss with no declared recovery path.* This is the
one requirement whose content only Bdo can supply; it is queued, not
defaulted.

## Verification mechanism: challenges (magic links)

Bdo's direction (2026-08-23): verification is passwordless. The mechanism is
the challenge — the magic-link pattern expressed in primitives the kernel
already has: mint a one-time token bound to a principal and a declared
channel with a short expiry (a lease with a fence and a TTL); deliver it over
that channel (a crossing, receipted); present it once inside its window to
upgrade a claim `UNVERIFIED -> VERIFIED`, with the challenge receipt as the
`verification_basis`. Recovery is the same door: a lost credential is a fresh
challenge to the declared channel, issued by the controller.

Phase I delivers over local channels only — the console session, the node
filesystem, the OS account. Email or SMS delivery is an `EXTERNAL_WORLD`
effect and is refused while `no_external_effects_in_phase_i` stands (O7);
the mechanism does not change when external channels are admitted.

The plain cost: the channel is the real key. Below the root that is
acceptable — a compromised channel is revoked and re-anchored by the
controller. For the root it is the crown: whoever controls the root's
recovery channel can become the root. Choosing that channel is ID-11's
content and remains Bdo's blank.

**ID-12 · A challenge is a one-time leased proof.** Minted with a fence and
expiry; presented at most once, inside its window; every mint, delivery,
presentation, and refusal is receipted. *Defeat: a token verifies twice, or
verifies after expiry.* (Executable case waits for implementation; declared
now.)

**ID-13 · Verification only over a declared channel.** A principal's
verification channel is part of its record, anchored like everything else;
a `VERIFIED` claim must name a challenge over a declared channel, and in
Phase I an external-kind channel cannot verify anything. *Defeat: a claim
verified over a channel the principal record does not declare, or over an
external channel while Phase I stands.*

**ID-14 · Recovery is a fresh challenge, not a special door.** Credential
loss below the root is re-challenge by the controller to the declared
channel, receipted like any transition. *Defeat: a recovery path that mints
no challenge or bypasses the declared channel.*

## ID-11 examined: the stack does not answer it, and cannot

Asked directly — does the Phase-I stack answer "which channel recovers the
root?" — the answer is no, for a structural reason rather than a missing
library. Every channel the stack offers (`console-session`, `local-file`,
`os-account`) lives inside the node's own failure domain. A recovery channel
must survive the loss it recovers from, so recovering the node by way of the
node is circular in exactly the shape `decisions/0020` removed from Owner.
`ENGINEERING.md` is consistent with this: `identity provider` is listed under
*not yet selected*.

Examining it also shows ID-11 was one question hiding three, only one of which
is technological:

**ID-11a · Credential lost, node intact.** Answerable today with no new
technology: sealed recovery secrets, generated from the standard library,
returned once, held by the human outside the node, redeemable single-use.
Physical custody sits outside the digital failure domain without being an
`EXTERNAL_WORLD` effect — no network crossing, no external system mutated —
so O7 does not block it. Built: `services/identity/.../recovery.py`.

A recovery secret is the inverse of a challenge and needs its own rules. A
challenge is short-lived and delivered on demand; at the moment recovery is
needed, the channel one would deliver over is the thing that was lost. So a
recovery secret is delivered once at enrollment and has **no expiry** — which
is not an oversight of ID-12 but its deliberate inverse, since an expiring
recovery secret expires exactly when nobody is watching. What replaces expiry
as the bound: single use, a finite set, and revocation of the whole set at
once.

**ID-11b · Node lost or destroyed.** Not an identity problem, and the stack
does not answer it either. `SPEC.md`'s fault model reaches power loss
(committed versus attempted) and stops there; no backup, restore, or custody
provision exists anywhere in the repository. Root identity would re-establish
from a restored journal plus the physically held secret — but nothing
currently produces a restorable copy. Recorded as `OPEN-SEAMS.md` S11.

**ID-11c · Root occupant unavailable.** Succession. No technology answers
this: it needs a named successor principal and a declared condition under
which succession fires. Pure judgement, and only Bdo can supply it.

**What the system owes regardless of the ruling.** `Recovery.unenrolled`
names every principal with no live recovery, root first, and states the
consequence plainly: for the root, no recovery exists and none can be
supplied afterwards, because there is no controller above it to enroll one.
A root with no recovery is not a defect the system can repair, so the only
honest handling is to report it continuously rather than discover it at the
worst possible moment.

## Bootstrap (O3, fed rather than solved)

The root principal is self-certified: trusted because `decisions/0001` seated
its occupant, not because anything attests it. Every other principal chains
from that anchor. O3's question — what attests the first attestor — is
answered by admission: nothing does, and the admission is on record.

## What this decision does not do

- No implementation, schema, or registry file yet; those are the next
  bounded operations below.
- No cryptography, no external identity provider, no real-world linkage.
  Linkage is in-system only (ID-2).
- No new authority. Eligibility narrows who may receive a grant; it never
  replaces one.

## Next bounded operations

Done: `contracts/principal.schema.json` with positive and defeating fixtures
including grade derivation and channel cases; the ID-1 orphan-actor check as
a fixture-level guard; retroactive adoption in
`reports/2026-08-23-principal-adoption.md`.

Also done: the challenge runtime (ID-12, ID-13, ID-14) in
`services/identity/`, with sixteen positive and defeating cases — replay,
expiry, stolen token, revoked principal, external channel, and a case
reading every emitted record back to prove no token ever enters one. Its
placement is provisional and its charter says so: the lifecycle is
storage-free precisely so judgement 3 can move it without changing
semantics.

Remaining:

1. Wire the ID-1 orphan-actor check into the kernel receipt path, once Bdo
   picks service-versus-registry (judgement 3).
2. Eligibility predicates (ID-9) as declared data over the derived grade,
   evaluated at the grant boundary.
3. Bind the challenge runtime to the principal registry, so presenting a
   challenge actually writes `verification: VERIFIED` with its basis. Held
   deliberately: that binding is where identity stops being a proposal, and
   ID-11 (which channel recovers the root) should be answered first.

## Judgement queue for Bdo

1. Ratify, amend, or strike the three grade axes and requirements ID-1..10.
2. ID-11: choose the root break-glass form — with magic links this
   concretely means choosing the root recovery channel, the single most
   security-critical selection in the system.
3. Is principal identity a service boundary (`services/identity/`) or a
   kernel-level registry? The service construction rule cuts either way.
4. Confirm the hop-0 convention (the root human) or set hop 0 at every
   human principal.
