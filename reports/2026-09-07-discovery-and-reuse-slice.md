# Discovery and reuse: the first P15-X3 slice

Session `session-e0662f`, principal `principal:claude-fable-5-1` (registered, `UNVERIFIED`,
one hop from `principal:bdo`; the registry names, it grants nothing), branch
`claude/sovereign-phase-1-5-5uzffu`, 2026-09-07. Concern: move
`custody:phase-1-5/discovery-and-reuse` (exit clause P15-X3) off its opening point with work
whose closure a command demonstrates, composed from what P15-X1 and P15-X2 already built.
Effect class `RECORD_LOCAL` for every build step; the landing is `RESOURCE_CONSUMPTION` under
`grant:standing-landing-loop`; the pull request into `main` is the remote crossing Bdo
authorised for grant-scoped landings in this session. No phase state, standing field, or
clause verdict moved.

## Terminal

Two parts, two terminals.

- The instrument and the custody edits: **landed** on `main`. Five frozen candidates
  through `python scripts/sov_land.py freeze`, each superseding the last on a witness
  finding or a gate refusal; the fifth, `60d5615`, merged by `land-candidate` under the
  ratified grant on pass 5's `CONFIRMED` observation and then onto `origin/main` by
  PR #219 as `aeecc60`.
- The witness records, this report, and the acceptance packet: **presented** for Bdo's
  review in a second pull request, because `witness/`, `reports/`, `acceptance/` and the
  orientation page are outside the grant's scope. Nothing in that pull request changes
  standing by itself; the custody member words it carries are the witness's, quoted.

## What was built, and the command that proves it

| Part | Proof | Reading at the landed candidate |
| --- | --- | --- |
| A fresh participant reads the artifact alone for the result P15-X1's custody carries at `WITNESSED`, reconstructs why it stands, restores the node's journal to the head the witness holds outside the export, enters the node as the principal it declares, and grades P15-Q3.1 and Q3.2 | `python scripts/sov_reuse.py run --principal principal:claude-fable-5-1` | `FAIL` on exactly two facts, both true of the record; see the next section |
| The reader can fail | `python scripts/sov_reuse.py selfcheck` | positive variant passes; nine defeating variants each fail with exactly the defects they declare |
| The layers are the product's own | `scripts/sovreuse/discover.py`, `settle.py`, `reuse.py` | custody model, the standing gate's record reader, the witness receipt, git, the lease store, `sovnode.journal` restore with the outside head, and the fresh-participation probe; the grade comes from `conformance/commissioning.py`, which imports none of them |
| Unit cases | `python -m unittest scripts.tests.test_sov_reuse` | 14 cases, run by verify's tooling-tests check |
| Custody board | `python scripts/sov_custody.py board custody:phase-1-5/discovery-and-reuse` | one `ITEM` member at `VERTICAL_SLICE` |
| Repository gate | `python scripts/verify.py`; `python scripts/lint.py` | PASS with attributed debt; hygiene PASS |

The closed path: custody collection, member at `WITNESSED`, the witness record and receipt
its `stage_observed_by` names, the record's own declaration block read the way
`sov_standing.py` reads it, the receipt's observed addresses digested again against the
bytes now in the tree, the merge on the trunk's first-parent line that first carried the
witnessed revision, the inventory this host can read for that custody and revision, the
journal export under `nodes/` whose declared head equals the head the receipt holds
outside it, a restore of that export into an empty node refusing truncation and a broken
chain, the node entered as the declared principal through the P15-X1 probe, and the two
predicates graded on what came back.

Nothing new was minted: no store, no contract, no vocabulary, no verify check. The custody's
closure command moved from `python scripts/sov_next.py`, a signpost reader that cannot see
the clause's defeating condition, to `python scripts/sov_reuse.py selfcheck`, which is
built to.

## The live reading

As `principal:claude-fable-5-1` against this repository at the landed candidate:

- Discovery, reconstruction and reach all succeed: the member, its pass-6 record and receipt,
  the outside head `23d3b48086be…`, the export that replays to it, and the landing merge
  `ee60801` (PR #218) are all read from the artifact, and the 85-entry journal restores into
  an empty node on this host, which has never held the node.
- **P15-Q3.1 reads `settlement was not against current state`.** Eight of the addresses the
  pass-6 receipt observed at `571e936` hold different bytes on the trunk: the journal helper
  and its tests, the commissioning check table, `nodes/README.md`, the custody collection,
  the principal registry, the P15-X1 report and its first packet. The pass-6 repairs landed
  after the pass that asked for them, in the same pull request. Witness pass 7 on P15-X1,
  launched from this session at `26b1887`, read every one of the eight and supports
  `WITNESSED` for that member at that revision (`witness/fresh-participation.md`, pass 7).
- **P15-Q3.2 reads `fresh participant did not use the accepted result`.** The restored node
  refuses this principal a session: its journal grants `open:session`, `read:registry` and
  `close:session` to `principal:claude-fable-5` and to nobody else. The refusal is the
  Console's, read from its record. A control run as `principal:claude-fable-5` commits the
  crossing and clears the predicate (witness pass 1, `witness/discovery-and-reuse.md`).

Both facts are the record's, not the reader's. The first is what "settles only after
independent observation" costs once a witness has digested a shared file: the pass-7
receipt digests the custody collection too, so the next edit to any member's words drifts
it again. The second is authority resolved separately from capability, which is what
P15-X1 asks for; it is also the smallest owner decision this run leaves.

## Composition: what existed, what was missing

The composition hypothesis held. Every layer the slice needed already existed; the slice
is 546 lines of reading and 254 of fixture over them. What the composition exposed:

1. A custody member's evidence lives in prose. `stage_observed_by` is free text; the reader
   extracts `witness/…` paths from it and reports `basis: prose`. The schema has no
   evidence field (P15-X1's F12, still open).
2. A witness receipt digests files, and one of them is the shared custody collection. The
   member's own standing words live in that file, so recording a pass in the member drifts
   the receipt that supports it. Receipts need an address finer than a file, or witnesses
   need to digest the member rather than the collection.
3. A custody's closure `check` is a `COMMAND` nothing executes. Only the unit suite measures
   the reader; the command is a declaration (P15-X1's F14, still open; the witness's F5).
4. The orientation page pins the number of verify checks, so adding one under the standing
   grant is impossible: `CLAUDE.md` is excluded from the grant and the snapshot gate fails
   the tree until the page moves. This session hit it, removed the check, and let the unit
   suite carry the slice under the existing tooling-tests check. The P15-X1 session hit the
   same wall and edited the page under Bdo's review. Two sessions in a row is a shape, not
   an accident: the page authors a number the repository derives.
5. `scripts/tests/test_sov_land.py` writes fixture landings into the live
   `.local/landing/ledger.ndjson` when verify runs (pass-7 witness, outside its subject).
   The ledger on this host holds two `grant:test` rows stamped during this session's
   verify runs. A test that writes the runtime record it is testing is a defect to route.
6. `git rev-list --first-parent --ancestry-path` drops the merge itself in git 2.43; the
   landing rule walks the ancestry path without `--first-parent` and intersects with the
   line. Recorded because the first draft read PR #218's landing as the witnessed commit.
7. `sov_land.py freeze` recorded a candidate's changed paths before committing, as the
   staged paths plus what the branch already carried. A staged page that returned to the
   base's bytes stayed in the list while the real range dropped it, and `land-candidate`
   refused the record for not describing its own range. Repaired in place: the record now
   reads the range after the commit, pinned by a test where a staged path reverts while a
   carried one stays. The gate was right to refuse; the record was wrong.
8. One entry in `STATUS.yaml`'s acceptance queue staled 62 clarity receipts, because every
   harness file declares `STATUS.yaml` whole as its basis. Each was re-read for a
   dependence on the queue and re-recorded; none had one. This is finding 2 again in
   another contract: a basis, like a receipt, addresses a file where it means a section.
   Four gates now share the shape: witness receipts digest the custody collection, clarity
   bases digest `STATUS.yaml`, four diagram views declare `STATUS.yaml` whole as a source
   and went stale on the same entry, and the orientation page pins counts the record
   derives. The missing primitive is an address below the file, a named member, section
   or field with its own digest, that receipts, bases and views can hold instead of the
   file.
9. The tooling-tests check crossed verify's 30-second catastrophic ceiling on the hosted
   runner at `ea01dcc`, and passed at `57271f7` by timing alone. Two causes, both this
   concern's to fix: the new suite built its fixture three times and ran every variant
   twice, and the runner's shard weight table, last measured at 97 modules, isolated two
   modules that now take about a second while the five multi-second modules packed into
   one shard at ordinary weight, 18.6 seconds against 4.5 for the lightest. Every module
   was timed alone, the weights set to the measured seconds times ten, and the shards now
   read 12.1, 9.6, 11.0 and 9.8 seconds. One test had pinned the old premise by name,
   asserting that the git-driving module's weight buys it fewer peers; it now asserts the
   property for whichever module the table weights heaviest. The table's own comment says
   to remeasure when the population changes; nothing enforces it, so the next arrival
   will stale it again.
10. `sov_land.py land-candidate` records no landing in `.local/landing/ledger.ndjson`; only
    the compatibility `plan` and `land` paths write it. The candidate path, the target
    model, lands without the record the ledger exists to keep, while the landing gate's
    own tests write `grant:test` rows into that ledger on every verify run: 72 rows with
    60 of them fixtures when this session first read it, 138 with 115 when this sentence
    was written, and more by the time anyone reads it. None of them is this landing.

11. The candidate CI job at `77421de` failed once in the tooling tests: `test_sov_diagrams`
    wrote its scratch view into the live `diagrams/` directory and removed it, while
    `test_sov_facets` in a parallel shard globbed the tree, found the file, and could not
    read it. The two modules were in parallel shards before the reweight too; the new
    partition changed the timing, not the defect. The grader resolves sources against
    the root, so the scratch view and the tool's own selfcheck view now live in temp
    directories. `test_sov_docs` edits the live `docs/documentation.html` in one case
    while verify's documentation reader may read it in the pool; same shape, recorded,
    not repaired here.

## Independent witness

Five passes on this concern by `sov-witness`, each launched from this session into a fresh
context with the candidate record, the claim as the commit states it, and the commands;
none read this report or the packet. Record: `witness/discovery-and-reuse.md`; receipts
under `witness/observations/2026-09-07-discovery-and-reuse-observation*.json`; the
landing-gate observation for each pass under `.local/observations/`, runtime state.

- Pass 1 at `26b1887`: `NOT-YET`, standing `BUILT`. Eight findings. The high one: on any
  clone with `origin/HEAD` set, git lists the symbolic ref as a bare remote name and the
  inventory read it as a branch left behind, so Q3.1 failed on a phantom this host could
  not show. Also: a tampered export raised instead of refusing; the member note counted
  the variants wrong and named one of the two live facts; the fixture's reader was its
  builder; the selfcheck asserted reason inclusion rather than the exact defect set. F5
  (nothing executes a custody's closure command) and F7 (the reader's own branch is
  excluded) recorded as residuals. Each repair carries its own defeating variant or test.
- Pass 2 at `b0c013c`: `RATIFIABLE-WITH-CONDITIONS`; `BUILT -> WITNESSED` supported for
  the instrument claim. One high finding, F9: the committed `docs/documentation.html` had
  been rendered over the shared working tree and indexed witness records the commit did
  not carry, so a clean clone failed verify while the shared tree passed. Trap T6, on the
  builder's side of it.
- Pass 3 at `ea01dcc`: `RATIFIABLE`, landing verdict `CONFIRMED`. The page rebuilt from the
  committed documents alone; a clean clone passes verify, lint and the documentation
  check; the instrument bytes are identical to `b0c013c`.
- The landing of `ea01dcc` was then refused by the gate itself: the candidate's recorded
  paths did not describe its base-to-commit range. Composition finding 7 below.
- Pass 4 at `57271f7`: `RATIFIABLE`, landing verdict `CONFIRMED`; the record's paths equal
  the range, the gate accepts the record and refuses a copy widened by the page, the
  instrument bytes are identical to `ea01dcc`. F10: the live reading on the shared tree
  now describes other sessions' uncommitted edits, so the attestable reading was taken on
  a clean clone.
- Two hosted CI jobs at `ea01dcc` then failed on verify's catastrophic ceiling: the
  tooling-tests check took 31 and 37 seconds alone against a 30-second ceiling.
  Composition finding 9 below. The repair is the fifth candidate.
- Pass 5 at `60d5615`: `RATIFIABLE`, landing verdict `CONFIRMED`. Measured on a clean clone:
  verify 16.1 seconds wall, the tooling-tests check 15.1 seconds against 22.8 at pass 1,
  the new suite 2.9 seconds against 4.4; the five heaviest modules in the table's order;
  the partition property holds and fails when the heaviest entry is dropped. F11: whether
  the hosted runner stays under the ceiling is evidence only that runner produces; it read
  23.5 seconds at this candidate against 31 and 37 before.
- Landed: `python scripts/sov_land.py land-candidate` merged `60d5615` onto local `main`
  as settlement `90275ae` under `grant:standing-landing-loop` on pass 5's observation;
  PR #219 then merged the same candidate onto `origin/main` as `aeecc60`, at Bdo's
  direction for grant-scoped landings in this session. Local `main` was then set to the
  remote merge; the local settlement commit is unreferenced and lives only in this report.

The witness's judgement items, carried: J1, which reading of "settled against current
state" P15-Q3.1 owns; J2, whether a grant to `principal:claude-fable-5-1` on the live node
is Bdo's to issue and the intended route, or the reuse the clause asks for is a second
session of the principal the node already grants.

P15-X1, pass 7 at `26b1887` by a second witness launched from this session, scoped to
journal custody and the standing's binding to current bytes: `REPRODUCED` with dissent on
the binding; `WITNESSED` re-supported for `scripts/sov_fresh.py` at that revision. Each of
the eight drifted addresses is placed inside or outside pass 6's claim; the pass-6 repairs
F43 to F48 read repaired at HEAD; new F53 (the member bound to two revisions, neither
holding the landed gate bytes) and F54 (the Record CLI opens a store under `.local` on
every command); J12 (the outside head has one holder on a host with no node store).

A closing pass by a sixth launch, on the presented head `d71f153`, over the completion
artifacts themselves: `NOT-YET`, nine findings, all inside this concern. The custody
member words reproduced byte for byte; the packet's demo reproduced except its expected
live reading, which described the landed candidate rather than the presenting commit;
the orientation page's commit count had crossed its tolerance on full history, which the
depth-one hosted checkout cannot see; and five numbers in this report were declarations
the record contradicted. Each is repaired in the commit after `d71f153`, and one is
recorded instead: `scripts/sovreuse/discover.py` says it reads committed files where it
reads the tree, a docstring the next landing on that module corrects. Receipt:
`witness/observations/2026-09-07-compression-run-closing-observation.json`.

## Concerns 2 and 3, held at one seam

After this concern landed, the loop selected the next work from its own findings.

- **Concern 2, an address below the file** (composition findings 2 and 8). `scripts/sovaddress.py`
  resolves `path#fragment` to the bytes it means: a JSON pointer whose steps select a list
  element by field, a top-level YAML block read by line shape, or a Markdown section. The
  receipt grader, the diagram grader, clarity bases and this concern's settle layer digest
  through it; a bare path keeps its meaning, and 113 committed addresses digest identically
  either way. Two witness passes (`witness/sovaddress.md`): `WITNESSED` for the module and
  its adoptions at `e835205`, landing withheld for one finding. The passes also found the
  freeze reading its checks before its own commit, the second freeze-before-commit defect of
  the day; it now commits first, judges scope before that and check-bound preconditions
  after. Branch `feat/address-below-the-file`, PR #221.
- **Concern 3, the tooling suite's cost.** The tooling-tests check crossed verify's
  30-second catastrophic ceiling on the hosted runner at #220's `d2ecb7c` on a commit that
  changed no code. The heaviest module re-ran the whole probe for each of ten readings of
  one result; it now shares runs and drops a selfcheck subprocess verify already runs. 10 to
  4 seconds here. Branch `feat/tooling-test-cost`, PR #223.

Both are held at the same seam, and it is the seam finding 4 named: `CLAUDE.md` says 942
commits, `main` sits at 967, the tolerance is 25, and the grant excludes the page. Every
grant-scoped candidate fails the orientation snapshot by construction until #220 lands the
count, and #220 is Bdo's to merge. The standing landing loop is stalled by a number in a
governing document that the record derives. That is the highest-leverage unresolved fact
this run leaves: not a missing capability, a page authoring what the repository measures.

## Standing changes

- `custody:phase-1-5/discovery-and-reuse`: one `ITEM` member, `scripts/sov_reuse.py`, stage
  `VERTICAL_SLICE`. Standing and `stage_observed_by`: as the witness's final pass supports,
  quoted verbatim in the second pull request.
- `custody:phase-1-5/fresh-participation` member: `work_state` `PRESENTED` to `LANDED`,
  which `git log --merges --first-parent` already said (PR #218). Its `stage_observed_by`
  moves to the pass-7 words in the second pull request (pass 7's F53).
- `contracts/phase-progress.json`: unchanged. The floor for discovery-and-reuse stays
  `ROOT_POINT` until a witnessed member exists on `main`.
- No `STATUS.yaml` field, phase state, or clause verdict moved. P15-X3 stays `NOT_EARNED`.

## Defaults taken

Reversible; each can be overturned in one place.

- The custody's closure check moves to `python scripts/sov_reuse.py selfcheck`, as
  P15-X1's moved to its own selfcheck; the P15-X1 witness's J2 (whether that wants a
  decision note) is still open and applies here too.
- "The accepted result" is read as the member a custody carries at `WITNESSED` whose
  witnessed revision the trunk carries; owner acceptance packets are a separate act and
  are not read by the instrument.
- The landing receipt is the merge that first carried the witnessed revision onto the
  trunk's first-parent line, or the revision itself when it sits on the line. Nothing
  committed records a landing otherwise; the local landing ledger is runtime state.
- Inventory is scoped to the result: leases on its custody still held by a dead session,
  branches and worktrees still carrying its witnessed revision other than the trunk and
  the reader's own line. The reader's own branch is excluded by design (witness F7).
- The fixture's reader is a second fixture principal the fixture root granted, not the
  builder; the live reading's principal is whoever the run declares.
- The slice has no verify check of its own; the unit suite under the tooling-tests check
  carries it. Composition finding 4 says why.

## Residuals

- The pass-7 receipt for P15-X1 observed the custody collection at `26b1887`; the second
  pull request edits that file (member words), so the live Q3.1 reading drifts on one
  address again the moment it lands. Composition finding 2 is the fix; this run did not
  build it.
- `principal:claude-fable-5-1` holds no grant on `node:local`. Whether it should is Bdo's
  (below).
- P15-X1's F35, F49, F52 and J4 to J12 are unchanged; pass 7 adds J12 (the outside head has
  one holder on a host with no node store).
- Witness F5 and F7 are recorded, not repaired; the closing pass's F9 (a docstring in
  `discover.py` says committed where the code reads the tree) waits for the next landing
  on that module rather than a sixth candidate for one word.
- Composition findings 3, 4 and 5 are routed, not repaired, each outside this custody's
  service or authority: the custody contract, the orientation page, the landing gate's tests.

## The owner decision

One, and it is small. The node's journal grants `principal:claude-fable-5` and nobody else.
This session runs as `principal:claude-fable-5-1`, at Bdo's direction. Either:

- Bdo directs an office act granting `principal:claude-fable-5-1` `open:session`,
  `read:registry` and `close:session` on `node:local`, performed with
  `python scripts/sov_fresh.py open-office --issuer principal:bdo --operator
  principal:claude-fable-5-1 --direction "<his words>" --directed-in <session id>` against a
  node restored from the committed journal, the export replaced under its new head and a
  witness holding that head outside it. That unlocks P15-Q3.2 reading met on the live node
  for this principal and gives the node a second granted operator.
- Or the reuse P15-Q3 asks for is a second session of the principal the node already
  grants, and this session's principal is the wrong reader for the live clause. That
  unlocks nothing new and closes the question.

The witness's J1 (whether Q3.1 owns "no observed byte moved" or "the exact revision
landed") is the other judgement item; the reader implements the first, and the second
would make Q3.1 read met today. It is recorded, not chosen.

## Next bounded operation

Composition findings 2 and 8 are one operation: an address below the file, a named member,
section or field with its own digest, that witness receipts and clarity bases can hold
instead of the whole file. It is the one defect that keeps P15-Q3.1 from staying true once
it reads true, it would have spared this run 64 re-records, and it sits inside
`contracts/` and `scripts/`, within the grant.
