# Console surface — experiment

Untracked experiment. Not a chartered service, no standing, commits the project
to nothing. Delete with `rm -rf experiments/console .local/console`.

    python experiments/console/seed.py     # build a real console store
    python experiments/console/serve.py    # http://127.0.0.1:8787
    python experiments/console/drive.py v4 # drive it in Chrome and check it

Every click calls the Console Service and writes to the append-preserving
journal. Nothing here is a mock: the posts on screen were written by
`ConsoleService.post`, the receipts shown are the receipts it returned, and the
refusals shown are refusals the service recorded before answering.

## The freezes

Served side by side so a later direction can be compared against an earlier one
instead of replacing it. `/` serves the newest.

| | What it is | What it fixed |
| --- | --- | --- |
| `/v1` | The Discord shape, working end to end | — |
| `/v2` | The register correction | v1's type was one face at one size and read as a demo; its content is a few long arguments, not many short messages, so the thread pane was mostly void. Serif display headline, a 68ch measure, an arrival that counts real work, and the queue's four owner actions read out of `STATUS.yaml` instead of a generic text box |
| `/v3` | The door made usable | v2's generated domain marks arrived as hairlines at 44px and three domains read the same, so the rail now carries two-letter codes unique by construction; the journal tape overlapped its own label; and the operation list was a manifest dump, so each declared operation is now a working control that runs and shows its receipt |
| `/v4` | The record made reachable | v3 threw away the verdict once a decision was answered, and its provenance chips were inert text. A settled decision now carries its owner action in the queue and the header, and any digest or entry chip pulls back to the journal entry behind it, with its position in the chain and the entry it follows |

## Above Discord

- `GET /api/operations` is the same discovery answer the CLI's `operations`
  command gives. From `/v3` on, the page builds working controls from it, so an
  operation added to the service reaches the surface without the page being
  edited.
- `window.__sov` exposes state and actions, so a model drives the same surface a
  human does through the same calls. `drive.py` uses only that handle and the
  DOM — it never trusts the page's own claims.
- A model operator is a peer in the operator list, not an integration. A human
  post and a model post take the same transition and differ only in
  `actor_kind` and the receipt's `interface_id`.
- Every act returns a receipt and the receipt is shown. So is every refusal.
- No control hands you a command to run somewhere else.

## What it is honest about

The judgement-request record does not exist in the Console Service, so the
`waiting-on-you` channel is threads standing in for it. An answer recorded there
is a real attributed post with a real receipt at `RECORDED` standing. It is not
a ratification, and the surface says so where the answer is recorded.

## Known debt

- `serve.py` is 369 lines against the repository's 300-line module budget. It is
  experiment code rather than a service, and `scripts/lint.py` does not flag it,
  but the number is over the line and recorded here rather than left silent.
- The store is rebuilt rather than migrated. `seed.py` drops `.local/console`
  and writes a new journal; append-preserving holds within a run.
- Stop the server before reseeding. Windows will not let the store be replaced
  while the process holds its SQLite file.
