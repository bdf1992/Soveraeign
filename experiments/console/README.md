# Console surface — experiment

Untracked experiment. Not a chartered service, no standing, commits the project
to nothing. Delete with `rm -rf experiments/console .local/console`.

    python experiments/console/serve.py    # http://127.0.0.1:8787

That is the only command. An absent or empty store is a state the surface
serves, not a failure to configure one: the node arrives empty and the page
offers the acts that found it. `python experiments/console/drive.py v4` and
`drive_fresh.py` drive it in Chrome and check it.

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
| `/v5` | The empty node made inhabitable | v4 could not survive a node with nothing in it: it read `channels[0]` on boot and hung on the arrival plate forever, and merely opening it wrote the two entries of its own session, so an untouched node greeted you by reporting that something had happened. Every region now carries its own first move, the session opens on first use rather than on sight, and the readout of an act survives the re-render that act causes |

## The fresh-node candidates

Three directions on the same question — what a person meets when the node holds
nothing — kept side by side rather than merged, so taste can pick.

| | Register | What it refuses |
| --- | --- | --- |
| `/fresh-a` | **The founding.** Five acts down one column, each a real call, each showing the receipt it wrote. Step two lets you attempt the ungranted act and watch it refuse. The journal builds in a spine on the left as you go | A tour. Nothing here is a preview of what would happen, and no step is simulated |
| `/fresh-c` | **The door.** One screen. The node says what it is, shows the five zeros it holds, and offers two composed gestures: found it, or fill it from the repository | Teaching. It assumes you would rather be inside than instructed |
| `/v5` | **The empty room.** No separate screen at all: the console itself, with the first move sitting in whichever region is empty | A modal onboarding path that has to be finished before the real surface appears |

## Above Discord

- `GET /api/operations` is the same discovery answer the CLI's `operations`
  command gives. From `/v3` on, the page builds working controls from it, so an
  operation added to the service reaches the surface without the page being
  edited.
- `window.__sov` (`/v4`, `/v5`), `window.__fresh` (`/fresh-a`) and
  `window.__door` (`/fresh-c`) expose state and actions, so a model drives the
  same surface a human does through the same calls. The drive scripts use only
  those handles and the DOM — they never trust a page's own claims.
- A model operator is a peer in the operator list, not an integration. A human
  post and a model post take the same transition and differ only in
  `actor_kind` and the receipt's `interface_id`.
- Every act returns a receipt and the receipt is shown. So is every refusal.
- No control hands you a command to run somewhere else. Filling the node from
  the repository and emptying it again are `console.fill` and `console.empty` on
  the door, reachable by a click and by a model, rather than a script to run in
  a terminal with the server stopped first.

## What it is honest about

The judgement-request record does not exist in the Console Service, so the
`waiting-on-you` channel is threads standing in for it. An answer recorded there
is a real attributed post with a real receipt at `RECORDED` standing. It is not
a ratification, and the surface says so where the answer is recorded.

An authority refusal used to be the one refusal the Console Service did not write
down. Every other refusal went through `append.refuse`, which appends a `REFUSED`
receipt before raising; `authority.check` raised directly, so a `NO_LIVE_GRANT`
left no entry, and the door answered such a refusal with the last receipt it
could find in the journal — labelling an unrelated entry as that refusal's proof.
Both are fixed: `authority.require` now checks and refuses at the same boundary
the Asset Service does, with three cases in
`services/console/tests/test_contract_shapes.py` proving every ungranted
transition leaves exactly one `REFUSED` receipt and no record of the thing it
refused. The door reports `recorded` per call rather than assuming, and
`/fresh-a` reads that field rather than asserting the record every time.

## Known debt

- The store is rebuilt rather than migrated. `console.fill` drops `.local/console`
  and writes a new journal; append-preserving holds within a journal, and
  refilling starts a different one rather than rewriting this one.
- `console.empty` destroys records. It refuses without `confirm: "empty"`,
  because the surface renders a control for every declared operation and a
  stray press should not drop a journal nobody agreed to drop. That is a guard,
  not a backup.
- `drive_fresh.py` stands up its own server on port 8788 over a throwaway store,
  because the empty state cannot be proven against a seeded one.
