# Product Requirements — Phase I

Status: `PROPOSED · REVISION 2 · NOT OWNER-ACCEPTED`

Supersedes the founding PRD of 2026-08-22, which was written before `GROUND.md`
and `CANON.md` existed and was never re-cut against them.

## What this document is for

Bdo accepted what the product **is** in `GROUND.md` — sixteen claims — and what
it **undertakes to a person** in `CANON.md` — fourteen promises, fourteen
journeys, ten participants. `SPEC.md` holds the predicate a build must satisfy.
`conformance/` holds the fixture that defeats a false one.

This document is the rung between them. It says which promises Phase I is
undertaking now, what a named participant actually gets when a requirement is
met, and what has to be true before the phase is done. It owns nine identifiers,
`PROD-I-1` through `PROD-I-9`, which the oracle, the contracts, the epic tree
and the service charters all address.

The admission test is Bdo's, ruled in `decisions/0052` and recorded in
`CLASSIFICATION.md`, Two requirement ladders:

> **Would failing it mean the phase is not done?**

Anything that fails that test belongs below this altitude. Anything that would
make Soveraeign a *different product* belongs above it, in `GROUND.md`.

### What this document does not own

It does not restate a predicate, a defeating case, an invariant, or a lifecycle.
Each requirement below points at the document that owns those. A rule copied
here would be a second authority for the same rule, which `AGENTS.md` forbids —
and that copy is what the previous revision of this file had become.

| Not here | Owned by |
| --- | --- |
| What kind of product this is | `GROUND.md` |
| What the product promises a participant | `CANON.md` |
| The system boundary and operating model | `SYSTEM.md` |
| The invariants | `CONTRACT.md` |
| Vocabulary, standing ladders, artifact lifecycle | `CLASSIFICATION.md` |
| The predicate each requirement must satisfy | `SPEC.md`, Requirement predicates |
| The fixture that proves or defeats it | `conformance/scenarios.json` |
| The order the work is attempted in | `ROADMAP.md`, F0-F6 |
| What is currently true | `STATUS.yaml`, and the participant baseline |

## What Phase I is for

One person can stand up a node on their own machine, bring a model of their own
choosing into it, and do real work in the same governed record the model works
in — without the model, its provider, or the node's own automation acquiring
authority by operating successfully.

Phase I is finished when that is demonstrated rather than described: by two
materially different model bindings and one human binding, over one unchanged
node, with an outside witness able to reconstruct what happened from the
artifact alone.

## Who it is for in Phase I

Eight of the canon's ten participants are in scope now. `peer-node` waits for
`PROMISE-15`, which is `LATER`. `external-system` has no expectations of its
own. Full descriptions are in `CANON.md`, Who this is for.

| Participant | What they came here to do | Served by |
| --- | --- | --- |
| `human-operator` | Do domain work without learning the node's internals first, and decide the things only a person can decide | 2, 3, 4, 6 |
| `model-operator` | Find out what it may legally do, act inside a live grant, be refused legibly outside one | 1, 3, 5 |
| `model-bringer` | Change which model runs without the record changing hands | 9 |
| `agent` | Choose among reachable operations without widening its own authority | 5 |
| `worker` | One bounded task, one unambiguous input state, a lease that fences it | 5, 8 |
| `witness` | Reach the durable output without relying on the executor's account of it | 7, 8 |
| `domain-owner` | A mandate narrow enough to finish, and a witness who is not themselves | 7, 8 |
| `node-owner` | Stand a node up and know it is theirs | 9 |

## The nine requirements

Each entry says who it serves, which promise it makes good, what that
participant gets, and where the binding predicate and the fixture live. The
`Today` line is the reference participant's standing from
`services/asset/conformance/BASELINE.md` — not a claim about the requirement's
difficulty, and not something this document may advance on its own.

The promise mapping was derived by reading the canon against the nine
requirements. It is a proposal, not owner-accepted, and `Coverage` at the end of
this document records what the derivation found missing.

### PROD-I-1 · Propose

Serves `model-operator` · makes good `PROMISE-04`, `PROMISE-07`

A model session that has never run here before can put a proposal into the
record, and the record keeps who made it, what it read, what it cost, and that
it claims nothing. Nothing is admitted by being written well.

Predicate `SPEC.md` PROD-I-1 · Fixture `CONF-I1-POS` / `CONF-I1-DEF` ·
Today `FAIL` — the proposal carries no content address, no source addresses, and
no cost record.

### PROD-I-2 · Remember

Serves `human-operator` · makes good `PROMISE-05`, `PROMISE-02` · journeys 04, 06

Something put under the node's custody comes back byte-identical, and anything
derived from it can say what it came from, by which reader, at which version,
with what left out. Reading never changes what was read.

Predicate `SPEC.md` PROD-I-2 · Fixture `CONF-I2-POS` / `CONF-I2-DEF` ·
Today `PASS` — the only requirement the reference participant currently keeps.

### PROD-I-3 · Cross

Serves `human-operator` and `model-operator` · makes good `PROMISE-04`,
`PROMISE-05`, `PROMISE-07` · journeys 02, 04

A fact one of them deposits, the other retrieves and uses — through the same
transition, with the origin and the projection visible on both sides, and a
receipt at the end. This is the requirement the phrase "one world" cashes out
to; a surface that reaches state without crossing it fails Phase I.

Predicate `SPEC.md` PROD-I-3 · Fixture `CONF-I3-POS` / `CONF-I3-DEF` ·
Today `FAIL` — no second binding and no fully declared crossing exist.

### PROD-I-4 · Gate and retract

Serves `human-operator` · makes good `PROMISE-07`, `PROMISE-08` · journey 07

Every admission is marked and receipted, and a wrong entry can be countered
without the original disappearing and without pretending the resources came
back.

Predicate `SPEC.md` PROD-I-4 · Fixture `CONF-I4-POS` / `CONF-I4-DEF` ·
Today `FAIL` — the original and the counter both survive, but the counter
receipt does not link the receipt it counters.

### PROD-I-5 · Typed authority

Serves `model-operator`, `agent`, `worker` · makes good `PROMISE-03`,
`PROMISE-04` · journeys 02, 05

Authority arrives as a typed, scoped, revocable grant that the record keeps.
A machine grant may settle verification-typed truth; judgement-typed truth needs
a person. Revoked, expired, out-of-scope and over-budget all refuse in a way the
participant can read.

Predicate `SPEC.md` PROD-I-5 · Fixtures `CONF-I5-POS` / `CONF-I5-DEF` and
`CONF-I5-GRANT-POS` / `CONF-I5-GRANT-DEF` ·
Today `FAIL` — judgement refusal works; the paired typed verification grant and
commit cannot be demonstrated.

### PROD-I-6 · Founder judgement budget

Serves `human-operator` · makes good `PROMISE-09` · journey 08

Work that needs a person's decision queues for one and stops that operation
only. Everything unrelated keeps moving, the waiting operation settles as
unresolved rather than hanging, and where judgement was actually spent is
visible. No invented quota.

Predicate `SPEC.md` PROD-I-6 · Fixture `CONF-I6-POS` / `CONF-I6-DEF` ·
Today `FAIL` — a missing judgement refuses on the spot instead of leaving a
visible pending right and a spend record.

### PROD-I-7 · Independent qualification

Serves `witness` · makes good `PROMISE-10` · journey 09

Someone who was not here can pick up the artifact, find the authority, run the
conformance suite, reconstruct the evidence, and reach a verdict — with no oral
explanation and no reliance on the implementation's account of itself. How long
that took is measured, not assumed.

Predicate `SPEC.md` PROD-I-7 · Fixture `CONF-I7-POS` / `CONF-I7-DEF` ·
Today `FAIL` — no clean-room witness run and no competence measurement exist.

### PROD-I-8 · Joint sign

Serves `witness`, `domain-owner` · makes good `PROMISE-11` · journey 09

A claim that was ratified once gets checked again at runtime, and the check
names its validator, version, inputs and run, and returns `reproduced`,
`dissented`, or `unattestable`. A dissent stops the claim being effective
without rewriting the history of its ratification.

Predicate `SPEC.md` PROD-I-8 · Fixture `CONF-I8-POS` / `CONF-I8-DEF` ·
Today `FAIL` — general runtime attestation is not implemented.

### PROD-I-9 · Bring your own model

Serves `model-bringer`, `node-owner` · makes good `PROMISE-01`, `PROMISE-02`,
`PROMISE-06` · journey 01

From one unchanged node and one input state, two materially different model
bindings — one of them the owner's own — find and attempt the same named
operation, through the same transitions, authority checks and receipts. Each run
records its binding, adapter, provider, model, version, runtime, host, input
projection, data boundary, usage and cost. Losing a provider costs the provider,
not the record. An unavailable model refuses where you can see it; there is no
silent substitution.

Predicate `SPEC.md` PROD-I-9 · Fixture `CONF-I9-POS` / `CONF-I9-DEF` ·
Today `FAIL` — no model-binding contract and no two-model portability run
exist. `contracts/kernel-transitions.json` declares `invoke_model` and no kernel
implements it.

## The two-binding proof

One human-facing binding and two materially different model bindings must run
the same authoritative transitions and return compatible receipts. One of the
two models arrives through the BYOM contract. Three bindings in total: it is
same-world human/model parity and two-model substitutability proved at once,
because either alone is cheap and the pair is not.

## Out of scope for Phase I

- A graphical production interface.
- Automated external-world effects.
- World rollback.
- Distributed consensus, or federation between nodes (`PROMISE-15` is `LATER`).
- A universal ontology or a frozen encoding.
- Importing a predecessor implementation wholesale.
- Optimizing performance ahead of semantic conformance.
- Treating the chosen name as evidence of maturity or public clearance.
- Treating any one subsystem — Gauge, Definition, Atlas, Asset — as the product.

## What finished looks like

Phase I exits when all of the following hold at once:

1. every normative predicate in `SPEC.md` has a positive and a defeating fixture;
2. the applicable fixtures run through one human-facing binding and two
   materially different model bindings;
3. an independent observer can reconstruct the receipts without help;
4. open judgement calls are visible rather than absorbed; and
5. Bdo ratifies Phase-I operational acceptance.

Requirements move `OPEN -> BUILT -> WITNESSED -> RATIFIED` — the artifact
lifecycle defined in `CLASSIFICATION.md`, distinct from the operational record
standing in `SPEC.md`. `BUILT` is a claim. `WITNESSED` needs evidence from a path
the builder did not control. `RATIFIED` needs the declared right. No participant
advances a requirement on its own report.

## Coverage

Re-deriving these nine against the canon found two Phase-I promises that no
requirement in this document carries. Both are owner judgement: widening what
Phase I requires is product intent, and `conformance/requirements.py` hardcodes
nine, so minting a tenth changes the oracle as well as this file.

| Uncovered | Journey | Where it stands today |
| --- | --- | --- |
| `PROMISE-12` — work carries across a session, operator, or model boundary | `JOURNEY-03` | The Console continuity path is built and self-tested. It is delivering a Phase-I promise that no requirement asks for. |
| `PROMISE-16` — decide against an exact version, and have someone who was not you counter it | `JOURNEY-11` | Proofing is a boundary with no implementation. `GROUND.md` says explicitly that proofing belongs in "a journey and `PRD.md`"; the journey exists and the requirement does not. |

Two more are carried thinly rather than not at all, recorded here so the
thinness is visible now rather than discovered later:

- `PROMISE-03` — finding out what can be asked — leans on PROD-I-7, which is
  about qualifying the *requirements*, not about a participant discovering its
  *operations*. `GROUND-006` already cites PROD-I-7 for this.
- `PROMISE-10`'s measurement half — how long a fresh participant took to become
  useful — sits inside PROD-I-7's predicate but has no fixture that fails when
  the measurement is absent.

Three admissible resolutions for each, and choosing among them is Bdo's: mint a
requirement, record the promise as carried by an existing one and say where, or
move it out of Phase I.

## Standing

`PROPOSED`. Drafted by Claude on 2026-08-28 at Bdo's direction, after he observed
that the founding PRD had stopped being a PRD. The nine identifiers, their scope,
the two-binding proof, the non-goals and the exit conditions are carried forward
unchanged in meaning from the 2026-08-22 revision. What changed: the predicates
and defeating cases were removed as duplicates of `SPEC.md`, and the promise,
journey and participant joins were added.

Nothing here is owner-accepted until Bdo accepts it. `PRD.md` is a root governing
document and sits outside the standing landing grant
(`contracts/standing-grants.json`), so this revision lands by his hand and not by
the loop.

What would defeat this revision:

- a requirement here that fails the admission test — failing it would not mean
  the phase is unfinished;
- a requirement that makes good no promise in `CANON.md`, which would mean
  Phase I is building something the product does not undertake;
- a `PHASE_I` promise carried by no requirement and not recorded under
  `Coverage`;
- a predicate or defeating case restated here rather than cited, which is the
  defect this revision exists to remove.
