# Slice draft · `read_source` and `Recording`

Status: `PROPOSED · WORKER DRAFT · NOT REGISTERED · NOT OWNER-RATIFIED`

A scope proposal for one vertical slice, drafted for Bdo. It is not an issue: no GitHub
issue is created, no number is claimed, and nothing here changes `STATUS.yaml` or the epic
tree. `AGENTS.md` Authority — a worker drafts, it does not register or ratify.

## Owned scope

Owned: the operation definition, the minimum cut through existing tickets, the contracts and
fixtures the operation requires, its effect class and refusal paths, and a metadata block
ready to author. Not owned: the issue number, the decision to register it, any answer to O4,
and any claim that the slice is admitted work.

## The operation

Implement `read_source` and the `Recording` object from `SPEC.md` in the Asset Service, so
that derived artifacts carry the provenance that makes staleness a query instead of a script.

One sentence of behavior: *reading a source produces an addressed `Recording` that names its
source digest, reader, reader version, configuration, fidelity, and omissions — and a
recording whose stored `source_digest` no longer matches its source is detectably stale.*

## Why this slice

Four reasons, in the order they matter.

**It is already specified and has zero code.** `SPEC.md` fixes every `Recording` field and
gives `read_source` its preconditions, commit, and refusals. The `ENGINEERING.md` Realization
map records `read_source` as one of four transitions with no implementation, and no
`recordings` table exists. This is not new design; it is the missing half of a settled design.

**The mechanism is already proven by hand.** `diagrams/` writes a `Recording` as a prose
provenance header, and running the digest comparison manually on 2026-08-23 correctly flagged
four of six views as stale against changed `CLASSIFICATION.md` and `STATUS.yaml` bytes. The
convention works. It is not in the database.

**It is vertical, not another layer.** The slice crosses source custody, reader declaration,
recording emission, relationship, and projection. It ends at the CLI, which
`ENGINEERING.md` names as the Phase-I local surface — so it terminates at something a person
can run, which layer work does not.

**It closes a settled source claim.** `sources_survive_reading` is settled; `PRD.md` PROD-I-2
requires that every recording resolve its exact source, reader version, configuration,
fidelity, and recoverable omissions. Today `report_derivative` hardcodes `"lossy": true` on
every derivative, so fidelity is asserted rather than measured.

## Minimum cut through existing tickets

The slice does not need a new ticket kind and does not cross villages. Every ticket it touches
is `village: ground-and-evidence`, `horizon: NOW`.

| Ticket | What the slice needs from it | What the slice leaves alone |
| --- | --- | --- |
| `#6` Shared Kernel | `read_source` as a legal transition with its two declared refusals | the other thirteen transitions |
| `#7` System of Record | a `recordings` relation in the append-preserving spine | the full Event Envelope journal |
| `#8` Asset Service | reader declaration and recording emission on the existing derivation path | asset identity, discovery, use records |
| `#25` Shared contracts | one `recording.schema.json` at the boundary | the remaining boundary records |

`#9` Observation and Attestation is deliberately excluded. Whether a stale recording is
*wrong* is applicability, not reproduction, and that is open decision O4.

## Contract and fixtures

Per `AGENTS.md` implementation order, the contract and its conformance pair precede the code.

`contracts/recording.schema.json`, governing the `SPEC.md` field list, with `fidelity` as an
enum of `EXACT | LOSSY` and a conditional requiring non-empty `omissions` when `LOSSY`.

Positive and defeating fixtures, both required:

| Case | Asserts |
| --- | --- |
| positive · exact read | recording resolves source, reader, version, configuration; `fidelity: EXACT`; `omissions: []` |
| defeating · lossy without omissions | a `LOSSY` recording declaring no omissions is refused |
| positive · stale detection | a recording whose `source_digest` differs from its source's current digest reports stale |
| defeating · source mutated by reading | source bytes differ before and after a read — refuse `SOURCE_CHANGED` |
| defeating · reader undeclared | a read with no `reader_id`/`reader_version` refuses `READER_UNDECLARED` |

The two refusal codes are already named in the `SPEC.md` transition contract. The oracle must
not import the participant.

## Effect class and boundaries

`RECORD_LOCAL`. No network, no provider, no external effect. Reading verifies a digest and
emits a record; it never mutates source bytes, which is `CONTRACT.md` C2 and the settled claim
`sources_survive_reading`.

Refusal paths: `SOURCE_CHANGED`, `READER_UNDECLARED`, and `DIGEST_MISMATCH` on capture. Every
refusal returns a receipt, per `PRD.md` PROD-I-4.

## What this slice does not deliver

Named so the scope cannot quietly widen:

- it does not decide whether a stale recording is wrong — that is O4;
- it does not build the Event Envelope journal, only the recording relation;
- it does not compose omissions across multiple hops, so accumulated fidelity loss over a
  derivation chain remains uncomputable;
- it does not add a second binding, so `PRD.md` PROD-I-3 parity is untouched;
- it does not close the oracle's participant binding, which remains
  `EXECUTABLE_ORACLE_CONTROLS_PARTICIPANT_BINDING_OPEN`.

## Metadata block, ready to author

The number is left unclaimed. `evidence_pointer` and `last_observed_at` are filled at
authoring time; the current tree carries 33 contract defects from blocks authored without
them.

```json
{
  "issue_schema": "soveraeign-ticket/v1",
  "tags": ["kind:bit", "village:ground-and-evidence", "horizon:now",
           "effect:record-local", "standing:proposed"],
  "kind": "bit",
  "bit_id": "BIT-GROUND-RECORDING",
  "village": "ground-and-evidence",
  "village_issue": "#4",
  "parent": "#1",
  "standing": "PROPOSED",
  "horizon": "NOW",
  "authority": "Bdo/phase-gate",
  "effect_class": "RECORD_LOCAL",
  "evidence_pointer": "PENDING",
  "last_observed_at": null,
  "walker_receipt": "PENDING",
  "demotion_pointer": "#demotion-pointer",
  "dependency_channels": ["record", "asset", "observation"],
  "requires": ["#6", "#7"]
}
```

Labels the metadata projects, which `sov_epic validate` checks: `horizon: now`,
`standing: proposed`, `type: bit`, `village: ground`.

## Open for Bdo

1. Register this as a new `bit`, or narrow `#7` to carry it? A new bit is discoverable in
   `sov_epic next`; a narrowing avoids a fifth name for work `#7` already implies.
2. Does the slice ship reproduction-only staleness now, with applicability explicitly
   deferred to O4 — or wait for O4 so the alarm means one thing from its first run?
