# Record Service Journeys

Status: `BUILT` (self-report, drafting session, 2026-08-27 — not `WITNESSED`,
not `RATIFIED`)

Per `decisions/0067`, this document has no root-level analog. It enumerates
the abstract journeys a caller takes through the Record Service and states
plainly, per journey, whether it completes or dead-ends, citing the evidence
that makes it so. Naming a gap here does not assign it; an open question
stays open and routes to a decision record the ordinary way
(`decisions/0067`, "What this is not").

## J-RECORD-1 · Append an event and get back durable proof it happened

Discover (`operations` on the CLI answers what may be done out of
`service.json` rather than out of the CLI itself, `CHARTER.md` "Reaching it")
→ authority-check → invoke `append-entry` → receipt → provenance via the
digest chain.

**COMPLETES**, for the one live caller. `services/console/src/soveraeign_console_service/core.py`
imports `RecordService` directly and `append.py`'s `emit` function calls
through it; `core.py` line 270 reads the journal back with
`self.record.reconstruct()`. `tests/test_journal.py` (eight tests) proves the
mechanics from inside; `scripts/witness_record.py` proves them from outside —
twenty-one observations hold across "commit, interrupt, restart, reconstruct,
retract, drop every projection, rebuild them, compare the resulting record
addresses and terminal receipts" (`CHARTER.md` "Proving operation").

One precise note on the authority-check step: `service.json`'s `append-entry`
preconditions are `declared_kind`, `declared_subject`, `declared_actor`,
`current_head` — no authority-grant precondition is declared for this
operation itself. The live caller (Console) performs its own check before
calling in (`authority.require(...)` at `core.py` line 120). `CHARTER.md`
states this is deliberate, not an oversight: "It does not decide legality...
A receipt here is evidence of an attempt, never a grant of authority." The
journey completes; the authority check lives one edge earlier than the
journal itself.

## J-RECORD-2 · Gate and retract a wrong entry

Invoke `counter-entry` against an existing entry → a counter-record is
appended → the original entry, its payload, and its position in the chain
are unchanged.

**COMPLETES**. `service.json` declares this operation with
`kernel_transition: retract`, requirement `PROD-I-4`, and refuses
`entry-mutation`/`history-erasure-on-retraction` by name. `scripts/witness_record.py`'s
twenty-one-step walk exercises retract as one of its stages; `tests/test_journal.py`
covers it as one of the "five declared defeating cases" `CHARTER.md` names.

## J-RECORD-3 · An outside witness reconstructs and verifies the whole journal

Invoke `reconstruct-journal` and `read-entry` from a process that did not
write the journal, recomputing every digest against the stated chain rule
rather than trusting `core.py`'s own report of itself.

**COMPLETES**. `scripts/witness_record.py` is exactly this: it "reaches the
service only as a subprocess through the CLI, recomputes every digest from
the chain rule stated above, and stages the interrupt against the SQLite
file from outside" (`CHARTER.md` "Proving operation"). `scripts/tests/test_witness_record.py`
proves the walk can in fact fail — a rewritten payload, actor, or removed
entry all stop verifying, so the completion is not vacuous.

## J-RECORD-4 · Export the journal to a portable document and restore it elsewhere

Invoke `export-journal` (refuses an unverifiable journal) → carry the
document → `verify-export` against a head digest held outside it →
`restore-journal` into an empty store only.

**COMPLETES** for the mechanics `tests/test_custody.py` and `custody.py`
implement: export, verify, and restore all exist, are wired through
`service.json`, and refuse the declared defeating cases
(`export-of-an-unverifiable-journal`, `restore-into-a-non-empty-journal`,
`truncation-detected-without-an-external-head`). But the completion carries a
stated, accepted boundary rather than a silent one: `CHARTER.md` "Export and
restore" is explicit that an export "cannot detect truncation" from inside
itself — "Rewriting the declared head is as easy as dropping the entries" —
and that only a head digest "held *outside* the document" catches it. See
open question Q1 below: nothing read in this pass names who or what holds
that external head digest.

## J-RECORD-5 · A ratified claim receives a runtime attestation, journaled as such

Invoke the kernel's `attest` transition against an already-ratified claim →
the outcome (`REPRODUCED`, `DISSENTED`, or `UNATTESTABLE`) is appended to
this journal as its own kind of record, distinct from an ordinary event.

**DEAD-ENDS**. `contracts/kernel-transitions.json` declares `attest` as a
kernel transition (effect class `RESOURCE_CONSUMPTION`). `service.json`'s
`owns` list — `journal-entry, terminal-receipt, counter-record, digest-chain,
subject-projection, journal-export` — has no `attestation` subject, and none
of its eleven operations cites `kernel_transition: attest` (only
`counter-entry` cites `retract`). `STATUS.yaml` ruling O4 describes an
`Attestation` as its own immutable evidence object, distinct from an ordinary
journal entry — exactly the kind of object this service does not yet own.
`contracts/domain-owners.json`'s Record entry (`owner-record@1`,
standing `PROPOSED`) names this precisely as its mandate: "Close the gap
between the built journal and PROD-I-8." Serves `PROD-I-8`. `SRD.md`
`SVC-RECORD-8` carries this as an `OPEN` requirement rather than a `BUILT`
one.

## J-RECORD-6 · A sibling service's own operational history reaches this journal

A service other than Console — most concretely the Asset Service, a
declared port — appends its own consequential events through Record instead
of, or in addition to, its own local tables.

**DEAD-ENDS**, for the Asset Service specifically. `service.json` `ports`
names `asset-service` as a declared caller. A search of
`services/asset/src/` for any import of `soveraeign_record_service` returns
nothing (checked directly; an earlier broad text match on the string
`record` in `services/asset/src/soveraeign_asset_service/routes.py` was a
false positive — it matches `UnknownRecord`, the Asset Service's own local
exception, not this service). `services/asset/KNOWN-GAPS.md`'s "Operational
journal" row states the same thing from Asset's side: "Mutable lifecycle
tables and partial receipts do not yet implement the complete
append-preserving Event Envelope," citing `C15; SPEC EventEnvelope`. `CLAUDE.md`'s
known-gaps section states this cross-service gap plainly: "The Record
Service owns an append-preserving journal, but it is not the kernel's: the
Asset Service still keeps its own SQLite tables," citing
`(PROD-I-8, services/asset/KNOWN-GAPS.md)`.

Worth recording as observed rather than silently reconciled: that `CLAUDE.md`
citation names `PROD-I-8`, while the specific `services/asset/KNOWN-GAPS.md`
row describing this exact gap ("Operational journal") itself cites
`C15; SPEC EventEnvelope`, not `PROD-I-8` — the two rows in that same file
that do cite `PROD-I-8` are "Effectiveness" and "Attestation," which are
about the joint-sign gap J-RECORD-5 already covers, not about Asset's own
event storage. This may be a loose parenthetical rather than a real
conflict, but it was not reconciled in this pass and is stated rather than
silently resolved.

## J-RECORD-7 · A governing document is offered to the journal by mistake

A caller declares `subject` as the name of one of the design System of
Record's own documents — the confusion the charter names explicitly.

**COMPLETES**, as a refusal. `core.py`'s `DESIGN_SYSTEM_OF_RECORD` frozenset
names fifteen governing filenames; an append against one of them raises
`DesignRecordRefused`, surfaced as `DESIGN_RECORD_REFUSED` and mapped to the
kernel code `ADMISSION_REFUSED`. `CHARTER.md`: "This service refuses to
journal a source whose name is one of the governing documents, so the
confusion fails loudly rather than accumulating." A refusal is a completed
outcome, not a dead end (`GROUND-008`).

## Open custody and ownership questions

Each of these is a question this service's own boundary cannot answer. It is
named here, not assigned, and not silently resolved by inventing an owner.

**Q1 — Who custodies the external head digest an export needs to detect
truncation?** `CHARTER.md` states plainly that only a digest held outside the
exported document can catch a dropped tail, and gives the practical
consequence as advice — "write the head digest down next to the recovery
secrets" — not as a built or assigned responsibility. Nothing read in this
pass (`CHARTER.md`, `service.json`, `core.py`, `custody.py`'s existence
without a full read of its body) names a role, seat, or process that
actually holds that digest. Silent in the charter; stated here as open.

**Q2 — Does this service ever refuse or redact a secret-shaped payload?**
The only content-based refusal `core.py` implements is
`DESIGN_RECORD_REFUSED`, and it keys on the declared `subject` string
matching one of fifteen governing-document filenames — it is not a check
against payload content. No refusal in `service.json`'s `refusals` or
`forbids` lists addresses a credential, token, or secret appearing inside an
appended payload. `AGENTS.md` "Secrets and local boundaries" states the
repository-wide rule — "Never print secrets or raw credentials in logs,
receipts, exceptions, prompts, fixtures, or test snapshots. Record only an
opaque credential reference" — but nothing read in this pass makes that rule
an enforced precondition of `append-entry` itself. If a caller appends a live
credential as an event payload, this service's charter and contract are
silent on whether that commits. Named as open because the charter is silent,
not because a defect was found.

**Q3 — Who owns building the `attest` leg, and does Record become the
attestor or only the journal of an attestation computed elsewhere?**
`contracts/domain-owners.json`'s mandate for `owner-record@1` says to close
the gap between the built journal and `PROD-I-8`, and lists `PROD-I-2` and
`PROD-I-4` as the entry's requirements — not `PROD-I-8` itself, even though
the mandate text names it. `SPEC.md`'s `attest` transition
(`VALIDATOR_UNDECLARED` refusal, `RESOURCE_CONSUMPTION` effect class) reads
as a computation a validator performs, with a receipt somewhere durable
after. Whether "somewhere durable" means Record grows an `attestation`
subject and an `append-attestation` operation, or whether attestation is
computed and owned by another service and only its outcome is journaled here
as an ordinary entry, is not settled by anything read in this pass.

**Q4 — Who is responsible for wiring the Asset Service's own event storage
through Record, and on which side?** `service.json` declares `asset-service`
as a port on Record's side; nothing on Asset's side currently crosses.
Closing J-RECORD-6 could mean Record builds whatever surface Asset would
need, Asset switches its own writes to cross into Record as it stands today,
or a third document assigns the sequencing. Not assigned in
`services/asset/KNOWN-GAPS.md`, `contracts/domain-owners.json`, or
`CHARTER.md`.

## README status, checked directly

`contracts/domain-owners.json`'s note on the Record entry, current as of
when that table was written, reads: "Has src and tests and no README; the
only built service with no owner before this table." A direct listing of
`services/record/` in this pass (`CHARTER.md`, `contracts/`, `observations/`,
`src/`, `tests/`) shows no `README.md` file. That gap is still current, not
stale, as of this draft.
