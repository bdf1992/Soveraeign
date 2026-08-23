# Engineering Baseline and Composable Primitives

Status: `OWNER-DIRECTED FRAMEWORK · TECHNICAL BASELINE PROPOSED`

This document defines the minimum Phase-I construction kit. It does not replace
the stack-neutral logical specification. It chooses a small reference stack and
names the primitives from which services may compose larger governed workflows.

## Two Systems of Record

The design System of Record is the governing repository set named in
`AGENTS.md`. Each document owns a distinct policy surface; no document becomes
authoritative by repeating another one.

The operational System of Record is the append-preserving journal of addressed
inputs, decisions, standing transitions, operations, observations, receipts,
and counter-records. It records what happened and under what authority. It does
not collapse recorded, admitted, ratified, effective, disputed, failed, or
countered claims into one undifferentiated “truth.”

SQLite is the Phase-I storage mechanism for that record. Search tables, graph
stores, indexes, caches, and UI views are projections rebuilt from the record.

## Selection rule

A technology belongs in the baseline only when it is required to prove a
current operation locally, keeps authority and history inspectable, survives
loss of optional providers, and can be replaced behind an existing contract.

## Minimal reference stack

| Concern | Phase-I choice | Boundary |
| --- | --- | --- |
| Language | Python 3.11+ | Reference implementation only; logical contracts remain language-neutral |
| Runtime dependencies | Python standard library first | New dependencies require a decision and named port or adapter |
| Operational record | Append-preserving events and receipts in transactional SQLite | SQLite does not define service or kernel semantics |
| Immutable payload custody | Filesystem content-addressed store using SHA-256 | Payload address differs from asset and source identity |
| Machine contracts | JSON Schema Draft 2020-12 | Schema validity is not semantic fitness |
| Human control files | Markdown and small YAML fixtures | YAML is not a parallel runtime contract |
| Local surface | Python API and CLI | Human and model bindings use the same kernel operations |
| Tests and lint | `unittest` and dependency-free repository scripts | Local, deterministic, network-free, under three seconds |
| Search and graph | Rebuildable local projections | External systems integrate through adapters later |
| Model execution | Declared Model Binding plus Model Adapter | BYOM; no provider-derived authority or silent fallback |

Not yet selected: HTTP or frontend framework, background queue, container
runtime, orchestrator, distributed database, event broker, vector store, graph
database, identity provider, cloud, or model SDK. Their absence is deliberate
until a conformance case makes a boundary concrete.

## Kernel primitives

These are semantic objects and transitions shared by services, not separate
microservices.

| Primitive | Minimum purpose | Composition rule |
| --- | --- | --- |
| Addressed source | Bind bytes to origin, address, digest, size, and custodian | Reading verifies the digest and never mutates source |
| Event envelope | Record actor, operation, reason, time, inputs, outputs, authority, effects, and outcome | Every consequential decision emits one; no silent state change |
| Recording or proposal | Preserve an attributed result without granting truth or authority | Begins recorded; gates add standing without overwriting history |
| Authority grant | Scope actor, capability, budget, validity, and revocation | Checked at the operation; credentials are not grants |
| Operation plan | Declare inputs, configuration, preconditions, observations, limits, and effects | Required before consequential execution |
| Run and lease | Attribute an attempt and fence delegated execution | Worker reports; stale or expired lease cannot settle |
| Observation | Test expected predicates independently against durable results | Executor output alone cannot establish success |
| Receipt | Record one terminal outcome for every crossing or transition | Failure, refusal, unresolved work, and counteraction are first-class |
| Counter-record | Stop prior state conditioning current operation without erasure | State what was not undone or refunded |
| Binding | Present one declared interface to a human or model | Different surfaces resolve to the same operation and receipt |
| Adapter | Translate a named external runtime or enterprise system | Translation stops at boundary; no authoritative writes |
| Projection | Build a disposable read model from events and records | Rebuildable and never authoritative by convenience |

Field names and transition predicates remain normative in `SPEC.md` and
`contracts/`.

## Composing larger motion

A service operation composes primitives instead of creating a custom authority
path:

```text
address inputs -> declare plan -> check authority -> append attempt
-> execute or refuse -> observe -> settle with receipt -> counter when needed
```

Asset ingestion, derivative generation, proofing rounds, model invocations, and
later integrations may arrange these primitives differently, but cannot remove
their distinctions.

A larger workflow is valid only when each step names its owner and exact inputs;
inter-service crossings use contracts and receipts; retries retain one
attributable operation identity; idempotency is explicit; judgement remains a
visible pending right; workers are replaceable; provider changes do not change
authority; partial failure is reconstructable; and compensation does not
pretend consumed resources or external effects vanished.

## Realization map

`SPEC.md` fixes fourteen transitions without choosing a mechanism. This section
records which mechanism currently realizes each one, so that "the stack" is a
checkable claim rather than a list of technologies. It adds no normative rule:
where this table and `SPEC.md` disagree, `SPEC.md` wins and this table is stale.

Record column values are SQLite tables in the Asset Service store, except the
content-addressed payload path, which is filesystem.

| `SPEC.md` transition | Realized by | Record | Kernel contract | Control fixture | State |
| --- | --- | --- | --- | --- | --- |
| `capture_source` | `AssetService.ingest` | `sources`, `versions`, CAS `blobs/sha256/` | — | `CONF-I2` | partial |
| `read_source` | none | — | — | `CONF-I2` | **absent** — no `Reader` object exists |
| `submit_proposal` | `AssetService.propose` | `proposals` | — | `CONF-I1` | partial |
| `admit` | none | — | — | `CONF-I1` | **absent** — declared gap |
| `ratify` | `AssetService.ratify` | `proposals`, `receipts` | — | `CONF-I5`, `CONF-I5-GRANT` | partial |
| `attest` | none | — | — | `CONF-I8` | **absent** — declared gap |
| `make_effective` | none; `ratify` writes `EFFECTIVE` directly | `relationships` | — | — | **collapsed** — declared gap |
| `begin_run` | `request_derivative`, `claim` | `runs` | `operation-plan` | — | partial |
| `report_run` | `report_derivative` | `runs` | — | — | partial |
| `observe_run` | `observe` | `observations` | `participant-observation` | — | partial — observer independence gap |
| `settle_run` | folded into `observe` and receipt emission | `receipts` | `receipt` | — | partial |
| `retract` | `AssetService.retract` | `retractions`, `receipts` | — | `CONF-I4` | partial |
| `cross` | `federation_cross` | `receipts` | `event-envelope` | `CONF-I3` | refuses `UNCONFIGURED` with a receipt |
| `invoke_model` | none | — | — | `CONF-I9` | **absent** — declared gap |

Four transitions have no implementation, one is collapsed, eight are partial,
and one refuses correctly. Every one of those divergences is already recorded in
`services/asset/KNOWN-GAPS.md` against its governing clause; none is a newly
discovered defect. The two projections, `search_projection` and
`graph_projection`, are rebuilt by `rebuild_projections` and hold no
authoritative state, per the `SPEC.md` Projection rule.

`federation_cross` is worth naming as correct rather than missing. It returns a
`REFUSED` receipt carrying reason `UNCONFIGURED` instead of attempting the
crossing, which is exactly what the `SPEC.md` local-operation rule requires of
an optional integration.

## Crossing realization

`diagrams/crossing-typology.md` fixes four crossing classes and the four
obligations every class owes identically. `diagrams/crossing-topology.md`
places them. This table binds those classes to the current mechanism.

| Class | Passage | Mechanism today | State |
| --- | --- | --- | --- |
| `C1` Operator | human ↔ model through one record | Python API and CLI only | one binding, not two |
| `C2` Service | sibling ↔ sibling in one node | none; Proofing and Console are charters | no live reader or writer |
| `C3` Boundary | surface ↔ kernel, node ↔ provider | `bindings/`, `adapters/` hold no executing adapter | egress never exercised |
| `C4` Federation | node ↔ node | `federation_cross` refusal stub | refuses visibly, as required |

`C3` is the only class whose far side is a third party, so it is the only class
carrying a `data_boundary` — `LOCAL_ONLY`, `REDACTED_REMOTE`, or
`REMOTE_ALLOWED`. Two obligations land there and nowhere else: provider loss
must leave authoritative custody and non-model local operation intact, and any
fallback must be a separately attributed invocation with its own receipt.
Neither obligation has been exercised, because no adapter executes.

## Service construction rule

Create a `<Domain> Service` only when a domain owns a distinct lifecycle,
contract, and authority boundary. Otherwise add a component, binding, adapter,
worker, or projection inside an existing service.

Within a service, dependencies point from binding or adapter to an application
operation, then to the domain lifecycle, kernel contracts, and storage or
projection component. Domain code never imports provider SDKs, CLI parsers, web
framework types, or projection-specific query types.

## Context and module budget

Production modules stay below 300 lines so one responsibility can be understood
without loading the service wholesale. A file approaching the limit is split by
owned lifecycle or boundary. Generated files, schemas, fixtures, and tests may
exceed it only with an explicit reason.

The current Asset Service `core.py` exceeds this limit and is named debt. Do not
add behavior to it before splitting storage, receipts/authority, and asset
lifecycle responsibilities without changing semantics.

Agent tasks carry only the governing excerpts, relevant contract, fixture,
service files, observed check summary, and current objective. A distinct
objective starts a fresh task or bounded handoff.

## Growth triggers

| Trigger | Smallest allowed addition |
| --- | --- |
| A second process must invoke an accepted operation | Transport port plus one local adapter |
| Durable work must outlive a process | Lease-backed queue component using the Run contract |
| A projection fails a measured local query | External search or graph adapter with rebuild proof |
| Two nodes must exchange governed records | Federation crossing, identity, policy, and receipt contracts |
| A model provider is required | Model Adapter contained by a Model Binding and data boundary |
| Concurrent writes defeat a current case | Fencing or compare-and-set at the storage boundary |

Do not add generalized infrastructure for imagined scale. Add the smallest
replaceable boundary resolving an observed failure while preserving the kernel.

## Acceptance

The framework is `BUILT` when the root instruction surfaces agree, the
dependency-free lint and verification loop enforce their invariants in under
three seconds, and existing conformance and participant tests still run. It is
`RATIFIED` only when Bdo accepts the exact Phase-I technology choices and
composition rules.
