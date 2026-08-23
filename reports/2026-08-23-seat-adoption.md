# Retroactive seat adoption, 2026-08-23

Status: `RECORDED · RETROACTIVE · NOTHING RATIFIED`

`decisions/0020-owner-seat-topology.md` defines Owner as a seat and admits
that every run before the topology executed ownerless. An adoption record is
the honest retroactive form: a named seat states that it adopts a past run,
what evidence it adopted, what it now settles about that run, and what was
never granted. An adoption is not a backdated grant; the runs below carried
no live grant and this file does not pretend otherwise. A report under
`reports/` is evidence, not policy; Bdo may adopt, re-execute, or strike any
row (decision 0020, judgement item 5).

Seats named here are the ones in the positive fixture of
`contracts/fixtures/seat-registry.fixtures.json`: `seat:root` (occupied by
Bdo), `seat:session-control` (occupied by the Claude interactive session Bdo
launched and directed on 2026-08-23).

## Adoptions by seat:session-control

| # | Run | Executed by | Evidence | What the seat settles | Never granted |
| --- | --- | --- | --- | --- | --- |
| A1 | Shared-kernel build for issue #6, commits `681861e`..`a768d3a` on `feat/6-shared-kernel-transitions` (PR #61) | the session occupant directly, worker-fashion | the branch, its verify/lint outputs, PR #61 | accepted as `BUILT` evidence; not witnessed by the builder | no scoped build grant existed; authority was Bdo's conversational directive |
| A2 | Witness pass 1 over `681861e` | launched agent `sov-witness` (a34f27a) | `reports/2026-08-23-kernel-witness.md` §pass 1 (on the PR #61 branch) | accepted as independent observation supporting `OPEN -> BUILT` | no typed Red-engagement grant; no lease, fence, or budget was recorded |
| A3 | Witness pass 2 over `d534dbd` | same agent, context intact | same report, §pass 2 | as A2 | as A2 |
| A4 | Witness pass 3 over `1485439` | same agent | same report, §pass 3 | as A2 | as A2 |
| A5 | Witness pass 4 over `55e7754` | same agent | same report, §pass 4 | as A2; the closing commit `a768d3a` remains un-witnessed | as A2 |
| A6 | This drafting run: decision 0020, seat-registry contract, fixtures, test, this file, on `docs/owner-seat-topology` | the session occupant directly | the branch and its PR | accepted as `BUILT` evidence only | no drafting grant; Bdo's "cont." directive in conversation |

Settlement note: `seat:session-control` settles `VERIFICATION`-shaped
evidence only. Nothing in this file ratifies anything; every `RIGHT-GREEN`
act over these runs belongs to `seat:root`.

## Pending adoption (evidence exists; launcher attribution incomplete)

Runs on `feat/federation-harness-and-hardening` predating this session's
records: the christening report (2026-08-22), the operation reports, and the
stack certification (2026-08-23). Each names its own session inside the
report body; adopting them belongs to whichever seat Bdo recognizes as
having launched those sessions. Listed rather than adopted, because an
adoption this file cannot evidence would be exactly the fabrication the form
exists to prevent.

## Residuals

- No lease, fence, budget, or typed grant existed for any adopted run; the
  topology that would have supplied them is itself only PROPOSED.
- The witness agent's four passes were settled by the same seat that
  launched the builder — legal one edge up, but the seat occupant also wrote
  the code being witnessed. The separation that matters (builder is not the
  witness) held; the separation the topology will add (the settling seat is
  not the building actor) did not exist yet.
- `.local/schedules/ledger.ndjson` was not present in this checkout; any
  scheduled-run attempts recorded there are not covered here.
