# Product canon and intent/effort attribution — discovery

Observed: `2026-08-24` on `feat/federation-harness-and-hardening` (80 commits ahead of
`main`, working tree dirty, seven live sessions sharing it).

Standing: a report. `AGENTS.md` — a file under `reports/` is not policy. Nothing here
rules, ratifies, renames, or changes a governing document. No governing file was edited
during this pass. **Intent & Effort Attribution Spine** is used below as a working label
for the thing being researched; it is not proposed as vocabulary.

Every claim is marked `OBSERVED` (read directly from a named artifact), `DERIVED`
(computed or inferred from artifacts, with the derivation stated), `PROPOSED` (mine, and
defeasible), or `OWNER` (only Bdo can settle it).

## Method and coverage

Read in full: `SYSTEM.md`, `CONTRACT.md`, `PRD.md`, `SPEC.md`, `CLASSIFICATION.md`,
`AI-NATIVE.md`, `BYOM.md`, `SOV.md`, `SDLC.md`, `ROADMAP.md`, `STATUS.yaml`,
`OPEN-SEAMS.md`, `README.md`, `services/README.md`, the Console, Gateway, Record and
Registry charters, `decisions/0036`, `decisions/0038`, `.claude/epic/README.md`,
`.claude/epic/NARRATIVE.md`, `adapters/ollama/README.md`, and the `CONTRIBUTING.md`
issue-coordination and pull-request sections.

Read as data: all eight `services/*/contracts/service.json`,
`contracts/capability-offices.json`, `contracts/fixtures/capability-map.reference.json`,
`contracts/capability-map.schema.json`, `contracts/service-manifest.schema.json`,
`contracts/issue-metadata.schema.json`, `contracts/ticket-transition.schema.json`,
`contracts/ticket-queue-policy.json`, `contracts/event-envelope.schema.json`,
`contracts/receipt.schema.json`, `contracts/operation-plan.schema.json`,
`contracts/observation.schema.json`, `contracts/model-binding.schema.json`,
`contracts/domain-owners.json`, `contracts/kernel-parity.json`,
`conformance/scenarios.json`, `.claude/epic/tree.json`, `.claude/epic/offices.json`,
`.claude/epic/villages.json`, `bindings/mcp/manifest.json`,
`adapters/ollama/bindings/*.json`, `adapters/ollama/observations/parity-live.json`,
`.local/observations/latest.json`, `services/asset/conformance/BASELINE.md`, and the git
log (122 commits).

**Not read, and it matters:** the live GitHub issue bodies — only the checked-in
`tree.json` projection, `synced_at: 2026-08-24T15:52:36Z`; `lineage/` evidence;
`docs/documentation.html`; `experiments/`; `infrastructure/`; `workers/`; `diagrams/`;
the 41 decision records other than 0036 and 0038 (statuses only);
`conformance/oracle-controls.json` beyond its authority cases. Four of six diagrams are
recorded as stale in `CLAUDE.md`, so nothing here rests on them.

---

# 1 · Executive finding

**The product is explained. What is missing is the layer that says who is being served
and what they are promised, and the join keys that would let anything be counted against
it.**

## What already exists, and is better than expected

`OBSERVED`. The downward half of the chain is largely built, and built as rebuildable
projections with staleness detection rather than as hand-maintained prose:

| Edge | Coverage | Where |
| --- | --- | --- |
| operation → logical endpoint | 102 / 102 | `services/*/contracts/service.json`, `sov://<service>/<operation>` |
| operation → owning service | 102 / 102 | same |
| operation → office and counter | 102 / 102 | `contracts/capability-offices.json` |
| operation → required authority | 102 / 102 | same |
| operation → effect class | 102 / 102 | same |
| operation → admitted actor kinds | 102 / 102 | same |
| operation → transport activation | 102 / 102 (4 transports each) | `contracts/fixtures/capability-map.reference.json` |
| operation → PRD requirement | **99 / 102** | `service.json` `requirement` field |
| operation → SPEC kernel transition | **23 / 102** | `service.json` `kernel_transition` field |
| operation → preconditions, commit, refusals | 102 / 102 | `service.json` |

The capability map is rebuilt from the manifests and the offices table alone, carries an
`input_state_digest`, refuses to answer when stale, and has eight named defeating fixtures
(`decisions/0038`). A repository that can already answer "which doors exist, who may use
them, and what each costs" for 102 operations is well past where this kind of discovery
usually starts.

## Where the chain actually breaks

`DERIVED`. Three places, in order of what they cost.

**Break 1 — above the requirement. There is no product layer.**

`PRD.md` has a five-line `Users` section listing six actor classes, and nine requirements
named `Propose`, `Remember`, `Cross`, `Gate and retract`, `Typed authority`, `Founder
judgement budget`, `Independent qualification`, `Joint sign`, `Bring your own model`.
These are engineering predicates, not promises. Nine of them carry 102 operations:
`PROD-I-2 · Remember` alone is cited by 32, `PROD-I-6` by 20. At that fan-in the
requirement edge does not discriminate — it can tell you an operation exists because of
"Remember", which is true of a third of the node.

Searched the whole repository outside `lineage/`: the words **journey**, **user need**,
and **product promise** appear zero times. There is no addressed artifact anywhere naming
a person, what they came to do, or what the system undertakes to let them do. The nearest
things are `conformance/scenarios.json` (nine scenarios, one per requirement, each with
`given` / `desired` / `gap`) and the single filed story `#67`, which uses `Expected` /
`Found`. The story kind is exactly the right shape, and there is one of them.

**Break 2 — between work and operation. A ticket cannot name what it is building.**

`contracts/issue-metadata.schema.json` has 47 properties. None is `capability`,
`operation`, `service`, `endpoint`, or `requirement`. A ticket carries `village`,
`bit_id`, `standing`, `horizon`, `authority`, `effect_class`, `evidence_pointer`,
`walker_receipt`, `requires`, and `dependency_channels` — a complete coordination
contract with no product referent in it.

Tickets and operations are both grouped by office. `.claude/epic/offices.json` puts 51
issues into 12 offices; `contracts/capability-offices.json` puts 102 operations into the
same 12 offices. They have never been joined to each other, and `decisions/0038` says so
in its own Consequences section: *"They must not disagree, and nothing yet checks that
they do not."*

**Break 3 — below the run. Nothing records what an operation consumed.**

`contracts/receipt.schema.json` (16 properties) and `contracts/event-envelope.schema.json`
(13 properties) have no field for usage, cost, duration, or tokens.
`contracts/operation-plan.schema.json` declares `limits` as literally `{"type": "object"}`
— required, and entirely unconstrained. `RESOURCE_CONSUMPTION` is one of three effect
classes in `AGENTS.md`, `SPEC.md`, and every service manifest, and no contract field
anywhere records the consumption it names.

`services/asset/conformance/BASELINE.md` states the consequence for the one executable
participant: *"PROD-I-1 · Propose | FAIL | proposal lacks content address, source
addresses, and cost record."* The single Phase-I requirement that demands a recorded cost
is failed by the reference implementation, and has been since 2026-08-22.

## Classification of the primary gap

`DERIVED`, in order:

1. **Identity** — the largest gap. There is no `journey`, `need`, or `promise` identifier
   at all, and no join key between a ticket and an operation. Everything else follows.
2. **Instrumentation** — second. Two places in the repository measure what a run consumed,
   and both are dead ends (§9).
3. **Project metadata** — third and smallest. The tracker schema is thorough and honest
   about being a projection; it is missing two fields, not a rewrite.
4. **Documentation** — last, and smaller than it looks. The semantics are written down
   extensively. What is unwritten is about a page.

## The finding not to miss

`OBSERVED`. **The Atlas vocabulary already exists in this repository, as filed, unbuilt
work.** Issue `#40` is titled *"Charting contract — canonicalize typed points, crossings,
coverings, and paradigms"* — `kind: bit`, village `ground-and-evidence`, standing `OPEN`,
horizon `NEXT`, `requires: [#6, #7, #14, #25]`. Issue `#41` is *"Skill and capability
graph — derive competence from SDLC and registry contracts"*. Issue `#48` is *"Skill
relation schema — validate Requirement and Capability declaration shape"* — the exact
relation this spine needs, already filed as a stub under `#41`.

`SOV.md` line 120 already refers to *"Dynamic Chart compilation"* as a boundary tracked by
`#40` and `#42`, and `#42` is *"Chart compiler bindings — lower governed charts into
human/model operator environments"* — where a **chart** is something compiled and lowered
into an operator environment, not a semantic territory.

Five of the eight proposed Atlas terms are therefore already spoken for by an open
boundary that means something adjacent but different. This is not new vocabulary to
introduce; it is existing vocabulary to build, redirect, or renumber, and that is Bdo's
call (§14, Q4).

## Direct answer to the owner's opening question

> *"It's possible we need something that captures what the 'product' is but it's well
> explained throughout so I don't know if that's needed."*

`PROPOSED`. Both halves of that instinct are right. It **is** well explained — across
`README.md`, `SYSTEM.md` Scope, `PRD.md` Product outcome, `AI-NATIVE.md` Definition, and
`BYOM.md`. And it is explained **as a system**, never as an experience: each of those
passages says what the environment is and what it refuses, and none says what a person
walks in wanting.

What is missing is not a second PRD. It is one addressed layer between "Soveraeign" and
`PROD-I-1..9` naming the participant, the need, and the promise, so a requirement has a
parent and an operation has a reason. Roughly a page, and the only genuinely new prose
this spine needs. Everything else missing is join keys and record fields.

---

# 2 · Semantic source and authority map

`OBSERVED` unless marked. `AGENTS.md` names eight files as the Design System of Record;
the categories below are the ones the discovery brief asked about, mapped onto what the
repository actually assigns.

| Category | Declared owner | Standing | Overlap / contention |
| --- | --- | --- | --- |
| PRODUCT IDENTITY | **none declared** | — | Said three ways: `README.md` (no status line), `SYSTEM.md` Scope (`PROVISIONAL SYNTHESIS`), `PRD.md` Product outcome (`FREEZE CANDIDATE`). `STATUS.yaml` owns only `product_name` and `category`. |
| PRODUCT INVARIANT | `CONTRACT.md` C1–C15 | `PROPOSED FOR OWNER RATIFICATION` | Clean. Single owner, no competitor. |
| USER / ACTOR | **four registries** | mixed | `PRD.md` Users (6 prose classes); `CLASSIFICATION.md` Participation and boundary roles (10 terms); `SPEC.md` `actor_kind` enum (4 values); `.claude/epic/offices.json` `cast` (7 tellers). The last three agree by construction; `PRD.md` is the odd one and names *maintainers* and *federated nodes* that appear nowhere else. |
| USER NEED | **none** | — | Zero occurrences repository-wide. Nearest: `conformance/scenarios.json` `given`/`desired`; story `#67` `expected`/`found`. |
| PRODUCT PROMISE | **none** | — | Zero occurrences. Nearest: `README.md` prose and `PRD.md` Product outcome. |
| DOMAIN / CHART | **five groupings** | mixed | `CLASSIFICATION.md` Initial service map (4 services, now 8); `services/README.md` table (8); `.claude/README.md` harness domains (9); `.claude/epic/villages.json` villages (4); `contracts/capability-offices.json` counters (12). `services/registry/CHARTER.md` names eight such tables and states that *"nothing checks any of them against the others, so they drift silently"*. |
| STATION | `contracts/capability-offices.json` `counters` | `PROPOSED` (0038) | Exists under the name **counter**, inside **office** (`FRONT`/`BACK`). 12 counters. Not called a station anywhere. |
| JOURNEY | **none** | — | Nearest: nine `conformance/scenarios.json` entries (requirement-shaped, not user-shaped) and each service charter's *Proving narrative* / *Initial proving narrative* section. |
| CAPABILITY | `contracts/capability-map.schema.json` + reference projection | `PROPOSED` | Strong owner. **Three senses of the word collide**: a capability-map row; `SPEC.md` `AuthorityGrant.capability`; `SPEC.md` `ModelBinding.capabilities` (e.g. `completion`, `tools`). Nothing disambiguates them. |
| CANONICAL OPERATION | `contracts/service-manifest.schema.json` + eight `service.json` | manifest `BUILT_SELF_TESTED_NOT_WITNESSED` | Strong owner. Address form `sov://<service>/<operation>`, id form `<service>.<operation>`. |
| INTERFACE | split | mixed | `logical_endpoint` in each manifest (transport-neutral); transports in `capability-offices.json`; concrete bindings in `bindings/{mcp,console,sov}`; `services/gateway/` charters the resolver. `OPEN-SEAMS.md` S18: two layers named gateway. |
| SERVICE | `services/<domain>/CHARTER.md` + `contracts/service.json` | 3 built, 5 chartered | Clean; `CLASSIFICATION.md` owns the term. |
| ROLE | `CLASSIFICATION.md` | `OWNER_ACCEPTED_CANONICAL_VOCABULARY` per `STATUS.yaml` | Clean. `decisions/0020` adds that Owner is a context, not a role. |
| AUTHORITY | `SPEC.md` `AuthorityGrant` + `STATUS.yaml` `authority` | accepted | Contended in two live seams: S12 (what surface carries Bdo's ratification) and Console-vs-permits (who owns `authority-grant`; `services/gateway/CHARTER.md` Open section). |
| REQUIREMENT | `PRD.md` | `FREEZE CANDIDATE · NOT OWNER-RATIFIED` | Clean owner, coarse instrument (9 for 102). |
| SPECIFICATION | `SPEC.md` + `contracts/kernel-transitions.json` | `PROPOSED · OWNER FREEZE PENDING`; `STATUS.yaml` notes SPEC moved after acceptance under 0034 | S17: a declared refusal code (`INCOMPLETE_PROPOSAL`) nothing can emit. |
| IMPLEMENTATION | `services/*/src/` | 2 507 lines across 3 services | Clean. |
| QUALIFICATION | `AI-NATIVE.md` + `conformance/` | `FREEZE_CANDIDATE` / executable | Per-surface records exist for **2 of 8** services (`asset`, `gateway`). |
| WORK COORDINATION | `CONTRIBUTING.md` + `contracts/issue-metadata.schema.json` + `.claude/epic/` | `OWNER_ACCEPTED` for ticket kinds | Explicitly a projection: *"Display labels are projections of that metadata, not a second authority."* |
| EXECUTION TELEMETRY | **none declared** | — | Fragments in `.local/observations/latest.json` (gitignored), `scripts/sovschedule/ledger.py` (ledger file absent), `adapters/ollama/observations/`. |
| RESOURCE ACCOUNTING | **none declared** | — | Fragments: `ModelBinding.usage_meter`/`cost_meter`; `contracts/domain-owners.json` `budget`; `scripts/verify.py` wall-time grades; `OperationPlan.limits` (empty schema). Five unrelated meanings of the word *budget* (§13, C3). |
| EVIDENCE | `lineage/` (historical) + `reports/` + `contracts/observation.schema.json` + `contracts/receipt.schema.json` | mixed | Ticket-level `evidence_pointer` is real on **18 of 51** issues; `walker_receipt` is `PENDING` on **51 of 51**. |

## Overlaps worth naming

`DERIVED`.

- **Actor is declared four times.** Three agree; `PRD.md` does not and is the oldest.
- **Domain is grouped five ways** and the Registry charter already treats that as the
  problem it exists to solve.
- **Capability means three different things** across `SPEC.md` and the capability map.
- **Budget means five different things** (§13, C3).

## Missing owners

`DERIVED`. Four categories have no owner at all: **user need**, **product promise**,
**journey**, and **resource accounting** — plus **execution telemetry**, which has
fragments but no owning document. Product identity has three claimants and no declared
owner in the `AGENTS.md` Design System of Record list.

Not fixed here.

---

# 3 · Actor and user inventory

`OBSERVED` for `observed_description`, `interfaces_or_stations`, `evidence`, `standing`.
`DERIVED` for `needs` and `expected_capabilities` — no artifact states a need, so those
lines are read out of what each actor is permitted and asked to do. Marked where it matters.

```yaml
role: Bdo — the enterprise owner
observed_description: >-
  Holds product-intent, naming, judgement and phase-gate authority. "Owner is not a role:
  it is the context that sets an operator's Binding and Projection over whatever role they
  hold" (decisions/0020; .claude/epic/offices.json cast_note). At the Operator Desk Bdo is
  a HUMAN/operator; Owner is what shapes the desk.
needs: [DERIVED] see a decision that needs him without hunting; answer it where the answer
  becomes a record; know what was spent and on what; not be asked for pre-approval.
expected_capabilities: resolve-judgement (HUMAN only); ratify-proposal; declare-owner;
  retire-owner; counter-observation; grant / revoke. Twelve of 102 capabilities are
  actor_kinds:[HUMAN] and every operation requiring ratify:judgement is among them.
authority_relationship: source of judgement-typed authority. The gate is ACCEPTANCE over
  evidence, never pre-approval (decisions/0023).
interfaces_or_stations: FRONT/operator-desk. Intended surface is a Human Binding
  (services/console/CHARTER.md, first slice). None built.
evidence: STATUS.yaml authority; AGENTS.md Authority; decisions/0020, 0023;
  contracts/capability-offices.json.
standing: authority OWNER_ACCEPTED. The surface that would carry it is not built.
open_questions: OPEN-SEAMS.md S12 — whether a CODEOWNERS review click is the ratification
  grant. Bdo said 2026-08-23 it cannot be; the replacement is chartered and unbuilt.
```

```yaml
role: Human operator
observed_description: A person working inside the node through a Human Binding
  (.claude/epic/offices.json cast). actor_kind HUMAN, role operator.
needs: [DERIVED] do domain work; see what happened while away; be told what concerns them.
expected_capabilities: 59 FRONT-office capabilities admit HUMAN — console.post,
  console.open-thread, asset.ingest-asset, proofing.add-annotation among them.
authority_relationship: untrusted outside explicitly recorded grants (SPEC.md Trust model).
interfaces_or_stations: FRONT/operator-desk, review-desk, job-window, drafting-window, door.
evidence: SPEC.md Interface parity; services/console/CHARTER.md Human and model participation.
standing: no Human Binding implementation exists. bindings/console/interface.json declares
  one and holds no code (adapters/ollama/README.md).
open_questions: the PRD.md two-binding proof needs one human-facing binding. There is none.
```

```yaml
role: Model operator
observed_description: A model working inside the node through a Model Binding; Sov when the
  portable profile is loaded, Claude in an interactive session. Same world, same record.
needs: [DERIVED] discover legal operations from the artifact alone; act inside a live grant;
  refuse coherently; hand off without private state.
expected_capabilities: every capability whose actor_kinds includes MODEL — 90 of 102.
  Excluded: the twelve ratify:judgement HUMAN-only rows and the SYSTEM-only rows.
authority_relationship: output is always a proposal, recording, report or observation;
  fluency never changes standing (SPEC.md Trust model; CONTRACT.md C11).
interfaces_or_stations: FRONT/operator-desk and model-counter; the MCP surface
  (bindings/mcp/, six tools) is the only machine transport that exists.
evidence: CONTRACT.md C1; AI-NATIVE.md Reachability gate; bindings/mcp/manifest.json.
standing: MCP binding PROPOSED and built; the capability map records MCP as
  DECLARED_NOT_ACTIVATED on all 102 rows (§8, defect D1).
open_questions: none blocking. The reachability gate is the whole AI-native argument.
```

```yaml
role: Person bringing an existing model or agent (BYOM)
observed_description: The node owner selects a compatible local or remote model through a
  declared Model Binding; identity, version, runtime, host, capabilities, data boundary,
  usage and cost are recorded configuration (BYOM.md; SYSTEM.md).
needs: [DERIVED] keep custody while changing models; know what each model cost; get a
  visible refusal, never a silent substitution.
expected_capabilities: the SPEC.md invoke_model transition; projection.package-context and
  read-context-package at FRONT/model-counter.
authority_relationship: a binding grants no capability by existing; every invocation still
  checks the actor's scoped authority (SPEC.md ModelBinding).
interfaces_or_stations: FRONT/model-counter — two capabilities, both PROPOSED.
evidence: BYOM.md; contracts/model-binding.schema.json; adapters/ollama/ with two live
  bindings (qwen3:4b, gpt-oss:20b) and one recorded two-model parity run.
standing: adapter BUILT_SELF_TESTED_NOT_WITNESSED. invoke_model has no kernel
  implementation (PROD-I-9; CLAUDE.md known gaps).
open_questions: adapters/ollama/README.md queues five for Bdo, including whether a locally
  hosted model's cost is zero for budget purposes or whether wall clock spends against a
  run's limits.
```

```yaml
role: Sov
observed_description: A portable context profile loaded by a compatible underlying model —
  not a model, provider, runtime, host, credential, authority slot, durable memory or
  second kernel (SOV.md; AGENTS.md).
needs: [DERIVED] a declared context, one named task, an effect envelope, a place to hand off.
expected_capabilities: whatever the loaded model's grants admit. Default candidate for the
  Control tier, never its automatic holder.
authority_relationship: loading Sov grants nothing.
interfaces_or_stations: FRONT/operator-desk (offices.json chartered_in names SOV.md).
evidence: SOV.md; bindings/sov/profile.json; issue #45.
standing: OWNER_ACCEPTED_CONTEXT_PROFILE_BUILT_SELF_TESTED_NOT_WITNESSED. No live activation.
open_questions: none product-defining.
```

```yaml
role: Controller / Orchestrator / Worker / Witness
observed_description: The three SDLC tiers plus the independent verifier. Grants flow down
  and narrow; reports flow up and never self-settle (SDLC.md, Three tiers).
needs: [DERIVED] Controller — a concern registry it does not privately own. Orchestrator —
  leases and fences. Worker — one bounded task. Witness — a path the builder did not control.
expected_capabilities: no capability-map row names a tier. Tiers are harness roles under
  .claude/agents/ with no service operations of their own.
authority_relationship: every tier is an operator under grant; none may ratify judgement.
interfaces_or_stations: FRONT/job-window (one capability, asset.request-derivative);
  BACK/inspectorate (nine, all PROPOSED).
evidence: SDLC.md; CLASSIFICATION.md; .claude/agents/.
standing: sdlc_loop_status OWNER_ACCEPTED_ACCEPTANCE_NOT_APPROVAL. The loop is a skeleton
  and its release gate has never been exercised against a real concern (SDLC.md Acceptance).
open_questions: the Observation Service that would make witnessing a service rather than a
  script is CHARTERED_BOUNDARY_NOT_IMPLEMENTED (decisions/0041).
```

```yaml
role: Domain owner — the "skillful owner over a slice"
observed_description: The participant accountable for a domain, the mandate given them, the
  requirements they answer, their resource budget, their deadline, and the separate
  participant that witnesses their work (services/registry/CHARTER.md, Owner records).
needs: [DERIVED] a mandate; an envelope they can spend inside; a witness who is not them.
expected_capabilities: registry.declare-owner, supersede-owner, retire-owner — all PROPOSED.
authority_relationship: an owner record names the authority an owner would need; it never
  holds it. Owner and witness may never be the same participant, and that is checked today.
interfaces_or_stations: BACK/permits-office.
evidence: contracts/domain-owners.json — three owners (registry, record, gateway), each
  with mandate, requirements (PROD-I-*), budget {max_usd_per_run: 5, runs_per_period: 5,
  period: WEEK}, deadline, witness. Checked by scripts/sov_owners.py check.
standing: PROPOSED. Budgets and deadlines are drafts until Bdo sets them.
open_questions: [DERIVED] the budget is declared and nothing spends against it. No record
  anywhere joins consumption to a domain owner (§9).
```

```yaml
role: Node owner / peer node
observed_description: A Soveraeign Node is a locally sovereign operating instance; a peer
  node is SYSTEM/node on the far side of a federation crossing.
needs: [DERIVED] custody; a governed crossing that moves nothing until admitted.
expected_capabilities: none reachable. The federation crossing and the public projection
  are contracted and graded; neither moves a byte and no transport exists for either.
authority_relationship: node identity is contracted; there is no admission transition.
interfaces_or_stations: FRONT/door (seven capabilities, all PROPOSED);
  BACK/beyond-the-node (zero capabilities; issue #24; locked in Phase I).
evidence: decisions/0039; contracts/node-identity.schema.json;
  contracts/federation-crossing.schema.json; STATUS.yaml.
standing: PROPOSED_CONTRACT_BUILT_SELF_TESTED_NO_TRANSPORT.
open_questions: decisions/0039 carries three unruled questions. OPEN-SEAMS.md S19 — a
  public projection built from console records cannot fill published_by honestly.
```

```yaml
role: External system / enterprise system
observed_description: Reached through a declared adapter. "It has no expectations of its
  own; its story is told on its behalf by the operator who integrated it"
  (.claude/epic/NARRATIVE.md cast).
needs: none of its own, by construction.
expected_capabilities: adapters/github (the only directory permitted to call the GitHub
  API); adapters/ollama.
authority_relationship: an adapter receives no authority by transporting a request.
interfaces_or_stations: FRONT/model-counter for models. The GitHub registrar is not on the
  capability map at all.
evidence: adapters/README.md; adapters/github/README.md; decisions/0016, 0044.
standing: github registrar BUILT_SELF_TESTED_NOT_WITNESSED.
open_questions: the registrar performs the repository's only real EXTERNAL_WORLD write
  under --apply while no_external_effects_in_phase_i stands; decisions/0044 is PROPOSED
  and unruled.
```

```yaml
role: Maintainer; federated enterprise node
observed_description: Named only in PRD.md Users — "Later, maintainers and federated
  enterprise nodes". Appears in no other registry.
needs: unknown.
expected_capabilities: none declared.
authority_relationship: undeclared.
interfaces_or_stations: none.
evidence: PRD.md Users, one line.
standing: [DERIVED] vestigial. Nothing in CLASSIFICATION.md, offices.json or the
  capability map knows this actor exists.
open_questions: OWNER — is "maintainer" a real participant class or leftover wording?
```

## What the actor inventory shows

`DERIVED`. Ten actor classes. **One** (Bdo) has an authority relationship written in a
governing document. **Four** have a station in the offices table. **Zero** have a recorded
need — the `needs` line above is inference in every single case. That is the cleanest
single measurement of Break 1.

---

# 4 · Product-promise inventory

`DERIVED` from attributed text; each row cites where the language actually is. A promise
absent from the repository is recorded as `UNKNOWN` rather than supplied.

| # | Candidate promise | Class | Attribution |
| --- | --- | --- | --- |
| P1 | People and models act through the same records, permissions, transitions, evidence and history | `EXPLICIT` | `CONTRACT.md` C1; `README.md` lede; `SYSTEM.md` Scope; `AI-NATIVE.md` Definition |
| P2 | The enterprise keeps custody of its operational memory and authority; losing a provider does not take them | `EXPLICIT` | `SYSTEM.md` Ownership; `BYOM.md`; `AI-NATIVE.md` check 8; `PRD.md` PROD-I-9 |
| P3 | Bring your own model: swap the model without changing state, standing, authority, receipts or contracts | `EXPLICIT` | `BYOM.md` BYOM definition; `PRD.md` PROD-I-9; `SPEC.md` `ModelBinding` |
| P4 | Every crossing returns a receipt — including refusal, failure and unresolved judgement | `EXPLICIT` | `CONTRACT.md` C8; `SPEC.md` `Receipt`; every manifest's `refusals` list |
| P5 | You can retract without pretending it never happened, and without a false rollback claim | `EXPLICIT` | `CONTRACT.md` C9; `PRD.md` PROD-I-4; `AI-NATIVE.md` Retraction axis |
| P6 | Human judgement is protected: requests queue without blocking, and where it was spent is reported | `EXPLICIT` | `PRD.md` PROD-I-6; `README.md` "human judgement is the scarce resource the system protects" |
| P7 | You can see why anything is what it is — source, version, reader, configuration, omissions | `EXPLICIT` | `CONTRACT.md` C2; `PRD.md` PROD-I-2; `AI-NATIVE.md` Provenance axis |
| P8 | A fresh person or model can become safely useful from the artifact alone | `EXPLICIT` | `CONTRACT.md` C12; `PRD.md` PROD-I-7; `AI-NATIVE.md` check 6 |
| P9 | A personal node is first-class and can grow to a team or federate without migrating its authority into someone else's system | `EXPLICIT` | `SYSTEM.md` Ownership and model portability; `BYOM.md`; `CLASSIFICATION.md` Ownership profiles |
| P10 | Discover what you can do here — what can be asked of this node, by whom, over what | `STRONGLY_DERIVED` | `services/gateway/CHARTER.md` states the need and that *"There is no single place that answers"* it; `console.discover-operations` is built; the `AI-NATIVE.md` reachability gate implies it. No document promises it to a user. |
| P11 | Delegate bounded work and get back something you can check | `STRONGLY_DERIVED` | `SDLC.md` three tiers; `SPEC.md` `Run`, lease, `observe_run`; `asset.request-derivative` at FRONT/job-window. Framed as internal process, never as a user promise. |
| P12 | Continue work across a boundary where context was lost | `STRONGLY_DERIVED` | `decisions/0036` built exactly this and calls it *"the record path that carries work across a boundary where context is lost"*. Stated nowhere as a product promise; it arrived as an implementation choice. |
| P13 | Interact with another authorized node | `WEAKLY_DERIVED` | `SYSTEM.md` Federation subsystem; `decisions/0039`. Explicitly out of Phase I (`PRD.md` Non-goals). |
| P14 | Install and operate your own node | `WEAKLY_DERIVED` | `infrastructure/` (not read this pass); `SPEC.md` Local operation. No install path, no first-run experience, no document that treats installation as an experience. |
| P15 | Version-pinned review and approval of a work product | `WEAKLY_DERIVED` | `services/proofing/CHARTER.md`; eleven capabilities at FRONT/review-desk, all `PROPOSED`. The only promise aimed at ordinary enterprise work rather than at the system's own governance. |
| P16 | Find something previously recorded | `CONTRADICTORY` | `services/projection/` charters search; `services/asset/` also ships `search` and `neighbors`. `OPEN-SEAMS.md` S14 carries the conflict — *"Two owners of the asset projections."* |
| P17 | What the product does for a business, as opposed to for its own governance | `UNKNOWN` | Every promise above except P15 is about how the system governs itself. `ROADMAP.md` defers "one bounded real enterprise workflow" to F5, and `OPEN-SEAMS.md` S10 carries this exact question as an open seam. |
| P18 | Which promise is worth building first | `OWNER_JUDGEMENT_REQUIRED` | `README.md` Immediate objective refuses to rank the two lanes: *"ordering them is owner judgement, and this file does not hold it."* |

## Reading

`DERIVED`. Nine promises are explicit and all nine are **properties of the record**, not
things a person came to do. The three strongly-derived ones — P10 discovery, P11
delegation, P12 continuity — are the closest the repository has to user-facing promises,
and all three arrived as engineering consequences rather than stated intent. P12 most
visibly: `decisions/0036` had to argue for it against the charter's declared first slice.

P17 is the row that should concern the owner. `OPEN-SEAMS.md` S10 has carried it since
founding, and it is precisely the question a product canon would have to answer.

---

# 5 · Candidate Atlas / charts

`DERIVED`. Ten candidate territories, tested against the seven questions in the brief. A
directory is not a chart: several charts below have no directory, and several directories
collapse into one chart.

### C-NODE · The node itself

1. **Problem it exists for:** somebody must own a sovereign instance — its identity, its
   ground, its continuity when providers vanish.
2. **Concepts:** node identity, ownership profile (personal / team / enterprise), custody,
   host, deployment topology.
3. **Lifecycle:** none declared. Node identity is contracted with **no admission
   transition** (`STATUS.yaml`).
4. **Capabilities:** zero rows under a `node` service. `gateway.bind-transport` at
   BACK/ground is the nearest thing.
5. **Crosses:** every chart. `beyond-the-node` is its far edge.
6. **Realized by:** `contracts/node-identity.schema.json`, `infrastructure/`, issues #37, #39.
7. **Semantically defined?** Defined in `SYSTEM.md` and `CLASSIFICATION.md`; **not**
   realized as a service. The only chart with neither a service nor a counter.

### C-DOOR · Ingress and egress

1. Nothing outside a service can currently ask a service for anything except by importing
   its Python package or running two CLI commands.
2. Request, logical endpoint, capability resolution, authority check, route, gateway
   receipt, refusal record, transport activation.
3. `accept → resolve → check → route → return`, each step refusing by name.
4. Seven capabilities at FRONT/door, all `PROPOSED`.
5. Crosses permits (authority), record (receipts), and every domain chart.
6. `services/gateway/`; issues #16, #17.
7. **Semantically defined**, thoroughly. `services/gateway/CHARTER.md` is the best-written
   chart document in the repository.

### C-PERMITS · Identity, authority, gates

1. No counter can currently know who is standing at it. `.claude/epic/NARRATIVE.md`:
   *"This is the widest gap between front and back."*
2. Identity, actor, grant, scope, budget, revocation, capability broker, registry entry,
   owner record.
3. `AuthorityGrant` `valid_from → valid_until → revoked_at`; grant and revoke both append.
4. Seventeen capabilities at BACK/permits-office — three built (`console.grant`,
   `console.revoke`, `console.list-grants`), thirteen registry rows `PROPOSED`, plus
   `gateway.check-authority`.
5. Crosses everything. Eighteen open issues declare `requires: #14`.
6. `services/registry/`, `services/console/` (grants); issues #11–#15.
7. **Defined and contested.** Whether the Console or a separate permits surface owns
   `authority-grant` is a default taken in `decisions/0040`, not a settled boundary.

### C-RECORD · The append-preserving journal

1. Reports are not observations, and history must survive correction.
2. Entry, digest chain, counter-record, receipt, subject projection, retraction.
3. `RECORDED → ADMITTED → RATIFIED → EFFECTIVE`, with `COUNTERED` as an event outcome.
4. Ten capabilities at BACK/record — eight built.
5. Crosses everything; every other chart writes here.
6. `services/record/`; issues #6, #7, #8, #10, #25, #27.
7. **Defined and built.** The strongest chart in the repository.

### C-ASSET · Governed enterprise identities

1. An asset is not its payload, and derivations must stay attributable.
2. Asset, version, payload, derivation, use record, shared custody, lease.
3. `ingest → version → derive → use → retract`.
4. Eleven capabilities — all `BUILT`.
5. Crosses record, permits, projection (S14 contested), proofing.
6. `services/asset/`; issues #8, #27.
7. **Defined and built** — and failing all nine conformance requirements
   (`services/asset/conformance/BASELINE.md`).

### C-REVIEW · Proofing

1. Version-pinned review, annotation and decision — the one chart aimed at ordinary work.
2. Session, round, annotation, reviewer assignment, comparison, decision.
3. `open-session → annotate → propose-decision → ratify-decision → close-session`.
4. Eleven capabilities at FRONT/review-desk, all `PROPOSED`.
5. Crosses asset (exact version identifiers), permits, record.
6. `services/proofing/`; issues #22, #28.
7. **Defined, not implemented.**

### C-PATTERN · Retrieval and competence

1. Finding something previously recorded, and packaging it for a model.
2. Collection, text / graph / vector configuration, index, build, retrieval receipt,
   context package, fidelity observation — and separately charts, points, coverings and
   paradigms (#40).
3. `declare → configure → build → retrieve → observe fidelity`.
4. Six at BACK/pattern-room, five search and traverse rows at FRONT/operator-desk, two at
   FRONT/model-counter — all `PROPOSED`.
5. Crosses asset (S14 conflict), model-counter, registry.
6. `services/projection/`; issues #40, #41, #47, #48.
7. **Partly defined.** `#40` names the charting vocabulary and nothing implements it;
   `NARRATIVE.md` calls this *"the newest and least settled line"* and notes a RED
   engagement (`#57`) is open against the foundation underneath it.

### C-INSPECT · Independent observation and qualification

1. An executor's report is not evidence the world changed (C7), and `AI-NATIVE.md` check 3
   reads `UNATTESTABLE` on every surface assessed.
2. Observer registration, declared predicate, observation request, independence relation,
   observation, attestation, qualification record.
3. `request → declare-predicates → observe → attest`, with independence inferred from the
   run's record rather than declared by the observer (Bdo's ruling, 2026-08-23).
4. Nine capabilities at BACK/inspectorate, all `PROPOSED`.
5. Crosses every chart that runs anything.
6. `services/observation/`, `conformance/`; issues #9, #23, #26, #32, #49, #57.
7. **Defined**, chartered 2026-08-23 (`decisions/0041`), not implemented.

### C-OPERATOR · The operator's own session

1. Continuity, attention, and where a human right actually gets exercised.
2. Session, channel, thread, post, notification, judgement request, judgement resolution,
   setting, dashboard and activity projection, publication.
3. session `OPEN → CLOSED`; thread `OPEN → ARCHIVED`; judgement request
   `QUEUED → RESOLVED | WITHDRAWN | EXPIRED`; notification `ISSUED → ACKNOWLEDGED`.
4. Twenty-six capabilities — sixteen `BUILT` (the continuity path), ten `PROPOSED`
   (notifications, settings, judgement, receipt reads, dashboards).
5. Crosses record (writes), every sibling (reads), permits (grants it currently owns).
6. `services/console/`; issues #30, #45.
7. **Defined and half-built.** The half that is built is not the half the charter named
   as first (`decisions/0036`).

### C-MODEL · Bringing a model in

1. Use your own model without surrendering the record to its provider.
2. Model binding, adapter, provider, data boundary, input projection, omissions, usage
   meter, cost meter, fallback policy, invocation record.
3. `invoke_model` with four declared refusals plus three proposed adapter refusals.
4. Two capabilities at FRONT/model-counter, both `PROPOSED`. `invoke_model` has no kernel
   implementation.
5. Crosses permits, record, pattern (context packages), inspect.
6. `adapters/ollama/`, `bindings/`, `BYOM.md`; issues #19, #29.
7. **Defined and adapter-built.** The only chart with real measured runs.

## Charts with no service, and work with no chart

`DERIVED`.

- **C-NODE has no service.** The only territory defined in a governing document with no
  `services/<domain>/` and no counter of its own.
- **The GitHub coordination registrar has no chart.** `adapters/github/` performs the
  repository's only real external write and appears on no capability-map row, in no office
  and in no chart. It is governed by `decisions/0016` and `0044` and by `CONTRIBUTING.md`,
  and is structurally invisible to the map.
- **`drafting-window` and `beyond-the-node` hold zero capabilities**
  (`decisions/0038`, Residuals). Two of twelve counters are empty rooms — and
  `drafting-window` is where a decision record or a charter gets written, which is a
  significant share of what actually happens here.

---

# 6 · Station inventory

`OBSERVED`. The concept exists under the name **counter**, grouped into **office**
(`FRONT` = where an actor meets the system, `BACK` = what holds that meeting up). Twelve
counters over 102 capabilities, defined in `contracts/capability-offices.json` and used to
group issues in `.claude/epic/offices.json`. `FRONT` 59, `BACK` 43.

The Console is **one counter among twelve**, not the product.

```yaml
station: FRONT / operator-desk
intended_actor: HUMAN or MODEL operator; Bdo arrives here in Owner context
job_to_be_done: [DERIVED] do work inside the node and keep continuity across sessions
what_the_actor_can_see: threads, posts, publications, session context, grants held
what_the_actor_can_do: 38 capabilities — the largest counter; 16 built
entry_conditions: an operator session (console.open-session), which is built
exit_or_continuation: console.close-session; the unread cursor is the continuation edge
reachable_operations: the console continuity path over CLI; asset.* by in-process import
authority_projection: grants are journal records; revocation appends (decisions/0036 R1)
observable_results: every transition emits one EVENT then one terminal RECEIPT (append.py)
failure_experience: a named refusal appended to the journal — "a transition that refused
  and left no trace would be indistinguishable from one nobody attempted"
related_journeys: J1 continuity; J8 judgement (declared, unreachable); J9 inspect
evidence: services/console/src/; .claude/hooks/console_session.py; 31 tests
semantic_gaps: no Human Binding, CLI only. KNOWN-GAPS records that reading continuity
  replays the whole journal on every call.
```

```yaml
station: FRONT / door
intended_actor: anything outside a service; later, a peer node
job_to_be_done: turn a request into a call on a service, or refuse it on the record
what_the_actor_can_see: nothing — not implemented
what_the_actor_can_do: 7 capabilities, all PROPOSED, every transport DECLARED_NOT_ACTIVATED
entry_conditions: a well-formed envelope on an activated transport
exit_or_continuation: return-receipt unaltered, or refuse-request recorded
reachable_operations: none
authority_projection: checks a grant the Console issued; cannot widen one or grant on an
  actor's behalf
observable_results: a gateway receipt naming both the route and the service receipt
failure_experience: MALFORMED_REQUEST, TRANSPORT_NOT_ACTIVATED, ENDPOINT_UNKNOWN,
  AUTHORITY_REFUSED, GRANT_NOT_COVERED, SERVICE_UNREACHABLE, EFFECT_CLASS_REFUSED,
  RECEIPT_MISSING
related_journeys: J4 discovery; every journey that is not in-process
evidence: services/gateway/CHARTER.md; contracts/service.json;
  contracts/ai-native-gateway-service.yaml
semantic_gaps: deny-by-default and narrowest-grant-wins are named in the charter and are
  in no contract. The in-process calling convention has no declared adapter shape, so
  route-request names a precondition it cannot check.
```

```yaml
station: FRONT / model-counter
intended_actor: a person bringing a model; an external system as operator
job_to_be_done: bring a model in as an operator and get a governed, metered invocation
what_the_actor_can_see: 2 capabilities — projection.package-context, read-context-package
what_the_actor_can_do: nothing on the map. Real work happens off-map through
  adapters/ollama/run.py
entry_conditions: a declared Model Binding
exit_or_continuation: an invocation record; fallback is never silent
reachable_operations: adapters/ollama/run.py {run, parity} — not a capability-map row
authority_projection: a binding grants nothing; authority arrives at the operation boundary
observable_results: an invocation record carrying usage {input_tokens, output_tokens,
  response_bytes, thinking_bytes, wall_clock_seconds} and cost {unit, monetary_charge,
  basis, wall_clock_seconds}
failure_experience: MODEL_UNAVAILABLE, MODEL_INCOMPATIBLE, DATA_BOUNDARY_REFUSED, plus
  three proposed adapter refusals. A cut-off answer records UNRESOLVED, never COMMITTED.
related_journeys: J3 bring my agent; J5 delegate work
evidence: adapters/ollama/observations/parity-live.json — a real two-model run
semantic_gaps: the only station in the node that measures anything, and it is not on the
  capability map. invoke_model has no kernel implementation.
```

```yaml
station: FRONT / job-window
intended_actor: an operator asking for work to be done
job_to_be_done: ask for work and collect the result
what_the_actor_can_do: exactly 1 capability — asset.request-derivative, effect class
  RESOURCE_CONSUMPTION
entry_conditions: a live grant for request:derivative
exit_or_continuation: request → claim (lease + fence) → report → observe
observable_results: services/asset/src/soveraeign_asset_service/runs.py — a runs table
  holding id, kind, asset_id, input_version_id, requester, status, worker, lease_fence,
  lease_expires, output_version_id, report_json, observation_id, created_at
failure_experience: StaleLease; observation of a run that never reported is refused
related_journeys: J5 delegate work
evidence: runs.py, 152 lines; contracts/kernel-parity.json asset correspondences
semantic_gaps: the runs table has created_at and no completion time, so the wall clock of
  a delegated run cannot be computed even in principle. No usage, no cost, no work-item
  link. This is the station where effort is spent and the least about it is recorded.
```

```yaml
station: FRONT / review-desk
intended_actor: HUMAN or MODEL reviewer
job_to_be_done: review a pinned version and land a decision
what_the_actor_can_do: 11 capabilities, all PROPOSED
entry_conditions_and_exit: open-session → close-session
authority_projection: ratify-decision restricted to HUMAN
observable_results: none — nothing implemented
failure_experience: declared in the manifest, unreachable
related_journeys: adjacent to J8, but a different record
evidence: services/proofing/CHARTER.md
semantic_gaps: the whole counter is boundary only.
```

```yaml
station: FRONT / drafting-window
intended_actor: an operator composing a governed artifact before proposing it
what_the_actor_can_do: zero capabilities (decisions/0038, Residuals)
evidence: .claude/epic/offices.json — issues #42, #50; chartered_in absent
semantic_gaps: an empty room, and it is where decision records and charters get written.
  That work currently happens entirely outside the governed surface.
```

```yaml
station: BACK / record, permits-office, inspectorate, pattern-room, ground, beyond-the-node
intended_actor: mostly SYSTEM; some HUMAN and MODEL reads
job_to_be_done: hold the front office up
what_the_actor_can_do: 43 capabilities. BACK_OFFICE_EXPOSED is a declared defect — back
  office machinery served straight to an operator fails the map check.
evidence: contracts/capability-offices.json; contracts/fixtures/capability-map.fixtures.json
semantic_gaps: permits-office holds 17 rows and 3 built; ground holds 1; beyond-the-node 0.
```

```yaml
station: MCP surface — NOT ON THE MAP
intended_actor: MODEL operator over local stdio
what_the_actor_can_do: 6 tools — authority_open_session, authority_grant, asset_ingest,
  asset_search, record_entries, observe_verify — across three tiers (read, observe, act)
authority_projection: the act tier requires a live session, and each endpoint declares
  whether the gate is the gateway's own capability check or the service's
observable_results: act appends an EVENT then a RECEIPT; observe appends an OBSERVATION
evidence: bindings/mcp/manifest.json, server.py, gateway.py, tests/
semantic_gaps: the capability map records MCP as DECLARED_NOT_ACTIVATED on all 102 rows,
  because scripts/sovkernel/capability_map.py derives ACTIVE only from `built`
  (IN_PROCESS) and from the cli_commands table (CLI). There is no mcp_tools input, so a
  live MCP tool is structurally unrepresentable. This is the one reachable model surface
  in the node and the map that exists to say what is reachable cannot see it.
```

## Station findings

`DERIVED`.

- **Twelve counters exist; two are empty**, and one of the empty ones is where governed
  artifacts are actually drafted.
- **The one station that measures effort (model-counter) is not on the map**, and the
  station where effort is most spent (job-window) records the least about it.
- **The MCP surface is real and invisible** to the projection whose job is reachability.
- The station vocabulary is already good and does not need renaming.

---

# 7 · Journey inventory

`DERIVED`. The thirteen probes from the brief, traced through the crossing sequence. The
probe list is used as probes, not adopted as canon.

Column order: NEED · STATION · DISCOVERY · CAPABILITY · OPERATION · AUTHORITY · EXECUTION ·
OBSERVATION · RECEIPT · CONTINUATION.

Marks: `REAL` realized · `PART` partially realized · `DECL` declared, not reachable ·
`IMPL` implicit · `MISS` missing · `OUT` out of phase.

| Journey | NEED | STN | DISC | CAP | OPN | AUTH | EXEC | OBS | RCPT | CONT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| J1 Continue work from another session | MISS | REAL | PART | REAL | REAL | REAL | REAL | PART | REAL | REAL |
| J2 Ingest an asset | MISS | REAL | PART | REAL | REAL | REAL | REAL | PART | REAL | REAL |
| J3 Bring my agent / model | MISS | PART | IMPL | DECL | PART | PART | REAL | PART | REAL | PART |
| J4 Discover what I can do | MISS | PART | PART | REAL | PART | REAL | PART | MISS | PART | MISS |
| J5 Delegate work | MISS | REAL | IMPL | REAL | REAL | REAL | REAL | PART | PART | PART |
| J6 Observe whether an operation succeeded | MISS | DECL | DECL | DECL | DECL | DECL | MISS | PART | MISS | MISS |
| J7 Counter or retract something | MISS | REAL | IMPL | REAL | REAL | REAL | REAL | MISS | REAL | REAL |
| J8 Resolve a human judgement request | MISS | DECL | DECL | DECL | DECL | DECL | MISS | MISS | MISS | MISS |
| J9 Inspect why something happened | MISS | PART | MISS | REAL | REAL | REAL | REAL | PART | REAL | PART |
| J10 Find something previously recorded | MISS | PART | MISS | DECL | PART | DECL | PART | MISS | MISS | MISS |
| J11 Run a workflow | MISS | REAL | IMPL | MISS | MISS | IMPL | REAL | PART | MISS | IMPL |
| J12 Establish my local node | MISS | MISS | MISS | MISS | MISS | MISS | PART | PART | MISS | MISS |
| J13 Interact with another authorized node | OUT | OUT | OUT | OUT | OUT | OUT | OUT | OUT | OUT | OUT |

## The column that matters

`OBSERVED`. **NEED is `MISSING` in twelve of thirteen rows and `OUT_OF_PHASE` in the
thirteenth.** Not one journey in this repository begins from a recorded user need. Every
row above starts at a station because there is nowhere earlier to start.

## Notes on individual rows

`DERIVED`.

- **J1 continuity** is the only journey realized end to end, and it exists because
  `decisions/0036` chose it over the charter's declared first slice. OBSERVATION is
  `PART`: `scripts/witness_console.py` is the independent look, and the Observation
  Service that would make witnessing a governed operation is chartered and unbuilt.
- **J4 discovery** is where the AI-native argument lives, and it has the worst shape.
  `console.discover-operations` is built; the capability map answers the question as data;
  the gateway that would serve it is unbuilt; the MCP surface that could reach it is
  invisible to the map. DISCOVERY scores `PART` only because a model can read the
  checked-in JSON directly.
- **J7 retraction** has no OBSERVATION crossing at all. `asset.retract-record` commits a
  counter-record and emits a `COUNTERED` receipt, and nothing independently observes that
  effective state actually changed.
- **J8 judgement** is `DECLARED_NOT_REACHABLE` at every crossing. It is the journey the
  Console charter named as its first slice, the journey `OPEN-SEAMS.md` S12 says the owner
  actually needs, and the one that got deferred. All ten crossings are declared with real
  refusal codes and none of them runs.
- **J11 run a workflow** has no OPERATION: `.claude/workflows/` is host plumbing holding no
  standing, on no capability-map row. A federation run leaves its changes uncommitted and
  emits no receipt — `CLAUDE.md` says `git status` and `git diff` are the independent path
  to what it did.
- **J12 establish a node** is `MISSING` almost throughout, which is the practical shape of
  C-NODE having no service (§5).

## Missing product interfaces this exposes

`DERIVED`. These fall out of the table rather than being proposed:

1. **A judgement inbox** — J8: every crossing declared, none reachable.
2. **A "what can I do" answer that is served rather than read** — J4: the data exists as
   a file and nothing serves it.
3. **An observation surface** — J6 and the OBSERVATION column generally. `AI-NATIVE.md`
   check 3 reads `UNATTESTABLE` on every assessed surface for exactly this reason.
4. **A first-run / node-establishment path** — J12.
5. **A retrieval surface with one owner** — J10, blocked behind `OPEN-SEAMS.md` S14.

None of these is a CRUD endpoint invented to fill a table; each is a crossing a stated
promise needs and does not have.

---

# 8 · Canonical-operation inventory

`OBSERVED`. **The inventory already exists and is machine-readable.** It is
`contracts/fixtures/capability-map.reference.json` — 102 rows, rebuilt by
`scripts/sovkernel/capability_map.py` from the eight service manifests plus
`contracts/capability-offices.json`, carrying `input_state_digest` and refusing to answer
when stale.

Restating 102 rows here would create a second, immediately stale copy of a projection that
already refuses to lie about its own freshness. The map is the inventory. What follows is
what the map does *not* carry, and the defects a join against it exposes.

## Shape of the existing inventory

| Field the map carries | Field the brief asked for | Present |
| --- | --- | --- |
| `capability_id` (`<service>.<operation>`) | `operation_id` | yes |
| `service_id` | `owning_service` | yes |
| `office`, `counter` | `station_or_binding` | yes, as office/counter |
| `required_authority` | `authority_requirement` | yes |
| `effect_class` | `effect_class` | yes |
| `actor_kinds` | — | yes |
| `endpoints[]` transport + activation + address | `interfaces`, `current_reachability` | yes |
| `service_standing` | `standing` | yes |
| manifest `logical_endpoint` | `interfaces` | yes (`sov://<svc>/<op>`) |
| manifest `preconditions`, `commit`, `refusals` | inputs/outputs, partial | yes |
| manifest `requirement` | `prd_requirement` | **99 / 102** |
| manifest `kernel_transition` | `spec_transition_or_predicate` | **23 / 102** |
| — | `semantic_intent` | **no field** |
| — | `user_need` | **no field** |
| — | `product_chart` | **no field** (office is not a chart) |
| — | `journeys` | **no field** |
| — | `receipt`, `observation` | **no field** (declared per-service, not per-row) |
| — | `positive_fixture`, `defeating_fixture` | **no field** |
| — | `implementation_locations` | **no field** |

## Exemplars

Three rows, filled as far as the repository actually allows. Absent fields are marked, not
guessed.

```yaml
operation_id: asset.ingest-asset
semantic_intent: [DERIVED] put bytes under governed custody with an identity and a version
user_need: MISSING
product_chart: C-ASSET  [DERIVED — no chart field exists]
station_or_binding: FRONT / operator-desk
journeys: MISSING  [J2 in this report only]
owning_service: asset
authority_requirement: ingest:asset
inputs: payload_bytes_readable, declared_label, declared_locator, live_grant
outputs: COMMITTED  [manifest `commit`; no output schema]
effect_class: RECORD_LOCAL
receipt: yes — store.receipt writes rcpt_* with event "asset.ingest"
observation: none for this operation
prd_requirement: PROD-I-2
spec_transition_or_predicate: capture_source
interfaces: sov://asset/ingest-asset; IN_PROCESS ACTIVE; CLI ACTIVE
  (python -m soveraeign_asset_service.cli ingest); MCP DECLARED_NOT_ACTIVATED
  (but bindings/mcp/manifest.json exposes it as asset_ingest — defect D1);
  HTTP REFUSED_UNCONFIGURED
implementation_locations: services/asset/src/soveraeign_asset_service/core.py:122
positive_fixture: services/asset/tests/test_walking_skeleton.py
defeating_fixture: DIGEST_MISMATCH, GRANT_NOT_COVERED, MISSING_PRECONDITION, PAYLOAD_ABSENT
  declared in the manifest; not mapped to named fixture files
current_reachability: reachable in-process and by CLI
standing: BUILT (self-tested, not witnessed)
```

```yaml
operation_id: console.resolve-judgement
semantic_intent: the owner answers a queued judgement request and the answer becomes a
  record that can carry RATIFIED
user_need: MISSING  [OPEN-SEAMS.md S12 records the owner stating this need in conversation
  on 2026-08-23; it is not an addressed artifact]
product_chart: C-OPERATOR
station_or_binding: FRONT / operator-desk
journeys: J8
owning_service: console
authority_requirement: ratify:judgement — actor_kinds [HUMAN]
effect_class: RECORD_LOCAL
prd_requirement: PROD-I-6
spec_transition_or_predicate: ratify  [charter states this explicitly]
interfaces: sov://console/resolve-judgement; every transport DECLARED_NOT_ACTIVATED
implementation_locations: none
current_reachability: DECLARED_NOT_REACHABLE
standing: PROPOSED
```

```yaml
operation_id: gateway.check-authority
semantic_intent: the door confirms the actor holds a live grant covering what the
  operation costs
user_need: MISSING
product_chart: C-DOOR / C-PERMITS  [crosses two]
station_or_binding: BACK / permits-office  — note: a gateway operation assigned to the
  permits counter, which is the office table recording a crossing it has no field for
journeys: prerequisite of J4 and every non-in-process journey
owning_service: gateway
authority_requirement: read:authority — actor_kinds [SYSTEM]
effect_class: RECORD_LOCAL
prd_requirement: PROD-I-5
spec_transition_or_predicate: MISSING
interfaces: sov://gateway/check-authority; all transports DECLARED_NOT_ACTIVATED
current_reachability: DECLARED_NOT_REACHABLE
standing: PROPOSED
open: deny-by-default and narrowest-grant-wins are in the charter and in no contract
```

## Defects a join exposes

`OBSERVED` unless marked.

**D1 · A live interface the map cannot represent.** `bindings/mcp/manifest.json` exposes
six tools over stdio, two of which name the manifest operation they realize
(`asset_ingest` → `asset.ingest-asset`, `record_entries` → `record.read-entry`). The
capability map records `MCP: DECLARED_NOT_ACTIVATED` for all 102 rows.
`scripts/sovkernel/capability_map.py` sets `ACTIVE` only from `built` (IN_PROCESS) and
from the `cli_commands` table (CLI); there is no `mcp_tools` input, so a live MCP tool is
structurally unrepresentable. The one reachable model surface in the node is invisible to
the projection that exists to describe reachability.

**D2 · Reachable endpoints with no declared operation.** Four of six MCP tools carry
`realizes: null`, each with a stated reason:

| Tool | Reason recorded in the manifest |
| --- | --- |
| `authority_open_session` | "The asset service implements sessions; no service manifest declares them as an operation." |
| `authority_grant` | "The asset service implements grants; no service manifest declares them as an operation." |
| `asset_search` | "Reads the search projection. The asset manifest declares read-asset, which is not the same." |
| `observe_verify` | "A repository check, not a service operation. No manifest declares it and none should." |

This is the honest version of the defect and it is worth preserving: the binding layer
already declares where the operation is missing rather than inventing one.

**D3 · Emitted receipt events that do not match capability ids.** The Console emits
receipts whose `operation_type` is exactly its capability id — `console.post`,
`console.open-session`, `console.publish-thread`, and six more. The Asset Service does not:

| Emitted event | Capability id on the map | Match |
| --- | --- | --- |
| `console.post` … (9 events) | `console.post` … | **yes, all nine** |
| `asset.ingest` | `asset.ingest-asset` | no |
| `proposal.record` | `asset.propose-description` | no |
| `proposal.ratify` | `asset.ratify-proposal` | no |
| `record.retract` | `asset.retract-record` | no |
| `federation.cross` | **no capability exists** | no |

`DERIVED`: the runtime-to-capability join already works for one service by convention and
is broken for the other, and nothing checks it. This is the cheapest real edge in the
whole report to close — it is a naming reconciliation plus one check, not a design.

**D4 · An emitted event with no declared operation.** `federation.cross` is emitted by
`services/asset/src/soveraeign_asset_service/core.py` as a `REFUSED` receipt and appears
in no service manifest and on no map row.

**D5 · Requirement fan-in defeats the edge.** 99 of 102 operations cite one of nine
requirements. `PROD-I-2` carries 32, `PROD-I-6` carries 20, `PROD-I-4` carries 11,
`PROD-I-5` carries 10. Three operations cite none: `asset.request-derivative`,
`console.set-setting`, `record.drop-projections`.

**D6 · Kernel-transition coverage is thin.** 23 of 102 operations name a
`kernel_transition`. Seventy-nine operations declare preconditions, a commit and refusals
without stating which of the fifteen `SPEC.md` transitions they realize.

**D7 · The two invalid manifests are now valid — residual closed.** `decisions/0038`
Residuals recorded that `services/console/contracts/service.json` and
`services/record/contracts/service.json` did not validate against
`contracts/service-manifest.schema.json`, and that nothing in `scripts/verify.py` checked
them. Re-verified in this pass: `python scripts/verify.py` reports
*"PASS: 8 service manifests, 102 declared operations, no defect"*. The check landed and
the residual is closed. Recorded here because `decisions/0038` still reads as open.

**D8 · Declared operations with no reachable interface: 68 of 102.** All rows of
`gateway`, `observation`, `projection`, `proofing` and `registry`, plus ten `console` rows.
`decisions/0038` treats this as the accurate shape of what is not built, not as a defect —
recorded here because the brief asked for the count.

## Aliases normalized without claiming equivalence

`DERIVED`. Three alias families, none of which should be silently merged:

1. `asset.ingest` (receipt event) ~ `asset.ingest-asset` (capability) ~
   `sov://asset/ingest-asset` (logical endpoint) ~ `asset_ingest` (MCP tool). Four names,
   one operation; only the MCP manifest asserts the identity, and only for that one hop.
2. `ROADMAP.md` name crosswalk — the repository's own answer to this problem, and the only
   place identity across vocabularies is asserted. Four rows. `scripts/sov_next.py`
   fails the check when a row stops resolving. This is the existing precedent for the
   whole spine, at four-row scale.
3. `capability` in three senses: a capability-map row, `AuthorityGrant.capability`,
   `ModelBinding.capabilities`. Nothing disambiguates them.

Nothing above is repaired here.

---

# 9 · Existing effort and resource telemetry inventory

`OBSERVED`. Every concept in the repository touching budget, usage, cost, time, identity of
a run, or attribution of spend. Searched: `budget`, `usage`, `cost`, `token`, `wallclock`,
`elapsed`, `meter`, `limits`, `consumed`, `started_at`, `completed_at`, `run_id`,
`session_id`, `duration`.

```yaml
measure: usage_meter (declared)
already_defined_where: SPEC.md ModelBinding; contracts/model-binding.schema.json (required,
  typed only as {"type": "object"} — no inner shape)
recorded_at_runtime: yes, by adapters/ollama/invoke.py only
unit: tokens — input_tokens, output_tokens, wall_clock_seconds (per binding declaration)
attributed_to: binding_id, actor_id, operation_id (a free-form label such as
  "operation_byom_parity_live", not a capability id)
stable_identity_used: invocation_id (urn:soveraeign:invocation:<hex>)
authoritative_or_projection: neither — a file under adapters/ollama/observations/
receipt_visibility: not in contracts/receipt.schema.json; the invocation record is its own
  shape
aggregate_possible: no — one file, one run, no store
missing_parent_links: no work item, no capability id, no requirement, no session, no domain
```

```yaml
measure: cost_meter (declared)
already_defined_where: SPEC.md ModelBinding; contracts/model-binding.schema.json
recorded_at_runtime: yes, ollama adapter only
unit: USD, monetary_rate 0, basis OWNER_OWNED_HARDWARE, also_metered [wall_clock_seconds]
attributed_to: same as usage_meter
stable_identity_used: invocation_id
authoritative_or_projection: neither
receipt_visibility: none
aggregate_possible: no
missing_parent_links: same as above, plus: whether wall clock on owner hardware is a cost
  at all is an open question queued for Bdo (adapters/ollama/README.md, Q3)
```

```yaml
measure: cost_record (on a Proposal)
already_defined_where: SPEC.md Proposal object; PRD.md PROD-I-1 requires it; the
  submit_proposal transition lists cost as a precondition (contracts/kernel-transitions.json)
recorded_at_runtime: NO
unit: undefined — the field has no declared shape anywhere
attributed_to: would be the proposal's actor
stable_identity_used: proposal_id
authoritative_or_projection: would be authoritative
receipt_visibility: none
aggregate_possible: no
missing_parent_links: everything. services/asset/conformance/BASELINE.md:
  "PROD-I-1 · Propose | FAIL | proposal lacks content address, source addresses, and cost
  record". The one requirement demanding recorded cost fails in the one participant.
```

```yaml
measure: AuthorityGrant.budget
already_defined_where: SPEC.md AuthorityGrant; checked at every consequential transition
  ("type, capability, scope, budget, time, and revocation")
recorded_at_runtime: partially — conformance/run.py evaluates a boolean budget_available;
  services/console/.../authority.py issues grants as journal records
unit: NONE. The field is declared and has no unit, no denomination, and no decrement path.
attributed_to: grant_id, actor_id
stable_identity_used: grant_id
authoritative_or_projection: authoritative
receipt_visibility: receipts carry authority_grant_ids, never a remaining balance
aggregate_possible: no
missing_parent_links: nothing consumes a budget. "over-budget grants refuse visibly"
  (SPEC.md PROD-I-5) is checked in the oracle as a boolean the test supplies, never
  computed from spend.
```

```yaml
measure: domain owner budget
already_defined_where: contracts/domain-owners.json; contracts/domain-owners.schema.json;
  services/registry/CHARTER.md
recorded_at_runtime: NO
unit: {max_usd_per_run: 5, runs_per_period: 5, period: WEEK} — three owners, identical
attributed_to: a domain and an owner actor_id/seat_id
stable_identity_used: domain name; owner actor_id
authoritative_or_projection: authored policy input, PROPOSED
receipt_visibility: none
aggregate_possible: no
missing_parent_links: scripts/sov_owners.py validates the declaration (rejects a budget of
  zero, rejects an owner witnessing itself) and computes no spend. This is the clearest
  BUDGET-without-USAGE pair in the repository.
```

```yaml
measure: OperationPlan.limits
already_defined_where: SPEC.md OperationPlan (required); contracts/operation-plan.schema.json
recorded_at_runtime: no plan object is constructed anywhere in the services
unit: none — the schema says {"type": "object"} and nothing more
attributed_to: operation_id
stable_identity_used: operation_id
authoritative_or_projection: would be authoritative
receipt_visibility: none
aggregate_possible: no
missing_parent_links: this is the field the kernel reserved for intent-to-spend, and it
  has no shape at all. begin_run's precondition "capability, budget, input, and effect
  gates pass" is checked against a field with no schema.
```

```yaml
measure: verification wall clock (per check and total)
already_defined_where: scripts/verify.py — BUDGET_GRADES (("PLATINUM",3.0),("GOLD",6.0),
  ("SILVER",15.0)); decisions/0042
recorded_at_runtime: YES — one Observation per check, per contracts/observation.schema.json
unit: seconds (elapsed_seconds, rounded to 3dp), plus exit_code and PASS/FAIL
attributed_to: observer_id (script path + digest), run_id, subject (a prose string such as
  "repository hygiene")
stable_identity_used: run_id (run_<hex>), observation_id (deterministic per run+subject)
authoritative_or_projection: an Observation — evidence, settling nothing
receipt_visibility: printed, and written to .local/observations/latest.json
aggregate_possible: within one run only; latest.json is overwritten each run
missing_parent_links: `.local/` is gitignored. The only durable-looking wall-clock record
  in the repository does not travel with the repository, is overwritten every run, and
  attributes to a prose subject rather than to an operation, a ticket or a requirement.
```

```yaml
measure: scheduled-run ledger
already_defined_where: scripts/sovschedule/ledger.py — append-only NDJSON of kernel event
  envelopes plus run_id and schedule name; CLAUDE.md points at .local/schedules/ledger.ndjson
recorded_at_runtime: no run has happened — every shipped schedule is disabled and the
  .local/schedules directory does not exist in this working tree
unit: event envelopes; no resource field (the envelope schema has none)
attributed_to: schedule name, run_id
stable_identity_used: run_id
authoritative_or_projection: explicitly non-authoritative — "the ledger is a projection"
receipt_visibility: the harness holds no grants and issues no receipt
aggregate_possible: would be, if it had any resource field
missing_parent_links: no capability, no ticket, no cost, no duration
```

```yaml
measure: asset Run record
already_defined_where: services/asset/src/soveraeign_asset_service/runs.py
recorded_at_runtime: YES — the only executable run lifecycle in the node
unit: none
attributed_to: requester, worker, asset_id, input_version_id
stable_identity_used: run id, lease_fence, observation_id
authoritative_or_projection: authoritative
receipt_visibility: report_json holds the worker's own claim; observation is separate
aggregate_possible: rows are countable; nothing about them is summable
missing_parent_links: the table has created_at and NO completion timestamp, so the wall
  clock of a delegated run cannot be computed even in principle. SPEC.md's Run object
  declares started_at and completed_at; the implementation carries neither pair.
```

```yaml
measure: token_budget (context package)
already_defined_where: services/projection/PARITY.md; services/projection/conformance/
  008-context-package-budgeted.yaml
recorded_at_runtime: NO — the Projection Service is chartered, not implemented
unit: tokens
attributed_to: a context package and its query
stable_identity_used: content_digest
authoritative_or_projection: projection
receipt_visibility: omissions list every dropped hit with reason BUDGET
aggregate_possible: no
missing_parent_links: a fifth, unrelated meaning of the word budget
```

```yaml
measure: module line budget
already_defined_where: ENGINEERING.md; AGENTS.md ("keep modules below 300 lines");
  scripts/lint.py; decisions/0044 Ruling 4
recorded_at_runtime: yes, at lint time
unit: source lines
attributed_to: a file path
authoritative_or_projection: a check
aggregate_possible: yes
missing_parent_links: not a resource measure at all — included because it is the sixth
  thing in this repository called a budget
```

```yaml
measure: git history as effort evidence
already_defined_where: the repository itself — 122 commits
recorded_at_runtime: yes, by git
unit: commits, files changed, lines
attributed_to: author, Co-Authored-By trailer, commit scope such as feat(console)
stable_identity_used: commit sha
authoritative_or_projection: authoritative for code, silent about effort
receipt_visibility: none
aggregate_possible: yes, but only by file path
missing_parent_links: 6 of 122 commit subjects carry a (#NN) pull-request reference;
  0 carry a "Closes #" or "Refs #" trailer; 10 mention a PROD-I requirement anywhere in
  the message. No commit names a capability, an operation, or a ticket in a parseable
  field. The link from a commit to the work it served is prose or nothing.
```

```yaml
measure: ticket evidence and receipt pointers
already_defined_where: contracts/issue-metadata.schema.json — evidence_pointer,
  walker_receipt, last_observed_at (all required)
recorded_at_runtime: partially
unit: an address (a path, a URL, or a commit sha)
attributed_to: an issue number
stable_identity_used: issue number; bit_id / stub_id / story_id / engagement_id / unblock_id
authoritative_or_projection: the issue body is the coordination authority; tree.json is a
  projection of it
receipt_visibility: walker_receipt is the field for it
aggregate_possible: no
missing_parent_links: measured on the checked-in projection — evidence_pointer is real on
  18 of 51 issues and PENDING on 33; walker_receipt is PENDING on 51 of 51; last_observed_at
  is null on every issue that carries it. The evidence field works; the receipt field has
  never once been filled.
```

## Can the repository distinguish the seven quantities?

`DERIVED`. The brief asked this directly. Answer per quantity:

| Quantity | Distinguishable today? | Where it lives, or why not |
| --- | --- | --- |
| **BUDGET** — what we intended to spend | **Partly, and overloaded six ways** | `contracts/domain-owners.json` (USD per run, runs per period) is the only one that means money. `AuthorityGrant.budget` has no unit. `OperationPlan.limits` has no schema. `verify.py` grades wall time. `token_budget` bounds a context package. `lint.py` bounds module lines. Six meanings, one word (§13, C3). |
| **USAGE** — what was consumed | **Almost no** | One place: `adapters/ollama/invoke.py` writes `usage` with real token counts and wall clock. Nothing else in the node records consumption of anything. |
| **COST** — valuation of what was consumed | **No** | One place, and it reports `monetary_charge: 0` with a note that a local run is *"cheap rather than free"*. Whether that zero is correct is an open question queued for Bdo. |
| **WALLCLOCK** — elapsed real time | **Partly** | `verify.py` per check (gitignored, overwritten); the ollama invocation record. The asset `runs` table has no completion time, so the wall clock of a delegated run is not recoverable. |
| **EFFORT** — participant activity attributable to an objective | **No** | Nothing anywhere attaches any measure to an objective. The only attribution keys that exist below a run are `run_id`, `observer_id`, `invocation_id`, and a prose `subject`. |
| **RESULT** — what changed | **Yes** | This is the repository's strongest layer: receipts, `emitted_record_addresses`, the digest chain, counter-records, `git diff`. |
| **VALUE** — whether the result advanced an accepted intention | **No, structurally** | There is no accepted product intention below the nine PRD requirements to advance (Break 1). The nearest proxy is ticket standing on the `OPEN → BUILT → WITNESSED → RATIFIED` lifecycle, and nothing in the repository is `WITNESSED` or `RATIFIED` yet. |

These are not collapsed above and should not be collapsed later: the repository already
keeps `RESULT` cleanly, and the temptation will be to let a receipt count as effort
evidence because it is the record that exists.

## The one-line version

`DERIVED`. **Budget is declared in six vocabularies and spent in none. Usage is measured in
one file. Effort is attributable to nothing.** The single richest telemetry record in the
repository — the ollama invocation — knows its binding, its provider, its model version,
its host, its input digest, its data boundary, its tokens, its wall clock and its cost, and
does not know which ticket, requirement, capability or promise it was serving.

---

# 10 · Five end-to-end lineage traces

`OBSERVED` for every filled edge; `MISSING` where no artifact carries the link. No edge is
filled by intuition.

Chain, top to bottom: product definition · promise · user/need · journey · chart · capability ·
canonical operation · PRD requirement · SPEC predicate · service · interface · work item ·
PR · commit · agent/session/run · measured resources · observed result · evidence/receipt.

## Trace 1 · A Gateway operation — `gateway.accept-request`

| Layer | Value | State |
| --- | --- | --- |
| Product definition | `SYSTEM.md` Scope | present, no id |
| Promise | P10 discovery / P1 same world | `STRONGLY_DERIVED`, no artifact |
| User / need | — | **MISSING** |
| Journey | — | **MISSING** (J4 exists only in this report) |
| Chart | C-DOOR | **MISSING as a field**; office `FRONT/door` is the nearest |
| Capability | `gateway.accept-request` | present |
| Operation | `sov://gateway/accept-request`, subject `request`, crud `CREATE` | present |
| PRD requirement | `PROD-I-3` | present |
| SPEC predicate | — | **MISSING** (no `kernel_transition` on this operation) |
| Service | `gateway`, standing `PROPOSED` | present |
| Interface | four transports, all `DECLARED_NOT_ACTIVATED` | present, unreachable |
| Work item | `#16` Gateway Service — governed ingress and egress | present, **not linked from the operation** |
| PR | — | **MISSING** |
| Commit | `35bc49c` — "make every service declare its operations, and charter the door", 9 files | present, **names no ticket and no capability** |
| Agent / session / run | — | **MISSING** |
| Measured resources | — | **MISSING** |
| Observed result | `contracts/ai-native-gateway-service.yaml` — reachability `PARTIAL`, everything else `NONE`, `earn_it: OPEN` | present |
| Evidence / receipt | `#16` `evidence_pointer: PENDING`, `walker_receipt: PENDING` | **empty** |

**Coverage: 9 of 18 edges.** The chain is intact from capability down to interface and
breaks at both ends. `#16` requires `#6, #7, #11, #12, #13, #14` — six dependencies, none
built — and the ticket does not know that `35bc49c` chartered it.

## Trace 2 · A service implementation — the Record Service

| Layer | Value | State |
| --- | --- | --- |
| Promise | P4 receipts / P5 retraction / P7 provenance | `EXPLICIT`, three of them, no id |
| User / need | — | **MISSING** |
| Journey | — | **MISSING** |
| Chart | C-RECORD | **MISSING as a field** |
| Capability | 8 rows, `record.*`, all `BUILT` | present |
| Operation | e.g. `sov://record/append-entry`, subject `journal-entry`, crud `CREATE` | present |
| PRD requirement | `PROD-I-2` on 7 of 8; `record.drop-projections` cites none | 7 / 8 |
| SPEC predicate | one operation of eight names a `kernel_transition` | **1 / 8** |
| Service | `record`, `BUILT_SELF_TESTED_NOT_WITNESSED` | present |
| Interface | `IN_PROCESS: ACTIVE` on all 8; `record_entries` also live as an MCP tool | present, and the MCP half is invisible to the map (D1) |
| Work item | `#65` System of Record, `CLOSED`, `evidence_pointer: services/record/` | present, and **the best-linked ticket in the tree** |
| PR | `#66` | present, in the merge subject only |
| Commit | `5c919e1` — 6 files, 502 insertions | present |
| Agent / session / run | — | **MISSING** |
| Measured resources | — | **MISSING** |
| Observed result | 144 lines of tests in `test_journal.py`; digest chain verified by `reconstruct` | present, self-tested |
| Evidence / receipt | `evidence_pointer: services/record/`; `walker_receipt: PENDING` | half |

**Coverage: 11 of 18.** The strongest trace in the repository, and it still cannot say who
needed it or what building it cost. Note the ticket is `CLOSED` at standing
`BUILT_SELF_TESTED_NOT_WITNESSED` — closed on the coordination surface, unwitnessed on the
evidence surface.

## Trace 3 · A harness change — `8383a05` "stop instructing every agent to escalate"

| Layer | Value | State |
| --- | --- | --- |
| Promise | none | the harness holds no standing and serves no promise by design |
| User / need | a model operator that escalated instead of deciding | **MISSING as an artifact**; the need is real and recorded only in `AGENTS.md` "Self-direction is not delegation" |
| Journey | — | **MISSING** |
| Chart | none | `.claude/` is host plumbing, on no chart |
| Capability | — | **MISSING** — `.claude/` appears on no capability-map row |
| Operation | — | **MISSING** |
| PRD requirement | — | **MISSING** |
| SPEC predicate | — | **MISSING** |
| Service | — | not a service |
| Interface | agent and skill markdown files | present |
| Work item | — | **MISSING** |
| PR | — | **MISSING** |
| Commit | `8383a05`, 9+ files across agents, skills and NARRATIVE | present |
| Agent / session / run | — | **MISSING** |
| Measured resources | — | **MISSING** |
| Observed result | — | **MISSING** — nothing observed that agents stopped escalating |
| Evidence / receipt | `decisions/0033` Ruling 1 governs the behaviour | policy present, observation absent |

**Coverage: 4 of 18.** The worst trace, and structurally so: `AGENTS.md` places the harness
outside standing on purpose. That is a defensible boundary and it has a cost — a change to
how every model operator behaves in this repository is attributable to nothing, and the
memory note recording that a full federation run cost roughly 1.8M subagent tokens exists
only in a private memory file, not in the repository.

## Trace 4 · A conformance effort — `CONF-I5-GRANT`

| Layer | Value | State |
| --- | --- | --- |
| Promise | P1 same world (typed authority half) | `EXPLICIT` |
| User / need | — | **MISSING** |
| Journey | `RUN-I5-AUTHORITY` in `conformance/scenarios.json` | **present** — the only trace with a journey-shaped artifact |
| Chart | C-INSPECT | **MISSING as a field** |
| Capability | — | **MISSING**; the oracle is not a service and has no capability row |
| Operation | — | **MISSING** |
| PRD requirement | `PROD-I-5` | present, on the scenario |
| SPEC predicate | "VERIFICATION authority cannot ratify a JUDGEMENT claim"; over-budget grants refuse visibly | present, in `SPEC.md` Requirement predicates |
| Service | `conformance/` — deliberately not a participant | n/a |
| Interface | `python conformance/run.py`; run by `scripts/verify.py` | present |
| Work item | `#26` Conformance harness, `evidence_pointer: conformance/` | present, **not linked to the control id** |
| PR | — | **MISSING** |
| Commit | `1696b9c` — one file, 29 lines | present, and the subject **does** name the control `CONF-I5-GRANT` |
| Agent / session / run | — | **MISSING** |
| Measured resources | `elapsed_seconds` for the oracle check, in `.local/observations/latest.json` | **present and gitignored** |
| Observed result | 20 controlled cases; every defeating fixture fails as declared | present |
| Evidence / receipt | `walker_receipt: PENDING` | empty |

**Coverage: 11 of 18**, and the only trace where the journey edge is filled — because
`conformance/scenarios.json` is the one artifact in the repository shaped like a journey.
It is requirement-shaped rather than user-shaped, which is why NEED is still missing above
it. `RUN-I5-AUTHORITY` carries `given` / `desired` / `gap` / `work_item` / `watched_delta`,
and its `work_item` is a prose string ("submit one model proposal"), not a ticket
reference.

## Trace 5 · An owner interaction — thread `thread_75092afc70cc414b`

`OBSERVED` from this session's own console-continuity hook output at start, and from
`decisions/0036`.

| Layer | Value | State |
| --- | --- | --- |
| Promise | P6 judgement protected / P12 continuity | one `EXPLICIT`, one `STRONGLY_DERIVED` |
| User / need | Bdo needs to answer "is the continuity path the console's first slice?" | **MISSING as an artifact**; the need exists as a thread title |
| Journey | — | **MISSING** (J8 declared and unreachable; this exchange happened as a post, not as a judgement request) |
| Chart | C-OPERATOR | **MISSING as a field** |
| Capability | `console.post`, `console.open-thread` | present, `BUILT` |
| Operation | `sov://console/post` | present |
| PRD requirement | `PROD-I-3` (crossing) and `PROD-I-6` (judgement) | present on the manifest rows |
| SPEC predicate | `cross` for post; `ratify` for the resolution that did not happen | half |
| Service | `console` | present |
| Interface | `cli.py`; opened by `.claude/hooks/console_session.py` | present |
| Work item | — | **MISSING**. The thread is pinned to `STATUS.yaml#L18`, an address, not a ticket |
| PR | — | **MISSING** |
| Commit | `955bf55` built the path; `decisions/0036` rules the order | present |
| Agent / session / run | `session_79fba9735cc343f4`, actors `operator:claude` (MODEL) and `operator:bdo` (HUMAN) | **present — the only trace with a real session id and both actor kinds** |
| Measured resources | — | **MISSING** |
| Observed result | two posts, addressed `posts/2e45f187…` and `posts/3182725c…`, both in the journal with digests | present |
| Evidence / receipt | `EVENT` then terminal `RECEIPT` per post, per `append.py` | **present, and the strongest receipt evidence of the five** |

**Coverage: 12 of 18** — the highest of the five, and the only one carrying a session
identity and an attributed human actor.

And the thing it shows: **the owner's question is open as a thread post, not as a judgement
request.** `console.request-judgement` and `console.resolve-judgement` are `PROPOSED` and
unreachable, so the exchange that most needed the judgement record used the post record
instead. Nothing marks that thread as holding an owner-held decision, nothing queues it,
and `STATUS.yaml` line 18 says in a comment what a `QUEUED` judgement request would say as
a field: *"Bdo has not ruled on whether this slice stands as the console's first."*

## What the five traces establish

`DERIVED`.

| Edge | Filled in how many of five |
| --- | --- |
| Capability → operation → service → interface | 4 / 5 (absent only for the harness) |
| Operation → PRD requirement | 4 / 5 |
| Operation → SPEC predicate | 2 / 5 |
| **Work item → operation** | **0 / 5** |
| **Commit → work item** | **0 / 5** |
| **Run → measured resources** | **0 / 5** |
| **Anything → user need** | **0 / 5** |
| **Anything → journey** | **1 / 5** (and it is requirement-shaped) |
| Result → evidence / receipt | 3 / 5 |

**Semantic lineage stops at the capability, in both directions.** Downward it is nearly
complete and unusually good. Upward there is nothing above the requirement. Sideways there
is no join from any work item, commit, session or run to the capability the work served.

---

# 11 · Missing-edge matrix

`DERIVED`. Every edge in the chain the brief named, with what carries it today and what is
absent. `PARTIAL` means the edge exists for some rows and not others, with the count given.

| # | Edge | Carrier today | State |
| --- | --- | --- | --- |
| E1 | product identity → promise | `README.md` prose | **MISSING as artifacts** — no promise has an address |
| E2 | promise → user / actor | — | **MISSING** — actors are inventoried four ways, promises zero ways, and nothing joins them |
| E3 | user → need | — | **MISSING** — zero occurrences repository-wide |
| E4 | need → journey | — | **MISSING** |
| E5 | journey → station | — | **MISSING** — stations exist as counters; journeys do not exist |
| E6 | journey → capability | — | **MISSING** |
| E7 | capability → operation | `capability_id` = `<service>.<operation>`; manifest is the source | **REALIZED**, 102 / 102, rebuilt and digest-checked |
| E8 | capability → station | `contracts/capability-offices.json` office + counter | **REALIZED**, 102 / 102 |
| E9 | capability → required authority | same table | **REALIZED**, 102 / 102 |
| E10 | capability → effect class | same table | **REALIZED**, 102 / 102 |
| E11 | capability → admitted actor kinds | same table | **REALIZED**, 102 / 102 |
| E12 | operation → PRD requirement | manifest `requirement` | **PARTIAL** 99 / 102, and coarse — 9 parents for 102 children |
| E13 | operation → SPEC transition | manifest `kernel_transition` | **PARTIAL** 23 / 102 |
| E14 | operation → service | manifest ownership | **REALIZED** 102 / 102 |
| E15 | operation → logical endpoint | `sov://<service>/<operation>` | **REALIZED** 102 / 102 |
| E16 | operation → transport activation | capability map `endpoints[]` | **PARTIAL** — correct for IN_PROCESS and CLI, structurally wrong for MCP (D1) |
| E17 | operation → positive / defeating fixture | manifest `refusals` names codes | **MISSING** — no field points at a fixture file |
| E18 | operation → implementation location | — | **MISSING** — no field; recoverable only by grep |
| E19 | **work item → operation** | — | **MISSING** — 47 ticket properties, none names a capability, operation, service or endpoint |
| E20 | work item → requirement | — | **MISSING** on tickets; present on `contracts/domain-owners.json` (3 domains → PROD-I-*) |
| E21 | work item → chart or office | `.claude/epic/offices.json` | **PARTIAL** — 51 issues placed in 12 offices, and never checked against the 102 operations placed in the same 12 offices (`decisions/0038`) |
| E22 | work item → evidence | ticket `evidence_pointer` | **PARTIAL** 18 / 51 real, 33 `PENDING` |
| E23 | work item → receipt | ticket `walker_receipt` | **MISSING in practice** — `PENDING` on 51 / 51 |
| E24 | **commit → work item** | commit message prose | **MISSING** — 6 / 122 carry a `(#NN)` PR reference, 0 carry a `Closes`/`Refs` trailer |
| E25 | PR → work item | `soveraeign-ticket-transition/v1` block in the PR body, `ticket` field | **REALIZED where used** — the mechanism exists and is checked by `scripts/sov_ticket.py transition`; only a standing-advancing PR carries it |
| E26 | PR → evidence | transition request `evidence` object | **REALIZED where used** |
| E27 | commit → run / session | — | **MISSING** |
| E28 | run → measured resources | ollama invocation record only | **PARTIAL, 1 surface** — and not for any service operation |
| E29 | run → work item | — | **MISSING** |
| E30 | run → capability | ollama `operation_id` is a free-form label; console receipt `operation_type` matches its capability id; asset receipt `event` does not | **PARTIAL and accidental** (D3) |
| E31 | run → budget | — | **MISSING** — no budget is decremented by anything |
| E32 | operation → receipt | `SPEC.md` C8; every service emits one | **REALIZED** for built services |
| E33 | receipt → resource consumed | — | **MISSING** — no field in `contracts/receipt.schema.json` |
| E34 | run → independent observation | `observe_run`; `scripts/witness_*.py`; `contracts/observation.schema.json` | **PARTIAL** — the transition and the schema exist, the Observation Service does not; `AI-NATIVE.md` check 3 reads `UNATTESTABLE` on every assessed surface |
| E35 | observation → evidence address | `observed_state_addresses` + digests | **REALIZED** |
| E36 | evidence → standing change | `contracts/ticket-transitions.json`, checked | **REALIZED** as a rule; never exercised — nothing in the repository is `WITNESSED` |
| E37 | standing → owner acceptance | `STATUS.yaml`; `decisions/0023` ACCEPT/REJECT/STRIKE/REDIRECT | **REALIZED** for design artifacts; **MISSING** as a reachable surface (J8) |
| E38 | domain owner → budget | `contracts/domain-owners.json` | **REALIZED as intent** for 3 of 8 domains |
| E39 | domain owner → spend | — | **MISSING** — `sov_owners.py` validates the envelope and computes nothing |
| E40 | domain owner → operations owned | — | **MISSING** — an owner names a domain and a mandate, never the capabilities in it |

## Summary of the matrix

`DERIVED`.

- **Realized: 14 edges.** All of them sit between capability and receipt.
- **Partial: 10 edges.**
- **Missing: 16 edges.** Fourteen of the sixteen are above the requirement or between the
  work surface and the operation.

## The four edges that unlock the most

`PROPOSED`, ranked by how many other edges they enable:

1. **E19 work item → operation.** One field on a ticket. Enables E24 (through the PR
   transition block that already carries a ticket reference), E29, and the whole "how much
   effort have we spent on this promise" direction.
2. **E30 run → capability.** Reconcile emitted receipt event names to capability ids and
   add a check. Enables E28 and E33 to mean something once they exist.
3. **E33 receipt → resource consumed.** One optional object on the receipt contract.
   Turns `RESOURCE_CONSUMPTION` from a label into a measurement.
4. **E6 journey → capability**, which requires E3 and E4 first. This is the only one
   needing genuinely new prose, and it is the one that makes the upward question
   ("why did we spend this?") answerable at all.

---

# 12 · Atlas and decomposition fit

## Does the proposed layer stack fit?

`DERIVED`. The brief's decomposition against what the repository already has:

| Proposed layer | Existing owner | Fit |
| --- | --- | --- |
| FOUNDING CONTRACT | `CONTRACT.md` C1–C15 | **exact** |
| PRODUCT CANON | — | **absent, and this is Break 1** |
| PRODUCT ATLAS | partially: `contracts/capability-offices.json` + capability map + `services/registry/CHARTER.md` | **half present under other names** |
| PRD / PRODUCT SLICE | `PRD.md` | **exact**, but PRD sits directly under the contract with nothing between |
| LOGICAL SPECIFICATION | `SPEC.md` + `contracts/kernel-transitions.json` | **exact** |
| SERVICE + INTERFACE CONTRACTS | `contracts/service-manifest.schema.json` + eight `service.json` | **exact** |
| ARCHITECTURE | `ENGINEERING.md` + `CLASSIFICATION.md` | **exact** |
| IMPLEMENTATION | `services/*/src/` | **exact** |
| CONFORMANCE / OBSERVATION | `conformance/` + `services/observation/` + `AI-NATIVE.md` | **exact** |

Seven of nine layers already exist with a single declared owner. The stack fits because it
is largely a description of what is there. **One layer is missing (Product Canon) and one
is half-built under other names (Atlas).**

`PROPOSED`: this is the strongest argument for a small canon rather than a large one. The
repository does not need a new spine; it needs the one vertebra between `CONTRACT.md` and
`PRD.md` that nothing occupies.

## Atlas vocabulary, term by term

`OBSERVED` for the collisions; `PROPOSED` for the verdicts.

| Term | Verdict | Why |
| --- | --- | --- |
| **Atlas** | `COLLIDES_WITH_EXISTING_VOCABULARY` | `SYSTEM.md` Initial subsystems already names **Atlas**: *"addressable views, routes, crossings, and declared projections."* `CLASSIFICATION.md` files it under cross-cutting capabilities; `PRD.md` Non-goals warns against *"treating Gauge, Definition, Atlas, or another subsystem as the whole product"* — which is precisely what reusing the word for "whole product world" would do. `ROADMAP.md` F5 also names it. Four governing documents. |
| **Chart** | `COLLIDES_WITH_EXISTING_VOCABULARY` | `SOV.md` line 120 refers to *"Dynamic Chart compilation"*; issue `#42` is *"Chart compiler bindings — lower governed charts into human/model operator environments"*. A chart there is something **compiled and lowered into an operator environment**, not a semantic territory. Two incompatible senses. |
| **Station** | `GOOD_FIT`, and probably `UNNECESSARY` | Nothing uses the word. The job is already done by **office** (`FRONT`/`BACK`) and **counter** (12 of them), which are checked by `contracts/capability-map.schema.json` and used by `.claude/epic/offices.json`. Introducing a synonym for a working term would violate `AGENTS.md` ("Do not create synonyms for existing standing, event, effect, or role terms"). |
| **Point** | `PARTIAL_FIT` and `DANGEROUSLY_AMBIGUOUS` | Issue `#40` already claims *"typed points"*. Separately, "point = capability / named operation" would be a third name for a thing that already has two (`capability_id` and `logical_endpoint`). |
| **Crossing** | `DANGEROUSLY_AMBIGUOUS` | Already load-bearing in three distinct senses: `CONTRACT.md` C8 *"Every crossing returns a receipt"*; the `SPEC.md` `cross` transition; `contracts/federation-crossing.schema.json`; and `adapters/github/README.md`'s crossing table. Redefining it as "interaction between charts/stations" would put a new meaning on an invariant. |
| **Path** | `PARTIAL_FIT` | Unclaimed as product vocabulary, but `path` is already a field on `contracts/issue-metadata.schema.json` (a repository path) and is a common word in every file listing. **Journey** is unclaimed and unambiguous, and is the better word for the same thing. |
| **Covering** | `OWNER_JUDGEMENT_REQUIRED` | Claimed by `#40` (*"coverings"*). The concept — an alternate interface exposing equivalent semantics — is already realized as the capability map's `endpoints[]` array, where one capability carries four transports. Whether that array is a covering or whether coverings are something else is `#40`'s question. |
| **Paradigm** | `OWNER_JUDGEMENT_REQUIRED` | Claimed by `#40`. Nothing else in the repository uses it and nothing realizes it. |

## The shape of the collision

`DERIVED`. Five of the eight terms — Atlas, Chart, Point, Crossing, Covering — are already
in use or already claimed, and two of the claims (`#40`, `#42`) are open tickets with
`requires` edges and a live RED engagement (`#57`) against them. Two more (Station, Path)
duplicate working vocabulary. **One term, Journey, is free and needed.**

`PROPOSED`: adopting the Atlas set wholesale would put new meanings on `CONTRACT.md` C8, on
a `SYSTEM.md` subsystem, and on two open tickets, in a repository whose own naming rule
(`NAMING.md`, `AGENTS.md`) exists to prevent exactly that. The concepts the brief is
reaching for are mostly present; it is the labels that are taken.

`OWNER`: whether `#40`'s charting vocabulary *is* this spine wearing a different name, or a
neighbouring thing that happens to share words, is not settleable from the artifacts —
`#40` has `evidence_pointer: PENDING` and no body was read this pass. It is queued as Q4.

---

# 13 · Candidate minimum attribution schema

`PROPOSED`, conceptual only. Nothing implemented. For each identifier: what cannot be
joined without it, whether an equivalent already exists, who would own it, whether it must
be immutable, whether it can be a projection, its cardinality, and what must **not** be
encoded into it.

## Identifiers that already exist and need no minting

| Proposed id | Existing equivalent | Owner |
| --- | --- | --- |
| `capability_id` | `capability_id`, `<service>.<operation>` | capability map |
| `operation_id` | `logical_endpoint`, `sov://<service>/<operation>` | service manifest |
| `service_id` | `service_id` | service manifest |
| `interface_id` | transport + address in `endpoints[]`; `interface_id` on `Receipt` | capability map / SPEC |
| `requirement_id` | `PROD-I-<n>` | `PRD.md` |
| `predicate_id` | transition names in `contracts/kernel-transitions.json` | `SPEC.md` |
| `work_item_id` | GitHub issue number, plus `bit_id` / `stub_id` / `story_id` / `engagement_id` / `unblock_id` | issue metadata contract |
| `change_id` | commit sha; PR number | git |
| `run_id` | `run_id` on `Run` and `Observation` | `SPEC.md` |
| `actor_id` | `actor_id`, with `actor_kind` | `SPEC.md` |
| `binding_id` | `binding_id` | `ModelBinding` |
| `receipt_id` | `receipt_id` | `SPEC.md` |
| `evidence_address` | address + digest pairs throughout | `SPEC.md` |
| `station_id` | office + counter | capability-offices table |

**Fourteen of the twenty identifiers the brief listed already exist.** That is the real
headline of this section.

## Identifiers that would have to be minted

```yaml
id: promise_id
what_cannot_be_joined_without_it: nothing above a requirement. A requirement has no parent,
  so "why does PROD-I-2 exist" has no answer in the repository.
existing_equivalent: none. The nine promises in §4 live as prose in five documents.
owner: a new canon document; PROPOSED to sit between CONTRACT.md and PRD.md
immutable: yes — a promise that changes identity silently changes what was built
projection: no. This is authored intent, not derived.
cardinality: single digits. Nine explicit promises exist today; more than ~15 would mean
  the layer has become a second PRD.
must_not_encode: a service, a phase, a priority, or a status. A promise outliving Phase I
  must not carry F-numbers in its identity.
```

```yaml
id: journey_id
what_cannot_be_joined_without_it: a need to a capability. Today an operation's only parent
  is a requirement shared with up to 31 siblings.
existing_equivalent: partial — conformance/scenarios.json ids (RUN-I1-PROPOSE …) are
  journey-shaped but requirement-derived, one per requirement, and there are exactly nine.
  The story kind (kind: story, story_id) is the closer shape and has one instance (#67).
owner: PROPOSED — the same canon document, or conformance/scenarios.json extended
immutable: yes
projection: no
cardinality: tens. One per complete user intention, not one per screen.
must_not_encode: the station it starts at (a journey may be reachable from more than one),
  or the service that serves it.
```

```yaml
id: need_id
what_cannot_be_joined_without_it: a promise to an actor. Whether this is separate from
  journey_id is genuinely open — a journey is a need plus a path.
existing_equivalent: none
owner: PROPOSED — the canon document
immutable: yes
projection: no
cardinality: tens
must_not_encode: anything
recommendation: [PROPOSED] fold into journey_id for a first pass. One identifier that says
  "an actor wanting X" is enough to close E4–E6; splitting need from journey before either
  exists is taxonomy ahead of evidence.
```

```yaml
id: chart_id
what_cannot_be_joined_without_it: arguably nothing. §5 shows ten territories and every one
  of them is already recoverable from service_id plus counter.
existing_equivalent: office + counter (12), village (4), harness domain (9), service (8).
  Four overlapping groupings already; services/registry/CHARTER.md names eight tables that
  drift.
owner: would be #40 or the Registry
immutable: n/a
projection: YES — if it exists at all, it should be derived, not authored
cardinality: ~10
must_not_encode: —
recommendation: [PROPOSED] do not mint. A fifth grouping over the same 102 operations is
  the drift the Registry charter exists to end.
```

```yaml
id: canon_revision_id
what_cannot_be_joined_without_it: "which version of the product definition was this built
  against" — the same question artifact_revision already answers for AI-native assessments.
existing_equivalent: git commit sha; contracts carry input_state_digest; AI-NATIVE.md's
  required test record already carries artifact_revision.
owner: git
immutable: yes, by construction
projection: n/a
cardinality: one per commit
recommendation: [PROPOSED] do not mint. Use the commit sha, as every other contract here
  already does.
```

```yaml
id: session_id
what_cannot_be_joined_without_it: run to actor to elapsed work across more than one run
existing_equivalent: YES — console operator session (session_79fba9735cc343f4), and
  bindings/mcp act-tier sessions
owner: Console Service
immutable: yes
projection: no
cardinality: many
must_not_encode: a grant. A session is not authority (SPEC.md, CHARTER.md).
recommendation: exists; needs to reach the receipt, which it does not today.
```

```yaml
id: budget_id
what_cannot_be_joined_without_it: intent-to-spend to actual spend
existing_equivalent: partial and overloaded — AuthorityGrant.budget (no unit),
  domain-owners budget (USD/run), OperationPlan.limits (no schema)
owner: OPEN. AGENTS.md puts grants at the operation boundary; domain-owners puts envelopes
  at the domain. These are different altitudes and both are legitimate.
immutable: no — a budget is consumed
projection: no. A remaining balance derived from receipts is a projection; the envelope is not.
cardinality: tens
must_not_encode: a unit. The unit belongs in the envelope, not in the identity — the node
  meters tokens, wall clock and USD, and a fourth will appear.
```

## The smallest set that closes the chain

`PROPOSED`. Three new identifiers and two new record fields:

1. `promise_id` — authored, immutable, single digits.
2. `journey_id` — authored, immutable, tens; absorbs `need_id` for now.
3. `budget_id` — only when something actually spends against it; not before.
4. **field:** `capability` (or `operation`) on `contracts/issue-metadata.schema.json`.
   Optional, so no existing ticket breaks. This is edge E19 and it is one line of schema.
5. **field:** `consumed` on `contracts/receipt.schema.json` — an optional object
   `{unit, amount, meter, measured_by}`, repeatable. This is edge E33, and it is the field
   `RESOURCE_CONSUMPTION` has been naming for two days with nothing behind it.

Everything else in the brief's twenty-identifier list already exists.

## Prefer links over restated descriptions

`OBSERVED`. The repository already holds this rule and enforces it:
`services/registry/CHARTER.md` — *"The Registry resolves; it does not define… Every registry
entry names the document that owns its subject and carries that document's address and
digest."* A promise or journey record should carry an address and a digest of the document
that owns its wording, never a copy of it.

---

# 14 · Project tracking as a projection of product intent

`OBSERVED`. The brief asked two specific questions of the tracker. Both have clean answers.

## Can a work item say why it exists?

> *"I exist because operation X is required for journey Y, which realizes capability Z,
> which serves product promise P under Canon revision C."*

**No.** `contracts/issue-metadata.schema.json` carries 47 properties. What it can say today:

- **which territory** — `village` (4 values), and separately `.claude/epic/offices.json`
  places the issue in one of 12 offices;
- **what kind of work** — `kind` (7 values: epic-of-epics, village, bit,
  implementation-stub, verification-engagement, story, unblock);
- **what it depends on** — `requires` (a DAG, deliberately not GitHub's single-parent tree),
  `parent_bits`, `dependency_channels`;
- **how much evidence stands behind it** — `standing` (8 values), `evidence_pointer`,
  `walker_receipt`, `last_observed_at`, `demotion_pointer`;
- **what it may do** — `authority`, `effect_class` (8 values, a wider enum than the kernel's
  three);
- **when** — `horizon` (6 values).

What it cannot say: **which capability, operation, service, endpoint, requirement, journey
or promise this work serves.** Not one of the 47 properties is a product referent.

The `story` kind is the exception that proves the shape is reachable: it carries
`actor_kind`, `role`, `expected`, `found`, `leans_on`, `asks`, and `scenario` — a teller, a
need, a gap, and a binding to `conformance/scenarios.json`. That is four-fifths of the
missing layer, already contracted, already accepted (`decisions/0022`), and instantiated
**once** (`#67`).

Minimum addition to close it: one optional `capability` field (an array of `capability_id`
values). Optional means no existing ticket breaks and no backfill is forced.

## Can a run say what it spent?

> *"This run spent N wallclock, N model tokens, N tool calls, N compute/cost units against
> budget B, produced these changes/evidence, and advanced or failed to advance that work
> item."*

**No, on every clause except the evidence one.**

- wall clock — only for `verify.py` checks, into a gitignored file;
- model tokens — only for ollama invocations, into an adapter-local file;
- tool calls — never counted anywhere;
- cost units — recorded once, as zero, with an open question about whether that is right;
- against budget B — no budget is decremented by anything;
- produced these changes / evidence — **yes**: this is the strong part.
  `emitted_record_addresses`, `observed_evidence_addresses`, the digest chain, `git diff`;
- advanced that work item — **partly**: `contracts/ticket-transition.schema.json` requires
  `ticket`, `from`, `to`, `actor_id`, `actor_kind`, `reason`, `effect_class` and `evidence`,
  and `contracts/ticket-transitions.json` refuses skipped standings, a builder witnessing
  its own work, an unconverged Red engagement, a confirmed finding with no permanent
  defeating fixture, and any machine claiming `RATIFIED`. The mechanism is real, checked by
  `scripts/sov_ticket.py transition`, and carries no resource field.

Minimum addition: an optional `consumed` array on the receipt contract, and the same on the
ticket transition request.

## Is GitHub the semantic authority?

`OBSERVED`. **No, and the repository is unusually clear about it.**

- `CONTRIBUTING.md`: *"GitHub is the coordination surface; the issue body remains the
  compressed specification."* and *"Display labels are projections of that metadata, not a
  second authority."*
- `.claude/epic/README.md`: the checked-in `tree.json` is *"a derived view of the issue
  tree. Non-authoritative"*, carries `synced_at`, and *"a walk reports the age rather than
  pretending currency."*
- `contracts/ticket-queue-policy.json`: *"The queue is a projection… position in it grants
  nothing."*
- `CONTRIBUTING.md`: *"A branch or pull request may close an implementation stub; it cannot
  by itself close its bit, promote a village, satisfy independent witness, or ratify the
  epic."*
- `adapters/github/` is the only directory permitted to call the GitHub API; every other
  check reads an export from disk.

`DERIVED`. One qualification. The tracker is a projection **of the issue body**, and the
issue body lives on GitHub. The metadata contract is checked in; the instances are not. So
the repository owns the shape of a work item and GitHub owns its content — which is why
`tree.json` exists and why refreshing it is an attended action.

That is a coherent boundary and it does not need changing for this spine. What it does mean:
a `capability` field added to the ticket schema would be authored on GitHub and read
locally, and a check that every declared operation is claimed by at most one open ticket
would run over the export, offline, like every other ticket check already does.

---

# 15 · Contradictions and open seams

`OBSERVED` unless marked. Nineteen seams are already carried in `OPEN-SEAMS.md`; listed
here are the ones this pass touched, plus what it found that is not yet recorded there.

## Already carried in OPEN-SEAMS.md and directly load-bearing for this spine

| Seam | Bearing on attribution |
| --- | --- |
| **S10 · Product boundary** | *"The boundary between a primary enterprise application and a constitutional runtime over existing applications must be tested through the first real subsystem rather than decided by metaphor alone."* This is the product-canon question, already open since founding. Any canon that answers it settles S10; any canon that avoids it is decoration. |
| **S12 · Ratification mechanism** | Owner input 2026-08-23: a code-owner review click cannot be Bdo's ratification surface. The Console judgement request is the chartered home and is unbuilt. Until it exists, the owner-acceptance edge (E37) has no reachable carrier — which is exactly what Trace 5 shows happening in practice. |
| **S14 · Two owners of the asset projections** | Blocks journey J10 and makes promise P16 `CONTRADICTORY`. |
| **S15 · Judgement request and unblock request** | *"These are one record seen from two surfaces… One must project from the other; neither may become a second queue of owner rights."* The same problem this spine has generally, in miniature and already named. |
| **S16 · Decision-number allocation across branches** | Structural warning for any new identifier: the repository already has one identifier family that collides across branches, and `decisions/0043` is absent from this branch's sequence. Anything minted here needs an allocation rule before it needs a schema. |
| **S18 · Two layers named gateway** | *"an operator reading a receipt cannot tell which gateway refused"* — an attribution failure already recorded as a naming failure. |
| **S19 · Who publishes: an operator or a seat** | A record cannot fill `published_by` honestly because two contracts name the actor at different altitudes. The same class of defect as E30. |

## Contradictions this pass found, not currently in OPEN-SEAMS.md

`DERIVED`. Recorded as findings, not filed — filing a seam is a change to a governing
document and this pass changes none.

**C1 · A live interface the reachability projection cannot represent.**
`bindings/mcp/manifest.json` exposes six tools; `contracts/fixtures/capability-map.reference.json`
records `MCP: DECLARED_NOT_ACTIVATED` on all 102 rows, because
`scripts/sovkernel/capability_map.py` can derive `ACTIVE` only from `built` and from
`cli_commands`. The map that exists to say what is reachable cannot see the one reachable
model surface. (§8 D1.)

**C2 · Receipt event names and capability ids agree for one service and not the other.**
Console: nine of nine match. Asset: zero of five match, and `federation.cross` names no
capability at all. Nothing checks either. (§8 D3, D4.)

**C3 · "Budget" means six things.** An authority-grant scope with no unit
(`SPEC.md`); a per-domain-owner money envelope (`contracts/domain-owners.json`); an
unschema'd `limits` object (`OperationPlan`); a graded wall-clock ceiling
(`scripts/verify.py`, `decisions/0042`); a context-package token ceiling
(`services/projection/`); and a module line ceiling (`ENGINEERING.md`, `scripts/lint.py`).
`AGENTS.md` forbids synonyms for existing terms; nothing forbids a homonym, and six have
accumulated.

**C4 · The one requirement demanding a recorded cost is failed by the only participant.**
`PRD.md` PROD-I-1 requires a proposal at a recorded cost;
`services/asset/conformance/BASELINE.md` records `FAIL — proposal lacks content address,
source addresses, and cost record`, unchanged since 2026-08-22. This is not new
information; it is the oldest evidence in the repository that the effort question was
already unanswerable.

**C5 · `RESOURCE_CONSUMPTION` is an effect class with no field behind it.** Declared in
`AGENTS.md`, `SPEC.md`, every service manifest and `contracts/capability-offices.json`.
Three capabilities carry it (`asset.request-derivative`, `proofing.request-comparison`,
`projection.register-vectors`). No contract in `contracts/` has a field recording what was
consumed.

**C6 · The only durable-looking effort record is gitignored.**
`.local/observations/latest.json` holds one `Observation` per verification check with
`elapsed_seconds`, a `run_id` and an `observer_relation` — good records, overwritten every
run, in a directory `.gitignore` excludes at line 33.

**C7 · The asset `runs` table cannot compute a duration.** `SPEC.md`'s `Run` object declares
`started_at` and `completed_at`; `services/asset/src/soveraeign_asset_service/runs.py`
carries `created_at` and no completion time.

**C8 · Charts of issues and charts of operations are never reconciled.**
`decisions/0038` Consequences: *"`.claude/epic/offices.json` groups issues by office; this
map groups operations by office. They must not disagree, and nothing yet checks that they
do not."*

## Preserved unknowns

`DERIVED`. Left visibly unresolved rather than guessed:

- Whether `#40`'s charting vocabulary is this spine under other words (Q4).
- Whether `PRD.md`'s "maintainers and federated enterprise nodes" is a real participant
  class or leftover wording.
- What is in the live GitHub issue bodies, as against the projection read here.

Closed during this pass: whether the two residual manifests from `decisions/0038` still
fail validation. They do not — `verify.py` reports 8 manifests and 102 operations with no
defect (§8 D7).

---

# 16 · Owner judgement queue

`OWNER`. Six questions. Each one changes what product is being built or what a governing
word means; none is an ordinary engineering choice. Every question is phrased for
`ACCEPT` / `REJECT` / `STRIKE` / `REDIRECT` per `decisions/0023`, and each carries the
evidence and the strongest case against.

Not queued, deliberately: whether to add a field to a schema, what to name a projection,
where a module lives, how to compute a digest. Those are settleable at Control or Work
under `decisions/0033` Ruling 1.

---

### Q1 · Does a product-canon layer exist at all?

**The question.** Should there be one addressed layer between `CONTRACT.md` and `PRD.md`
naming participants, needs and promises — so that a requirement has a parent and an
operation has a reason?

**Evidence for.** `NEED` is `MISSING` in 12 of 13 journeys (§7). The `needs` line is
inference for all 10 actor classes (§3). Nine PRD requirements carry 102 operations, one of
them 32 (§8 D5). Nothing in the repository answers "who is this for".

**Strongest case against.** `PRD.md` Non-goals already warns against treating a subsystem
as the whole product, and `README.md` says the next code change *"must not decide what the
product means."* A canon written before F5 delivers one real enterprise workflow risks
being metaphor rather than evidence — which is precisely what `OPEN-SEAMS.md` S10 warns
about.

**Options.** `ACCEPT` a small canon now (≈1 page, ≤15 promises, no new machinery).
`REDIRECT` to file promises as `kind: story` tickets instead, using the contract that
already exists. `REJECT` and carry the gap under S10 until F5.

---

### Q2 · Is the effort question worth instrumenting in Phase I?

**The question.** Should a receipt carry what its operation consumed?

**Evidence for.** `RESOURCE_CONSUMPTION` is one of three effect classes and has no field
behind it (C5). `PRD.md` PROD-I-1 requires a recorded cost and the reference participant
fails it (C4). `PRD.md` PROD-I-6 requires reporting *"where human judgement was spent"* and
nothing measures spend of any kind. Three domain owners have declared USD budgets that
nothing decrements (§9).

**Strongest case against.** `PRD.md` Non-goals: *"Optimizing performance before semantic
conformance."* Measurement is not optimization, but it is machinery, and no Phase-I
requirement is currently blocked for want of it — PROD-I-1 is blocked for want of a cost
*field on a proposal*, which is a smaller thing than a metering substrate.

**Options.** `ACCEPT` a minimal `consumed` object on the receipt contract, optional,
populated only where a meter already exists. `REDIRECT` to close PROD-I-1's `cost_record`
only, and defer general metering. `REJECT` and carry it to F5.

---

### Q3 · Which promise is Soveraeign's first, for a user who is not Bdo?

**The question.** Every explicit promise in §4 is a property of the record. P15
(version-pinned review) is the only one aimed at ordinary enterprise work, and P17 — what
this does for a business — is `UNKNOWN`. Which promise does the node exist to keep?

**Evidence.** `OPEN-SEAMS.md` S10 has carried this since founding. `ROADMAP.md` defers
"one bounded real enterprise workflow" to F5. `README.md` Immediate objective explicitly
declines to rank the two lanes: *"ordering them is owner judgement, and this file does not
hold it."* Eleven capabilities sit chartered and unbuilt at FRONT/review-desk.

**Why it is owner-held.** This is product intent. `AGENTS.md`: no agent may present its
synthesis as Bdo's judgement.

**Options.** `ACCEPT` proofing as the first business-facing promise. `REDIRECT` to a
different first workflow. `REJECT` and hold the question until F5 as currently planned.

---

### Q4 · Is issue `#40`'s charting vocabulary this spine, or a neighbour?

**The question.** `#40` is *"Charting contract — canonicalize typed points, crossings,
coverings, and paradigms"*, `OPEN`, horizon `NEXT`, `requires: [#6, #7, #14, #25]`, with a
RED engagement `#57` open against its foundation. `#42` lowers *"governed charts"* into
operator environments. Five of the eight terms the discovery brief proposed are already
spoken for there.

**Why it is owner-held.** Two answers lead to different work. If `#40` is this spine, the
right move is to write its body and let it absorb the promise and journey layer. If it is a
neighbour, then this spine needs different words — because reusing **Atlas** (a `SYSTEM.md`
subsystem, cited in four governing documents) or **Crossing** (`CONTRACT.md` C8, an
invariant) would put new meanings on settled text, and `NAMING.md` owns the collision
screen with Bdo owning naming.

**Evidence.** §12 term table. `#40` has `evidence_pointer: PENDING`; its body was not read
this pass.

**Options.** `ACCEPT` that `#40` is the home and route this work there. `REDIRECT` to a
separate boundary with non-colliding words (**journey** is the only free term of the
eight). `STRIKE` `#40` if its vocabulary is no longer wanted.

---

### Q5 · Does a locally hosted model's wall clock spend against anything?

**The question.** `adapters/ollama/` records `monetary_charge: 0`,
`basis: OWNER_OWNED_HARDWARE`, with wall clock metered separately and a note that a local
run is *"cheap rather than free"*. Is a local run's cost zero for budget purposes, or does
wall clock spend against a run's limits?

**Why it is owner-held.** It sets what "spend" means for the whole node, and the answer
decides whether a budget is money or a resource envelope. `adapters/ollama/README.md`
already queues this to Bdo as its question 3; it is repeated here because it is now on the
critical path for anything measuring effort.

**Options.** `ACCEPT` zero-cost-local (wall clock recorded, never charged).
`REDIRECT` to a declared conversion. `REJECT` and hold budgets at the money envelope only.

---

### Q6 · Where does the ticket's product referent live?

**The question.** If a work item is to say which capability it serves, the field is
authored on GitHub (where issue bodies live) and read locally. Is that acceptable, or must
the referent live in the repository?

**Evidence.** `CONTRIBUTING.md` already treats the issue body as the compressed
specification and labels as its projection; `adapters/github/` is the only directory
permitted to call the API; `decisions/0044` (`PROPOSED`, unruled) governs the write half.
`OPEN-SEAMS.md` S15 already warns that one record seen from two surfaces must project from
one source, never become two queues.

**Why it is owner-held.** It decides whether the coordination surface holds any product
identity at all, which is the exact boundary the brief asked not to concede by default.

**Options.** `ACCEPT` the field on the ticket schema, authored on GitHub, checked offline
against the capability map. `REDIRECT` to a repository-side table mapping ticket → capability,
with the ticket carrying nothing. `REJECT` and leave work items without a product referent.

---

# 17 · Recommended next bounded work

`PROPOSED`. Sequenced by dependency, typed by kind. Nothing below is started. Times are
rough and assume one operator.

## Lane A · Research (no dependency; can start now)

**A1 · Read issue `#40`, `#41`, `#42`, `#48` bodies and report whether the charting
contract is this spine.** ~1 h. Requires an attended `gh` crossing (`sov_epic.py sync` is
already the declared path). Feeds Q4 and blocks nothing else. This is the single cheapest
thing that could change the shape of everything below.

**A2 · Amend `decisions/0038` Residuals to record that the manifest residual is closed.**
~10 min. Re-verified in this pass (§8 D7); the decision record still reads as open, which
is the kind of small drift `sov_next.py` exists to catch and does not cover here.

## Lane B · Product definition (depends on Q1; blocked on Bdo)

**B1 · Draft the canon at proposal standing.** ~3 h. Nine to fifteen promises with
identities, ten actor classes with a stated need each, and ten to twenty journeys. Cites
existing documents by address and digest rather than restating them
(`services/registry/CHARTER.md`'s own rule). Lands as `decisions/00NN` plus one document;
changes no governing file until accepted.

**B2 · Bind each of the nine PRD requirements to at least one promise.** ~1 h, after B1.
Turns the 32:1 fan-in into a two-level hierarchy without touching `PRD.md`.

**B3 · File the remaining journeys as `kind: story` tickets.** ~2 h, after B1. Uses the
contract that already exists and is accepted (`decisions/0022`); `#67` is the template.
This is the `REDIRECT` answer to Q1 if the canon itself is rejected, and it works as a
complement if the canon is accepted.

## Lane C · Contracts (independent of Q1; each is small and separately useful)

**C1 · Add an optional `capability` array to `contracts/issue-metadata.schema.json`.**
~2 h with fixtures. Closes E19. Optional, so nothing breaks and nothing is backfilled by
force. Depends on Q6.

**C2 · Add an optional `consumed` array to `contracts/receipt.schema.json`.** ~2 h with
fixtures. Closes E33 and gives `RESOURCE_CONSUMPTION` a field. Depends on Q2. Positive
case: an ollama invocation receipt carrying its real token counts. Defeating cases: a
`RECORD_LOCAL` receipt claiming consumption; a `consumed` entry with no unit; a receipt
claiming a retraction reversed consumption (`CONTRACT.md` C9).

**C3 · Give `OperationPlan.limits` a shape.** ~1 h. Same vocabulary as C2. Turns
`begin_run`'s budget precondition into something checkable. Depends on Q5 for units.

**C4 · Teach `contracts/capability-offices.json` an `mcp_tools` map, as it already has
`cli_commands`.** ~2 h. Closes C1/D1 — the live MCP surface becomes visible to the map, and
`bindings/mcp/manifest.json`'s `realizes` field becomes the check rather than a comment.
No owner question; this is a defect against an existing contract.

## Lane D · Instrumentation (depends on Lane C)

**D1 · Reconcile emitted receipt event names to capability ids, and add a check.** ~3 h.
Rename five asset events (or declare an alias table), declare `federation.cross` as an
operation or remove it, then add a `verify.py` check that every emitted `operation_type`
resolves to a capability-map row. Closes E30 and C2. **This is the highest value-to-cost
item in the report** — it makes every future receipt joinable to the map, and it is a
naming reconciliation plus one check.

**D2 · Add `completed_at` to the asset `runs` table.** ~30 min. Closes C7 and makes a
delegated run's wall clock computable at all.

**D3 · Write the ollama invocation record's usage into a receipt.** ~2 h, after C2. Gives
the node exactly one operation whose full chain — capability, requirement, authority,
receipt, tokens, wall clock, cost — resolves end to end. One is enough to prove the shape.

## Lane E · Implementation (depends on Bdo, and on work already queued elsewhere)

**E1 · Build the judgement request and resolution path** (`console.request-judgement`,
`console.resolve-judgement`). Days, not hours. Closes journey J8, seam S12 and edge E37.
This is the Console charter's own declared first slice, deferred once by `decisions/0036`.
It is what Trace 5 shows the absence of: the owner's live question is currently a thread
post because the judgement record does not exist. Gated on nothing but sequencing —
`decisions/0036` says the continuity path was built *so that* this could be operations on a
mechanism that already exists.

**E2 · A projection joining ticket → capability → requirement → promise.** After B1 and C1.
Rebuildable, digest-checked, refusing when stale — the same shape as the capability map, and
buildable by extending `scripts/sovkernel/capability_map.py` rather than by minting a new
projection family.

## Dependency order

```text
A1 ──────────────► Q4 ──► (shapes B and E2)
A2 (independent)

Q1 ──► B1 ──► B2
          └──► B3

Q6 ──► C1 ──┐
Q2 ──► C2 ──┼──► D3
Q5 ──► C3 ──┘
(none) C4

(none) D1   ◄── start here; no owner question blocks it
(none) D2

B1 + C1 ──► E2
(sequencing only) ──► E1
```

**If only one thing is done: D1.** It requires no owner decision, closes the accidental
half of the run-to-capability join, and every later measurement depends on it.

**If only one owner question is answered: Q1.** Everything in Lane B and half of E2 waits
on it, and it is the question the owner opened this work with.

---

# 18 · Machine-readable artifact

`PROPOSED`. **Not emitted.** No natural existing location or format fits, and the brief's
own instruction is to recommend rather than invent a competing source of truth.

Why each candidate was rejected:

- `reports/` holds prose only — all eighteen existing reports are `.md`. A JSON file here
  would be the first, with no reader and no check.
- `contracts/fixtures/` holds reference projections **of governed contracts**, each rebuilt
  by a named script and checked by `scripts/verify.py`. Placing an unrebuildable research
  table there would look like policy and would drift on the first commit.
- `contracts/` holds schemas and authored policy tables. This research is neither.
- `.local/` is gitignored and would not travel.
- `conformance/observations/` holds participant observations against the oracle.

**Recommended instead**, in this order:

1. **The inventories in this report are already the machine-readable artifact, once they
   are joins rather than tables.** §8 does not restate the 102 operations precisely because
   `contracts/fixtures/capability-map.reference.json` already is that record, rebuilt and
   digest-checked. The right destination for the missing columns is *that projection gaining
   fields*, not a second file.

2. **Extend `scripts/sovkernel/capability_map.py`** once `promise_id` and `journey_id` exist
   (B1) and the ticket carries a `capability` (C1). The map already joins manifests to a
   policy table, carries `input_state_digest`, refuses when stale, and has eight defeating
   fixtures. Adding `promise`, `journey`, `work_items` and `consumed_to_date` columns
   extends a working projection instead of founding a competing one — which is the
   `services/registry/CHARTER.md` complaint about the existing eight hand-maintained tables,
   answered rather than repeated.

3. **Until then, the ROADMAP name crosswalk is the working precedent.** Four rows, the only
   place identity across vocabularies is asserted, and `scripts/sov_next.py` fails when a
   row stops resolving. If a joined table is wanted before B1 and C1 land, adding rows there
   is the honest small version — it already has a reader and a check.

---

## Closing note on standing

This report observes. It settles nothing, ratifies nothing, and renames nothing. No
governing document was edited. Six questions are queued for Bdo in §16; everything else in
§17 is settleable at Control or Work under `decisions/0033` Ruling 1 and should not wait.

The quality bar the brief set was whether a reader could take a product idea — *"a person
can bring their own agent into a sovereign node and discover and use the capabilities
available under their authority"* — and follow it down to evidence. Against that idea
specifically: the capabilities exist and are enumerated (102, with authority and reachability
per transport); the discovery answer exists as data and is served by nothing; the "bring
your own agent" half is real, measured, and off the map; and the chain has no top, because
no artifact in the repository says that sentence is a promise Soveraeign makes.

---

# Addendum · 2026-08-24 — A1 boundary analysis, and what was built

Added after Bdo's rulings on §16. This addendum records the answer to Q4 and the work
done under §17; the sections above are unchanged and still describe the state before that
work.

## A1 · Is `#40` this boundary? — **`COMPOSES_WITH`**

`OBSERVED`. The live bodies of `#40`, `#41`, `#42` and `#48` were read through `gh` on
2026-08-24, an attended crossing per `.claude/epic/README.md`. The bodies say more than
the titles and they change the answer from "cannot tell" to a clear one.

**`#40` Charting contract** is a *typed-graph and projection substrate*. Its bounded
obligation is "the smallest canonical typed-contract charting vocabulary required to
project governed local views." Its acceptance contract asks for stable identifiers with
explicit provenance, a graph that can reject type-invalid relations, a covering that
selects local material without becoming authoritative, a chart that pins its source
revision and declares omissions, and tree views that are projections rather than
canonical hierarchy. Its defeating cases include *"a graph edge collapses requirement,
capability, implementation, and evidence into one relation"* and *"a stale chart makes an
otherwise illegal transition legal."*

None of that names a promise, a need, a participant's expectation, or product intent.
`#40` is machinery for expressing typed relations and projecting them safely.

**`#41` Skill and capability graph** is *eligibility derivation*: "represent skills,
requirements, capabilities, implementations, and operator possession as typed relations so
eligibility can be derived instead of inferred from prompt prose or folder layout." Its
declared shape is `Skill -> requires -> Requirement -> binds -> Capability`.

**The verdict.** The canon `COMPOSES_WITH` `#40`. The canon would be a consumer,
contributing node and edge types — promise, journey — that `#40`'s vocabulary does not
name, while `#40` supplies the provenance, state-pinning and type-invalidity rules such a
graph needs. Bdo's provisional expectation was right.

**The sub-finding that matters**, and it is worth catching before both exist:

> **`#41`'s `Requirement` and `PRD.md`'s `PROD-I-n` are different things sharing a word.**

`#41`'s Requirement is a *competence obligation a skill carries* — "initial QA
requirements may cover only repository verification and independent observation."
`PRD.md`'s requirement is a *product requirement Phase I must prove*. `#48` then asks for
a schema in which "Requirement identity is distinct from Capability identity", meaning the
competence sense.

The attribution chain uses the product sense: `capability → operation → PROD-I-n`. If
`#41` and `#48` land carrying the other sense unqualified, a reader following a
`Requirement` edge cannot tell which ladder they are on. That is `OPEN-SEAMS.md` S18's
"two layers named gateway" defect one level up, and it is cheaper to name now than to
unpick later.

**`#42` Chart compiler bindings** is `ORTHOGONAL` to the canon. It lowers a state-pinned
chart into human and model operator environments, is explicitly downstream of `#40` and
`#41`, and consumes product intent rather than producing it.

**`#48`** is `COMPOSES_WITH`, carrying the same collision as `#41`.

`OWNER`. Recommended: keep the canon and `#40` separate, and qualify one of the two senses
of `Requirement` before `#41` or `#48` lands. `NAMING.md` owns the collision screen and
naming is Bdo's. Nothing was renamed.

## What was built under §17

`OBSERVED`. Every item below passes `python scripts/verify.py`.

| Item | Outcome |
| --- | --- |
| **D1** receipt events → capability identifiers | Seven asset events renamed to their capability identifier; ten events realizing no declared operation recorded in the manifest with a stated reason each; `scripts/sovkernel/receipt_events.py` reads each service's own source by AST and refuses an event that is neither, or an excuse the service stopped emitting. 27 events across three services, all resolving. Four declared defeats, 14 cases. |
| **A2** the `decisions/0038` residual | Residual 1 closed on evidence — 8 manifests, 102 operations, no defect. Residuals 2 and 3 recorded as standing and as moved, in a `Movement 2026-08-24` section that does not reopen the ruling. |
| **C4** MCP made representable | `contracts/capability-offices.json` gained `mcp_tools` beside `cli_commands`; `asset.ingest-asset` now reads `MCP: ACTIVE`. Table and binding are held together by a check rather than by coincidence. One capability withheld — below. |
| **D2** run completion time | `started_at` and `completed_at` on the asset `runs` table, with a forward migration for stores written before them; `Runs.elapsed()` measures lease to observation and deliberately excludes queue time. Six cases. |
| **B1** the canon | `CANON.md` at `CANON-1`, `contracts/product-canon.json`, its schema, `scripts/sovkernel/canon.py`, `scripts/sov_canon.py`, `decisions/0046`. Ten participants, fifteen promises, thirteen journeys. Nine declared defeats, 21 cases. |

### The finding C4 turned up

`OBSERVED`. Making MCP representable fired `BACK_OFFICE_EXPOSED` — a defect
`decisions/0038` declared and that nothing could trigger until now, because `CLI` and
`IN_PROCESS` are not operator-facing and `HTTP` is always refused. `MCP` is the first
transport able to reach it.

`bindings/mcp/manifest.json` served `record_entries`, realizing `record.read-entry`:
*"Every entry in the operational journal, in append order, with its digest chain"*, at
`read` tier, under no grant. `contracts/capability-offices.json` places
`record.read-entry` at `BACK/record` with `actor_kinds: ["SYSTEM"]`. Two declared rules
broken at once — the office and the actor kind.

`PROPOSED`. Default taken: the endpoint is withheld in the binding, with its reason
recorded in a new `withheld_endpoints` array, and the implementation stays in
`gateway.py`. Policy is older and accepted; the binding is `PROPOSED` plumbing;
withholding is one entry to reverse and re-officing a capability is not.

The view of the participant that took it, offered because agreeing is not support: **the
office table is more likely the wrong side than the binding.** Reading operational history
is how an operator finds out why something happened — `JOURNEY-06` in the canon — and
`actor_kinds: ["SYSTEM"]` was applied to all eight `record.*` rows in the one-pass
assignment `decisions/0038` records under its own Defaults taken. A node whose model
operators cannot read history is less AI-native, not more. Either answer is one line, and
it is Bdo's.

## What the canon reads on the three journeys Bdo asked for

`OBSERVED`, from `python scripts/sov_canon.py trace`.

**`JOURNEY-01` Bring my model and put it to work here** — 2 reachable, 2 declared, 2 missing.

| Crossing | State |
| --- | --- |
| `asset.propose-description` | reachable, `IN_PROCESS` |
| `console.grant` | reachable, `IN_PROCESS` |
| `projection.package-context` | declared, not reachable |
| `projection.read-context-package` | declared, not reachable |
| `model.invoke` | **MISSING** — `SPEC.md` declares the `invoke_model` transition and no manifest declares an operation realizing it; `adapters/ollama/` executes one outside the map entirely |
| `model.declare-binding` | **MISSING** — a Model Binding is a file under `adapters/ollama/bindings/`, so bringing a model is a filesystem act rather than a governed transition |

**`JOURNEY-02` Find out what I can do here** — 1 reachable, 4 declared, 0 missing.
`console.discover-operations` runs in process. `gateway.list-endpoints`,
`gateway.resolve-capability`, `registry.resolve` and `registry.read-index` are declared
and unreachable. Nothing is missing, which is the useful reading: **the answer already
exists as a checked-in projection and nothing serves it.** A model reads the file; it
cannot ask.

**`JOURNEY-11` Review a pinned version and land a decision** — 1 reachable, 8 declared,
0 missing. `asset.read-version` runs; all eight `proofing.*` crossings are declared and
unbuilt. Nothing is missing here either: the enterprise workflow needs no new operation
invented, only the eight already contracted.

## Against the acceptance test

`DERIVED`. Bdo's test had two directions. Where each stands after this work:

**Promise → work.** Answerable in principle, not yet in practice.
`sov_canon.py promises` gives a per-promise reading of reachable, declared and missing
crossings; `PROMISE-12` is the only promise every crossing of which is reachable. What it
cannot give is *what was spent*, because no work item names a capability
(`contracts/issue-metadata.schema.json`, edge E19) and no receipt records consumption
(`contracts/receipt.schema.json`, edge E33).

**Expenditure → promise.** Not answerable yet. The run-to-capability join now works for
receipt event names, which is the half D1 closed. The half still missing is that nothing
records what a run consumed: `asset.request-derivative` is the only
`RESOURCE_CONSUMPTION` operation with a live run lifecycle, and after D2 it can report
wall clock and nothing else.

The two contracts that close both directions are the ones Bdo ruled on in Q2, Q5 and Q6
and that were not in the proceed-now list: an optional `capability` array on the ticket
schema, and an optional multidimensional `consumed` array on the receipt schema. Both are
now unblocked by those rulings, and neither is canon work.
