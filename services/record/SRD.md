# Record Service Requirements Document

Status: `BUILT` (self-report, drafting session, 2026-08-27 — not `WITNESSED`,
not `RATIFIED`)

This is a service-scoped projection of `PRD.md`, per `decisions/0067`. It
states what the Record Service owes the node that depends on it — the node
being the caller here, not a human end user. It does not compete with
`PRD.md`; where a requirement below serves a root Phase-I requirement, the
`PROD-I-<n>` it serves is named.

## Product outcome

Give every other participant in the node one place to deposit what actually
happened and under what authority, in a form that cannot be edited or deleted
after the fact and that an outside party can verify without trusting this
service's own code.

## Callers

`services/record/contracts/service.json` declares three ports: `asset-service`,
`conformance-oracle`, `console-projection`. Of those, only the Console Service
crosses into Record today — `services/console/src/soveraeign_console_service/core.py`
imports `RecordService` directly, appends through it, and reconstructs the
journal through it (`services/console/src/soveraeign_console_service/append.py`).
The conformance oracle reaches Record only as an external witness, through the
CLI subprocess boundary `scripts/witness_record.py` uses deliberately so the
walk does not import the code it is checking (`CHARTER.md`, "Reaching it").
The Asset Service is a declared port with no live crossing: nothing under
`services/asset/src/` imports `soveraeign_record_service` (verified by search;
see `JOURNEYS.md` for the standing this leaves).

Enumerated callers:

- **Console Service**, appending continuity events and receipts and reading
  them back, live today.
- **Conformance oracle**, witnessing the journal from outside the process
  boundary, live today.
- **Asset Service**, a declared but unrealized port — see `JOURNEYS.md`.
- **A human or model operator through the CLI**, `src/soveraeign_record_service/cli.py`,
  the declared invocation surface named in `CHARTER.md`.
- **The Gateway**, chartered to route requests but not built (`CLAUDE.md`
  repository snapshot: "Gateway... boundary only"); not a live caller.

## Requirements

### SVC-RECORD-1 · Append-preserving admission

Standing: `BUILT`.

Every declared entry (`EVENT`, `RECEIPT`, `OBSERVATION`, `COUNTER` —
`core.py` `ENTRY_KINDS`) is appended once and never updated or deleted after
commit. Serves `PROD-I-2`, `PROD-I-4`.

Defeating case: any code path issues `UPDATE` or `DELETE` against a journal
row. `CHARTER.md`: "No method updates or deletes a journal row. The only
`DELETE` in the service is against projections."

### SVC-RECORD-2 · Verifiable digest chain

Standing: `BUILT`.

Every entry carries the digest of the entry before it, hashed under a named,
stated profile (`soveraeign-record-chain/v1` or `/v2`,
`CHARTER.md` "The digest chain"). `reconstruct-journal` raises `BrokenChain`
at the first link that does not hold, and never tries an ambiguous algorithm
against a row that declares which profile produced it. Serves `PROD-I-2`.

Defeating case: a rewritten payload, actor, or removed entry still verifies,
or a v2 row passes under the v1 rule. `scripts/tests/test_witness_record.py`
is the existing defeating-case proof.

### SVC-RECORD-3 · Retraction preserves history

Standing: `BUILT`.

`counter-entry` appends a counter-record and leaves the original entry
exactly where it was, readable, with its payload intact. Serves `PROD-I-4`,
specializes `GROUND-009`.

Defeating case: a retraction removes or edits the original entry, or a
counter-record claims that consumed resources or an external effect came
back — refused by `service.json` `forbids: history-erasure-on-retraction`.

### SVC-RECORD-4 · Projection is derived, never authoritative

Standing: `BUILT`.

`subject_projection` can be dropped and rebuilt from the journal alone and is
identical each time. `append_from_projection` exists only to refuse.
Serves `PROD-I-2`.

Defeating case: `append_from_projection` succeeds instead of refusing, or a
rebuilt projection differs from a prior rebuild against unchanged journal
state. `CHARTER.md` "Authoritative versus derived" names this a declared
defeating case on issue #7 rather than a hypothetical.

### SVC-RECORD-5 · Design records refused as event storage

Standing: `BUILT`.

An append whose declared `subject` names one of the governing documents
(`DESIGN_SYSTEM_OF_RECORD` in `core.py`: `SYSTEM.md`, `CONTRACT.md`,
`CLASSIFICATION.md`, `PRD.md`, `SPEC.md`, `SDLC.md`, `AGENTS.md`,
`ENGINEERING.md`, `OPEN-SEAMS.md`, `NAMING.md`, `PUBLICATION.md`,
`ROADMAP.md`, `STATUS.yaml`, `AI-NATIVE.md`, `BYOM.md`) is refused
`DESIGN_RECORD_REFUSED`, mapped to `ADMISSION_REFUSED` at the kernel vocabulary
(`service.json` `local_refusals`). No `PROD-I-<n>` names this directly; it
enforces `ENGINEERING.md`'s two-Systems-of-Record split, restated in
`CHARTER.md` "Role in Soveraeign".

Defeating case: an append naming one of those exact filenames as `subject`
commits instead of refusing.

### SVC-RECORD-6 · Export and restore integrity

Standing: `BUILT`.

`export-journal` renders the whole journal as a portable, self-verifying
document and refuses an unverifiable journal rather than exporting it.
`restore-journal` refuses into a non-empty store. `verify-export` detects a
truncated export only when handed a head digest held outside the document.
Serves `PROD-I-2`.

Defeating case: export of a broken chain succeeds; restore commits into a
store that already holds entries; or a truncated export with no external head
verifies as complete. `CHARTER.md` "Export and restore" states the exact
limit: "It cannot detect truncation" from inside the document alone.

### SVC-RECORD-7 · Independently witnessable without importing the participant

Standing: `BUILT`.

The chain rule is stated in `CHARTER.md` precisely enough that
`scripts/witness_record.py` recomputes every digest and stages an interrupt
against the SQLite file from outside, reaching the service only through the
CLI subprocess boundary. Serves `PROD-I-7`, specializes `GROUND-010`.

Defeating case: a witness needs undocumented oral explanation, or must import
`core.py` to verify a claim the CLI already exposes.

### SVC-RECORD-8 · Attestation admission

Standing: `OPEN`.

The journal accepts and preserves an attestation outcome (`REPRODUCED`,
`DISSENTED`, `UNATTESTABLE` — `SPEC.md` `Attestation`) as an owned subject,
distinct from an ordinary event, receipt, or counter-record. Serves
`PROD-I-8`.

Currently true, not a hypothetical: `contracts/kernel-transitions.json`
declares `attest` as a kernel transition; `services/record/contracts/service.json`
`owns` lists `journal-entry, terminal-receipt, counter-record, digest-chain,
subject-projection, journal-export` — no `attestation`, and no operation in
that file cites `attest` as its `kernel_transition` (only `counter-entry`
cites `retract`). There is presently nowhere in this service to journal an
attestation outcome. `contracts/domain-owners.json`'s Record entry
(`owner-record@1`) names exactly this as its mandate: "Close the gap between
the built journal and PROD-I-8." Standing stays `OPEN` until an operation
exists and is `BUILT`.

Defeating case (today, trivially satisfied because nothing exists to defeat):
an attempted `attest` crossing into Record has no operation to resolve
against.

## Non-goals

- Deciding whether a transition is legal. `contracts/kernel-transitions.json`
  and `scripts/sovkernel/` own that; this service records that a transition
  was attempted and how it ended (`CHARTER.md` "What it does not do").
- Carrying actor identity. Every actor is a string until Identity (#11)
  exists (`CHARTER.md`).
- Guaranteeing media durability beyond detectable corruption — an
  infrastructure concern per `SPEC.md`'s fault model, realized by
  `custody.py` per `decisions/0049` rather than claimed by this service.
- Routing. The Gateway's job, not built, and not this service's to assume.
- Ranked search or graph traversal over journaled content — the Asset
  Projection Service's chartered concern, not Record's.
