# Registry Service Logical Specification

Status: `PROPOSED · SERVICE-SCOPED PROJECTION OF SPEC.md`

This document applies `decisions/0093-service-srd-spec-ground.md` to the
Registry: `SPEC.md`'s shape, re-scoped to what the Registry itself owns. It
does not re-derive the kernel transition contract, the receipt shape, or the
authority model — those stay owned by `SPEC.md`, `contracts/kernel-transitions.json`,
and `contracts/service-manifest.schema.json`. It states which of them the
Registry uses, and what its own records add.

## Owned domain records

Named in `services/registry/contracts/service.json`, `owns`, and described in
`CHARTER.md`, Owned domain records:

- `registry-entry` — one versioned entry for a named thing: kind, owning
  document address and digest, and the standing that document declares.
- `entry-relation` — a typed edge between two entries.
- `owner-record` — the participant accountable for a domain, its mandate,
  requirements, budget, deadline, and independent witness.
- `registry-index` — the rebuildable projection over every declared source.
  Never itself a source of truth: `CHARTER.md`, What it is not — "If the
  index and a source disagree, the source wins."
- `resolution` — the answer to one lookup: the entry, its relations, and the
  source that owns it.
- `drift-finding` — a recorded disagreement between the index and one of its
  declared sources.
- `registry-receipt` — the terminal receipt for any Registry operation,
  structured as `SPEC.md`'s `Receipt` object.

None of these records are new information-object kinds at kernel scope;
`registry-entry` and `resolution` are Registry-local specializations that
still resolve to `SPEC.md`'s `Source` and `Recording` shapes for the document
bytes they cite.

## Service-local states

`registry-entry` and `owner-record` carry the standing of the document that
owns them, not a Registry-invented standing ladder — `CHARTER.md` is explicit
that the Registry "resolves; it does not define." The Registry's own local
state is only:

```text
registry-index:  FRESH | STALE
resolution:      COMMITTED | REFUSED
drift-finding:   OPEN
```

`FRESH` means every digest in `source_digests` currently matches
`_read_digest(address)`; any mismatch is `STALE` for every name the index
would otherwise answer, not only the drifted one — `resolve` in
`src/soveraeign_registry_service/core.py` checks all declared sources before
answering any lookup.

## Legal transitions

The Registry crosses no transition `contracts/kernel-transitions.json` does
not already declare:

| Registry operation | Kernel transition | Preconditions (`contracts/service.json`) | Commit | Refusals |
| --- | --- | --- | --- | --- |
| `resolve` | none declared; a `READ` | `declared_name`, `index_fresh` | `DERIVED` | `NAME_UNKNOWN`, `INDEX_STALE` |
| `register-entry` | `capture_source` | `declared_kind`, `declared_name`, `owning_document_address`, `owning_document_digest`, `declared_actor` | `COMMITTED` | `INCOMPLETE_PROPOSAL`, `SOURCE_UNRESOLVED`, `NAME_COLLIDES` |
| `supersede-entry` | none declared; a `SUPERSEDE` | `entry_exists`, `owning_document_digest`, `declared_actor` | `COMMITTED` | `STALE_STATE`, `SOURCE_UNRESOLVED`, `INCOMPLETE_PROPOSAL` |
| `relate-entries` | none declared | `both_entries_exist`, `declared_relation_type`, `declared_actor` | `COMMITTED` | `RELATION_UNTYPED`, `NAME_UNKNOWN`, `INCOMPLETE_PROPOSAL` |
| `declare-owner` | none declared | `domain_entry_exists`, `declared_owner`, `declared_mandate`, `declared_budget`, `declared_deadline`, `declared_witness` | `RECORDED` | `INCOMPLETE_PROPOSAL`, `WITNESS_NOT_INDEPENDENT`, `NAME_UNKNOWN` |
| `supersede-owner` | none declared | `owner_record_exists`, `declared_budget`, `declared_deadline`, `declared_witness` | `RECORDED` | `STALE_STATE`, `WITNESS_NOT_INDEPENDENT`, `INCOMPLETE_PROPOSAL` |
| `retire-owner` | `retract` | `owner_record_exists`, `authority_grant_id`, `declared_reason` | `COUNTERED` | `AUTHORITY_REFUSED`, `STALE_STATE` |
| `rebuild-index` | none declared | `declared_sources`, `every_source_readable` | `REBUILT` | `UNREADABLE`, `SOURCE_UNRESOLVED` |
| `report-drift` | none declared | `index_exists`, `source_digest_compared` | `COMMITTED` | `MISSING_PRECONDITION`, `SOURCE_CHANGED` |
| `read-entry`, `read-owner`, `read-index`, `read-receipt` | none declared; all `READ` | subject exists | `DERIVED` | `NAME_UNKNOWN` or `MISSING_PRECONDITION` |

Only `resolve` is `BUILT`; every other row is `PROPOSED` and unreachable
through any route today (`contracts/service.json`, per-operation `standing`).
`retire-owner` is the one Registry operation typed to a kernel transition that
itself requires `JUDGEMENT` authority (`contracts/kernel-transitions.json`,
`retract`, `requires_authority_type`) — matching
`contracts/capability-offices.json` assigning `registry.retire-owner` the
`ratify:judgement` authority and `HUMAN`-only actor kinds.

## Refusal reason codes

`services/registry/contracts/service.json`, `local_refusals`, maps each
Registry-local refusal to the kernel-level reason `SPEC.md` and
`contracts/service-manifest.schema.json` already define:

```text
INDEX_STALE           → STALE_STATE
NAME_COLLIDES          → ADMISSION_REFUSED
NAME_UNKNOWN            → MISSING_PRECONDITION
RELATION_UNTYPED        → INCOMPLETE_PROPOSAL
SOURCE_UNRESOLVED       → READER_UNDECLARED
WITNESS_NOT_INDEPENDENT → OBSERVER_NOT_INDEPENDENT
```

No refusal code here is invented outside this mapping; a Registry-local code
with no kernel-level counterpart would be a defect against `contracts/service.json`.

## Persistence

`registry-index` persists nothing. `RegistryService.__init__` derives the
index in memory from the closure, manifests, policy, and declared source
digests passed to it on construction (`src/soveraeign_registry_service/core.py`,
`src/soveraeign_registry_service/index.py`); every `resolve` call re-reads
declared source bytes through `_source_drift` rather than trusting the
in-memory copy. This is the mechanism, not a separate claim, behind
`CHARTER.md`'s "It persists no index. Each lookup re-digests every source
that conditioned the index before answering."

`owner-record`, `registry-entry`, `entry-relation`, and `drift-finding` have
no persistence mechanism today — the operations that would create them
(`register-entry`, `declare-owner`, `relate-entries`, `report-drift`) are all
`PROPOSED`. `contracts/service.json`, `depends_on`, names
`record:append-preserving-journal` as where they would eventually commit,
consistent with `AGENTS.md`, State and execution: mutable projections must be
rebuildable, and the append-preserving journal is where a consequential
commit lives.

## Authority notes

`contracts/service.json`, `uses_kernel_contracts`, lists `standing`,
`typed-authority`, `operation`, `receipt`, and `retraction` — the Registry
introduces no authority primitive `SPEC.md` does not already define. Every
operation requires `read:registry` except `register-entry` and
`supersede-entry` (`register:entry`), `relate-entries` (`register:relation`),
`declare-owner` and `supersede-owner` (`declare:owner`), `retire-owner`
(`ratify:judgement`), and `rebuild-index` (`rebuild:projection`)
(`contracts/capability-offices.json`). `declare-owner`, `supersede-owner`, and
`retire-owner` further restrict `actor_kinds` to `HUMAN` alone; every other
operation admits both `HUMAN` and `MODEL`. `contracts/service.json`,
`depends_on`, also names `console:authority-grant` — the Registry checks
grants issued through Console's authority path rather than minting its own.

## Traceability

| Spec area | Requirement (`SRD.md`) | Root spec area |
| --- | --- | --- |
| Fresh-index resolution | SVC-REGISTRY-1, SVC-REGISTRY-4 | `SPEC.md` PROD-I-2 predicates |
| Entry admission and collision | SVC-REGISTRY-2, SVC-REGISTRY-3 | `SPEC.md` `capture_source`, `submit_proposal` |
| Owner declaration and independence | SVC-REGISTRY-5 | `SPEC.md` PROD-I-5 predicates, `ratify` |
| Owner retirement | SVC-REGISTRY-6 | `SPEC.md` `retract` |
| No standing by registration | SVC-REGISTRY-7 | `SPEC.md` Historical standing and current effectiveness |
