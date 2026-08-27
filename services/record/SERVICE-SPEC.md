# Record Service Logical Specification

Status: `BUILT` (self-report, drafting session, 2026-08-27 — not `WITNESSED`,
not `RATIFIED`)

Service-scoped projection of `SPEC.md`, per `decisions/0067`. Named
`SERVICE-SPEC.md`, not `SPEC.md` — the root document owns that name. This file
does not re-derive kernel transitions or refusal codes; it cites
`contracts/kernel-transitions.json` and `services/record/contracts/service.json`
and states only what is local to this service.

## Owned domain records

`service.json` `owns`: `journal-entry`, `terminal-receipt`, `counter-record`,
`digest-chain`, `subject-projection`, `journal-export`.

- **journal-entry** — one immutable row. `core.py` `ENTRY_KINDS` fixes the
  kind vocabulary to `EVENT | RECEIPT | OBSERVATION | COUNTER`. Every row
  carries the digest of the row before it.
- **terminal-receipt** — the outcome of `append-receipt`, tied to an existing
  entry (`entry_exists` precondition).
- **counter-record** — the outcome of `counter-entry`; a new appended row that
  changes what an entry currently conditions without touching the entry
  itself. `SPEC.md` `Retraction`.
- **digest-chain** — the derived structure `reconstruct-journal` walks and
  verifies; not a stored object of its own, a property of the sequence of
  journal-entry rows.
- **subject-projection** — `subject_projection`, a rebuildable index dropped
  and rebuilt from the journal alone. `CHARTER.md` "Authoritative versus
  derived": "A projection can never be promoted to the record."
- **journal-export** — the portable document `export-journal` renders and
  `restore-journal` replays; carries every row's digest profile so a version-2
  export never re-runs under the ambiguous version-1 rule.

## Service-local states

- **Entry kind**: `EVENT | RECEIPT | OBSERVATION | COUNTER` (`core.py`
  `ENTRY_KINDS`). This is local vocabulary for what kind of row was appended,
  distinct from `SPEC.md`'s `EventEnvelope.event_phase`
  (`ATTEMPTED | REPORTED | OBSERVED | SETTLED | COUNTERED`), which this
  service does not itself track — it journals whatever phase or outcome its
  caller declares.
- **Digest profile**: `soveraeign-record-chain/v1` (legacy, key-sorted JSON
  payload text joined by `|` with `prev_digest`, `kind`, `subject`, `actor`;
  read-only for existing rows) or `soveraeign-record-chain/v2` (current;
  UTF-8 bytes of compact JSON over
  `[profile, prev_digest, kind, subject, actor, payload]`, keys sorted,
  non-finite numbers refused). `CHARTER.md` "The digest chain". Every new row
  is v2; opening a pre-profile database backfills `digest_profile = v1` onto
  existing rows only.
- **Projection state**: built or dropped. `drop-projections` and
  `rebuild-projections` are the only two transitions between them; no
  intermediate state is declared.
- **Export state**: an export either verifies against its own chain and,
  where supplied, an external head digest, or it does not. There is no
  partial-verify state — `verify-export` returns one outcome.

## Legal transitions

Cites `contracts/kernel-transitions.json` where a `kernel_transition` is
declared; otherwise the operation is local to this service and not yet a
named kernel transition.

| Operation | Kernel transition | Preconditions | Commit | Refusals |
| --- | --- | --- | --- | --- |
| `append-entry` | — (local) | `declared_kind`, `declared_subject`, `declared_actor`, `current_head` | `COMMITTED` | `STALE_STATE`, `MISSING_PRECONDITION`, `DESIGN_RECORD_REFUSED` |
| `append-receipt` | — (local) | `entry_exists`, `declared_outcome` | `COMMITTED` | `STALE_STATE`, `MISSING_PRECONDITION` |
| `counter-entry` | `retract` | `entry_exists`, `declared_reason`, `declared_actor` | `COUNTERED` | `STALE_STATE`, `MISSING_PRECONDITION` |
| `reconstruct-journal` | — (local) | `journal_readable` | `DERIVED` | `UNREADABLE`, `DIGEST_MISMATCH` |
| `read-projection` | — (local) | `projection_built` | `DERIVED` | `MISSING_PRECONDITION` |
| `drop-projections` | — (local) | `projection_store_writable` | `REBUILT` | `MISSING_PRECONDITION` |
| `rebuild-projections` | — (local) | `journal_readable` | `REBUILT` | `UNREADABLE`, `DIGEST_MISMATCH` |
| `read-entry` | — (local) | `entry_exists` | `DERIVED` | `MISSING_PRECONDITION` |
| `export-journal` | — (local) | `journal_verifies` | `DERIVED` | `EXPORT_REFUSED`, `DIGEST_MISMATCH` |
| `verify-export` | — (local) | `export_readable` | `DERIVED` | `RESTORE_REFUSED`, `DIGEST_MISMATCH`, `TRUNCATED_EXPORT` |
| `restore-journal` | — (local) | `export_verifies`, `store_empty` | `COMMITTED` | `RESTORE_REFUSED`, `DIGEST_MISMATCH`, `TRUNCATED_EXPORT` |

No operation in `service.json` declares `kernel_transition: attest`, and no
owned subject is named `attestation`. `contracts/kernel-transitions.json`
declares `attest` (effect class `RESOURCE_CONSUMPTION`) as a kernel
transition; this service has no leg of it. See `SRD.md` `SVC-RECORD-8` and
`JOURNEYS.md`.

## Refusal reason codes

Codes named directly in `service.json` operation `refusals`:
`STALE_STATE`, `MISSING_PRECONDITION`, `DESIGN_RECORD_REFUSED`, `UNREADABLE`,
`DIGEST_MISMATCH`, `EXPORT_REFUSED`, `RESTORE_REFUSED`, `TRUNCATED_EXPORT`.

`service.json` `local_refusals` maps four service-local codes onto the kernel
vocabulary `contracts/kernel-transitions.json` declares, so an outside caller
reading only the kernel table still resolves them:

| Local code | Resolves to |
| --- | --- |
| `DESIGN_RECORD_REFUSED` | `ADMISSION_REFUSED` |
| `EXPORT_REFUSED` | `MISSING_PRECONDITION` |
| `RESTORE_REFUSED` | `MISSING_PRECONDITION` |
| `TRUNCATED_EXPORT` | `DIGEST_MISMATCH` |

## Persistence and authority notes

- Persistence is local SQLite for the journal store and the derived
  projection store, matching `ENGINEERING.md`'s technical baseline; no remote
  database is used.
- `contracts/domain-owners.json` names `record:event` as the required
  authority for the Record domain-owner seat (`owner-record@1`). No other
  authority-scope document was read for this draft; a caller-side authority
  check for individual operations (e.g. whether `append-entry` itself
  enforces a grant, versus relying on its caller to have checked) was not
  verified against `core.py` in this pass and is not claimed here either way.
- No actor identity is verified or resolved. `actor` is carried as an opaque
  string (`CHARTER.md` "It does not carry identity"); this service performs
  no lookup against Identity (#11), which does not yet exist.
- `service.json` `forbids` is a declared negative list, not a runtime
  enforcement mechanism by itself: `entry-mutation`, `entry-deletion`,
  `projection-as-authority`, `digest-chain-rewrite`, `history-erasure`,
  `journal-row-update`, `journal-row-deletion`,
  `history-erasure-on-retraction`, `projection-as-authoritative-record`,
  `design-documents-as-event-storage`, `unverified-history-replay`,
  `export-of-an-unverifiable-journal`, `restore-into-a-non-empty-journal`,
  `truncation-detected-without-an-external-head`. Each corresponds to a
  refusal or an architectural absence described above or in `CHARTER.md`.
