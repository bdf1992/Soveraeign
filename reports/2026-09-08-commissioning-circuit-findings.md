# Commissioning circuit: what one lap found

One bounded concern was carried around all seventeen stages of the Phase 1.5
commissioning circuit by hand on 2026-09-08, to establish which stages have a
mechanism. This is the compressed result. It grades nothing and settles nothing.

The payload was `concern:schematically/golden-rendered-text`, deliberately not
maintenance of this repository. Its record is the branch and pull request named
under Provenance.

## Observations

Each row names how it was established. Rows marked *read* carry an address a reader can
open; rows marked *run* were established by executing the command named. An independent
reading on 2026-09-09 corrected four of these and struck one; the corrections are in the
rows and the struck row is kept struck rather than deleted.

| # | Stage | Observation | Address |
| --- | --- | --- | --- |
| O1 | Request, Agenda | *run.* **Corrected.** A session can declare its own sources and queues at `register --source S --queue Q`, and `console` then projects them. What does not exist is anything putting work there the session did not name itself, and there is no Request or Agenda object | `scripts/sov_session.py register`, then `console` |
| O2 | Custody, Lease | Custody boards and leases hold no reference to each other in either direction | `grep -c lease scripts/sovcustody/board.py scripts/sovcustody/model.py` → `0`, `0` |
| O3 | Participant context | A lease mints and accepts a principal the session registry reports as unidentified | `sov_session.py register` vs `sov_lease.py take` |
| O4 | Execution, Record | The lease recorded nothing about work done under it; `sov_lease.py draw` exists and nothing calls it | `readings: []`, `pressure: 0.0` |
| O5 | Findings | *read.* No Finding instance is checked in. `.claude/workflows/sov-loop.js` shapes one at runtime and gates on its schema, so the contract is exercised by the harness and never reaches the Record | S32 |
| O6 | Receipt | *read.* **Corrected.** A receipt is emitted: `bindings/mcp/observe_journey_02.py` runs an operation under a grant and writes a conforming receipt. Two artifacts satisfy the schema, not one. What no service does is emit one as part of its own settlement | S32 |
| O7 | Settlement | `WITNESSED` is refused without a witness lease held by another principal; a citation buys nothing | `UNWITNESSED_STANDING_CLAIM`, `scripts/sovkernel/work_lease.py` |
| O8 | Settlement | Nothing routes a launched independent reading to `sov_lease.py helper`, so evidence that exists cannot be seen by settlement | measured; the lap settled at `BUILT` for this reason |
| O9 | Cleanup | `contracts/custody.schema.json` declares `cleanup_obligations` and the settlement path never reads it | source |
| O10 | Discovery | `STATUS.yaml` line 88 names `.local/acceptance/ledger.ndjson`, which does not exist | `STATUS.yaml:88` |
| O11 | Discovery | *run.* **Corrected.** 234 rows, 195 `grant:test` and 39 with no grant, across many timestamps, growing six per `verify` run. The count, the uniform grant and the single timestamp were all wrong. The row stands only in that nothing marks fixture rows as fixtures, and `acceptance/A24.json` already records that | `.local/landing/ledger.ndjson`, gitignored |
| O12 | Discovery | `sov_lease.py status` returns empty for a closed lease unless `--all` is given, and the store location is named only in a source docstring | measured on the lap's own lease |
| O13 | Use | A participant that built none of it reached the capability and reproduced every claim, including the disclosed residual | the cold-discovery run, recorded under Provenance |
| O14 | Whole circuit | `CHROMIUM_PATH` appears in no document in either repository; two fresh participants lost their first run to it | measured twice |

## Already represented elsewhere

Recorded here only so a reader does not file them twice.

| Finding | Its home |
| --- | --- |
| A conforming witness record cannot satisfy the gate requiring one | `OPEN-SEAMS.md` S29 |
| A repair invalidates the evidence taken against its subject, and nothing re-arms | `OPEN-SEAMS.md` S30, met at a different object |
| Observer independence is declared rather than measured | `reports/2026-09-07-controller-handoff.md`, finding 6. **Corrected**: an earlier version of this row sent readers to `decisions/0104`, which is about Communications fidelity and never mentions independence. A routing table that misroutes is worse than none |
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
  *Defeated by* a run whose work was chosen from a queue or ticket the participant did not
  itself name. An earlier wording said "entered at Request", which S31 makes unreachable and
  so could never have fired.
- **C3.** A definition written narrower than the concern it serves is satisfied by work that
  leaves the concern open, and nothing compares the two. Observed once on this lap, where the
  closure condition said "compares rendered text" and the concern asked for a check that would
  have caught a regression an invisible caption also produces. One instance is not a pattern.
  *Defeated by* a second concern whose definition was narrower than its concern and whose work
  nevertheless closed it, or by a reading showing the two were the same scope all along.

## Work items

Concrete, small, and none of them taken here.

1. `STATUS.yaml` line 88 names an acceptance ledger that does not exist — repair or remove the reference. Governing document; outside `grant:standing-landing-loop`.
2. Mark the twelve fixture rows in `.local/landing/ledger.ndjson` as fixtures, or move them out of a ledger a reader is told to trust.
3. Document `CHROMIUM_PATH` where a fresh participant meets it.
4. Make `sov_lease.py status` name the store it reads and say that closed leases need `--all`.
5. Route a launched independent reading to a witness lease, so settlement can see evidence that exists (O8). This is the one that unblocks `WITNESSED`.

## Provenance

- Payload and its two independent readings: `bdf1992/schematically` PR #35, branch `claude/movement-72-hours-2claax`, files `LAP-EXECUTION-REPORT.md`, `FINDING-WORK.md`, `FINDING-PARTICIPANT.md` and `FINDING-GUARD.md`. Those four are in that repository and do not resolve here.
- The lap's own settlement is `reports/settlements/2026-09-08-lease-concern-soveraeign-lease-settlement-record-2.json`, closed at `BUILT`. It resolves only on the branch of pull request #240 and not on `main`, which is the disqualifying condition this register's own `P15-X5` ticket names. Stated rather than cited as though it resolved here.
- The full 847-line trace and cold-discovery report were the working record. They are not carried: everything in them that changes a decision, an invariant, a test, or a future investigation is above, and the rest was narration. Superseded PR: #241.
