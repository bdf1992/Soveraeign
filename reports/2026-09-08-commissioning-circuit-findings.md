# Commissioning circuit: what one lap found

One bounded concern was carried around all seventeen stages of the Phase 1.5
commissioning circuit by hand on 2026-09-08, to establish which stages have a
mechanism. This is the compressed result. It grades nothing and settles nothing.

The payload was `concern:schematically/golden-rendered-text`, deliberately not
maintenance of this repository. Its record is the branch and pull request named
under Provenance.

## Observations

Reproducible from the addresses given. Each was read, not inferred.

| # | Stage | Observation | Address |
| --- | --- | --- | --- |
| O1 | Request, Agenda | No producer writes into the work console; no Request or Agenda object exists | `scripts/sov_session.py console` → `sources: (none)`, `queues: (none)` |
| O2 | Custody, Lease | Custody boards and leases hold no reference to each other in either direction | `grep -c lease scripts/sovcustody/board.py scripts/sovcustody/model.py` → `0`, `0` |
| O3 | Participant context | A lease mints and accepts a principal the session registry reports as unidentified | `sov_session.py register` vs `sov_lease.py take` |
| O4 | Execution, Record | The lease recorded nothing about work done under it; `sov_lease.py draw` exists and nothing calls it | `readings: []`, `pressure: 0.0` |
| O5 | Findings | No Finding instance exists and no code constructs one | S32 |
| O6 | Receipt | No operation has ever produced a receipt | S32 |
| O7 | Settlement | `WITNESSED` is refused without a witness lease held by another principal; a citation buys nothing | `UNWITNESSED_STANDING_CLAIM`, `scripts/sovkernel/work_lease.py` |
| O8 | Settlement | Nothing routes a launched independent reading to `sov_lease.py helper`, so evidence that exists cannot be seen by settlement | measured; the lap settled at `BUILT` for this reason |
| O9 | Cleanup | `custody.schema.json` declares `cleanup_obligations` and the settlement path never reads it | source |
| O10 | Discovery | `STATUS.yaml` line 88 names `.local/acceptance/ledger.ndjson`, which does not exist | `STATUS.yaml:88` |
| O11 | Discovery | `.local/landing/ledger.ndjson` holds twelve rows shaped like landings, all `grant:test` on branch `work` at one timestamp, marked as fixtures nowhere | a fresh reader nearly reported one as a real landing |
| O12 | Discovery | `sov_lease.py status` returns empty for a closed lease unless `--all` is given, and the store location is named only in a source docstring | measured on the lap's own lease |
| O13 | Use | A participant that built none of it reached the capability and reproduced every claim, including the disclosed residual | the cold-discovery run, recorded under Provenance |
| O14 | Whole circuit | `CHROMIUM_PATH` appears in no document in either repository; two fresh participants lost their first run to it | measured twice |

## Already represented elsewhere

Recorded here only so a reader does not file them twice.

| Finding | Its home |
| --- | --- |
| A conforming witness record cannot satisfy the gate requiring one | `OPEN-SEAMS.md` S29 |
| A repair invalidates the evidence taken against its subject, and nothing re-arms | `OPEN-SEAMS.md` S30, met at a different object |
| Observer independence is declared rather than measured, on both context and perspective | `decisions/0104`, open in PR #231 |
| A settled result was unreachable from a clone | Repaired in PR #240 |

## Conjectures

Not observations. Each is defeasible and none is acted on here.

- **C1.** The participant circuit and the Record are two parallel worlds: `services/`
  converges on the Record Service, and `scripts/sovsession/store.py` writes sessions and
  leases under the common git directory. O1, O2, O4, O5 and O6 may all be symptoms of that
  one split. *Defeated if* the stages are meant to be independently recorded, in which case
  the missing primitive is the act that joins them rather than a shared store.
- **C2.** The reason five days of work produced instruments rather than delivery is that
  inspection is the part of the circuit that exists, so it is the part that can be improved.
  *Defeated by* any run in the record that entered at Request.
- **C3.** A definition written narrower than the concern it serves is satisfied by work that
  leaves the concern open, and nothing compares the two. Observed once on this lap, where the
  closure condition said "compares rendered text" and the concern asked for a check that would
  have caught a regression an invisible caption also produces. One instance is not a pattern.

## Work items

Concrete, small, and none of them taken here.

1. `STATUS.yaml` line 88 names an acceptance ledger that does not exist — repair or remove the reference. Governing document; outside `grant:standing-landing-loop`.
2. Mark the twelve fixture rows in `.local/landing/ledger.ndjson` as fixtures, or move them out of a ledger a reader is told to trust.
3. Document `CHROMIUM_PATH` where a fresh participant meets it.
4. Make `sov_lease.py status` name the store it reads and say that closed leases need `--all`.
5. Route a launched independent reading to a witness lease, so settlement can see evidence that exists (O8). This is the one that unblocks `WITNESSED`.

## Provenance

- Payload and its two independent readings: `bdf1992/schematically` PR #35, branch `claude/movement-72-hours-2claax`, files `LAP-EXECUTION-REPORT.md`, `FINDING-WORK.md`, `FINDING-PARTICIPANT.md`.
- The lap's own settlement: `reports/settlements/2026-09-08-lease-concern-soveraeign-lease-settlement-record-2.json`, closed at `BUILT`.
- The full 847-line trace and cold-discovery report were the working record. They are not carried: everything in them that changes a decision, an invariant, a test, or a future investigation is above, and the rest was narration. Superseded PR: #241.
