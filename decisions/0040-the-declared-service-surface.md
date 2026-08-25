# 0040 · The declared service surface: one manifest per service, one door for the node

Status: `PROPOSED · OWNER ACCEPTANCE OVER EVIDENCE`

Drafted at Bdo's direction (2026-08-23 conversation). Bdo asked whether each service and the
system should have a specification, observed that the declared surface described what had code
rather than what had plans and requirements, and named a missing interface or gateway service.

Drafted under `decisions/0023-acceptance-not-approval.md` and the lowest-tier rule of
`decisions/0033-close-the-founding-docket.md`, Ruling 1.

## Decision

### 1. The service manifest is the per-service specification. There is no per-service SPEC.md

`SPEC.md` owns the kernel: fourteen transitions, each with preconditions, what a commit
produces, the refusals it may return, and its effect class. `contracts/kernel-transitions.json`
is that table in machine form. Nothing was missing at that level.

What was missing sat one layer down. Each service declared `operations` as a list of bare
strings. The refusal codes those services actually enforce — `SOURCE_CHANGED`,
`DIGEST_MISMATCH`, `PAYLOAD_ABSENT`, `GRANT_NOT_COVERED`, `SESSION_NOT_LIVE` — existed only in
Python. Nothing outside the implementation declared them, so the conformance oracle could not
test a refusal it was never told to expect, and a second implementation had nothing to build
against.

A second prose document per service was the wrong fix: prose cannot be checked, and the shape
already existed in machine form. `contracts/service-manifest.schema.json` now makes each
operation an object carrying the record it acts on, the CRUD verb it realizes, its logical
endpoint, its preconditions, what a commit produces, and every refusal it may return.
`CHARTER.md` keeps its job — why the service exists and where its boundary sits.

### 2. A logical endpoint is `sov://<service>/<operation>` and names no transport

Every declared operation carries a transport-neutral address. The address says what is being
asked for; it never says how the bytes arrive. `contracts/capability-offices.json` binds
transports to it and records which are active, declared but not activated, or refused in this
phase. Neither table restates the other: the manifest owns what the operation is, the offices
table owns where it is answered and what authority it needs.

The address is not trusted as declared. `scripts/sov_service.py check` rebuilds it from the
manifest's own `service_id` and operation id and fails on any difference, so a rename cannot
leave a stale address pointing at nothing.

### 3. CRUD in an append-preserving system has five verbs, and neither of them is DELETE

Bdo asked for basic CRUD. In a system whose kernel forbids erasure, the four familiar verbs do
not map one to one:

| Verb | What it does |
| --- | --- |
| `CREATE` | appends a new record |
| `READ` | derives without writing; commits `DERIVED` and nothing else |
| `SUPERSEDE` | adds a later version and preserves the earlier one; never overwrites |
| `COUNTER` | adds a counter-record; commits `COUNTERED` and erases nothing |
| `REBUILD` | discards and recomputes a projection only |

`UPDATE` and `DELETE` are not admissible verbs. A manifest that names one fails the check
rather than describing erasure the kernel forbids.

### 4. A record written by one operation and readable by none is a defect

The first run of the check found this in every one of the five existing services: twenty-eight
records could be created and never retrieved. That hole also hides whether the write committed
at all.

Eleven read operations were added to close it — two built ones on the Asset Service and one on
the Record Service, where the code already existed; the rest at proposal standing. Where a
record is genuinely read through its parent, the read declares `also_reads` rather than leaving
the composition assumed.

### 5. The Gateway Service is chartered at proposal standing as the node's door

`services/gateway/` is the one place a request from outside a service becomes a call on that
service, and the one place a refusal to admit it is recorded. It resolves a logical endpoint to
the owning service, checks the grant, routes, and returns the owning service's receipt
unchanged.

It settles nothing, witnesses nothing it routed, holds no service state, issues no authority,
and opens no external transport in this phase. The `door` counter in
`contracts/capability-offices.json` held zero capabilities before this decision; it now holds
the Gateway's front-office operations.

### 6. A service refusal is a kernel refusal or maps to one

A code outside the kernel vocabulary is declared in the manifest's `local_refusals` alongside
the kernel refusal it realizes. A local code with no mapping, a mapping to a code the kernel
does not declare, a local entry shadowing a kernel code, and vocabulary no operation returns
are each defects. This is the same correspondence `contracts/kernel-parity.json` already
declares for the Asset Service, made total across every service.

## Observed state at drafting

- Six services, 76 declared operations: asset 9, console 23, gateway 9, projection 16,
  proofing 11, record 8.
- Built operations: asset 9, record 8, console 12. Gateway, projection, and proofing declare
  none.
- `python scripts/verify.py` passes at 20 checks in 2.556 s against a 3 s budget.
- `python scripts/sov_service.py check` passes over all six manifests.
- `contracts/fixtures/service-manifest.fixtures.json` carries one admissible manifest and
  twenty-one defeats: five the schema rejects, sixteen it admits and the manifest check
  catches.
- The capability map is total over all 76 operations and not stale.

## Constraints

- No new transport is opened. HTTP remains refused for every capability while the phase stands;
  a local tool surface remains declared and not activated.
- No service implementation changed. This decision moves declarations, not behaviour.
- `contracts/capability-offices.json` keeps sole ownership of office, counter, required
  authority, effect class, and actor kinds. The manifest does not restate them.

## Consequences

- `built_operations` is retired. Per-operation `standing` replaces it, and
  `scripts/sovkernel/capability_map.py` reads standing from the operation rather than the
  service.
- The requirement id pattern widened to `^PROD-[IVX]+-[1-9][0-9]*$`. A later-phase id is well
  formed but absent from `PRD.md`, so the traceability check is falsifiable by fixture instead
  of unfalsifiable.
- The Console Service manifest now claims `authority-grant` among the records it owns, because
  `grant`, `revoke`, and `list-grants` are built there. That is a default, not a settled
  boundary; see below.
- Every operation that serves a PRD requirement now names it, so requirement coverage is
  readable from the manifests rather than inferred.

## Defaults taken

Reversible choices made to keep moving; Bdo may overturn any of them without defeating the
ruling.

- **The Console Service owns `authority-grant`.** It has the built grant operations, and the
  Gateway needs something to check against. A separate permits service may claim it instead.
- **`sov://` is the address scheme.** No registry, resolution protocol, or namespace authority
  is proposed; it is a local naming convention that reads as an address.
- **Newly declared reads are `PROPOSED` unless code already backs them.** Three are marked
  `BUILT` because the Asset and Record services already implement them.
- **The Gateway's receipt is its own owned record.** `contracts/receipt.schema.json` may absorb
  it instead.
- **`REBUILD` counts as neither a write nor a read for the read-back check.** A projection is
  rebuildable by definition, so it needs no separate reader.

## What would defeat this ruling

- A service whose operation genuinely acts on a record it does not own, with a declared
  crossing, that the subject check cannot express. That would defeat claim 1's boundary rule.
- A transport whose address cannot be derived from the logical endpoint — one that needs a
  path, a version, or a method the address has no room for. That would defeat claim 2.
- A required behaviour that is genuinely an in-place update with no earlier version worth
  keeping. That would defeat claim 3's verb set.
- A record that must be write-only for a stated reason — a secret, a sealed audit input — which
  claim 4 currently treats as a defect without exception.
- Evidence that routing through one door forces the Gateway to hold state or settle an
  operation, which its charter forbids.

## Judgement queue for Bdo

1. Does the Console Service own authority grants, or does a permits service? The Gateway
   depends on the answer and assumes the Console today.
2. Is `sov://` the address scheme you want operators and models to see, given `SOV.md` already
   names the operating profile?
3. Should the Gateway be built next, or does it wait behind the Record Service journal it
   depends on? Its charter names a two-case proving operation that needs neither.

## Residuals

- `bindings/mcp/gateway.py` already carries the name "gateway" for the tool-surface binding.
  Two layers now share the word. Recorded as a seam; not resolved here.
- No Gateway implementation, tests, or conformance fixtures exist. The charter and manifest are
  the whole of it.
- The 76 declared operations include 47 at proposal standing. The manifests now state that
  precisely, which makes the unbuilt surface look larger than it did when it was undeclared.
- `services/asset/KNOWN-GAPS.md`, `services/console/KNOWN-GAPS.md`, and the service charters
  were not rewritten against the new manifests.
- `OPEN-SEAMS.md` S14 records the asset CLI carrying `search` and `receipts` as undeclared
  operations. `read-asset` and `read-use-record` now declare that surface, so S14 is narrowed
  but not closed.
