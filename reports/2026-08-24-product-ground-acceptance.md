# Product Ground and CANON-2 · acceptance presentation

Date: 2026-08-24
Branch: `feat/federation-harness-and-hardening`
Author: Claude, at Bdo's direction
Standing: `PROPOSED`. One owner action decides it: `ACCEPT`, `REJECT`, `STRIKE`, `REDIRECT`.

This is not a discovery report. The discovery is
`reports/2026-08-24-product-canon-attribution-discovery.md` and it still stands. This
paper presents a corrected semantic layer for acceptance and shows what accepting it
would constrain.

Two artifacts are on the table:

| Artifact | What it says | Files |
| --- | --- | --- |
| **Product Ground** `EPOCH-1 / GROUND-1.0` | what product Soveraeign is — 16 claims | `GROUND.md`, `contracts/product-ground.json` |
| **Product Canon** `CANON-2.0` | who it is for and what it undertakes — 10 participants, 15 promises, 14 journeys | `CANON.md`, `contracts/product-canon.json` |

`CANON-2` supersedes the never-accepted `CANON-1`. Accepting the ground is the larger
decision; the canon can be redirected without touching it.

Everything below is checked: `python scripts/sov_canon.py check` refuses a promise
deriving from no ground claim, a ground claim no promise carries, a promise that is
canonical only because something was built that way, an identifier declared in a record
and absent from the document that owns its wording, and a capability the canon names that
no service manifest declares.

---

## A · The product in one paragraph

> Soveraeign is a locally sovereign enterprise environment in which people and models are
> operators of the same governed world. You bring your own model into a node you own or
> are authorized to use; the node — not the provider — keeps your record, your authority
> and your continuity. A participant finds out what it may do by reading the node rather
> than by being told, acts only by crossing a declared operation, is refused legibly when
> it may not, and leaves a receipt either way. Work handed to an agent is checked through
> a path the agent did not control. Corrections counter the record instead of erasing it.
> What every hour and every token was spent on stays answerable, upward to the intention
> that justified it and downward to what has actually been spent realizing it.

Every clause of that paragraph is one of the sixteen ground claims. Nothing in it is
aspirational wording: `GROUND.md` carries each clause with the governing address its
language already lives at, and with the answer to what would change if it stopped being
true.

---

## B · Product Ground

Sixteen claims. The test each one passed:

> If this statement became false, would we merely implement Soveraeign differently, or
> would we be building a materially different product?

Only the second belongs. Sixteen claims stand under 102 declared operations, nine `PROD-I`
requirements and eight services — that ratio is the point of the layer, not an accident of
drafting. `GROUND.md` carries each in full; this is the index.

| Id | Claim | Grounded in | If it changed |
| --- | --- | --- | --- |
| `GROUND-001` | Custody of memory, authority, operation and continuity stays with the enterprise | `SYSTEM.md` Scope, Ownership | It becomes a hosted platform that runs your work rather than a node you own |
| `GROUND-002` | People and models are native operators of one governed world | `CONTRACT.md` C1, `SYSTEM.md` | It becomes an ordinary app with an AI feature, or a model framework with a dashboard |
| `GROUND-003` | Authority is granted, typed and scoped; nothing acquires it by operating | `CONTRACT.md` C3, C11 | It becomes automation where capability implies permission |
| `GROUND-004` | You act by crossing a declared operation, not by having access | `CONTRACT.md` C6, `SPEC.md` | It becomes a permissions layer over arbitrary action, with no unit to discover or attribute |
| `GROUND-005` | A consequential act binds to exact state | `CONTRACT.md` C2, C10, C15 | It records that something happened without being able to say what it happened to |
| `GROUND-006` | What may be asked is discoverable from the artifact alone | `CONTRACT.md` C12, `AI-NATIVE.md` | It needs a person who already knows, which is normal enterprise software |
| `GROUND-007` | Every crossing leaves an attributable durable record | `CONTRACT.md` C8, C15 | It cannot answer why anything is what it is |
| `GROUND-008` | Refusal is an outcome, not an error | `CONTRACT.md` C6, C8 | It becomes permissive by default, and "not allowed" stops being distinguishable from "broken" |
| `GROUND-009` | Correction never erases occurrence | `CONTRACT.md` C4, C9 | The record becomes rewritable and every historical attribution becomes provisional |
| `GROUND-010` | A report is not an observation | `CONTRACT.md` C7, C5, `SDLC.md` | It takes an agent's word for its own work, and delegation at scale collapses |
| `GROUND-011` | Standing does not collapse | `CONTRACT.md` C4, C11, C14 | It becomes a wiki with permissions |
| `GROUND-012` | Human judgement is reserved and scarce, not a gap to automate | `CONTRACT.md` C5, `decisions/0023` | It becomes an autonomous agent runtime and the owner becomes an operator of last resort |
| `GROUND-013` | The model is substitutable | `SYSTEM.md`, `BYOM.md`, `PRD.md` PROD-I-9 | It becomes a wrapper around one provider and the custody argument becomes marketing |
| `GROUND-014` | Effort resolves to intention | `CONTRACT.md` C15, `PRD.md` PROD-I-1 | Agents run all night and produce a ledger nobody can read as a decision |
| `GROUND-015` | Work survives the loss of a participant's context | `CONTRACT.md` C12, `AGENTS.md` | It is usable only inside one conversation, which is the constraint it exists to remove |
| `GROUND-016` | A node is whole at any size | `SYSTEM.md`, `decisions/0039` | It becomes enterprise software with a hobby tier, and federation becomes a migration path |

**What was deliberately left out**, each with the reason:

| Considered | Belongs at | Because |
| --- | --- | --- |
| Proofing as a product domain | journey and `PRD.md` | Without proofing and with all sixteen claims, it is still Soveraeign |
| SQLite, Python, the filesystem store | `ENGINEERING.md` | Change all three and no promise moves |
| Offices and counters | `CLASSIFICATION.md`, `decisions/0038` | A way to place an operation, not a claim about the product |
| Leases and fencing tokens | `SPEC.md` | The mechanism `GROUND-010` is kept by |
| The seven resource words | canon, then the accounting contract | Vocabulary protecting `GROUND-014`, not ground itself |
| Federation | already inside `GROUND-016` | A node whole at any size is what makes crossing without absorption mean anything |

---

## C · Participants and needs

Ten participants, unchanged from `CANON-1` and re-checked. Where the repository already
names a participant — the cast in `.claude/epic/offices.json` — the canon reuses that name
rather than minting a second. Needs stay prose with no identifier: they are not a join in
the chain, and an unnamed need is cheaper to correct than a wrong one made canonical.

**Owner is deliberately absent.** Owner is not a role; it is the context that sets which
Binding and which Projection a person comes through, over whatever role they hold
(`decisions/0020`). Bdo at the operator desk is a `human-operator`.

| Participant | Kind | Trying to accomplish |
| --- | --- | --- |
| `human-operator` | `HUMAN` | Do domain work without learning the internals first; see what happened while away; decide what only a person can decide |
| `model-operator` | `MODEL` | Discover the legal operations from the artifact alone; be refused legibly; hand off without private state |
| `model-bringer` | `HUMAN` | Keep custody while changing which model runs; know what each model consumed; get a visible refusal, never a silent substitution |
| `agent` | `HUMAN`/`MODEL` | Choose among reachable operations without widening its own authority; escalate without stalling everything else |
| `worker` | `WORKER` | One bounded task, unambiguous input state, a lease that fences it |
| `witness` | `HUMAN`/`MODEL` | Reach the durable output without the executor's account of it; record a dissent that stays visible |
| `domain-owner` | `HUMAN`/`MODEL` | A mandate narrow enough to finish; an envelope with a visible remainder; a witness who is not themselves |
| `node-owner` | `HUMAN` | Stand a node up and know it is theirs; grow or federate without migrating authority |
| `external-system` | `SYSTEM` | Be reached only through a declared crossing that leaves a receipt |
| `peer-node` | `SYSTEM` | Cross into another node without either absorbing the other |

---

## D · Product promises

Fifteen. Each derives from at least one ground claim, and the check refuses one that
derives from none. `reach / decl / miss` counts **distinct** crossings — a change from
`CANON-1`, explained in section H.

| Promise | Source | Ground | reach | decl | miss |
| --- | --- | --- | ---: | ---: | ---: |
| `PROMISE-01` bring your own participant · **composite** | `OWNER_DIRECTED` | 001, 002, 006, 013 | 17 | 25 | 4 |
| `PROMISE-02` custody stays here | `GOVERNINGLY_GROUNDED` | 001, 013 | 2 | 4 | 4 |
| `PROMISE-03` you can find out what can be asked | `GOVERNINGLY_GROUNDED` | 004, 006 | 1 | 10 | 0 |
| `PROMISE-04` one world | `GOVERNINGLY_GROUNDED` | 002 | 7 | 12 | 0 |
| `PROMISE-05` you can find out why | `GOVERNINGLY_GROUNDED` | 005, 007, 014 | 9 | 9 | 0 |
| `PROMISE-06` the model is swappable | `GOVERNINGLY_GROUNDED` | 001, 013 | 2 | 2 | 2 |
| `PROMISE-07` everything leaves a receipt | `GOVERNINGLY_GROUNDED` | 007, 008 | 13 | 12 | 1 |
| `PROMISE-08` correction never erases | `GOVERNINGLY_GROUNDED` | 009, 011 | 4 | 9 | 0 |
| `PROMISE-09` your judgement is the scarce thing | `STRONGLY_DERIVED` | 012 | 0 | 5 | 0 |
| `PROMISE-10` useful from the artifact alone | `GOVERNINGLY_GROUNDED` | 006 | 0 | 5 | 0 |
| `PROMISE-11` delegate and check | `GOVERNINGLY_GROUNDED` | 003, 010 | 1 | 7 | 1 |
| `PROMISE-12` work carries across a boundary | `STRONGLY_DERIVED` | 015 | **5** | **0** | **0** |
| `PROMISE-14` a node of your own | `OWNER_CONFIRMATION_REQUIRED` | 001, 016 | 0 | 2 | 2 |
| `PROMISE-15` cross to another node · `LATER` | `GOVERNINGLY_GROUNDED` | 016 | 2 | 0 | 1 |
| `PROMISE-16` decide against exact state | `STRONGLY_DERIVED` | 005, 009, 011 | 1 | 8 | 0 |
| ~~`PROMISE-13`~~ | **retired in `CANON-2`** | — | — | — | — |

**Composite versus atomic.** One promise is composite: `PROMISE-01` composes `02`, `03`,
`04`, `05` and `06`. Bdo's wording bundled five undertakings, and composing them keeps each
separately testable while a reading of `PROMISE-01` answers for all of them. The other
fourteen are atomic. A composite promise is never counted as a sixth thing to build.

**Three source classifications worth reading closely:**

`PROMISE-12` was `IMPLEMENTATION_DERIVED` in everything but name. `CANON-1` said it
"arrived as an implementation choice rather than a stated intention" and named it anyway.
That had the direction of authority backwards. It now stands on `CONTRACT.md` C12,
`SYSTEM.md` giving Sov bounded agency over its own handoff, and `AGENTS.md` requiring a
handoff that names standing, changes, observations, residuals and next action.
`decisions/0036` is cited as evidence that the promise is keepable, not as the reason it
exists. The checker now refuses any promise carrying `IMPLEMENTATION_DERIVED`.

`PROMISE-14` is `OWNER_CONFIRMATION_REQUIRED`, and it is the one promise here I would not
put my name to. `GROUND-016` establishes that a node is whole at any size — a claim about
nodes. `PROMISE-14` is about standing one up being an experience the product undertakes to
give someone, and no governing document treats it as one. Confirm it or it moves below
canon.

`PROMISE-16` replaces the retired `PROMISE-13`, which said proofing. The test was yours:
would Soveraeign still be Soveraeign if it stopped shipping proofing as a first-class
domain while keeping its foundational promises? It would. So the proofing wording was
domain altitude wearing canon clothes, and this is the durable claim underneath it —
consequential work over governed, versioned state, decided against an exact version and
inspectable by someone who was not you. Proofing remains the first substantive enterprise
proving workflow, which is a real claim and a smaller one.

`PROMISE-13` was **retired**, not reworded. `python scripts/sov_canon.py trace PROMISE-13`
still answers and says what happened to it. Nothing ever attributed to `PROMISE-13`
silently comes to mean something wider.

---

## E · Three end-to-end journeys

Each rendered as the full chain, from participant down to what a fact could say today.
Marks: `REALIZED` reachable and demonstrated · `PARTIAL` some crossings reachable ·
`DECLARED_UNREACHABLE` the operation exists and nothing carries it · `MISSING` no service
declares it · `OUT_OF_PHASE` deliberately not required yet.

### 1 · Bring my model and put it to work here — `PARTIAL`

```text
model-bringer
  → need    use the model I already have, inside my node, without the node becoming
            the provider's and without losing track of what it consumed
  → ground  GROUND-001 custody · GROUND-013 substitutable
  → promise PROMISE-01 (composite) · PROMISE-02 · PROMISE-06
  → journey JOURNEY-01
```

| Crossing | Requirement | `SPEC.md` transition | State |
| --- | --- | --- | --- |
| `asset.propose-description` | PROD-I-1 | `submit_proposal` | `REALIZED` · IN_PROCESS |
| `console.grant` | PROD-I-5 | — | `REALIZED` · IN_PROCESS |
| `projection.package-context` | PROD-I-3 | `cross` | `DECLARED_UNREACHABLE` |
| `projection.read-context-package` | PROD-I-3 | — | `DECLARED_UNREACHABLE` |
| `model.invoke` | — | `invoke_model` **orphaned** | `MISSING` |
| `model.declare-binding` | — | — | `MISSING` |

**Evidence today:** `adapters/ollama/observations/parity-live.json` records a live
inventory grading. It grades declared bindings against a recorded inventory; it does not
execute a model.

**The reading that matters.** `SPEC.md` declares an `invoke_model` transition and no
manifest declares an operation realizing it, while `adapters/ollama/` executes one
*outside the capability map entirely*. Bringing a model is a filesystem act: you author a
file under `adapters/ollama/bindings/` and no operation admits it. The node's flagship
promise runs through the one part of the system that is not governed by the node.

### 2 · Find out what I can do here — `DECLARED_UNREACHABLE`

```text
model-operator
  → need    learn the operations, their inputs and their authority cost from the node
            itself, before asking a person
  → ground  GROUND-004 declared operations · GROUND-006 discoverable from the artifact
  → promise PROMISE-01 (composite) · PROMISE-03 · PROMISE-04
  → journey JOURNEY-02
```

| Crossing | Requirement | State |
| --- | --- | --- |
| `console.discover-operations` | PROD-I-6 | `REALIZED` · IN_PROCESS |
| `gateway.list-endpoints` | PROD-I-3 | `DECLARED_UNREACHABLE` |
| `gateway.resolve-capability` | PROD-I-3 | `DECLARED_UNREACHABLE` |
| `registry.resolve` | PROD-I-2 | `DECLARED_UNREACHABLE` |
| `registry.read-index` | PROD-I-2 | `DECLARED_UNREACHABLE` |

**Evidence today:** `contracts/fixtures/capability-map.reference.json`, 102 capabilities,
digest `3aab7102…`, rebuilt and checked on every `verify.py` run.

**The reading that matters.** Nothing is missing. Every operation this journey needs is
declared. The complete answer to "what can I do here" already exists as a checked-in
projection, and no service serves it. A model reads the file; it cannot ask. This is the
cheapest journey on the board to finish and it sits under the promise the AI-native claim
rests on.

### 3 · Perform the first substantive enterprise workflow — `DECLARED_UNREACHABLE`

```text
human-operator
  → need    look at an exact version of a work product with someone else, disagree in
            writing, and end with a decision attached to that version
  → ground  GROUND-005 bind to exact state · GROUND-009 correction · GROUND-011 standing
  → promise PROMISE-16 · PROMISE-04 · PROMISE-08
  → journey JOURNEY-11
```

| Crossing | Requirement | `SPEC.md` transition | State |
| --- | --- | --- | --- |
| `asset.read-version` | PROD-I-2 | `read_source` | `REALIZED` · IN_PROCESS, CLI |
| `proofing.open-session` | PROD-I-1 | — | `DECLARED_UNREACHABLE` |
| `proofing.assign-reviewer` | PROD-I-8 | — | `DECLARED_UNREACHABLE` |
| `proofing.add-annotation` | PROD-I-2 | `read_source` | `DECLARED_UNREACHABLE` |
| `proofing.request-comparison` | PROD-I-2 | `begin_run` | `DECLARED_UNREACHABLE` |
| `proofing.request-revision` | PROD-I-1 | — | `DECLARED_UNREACHABLE` |
| `proofing.propose-decision` | PROD-I-1 | `submit_proposal` | `DECLARED_UNREACHABLE` |
| `proofing.ratify-decision` | PROD-I-5 | `ratify` | `DECLARED_UNREACHABLE` |
| `proofing.close-session` | PROD-I-4 | — | `DECLARED_UNREACHABLE` |

**Evidence today:** `services/proofing/` has a charter and eight declared operations with
defeating fixtures. None runs.

**The reading that matters.** Nothing is missing here either. The enterprise workflow
needs no operation invented — only the eight already contracted, built. Every one already
carries a `PROD-I` requirement and five carry a `SPEC.md` transition, so the specification
work is done and the implementation is not.

### What the three together say

The node can put something under custody and read it back at an exact version. It cannot
answer a question about itself, run a model under its own governance, or complete a single
domain workflow end to end. Two of the three journeys have **nothing missing** — only
things unbuilt. That is a materially better position than it looks from the promise table,
and it is the strongest argument for the layer: the table now says which.

---

## F · What belongs where

The boundary questions this layer had to settle, with the answer and the test.

| Layer | Owns | Never owns | Test |
| --- | --- | --- | --- |
| `CONTRACT.md` | invariants that constrain every specification and implementation | product identity, participants, journeys | "may this ever stop being true?" |
| **Product Ground** | what product this is — 16 claims | requirements, mechanisms, services, sequencing | "different product, or different implementation?" |
| **Product Canon** | participants, needs, promises, journeys | requirements, architecture, roadmap, runtime state, accounting mechanics | "who is it for, and what does it undertake?" |
| Journeys | one participant's complete intention, and the crossings it needs | screens, flows, sequencing | "could one person walk this and be finished?" |
| `PRD.md` | what Phase I must prove | product intent above it, design below it | "is this required now?" |
| `SPEC.md` | logical objects, transitions, predicates, refusals | phase scope, product intent | "what exactly happens?" |
| Charting (`#40`/`#41`/`#42`/`#48`) | typed graph substrate, provenance, state-pinned projections | product intent, promises, needs | "is this how relations are expressed, or what they mean?" |
| Resource accounting | budgets, usage, cost, conversions | the intention half of `VALUE` | "is this a measurement or a meaning?" |
| Service contracts | one bounded lifecycle | another service's state | "who owns this transition?" |
| Evidence and state | what was demonstrated, what currently claims to exist | meaning | "did this happen, or does this mean something?" |

`PRD.md` and `SPEC.md` cut **across** capabilities rather than sitting in a linear stack
below them — one `PROD-I` requirement carries operations from several services, and one
`SPEC.md` transition is realized by several operations. The chain in `CANON.md` is a
traversal order, not a containment hierarchy.

### Two boundaries that are still contested

**The word `Requirement` means two different things**, and both are about to be
mechanized. `#41`'s Requirement is a *competence obligation a skill carries* — "QA
requirements may cover repository verification and independent observation". `PRD.md`'s
requirement is a *product requirement Phase I must prove*. The attribution chain uses the
product sense. If `#41` and `#48` land unqualified, a reader following a `Requirement`
edge cannot tell which ladder they are on. This is `OPEN-SEAMS.md` S18's "two layers named
gateway" one level up, and it is cheaper to name now. Naming is yours; nothing was
renamed.

**`OPEN-SEAMS.md` S10, the product boundary, is not closed by this layer.** S10 asks
whether Soveraeign is a primary enterprise application or a constitutional runtime over
existing ones. The ground is deliberately silent on it — every one of the sixteen claims
is true under either answer, which is a point in the ground's favour and a reason S10
still needs settling somewhere else.

---

## G · Five readings of one source

These are **projections**, not competing truths. Each was produced by hand from
`GROUND.md` and `CANON.md` and nothing else. None of them may contradict the ground; where
one disagrees it appears below as dissent, not as a rewritten product definition.

That they were written by hand is itself the finding — see `JOURNEY-14` in section H.

### G1 · Owner read

**What we are actually building.** A governed operating world where a model is a first-class
operator rather than a feature. Sixteen ground claims, fifteen promises, fourteen journeys,
102 declared operations across eight services. Three services are built; 34 capabilities are
reachable, all 34 in process, five of them also over a CLI and exactly one over MCP.

**Strongest.** The evidence discipline. Positive and defeating fixtures on everything, a
verification gate that grades itself, refusals that are contracted rather than incidental,
and a capability map that refuses to build when a policy is broken — which it did, this
week, on a real defect nobody had found by reading. `PROMISE-12` is the only promise every
crossing of which is reachable, and the continuity path behind it works.

**Incoherent.** `GROUND-010` — a report is not an observation — is the claim the whole
delegation story rests on, and the node cannot currently keep it. The Observation Service
is a charter. `AI-NATIVE.md` check 3 reads `UNATTESTABLE` on every surface assessed. The
system that exists to refuse self-witnessing is presently self-witnessed.

**Where effort is going.** Governance machinery, at a ratio worth looking at squarely: 44
decision records, 19 skills, 16 workflows, five agent roles and a session registry, against
three built services and no wire protocol. That is defensible for a founding phase and it
is not defensible for another one.

**Built without sufficient product justification.** Nothing found. The most exposed item
was `PROMISE-12`, and re-grounding it held — `CONTRACT.md` C12 and `SYSTEM.md` carry it
independently of the console. The harness itself is the honest candidate: it holds no
standing, and after this pass it also derives from no ground claim, because it is host
plumbing rather than product. That is the correct answer and it is worth saying out loud
before someone attributes a year of harness work to a promise.

**Genuinely requires your judgement.**

1. Accept, redirect or strike `EPOCH-1 / GROUND-1.0`.
2. Confirm or drop `PROMISE-14` — the only promise carrying `OWNER_CONFIRMATION_REQUIRED`.
3. `record.read-entry`: is reading operational history an operator act or back-office
   machinery? Held open since the MCP withholding.
4. Qualify one of the two senses of `Requirement` before `#41` and `#48` land.

**Highest-leverage next move.** Serve the capability map. `JOURNEY-02` has nothing missing
— five declared operations, four unreachable, and the whole answer already sitting in a
checked-in projection. Building the read path turns `PROMISE-03` and `PROMISE-10` from
zero-reachable into demonstrable, and it is the promise the AI-native claim rests on. It is
also the smallest of the three candidate moves.

### G2 · End-user read

*A person meeting this for the first time, told nothing.*

**What I think this is.** A place where I can point my AI at my own work and have it
actually do the work, with a record of what it did, on my machine, without handing my
company to a model vendor.

**What I can do.** Thirty-four things, and I reach every one of them by calling Python in a
terminal. Put a file under custody and read it back at an exact version; retract something
without erasing it; grant someone authority; open a session and pick up where I left off;
read the journal of what happened. That is a real amount and none of it looks like a
product yet.

**Why I should care.** Because I have agents doing real work and no way to answer what they
did, under whose authority, or what it cost — and because switching model provider
currently means rebuilding everything around it.

**What I expect to happen first.** I connect my model. I ask it what it can do here. It
tells me.

Neither of those two steps works. Connecting a model means hand-authoring a file in a
directory. Asking what it can do means reading a JSON file myself.

**Product versus internal machinery.** Assets, versions, receipts, permissions and "what
happened while I was away" read as product. Offices and counters, standings, effect
classes, seams, the capability map and the harness read as machinery — and machinery is
most of what is visible.

**Confusing or missing.** There is no way in. No install, no first run, no first screen.
`JOURNEY-12`, standing up a node, has two of its four crossings missing entirely — the
first thing a person would do is the least built thing here.

**What would disappoint me.** Being told models are first-class operators and then finding
that the node cannot invoke a model. That is the gap between the pitch and the artifact,
and it is one operation wide.

### G3 · Marketing read

Marketing may omit. It may not redefine. Each compression below is scored against the
canonical claim it compresses.

**Headline candidate:** *Your agents work here. Your company stays yours.*

| canonical_claim | marketing_compression | omitted | risk_of_distortion | safe_or_not |
| --- | --- | --- | --- | --- |
| `GROUND-001` custody of memory, authority, operation and continuity | "Your company stays yours" | which four things; that compute may still be remote | Reads as "no cloud", which is not the claim — `SYSTEM.md` explicitly permits remote compute | **SAFE with a footnote.** Without one, it is a data-residency promise the product does not make |
| `GROUND-002` one governed world | "Your agents work here" | that "here" is a governed world with declared operations, not a sandbox | Reads as an agent runtime | **SAFE** |
| `GROUND-013` model substitutable | "Swap models without rebuilding" | that no model is invocable through the node today | Present tense on an unbuilt capability | **NOT SAFE TODAY.** Needs "designed so that", or `model.invoke` built |
| `GROUND-014` effort resolves to intention | "Know what every token was spent on, and why" | that no receipt records consumption yet | Straight future-tense claim in present tense | **NOT SAFE TODAY.** The join exists; the measurement does not |
| `GROUND-006` discoverable from the artifact | "Your agent reads the manual itself" | that nothing serves the answer over a wire | Implies a live discovery endpoint | **NOT SAFE TODAY** |
| `GROUND-010` report is not observation | "Delegated work gets checked by something that isn't the worker" | that the checker is a charter | Implies a shipped verifier | **NOT SAFE TODAY** |
| `GROUND-009` correction never erases | "Undo without rewriting history" | that "undo" is a counter-record, not a reversal | "Undo" implies reversal, which `GROUND-009` explicitly refuses | **NOT SAFE.** Distorts the claim. Use "correct", never "undo" |
| `GROUND-012` judgement is reserved | "The decisions that need you still reach you" | the whole queue mechanism | Low | **SAFE** |

**The finding.** Four of eight compressions are unsafe *today* for the same reason — they
state in present tense something the canon marks as reachable rather than kept. One,
`GROUND-009` → "undo", is unsafe *permanently*, because it distorts rather than omits. That
is the distinction worth keeping: four are timing, one is meaning.

### G4 · Compression read

Optimized for reconstruction fidelity: the smallest form from which the major
distinctions can still be recovered.

```text
SOVERAEIGN — a node you own where people and models operate one governed world.

  CUSTODY     your record, authority, operation, continuity stay with the node   [001,016]
  PARITY      people and models: same state, transitions, authority, history     [002]
  GRANT       authority is given, typed, scoped; never earned by operating       [003]
  OPERATION   you act by crossing a declared operation, pinned to exact state    [004,005]
  DISCOVERY   what may be asked is readable from the artifact alone              [006]
  RECEIPT     every crossing records; refusal is a result, not an error          [007,008]
  CORRECTION  countered, never erased; consumption never un-spends               [009]
  WITNESS     a report is not an observation; standing does not collapse         [010,011]
  JUDGEMENT   a person's decision is scarce and reserved, and never blocks all   [012]
  PORTABILITY the model swaps; nothing authoritative moves                       [013]
  ATTRIBUTION effort resolves up to intention, intention down to spend           [014]
  CONTINUITY  work survives a lost session, operator, model, day                 [015]
```

**PRESERVED.** All sixteen claims, and the twelve distinctions that actually separate this
from adjacent products. The atomic/composite structure recovers from the bracketed ids.

**OMITTED.** Participants, journeys, every reachability figure, all evidence addresses, the
resource vocabulary, phase. Someone reading only this would know what the product means and
nothing about whether any of it works.

**DISTORTED.** Two, and both by pairing. `CUSTODY` folds `GROUND-001` with `GROUND-016`,
which loses that a personal node is a first-class node rather than an implication of
custody. `WITNESS` folds `GROUND-010` with `GROUND-011`, which loses that standing is about
claims and observation is about the world — different failures, same line.

**RECONSTRUCTION_CONFIDENCE: high for meaning, none for state.** A fresh model given only
this block would restate the product correctly, propose journeys close to the real
fourteen, and be unable to say a single true thing about what exists. That split is the
design working: this is the compression a receipt or a ticket should carry, and state
belongs in the state references beside it.

### G5 · Raw perspective read — skeptical platform architect

*Twenty years of platforms. Has seen governance frameworks arrive and be routed around.*

**WHAT I THINK THIS IS.** A constitution for agent work, with a reference implementation
attached. The document set is the product; the code is a proof that the documents are
implementable.

**WHAT FEELS DISTINCTIVE.** Refusal as a contracted first-class outcome. Almost nobody
does this — refusals are error paths everywhere else, and here they are results with
codes, fixtures and receipts. Second: the capability map refusing to build when policy is
violated, and actually catching a live exposure this week. That is a governance artifact
with teeth, which I did not expect.

**WHAT FEELS OVERBUILT.** The ratio. Forty-four decision records, nineteen skills, sixteen
workflows, five agent roles, a session registry with path claims, a scheduling ledger — for
three built services reachable only in process. I have watched this pattern eat teams. The counter-case
is that this is a founding phase and the machinery is the deliverable; I would want to see
that ratio invert inside one more phase or I would call it.

**WHAT FEELS UNDERDEFINED.** Deployment. There is no server, no wire protocol, no
concurrency story, no multi-tenancy, no failure model, no upgrade path. Everything is
in-process or CLI. "Add HTTP when a conformance case requires it" is a defensible
discipline and it means the distributed-system questions have not been asked yet, and those
are the ones that kill platforms.

**WHAT I EXPECT NEXT.** Serving the capability map over something. If discovery does not
get a wire, the AI-native claim stays a document claim.

**WHAT I DO NOT BELIEVE YET.** That a model can be an operator here. There is no
`model.invoke`. The AI-native product cannot invoke a model through its own governance —
the one adapter that does runs outside the capability map. Everything about model
participation is currently a person driving Claude Code with a very good set of rules
loaded, which is not the same claim.

**WHAT I WOULD CALL IT.** A governed agent operating environment. Not a platform, not a
framework. "Sovereign" is doing real work in the name and I would keep it.

**WHAT I WOULD PAY FOR.** The attribution answer, once it is real: point at a month of
agent spend and get back what product intention justified it. Nobody has that. I would not
pay for the governance framework by itself — I would adopt it free and pay for the thing
that makes the spend legible.

**WHAT WOULD MAKE ME LEAVE.** Finding out that the governance is advisory. One place where
a service writes authoritative state around the kernel, or a standing that got promoted by
a report, and the whole edifice becomes documentation. The defeating fixtures are what
keeps me here.

**ONE-SENTENCE RAW READ.** The most rigorous thinking about agent governance I have seen
written down, attached to a system that cannot yet run an agent.

---

## G6 · Uplift

Every reading's friction, classified. `SOURCE → READING → FRICTION → UPLIFT`.

| Source | Reading | Friction | Class | Uplift |
| --- | --- | --- | --- | --- |
| `GROUND-006`, `JOURNEY-02` | end-user, architect | The answer to "what can I do" exists as a file and nothing serves it | `INTERFACE` | Build the capability read path. Five declared operations, none reachable, nothing missing |
| `GROUND-013`, `JOURNEY-01` | end-user, architect, marketing | The node cannot invoke a model | `PRODUCT` | `model.invoke` and `model.declare-binding` are `MISSING`. Until one exists, model participation is a person driving a model |
| `GROUND-010`, `JOURNEY-09` | owner | The claim delegation rests on cannot be kept; check 3 reads `UNATTESTABLE` everywhere | `EVIDENCE` | Build the Observation Service, or say plainly that independent observation is Phase II |
| `GROUND-014` | marketing, architect | The strongest commercial claim is the least built | `PRODUCT` | The two contracts: `capability` on the ticket schema, `consumed` on the receipt schema |
| `JOURNEY-12` | end-user | No install, no first run; the first thing anyone does is the least built | `PRODUCT` | `node.establish` and `node.read-identity` are both `MISSING` |
| Offices, counters, seams, standings | end-user | Machinery is most of what is visible; product is a thin layer over it | `PEDAGOGICAL` | Not a semantic problem. The vocabulary is sound and the front door is missing |
| `GROUND-009` → "undo" | marketing | "Undo" distorts a counter-record into a reversal | `NAMING` | Never use "undo". "Correct" is the word, and the distinction is load-bearing |
| Four of eight compressions | marketing | Present tense on reachable-not-kept | `MARKETING` | A house rule: canon reachability decides the tense. Reachable is "designed to"; kept is "does" |
| `Requirement` in `#41`/`#48` vs `PROD-I-n` | architect | Two ladders, one word, both about to be mechanized | `SEMANTIC` | Qualify one sense before either lands. Owner-held |
| Sixteen claims / 2365-line discovery report | compression | The full meaning fits in twelve lines | `COMPRESSION` | Done: the G4 block is the carry-format. Ship it into receipts and tickets |
| `GROUND-001` + `GROUND-016` pairing | compression | Compressing them loses that a personal node is first-class | `SEMANTIC` | Watch it. If the pairing survives three compressions, `GROUND-016` may be redundant |
| Governance-to-function ratio | architect, owner | 51 decisions against one service | — | Not uplift. A phase judgement, and the owner's |

A marketing or user perspective revealed real work here — four of these twelve came from
outside the engineering view. None of them granted authority to change what the product
means, and none did.

---

## H · What accepting this would do

Product acceptance only. Nothing here asks approval for an implementation.

### Becomes semantically constrained

- **A promise must derive from a ground claim.** New product intent has to be argued at the
  ground layer first, where the test is "different product or different implementation".
  This is the constraint with teeth, and it is aimed at future me as much as anyone.
- **A promise may never be canonical because it was built.** `IMPLEMENTATION_DERIVED` is a
  hard defect with three named exits.
- **An identifier's meaning is fixed for good.** Change the meaning, retire the identifier.
  `PROMISE-13` is the worked example and it happened before any acceptance, deliberately.
- **A typo is not a new product.** Rendering, revision and epoch are three separate levels,
  checked: a rendering may not render a revision other than its own.
- **A journey's crossings must be declared operations or named gaps.** A crossing cannot be
  described into existence.
- **Measured usage is counted once.** Views may overlap; a total may not be reached by
  summing them.
- **A canon is pinned to a ground revision.** It cannot silently start meaning something
  else when the ground moves.

### Now well-grounded

| Work | Ground | Note |
| --- | --- | --- |
| Asset Service — custody, versions, receipts, retraction | 005, 007, 009 | `PROMISE-05`, `PROMISE-07`, `PROMISE-08` |
| Record Service — append-preserving journal, counter-records | 007, 009 | The one service every promise about "why" runs through |
| Console continuity path | 015 | `PROMISE-12`, the only fully reachable promise |
| Capability map and offices | 004, 006 | The projection `PROMISE-03` needs, unserved |
| Defeating-fixture discipline, refusal codes | 008, 011 | The distinctive thing, per the architect read |
| Grants, leases, fencing | 003, 010 | `PROMISE-11` |
| Conformance oracle | 010, 011 | Independent by construction |
| BYOM adapter and model bindings | 013 | Grounded, and running outside the map |

### Conflicts with it

One, and it is small: **`bindings/mcp` withholding `record.read-entry` sits awkwardly under
`GROUND-002`.** One governed world means people and models resolve through the same
history. A model operator that cannot read the journal is one door short of a person. The
withholding was the reversible default and the office table is the more likely error. Your
call, unchanged.

Nothing else conflicts. That is a weaker result than it sounds: it mostly says the ground
was read out of the repository rather than imposed on it.

### Remains weakly grounded

- **`PROMISE-14`**, marked `OWNER_CONFIRMATION_REQUIRED`. The only one.
- **`GROUND-016`** is the thinnest claim. It is carried by `PROMISE-14` and `PROMISE-15`,
  one of which is `LATER` and the other unconfirmed. If you drop `PROMISE-14`, `GROUND-016`
  is left carried by a `LATER` promise alone, which is admissible and worth noticing.
- **`GROUND-014`** is the claim with the most product weight and the least implementation.
  It is grounded in `PRD.md` PROD-I-1, which requires a recorded cost that
  `services/asset/conformance/BASELINE.md` records as failing.

### Open seams this settles

| Seam | Effect |
| --- | --- |
| **The missing product layer** (this pass's own finding) | Closed. `journey`, `user need` and `product promise` appeared zero times outside `lineage/`; they now have a layer, identifiers and a check |
| **`PROMISE-12`'s provenance** | Closed. Re-grounded, with `decisions/0036` demoted from reason to evidence |
| **Proofing's altitude** | Closed. First enterprise workflow, not part of the definition |
| **Double counting, before it existed** | Closed by construction. Also fixed a live instance: `promise_reading` was summing crossings across journeys, which is why `PROMISE-01` reads 17 here and 18 in `decisions/0046` |

### Open seams this does not touch

- **S10, the product boundary.** Primary enterprise application or constitutional runtime
  over existing ones. All sixteen claims are true either way.
- **S14, two owners for search.** Asset and Projection both ship it.
- **S18, two things named gateway.** And now the second instance, `Requirement`.
- **`record.read-entry`'s office.** Named above.
- The 2026-08-23 residuals in `LESSONS.md`, untouched.

### Joins that become mechanically enforceable

Already enforced by `python scripts/verify.py`:

```text
GROUND → PROMISE            promise derives from a declared claim; claim carried by a promise
PROMISE → JOURNEY           every promise reached by a journey or composed by one that is
JOURNEY → CAPABILITY        every crossing is a declared operation or a named gap
CAPABILITY → OPERATION      logical endpoint rebuilt from the manifest, not trusted
OPERATION → REQUIREMENT     99 of 102 carry a PROD-I id
OPERATION → RECEIPT EVENT   27 emitted events, each a capability or a stated exception
record ↔ wording            every identifier appears in the document that owns its prose
epoch/revision/rendering    a rendering may not render another revision
usage → intention           measured once, viewed through every ancestor
```

Still not enforceable, and neither is canon's to supply:

```text
WORK ITEM → CAPABILITY      contracts/issue-metadata.schema.json has no product referent
RECEIPT → RESOURCE USAGE    contracts/receipt.schema.json has no consumption field
```

---

## I · Investigations

### I1 · Charting boundary — `COMPOSES_WITH`

`OBSERVED`. The live bodies of `#40`, `#41`, `#42` and `#48` were read through `gh` on
2026-08-24 and re-checked at the top of this pass; all four are `OPEN` and last touched by
the registrar's own sync, with no content change since the read.

`#40` is a typed-graph and projection substrate: stable identifiers with explicit
provenance, a graph that rejects type-invalid relations, a covering that selects local
material without becoming authoritative, a chart that pins its source revision and declares
omissions. Its defeating cases include *"a graph edge collapses requirement, capability,
implementation, and evidence into one relation"*. It names no promise, no need and no
product intent.

The canon would be a **consumer** of `#40`, contributing node and edge types — `ground`,
`promise`, `journey`, `derives_from`, `serves`, `directly_serves`, `rolls_up_to` — that
`#40`'s vocabulary does not name, while `#40` supplies the provenance, state-pinning and
type-invalidity rules such a graph needs. `#42` is `ORTHOGONAL`: it lowers state-pinned
charts into operator environments and consumes intent rather than producing it. `#48` is
`COMPOSES_WITH`.

**No governed word was reused.** `Atlas`, `Chart`, `Crossing`, `Covering` and `Point` are
`#40`'s. `Journey`, `Ground`, `Promise`, `Rendering` and `Epoch` appeared nowhere in the
repository at a conflicting altitude before this pass. `Crossing` is used inside `CANON.md`
as ordinary English for a journey step and never as an identifier or a type — if that reads
as a collision, the fix is one word.

### I2 · SOV as reader — `NATURAL_EXTENSION`, and the acronym is `UNNECESSARY`

Two questions, two answers, because they are not the same question.

**The capability is a natural extension.** `SOV.md` already gives Sov "decide which
relevant material to inspect and declare material omissions", "return a compact,
attributable handoff", and — step 6 — "package the claim, visible result, exact evidence,
strongest defeating case, and residuals into an engaging, legible acceptance presentation".
That is a bounded, perspective-taking, omission-declaring reading. The vehicle half already
exists.

What did not exist is the thing being carried. Until this pass, Sov loaded governing
documents and reconstructed product intent from scattered prose every session. `GROUND.md`
and `CANON.md` are the stable vocabulary; step 3 of the load sequence should name them. The
five readings in section G are exactly what a Sov read produces, and I produced them by
hand because nothing serves them.

**The acronym is unnecessary and slightly harmful.** `Sov` is Bdo's chosen name for the
operating-agent profile. Expanding it into "Semantic Operating Vocabulary" and "System
Operating Vehicle" would give one word three meanings — the profile, the language, the
mechanism — and the repository already carries `OPEN-SEAMS.md` S18 for exactly this failure
with the word `gateway`. The vocabulary has a name: Product Ground. The vehicle has a name:
Sov. Keeping them apart costs nothing.

`OWNER_JUDGEMENT_REQUIRED` on the naming, since naming is yours. `SOV.md` was not modified.

### I3 · A semantic `Read` operation — recommended, and recorded as missing

Conceptually sound and it belongs in the capability map. The shape:

```text
projection.read-perspective(
    system      : which node, at which capability revision
    perspective : owner | end-user | buyer | engineer | security | skeptic | …
    purpose     : what the reader is trying to decide
    resolution  : how much detail, and what budget
) → projection                    the reading itself
    source_ground                 which GROUND-nnn claims it resolved through
    current_state_references      capability revision, binding revision, authority state
    evidence_references           observations and receipts it rested on
    omissions                     what it left out, declared rather than silent
    perspective_attribution       whose position this is, so it is never mistaken for ground
```

This is not file reading. It is a perspectival projection, and the constraint that makes it
safe is `perspective_attribution` plus `source_ground`: a reading that disagrees with the
ground surfaces as **dissent**, never as a rewritten product definition. `CONTRACT.md` C14
already says reality retains veto power and contradictions stay visible; a reading is the
natural place for one to appear.

**Home: the Projection Service.** It already declares `package-context`, which packages
material for a consumer without adopting a position. A perspectival read is that operation's
sibling, not a new service.

**Recorded as a gap rather than built.** `JOURNEY-14` "Read this node from where I stand" is
added to `CANON-2` — `human-operator`, serving `PROMISE-10` and `PROMISE-05`, crossing
`console.discover-operations`, `registry.read-index`, `record.read-entry` and
`observation.read-observation`, with `projection.read-perspective` in
`missing_capabilities`. That is the canon's own mechanism for "a crossing we need that
nothing declares", and it puts the gap under the same check as every other one. No service
manifest was modified.

### I4 · Semantic compression, and facts that address it

`GROUND-014` is not only about money. A second reason for stable identifiers is that a
receipt, a ticket or a run should not have to restate the philosophy of Soveraeign to say
what it was for. It carries this instead:

```yaml
ground:     [GROUND-004, GROUND-006]
promise:    [PROMISE-03]
journey:    [JOURNEY-02]
capability: [gateway.list-endpoints]
```

Four lines, and a fresh model resolves them from two documents instead of reconstructing
product intent from a 2365-line report and 44 decision records. The G4 compression block is
the human-readable form of the same thing.

`contracts/state-fact.schema.json` is the shape for a proposition read through all four
planes, with two worked examples in `contracts/fixtures/state-fact.example.json`:

| Fact | Status | Reading |
| --- | --- | --- |
| `FACT-mcp-ingest-declared` | `DECLARED` | The map reads `MCP: ACTIVE` and the gateway declares the tool. Nobody has called it through a real client. Marking this `OBSERVED` is exactly the collapse `GROUND-010` refuses |
| `FACT-mcp-journal-withheld` | `REFUTED` | A model operator cannot read the journal through MCP. Refuted rather than absent — the difference between a node that cannot do something and a node that does not know it cannot |

Both pin `capability_revision` to the map digest, so both can go `STALE` when the state they
rested on moves. If MCP disappeared tomorrow: the ground would not change, the promise would
not change, the journey would not change, both facts would remain historical, and current
reachability would become false. That is the temporal stability the layer exists to give.

**One deliberate deviation from your sketch.** You wrote `standing: OBSERVED`. The field is
named `evidential_status`. `standing` already means the artifact lifecycle
(`OPEN`/`BUILT`/`WITNESSED`/`RATIFIED`) and the record lifecycle
(`RECORDED`/`ADMITTED`/`RATIFIED`/`EFFECTIVE`), and `AGENTS.md` forbids a synonym for an
existing standing term. A third meaning on the same word would have been the `Requirement`
collision, self-inflicted. The same reasoning renamed the promise field `standing` to
`source`. Both are one-line reversals if you disagree.

### I5 · Engineering carried on independently

All five items from your list, none needing a decision. Every one passes `verify.py`.

| Item | State |
| --- | --- |
| Emitted event names reconciled to capability ids | **Done.** Seven asset events renamed; ten events realizing no declared operation recorded in the manifest with a stated reason; an AST reader over each service's own source refuses an event that is neither, and an excuse the service stopped emitting. 27 events, all resolving |
| MCP representable in the capability projection | **Done.** `mcp_tools` beside `cli_commands`; `asset.ingest-asset` reads `MCP: ACTIVE`. Turned up one real defect, `BACK_OFFICE_EXPOSED`, still yours |
| Completion timestamp for delegated-run wallclock | **Done.** `started_at`/`completed_at` on the asset runs table with a forward migration; `Runs.elapsed()` measures lease to observation |
| `decisions/0038` residuals | **Done.** Residual 1 closed on evidence — 8 manifests, 102 operations, no defect. Residuals 2 and 3 recorded as standing and as moved |
| `#40`/`#41`/`#42`/`#48` inspected before any vocabulary ruling | **Done.** I1 above |

**Concurrency boundary preserved.** `docs/documentation.html` and `docs/surface.html` are
stale in the working tree from another session's in-flight documentation work. Both were
failing before this pass began, verified by reproducing with my files removed. My additions
to `CANON.md`, `GROUND.md` and the capability map now also contribute to that staleness.
Nothing of theirs was rebuilt, absorbed or committed.

---

## J · Against your acceptance test

Ten questions. Where each can be answered from an addressed artifact rather than
conversation memory.

| Question | Answerable | From |
| --- | --- | --- |
| What is Soveraeign? | **Yes** | `GROUND.md`, sixteen claims; section A |
| What would make it a different product rather than a different implementation? | **Yes** | The `if_false` line on each claim; a required field, not a convention |
| Who enters this world, and what are they trying to accomplish? | **Yes** | Ten participants with stated needs |
| What does the product promise them? | **Yes** | Fifteen promises, each with source and ground |
| Which journey realizes that promise? | **Yes** | `sov_canon.py trace PROMISE-nn` |
| Which capabilities and operations make the journey possible? | **Yes** | `sov_canon.py trace JOURNEY-nn`, joined to the map |
| Which current facts say whether those operations are usable? | **Yes** | Reachability per crossing, from the map's own endpoints |
| What evidence supports those facts? | **Partly** | The map is rebuilt and checked. Whether an ACTIVE endpoint *works* rests on service tests, and independent observation reads `UNATTESTABLE` everywhere — `GROUND-010` is the gap |
| Which work and resource consumption were spent realizing the promise? | **No** | A work item cannot name a capability; a receipt cannot record consumption. Both contracts named, neither built |
| Can one source be rendered for owner, user, buyer, engineer and skeptic without each inventing a product? | **Yes, by hand** | Section G, five readings, no contradiction with ground. Nothing serves them — `JOURNEY-14`, `projection.read-perspective` `MISSING` |
| Can one unit of consumption be viewed through every ancestor without being counted twice? | **Yes** | `scripts/sovkernel/attribution.py`, 16 cases. On the example fixture, summing the ground views would report 116,800 tokens where 20,000 were spent; `overlap()` reports the difference rather than hiding it |

Eight yes, one partly, one no, one yes-with-a-missing-interface. The single **no** is the
same two contracts named in the previous report's addendum, and both were unblocked by your
own Q2, Q5 and Q6 rulings.

---

## K · Defaults taken

Reversible, each one line to counter.

- Put Ground in `GROUND.md` at the repository root, beside the rest of the governing set,
  with its own revision line rather than as a section of `CANON.md`.
- Named the three levels `rendering` / `revision` / `epoch`, with the ground owning the
  epoch and the canon carrying it.
- Renamed the promise field `standing` to `source`, and named the state-fact field
  `evidential_status`, to avoid a third meaning on a governed word.
- Made `IMPLEMENTATION_DERIVED` a hard defect rather than a warning.
- Retired `PROMISE-13` rather than rewording it, even though `CANON-1` was never accepted
  and no attribution existed — the machinery is worth exercising once for real.
- Added `JOURNEY-14` rather than only describing the perspectival read in prose.
- Taught `scripts/sovkernel/jsonschema.py` the `maxItems` keyword so the eight-to-twenty
  ceiling on Ground could be a contract rather than a convention.
- Fixed `promise_reading` to count distinct crossings. This changes published figures:
  `PROMISE-01` reads 17 reachable here against 18 in `decisions/0046`, and the earlier
  number was wrong.

## L · What would defeat this

- A ground claim whose `if_false` line, read honestly, describes a different implementation
  rather than a different product.
- A participant a node genuinely serves that none of the ten covers.
- A journey whose crossings cannot be expressed as declared operations plus named gaps.
- A ground or promise identifier re-pointed at a different meaning instead of retired.
- The canon acquiring requirements, sequencing or architecture.
- Ground growing past twenty claims — the signal that claims are being minted per feature.
- A reading in section G that contradicts the ground and is treated as a correction to it
  rather than as dissent.

## M · Residuals

- `PROMISE-14` unconfirmed; `GROUND-016` thin if it goes.
- `GROUND-014` carries the most product weight and the least implementation.
- Nothing reconciles the canon's fourteen journeys against `.claude/epic/offices.json` or
  `conformance/scenarios.json`, both of which describe adjacent things in different words.
- The harness derives from no ground claim. Correct — it is host plumbing — and worth
  saying before someone attributes harness work to a promise.
- `STATUS.yaml` unchanged. Recording the layer's standing there is part of accepting it,
  and a participant does not record its own acceptance.

## N · One owner action

`ACCEPT` · `REJECT` · `STRIKE` · `REDIRECT`

on `EPOCH-1 / GROUND-1.0` and `CANON-2.0`, plus the four judgement calls in G1.
