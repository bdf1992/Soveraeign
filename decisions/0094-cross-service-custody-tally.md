# 0094 · Cross-service custody tally: what the seven journey maps found

Status: `PROPOSED · EVIDENCE TALLY, NOT A RULING`

## Why this exists

`decisions/0067` applied the SRD/Service-Spec/Service-Ground/Journeys pattern to
all seven chartered services (`identity`, `console`, `registry`, `host`,
`asset`, `gateway`, `record`). Each `JOURNEYS.md` independently names the open
custody/ownership questions that service's own boundary cannot answer — thirty
one of them across the seven files, none resolved in place, per `decisions/0067`'s
own rule against silently absorbing or silently answering a question that
isn't the naming service's to decide.

Read together rather than file by file, several of the thirty-one turn out to
be the same question asked from different services' angles. That's the signal
`CLASSIFICATION.md` names as the bar for minting a new service boundary:
*"Atlas, Gauge, definition, pedagogy, and observation are capabilities until
evidence gives one an independently useful service boundary."* This decision
tallies that evidence against two live candidates from the epic tree —
`Authority Service` (`#12`), `Capability Broker` (`#15`) — and against `Relay`
(`#17`) and `Storage`, which the same conversation raised.

## The tally

| # | Theme | Services | Citations |
| --- | --- | --- | --- |
| 1 | **Secret/credential custody** — who holds an actual secret value | Identity, Registry, Host, Asset, Gateway, Record (6/7) | Identity Q1 (recovery-secret paper, ID-11); Registry "no participant named accountable for secret or credential custody anywhere the Registry is chartered to read"; Host Q1 (future privilege-broker credential); Asset Q1 (source-access credential, silent); Gateway Q1 (future external-crossing credential); Record Q1+Q2 (export head digest; secret-shaped payload, silent) |
| 2 | **Authority-grant issuance and long-term ownership** — who mints/owns grants vs. who only checks them | Console, Asset, Gateway (3/7) | Console Q1 ("does the console own who may grant or revoke authority, or does it only enforce grants issued elsewhere?"); Asset Q3 (who issues/revokes Asset's own grants); Gateway Q2 (long-term grant-store ownership if Authority Service supersedes Console) |
| 3 | **Node composition/assembly root** — who wires the services into one running node | Gateway, Host, Console (3/7) | Gateway Q3 (explicitly not Gateway itself, per its own charter — nothing else claims it); Host Q2 (`automation:trigger-time`/`runtime:leased-execution` depend on services that don't exist as directories); Console Q4 (node-scoping rests on a one-time bootstrap default only) |
| 4 | **Admission of verified state into a durable registry** | Identity, Registry (2/7) | Identity Q3 (who admits a verified claim into a principal's registry record); Registry Q2/Journey 4 (`read-owner`/`register-entry` unbuilt — the same gap from the receiving side) |
| 5 | **Asset↔Record journal wiring** | Asset, Record (2/7) | Asset Q2 (who migrates Asset's lifecycle onto Record's journal); Record Q4 (who wires Asset's event storage through Record) — mutually confirming, neither side has built its half |
| 6 | **Node continuity/destruction/succession** | Identity (1/7) | Q5 (node lost/destroyed, no backup/restore/off-node custody); Q6 (root occupant unavailable — pure judgement) |
| 7 | **Cross-node negotiation ownership** | Gateway (1/7) | Q4 — federation port declared, no negotiating owner named |
| 8 | **Provenance/trust-root for external updates** | Host (1/7) | Q3 — signed-source policy named missing in `KNOWN-GAPS.md`, no trust root owner |
| 9 | **Witness-load concentration** | Registry (1/7) | Q3 — `sov-witness@1` witnesses all three declared owner records at once; no rule addresses the concentration itself |
| 10 | **Contract-vs-implementation drift** (not custody, carried forward as a correctness finding) | Console, Identity, Record, Asset (4/7) | Console Q5 (does a declared precondition mean enforced or logical shape); Identity (5 refusal-vocabulary mismatches between `contracts/service.json` and code); Record (citation mismatch: `CLAUDE.md` cites PROD-I-8 for the Asset SQLite gap, `services/asset/KNOWN-GAPS.md`'s own row cites C15/EventEnvelope instead); Asset (same mismatch, other side) |

Thirty-one questions map onto ten themes; four themes (secret custody,
authority-grant ownership, composition root, admission-into-registry) each
recur across at least two independently-drafted documents with no shared
source between them beyond the root governing set.

## Testing the candidates against `CLASSIFICATION.md`'s bar

**Authority Service (`#12`) / Capability Broker (`#15`) — evidence supports
chartering.** Themes 1 and 2 together are nine independent citations across
six of seven services, all converging on the same missing boundary: something
that issues, revokes, and custodies typed authority and the material (secrets,
tokens) that backs it. `GROUND-003` ("authority is granted, never acquired")
already states the invariant such a service would enforce; nothing today owns
enforcing it end to end. This is the shape of evidence `CLASSIFICATION.md`
asks for, now documented rather than asserted. `decisions/0040` chartered the
Gateway Service "at proposal standing" from evidence, without first waiting on
Bdo — the same move applies here.

**Relay (`#17`) — no fresh evidence.** None of the thirty-one questions named
message delivery, relay, or transport-independent routing as a gap. Relay
stays exactly where it was before this exercise: a named epic-tree intention
with no charter and no contract. Nothing here argues for or against minting
it; the silence itself is the finding.

**Storage — no case for a new boundary; existing categorization holds.**
Theme 5 (Asset↔Record wiring) and part of Theme 1 (payload-adjacent
credentials) are storage-shaped, but both resolve to "which existing service
owns this" (Asset vs. Record), not "a missing third service." `CLASSIFICATION.md`
already places the Record substrate beside the Shared Kernel and Runtime as a
cross-cutting foundation, not a Service-level entry. This tally does not
disturb that categorization.

**Adapters — not eligible regardless of evidence.** `CLASSIFICATION.md` defines
Model Adapter as a translation Component, not a bounded domain lifecycle. No
volume of custody findings changes what structural kind of thing it is.

## What this is not

Not a ruling, and it charters nothing itself. None of the thirty-one open
questions is resolved, reassigned, or made less open by appearing in this
tally — each remains exactly as open as its home `JOURNEYS.md` states it, per
`decisions/0067`'s own rule. This document only does what a tally does: count
independent citations and compare the count to a bar that already existed.

## Recommended next bounded concern

Charter an Authority Service (or Capability Broker — `#12` and `#15` overlap
enough that picking between them, or merging them, is a short scoping
question worth settling before writing the charter) at `PROPOSED` standing,
scoped to: authority-grant issuance and revocation (currently ad hoc across
Console, Asset, and Gateway per Theme 2), and a first owned answer to
secret/credential custody (currently owned by nobody, refused everywhere it
is touched, per Theme 1).

This is a distinct bounded concern from the seven documents this decision
tallies — a new service domain, and plausibly a new effect class once it
holds real credential material — and belongs on its own branch and pull
request per `AGENTS.md` Closure ownership, not absorbed into this one.

## Defaults taken

- Themes are my own clustering of the thirty-one citations, not something any
  drafting agent declared; the citations themselves are verbatim from each
  service's `JOURNEYS.md` and are the load-bearing evidence, not the theme
  labels.
- "Evidence supports chartering" for Authority Service/Capability Broker is a
  reversible recommendation, not an act — no `services/authority/` or
  `services/capability-broker/` directory is created here.
