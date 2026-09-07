# Witness record: fresh participation vertical slice (P15-X1)

```witness
standing_supported  WITNESSED
subject  fresh-participation
revision  26b1887e84357124c8e99f42382d064ffbeccf8c
pass  7
```

Seven passes by the same role, different commits. Pass 7 (commit `26b1887`) is current and owns
the declaration above. Pass 6 (commit `571e936`), pass 5 (commit `219686d`), pass 4 (commit
`0cf5a57`), pass 3 (commit `8fd7716`), pass 2 (commit `161d559`) and pass 1 (commit `d40d61f`)
follow it unchanged as history.

No `*_status` field in `STATUS.yaml` names this subject, so `scripts/sov_standing.py` does not
read this file. The subject is the one `ITEM` member under
`custody:phase-1-5/fresh-participation` in `contracts/custodies/phase-1-5.json`:
`scripts/sov_fresh.py`, stage `VERTICAL_SLICE`, standing `WITNESSED` since `5f3fd67`,
`work_state` `LANDED` since `ed17795`, `stage_observed_by` naming pass 6 at `571e936`.

## Pass 7: commit 26b1887 (2026-09-07)

Verdict: **REPRODUCED** for the journal's custody at this revision: the committed export is
byte-identical to what pass 6 read, replays to the head pass 6 held outside it, restores into
an empty node with that head, and a truncated copy is refused once that head is supplied and
now leaves no store behind. The gate at this revision refuses every case pass 6 said it should
and did not (F44 to F47), and each repair is pinned by a test a mutant fails. **DISSENT** on
the standing's binding: the member carries two revisions in one record (`0cf5a57` in its
note, `571e936` in `stage_observed_by`), and neither is a revision whose gate bytes are the
ones that landed; three files inside the claim changed at `ed17795` and no pass had read them
until this one (F53). The first packet is again the bytes pass 5 read, and those bytes still
embed a 31-entry journal beside its own head (F43, disposition below).

Scope: journal custody and the standing's binding to current bytes, at the launcher's
direction. The office and the run were witnessed at pass 5; the instrument at pass 4. The new
member under `custody:phase-1-5/discovery-and-reuse` (`scripts/sov_reuse.py`, `BUILT`,
`PRESENTED`) is not this subject and is not witnessed here; its reader was run once, confined
to a scratch copy, because it measures the same drift this pass measures.

Claim under observation: the standing pass 6 declared, as its receipt states it in
`standing_binds.claim`, read against the bytes now at `26b1887`. No builder report was taken
as evidence. `reports/2026-09-06-fresh-participation-slice.md` sits in the drift set, so its
diff since `571e936` was seen in `git diff` before any command ran; nothing below is taken
from it. The member's note in `contracts/custodies/phase-1-5.json` was read for its words,
not its conclusions.

Subject frozen: commit `26b1887e84357124c8e99f42382d064ffbeccf8c` on
`claude/sovereign-phase-1-5-5uzffu`; its first parent `ee60801` is `origin/main`, the merge of
PR #218, which carries `571e936`, `ed17795` and `358303b`. `git rev-parse HEAD` read the commit
and `git status --porcelain` was empty before and after every command up to this pass's two
writes. At `05:01:02Z`, after both writes and during the checks that followed them, another
session deposited `witness/discovery-and-reuse.md` and
`witness/observations/2026-09-07-discovery-and-reuse-observation.json`, untracked; they are the
other custody member's, were not read, and touch nothing this pass observed (`CLAUDE.md`, trap
T6). There is no node on this host: `.local/node-interface` does not exist (`.gitignore:33`
still names `.local/`). `.local/` holds `candidates/` (a `FROZEN` candidate record for `26b1887`
written at `04:46:58Z`, before this pass began), `console/`, `landing/`, `registrar/` and, from
`04:50:00Z`, `record/` (F54).
Every mutation ran in `git archive 26b1887` unpacked under scratch (`<mut>`); every restore ran
into a scratch directory (`<x>`). The commit changes 8 files (+938/-3) against `ee60801`, none
under `nodes/`, `reports/`, `witness/`, `scripts/sovnode/`, `scripts/sovfresh/` or
`services/`.

Witness: `claude-fable-5-1/sov-witness@2026-09-07`, pass 7 by the same role. `SOV_PRINCIPAL`
was set to `principal:claude-fable-5-1` for every command; that registry entry is
`UNVERIFIED` and grants nothing, and no command here needed a grant. This participant did not
build, edit, stage or commit anything under the subject and read no transcript. The only files
it wrote are this section, the header block and the two paragraphs above that name the current
pass, and `witness/observations/2026-09-07-fresh-participation-observation-7.json`, all after
every command under `Verified` had returned. Passes 6 to 1 are carried unchanged: the bytes
from `## Pass 6` to the end of this file are identical to `git show 26b1887:witness/fresh-participation.md`
from the same heading (sha256 `6b9f81b7...` over 133849 bytes), and the six prior receipts
digest as they do at `26b1887`.

### Drift from pass 6, address by address

Pass 6 recorded 26 addresses with digests at `571e936`. At `26b1887`, 18 hold the same bytes
and 8 do not. The reuse reader in the scratch copy (`sov_reuse.py run`, which reads the pass-6
receipt and digests each address itself) names the same eight. Whether a change is inside the
claim is read against `standing_binds.claim` in the pass-6 receipt.

| Address | `571e936` | `26b1887` | Changed at | Inside the claim |
| --- | --- | --- | --- | --- |
| `scripts/sovnode/journal.py` | `e16de79c` | `6ef8bcc2` | `ed17795` | Yes. The gate the claim describes. Adds: one head per node, directory name against the entries' `node_id` and the node registry, every `entry_id`/`receipt_id` a report mentions must resolve, cited entry count against the export, `BrokenChain` caught as a named defect, a refused restore removes the store it created. Nothing the positive path does changed |
| `scripts/tests/test_sov_node_journal.py` | `2c740266` | `7afcab68` | `ed17795` | Yes. "The eight journal tests" are now thirteen; the F48 assertion tightened from "no non-genesis head" to "no `record/` directory" |
| `scripts/sovverify/commissioning.py` | `b4df3500` | `a124a998` | `ed17795` | Yes, the check's declared reach: `sov_node.py` and `custody.py` added to what check 52 observes (F51). The command is unchanged |
| `nodes/README.md` | `f33a45ae` | `456d3dda` | `ed17795` | Yes, as prose: "a node has one head, so one export sits under each node", now what the gate enforces (F45) |
| `contracts/custodies/phase-1-5.json` | `994dcb7a` | `3b6f0aca` | `ed17795`, `26b1887` | It is the field the standing binds (`members[0]`): `work_state` `PRESENTED` to `LANDED` and `stage_observed_by` to pass 6 words at `ed17795`; the discovery-and-reuse member added at `26b1887`. Inside the binding, outside the behavior (F53) |
| `contracts/principals.json` | `cec549f6` | `2f672d7a` | `358303b` | No. Adds `principal:claude-fable-5-1`, `UNVERIFIED`; the probe still runs as `principal:claude-fable-5`, and the node's journal grants the new name nothing (the reuse reader's run is refused `SESSION_IDENTITY_REQUIRED` for it, as the node decides) |
| `reports/2026-09-06-fresh-participation-slice.md` | `b13c6a16` | `90524cad` | `ed17795` | No. The builder's report; a description of the artifact, not the artifact |
| `reports/observations/2026-09-06-fresh-participation-live-node.json` | `3c9b8407` | `1882e38c` | `ed17795` | Yes, the third artifact of the journal-custody claim: now equal to `219686d` byte for byte, so "kept as the bytes pass 5 read" is true (F43). Those bytes embed `journal_export` of 31 entries beside `record_head_after_run` `032377e0...`; the 31 are an exact prefix of the 85-entry export (entry 31's digest is `032377e0...`) |

Changed since `571e936` at addresses pass 6 did not record: `contracts/verification-budget.json`
(`fresh participation slice` ceiling 1.5s to 3.0s, F50); `docs/documentation.html` (not read);
`scripts/sov_reuse.py`, `scripts/sovreuse/` and `scripts/tests/test_sov_reuse.py` (new, the
other custody's member). The 18 unchanged include `scripts/sov_fresh.py`, `scripts/sov_node.py`,
both `sovfresh` modules, `test_sov_fresh.py`, all four Record Service modules, the export, the
node registry, the publication surface, the second self-report and the five prior receipts.

### The head held outside the export

On this host there is no store to read it from. The head has exactly one holder here: pass 6's
record and receipt, whose bytes at `26b1887` are what `ed17795` committed (`git diff ed17795
26b1887 -- witness/fresh-participation.md` empty; `observation-6.json` `7416bd3f...` at both).
Read from them: `23d3b48086becd541d6054d78185f730e41a10054848ad4f654191315f87b342`, 85 entries.

The committed export reaches exactly that head, by three paths that share no code with the
record: `verify-export --expect-head` exits 0 with 85 entries; the journals gate prints it;
`restore-journal --expect-head` into an empty scratch store restores 85 entries whose last row
digests to it. Against `032377e0...` (entry 31, the first packet's embedded head) and against a
60-entry truncation (head `94aafd47...`) the verifier refuses. The export carries 7 entries with
`granted_by` `principal:bdo` in two acts (`recorded_at` 1788704979 and 1788706269), every
payload `node_id` is `node:local`, and its top-level keys are still `entries`, `entry_count`,
`export_schema`, `head_digest` (F47, product half).

What "outside" means here is narrower than at pass 6: not a gitignored store on the builder's
host, but a file on the builder's branch that this pass can only check for consistency with the
export. A host that holds no node cannot add a second holder; it can say the two files agree,
and they do (J12).

### Standing supported

`WITNESSED`, declared in the block above, for the member at `26b1887`, with the claim pass 6
bound and this pass re-measured against the bytes now at every address inside it: the export
is the node's journal to the head held outside it; `restore-journal` refuses a populated store
and a truncated export once that head is given, removes the store it created on refusal, and
into an empty store carries 85 entries and 7 grants; `journals` replays every export under
`nodes/` and refuses a misnamed export, a second head for one node, an export whose directory
names a node its entries do not or the registry does not, an edited count, an edited or
fabricated entry by name rather than by traceback, a citation of a wrong head, of a wrong entry
count, of an entry or receipt id anywhere in the report that the export does not hold, or of a
file outside `nodes/`; `selfcheck` and the thirteen journal tests fail under six mutants
(verifier ignoring the outside head; gate dropping the one-head rule, the whole-report id
walk, the node-identity comparison, the `BrokenChain` catch; restore keeping its store on
refusal).

For the journal-custody claim as pass 6 stated it: all three artifacts are now as described,
with one residual. The first packet is the bytes pass 5 read; being those bytes, it embeds a
31-entry prefix of the journal with its own head, so the journal is still committed twice (in
part), and the shape pass 5 called F40 persists by the builder's chosen repair rather than by
accident. That is recorded, not held against the standing.

What this record does not support is unchanged: nothing authenticates who passed the name
`principal:bdo` (F35, F52, J4); no clause verdict moves; `custody:phase-1-5/fresh-participation`
reads `PROPOSED` and P15-X1 stays unearned. The member's `work_state` `LANDED` is true on the
current line: `571e936` and `ed17795` are ancestors of `origin/main` through `ee60801`.

The words this record wants the member to carry, if the builder or lander moves it:
`stage_observed_by` `claude-fable-5-1/sov-witness@2026-09-07 pass 7 at 26b1887
(witness/fresh-participation.md; witness/observations/2026-09-07-fresh-participation-observation-7.json)`.
F53 and F54 are defects owed inside the concern; neither is a precondition of this standing.
This is an observation. It ratifies nothing.

### Verified

Commands run from the repository root at the commit above with `SOV_PRINCIPAL` set. Exit codes
are the process's own. `<x>` is a directory under scratch; `<mut>` is `git archive 26b1887`
unpacked under scratch, mutated there, never copied back; `H` is the head above; `E` is
`nodes/node-local/journal/23d3b48086be.json`.

| Command | Exit | Reading |
| --- | --- | --- |
| `git rev-parse HEAD`; `git status --porcelain`; `git rev-parse origin/main HEAD^`; `git diff --stat ee60801 26b1887`; `git check-ignore -v .local/node-interface`; `ls .local/node-interface` | 0; 0; 0; 0; 0; 2 | `26b1887e...`; empty before and after every command; both `ee608015...`; 8 files +938/-3; `.gitignore:33`; no such directory |
| `git merge-base --is-ancestor 571e936 ee60801`; the same for `ed17795`; `git log --format='%h %p' -1 ee60801` | 0; 0; 0 | both ancestors of `origin/main`; `ee60801` is the merge of `4b0bc1d` and `358303b` |
| sha256 of the 26 addresses in `observation-6.json` against the digests recorded there | - | 18 same, 8 drifted, as tabled above |
| `python scripts/sov_node.py journals` | 0 | `PASS: 1 node journal export(s) replay to their heads and every citation resolves` |
| `python -m soveraeign_record_service.cli verify-export --export E --expect-head H`; without a head; `--expect-head 032377e0...` | 0; 0; 2 | 85 entries, `verified: true`; the same; `REFUSED` "export reaches 23d3b480... but the head held outside it is 032377e0...; entries are missing from the end", `reason_code: MISSING_PRECONDITION`, though the export is longer than the head asked for (F49). Each invocation created or opened `.local/record/record-service.sqlite3` (F54) |
| E read: entry count, head, kinds, `granted_by`, `node_id`, top-level keys; the first packet's 31 embedded entries against E | - | 85 = 85, `23d3b480...`, kinds `EVENT` 62 and `RECEIPT` 23; 7 entries carry `granted_by: principal:bdo`, at seq 1, 3, 5, 7 (first act) and 55, 57, 59 (second act); every `node_id` `node:local`; no node field; entries 1-31 identical in `entry_id` and `entry_digest`, entry 31 `032377e0...` |
| `sov_node.py restore-journal --export E --node-state <x>/restored --expect-head H`; `sqlite3` read of the result | 0 | `restored 85 entries`; 85 rows, last `entry_digest` `23d3b480...` |
| E truncated to 60 entries (head `94aafd47...`); `restore-journal ... --node-state <x>/trunc --expect-head H`; `find <x>/trunc` | 1 | `REFUSED TruncatedExport: export reaches 94aafd47... but the head held outside it is 23d3b480...; entries are missing from the end`; `<x>/trunc` is an empty directory, no `record/` (F48 repaired) |
| the same truncated copy without `--expect-head`; `restore-journal --export E --node-state <x>/restored --expect-head H` (populated) | 0; 1 | `restored 60 entries`, as declared; `REFUSED RestoreRefused: .../restored/record already holds a journal` |
| `python scripts/sov_fresh.py selfcheck` | 0 | `PASS: fresh participation slice closes on the positive variant, 3 defeating variants each fail their own predicates, and the office carries across an export and restore`; tree clean after |
| `python -m unittest scripts.tests.test_sov_fresh scripts.tests.test_sov_node_journal` | 0 | `Ran 38 tests OK` (33 at pass 6) |
| `python scripts/verify.py` (stdout to a file; the verdict is the exit code and the `PASS: 52 checks` line) | 0 | `PASS: 52 checks in 23.161s wall`; `fresh participation slice` PASS 2.787s under its 3.0s ceiling; `node journal custody` PASS 0.126s; `DEBT: no wall-clock grade`; `BUDGET DEBT: 9 check(s) over ceiling`, none of them this subject's. The `FAIL` lines are planted oracle-control output |
| `python scripts/lint.py` | 0 | `PASS: repository hygiene (1204 text files, 562 Python modules, 10 named debt)` |
| `python scripts/sov_witness_layer.py records`; `python scripts/sov_standing.py` | 0; 0 | `12 witness receipt(s) graded, 0 unusable, 12 stale against their subject`; `observation-6.json` `STALE_SUBJECT` naming the same 8 addresses; `PASS: 1 standing claim(s)` (this subject has no `STATUS.yaml` field) |
| `python scripts/sov_active_phase_progress.py` | 0 | prints nothing: the module has no entry point and is graded as verify's `phase progress floor`, which passed |
| `<mut>` D3: E's 60-entry truncation beside it as `94aafd47b108.json` | 1 | `nodes/node-local: a node has one head; found 2 exports` (F45 repaired) |
| `<mut>` D6: `live_run.node.own.receipt_id` set to `entry_not_in_export` | 1 | `names entries absent from nodes/node-local/journal/23d3b48086be.json: entry_not_in_export` (F44 repaired) |
| `<mut>` D4: entry 5 `granted_by` edited; D10: a fabricated 86th entry | 1; 1 | `entry 4 digest does not match its contents`; `entry 85 digest does not match its contents`; then the report's citation fails as `not a verified export under nodes/`; no traceback (F46 repaired) |
| `<mut>` D5: E copied to `nodes/node-other/journal/` | 1 | `entries name node node:local, the directory names node:other`; `node:other is not in the node registry` (F47 repaired, repository half) |
| `<mut>` D9: `entry_count` 84; D11: the report's `journal.entries` 84 | 1; 1 | `declared entry count does not match the entries carried`; `cites 84 entries, the export carries 85` |
| `<mut>` m1: `custody.verify_export` skips `expected_head`; the journal tests; `selfcheck` | 1; 1 | `FAILED (failures=1)` the truncation test; `truncated export: restore with the outside head did not refuse` |
| `<mut>` m6: `grade` drops the one-head rule; m7: `_grade_citation` drops `_ids_in`; m8: `restore` keeps its store on refusal; m9: `BrokenChain` no longer caught; m10: node identity not compared; each with the journal tests | 1 each | one named test fails per mutant: `test_a_node_has_one_head`; `test_every_entry_or_receipt_id_a_report_mentions_must_resolve`; `test_a_truncated_export_verifies_alone_and_refuses_against_the_outside_head`; `test_an_edited_entry_is_a_defect_not_a_traceback` (as an error); `test_the_directory_must_name_the_node_the_entries_name`. The archive's `journal.py` and `custody.py` digest as the repository's after restoring |
| `<mut>` `python scripts/sov_reuse.py run --principal principal:claude-fable-5-1 --sessions-dir <x>/sess --json` | 1 | `drifted` names the same 8 addresses; `landing NONE` because the archive has no `.git`; the restored node refuses the principal `SESSION_IDENTITY_REQUIRED` (it holds no grant for that name). Read for its drift list only; the reader itself is not witnessed here |
| CR bytes in the 19 files changed since `571e936`; `ls -la .local/` | 0 | 0 in each; `.local/record/record-service.sqlite3` 24576 bytes, 0 rows, created `04:50:00Z` by the Record CLI (F54); `.local/landing/ledger.ndjson` last line `04:50:57Z` (outside the subject, below) |

### Pass-6 findings, disposition at 26b1887

- **F43 - repaired by restoring the `219686d` bytes; residual.** The statement is now true.
  Being those bytes, the first packet embeds 31 entries and `record_head_after_run` inside
  the file it vouches for, the shape pass 5 named F40. The gate leaves it alone (no `journal`
  dict). The second packet's `supersedes` text ("it embedded the journal, which this file does
  not") is accurate.
- **F44 - repaired.** `_ids_in` walks the whole report for `entry_id` and `receipt_id`; D6
  refused; m7 caught. `grant_id` is not in `ID_KEYS`; the nine `cited_entries` still cover the
  grant ids the report leans on (measured at pass 6, export unchanged).
- **F45 - repaired.** One head per node; D3 refused; m6 caught; `nodes/README.md` says so.
- **F46 - repaired.** `BrokenChain` is caught and named; D4 and D10 refused; m9 caught.
- **F47 - repaired in the repository half.** Directory against the entries' `node_id` and the
  registry; D5 refused; m10 caught. The export still has no node field (product half).
- **F48 - repaired.** A refused restore removes the store it created; the state directory it
  was asked for remains, empty. m8 caught.
- **F49 - reproduced, residual (product).** `cli.py` unchanged; the `TruncatedExport` branch is
  still unreachable and the message still says "missing from the end" for a longer export.
- **F50 - closed by the contract, not by speed.** The ceiling moved from 1.5s to 3.0s at
  `ed17795`; the check measured 2.787s here (3.861s at pass 6 on another host).
- **F51 - repaired.** Check 52 declares `scripts/sov_node.py` and `custody.py`.
- **F52 - unchanged, residual (record).** The export is byte-identical; duplicate grants stand.
- **F35, F39, F41, F42 - unchanged, residual.**

### New findings

- **F53 - LOW, defect (the binding names two revisions and the wrong one).
  `contracts/custodies/phase-1-5.json` `members[0]` `stage_observed_by` and `note`.** The
  `note` still reads "The witnessed standing binds to 0cf5a57 and to the instrument claim"
  while `stage_observed_by` names pass 6 at `571e936`, with words pass 6 did not ask for
  ("instrument and custody commands"; "first supported at pass 4, 0cf5a57"). Neither revision
  holds the gate bytes that landed: `journal.py`, its tests and `commissioning.py` changed at
  `ed17795`, and this is the first pass to read them. A reader following the member to the
  receipt finds digests that disagree with the tree at eight addresses, three of them inside
  the claim, and nothing in the member saying so. Repair: one revision in the member, the one
  the current pass read, and the note's sentence brought to it.
- **F54 - LOW, residual (product, predates the subject; a check that writes state).
  `services/record/src/soveraeign_record_service/cli.py:37,248`.** `main` opens
  `RecordService(args.root)` before dispatch, default `.local/record`, for every command.
  `verify-export` reads one file and needs no store; run from the repository root it created
  `.local/record/record-service.sqlite3` (24576 bytes, 0 rows, sha256 `d9a182b2...`) on this
  host at `04:50:00Z`, the same shape F48 had. `sov_node.py journals` does not share the
  defect: it calls `custody.verify_export` on the document and opens no store. Pass 6 ran the
  same CLI command and did not record this; whether `.local/record` already existed there is
  not knowable from here.

### Outside the subject

`scripts/tests/test_sov_land.py`, run by verify's `repository tooling tests`, appends fixture
landings (`grant:test`, `merge_commit` `c9073e51...`, which is not an object in this repository)
to `<root>/.local/landing/ledger.ndjson`; under the scratch archive one run wrote 6 lines, and
in the repository the live ledger's last line is stamped `04:50:57Z`, during this pass's verify
run (48 lines now). That is the landing loop's concern, not this one's; it is recorded here for
the launcher to route and is not a finding against this subject.

### What a reader on another host can verify from the export alone

As pass 6 stated, with one change: without a node store, the head written in this record and
pass 6's is the only holder a reader on this host meets, and this pass could confirm agreement
between it and the export, not custody of it.

### Conditions for a later pass

None on this standing. F53 is owed inside the concern; a pass over the commit that repairs it
reads the member's words. A pass on a host that holds the node reads the head from the store
again.

### Judgement items (questions, not the witness's to answer)

- J1 to J3 carried from pass 1; J5 and J6 from pass 3; J7 from pass 4; J4 as pass 5 split it;
  J10 and J11 from pass 6.
- J12. On a host with no node store, the outside head has one holder, the witness record on the
  builder's branch, and a pass there can only show the record and the export agree. Is that a
  custody reading the clause accepts, or does P15-X1's "survives the participant's session"
  need a holder that is neither the export nor a file beside it on the same branch? This
  sharpens J10; it does not answer it.

### Uncovered

- `ed17795`'s `docs/documentation.html`: `sov_docs.py check` passed inside verify; not read.
- `scripts/sov_reuse.py`, `scripts/sovreuse/` and `test_sov_reuse.py`: read for what they read
  about this subject; their own claim is another member's and was not witnessed.
- The Console, Gateway and Record suites were not rerun outside verify (no service file
  changed since `571e936`).
- The office and the run: not re-exercised beyond `selfcheck` and the restored-node probe
  inside the reuse reader; pass 5's readings stand for them.
- Bdo's direction, for either act: no transcript was read and none is in the record.
- No network, no `gh`, no ruleset query.

## Pass 6: commit 571e936 (2026-09-06)

Verdict: **REPRODUCED** for the journal's custody: the committed export is the live node's
journal to the head this witness holds outside it, it restores into an empty node that then
admits the granted operator without issuing a grant, and a truncated copy is refused once that
head is supplied. **DISSENT** from the claim that the first packet is kept as the bytes pass 5
read: it was rewritten at `ed6a4f4`, still embeds the whole journal, and still holds its own
head. The gate `sov_node.py journals` checks what it says it checks and no more; where it reads
a declaration it could have measured is recorded below (F44, F45).

Scope: journal custody only, at the launcher's direction. The office and the run were witnessed
at pass 5; what `ed6a4f4` changed on that surface is read here only where a pass-5 finding's
disposition depends on it.

Claim under observation, as the builder states it (`reports/2026-09-06-fresh-participation-slice.md`,
"The journal, separated from the report"): the packet is three artifacts. The node's journal is
the Record Service's own export at `nodes/node-local/journal/23d3b48086be.json`, written by
`python scripts/sov_node.py export-journal`, named by the head it replays to, and brought back
into an empty node by `restore-journal` so the office is opened once and the history stays one
chain. The self-report `reports/observations/2026-09-06-fresh-participation-live-node-2.json`
cites the export by address, head and nine entry ids and embeds no journal; the first packet is
kept as the bytes pass 5 read. The outside head is the witness's; `python scripts/sov_node.py
journals` runs inside verify as check 52, refuses a misnamed export or an unresolved citation,
and cannot detect truncation. `selfcheck` proves export, restore, entry as the granted operator
with no grant issued, and refusal of a truncated export once an outside head is supplied. The
report section was read before any command ran, because the launcher quoted it; nothing below
is taken from it.

Subject frozen: commit `571e936c733ad399aa0cb79d620f019302e6c045` on
`claude/phase-2-citizen-mechanics-inrozu`, plus the node at `.local/node-interface` (gitignored,
`.gitignore:33`). `git status --porcelain` was empty before and after every command and `git
rev-parse HEAD` read the commit throughout. Before any command ran, the node state was copied
byte for byte into this witness's scratch directory: `record/record-service.sqlite3`
`565d3be8cf65e878dcfa38e08e36906714dd9856a4201a59025011ed94a0c822`, `office-acts.ndjson`
`653f73a7...`, `office-opened.json` `09ee6afe...` (unchanged since pass 5),
`asset/asset-service.sqlite3` `7a55b640...` (unchanged since pass 5). No command in this pass
wrote to the live node; its four files digest the same after the last command as before the
first. Every run that needed a node ran against a restored copy under scratch. The commit
changes 15 files (+2843/-18); `conformance/` and `services/` are unchanged since `219686d`.
Between `219686d` and this commit sits `ed6a4f4`, which no witness pass has read; it is inside
the frozen subject and is named below wherever a reading depends on it.

Witness: `claude-fable-5-1/sov-witness@2026-09-06`, pass 6 by the same role, launched from the
session named in `office-acts.ndjson` `directed_in` (F42 holds). This participant did not
build, edit, stage or commit anything under the subject and read no transcript. The only files
it wrote are this section, the header block and the paragraph above that name the current pass,
and `witness/observations/2026-09-06-fresh-participation-observation-6.json`, all after every
command under `Verified` had returned. Passes 5 to 1 are carried unchanged: the bytes from
`## Pass 5` to the end of this file are identical to `git show 571e936:witness/fresh-participation.md`
from the same heading (sha256 `93c4224c...` over that span), and the five prior receipts
digest as they do at `571e936`.

### The head held outside the export

Read from the byte copy of the live node, by `sqlite3` over the `journal` table ordered by
`seq`, independently of every file under `nodes/` and `reports/`:

- entries: 85; `prev_digest` chain continuous from `0000...` with every row on
  `soveraeign-record-chain/v3`;
- head (the last row's `entry_digest`):
  `23d3b48086becd541d6054d78185f730e41a10054848ad4f654191315f87b342`.

The committed export reaches exactly that head. `verify-export --expect-head <that head>` exits
0 with 85 entries; every one of the 85 entries is identical to the copy's row in `entry_id`,
`kind`, `subject`, `actor`, `payload`, `recorded_at`, `prev_digest` and `entry_digest`; and
`export-journal` run against a second byte copy writes a file whose sha256
(`b8805d23ce21ee352b7f0ea5796d7c5bb4ea8fdee5eb4e38ab1f194bcd5cfa1e`) equals the committed
export's. Against pass 5's post-run head `0e357ea0...` (entry 54) the verifier refuses.

What "outside" means here: outside the export file and outside every committed file, not
outside the host or the builder's session. The head was read from a gitignored SQLite file on
the same machine the builder's session writes; a session that rewrote the node and the export
together would present a consistent pair to a later witness. The head is now written in this
record and its receipt, which are on the same branch the builder commits to.

### Standing supported

`WITNESSED`, declared in the block above, for the member at `571e936`, with pass 5's scope
extended by what this commit adds and this pass measured: `export-journal` writes the Record
Service's export of a node's journal under the head it replays to; `restore-journal` refuses a
populated store and a truncated export once an outside head is given, and into an empty store
carries the office so that `run --node-state` on the restored node admits the granted operator,
is refused three times for the reasons the node declares, grades P15-Q1.1 to Q1.3 as holding on
identities read from the restored journal, and issues no grant (7 `authority-grant` entries
before and after); `journals` replays every export under `nodes/` and refuses a misnamed export,
an edited count, a citation of a wrong head, of an absent entry, or of a file outside `nodes/`;
`selfcheck` and the eight new tests fail when the verifier stops honouring the outside head or
the gate stops comparing heads (two mutants).

For the journal-custody claim as the builder states it: two of its three artifacts are as
described. The export is the live node's journal to the outside head; the second self-report
cites it by address, head and nine ids that resolve to the entries it says they are, and embeds
nothing. The third statement, that the first packet is kept as the bytes pass 5 read, is false
(F43), and with it the claim that the journal has left the report: the journal is committed
twice, once as the export and once inside the first packet with its head beside it.

What this record does not support is unchanged from pass 5: nothing in the node, the export,
the gate, or either receipt file authenticates who passed the name `principal:bdo`. The export
carries seven grants with `granted_by: principal:bdo`, issued by two acts (14:29:39Z and
14:51:09Z); the gate reads none of them and verifies only that each entry's digest matches its
own contents. P15-X1 stays `NOT_EARNED`; no clause verdict moves on a witness reading.

The words this record wants the member to carry, if the builder or lander moves it:
`stage_observed_by` `claude-fable-5-1/sov-witness@2026-09-06 pass 6 at 571e936
(witness/fresh-participation.md; witness/observations/2026-09-06-fresh-participation-observation-6.json)`.
F43 to F48 are defects owed inside the concern; none changes what the positive path does, and
none is a precondition of this standing. This is an observation. It ratifies nothing.

### Verified

Commands run from the repository root at the commit above. Exit codes are the process's own.
`<copy>` and `<copy2>` are byte copies of `.local/node-interface` under scratch; `<x>` is a
directory under scratch; `<mut>` is `git archive 571e936` unpacked into scratch, mutated there,
never copied back; `H` is the outside head above; `E` is
`nodes/node-local/journal/23d3b48086be.json`.

| Command | Exit | Reading |
| --- | --- | --- |
| `git rev-parse HEAD`; `git status --porcelain`; `git show --stat 571e936`; `git diff --stat 219686d HEAD -- conformance/ services/`; `git check-ignore -v .local/node-interface` | 0; 0; 0; 0; 0 | `571e936c...`; empty before and after every command; 15 files +2843/-18; nothing under either; `.gitignore:33` |
| `cp -a .local/node-interface <copy>`; `sha256sum` over its four files; `sqlite3` read of `journal` | 0 | 85 entries, head `23d3b480...`; digests as above; entries 55-60 are three grants issued at `14:51:09Z` under `principal:bdo` (`open:session`, `close:session`, `read:registry`) that pass 5's 54-entry post-copy did not hold; entries 84-85 close `session_48f90d77...` under `grant_119ebb48...` |
| `python scripts/sov_node.py journals` | 0 | `PASS: 1 node journal export(s) replay to their heads and every citation resolves` |
| `python -m soveraeign_record_service.cli verify-export --export E`; `... --expect-head H`; `... --expect-head 0e357ea0...` | 0; 0; 2 | 85 entries, head `23d3b480...`, `verified: true`; the same; `REFUSED` "export reaches 23d3b480... but the head held outside it is 0e357ea0...; entries are missing from the end", `reason_code: MISSING_PRECONDITION` (F49) |
| export E against `<copy>` journal, entry by entry; `sov_node.py export-journal --node-state <copy2> --out-dir <x>` | -; 0 | 85 of 85 identical in every field; the re-export is byte-identical to E (`b8805d23...`) |
| E: `authority-grant` entries and their `granted_by`; `node_id` values; top-level keys | - | 7 grants, all `granted_by: principal:bdo`; every payload `node_id` is `node:local`; keys `entries`, `entry_count`, `export_schema`, `head_digest` and no node field (F47) |
| the second self-report's nine `cited_entries` read out of E | - | seq 5 `grant_3807...` `open:session` and seq 7 `grant_6ab7...` `read:registry`, the first act; seq 55 `grant_fe49...` `open:session`, seq 57 `grant_119e...` `close:session`, seq 59 `grant_1453...` `read:registry`, the second act, all `granted_by: principal:bdo`; seq 68 `registry.resolve` `COMMITTED` receipt (subject `sov://asset/ingest-asset`, F41); seq 80 `gateway.refuse-request` `check-authority` `AUTHORITY_REFUSED`; seq 72 and 75 `gateway.refuse-request` `check-attribution` `ACTOR_ATTRIBUTION_MISMATCH` (own session with a foreign session id; `another-participant` on the own session). The `live_run` receipt ids and Q1.3 `grant_6ab7...` are all among the nine |
| `sha256sum` of `reports/observations/2026-09-06-fresh-participation-live-node.json` at `219686d`, `ed6a4f4`, `571e936`; its top-level keys at `219686d` and `571e936` | 0 | `1882e38c...`; `3c9b8407...`; `3c9b8407...`. Rewritten at `ed6a4f4` (+1685/-113): `office_opened` became `office_acts`, `earlier_live_run_at_219686d` added, `journal_export` now 85 entries with `record_head_after_run` `23d3b480...` inside the same file (F43) |
| `sov_node.py restore-journal --export E --node-state <x>/restored --expect-head H` | 0 | `restored 85 entries`; 7 grants; head `23d3b480...` |
| `sov_fresh.py run --principal principal:claude-fable-5 --node-state <x>/restored --json` | 0 | `passed: true`; `issuer: null`; `root_principal: principal:bdo`; own `COMMITTED`; `beyond_the_grant` `check-authority` `AUTHORITY_REFUSED`; `foreign_session` and `other_actor_on_this_session` `check-attribution` `ACTOR_ATTRIBUTION_MISMATCH`; Q1.3 `grant_6ab7d1d0a99e419e` / `session_78e9b5d7...`; Q1.2 `survives_session: true`; trace `console session ... closed`; journal 85 to 110 entries, grants 7 before and 7 after |
| E truncated to 60 entries (head `94aafd47...`, the second act's last receipt); `restore-journal ... --node-state <x>/trunc --expect-head H`; `find <x>/trunc` | 1 | `REFUSED TruncatedExport: export reaches 94aafd47... but the head held outside it is 23d3b480...; entries are missing from the end`; `<x>/trunc/record/record-service.sqlite3` exists, 24576 bytes, 0 entries, head genesis (F48) |
| the same truncated copy without `--expect-head` | 0 | `restored 60 entries`: a truncation restores when no outside head is given, as declared |
| `restore-journal --export E --node-state <x>/wrong --expect-head 0e357ea0...` | 1 | `TruncatedExport ... entries are missing from the end`, though the export is longer than the head asked for (F49); empty store left behind (F48) |
| `restore-journal --export E --node-state <x>/restored --expect-head H` (populated) | 1 | `REFUSED RestoreRefused: .../restored/record already holds a journal`; journal unchanged at 110 |
| `python -m soveraeign_record_service.cli restore-journal --export <trunc> --expect-head H` | 2 | `unrecognized arguments: --expect-head`: the Record CLI's own restore takes no outside head (F49) |
| `python scripts/sov_fresh.py selfcheck` | 0 | `PASS: ... 3 defeating variants each fail their own predicates, and the office carries across an export and restore` |
| `python -m unittest scripts.tests.test_sov_node_journal scripts.tests.test_sov_fresh` | 0 | `Ran 33 tests OK` |
| `python scripts/verify.py` (stdout to a file; the verdict is the exit code and the `PASS: 52 checks` line) | 0 | `PASS: 52 checks in 21.107s wall`; `node journal custody` PASS 0.189s; `DEBT: no wall-clock grade`; `BUDGET DEBT: 11 check(s) over ceiling`; `fresh participation slice: 3.861s over its 1.500s ceiling` (F50). The `FAIL` lines are planted tooling self-test output |
| `python scripts/lint.py` | 0 | `PASS: repository hygiene (1196 text files, 555 Python modules, 10 named debt)` |
| `python scripts/sov_publication.py` at `571e936`; the same at `219686d` in a scratch clone | 0; 0 | `FAIL: 58 declared path(s), 20 finding(s), 19 held by sov, 1 held by the owner`; at `219686d` `57 declared, 21 findings`. The one finding that closed is `ENTRYPOINT_UNINDEXED sov_fresh.py`; `nodes` is the added path and raises no finding; the 20 that remain (18 `ENTRYPOINT_UNINDEXED`, the owner's `README.md->LICENSE` route gap, and one more) predate the subject. The default command reports and exits 0 (`sov_publication.py:290`); `check` would exit 1 |
| `<mut>` D1: second self-report cites head `0e357ea0...` | 1 | `cites head 0e357ea0b2a4 but ... replays to 23d3b48086be` |
| `<mut>` D2: E renamed `0e357ea0b2a4.json` | 1 | `replays to 23d3b48086be, filename says 0e357ea0b2a4`; the citation then fails as `not a verified export under nodes/` |
| `<mut>` D3: E's 60-entry truncation written beside it as `94aafd47b108.json`; report re-pointed at it with the cited ids it holds | 0 | `PASS: 2 node journal export(s) replay to their heads and every citation resolves` (F45) |
| `<mut>` D4: entry 5 `granted_by` edited; D10: a fabricated 86th entry appended | 1; 1 | both: uncaught `soveraeign_record_service.errors.BrokenChain` traceback through `journals` (F46) |
| `<mut>` D5: E copied to `nodes/node-other/journal/` | 0 | `PASS: 2 node journal export(s)` (F47) |
| `<mut>` D6: `cited_entries` cut to one id; `live_run.node.own.receipt_id` set to `entry_not_in_export` | 0 | `PASS` (F44) |
| `<mut>` D7: report cites a truncated copy under `reports/observations/`; D9: `entry_count` set to 84 | 1; 1 | `not a verified export under nodes/`; `declared entry count does not match the entries carried` |
| `<mut>` D8: the report's `journal` key renamed, `cited_entries` naming an absent id | 0 | `PASS`: a report without a `journal` dict is left alone, as its test says |
| `<mut>` m1: `custody.verify_export` skips the `expected_head` check; `selfcheck`; the journal tests | 1; 1 | `truncated export: restore with the outside head did not refuse`; `FAILED (failures=1)` `test_a_truncated_export_verifies_alone_and_refuses_against_the_outside_head` |
| `<mut>` m4: `_grade_citation` drops the head comparison; the journal tests | 1 | `FAILED (failures=1)` `test_a_citation_of_an_unknown_export_or_wrong_head_or_missing_entry_fails` |
| `<mut>` m5: `journal.restore` drops its own emptiness guard; the journal tests | 0 | `OK`: `custody.restore` (`custody.py:142`) refuses on its own, so the guard at `journal.py:49` is a duplicate, not an unpinned rule |
| `sov_fresh.py run ... --node-state <x>/restored --variant no-grant`; `open-office --node-state <x>/restored --issuer principal:other ...` | 2; 2 | `REFUSED VARIANT_NOT_ADMITTED: ...` and `REFUSED PROBE_ISSUER_GATE: ...`, no traceback (F34 repaired at `ed6a4f4`) |
| `grep -n "def test" scripts/tests/test_sov_fresh.py` | 0 | `test_open_office_records_every_grant_under_the_issuer` (:228), `test_a_persisted_node_refuses_the_seeding_options` (:265), `test_seeding_options_on_a_persisted_node_refuse_without_a_traceback` (:287) (F33 repaired at `ed6a4f4`; not mutated this pass) |
| CR bytes in the 21 files changed since `219686d`; live node digests after the last command | 0 | 0 in each; the four files digest as the pre-copy |

### Pass-5 findings, disposition at 571e936

- **F33 - repaired at `ed6a4f4`.** Three tests name `open_office` and the persisted-node
  refusals, and `selfcheck` runs `_persisted_cases` and now `_custody_cases`. Present, not
  mutated this pass.
- **F34 - repaired at `ed6a4f4`.** `VARIANT_NOT_ADMITTED` and `PROBE_ISSUER_GATE` are named
  refusals with exit 2; the `AuthorityRefused` catch in `cmd_open_office` is in the diff and was
  not reached this pass (the issuer gate fires first).
- **F35 - reproduced, residual (product).** Seven grants now, two acts, all `granted_by` the
  string `principal:bdo`; nothing new authenticates it.
- **F36 - repaired in shape at `ed6a4f4`, residual.** `office-acts.ndjson` is appended, names
  the registry by path and digest and the journal head before and after, and says it proves
  nothing the journal does not. The pass-5 `office-opened.json` still sits beside it; both are
  free text digested by nothing; the act line records the registry by host-absolute path.
- **F37 - repaired at `ed6a4f4`.** The member note no longer says "which is this node today"
  and calls the direction "a claim of the session's transcript, not of the record" (J8).
- **F38 - repaired at `ed6a4f4`.** The participant closes its own session under `close:session`
  (entries 84-85; the restored run's trace reads `closed`). The two earlier sessions stay
  `OPEN` in the history, as history does.
- **F39, F41, F42 - unchanged, residual.**
- **F40 - moved, not closed.** The design answers it: the gate says it cannot detect
  truncation, and the outside head is held here. But the file pass 5 named still holds the
  journal and its own head (F43), and the gate accepts two heads for one node (F45).

### New findings

Severity names the consequence if the claim were accepted as-is. Defects are the builder's to
repair inside the concern; residuals are recorded and hold nothing.

- **F43 - MEDIUM, defect (a statement about evidence is false).
  `reports/2026-09-06-fresh-participation-slice.md` ("The first packet is kept as the bytes
  pass 5 read"); `reports/observations/2026-09-06-fresh-participation-live-node-2.json`
  `supersedes`; the commit message of `571e936`;
  `reports/observations/2026-09-06-fresh-participation-live-node.json` (whole file).** The
  first packet digests `3c9b8407...` at `571e936` and `1882e38c...` at `219686d`; `ed6a4f4`
  rewrote it (+1685/-113) with `office_acts`, `earlier_live_run_at_219686d`, and a
  `journal_export` of all 85 entries beside `record_head_after_run` `23d3b480...`. So the
  journal is committed twice, and the shape pass 5 called F40 (the head inside the file it
  vouches for) persists in the file this commit says it kept. Repair: either restore the
  `219686d` bytes if "kept" is meant, or say the packet was rewritten at `ed6a4f4` and strip
  its embedded journal so the export is the one committed copy.
- **F44 - MEDIUM, defect (the gate grades a declared list). `scripts/sovnode/journal.py:94-99`.**
  Only `cited_entries` is resolved. The ids the report actually leans on
  (`live_run.node.own.receipt_id`, the three refusal `receipt_id`s, Q1.3 `grant_id` and
  `session_id`, `office_acts[*].grants[*].entry_id`) and `journal.entries` are not read: D6
  sets `own.receipt_id` to an id that is in no export and passes. Today the nine cited ids
  cover every id the report leans on (measured); the gate does not know that. Repair: resolve
  every `entry_*`, `grant_*` and `session_*` id the report carries, or at least assert the
  cited set covers them.
- **F45 - MEDIUM, defect (README claims one file per node; the gate accepts any number).
  `scripts/sovnode/journal.py:64-65,103-111`; `nodes/README.md:4`.** Every `*/journal/*.json`
  is graded alone. D3: a 60-entry truncation of E named by its own head sits beside E, both
  pass, and a report re-pointed at the short one passes. A reader of `nodes/node-local/journal/`
  then finds two heads for one node with nothing saying which is current, and check 52 prints
  both as `PASS`. The builder's limit ("cannot detect truncation") is about one file; two
  files of one node are a case the gate could decide (refuse a second head, or require the
  shorter to be an exact prefix of the longer) and does not.
- **F46 - LOW, defect (refusal by traceback). `scripts/sovnode/journal.py:72`;
  `services/record/src/soveraeign_record_service/errors.py:21`.** `_grade_export` catches
  `OSError`, `ValueError` and `RestoreRefused`; `BrokenChain` is a `RuntimeError`, so an edited
  entry or a fabricated one appended under `nodes/` (D4, D10) escapes `journals` as an uncaught
  traceback with exit 1. The check refuses, not through its declared surface; the same shape as
  F34 was.
- **F47 - LOW, defect. `scripts/sovnode/journal.py:64-65`;
  `services/record/src/soveraeign_record_service/custody.py:75-80`.** The export carries no
  node identity at the top level; the directory name `node-local` is compared to nothing, not
  to the `node_id` every payload carries (`node:local`) nor to `self_node` in
  `contracts/fixtures/node-registry.reference.json`. D5: E under `nodes/node-other/journal/`
  passes. Repair inside the concern: derive or check the directory from the entries' `node_id`;
  the product half (a node field in the export) is the Record Service's.
- **F48 - LOW, defect. `scripts/sovnode/journal.py:47-50`;
  `services/record/src/soveraeign_record_service/core.py:63,72`;
  `scripts/tests/test_sov_node_journal.py:72-74`.** `restore` constructs the `RecordService`
  before it checks for a journal, and the constructor creates `record/record-service.sqlite3`
  with its schema. After a refused truncated restore, an empty store (24576 bytes, head genesis)
  is left at the target; the test is written to accept that (`assertFalse(exists and head !=
  GENESIS)`). A second restore into it succeeds, so nothing is lost; but "refuses into an empty
  state" leaves a state.
- **F49 - LOW, residual (product, predates the subject).
  `services/record/src/soveraeign_record_service/cli.py:271-276,236-237`;
  `.../custody.py:129-131`.** `except (ExportRefused, RestoreRefused)` precedes `except
  TruncatedExport`, its subclass, so a head mismatch on `verify-export` returns
  `MISSING_PRECONDITION` and the `DIGEST_MISMATCH` branch is unreachable. The message "entries
  are missing from the end" is emitted for any mismatch, including an export longer than the
  head asked for. The Record CLI's own `restore-journal` takes no `--expect-head`; only
  `sov_node.py restore-journal` does, which `nodes/README.md` correctly names.
- **F50 - LOW, residual (budget, F24 lineage).** `fresh participation slice` reads 3.861s
  against a 1.500s ceiling, up from 1.476s at pass 5, because `selfcheck` now exports,
  restores and runs a third probe. Attributed debt; the total run has no wall-clock grade.
- **F51 - LOW, residual (observation reach). `scripts/sovverify/commissioning.py:32`.** Check
  52 declares that it observes `nodes`, `reports/observations` and `scripts/sovnode/journal.py`;
  the verifier that replays the chain (`custody.py`) and `sov_node.py` are not in the set, so
  the observation record for the check digests neither. The gate's reach is right; the
  observation's declared reach is narrower than what the check reads.
- **F52 - LOW, residual (record).** Entries 55-60 are a second `open-office` act at
  `14:51:09Z`, between pass 5 and `ed6a4f4`, issuing `open:session`, `close:session` and
  `read:registry` under `principal:bdo`; its act line quotes the first act's direction with
  "second act adds close:session" appended. The node now holds duplicate `open:session` and
  `read:registry` grants (`held` picks the first, `grant_6ab7...`, for Q1.3). Whether a second
  direction was given is, like the first, a transcript claim (F35, J4).

### What a reader on another host can verify from the export alone

Can: that the 85-entry export is an unbroken chain reaching `23d3b480...`; that within it
`principal:bdo` is root issuer by genesis and issued seven grants to `principal:claude-fable-5`
in two acts; that three sessions opened under `open:session` grants and one closed; that the
crossings carry request, attribution, authority and receipt entries with the outcomes the second
self-report names, and that its nine cited ids are those entries; that `restore-journal` with
the head written here brings the node back and admits the operator without a grant. Cannot:
that the export is complete without the head written here; that this record's head was not
written by the same hand as the export (both live on one branch); that anyone but the builder's
process typed `principal:bdo`; that either direction was given.

### Conditions for a later pass

None on this standing. F43 to F48 are owed inside the concern; a pass over the commit that
repairs them reads that commit and, for F43, compares the first packet to `219686d` again.

### Judgement items (questions, not the witness's to answer)

- J1 to J3 carried from pass 1; J5 and J6 from pass 3; J7 from pass 4; J4 as pass 5 split it.
- J8, disposition: repaired at `ed6a4f4` (F37); no question remains.
- J9, disposition: answered in design. The gate reads the export and refuses a misnamed file or
  an unresolved citation, and names truncation as what it cannot see; the outside head is the
  witness's and is written here. What remains is narrower and is J10.
- J10. The head that vouches for the export is now held in `witness/`, on the branch the
  builder commits to, read from a gitignored file on the builder's host. Is "outside the
  export" the custody the clause wants, or does the outside head need a holder the builder's
  session cannot write (an owner-held note, another host, or a signed receipt)? This is a
  custody question the witness cannot settle by reading.
- J11. `contracts/publication-surface.json` now classifies `nodes/` as `JOURNAL`, and the
  builder reports that Bdo said yes to an operational node's journal living in the repository.
  That yes is a transcript claim until accepted; acceptance of this packet is what makes an
  export carrying `principal:bdo` grants publishable under the surface policy.

### Uncovered

- `ed6a4f4`'s changes to `scripts/sovfresh/node.py`, `probe.py` and `test_sov_fresh.py` were
  read in diff and exercised only where a pass-5 disposition needed them; the Console, Gateway
  and Record suites were not rerun (no service file changed since `219686d`; verify ran them).
- `docs/documentation.html`: `sov_docs.py check` passed inside verify; the page was not read.
- The `asset/asset-service.sqlite3` and `console/` in the node state were digested, not read.
- Bdo's direction, for either act: no transcript was read and none is in the record.
- No network, no `gh`, no ruleset query.

## Pass 5: commit 219686d (2026-09-06)

Verdict: **REPRODUCED** for the instrument and for the live-node run; **DISSENT** from any
reading of the record as showing that the root seat acted.

Claim under observation, as the builder states it: Bdo, occupying the root seat, directed the
builder's session in his own words ("Open the office on my behalf me and rerun it as evidence and
level with me"); the session ran `python scripts/sov_fresh.py open-office --node-state
.local/node-interface --issuer principal:bdo --operator principal:claude-fable-5 --capability
read:registry=registry:any ...`, which seated `principal:bdo` as that node's root issuer and
recorded two grants to `principal:claude-fable-5` with `granted_by: principal:bdo`; then `run
--principal principal:claude-fable-5 --node-state .local/node-interface` entered the node as
that principal, seeded nothing, and P15-Q1.1 to Q1.3 hold with every identity read from the
node's records. Builder's self-report:
`reports/observations/2026-09-06-fresh-participation-live-node.json` (the office receipt, the
run, and the node's journal export with its `record_head`) and the report section "The office,
opened" in `reports/2026-09-06-fresh-participation-slice.md`. The report section was read after
the export had been verified and the journal read; both are the executor's word and nothing
below is taken from them.

Subject frozen: commit `219686db5328db9d227bc9ac110779952deef5d4` on
`claude/phase-2-citizen-mechanics-inrozu`, plus one piece of runtime state on this host, the node
at `.local/node-interface` (gitignored, `.gitignore:33`). `git status --porcelain` was empty
before and after every command and `git rev-parse HEAD` read the commit throughout. Before any
command ran, the node state was copied byte for byte into this witness's scratch directory:
`record/record-service.sqlite3` `18145070...`, `office-opened.json` `09ee6afe...`,
`asset/asset-service.sqlite3` `7a55b640...`; the journal held 31 entries with head
`032377e0284f53a817779049fca5d4a0a1cc5e637e2aa257953c93383c2d0e82`. Every journal reading below
is from that copy or from a second copy taken after this witness's one run; the live state was
written only by that run. The commit changes 8 files (+1122/-29): the CLI and two probe modules,
the test file, the custody fixture's member note, the built documentation page, the report, and
the packet. `conformance/` is unchanged since `d40d61f`. Between `0cf5a57` and this commit sits
`5f3fd67`, which moved the member to `WITNESSED` on pass 4, raised the custody floor, and added
the two tests that pin F31.

Witness: `claude-fable-5-1/sov-witness@2026-09-06`, pass 5 by the same role, launched from the
session named in `office-opened.json` `directed_in` (F42). This participant did not build, edit,
stage or commit anything under the subject, read no transcript, and took the quoted direction
only as the launcher's task text, which is not evidence. The only files it wrote are this
section, the header block and the two paragraphs above that name the current pass, and
`witness/observations/2026-09-06-fresh-participation-observation-5.json`, all after every
command under `Verified` had returned. Passes 4 to 1 are carried unchanged: the bytes from
`## Pass 4` to the end of this file are identical to `git show 219686d:witness/fresh-participation.md`
from the same heading, and the four prior receipts digest as they do at `219686d`.

### Standing supported

`WITNESSED`, declared in the block above, for the instrument claim at `219686d`, with pass 4's
scope extended by what this commit adds: `open-office` seats the registry's root name as a
persisted node's root issuer and grants one operator, refusing any other name by the probe's own
rule and writing nothing on refusal; `run --node-state` enters a persisted node as the declared
principal, seeds nothing, opens its session under the `open:session` grant the journal holds,
crosses once under the `read:registry` grant, is refused three times by the Gateway for the
reasons the node declares, and grades P15-Q1.1 to Q1.3 on identities read from the journal. The
builder's live run reproduces: this witness's own run against the same node read the same
grant, the same three refusal codes and stages, all three predicates holding, and grew the
journal by exactly the run's 23 entries with no grant among them.

What this record does not support, and dissents from where the report or the custody note
reads otherwise: that the record shows the root seat opened the office. The journal shows a
node whose root issuer is the string `principal:bdo`, seated by the Console's genesis on the
first `console.grant` (entries 0-3, `authority_grant_ids: []`), because the string a session
passed as `--issuer` equalled `root_principal` in `contracts/principals.json`. Nothing in the
node, the probe, the packet, or the direction receipt authenticates who passed it (F35, F36).
The claim "P15-X1 has been observed to hold on a node whose office the root seat opened" is
therefore two claims: the first half, "P15-Q1.1 to Q1.3 hold on a persisted node whose journal
names `principal:bdo` as root issuer and grants `principal:claude-fable-5` under that name", is
`REPORTED` by the builder and reproduced here; the second half, "whose office the root seat
opened", has no path in the record that could distinguish it from a session typing the root's
name, so it is unwitnessable as a record claim and goes to Bdo as J4. P15-X1 stays
`NOT_EARNED`; no clause verdict moves on a witness reading.

The words this record wants the member to carry, if the builder or lander moves it:
`stage_observed_by` `claude-fable-5-1/sov-witness@2026-09-06 pass 5 at 219686d
(witness/fresh-participation.md; witness/observations/2026-09-06-fresh-participation-observation-5.json)`.
F33, F34, F36 and F37 are defects owed inside the concern; F33 and F34 change nothing this
revision does on its positive path and are not preconditions of this standing, as F31 was not at
pass 4. This is an observation. It ratifies nothing.

### Verified

Commands run from the repository root at the commit above. Exit codes are the process's own.
`<pre>` and `<post>` are the two byte copies of `.local/node-interface`; `<tmp>` is a directory
under the witness's scratch directory; `<other-root>` is `contracts/principals.json` with
`root_principal` set to `principal:other-root`; `<mut>` and `<mut1>` are `git archive 219686d`
unpacked into scratch, mutated there, never copied back.

| Command | Exit | Reading |
| --- | --- | --- |
| `git rev-parse HEAD`; `git status --porcelain`; `git show --stat 219686d`; `git diff --stat d40d61f 219686d -- conformance/`; `git check-ignore -v .local/node-interface` | 0; 0; 0; 0; 0 | `219686db...`; empty before and after every command; 8 files +1122/-29; nothing under `conformance/`; `.gitignore:33` |
| `cp -a .local/node-interface <pre>`; `sha256sum` over its three files; `sqlite3` read of `journal` | 0 | 31 entries, head `032377e0...`; `record-service.sqlite3` `18145070...`; `office-opened.json` `09ee6afe...` |
| `custody.verify_export(<packet journal_export>, expected_head="032377e0...")`; `python -m soveraeign_record_service.cli verify-export --export <packet export> --expect-head 032377e0...` | 0; 0 | head `032377e0...`; `{"entries": 31, "head": "032377e0...", "verified": true}`. The office receipt's `record_head` `a127e398...` is entry 7's `entry_digest` |
| verifier defeating cases: export truncated to 8 entries with the head held outside; entry 4 `granted_by` edited | - | `TruncatedExport: export reaches a127e398... but the head held outside it is 032377e0...`; `BrokenChain: entry 4 digest does not match its contents` |
| packet export against `<pre>` journal, entry by entry | - | 31 of 31 `entry_id` and `entry_digest` identical in order; same head |
| journal read from `<pre>` (`entry_id`, `kind`, `subject`, `actor`, `payload`) | - | 0-3: `principal:bdo` grants `grant:authority` and `revoke:authority` to `principal:bdo`, scope `node:local`, receipts `authority_grant_ids: []` (genesis); 4-7: `open:session` (`grant_3807e177a65746b1`) and `read:registry` scope `registry:any` (`grant_6ab7d1d0a99e419e`) to `principal:claude-fable-5`, `granted_by: principal:bdo`, receipts under `grant_a1de4eb14460415d`; 8-9: `session_9fda2bae13834739` opened by `principal:claude-fable-5`, `principal_id` the same, under `grant_3807...`; 10-16: `registry.resolve` request `gateway_request_9afad140...`, attribution `ALLOWED`, resolution, authority `ALLOWED` under `grant_6ab7...`, routing, receipt `COMMITTED` `entry_08efe9c3...` (subject `sov://asset/ingest-asset`, F41), returned; 17-19: `session_never_opened_here` refused `check-attribution` `ACTOR_ATTRIBUTION_MISMATCH`, receipt `entry_edbe9986...`; 20-22: actor `urn:soveraeign:principal:instance:another-participant` on `session_9fda...` refused the same, receipt `entry_e9c6b83a...`; 23-27: `asset.ingest-asset` attribution `ALLOWED`, authority `REFUSED` `AuthorityRefused` for `ingest:asset`, receipt `entry_3845543f...` `check-authority` `AUTHORITY_REFUSED`; 28-30: the probe's `register`, `work`, `crossing` trailer under `fresh-dd627175`. The packet's `live_run` receipt ids, `grant_id` and `session_id` all name these entries |
| `python scripts/sov_fresh.py selfcheck` | 0 | `PASS: fresh participation slice closes on the positive variant and 3 defeating variants each fail their own predicates` |
| `python -m unittest scripts.tests.test_sov_fresh` | 0 | `Ran 19 tests OK` |
| `python scripts/verify.py` (stdout to a file; the verdict is the exit code and the `PASS: 51 checks` line) | 0 | `PASS: 51 checks in 16.397s wall`; `DEBT: no wall-clock grade`; `BUDGET DEBT: 8 check(s) over ceiling`; `fresh participation slice: 1.476s wall` within its 1.500s ceiling (F24). The `FAIL` lines are planted tooling self-test output |
| `python scripts/lint.py` | 0 | `PASS: repository hygiene (1190 text files, 553 Python modules, 10 named debt)` |
| `open-office --node-state <tmp>/n1 --issuer principal:not-root ...`; `... --issuer "" ...` | 2; 2 | `REFUSED PROBE_ISSUER_GATE: issuer 'principal:not-root' is not the registry's root principal 'principal:bdo'; nothing issued`; same for `''`; `<tmp>/n1` never created |
| `run --principal principal:claude-fable-5 --node-state .local/node-interface --variant no-grant`; `... --issuer principal:bdo` | 1; 1 | both: uncaught `ValueError: a persisted node is what it is: no-grant and --issuer describe a node this run would open itself`, traceback (F34); live journal still 31 entries, head `032377e0...` |
| `run --principal principal:claude-fable-5 --node-state .local/node-interface --json` (the one write to the live state); `cp -a .local/node-interface <post>` | 0; 0 | `passed: true`; `issuer: null`; `root_principal: principal:bdo`; `registry: contracts/principals.json`; `refused_by: null`; `admitted: null`; own `COMMITTED` receipt `entry_ff6c5928...`, `grant_id: null` (F22); `foreign_session` and `other_actor_on_this_session` `REFUSED` `check-attribution` `ACTOR_ATTRIBUTION_MISMATCH`; `beyond_the_grant` `REFUSED` `check-authority` `AUTHORITY_REFUSED` / `AuthorityRefused`; Q1.1 `session_id: fresh-57ae9c86`, `node_session_id: session_529955fd48d24543`, `oral_history_used: false`, `required_authority: read:registry`; Q1.3 `principal:claude-fable-5` / `session_529955fd48d24543` / `grant_6ab7d1d0a99e419e` / `urn:soveraeign:binding:node-interface:model-json-v1`, mismatch `REFUSED`; Q1.2 `survives_session: true`; all three hold; `other_defects: []` |
| `<pre>` journal against `<post>` journal | - | 31 to 54 entries; the 31-entry prefix identical; entry 31's `prev_digest` is the old head; 23 new entries: session `session_529955...` opened under `grant_3807...` (2), four crossings (7, 3, 3, 5), the probe trailer (3); 0 `authority-grant` records; new head `0e357ea0b2a40200c4eb4ab714169ce2caf21556c97b0feff17a2d8673d2880c`; `office-opened.json` digest unchanged |
| `open-office --node-state <tmp>/n2 --issuer principal:bdo --operator principal:claude-fable-5 --capability read:registry=registry:any --direction "first direction text" ... --json` | 0 | two grants, `granted_by: principal:bdo`; `office-opened.json` digest `b707a254...` |
| the same on `<tmp>/n2` again, `--operator principal:someone-else --direction "SECOND direction text"` | 0 | `office-opened.json` replaced, digest `a00014e3...`, now carrying only the second direction, operator and head; `n2` journal holds 5 grants (F36) |
| `open-office --node-state <tmp>/n3 --issuer principal:other-root --registry <other-root> ...` | 0 | `office opened at <tmp>/n3 by principal:other-root for principal:claude-fable-5`; the receipt does not name the registry (F35) |
| `open-office --node-state <tmp>/n2 --issuer principal:other-root --registry <other-root> ...` (node already seated under `principal:bdo`) | 1 | uncaught `AuthorityRefused: principal:other-root holds no live grant:authority grant for this operation`, traceback (F34): the Console's check, not the probe's |
| `run --principal principal:claude-fable-5 --node-state <tmp>/n2 --json` | 0 | `passed: true`; Q1.3 `grant_0ca6ca2a8cad4f78`, `session_2436a380b98e40cc` |
| `python -m unittest discover -s services/console/tests ...`; `... gateway ...`; `... record ...` | 0; 0; 0 | `Ran 193 tests OK`; `Ran 26 tests OK`; `Ran 65 tests OK` |
| `<mut1>`: `layers.py:48` reverted to `root / principals.REGISTRY_PATH`; `python -m unittest scripts.tests.test_sov_fresh` | 1 | `FAILED (failures=1)`: `test_the_issuer_gate_reads_the_registry_the_resolver_reads` |
| `<mut>`: `node.py:105` `"refused_by": None` on the issuer gate; the same | 1 | `FAILED (failures=2)`, among them `test_the_issuer_gate_names_itself_as_the_probes_rule` (F31 repaired) |
| `grep -n "open_office\|admit_persisted\|node_state\|open-office\|export_journal" scripts/tests/test_sov_fresh.py` | 1 | no match (F33) |
| `grep -rn office-opened` over the tree; `grep -rln fresh-participation-live-node scripts contracts conformance` | 0; 0 | one writer (`sov_fresh.py:104`), no reader; the custody note only (F40) |
| `<post>` journal: `operator-session` records and close events | - | `session_9fda2bae...` `OPEN`, `session_529955fd...` `OPEN`; no close event (F38) |
| `python scripts/sov_custody.py selfcheck`; `... board custody:phase-1-5/fresh-participation`; `python scripts/sov_next.py --strict`; `python scripts/sov_active_phase_progress.py` | 0; 0; 0; 0 | `27/27 declared refusals reached`; member `observed by ... pass 4 at 0cf5a57`, note quoted under F37; `PASS`; no output |
| `python scripts/sov_witness_layer.py records`; `python scripts/sov_standing.py`; `python scripts/sov_docs.py check` (before writing) | 0; 0; 0 | `PASS: 10 witness receipt(s) graded, 0 unusable, 10 stale against their subject`; `PASS: 1 standing claim(s)`; `PASS: documentation page matches 281 documents` |
| `git show -s --format=%ci 219686d`; `granted_at` in entries 0-7 | 0 | commit `14:30:42 +0000`; grants `14:29:39Z`: the office was opened one minute before the commit that carries the packet |
| CR bytes in the 8 changed files; `sha256sum` over 22 addresses against `git show 219686d:<path>` | 0 | 0 in each; 22 of 22 identical, recorded in the receipt's `observed_state_digests` |

### Pass-4 findings, disposition at 219686d

- **F31 - repaired at `5f3fd67`.** `test_the_issuer_gate_reads_the_registry_the_resolver_reads`
  and `test_the_issuer_gate_names_itself_as_the_probes_rule` (`scripts/tests/test_sov_fresh.py`)
  assert `root_principal`, `registry`, and `refused_by`. Measured: pass 4's two mutants now fail
  the suite (1 and 2 failures).
- **F32 - open, residual.** `scripts/sovsession/principals.py` is unchanged since `0cf5a57`.
- **F22, F23 - reproduced, residual (product).** `own.grant_id` and `own.stage` are `null` on the
  `COMMITTED` reading; Q1.1 `session_id` is the host session and Q1.3 `session_id` the node
  session, bridged by `node_session_id`.
- **F24 - within ceiling this run** (1.476s against 1.500s); attributed debt either way.
- **F25 - not re-exercised**; no code on that path changed.

### New findings

Severity names the consequence if the claim were accepted as-is. Defects are the builder's to
repair inside the concern; residuals are recorded and hold nothing.

- **F33 - MEDIUM, defect (new surface unpinned). `scripts/tests/test_sov_fresh.py` (whole file);
  `scripts/sov_fresh.py:78-109,151-178`; `scripts/sovfresh/node.py:51-86`;
  `scripts/sovfresh/probe.py:99-102`.** No test names `open_office`, `admit_persisted`,
  `export_journal`, `node_state`, or `open-office`; the commit's only test change renames the
  third refusal leg (`test_sov_fresh.py:66-70`), and `selfcheck` never passes `node_state`. So the
  `open-office` issuer gate, the no-seeding invariant of `admit_persisted`, the persisted-node
  refusal of `no-grant` and `--issuer`, and the export have neither a positive nor a defeating
  case in the suite; every reading of them in this record is direct measurement. Consequence: a
  later commit can let `open-office` accept any issuer or let `run --node-state` seed a grant and
  no gate turns red.
- **F34 - MEDIUM, defect. `scripts/sovfresh/probe.py:99-102`; `scripts/sov_fresh.py:63-75,92-96`.**
  Two refusals on the new surface are uncaught exceptions: `run --node-state` with `--variant
  no-grant` or `--issuer` raises `ValueError` through `cmd_run` (traceback, exit 1), and
  `open-office` against a node already seated under another root lets the Console's
  `AuthorityRefused` escape `cmd_open_office` (traceback, exit 1). Each refusal fires and names its
  reason, so no false pass; but neither is a named refusal through the declared surface, which
  is what pass 3's C9 asked of the issuer gate and what `PROBE_ISSUER_GATE` now does (exit 2, no
  traceback).
- **F35 - HIGH, residual (product rule, the crux of the claim).
  `services/console/src/soveraeign_console_service/permits.py:80-90,100-110`;
  `.../authority.py:199-223`; `.../refusals.py:47-53`; `scripts/sov_fresh.py:86-91,209`;
  `contracts/principals.json` (`principal:bdo`).** What the node verifies about `granted_by`:
  `issue` reads `root_issuer`; when none, `_genesis` writes `grant:authority` and
  `revoke:authority` to whatever non-empty string `granted_by` carries (`issuer_name` only strips
  whitespace), with no admitting grant (`authority_grant_ids: []`, entries 0-3), and `require`
  then finds the grant it just wrote. A fresh node's root is the first name offered. The grants to
  `principal:claude-fable-5` (entries 4-7) check against that self-seated grant. The only link
  from the string `principal:bdo` to the person is `sov_fresh.py:88`: the argv string must equal
  `root_principal` in the registry, whose own entry for `principal:bdo` reads `verification:
  UNVERIFIED`, `verification_channel: console-session`; and `--registry` lets the caller choose
  the registry the gate reads, so `<tmp>/n3` was opened under `principal:other-root` with exit 0.
  Nothing in the node, the probe, or the packet authenticates that the root seat, rather than a
  session typing its name, issued. This is pass 3/4's F27 and J4 exercised on a persisted node; a
  channel that would authenticate the seat is owner-held identity, so it is recorded, not
  assigned.
- **F36 - MEDIUM, defect. `scripts/sov_fresh.py:97-105`.** `office-opened.json` is written with
  `write_text`: a second `open-office` on the same node replaced it (`<tmp>/n2`: the first
  direction, operator and head are gone from the state; the first grants remain in the journal).
  It is unchained, in no journal, digested by nothing, read by nothing, and its `direction` and
  `directed_in` are free-text argv; it does not name the registry in force. What it proves: only
  what the journal already proves (its `record_head` is entry 7's digest). What it does not
  prove: that the words were said, by whom, or where. Repair inside the concern: append or refuse
  a second opening, record the registry path and digest, and say in the file that it is the
  operator's declaration.
- **F37 - LOW, defect (governed note contradicts itself). `contracts/custodies/phase-1-5.json:57`;
  `docs/documentation.html:1548`.** The member note still reads "A node whose permits office
  nobody has opened reads Q1.3 unmet, which is this node today" and, in the same note, "On
  2026-09-06 Bdo directed this session to open the node's permits office". The second sentence
  also asserts the direction as fact in a governed contract before anyone but the builder has
  attested it (J8).
- **F38 - LOW, residual (lineage F5). `scripts/sovfresh/node.py:64-81`; `<post>` journal.** Neither
  the packet run's `session_9fda2bae...` nor this witness's `session_529955fd...` was closed; both
  read `lifecycle: OPEN` and the journal holds no close event. The Q1.2 cleanup obligation "close
  console session ..." is composed and never performed; on a persisted node open sessions
  accumulate under the operator.
- **F39 - LOW, residual (subject moved under the standing). `scripts/sovfresh/probe.py:50-68`;
  `scripts/tests/test_sov_fresh.py:66-70`.** The third refusal leg changed between the witnessed
  revision and this one: `other_actor_without_the_grant` (another operator, its own session, no
  grant) became `beyond_the_grant` (this actor, this session, `asset.ingest-asset`, refused
  `check-authority`). The replacement no longer issues a grant to `OTHER_ACTOR` under the
  issuer's name, which is what makes it possible on a persisted node without seeding; it is a
  real node refusal and reads as declared here. Recorded because the pass-4 `WITNESSED` binds to
  the earlier leg and the member note does not say the leg moved.
- **F40 - LOW, residual. `scripts/sovverify/commissioning.py`; the packet.** No gate reads the
  packet: `verify.py`'s `fresh participation slice` runs `selfcheck`, and the packet's name occurs
  only in the custody note. `record_head_after_run` sits inside the same file as the export it
  checks, so a packet truncated and re-headed would self-verify (`custody.py` docstring). The
  head held outside the packet is the live node's, on one host; this pass holds it as the `<pre>`
  copy's head and records it in the receipt.
- **F41 - LOW, residual (product).** The `COMMITTED` receipt for the `registry.resolve` crossing
  (entry 15; entry 38 in this witness's run) carries `subject: sov://asset/ingest-asset`, the
  resolved name, while its request, attribution, resolution, authority and routing entries carry
  `sov://registry/resolve`. Reading the four crossings by subject miscounts; by `request_id` it
  reads correctly.
- **F42 - LOW, residual (witness lineage).** `office-opened.json` `directed_in` names
  `claude.ai/code session_014F32VV3yNJqQMCZiCDjunn`; this witness invocation carries the same
  session id in its host attribution. It is a child of the session that built the change, read no
  transcript, and holds the same relation pass 4 declared:
  `INDEPENDENT_OF_BUILDER_DECLARED_SURFACE_ONLY`.

### What a reader on another host can verify from the packet alone

Can: that the 31-entry export is an unbroken chain reaching `032377e0...` (`verify-export`); that
within it `principal:bdo` is the root issuer by genesis and issued the two grants to
`principal:claude-fable-5`; that one session opened under `grant_3807...`; that the four
crossings carry request, attribution, authority and receipt entries with the outcomes the
packet's `live_run` reports, and that its receipt ids, `grant_id` and `session_id` name entries in
the export. Cannot: that the export is the live node's journal rather than a shorter or different
one (no head held outside the packet; this pass supplies one); that anyone but the builder's
process typed `principal:bdo`; that Bdo said the words; that `office-opened.json` is the file
that was written (F36); that the node still exists or was not written between the office and
the run.

### Conditions for a later pass

None on this standing. F33, F34, F36 and F37 are owed inside the concern; a pass over the commit
that repairs them reads that commit.

### Judgement items (questions, not the witness's to answer)

- J1 to J3 carried from pass 1; J5 and J6 from pass 3; J7 from pass 4.
- J4, disposition as read now. The builder answered pass 4's question by producing the second
  branch: a persisted node, opened under the root's name at his reported direction. The record
  cannot tell that branch from the first: on both, the node's root is a typed string equal to the
  registry's `root_principal`, and the difference is persistence plus a transcript. J4 therefore
  moves from "temporary or real node" to "who authenticates `granted_by`", and splits: (a) may
  P15-X1 be observed on a node whose root issuer is the registry root's name, seated by genesis at
  the root's reported direction, when nothing in the record authenticates the direction; if Bdo
  accepts this packet with the quoted words, that acceptance is itself the record that the seat
  acted (`decisions/0023`), which no witness reading can substitute for; (b) if not, what channel
  authenticates the root seat's issuance, given the registry's `verification_channel` for
  `principal:bdo` is `console-session`, `UNVERIFIED`. Both are owner-held.
- J8. May a governed custody note assert "Bdo directed this session" as fact before the
  acceptance in J4(a), or should it read as reported direction until then (F37)?
- J9. Does the clause want the live-node packet read by a gate with a head held outside it
  (F40), or is a by-hand `verify-export` the intended reading?

### Uncovered

- `docs/documentation.html`: the one changed line was word-diffed against the custody note and
  matches it; nothing else on the page was read.
- The Console, Gateway and Record suites were run, not re-read; no service file changed.
- Bdo's direction: no transcript was read and none is in the record.
- The `asset/asset-service.sqlite3` in the node state was digested and not read.
- No network, no `gh`, no ruleset query.

### Landing residual

As in passes 1 to 4: `scripts/sovdocs/facets.py` indexes `witness/*.md`, so after this section is
written `documentation reader`, `repository tooling tests` and `sov_docs.py check` are expected to
read the built page as stale. The witness may not rebuild the page; whoever lands this record runs
`python scripts/sov_docs.py build`. The exact readings after writing are in the receipt's
`telemetry.after_writing`.

## Pass 4: commit 0cf5a57 (2026-09-06)

Verdict: **REPRODUCED**.

Claim under observation, as the builder states it: pass 3's two conditions are discharged at this
commit. C8 (F26): `layers.root_principal` reads the registry through `principals.registry_path(root)`,
the same path the resolver honours, and the Q1.1 observation carries `registry`, the path the
resolver reported (`scripts/sovfresh/layers.py`, `scripts/sovfresh/probe.py`). C9 (F27): the issuer
gate is named `PROBE_ISSUER_GATE`, its reason string says "probe rule", `node.admit` returns
`refused_by`, and the module docstring states the rule is the probe's (`scripts/sovfresh/node.py`).
F28's dead `declared` parameter is removed; F29's long lines are wrapped. Builder's report:
`reports/2026-09-06-fresh-participation-slice.md`, section "Independent witness". Its 27 changed
lines were read after every command below had returned and after the mutation probe; it is the
executor's self-report and nothing here is taken from it.

Commit witnessed: `0cf5a573d89798db04823552660c5df967cd83b6` on
`claude/phase-2-citizen-mechanics-inrozu`. `git status --porcelain` was empty before and after
every command, `git rev-parse HEAD` read the commit throughout, the 18 addresses digested below
read identically in the tree and in `git show 0cf5a57:<path>`, and `.local/sov-sessions/` does not
exist on this host, so every probe run wrote only to its temporary directory or to this witness's
scratch directory. The commit changes 9 files (+603/-49): three probe modules and the CLI, the
custody fixture's member note, the report, the built documentation page, and the two pass-3
witness files. `scripts/tests/test_sov_fresh.py` is not among them and digests as it did at
`8fd7716`. `conformance/` is unchanged since `d40d61f`, so the oracle is not weakened.

Witness: `claude-fable-5-1/sov-witness@2026-09-06`, pass 4 by the same role. This participant did
not build, edit, stage or commit anything under the subject. The only files it wrote are this
section, the header block and one paragraph above that name the current pass, and
`witness/observations/2026-09-06-fresh-participation-observation-4.json`, all after every command
under `Verified` had returned. Passes 3, 2 and 1 below are carried unchanged: the bytes from
`## Pass 3` to the end of this file are identical to `git show 0cf5a57:witness/fresh-participation.md`
from the same heading, the pass-1 section (199 lines) and the bytes from `## Pass 2` onward (430
lines) are identical between `8fd7716` and `0cf5a57`, the pass-1 and pass-2 receipts are unchanged
between those commits, and the pass-3 receipt's 20 digests recompute exactly against
`git show 8fd7716:<address>`. Pass 3's section and receipt first enter history in `0cf5a57`, the
commit they are graded alongside, as pass 2's did in `8fd7716` (F30).

### Standing supported

`WITNESSED`, declared in the block above, for the instrument claim: the one `ITEM` member
`scripts/sov_fresh.py` at stage `VERTICAL_SLICE` closes the path host session -> principal ->
campaign -> work -> lease -> node session and grant -> one admitted crossing and three the Gateway
refuses -> Record projection -> session end -> survival and cleanup read back -> instrument, grades
P15-Q1.1 to Q1.3 through `conformance/commissioning.py` on values read from a node record, the
artifact, or `None`, and discriminates on three defeating variants that are real node states. C8
and C9 reproduce as discharged through the declared surface; C5 to C7 were discharged at pass 3.
The one value the probe writes rather than reads, the issuer-gate refusal, now names itself as the
probe's in `refused_by` and in its reason string, and appears only on failing paths.

The words this record wants the member to carry: `standing` `WITNESSED`; `stage_observed_by`
`claude-fable-5-1/sov-witness@2026-09-06 pass 4 at 0cf5a57 (witness/fresh-participation.md;
witness/observations/2026-09-06-fresh-participation-observation-4.json)`. The standing binds to
revision `0cf5a57` and to the instrument claim. It is not evidence that P15-X1 holds for this node:
the positive run is a temporary node whose genesis the probe seeds under the registry root's typed
name, and whether that observes the clause is J4, the owner's. F31 below is a defect owed inside
the concern; it does not condition this standing because it changes nothing this revision does,
only what a later revision could undo unseen, and a later revision is a new subject.

This is an observation. It ratifies nothing, and a `WITNESSED` written into the member is the
builder's or the lander's act over this record, not this record's.

### Verified

Commands run from the repository root at the commit above. Exit codes are the process's own.
`<other-root>` is a copy of `contracts/principals.json` in the witness's scratch directory with
`root_principal` set to `principal:other-root`; `<mut>` is `git archive 0cf5a57` unpacked into the
scratch directory, mutated there, and never copied back.

| Command | Exit | Reading |
| --- | --- | --- |
| `git rev-parse HEAD`; `git status --porcelain`; `git diff --stat 8fd7716 0cf5a57`; `git diff --stat d40d61f 0cf5a57 -- conformance/` | 0; 0; 0; 0 | `0cf5a573...`; empty before and after every command; 9 files +603/-49; nothing under `conformance/` |
| `python scripts/sov_fresh.py selfcheck` | 0 | `PASS: fresh participation slice closes on the positive variant and 3 defeating variants each fail their own predicates` |
| `python -m unittest scripts.tests.test_sov_fresh` | 0 | `Ran 17 tests in 3.046s OK` |
| `python scripts/verify.py` | 0 | `PASS: 51 checks in 16.948s wall`; `DEBT: no wall-clock grade`; `BUDGET DEBT: 9 check(s) over ceiling`, among them `fresh participation slice: 1.972s over its 1.500s ceiling` (F24); the `FAIL` lines in the output are planted tooling self-test output; the check's verdict is the exit code (`scripts/sovverify/clocks.py:124`), not stdout |
| `python scripts/lint.py` | 0 | `PASS: repository hygiene (1188 text files, 553 Python modules, 10 named debt)` |
| `SOV_PRINCIPAL_REGISTRY=<other-root> python scripts/sov_fresh.py run --principal principal:claude-fable-5 --issuer principal:bdo --json` | 1 | `root_principal: principal:other-root`; `registry: <other-root>` at the top level and in Q1.1; `node.refused_by: PROBE_ISSUER_GATE`; `node.admitted: "probe rule PROBE_ISSUER_GATE: issuer 'principal:bdo' is not the registry's root principal 'principal:other-root'; the probe seeded nothing"`; own `REFUSED` at `stage: bind`, `SESSION_IDENTITY_REQUIRED`; only the `foreign_session` leg observed; Q1.1 `required oral history`, `oral_history_used: true`, `other_defects: undeclared environment inputs: SOV_PRINCIPAL_REGISTRY`; Q1.2 `holds`; Q1.3 five defects. One registry in force (F26); at `8fd7716` the same command read `root_principal: principal:bdo` and issued |
| `python scripts/sov_fresh.py run --principal principal:claude-fable-5 --issuer principal:other-root --registry <other-root> --json` | 0 | `passed: true`; `root_principal: principal:other-root`; `registry: <other-root>`; `refused_by: null`; `admitted: null`; own `COMMITTED` with `receipt_id`; three legs `REFUSED` at `check-attribution` / `check-attribution` / `check-authority`; Q1.3 `principal:claude-fable-5` / `session_029622ccc65e4ad5` / `grant_4533b9b323034350` / `urn:soveraeign:binding:node-interface:model-json-v1`, mismatch `REFUSED` (F27: the probe's rule against whatever registry the caller passes, now stated as such) |
| `SOV_PRINCIPAL_REGISTRY=<other-root> ... --issuer principal:bdo --registry contracts/principals.json --json` | 0 | `PASS`; `root_principal: principal:bdo`; `registry: contracts/principals.json`; `oral_history_used: false`: the flag wins for the gate and the resolver alike |
| `python scripts/sov_fresh.py run --principal principal:claude-fable-5 --issuer principal:bdo --json` | 0 | `passed: true`; `root_principal: principal:bdo`; `registry: contracts/principals.json`; `refused_by: null`; `admitted: null`; own `COMMITTED` `receipt_id entry_9c1c7280...`, `stage: null`, `grant_id: null` (F22); `foreign_session` `REFUSED`, `check-attribution`, `ACTOR_ATTRIBUTION_MISMATCH`, receipt `entry_a462d741...`; `other_actor_on_this_session` same code and stage, receipt `entry_669bc843...`; `other_actor_without_the_grant` `check-authority`, `AUTHORITY_REFUSED` / `AuthorityRefused`, receipt `entry_20ad6df4...`; Q1.1 `session_id: fresh-4c105122`, `node_session_id: session_4bb24c5fd7094f2c`, `oral_history_used: false`; Q1.3 `principal:claude-fable-5` / `session_4bb24c5fd7094f2c` / `grant_d431bab6be8b43b9` / `urn:soveraeign:binding:node-interface:model-json-v1`, mismatch `REFUSED`; Q1.2 `survives_session: true`, cleanup `release lease:...` and `close console session session_4bb24c5fd7094f2c`; all three hold |
| `... --json` (no `--issuer`) | 1 | `refused_by: null`; `admitted: "no issuer: this node has recorded no grant for any actor"`; Q1.3 five defects; Q1.1, Q1.2 hold: no probe rule fired, so none is named |
| `... --issuer "" --json` | 1 | `refused_by: PROBE_ISSUER_GATE`; `admitted: "probe rule PROBE_ISSUER_GATE: issuer '' is not the registry's root principal 'principal:bdo'; the probe seeded nothing"`; no traceback |
| `... --issuer principal:nobody-at-all` (text) | 1 | last line `node: probe rule PROBE_ISSUER_GATE: issuer 'principal:nobody-at-all' is not the registry's root principal 'principal:bdo'; the probe seeded nothing` |
| `... --registry /nonexistent --issuer principal:bdo --json` | 1 | `root_principal: null`; `registry: null`; `principal: null`; `refused_by: PROBE_ISSUER_GATE`; Q1.1 `missing principal_id`; `other_defects: []` (F32) |
| `SOV_PRINCIPAL=principal:bdo python scripts/sov_fresh.py run --issuer principal:bdo --json` (no `--principal`) | 0 | `PASS`; `principal: principal:bdo`; `oral_history_used: false` (F28 residual reproduced) |
| `run --principal principal:claude-fable-5 --issuer principal:bdo --variant unregistered-principal` / `work-dies-with-session` / `no-grant` | 1 / 1 / 1 | `COMMITTED`, Q1.1 `missing principal_id`, Q1.3 `missing principal_id; collapsed` (F25 reproduced) / Q1.2 `missing custody_or_lease; does not survive`, Q1.1 and Q1.3 hold / own `REFUSED`, Q1.3 five defects, `refused_by: null` |
| `<mut>` mutant 1: `layers.py:47` reverted to `root / principals.REGISTRY_PATH`; then `python -m unittest scripts.tests.test_sov_fresh`; `python scripts/sov_fresh.py selfcheck` | 0; 0 | `Ran 17 tests OK`; `PASS` (F31) |
| `<mut>` mutant 2: `node.py:57` `"refused_by": None` on the issuer gate; the same two commands | 0; 0 | `Ran 17 tests OK`; `PASS` (F31). `git status --porcelain` in the repository empty after both |
| `python -m unittest discover -s services/console/tests -t services/console/tests`; `... gateway ...` | 0; 0 | `Ran 193 tests OK`; `Ran 26 tests OK` (no service file changed in this commit) |
| `python scripts/sov_custody.py selfcheck`; `python scripts/sov_custody.py board custody:phase-1-5/fresh-participation` | 0; 0 | `46 case(s), 27/27 declared refusals reached; selfcheck PASS`; `ITEM scripts/sov_fresh.py [build claim]`, `closes when COMMAND python scripts/sov_fresh.py selfcheck`, the member note names passes 1 to 3 and carries no repair claim |
| `python scripts/sov_next.py --strict`; `python scripts/sov_active_phase_progress.py` | 0; 0 | `PASS: phase/custody precedence is explicit ...`; no output |
| `python scripts/sov_witness_layer.py records`; `python scripts/sov_standing.py`; `python scripts/sov_docs.py check` (before writing) | 0; 0; 0 | `PASS: 9 witness receipt(s) graded, 0 unusable, 9 stale against their subject`; `PASS: 1 standing claim(s)`; `PASS: documentation page matches 281 documents` |
| pass-1 and pass-2 receipts `git diff 8fd7716 0cf5a57`; pass-1 section and bytes from `## Pass 2` onward, `8fd7716` vs `0cf5a57`; pass-3 receipt's 20 digests against `git show 8fd7716:<address>`; `git cat-file -e 8fd7716:<pass-3 receipt>` | 0; 0; 0; 128 | unchanged, unchanged; identical (199 lines), identical (430 lines); 20/20; absent at `8fd7716` (F30) |
| `awk 'length($0)>100'` over the five probe Python files; `python -m ruff --version`; CR bytes in the changed files | -; 1; - | none (F29 repaired); `No module named ruff`; 0 |
| `sha256sum` over 18 addresses | 0 | recorded in the receipt's `observed_state_digests` |

### Pass-3 findings, disposition at 0cf5a57

- **F26 - repaired.** `root_principal` reads `principals.registry_path(root)` when no registry is
  passed (`scripts/sovfresh/layers.py:47`), the function the resolver itself calls
  (`scripts/sovsession/principals.py:46-49,71`), and its docstring now says so (`layers.py:42-45`).
  `probe.run` reads the resolver's `registry` from the claim (`scripts/sovfresh/probe.py:107`)
  and carries it in the trace, the Q1.1 observation, and the result (`probe.py:110,167,191`).
  Measured: under the environment override the gate and the resolver read `<other-root>` together
  and the root seat's name was refused; with `--registry` set and the variable set to a different
  file, the flag won for both. C8 discharged. Not pinned by any test: F31.
- **F27 - repaired as stated.** `PROBE_ISSUER_GATE` is declared with a docstring
  (`scripts/sovfresh/node.py:33-34`); the module docstring names the one rule the probe applies and
  says it is reported as such (`node.py:6-8`); `admit`'s docstring states that the Console makes a
  fresh node's first issuer its root and reads no registry, and that the node would have accepted
  the name (`node.py:45-50`); the refusal returns `refused_by: PROBE_ISSUER_GATE` and a reason that
  opens with `probe rule PROBE_ISSUER_GATE:` (`node.py:57-59`); `refused_by` is `None` when no
  issuer was offered and no rule fired (`node.py:54-55`); the result carries `node.refused_by`
  (`probe.py:192`); the `--issuer` help reads "the probe accepts only the registry's root
  principal" (`scripts/sov_fresh.py:150-151`) and the module docstring "by the probe's own rule"
  (`sov_fresh.py:7-8`). C9 discharged by its second clause: the probe-side refusal is marked
  `refused_by`. Residual, not a condition: the reason still sits under the key `node.admitted` and
  the text renderer prints it after `node:` (`sov_fresh.py:54-55`); the string now identifies its
  author, so a reader is no longer misled. `permits.issue` is unchanged and still takes whoever
  grants first as a fresh node's root; that is the product rule, and J4 is where it goes.
- **F28 - parameter removed; residual stands.** `undeclared_inputs(registry_declared)` has no
  `declared` parameter (`layers.py:29`), `probe.run` has none (`probe.py:95-96`), and `cmd_run`
  reads `--principal` or `SOV_PRINCIPAL` in one expression (`sov_fresh.py:60`). The residual is
  unchanged: `SOV_PRINCIPAL=principal:bdo run --issuer principal:bdo` reads `PASS` with
  `oral_history_used: false`, and the `ENVIRONMENT_INPUTS` docstring (`layers.py:25-26`) still
  says both variables are oral history when set and undeclared, which is true of one. J6.
- **F29 - repaired.** No line over 100 characters in the five probe Python files. The wrap at
  `sov_fresh.py:7-8` leaves a short line mid-sentence; style only.
- **F30 - continues, residual.** Pass 3's section and receipt first enter history in `0cf5a57`,
  the builder's repair commit; their integrity rests on 20/20 digest recomputation against
  `8fd7716` and on the older sections being byte-identical across the commits that carry them.
  This pass will be committed the same way.
- **F10 (pass 1) - repaired.** The result and the Q1.1 observation now carry `registry`, the path
  the principal resolved from, relative when inside the repository and absolute otherwise
  (`principals.py:52-61`).
- **F22, F23, F25 - open, residual (product).** Unchanged: `own.grant_id` and `own.stage` are
  `null` in the `COMMITTED` reading; Q1.1 `session_id` and Q1.3 `identities.session_id` name two
  sessions under one label with `node_session_id` as the bridge; the node commits a crossing for
  a session opened with `principal_id: null`.
- **F24 - open, residual (debt).** The check read 1.972s pooled over its 1.500s ceiling at this
  pass; attributed, not a refusal.

### New findings

Severity names the consequence if the member were ratified at `VERTICAL_SLICE` as-is. Defects are
the builder's to repair inside the concern; residuals are recorded and hold nothing.

- **F31 - LOW, defect (unpinned repair). `scripts/tests/test_sov_fresh.py:86-103,118-123`;
  `scripts/sov_fresh.py:112-139`.** Neither the F26 nor the F27 repair has a case that fails
  without it. In a `git archive 0cf5a57` copy, reverting `layers.py:47` to
  `root / principals.REGISTRY_PATH` and, separately, setting `refused_by` to `None` on the issuer
  gate (`node.py:57`) each left `python -m unittest scripts.tests.test_sov_fresh` at 17 OK and
  `selfcheck` at `PASS`. `test_oral_history_is_earned_not_asserted` sets the environment registry
  to the fixture and asserts only that Q1.1 fails and the run does not pass; it does not read
  `root_principal` or `registry`, and with the reversion the run fails Q1.3 as well, unasserted.
  `test_only_the_registry_root_may_issue` asserts the reason substring and a null `grant_id`, not
  `refused_by`. `selfcheck` cannot see either by design (J5). The test file's digest is unchanged
  since `8fd7716`. Consequence: a later commit can reinstate two registries in one run, masked by
  the Q1.1 failure exactly as F26 was, and no gate turns red. This pass measured the behaviour
  directly, so the claim is witnessed at this revision; the pin is owed for the next one.
- **F32 - LOW, residual. `scripts/sovsession/principals.py:140-146,159-161`;
  `scripts/sovfresh/probe.py:107`.** When the registry cannot be read, `resolve` returns
  `_blank(session, reason)` with `registry: None`, so the run's `registry` and Q1.1 `registry` are
  `null` and the path the resolver tried appears only in the claim's `basis`
  ("no principal registry at /nonexistent"), which the probe does not carry. "The path the
  resolver reported" holds on the readable path only. Honest null; a reader of a failing run has
  to rerun to learn which file was missing.

### Conditions for a later pass

None on this standing. F31 is owed inside the concern and is not a precondition of `WITNESSED` at
`0cf5a57`; a pass over the commit that pins it reads that commit.

### Judgement items (questions, not the witness's to answer)

- J1 to J3 carried from pass 1; J5 and J6 carried from pass 3.
- J4, carried and now the live one: this record supports `WITNESSED` for the instrument, not for
  the clause. May P15-X1 be observed against a temporary node whose genesis the instrument seeds
  in the root seat's typed name, when nothing verifies that the seat acted? If not, what the exit
  custody closes on is the instrument's discrimination (`selfcheck`), and a recorded live `run`
  against a node whose office the root seat opened is still owed (J5).
- J7. `contracts/custody.schema.json:183` describes `stage_observed_by` as "the participant that
  settled this member stage". Under `AGENTS.md` a witness observation settles nothing. Does the
  field want "observed", or does writing a witness id there claim more than a witness can give?

### Uncovered

- `docs/documentation.html`: the 14 changed lines were not read; accepted on `sov_docs.py check`.
- The Console and Gateway suites were run, not re-read; no service file changed in this commit.
- The kept-node journal drive from pass 3 was not repeated; no receipt-producing code changed.
- The builder's report was read after every command had returned; its F26 and F27 statements
  match what was measured, and its terminal is presented on the branch for Bdo's review because
  the change touches `CLAUDE.md`, which the standing grant excludes.
- No network, no `gh`, no ruleset query.

### Landing residual

As in passes 1 to 3: `scripts/sovdocs/facets.py` indexes `witness/*.md`, so after this section is
written `documentation reader`, `repository tooling tests` and `sov_docs.py check` are expected to
read the built page as stale. The witness may not rebuild the page; whoever lands this record runs
`python scripts/sov_docs.py build`. The exact readings after writing are in the receipt's
`telemetry.after_writing`.

## Pass 3: commit 8fd7716 (2026-09-06)

Verdict: **RATIFIABLE-WITH-CONDITIONS**.

Claim under observation, as the builder states it: F18, F19, F20 and F21 from pass 2 are repaired
at this commit. Only `SOV_PRINCIPAL_REGISTRY` counts as an undeclared resolver input, and only
when no registry is passed (`scripts/sovfresh/layers.py` `undeclared_inputs`); the fixture
registry is read from the repository path with a fixture root (`scripts/sov_fresh.py`
`fixture_registry`); the foreign-session leg binds to a session the node never opened and the
Gateway refuses it at `check-attribution` with a receipt (`scripts/sovfresh/probe.py` `_refusals`,
`scripts/sovfresh/node.py` `bind`); only the registry's `root_principal` may issue, any other or
empty issuer issues nothing (`node.py` `admit`, `layers.py` `root_principal`). F23 is answered by a
`node_session_id` field beside `session_id` in the Q1.1 observation. Builder's report:
`reports/2026-09-06-fresh-participation-slice.md`, section "Independent witness". It was read
after every command below had run and after the findings below were fixed; it is the executor's
self-report and nothing here is taken from it.

Commit witnessed: `8fd7716d6f1bb9a3b7bd1b11d76d9bbe06362c16` on
`claude/phase-2-citizen-mechanics-inrozu`. `git status --porcelain` was empty before and after
every command, `git rev-parse HEAD` read the commit throughout, three changed files digest
identically in the tree and in `git show 8fd7716:<path>`, and `.local/sov-sessions/` does not
exist on this host, so every probe run wrote only to its temporary directory or to this
witness's scratch directory. The commit changes 10 files (+736/-53): the four probe modules, the
unit suite, the custody fixture's member note, the report, the built documentation page, and the
two pass-2 witness files. `conformance/` is not among them, so the oracle is unchanged since
`d40d61f`.

Witness: `claude-fable-5-1/sov-witness@2026-09-06`, pass 3 by the same role. This participant
did not build, edit, stage or commit anything under the subject. The only files it wrote are this
section, the two header lines and one paragraph above that name the current pass, and
`witness/observations/2026-09-06-fresh-participation-observation-3.json`, all after every command
under `Verified` had returned. Pass 2 and pass 1 below are carried unchanged: the bytes from
`## Pass 2` to the end of this file are identical to `git show 8fd7716:witness/fresh-participation.md`
from the same heading, the pass-1 section is byte-identical between `161d559` and `8fd7716`, the
pass-1 receipt is unchanged between those commits and its 24 digests recompute against `d40d61f`,
and the pass-2 receipt's 25 digests recompute exactly against `git show 161d559:<address>`. Pass 2's
section and receipt first enter history in `8fd7716`, the commit they are graded alongside, so
"unchanged" for pass 2 rests on that recomputation and on nothing older (F30).

### Standing supported

`BUILT`, unchanged in the block above. The pass-2 conditions are discharged as written: C5 (F18),
C6 (F19) and C7 (F20, F21) each reproduce through the declared surface, and every value in the
positive run's three observations is read from a node record, the artifact, or derived from
them. `BUILT -> WITNESSED` is supported for the instrument claim once C8 and C9 below are
discharged, and is not declared, because a conditional advance is not an advance and the gate
reads one word. C8 (F26) is a small correctness defect masked today by another failure; C9 (F27)
is a statement defect: the issuer gate that now refuses a non-root issuer is the probe's rule, the
Console still makes the first issuer a fresh node's root, and `node.py`'s docstring and the
observation's `node.admitted` field present the probe's refusal as the node's. Whether the
positive run, a temporary node whose genesis the probe seeds under the registry root's typed
name, is evidence for P15-X1 remains J4 and is the owner's, not a reason this pass withholds.

### Verified

Commands run from the repository root at the commit above. Exit codes are the process's own.
`<copy>` is a byte copy of `contracts/principals.json` in the witness's scratch directory;
`<other-root>` is the same copy with `root_principal` set to `principal:other-root` and that
principal appended.

| Command | Exit | Reading |
| --- | --- | --- |
| `git rev-parse HEAD`; `git status --porcelain`; `git diff --stat 161d559 8fd7716` | 0; 0; 0 | `8fd7716d...`; empty before and after every command; 10 files +736/-53, none under `conformance/` |
| `python scripts/sov_fresh.py selfcheck` | 0 | `PASS: fresh participation slice closes on the positive variant and 3 defeating variants each fail their own predicates` |
| `SOV_PRINCIPAL=principal:bdo python scripts/sov_fresh.py selfcheck` | 0 | same `PASS` (F18) |
| `SOV_PRINCIPAL_REGISTRY=/nonexistent python scripts/sov_fresh.py selfcheck` | 0 | same `PASS` (F18) |
| `python scripts/sov_fresh.py run --principal principal:claude-fable-5 --issuer principal:bdo --json` | 0 | `passed: true`; `root_principal: principal:bdo`; `node.admitted: null`; own `COMMITTED` with `receipt_id`, `stage: null`, `grant_id: null`; `foreign_session` `REFUSED`, `stage: check-attribution`, `ACTOR_ATTRIBUTION_MISMATCH`, `receipt_id` present (F19); `other_actor_on_this_session` the same code and stage; `other_actor_without_the_grant` `stage: check-authority`, `AUTHORITY_REFUSED` / `AuthorityRefused`, `receipt_id`; Q1.1 `session_id: fresh-1aca0dbe`, `node_session_id: session_c560a1fb1e4a48dd` (F23); Q1.3 identities `principal:claude-fable-5` / `session_c560a1fb1e4a48dd` / `grant_20bd94abd3124ed5` / `urn:soveraeign:binding:node-interface:model-json-v1`, mismatch `REFUSED`; all three predicates hold |
| `... --issuer principal:nobody-at-all --json` | 1 | `node.admitted: "issuer 'principal:nobody-at-all' is not the registry's root principal 'principal:bdo'; nothing issued"`; own `REFUSED` at `stage: bind`, `SESSION_IDENTITY_REQUIRED`; only the `foreign_session` leg observed (`REFUSED`, `check-attribution`, receipt); `node_session_id: null`; Q1.3 `missing session_id; missing grant_id; missing interface_binding_id; collapsed; mismatch did not refuse` (F20) |
| `... --issuer "" --json` | 1 | `node.admitted: "issuer '' is not the registry's root principal 'principal:bdo'; nothing issued"`; no traceback; otherwise the row above (F21) |
| `... --json` (no `--issuer`) | 1 | `node.admitted: "no issuer: this node has recorded no grant for any actor"`; otherwise the row above |
| `SOV_PRINCIPAL_REGISTRY=<copy> python scripts/sov_fresh.py run --principal principal:claude-fable-5 --issuer principal:bdo` | 1 | `P15-Q1.1: fresh participation required oral history`; `defect: undeclared environment inputs: SOV_PRINCIPAL_REGISTRY`; Q1.2, Q1.3 `holds` |
| the same with `--registry <copy>` | 0 | `PASS`; all three `holds` |
| the same with both the variable and `--registry <copy>` | 0 | `PASS`; the flag declares the input |
| `SOV_PRINCIPAL_REGISTRY=<other-root> ... --issuer principal:other-root --json` | 1 | `root_principal: principal:bdo` while the principal resolved through `<other-root>`; `node.admitted: "issuer 'principal:other-root' is not the registry's root principal 'principal:bdo' ..."`; Q1.1 `required oral history` (F26) |
| `SOV_PRINCIPAL_REGISTRY=<other-root> ... --issuer principal:bdo --json` | 1 | `root_principal: principal:bdo`; `node.admitted: null`, grants issued; Q1.3 `holds`; the run fails on Q1.1 `required oral history` only (F26) |
| `... --registry <other-root> --issuer principal:other-root --json` | 0 | `PASS`; `root_principal: principal:other-root`: whoever writes the registry file names who may issue (F27) |
| `... --registry /nonexistent --issuer principal:bdo --json` | 1 | `root_principal: null`; `principal: null`; `node.admitted: "issuer 'principal:bdo' is not the registry's root principal None ..."`; Q1.1 `missing principal_id`; `other_defects: []` |
| `SOV_PRINCIPAL=principal:bdo python scripts/sov_fresh.py run --issuer principal:bdo --json` (no `--principal`) | 0 | `PASS`; `principal: principal:bdo`; `oral_history_used: false` (F28) |
| `run --principal principal:claude-fable-5 --issuer principal:bdo --variant unregistered-principal` / `work-dies-with-session` / `no-grant` | 1 / 1 / 1 | `COMMITTED`, Q1.1 `missing principal_id`, Q1.3 `missing principal_id; collapsed` (F25 reproduced) / Q1.2 `missing custody_or_lease; does not survive`, Q1.1 and Q1.3 `holds` / `REFUSED SESSION_IDENTITY_REQUIRED`, Q1.3 fails, `node: no issuer` |
| witness's own drive of `sovfresh.probe.run` against a kept node (fixture registry and fixture issuer from `sov_fresh.fixture_registry`), then `LocalActionPath(...).record.reconstruct()` | 0 | `passed True`; 35 journal entries (24 `EVENT`, 11 `RECEIPT`); the four `receipt_id`s resolve to `RECEIPT` entries whose payloads read `REFUSED` / `check-attribution` / `ACTOR_ATTRIBUTION_MISMATCH` (two legs), `REFUSED` / `check-authority` / `AuthorityRefused`, and `COMMITTED` (subject `sov://asset/ingest-asset`); grants in the journal: genesis `grant:authority` and `revoke:authority` to `principal:fixture-root` by `principal:fixture-root`, then `open:session` and `read:registry` to the actor and `open:session` to the other actor, all `granted_by principal:fixture-root` |
| `python -m unittest scripts.tests.test_sov_fresh` | 0 | `Ran 17 tests in 2.986s OK` |
| `python -m unittest discover -s services/console/tests`; `... -s services/gateway/tests` | 0; 0 | `Ran 193 tests OK`; `Ran 26 tests OK` (pass 2 left both uncovered) |
| `python scripts/sov_custody.py selfcheck`; `python scripts/sov_custody.py board custody:phase-1-5/fresh-participation` | 0; 0 | `46 case(s), 27/27 declared refusals reached; selfcheck PASS`; `ITEM scripts/sov_fresh.py [build claim]`, `closes when COMMAND python scripts/sov_fresh.py selfcheck`, the member note names both prior passes and carries no repair claim (F24) |
| `python scripts/sov_next.py --strict`; `python scripts/sov_active_phase_progress.py` | 0; 0 | `PASS: phase/custody precedence is explicit ...`; no output (pass-1 residual reproduced) |
| `python scripts/lint.py` | 0 | `PASS: repository hygiene (1187 text files, 553 Python modules, 10 named debt)` |
| `python scripts/verify.py` | 0 | `PASS: 51 checks in 16.914s wall`; `DEBT: no wall-clock grade`; `BUDGET DEBT: 9 check(s) over ceiling`, among them `fresh participation slice: 1.630s over its 1.500s ceiling` (F24); the `FAIL` lines in the output are planted tooling self-test output |
| `python scripts/sov_witness_layer.py records`; `python scripts/sov_standing.py`; `python scripts/sov_docs.py check` (before writing) | 0; 0; 0 | `PASS: 8 witness receipt(s) graded, 0 unusable, 8 stale against their subject`; `PASS: 1 standing claim(s)`; `PASS: documentation page matches 281 documents` |
| pass-1 section bytes, `git show 161d559:` against `8fd7716`; pass-1 receipt `git diff 161d559 8fd7716`; pass-1 receipt digests against `d40d61f` | 0 | identical (199 lines); unchanged; 24/24 |
| pass-2 receipt's 25 digests against `git show 161d559:<address>` | 0 | 25/25 |
| lines over 100 characters in the five changed Python files (`awk`); `python -m ruff` | - | `probe.py:188` (116), `probe.py:86` (101), `sov_fresh.py:94` (101); Ruff is not installed on this host (F29) |
| `sha256sum` over 20 addresses | 0 | recorded in the receipt's `observed_state_digests` |

### Pass-2 findings, disposition at 8fd7716

- **F18 - repaired.** `undeclared_inputs` (`layers.py:29-38`) considers `SOV_PRINCIPAL_REGISTRY`
  alone and returns nothing when a registry was passed; `fixture_registry` reads
  `ROOT / contracts/principals.json` directly (`sov_fresh.py:83-86`) and substitutes a fixture root
  (`:87-98`). Measured: `selfcheck` exit 0 under a bare environment, under `SOV_PRINCIPAL`, and
  under `SOV_PRINCIPAL_REGISTRY=/nonexistent`. Both polarities are pinned
  (`test_sov_fresh.py:86-116`). Successor residual: F28.
- **F19 - repaired.** `_refusals` binds the participant's own binding to
  `session_id="session_never_opened_on_this_node"` (`probe.py:56-57`); the composer binds, the
  Gateway refuses at `check-attribution` with `ACTOR_ATTRIBUTION_MISMATCH`, and the receipt is a
  `RECEIPT` entry in the node's journal, re-read by this witness from a kept node. `_mismatch`
  requires that code for the leg (`probe.py:76`); the unit suite pins stage and receipt
  (`test_sov_fresh.py:64-66`).
- **F20 - repaired as pass 2's first alternative, with a successor.** `admit` refuses an issuer that
  is not the registry's `root_principal` and returns the refusal (`node.py:50-53`);
  `principal:nobody-at-all` reads exit 1 and Q1.3 unmet, and `principal:bdo` issues nothing
  against the fixture registry whose root is `principal:fixture-root`
  (`test_sov_fresh.py:118-123`). The gate is the probe's, not the node's, and is stated as the
  node's: F27. Which registry names the root when the environment overrides it: F26.
- **F21 - repaired.** `--issuer ""` returns `node.admitted` with a reason and exit 1; no traceback
  (`node.py:50`).
- **F22 - open, residual (product).** `own.grant_id` and `own.stage` are `null` in the `COMMITTED`
  reading; unchanged.
- **F23 - answered in part, residual.** Q1.1 carries `node_session_id` beside `session_id`
  (`probe.py:165`), so a reader can relate the host session to the console session. Q1.1
  `session_id` and Q1.3 `identities.session_id` still name two different sessions under one
  label; `conformance/commissioning.py` reads neither bridge field.
- **F24 - half repaired, half open.** The member note no longer carries the builder's repair claim
  and cites this record with both prior verdicts (`contracts/custodies/phase-1-5.json:57`). The
  check read 1.630s pooled against a 1.500s ceiling at this pass; attributed debt, not a refusal.
- **F25 - open, residual (product).** Reproduced: `--variant unregistered-principal --issuer
  principal:bdo` reads `COMMITTED` for a session opened with `principal_id: null`.
- **F10 (pass 1) - CLI half repaired.** `run --registry` exists (`sov_fresh.py:155-156`); the
  result carries `root_principal` but still not the path the principal resolved from.

### New findings

Severity names the consequence if the member were ratified at `VERTICAL_SLICE` as-is. Defects are
the builder's to repair inside the concern; residuals are recorded and hold nothing.

- **F26 - LOW, defect. `scripts/sovfresh/layers.py:41-47`; `scripts/sovsession/principals.py:46-49`;
  `scripts/sovfresh/probe.py:96-97`; `scripts/sov_fresh.py:68`.** `root_principal` reads
  `root / contracts/principals.json` whenever no `--registry` is passed, while the resolver's
  `registry_path` honours `SOV_PRINCIPAL_REGISTRY`. With the variable naming a registry whose
  root is `principal:other-root` and `--issuer principal:bdo`, the principal resolved through the
  environment registry and the issuer gate compared against the checked-in root and issued:
  `node.admitted: null`, Q1.3 `holds`. Two registries were in force in one run, and the docstring
  "the root principal the registry in force names" is untrue in the override case. Masked today
  because the same run fails Q1.1 for the undeclared input, so no passing run results.
  Consequence: the issuer gate can be satisfied by a registry the run did not resolve from.
- **F27 - LOW, defect (statement). `scripts/sovfresh/node.py:1-7,38-53`;
  `scripts/sovfresh/probe.py:187-189`; `scripts/sov_fresh.py:153-154`;
  `services/console/src/soveraeign_console_service/permits.py:101-102`.** The root check is the
  probe's rule. `permits.issue` still takes whoever grants first as a fresh node's root, neither
  the Console nor the Gateway reads `contracts/principals.json`, and `--registry <file naming X
  as root> --issuer X` passes. The `node.py` docstring says everything in the module "is read back
  from records the node's own services wrote" and that the probe "decides nothing about whether
  they are admitted", but `admit` decides at `:50-53` before the node is asked, and its reason
  string is reported under `node.admitted` as though the node said it. The `--issuer` help "any
  other name issues nothing" reads as product behaviour. `sov_fresh.py:9-10` carries the honest
  half: naming the root seat "shows the mechanism; it is not evidence that the seat acted".
  Consequence: a reader of a failing observation cannot tell whether the node or the probe
  refused; a reader of the passing one cannot tell from the code that the node would have taken
  any name. This is the one value in the run written by the probe rather than read from a record
  or honestly `None`; it appears only on failing paths.
- **F28 - LOW, residual. `scripts/sovfresh/layers.py:25-26,29-38`; `scripts/sov_fresh.py:59-63`.**
  `undeclared_inputs` no longer considers `SOV_PRINCIPAL` at all, and its `declared` parameter is
  tested only for `SOV_PRINCIPAL_REGISTRY`, which `cmd_run` never adds, so the parameter is dead;
  the `ENVIRONMENT_INPUTS` docstring "set and undeclared, they are oral history" is stale for the
  principal variable. `SOV_PRINCIPAL=principal:bdo run --issuer principal:bdo` with no
  `--principal` reads `PASS` with `oral_history_used: false`: the host environment supplied the
  principal and the CLI counts the variable as a declaration channel. Whether a variable preset
  on the host is artifact-derived entry or private history is a reading of P15-Q1.1 the probe
  has settled by definition (J6).
- **F29 - LOW, residual (style). `scripts/sovfresh/probe.py:188` (116 characters), `:86` (101);
  `scripts/sov_fresh.py:94` (101).** `AGENTS.md` targets 100; `lint.py` does not grade it and Ruff
  is not installed here.
- **F30 - LOW, residual (record provenance).** Pass 2's section and receipt first enter history in
  `8fd7716`, the builder's repair commit, as pass 1's did in `161d559`. Their integrity rests on
  digest recomputation against the commits they name (25/25, 24/24) and on the pass-1 section
  being byte-identical across the two commits that carry it; no copy independent of the
  builder's hand exists, and this pass will be committed the same way.

### Conditions for a later pass to support `BUILT -> WITNESSED`

- C8 (F26): take the root from the registry the resolver actually used (the resolver's claim
  names it), so one registry is in force per run; or refuse the run when the environment names a
  registry, none was passed, and the two differ.
- C9 (F27): state in `node.py`'s docstring and the `--issuer` help that the root check is the
  probe's rule and that the Console makes a fresh node's first issuer its root; report the
  probe-side refusal under a key that does not read as the node's, or mark it `refused_by`.
- C5 to C7 from pass 2 are discharged.

### Judgement items (questions, not the witness's to answer)

- J1 to J3 carried from pass 1; J4 carried from pass 2, sharpened: the product rule is that a
  fresh node's first issuer becomes its root; the registry check is the instrument's. May P15-X1 be
  observed against a temporary node whose genesis the instrument seeds in the root seat's typed
  name, when nothing verifies that the seat acted?
- J5. The exit custody closes on `python scripts/sov_fresh.py selfcheck`, which since the F18
  repair cannot see the operator's environment by design, while the custody's `defeated_by`
  names "a fresh session that needs oral history to find its principal". Only `run` observes
  that condition. Is closing on the instrument's discrimination what the clause wants, or does
  closure want a recorded live `run`?
- J6. Under P15-Q1.1, is a `SOV_PRINCIPAL` preset on the host a declaration channel, as the CLI
  reads it, or oral history?

### Uncovered

- `docs/documentation.html`: the 10 changed lines were read for shape only (the witness block of
  this record and two re-wrapped unrelated lines); accepted on `sov_docs.py check`.
- The Console and Gateway suites were run, not read; their behaviour was read through
  `permits.py`, `authority.py`, `attribution.py`, and the kept node's journal.
- The Record Service's `evidence_projection` was not exercised beyond the probe's own call.
- The builder's report was read after the findings above were fixed; its statements of F18 to
  F21 and F23 match what was measured, and its "Independent witness" section describes passes 1
  and 2, not this one.
- No network, no `gh`, no ruleset query.

### Landing residual

As in passes 1 and 2: `scripts/sovdocs/facets.py` indexes `witness/*.md`, so after this section
is written `documentation reader`, `repository tooling tests` and `sov_docs.py check` are expected
to read the built page as stale. The witness may not rebuild the page; whoever lands this record
runs `python scripts/sov_docs.py build`. The exact readings after writing are in the receipt's
`telemetry.after_writing`.

## Pass 2: commit 161d559 (2026-09-06)

Verdict: **NOT-YET**.

Claim under observation, as the builder states it: every F1 to F7 defect from pass 1 is
repaired at this commit, and every identity in the P15-Q1.3 observation is read from a node
record (the Console Service's grant and session records and the Gateway's receipts,
`scripts/sovfresh/node.py`, `scripts/sovfresh/probe.py`). Builder's report:
`reports/2026-09-06-fresh-participation-slice.md`, section "Independent witness". It was read
after every command below had run and is the executor's self-report; nothing here is taken from
it.

Commit witnessed: `161d559fc4eba85dab598c3495d0620cbacbf011` on
`claude/phase-2-citizen-mechanics-inrozu`. `git status --porcelain` was empty before and after
every command, `git rev-parse HEAD` read the commit throughout, and `.local/sov-sessions/` does
not exist on this host, so every probe run wrote only to its temporary directories. The commit
changes 11 files (+1000/-373), all inside the concern; `conformance/` is unchanged between
`d40d61f` and `161d559`, so the oracle was not weakened.

Witness: `claude-fable-5-1/sov-witness@2026-09-06`, pass 2 by the same role. This participant
did not build, edit, stage or commit anything under the subject. The only files it wrote are
this section and `witness/observations/2026-09-06-fresh-participation-observation-2.json`, both
after every command under `Verified` had returned. Pass 1 below is carried unchanged: the
pass-1 receipt's 24 digests recompute exactly against the bytes `git show d40d61f:<path>`
returns, and its line citations (`probe.py:127,131-133,146,162-164`, `layers.py:182`) match the
`d40d61f` source. Both witness files first enter history in the builder's commit `161d559`,
which is the landing residual pass 1 named; no independent copy exists, so "unchanged" rests on
the digest recomputation, not on a byte comparison.

### Standing supported

`BUILT`, unchanged. The identity claim is reproduced: with an issuer, `principal_id` comes from
the registry through the resolver, `session_id` and `grant_id` from Console records the node
wrote, `interface_binding_id` from the Node Interface document, and each reads `None` when the
product refused. F2 to F8 and F13 are repaired through the surface; F1 is repaired for two of
its three legs. `BUILT -> WITNESSED` is not supported, for three reasons the builder can repair
inside the concern: the positive live run passes under any non-empty `--issuer` string, because
the Console's genesis makes the first issuer on a fresh node its root and the probe never
consults the registry that names the root seat (F20); the `foreign_session` leg of the Q1.3
mismatch is refused by the binding composer in `scripts/`, never reaches the node, and leaves no
receipt (F19); and the custody's closure command reads `FAIL` under an operator environment it
overrides and cannot be affected by, which `verify.py` inherits (F18).

### Verified

Commands run from the repository root at the commit above. Exit codes are the process's own.

| Command | Exit | Reading |
| --- | --- | --- |
| `git rev-parse --short HEAD`; `git status --porcelain`; `git show --stat 161d559`; `git diff --stat d40d61f 161d559 -- conformance/` | 0 | `161d559`; empty; 11 files +1000/-373; empty |
| `python scripts/sov_fresh.py selfcheck` | 0 | `PASS: fresh participation slice closes on the positive variant and 3 defeating variants each fail their own predicates` |
| `python scripts/sov_fresh.py run --principal principal:claude-fable-5` | 1 | `FAIL`; `registry.resolve as urn:...:instance:fresh-<id>: REFUSED SESSION_IDENTITY_REQUIRED`; only `foreign_session: REFUSED SESSION_IDENTITY_REQUIRED`; Q1.1, Q1.2 `holds`; Q1.3 `missing session_id; missing grant_id; missing interface_binding_id; collapsed; mismatch did not refuse`; `node: no issuer: this node has recorded no grant for any actor` (the builder's claimed honest FAIL, reproduced) |
| `python scripts/sov_fresh.py run --principal principal:claude-fable-5 --issuer principal:bdo` | 0 | `PASS`; own crossing `COMMITTED`; `foreign_session: REFUSED SESSION_ATTRIBUTION_CONFLICT`; `other_actor_on_this_session: REFUSED ACTOR_ATTRIBUTION_MISMATCH`; `other_actor_without_the_grant: REFUSED AuthorityRefused`; cleanup `release lease:...`, `close console session session_...`; all three `holds` |
| `python scripts/sov_fresh.py run --principal principal:claude-fable-5 --issuer principal:bdo --json` | 0 | `identities` = `principal:claude-fable-5`, `session_c9ad17d6685b40c0`, `grant_ce7bfb68d8dc49c0`, `urn:soveraeign:binding:node-interface:model-json-v1`; `cross_principal_session_mismatch` = `REFUSED`; `oral_history_used` = `false`; `node.own.grant_id` = `null`; `refusals.foreign_session` has `stage: bind` and no `receipt_id`; the other two carry `receipt_id` and stages `check-attribution`, `check-authority` (F8 repaired: `--json` after the subcommand) |
| `run --principal principal:claude-fable-5 --variant unregistered-principal` (no issuer / `--issuer principal:bdo`) | 1 / 1 | `principal UNIDENTIFIED` in both; Q1.1 `fresh context missing principal_id`; Q1.3 fails; with the issuer the node still reads `registry.resolve ...: COMMITTED` (F3 repaired; F25) |
| `run --principal principal:claude-fable-5 --variant work-dies-with-session` (no issuer / `--issuer principal:bdo`) | 1 / 1 | `work ... recorded only on the session`; `work survives False`; Q1.2 `missing custody_or_lease; work does not survive the carrying session`; with the issuer Q1.1 and Q1.3 `holds` |
| `run --principal principal:claude-fable-5 --variant no-grant` (no issuer / `--issuer principal:bdo`) | 1 / 1 | identical readings to the no-issuer positive run in both; `--issuer` is discarded by `probe.py:101-102` |
| `env -u SOV_PRINCIPAL python scripts/sov_fresh.py run` | 2 | `REFUSED PRINCIPAL_REQUIRED: ...` |
| `SOV_PRINCIPAL=principal:somebody python scripts/sov_fresh.py run --principal principal:claude-fable-5 --issuer principal:bdo` | 1 | `P15-Q1.1: fresh participation required oral history`; `defect: undeclared environment inputs: SOV_PRINCIPAL` (F4 repaired) |
| `SOV_PRINCIPAL=principal:claude-fable-5 python scripts/sov_fresh.py run --issuer principal:bdo` | 0 | `PASS`; the variable is the declared channel when `--principal` is absent (`sov_fresh.py:60-62`) |
| `SOV_PRINCIPAL_REGISTRY=/nonexistent python scripts/sov_fresh.py run --principal principal:claude-fable-5 --issuer principal:bdo` | 1 | `principal UNIDENTIFIED`; Q1.1 `missing principal_id; required oral history`; `defect: undeclared environment inputs: SOV_PRINCIPAL_REGISTRY` (F10 traced) |
| `SOV_PRINCIPAL=principal:bdo python scripts/sov_fresh.py selfcheck` | 1 | `FAIL: fresh participation probe does not discriminate`; `positive variant failed: ... undeclared environment inputs: SOV_PRINCIPAL` (F18) |
| `SOV_PRINCIPAL_REGISTRY=/nonexistent python scripts/sov_fresh.py selfcheck` | 1 | `FAIL: no principal registry at /nonexistent` (F18) |
| `python scripts/sov_fresh.py run --principal principal:claude-fable-5 --issuer principal:nobody-at-all` | 0 | `PASS`; Q1.3 `holds` (F20) |
| `python scripts/sov_fresh.py run --principal principal:claude-fable-5 --issuer ""` | 1 | uncaught traceback ending `soveraeign_console_service.refusals.AuthorityRefused: a grant must name who issued it; an empty issuer is not a name` (F21) |
| witness's own drive of `scripts/sovfresh/node.py` functions against a temporary node (`open_node`, `admit(..., "principal:bdo", ...)`, `bind(..., session_id="session_deadbeefdeadbeef")`, `cross`) | 0 | composer verdict `BOUND`; Gateway reading `REFUSED`, stage `check-attribution`, `ACTOR_ATTRIBUTION_MISMATCH`, with `receipt_id` (the node's own foreign-session refusal, reachable and not driven by the probe: F19); the own `COMMITTED` receipt payload carries `detail.resolution` and no grant identifier (F22); `node.console.grants(reader_id=actor)` -> `AuthorityRefused: ... holds no live read:authority grant` |
| `python -m unittest scripts.tests.test_sov_fresh` | 0 | `Ran 15 tests in 2.335s OK` |
| `python scripts/sov_custody.py selfcheck` | 0 | `46 case(s), 27/27 declared refusals reached`; `selfcheck PASS` |
| `python scripts/sov_next.py --strict` | 0 | `scripts/sov_fresh.py [PRESENTED] drawn / custody custody:phase-1-5/fresh-participation`; `PASS: phase/custody precedence is explicit ...` |
| `python scripts/sov_active_phase_progress.py` | 0 | no output (pass-1 residual reproduced) |
| `python scripts/lint.py` | 0 | `PASS: repository hygiene (1186 text files, 553 Python modules, 10 named debt)` |
| `python scripts/verify.py` | 0 | `PASS: 51 checks in 15.862s wall`; `BUDGET DEBT: 9 check(s) over ceiling`, among them `fresh participation slice: 1.570s over its 1.500s ceiling` (F24); the `FAIL` lines in the output are planted tooling self-test output inside `repository tooling tests` |
| `python -c` over `sovverify.checks.CHECKS` after package import | 0 | 51 names, 51 distinct, `fresh participation slice` once (F13 repaired) |
| `python scripts/sov_fresh.py selfcheck` timed alone, three runs | 0; 0; 0 | 0.609s, 0.649s, 0.611s wall |
| `python scripts/sov_witness_layer.py records` (before writing) | 0 | `PASS: 7 witness receipt(s) graded, 0 unusable, 7 stale against their subject` (the pass-1 receipt is now `STALE_SUBJECT`, as expected once the subject moved) |
| recomputation of the pass-1 receipt's 24 `observed_state_digests` against `git show d40d61f:<address>` | 0 | 24/24 match |
| `python scripts/sov_standing.py`; `python scripts/sov_clarity.py check`; `python scripts/sov_docs.py check` (before writing) | 0; 0; 0 | `PASS: 1 standing claim(s)`; `PASS: clarity scope and receipts are well-formed and current`; `PASS: documentation page matches 281 documents` |
| `sha256sum` over 25 addresses | 0 | recorded in the receipt's `observed_state_digests` |

### Pass-1 findings, disposition at 161d559

- **F1 - repaired through the surface for two of three legs; the third is F19.**
  `other_actor_on_this_session` is refused by the Gateway at `check-attribution` with
  `ACTOR_ATTRIBUTION_MISMATCH` (`services/gateway/.../attribution.py:32`) and
  `other_actor_without_the_grant` at `check-authority` with `AUTHORITY_REFUSED` /
  `AuthorityRefused` (`services/gateway/.../core.py:247`); both are read from receipts the node
  wrote. `_mismatch` (`probe.py:70-87`) compares exact codes against `reason` or `diagnostic`
  and returns `REFUSED` only when the participant's own crossing `COMMITTED`; nothing but those
  three codes satisfies it. The `borrowed-authority` variant and the `sovkernel.authority`
  request are gone.
- **F2 - repaired.** `grant_id` is `admitted["grant_id"]`, the Console record
  `console.grant(actor, required_authority, SCOPE, granted_by=issuer)` returned
  (`node.py:49-51`); it names a grant the actor holds, and is `None` with no issuer, which the
  instrument fails as `missing grant_id`. Residual F22.
- **F3 - repaired through the surface.** `probe.py:99-100` substitutes
  `principal:unregistered-<session>` whatever the caller declared; the variant fails Q1.1 and
  Q1.3 with and without an issuer.
- **F4 - repaired as derived.** `oral_history_used` is `bool(layers.undeclared_inputs(declared))`
  (`probe.py:96,162`; `layers.py:24-31`) and fires on `SOV_PRINCIPAL` or
  `SOV_PRINCIPAL_REGISTRY` set and undeclared. The same derivation is what F18 trips on.
- **F5 - repaired as derived.** Cleanup is the custody's declared list plus leases the lease
  store reads as orphaned after the host session ended plus a console session the Record
  reads as `OPEN` (`probe.py:142-149`; `node.py:104-111`). The labels are the probe's, the
  facts are the stores'.
- **F6 - repaired.** `interface_binding_id` is `own_binding["interface_binding_id"]`, `None`
  on refusal (`node.py:73-74`; `probe.py:176`); observed as `missing interface_binding_id` on
  every no-issuer run.
- **F7 - repaired.** Codes, not verdicts (`probe.py:76-86`).
- **F8 - repaired.** `--json` is accepted after `run` (`sov_fresh.py:130-134`).
- **F9 - superseded.** The declared-evidence authority request no longer exists.
- **F10 - traced, partly.** An undeclared `SOV_PRINCIPAL_REGISTRY` now fails Q1.1 and is
  named. The observation still does not record which registry the principal resolved from,
  and `run` has no `--registry` argument: the builder's report says the registry "is now an
  explicit argument", which is true of `probe.run` and not of the CLI.
- **F11 - open, residual.** `survives` (`probe.py:145-146`) is true whenever a lease was taken
  and the store reads it orphaned; only declining the lease defeats it.
- **F12 - open, unchanged.** The stage is a declaration nothing measures.
- **F13 - repaired.** `checks.py:298` no longer imports `COMMISSIONING_CHECKS`;
  `sovverify/__init__.py:15` is the one splice; 51 distinct checks measured.
- **F14 - open, unchanged.**
- **F15 - repaired.** The report carries an "Independent witness" section.
- **F16 - open, unchanged** (`layers.py:22,80-93`).
- **F17 - open, residual (product), extended by F25.**

### New findings

- **F18 - MEDIUM, defect. `scripts/sovfresh/probe.py:96`; `scripts/sov_fresh.py:80,103-109`;
  `scripts/sovverify/clocks.py:135`.** `selfcheck` reads `FAIL` when the operator's
  environment carries `SOV_PRINCIPAL` (measured: exit 1, `positive variant failed ...
  undeclared environment inputs: SOV_PRINCIPAL`), although `layers.speaking_as` overrides both
  resolver variables for every selfcheck run, so the environment cannot change what selfcheck
  resolves. `cmd_selfcheck` passes no `declared` set and `probe.run` grades the operator's
  environment anyway. `fixture_registry` builds its copy from `principals.load(ROOT)`, which
  honours `SOV_PRINCIPAL_REGISTRY`, so the fixture's base is itself an undeclared environment
  input (`SOV_PRINCIPAL_REGISTRY=/nonexistent selfcheck` -> `FAIL: no principal registry`).
  `verify.py` launches every check through `Popen` without `env=`, so the custody's closure
  command and the `fresh participation slice` check go red on an input they do not read.
  Consequence: the closure check's verdict varies with the operator's shell; a check that
  fails on what it cannot see is the defect class this repository's history names.
- **F19 - MEDIUM, defect. `scripts/sovfresh/probe.py:56-58,76`; `scripts/sovfresh/node.py:1-6,64,88-90`;
  `scripts/sovnode/bindings.py:107-108`.** The `foreign_session` leg of `_mismatch` is
  satisfied by `SESSION_ATTRIBUTION_CONFLICT`, raised by the Node Interface binding composer in
  `scripts/sovnode/bindings.py` when the probe's own argument `session_id: "another-session"`
  disagrees with the binding's session id. The request never reaches the node, `cross` returns
  at stage `bind`, and no receipt exists (`--json` shows no `receipt_id` for that leg). The
  node's own refusal of a session it never opened was reachable through the `session_id`
  override on `node.bind` (`node.py:64`), which the probe never uses; driven directly, the
  Gateway refuses it at `check-attribution` with `ACTOR_ATTRIBUTION_MISMATCH` and a receipt.
  Consequence: the module docstring "the Gateway refuses or admits the crossing, and the
  receipt carries the reason" and the report's "every identity and refusal is read from the
  node's Console and Gateway records" are untrue of one of the three legs Q1.3 rests on.
- **F20 - MEDIUM, defect. `scripts/sov_fresh.py:6-7,137`; `scripts/sovfresh/node.py:38-51`;
  `services/console/src/soveraeign_console_service/permits.py:100-103`.** `--issuer` is
  described as "the seat that holds that authority" and "the seat opening this node's permits
  office". Nothing checks it. On a fresh node `permits.issue` runs `_genesis(console,
  granted_by)` for whoever grants first, so `--issuer principal:nobody-at-all` reads `PASS`,
  exit 0, Q1.3 `holds`. The registry that could have measured the name
  (`contracts/principals.json`, `root_principal: principal:bdo`) is loaded by the same run and
  not consulted; the observation's `issuer` field records the typed string as a seat.
  Consequence for P15-X1: the positive live run is a controlled fixture (temporary node, genesis
  seeded under a typed name), which is admissible as a demonstration that the mechanism
  separates identities and refuses borrowed ones, and is not evidence that any seat issued
  anything. The repair is the builder's: refuse an issuer the registry does not name as root,
  or name the flag for what it does and record it as a fixture in the observation.
- **F21 - LOW, defect. `scripts/sovfresh/node.py:48`.** `--issuer ""` escapes as an uncaught
  `AuthorityRefused` traceback from the Console; the node layer's own contract is that a
  refusal is returned, not raised.
- **F22 - LOW, residual (product receipt shape). `scripts/sovfresh/node.py:99`;
  `services/gateway/src/soveraeign_gateway_service/core.py`.** The `COMMITTED` receipt
  carries no grant identifier (`own.grant_id` is `null`), so "this crossing was admitted under
  `grant_id`" is inferred from the `check-authority` stage having passed, not read from the
  receipt. The actor cannot read its grants back (`console.grants` refuses without
  `read:authority`); the probe reads the grant from the write's return, which is the record as
  appended.
- **F23 - LOW, residual. `scripts/sovfresh/probe.py:155,174`.** Two sessions are reported under
  one label: Q1.1 `session_id` is the host session (`fresh-<id>`), Q1.3 `session_id` is the
  console session (`session_<id>`). The instrument does not relate them and a reader of the
  observation would take them for one.
- **F24 - LOW, residual. `contracts/verification-budget.json` (`fresh participation slice`:
  1.5); `contracts/custodies/phase-1-5.json:57`.** The check read 1.570s pooled at this
  commit, over the ceiling pass 1 saw set from 0.46s evidence before the repair added a node
  and three more crossings per variant; alone it reads 0.61-0.65s. Attributed debt, not a
  refusal. The same custody member's `note` now carries "findings repaired in the second
  commit", the builder's own repair claim inside a contract fixture before any witness read
  it; `stage_observed_by` is correctly `null`.
- **F25 - LOW, residual (product, not probe).** With an issuer and an `UNIDENTIFIED`
  principal (`--variant unregistered-principal --issuer principal:bdo`) the Console opens a
  session with `principal_id: null` and the Gateway `COMMITTED` the crossing; the probe's Q1.1
  and Q1.3 fail for the missing principal, so the product's admission is masked. Whether a
  crossing may commit for an actor whose durable principal nobody named is the Console and
  Gateway contracts' question, alongside F17's lease under a null controller.

### Conditions for a later pass to support `BUILT -> WITNESSED`

- C5 (F18): make `selfcheck` independent of the operator's environment: declare or scrub the
  two resolver variables it overrides, and read the fixture's base registry from the repository
  path, not the override.
- C6 (F19): drive the foreign-session leg through the Gateway (a session the node never opened,
  consistent in binding and arguments) and read the node's receipt; keep the composer's
  conflict as an additional reading if wanted, but not as the leg that satisfies Q1.3.
- C7 (F20, F21): either refuse an `--issuer` the registry does not name as `root_principal`,
  returning the refusal, or rename and document the flag as seeding a temporary node's genesis
  and carry that into the observation; return the empty-issuer refusal rather than raising it.
- C1 to C4 from pass 1 are discharged except as F19 narrows C1.

### Judgement items (questions, not the witness's to answer)

- J1 to J3 carried from pass 1. J1 is narrowed by the builder's choice: the instrument requires
  a grant, and a node with no issuer reads Q1.3 unmet.
- J4. May P15-X1 be observed against a temporary node whose root grant the probe itself seeded
  under a declared issuer name, once the name is checked against the registry, or does the
  clause want a node whose permits office the root seat opened and whose grant to this
  participant persists beyond the run?

### Uncovered

- `docs/documentation.html` was accepted on `verify.py`'s `documentation reader` and
  `sov_docs.py check`; the 15 changed lines were skimmed for shape only.
- The Console and Gateway services' own test suites were not rerun; their behaviour was read
  through the probe's node layer and one direct drive of the same functions.
- The Record Service's `evidence_projection` was not exercised beyond the probe's own call.
- No network, no `gh`, no ruleset query.

### Landing residual

As in pass 1: `scripts/sovdocs/facets.py:66` indexes `witness/*.md`, so after this section is
written `documentation reader`, `repository tooling tests` and `sov_docs.py check` are expected
to read the built page as stale. The witness may not rebuild the page; whoever lands this record
runs `python scripts/sov_docs.py build`. The exact readings after writing are in the receipt's
`telemetry.after_writing`.

## Pass 1: commit d40d61f (2026-09-06)

Verdict: **NOT-YET**.

Claim under observation, as the builder states it: a closed path session -> principal ->
campaign -> work -> lease -> capability -> authority -> Record projection -> session end ->
survival -> instrument, with P15-Q1.1 to Q1.3 graded by `conformance/commissioning.py` on a
live run and three defeating variants each failing their own predicate. Builder's report:
`reports/2026-09-06-fresh-participation-slice.md`. It was read after every command below had
run and is treated as the executor's self-report; nothing in this record is taken from it, and
where it is named it is named as a claim.

Commit witnessed: `d40d61fe83e10d6eca235ee2cfff5dc8e5ae2a27` on
`claude/phase-2-citizen-mechanics-inrozu`. `git status --short` was empty before and after every
command, `git rev-parse HEAD` read the commit throughout, and `.local/sov-sessions/` did not
change, so the probe wrote only to its temporary directories.

Witness: `claude-fable-5-1/sov-witness@2026-09-06`. This participant did not build, edit, stage
or commit anything under the subject. The only files it wrote are this record and
`witness/observations/2026-09-06-fresh-participation-observation.json`, both after every
command under `Verified` had returned.

### Standing supported

`BUILT`, unchanged. The build claim stands: the probe exists, runs through its declared
surface, its self-tests pass, and the repository gates read `PASS` at this commit. The
transition `BUILT -> WITNESSED` is not supported, because three of the fields the instrument
grades are written by the probe rather than derived from a product layer (F2, F4, F5), one
declared defeating variant passes through the declared surface (F3), and the cross-principal
half of P15-Q1.3 was never put to the product (F1). Each of those is the builder's to repair
inside the concern; none is a new ticket.

### Verified

Commands run from the repository root at the commit above. Exit codes are the process's own.

| Command | Exit | Reading |
| --- | --- | --- |
| `git rev-parse HEAD`; `git status --short`; `git show d40d61f --stat` | 0; 0; 0 | `d40d61fe...`; empty; 14 files, +803/-17 |
| `python scripts/sov_fresh.py selfcheck` | 0 | `PASS: fresh participation slice closes on the positive variant and 3 defeating variants each fail their own predicate` |
| `python scripts/sov_fresh.py run --principal principal:claude-fable-5` | 0 | `PASS`; `principal principal:claude-fable-5`; `phase phase:1-5 from STATUS.yaml@sha256:9ddb4c4f... + contracts/phases.json@sha256:05a27e13...`; `lease lease:custody-phase-1-5-fresh-participation-fresh-<id> held`; `capability asset.ingest-asset: own session BOUND, foreign session SESSION_ATTRIBUTION_CONFLICT`; `authority for 'principal:claude-fable-5': REFUSED AUTHORITY_REFUSED`; `work survives: True`; Q1.1, Q1.2, Q1.3 `holds` |
| `python scripts/sov_fresh.py run --principal principal:claude-fable-5 --json` | 2 | `error: unrecognized arguments: --json` (F8) |
| `python scripts/sov_fresh.py --json run --principal principal:claude-fable-5` | 0 | JSON; `identities.grant_id` = `grant:standing-landing-loop`; `interface_binding_id` = `urn:soveraeign:binding:node-interface:model-json-v1`; `cross_principal_session_mismatch` = `REFUSED`; `cleanup_obligations` = `["release lease:...", "end session fresh-..."]`; `oral_history_used` = `false`; `required_authority` = `ingest:asset`; `effect_envelope` = `RECORD_LOCAL` |
| `python scripts/sov_fresh.py run --principal principal:claude-fable-5 --variant unregistered-principal` | 0 | `fresh participation [unregistered-principal]: PASS`; all three predicates `holds` (F3) |
| `python scripts/sov_fresh.py run --principal principal:nobody --variant unregistered-principal` | 1 | `principal UNIDENTIFIED`; `lease ... held`; `own session REFUSED, foreign session SESSION_IDENTITY_REQUIRED`; `authority for '': REFUSED`; Q1.1 `fresh context missing principal_id`; Q1.2 `holds`; Q1.3 `identity separation missing principal_id; principal, session, grant, and interface binding collapsed` |
| `python scripts/sov_fresh.py run --principal principal:nobody` (positive variant) | 1 | identical readings to the row above: the variant name changes nothing in `probe.run` |
| `python scripts/sov_fresh.py run --principal principal:claude-fable-5 --variant work-dies-with-session` | 1 | `work recorded only on the session`; `work survives: False`; Q1.2 `durable work missing custody_or_lease; work does not survive the carrying session`; Q1.1, Q1.3 `holds` |
| `python scripts/sov_fresh.py run --principal principal:claude-fable-5 --variant borrowed-authority` | 1 | `authority for 'sov': PERMITTED grant:standing-landing-loop`; Q1.3 `cross-principal/session mismatch did not refuse`; Q1.1, Q1.2 `holds` |
| `env -u SOV_PRINCIPAL python scripts/sov_fresh.py run` | 2 | `REFUSED PRINCIPAL_REQUIRED: declare the registered principal ... the registry names, it does not guess` |
| `python -m unittest scripts.tests.test_sov_fresh` | 0 | `Ran 11 tests in 1.199s OK` |
| `python scripts/sov_custody.py board custody:phase-1-5/fresh-participation` | 0 | `VERTICAL_SLICE 1`, `ITEM scripts/sov_fresh.py [build claim]`; `closes when COMMAND python scripts/sov_fresh.py selfcheck`; estimate `grants 0..1 PENDING`, `judgement_units 1..1 PENDING` |
| `python scripts/sov_custody.py selfcheck` | 0 | `46 case(s), 27/27 declared refusals reached`; `selfcheck PASS` |
| `python scripts/sov_active_phase_progress.py` | 0 | no output (the builder's residual about a silent pass is reproduced) |
| `python scripts/sov_next.py --strict` | 0 | `scripts/sov_fresh.py [PRESENTED] drawn / custody custody:phase-1-5/fresh-participation`; `PASS: phase/custody precedence is explicit ...` |
| `python scripts/verify.py` | 0 | `PASS: 51 checks in 14.098s wall`; `GRADE: SILVER`; `BUDGET DEBT: 8 check(s) over ceiling` (attributed, non-refusing); `TIME: fresh participation slice: 1.107s wall, 0.483s cpu`. The `FAIL` lines in the output are planted tooling self-test output inside `repository tooling tests`; the verdict is the `PASS: 51 checks` line and the exit code |
| `python -c` over `sovverify.checks.CHECKS` after package import | 0 | 51 names, 51 distinct; `REPOSITORY_CHECKS` 41, `PARTICIPANT_CHECKS` 7 |
| `python scripts/sov_fresh.py selfcheck` timed alone, three runs | 0; 0; 0 | 0.463s, 0.462s, 0.456s wall |
| `python scripts/lint.py` | 0 | `PASS: repository hygiene (1183 text files, 552 Python modules, 10 named debt)` |
| `python scripts/sov_snapshot.py` | 0 | `PASS: 9 of 10 snapshot claim(s) match the record` (commits not checked here: shallow clone) |
| `python scripts/sov_clarity.py check` | 0 | `PASS: clarity scope and receipts are well-formed and current` |
| `python scripts/sov_traps.py` | 0 | `PASS: 2 trap(s) still hold, 3 recorded for attended checking` |
| `python scripts/sov_standing.py`; `python scripts/sov_witness_layer.py records` (before writing) | 0; 0 | `PASS: 1 standing claim(s)`; `PASS: 6 witness receipt(s) graded, 0 unusable, 6 stale against their subject` |
| `sha256sum` over 24 addresses | 0 | recorded in the receipt's `observed_state_digests` |

### Findings

Severity names the consequence if the member were ratified at `VERTICAL_SLICE` as-is. Defects
are the builder's to repair inside the concern; residuals are recorded and hold nothing.

- **F1 - HIGH, defect. `scripts/sovfresh/probe.py:101,127-130`; `scripts/sovfresh/layers.py:160-184`.**
  `cross_principal = graded["verdict"] == "REFUSED"` reads the participant's own authority
  request, made as its own actor, for a capability no grant gives it. `AUTHORITY_REFUSED` there
  is the ordinary absence of a grant, not a refused cross-principal mismatch. No product layer
  was handed a session principal together with another actor's grant and asked to refuse. The
  `borrowed-authority` variant swaps the request's actor for `sov`, and `sovkernel.authority`
  correctly reads `PERMITTED` for `sov`; nothing in what the probe drives could have refused it,
  so the variant defeats the probe's own derivation, not the product. A product seam that does
  bind a session to a grant exists (`bindings/mcp/gateway.py:173-215`, `SESSION_NOT_LIVE`,
  `GRANT_NOT_HELD`) and was not driven. Consequence: the second clause of P15-Q1.3 reads as
  observed when it was never exercised against the product.
- **F2 - HIGH, defect. `scripts/sovfresh/layers.py:182`; `scripts/sovfresh/probe.py:162`;
  `scripts/tests/test_sov_fresh.py:72`.** `grant_id` is `result.get("grant_id") or considered[0]`:
  when the participant is refused, the identity slot is filled with the grant that refused it.
  The honest reading of a principal no grant names is `None`, which the instrument
  (`conformance/commissioning.py:49-51`) would fail as `identity separation missing grant_id`.
  The probe supplies a value the participant does not hold, and the unit test pins
  `grant:standing-landing-loop` as the fresh participant's grant identity. "Grant authority
  remains distinct" is satisfied here only by string inequality; the grant named is somebody
  else's authority. Consequence: a ratified Q1.3 would rest on an identity the participant
  never held.
- **F3 - HIGH, defect. `scripts/sov_fresh.py:91-93`; `scripts/sovfresh/probe.py:37-43,68-71`.**
  The `unregistered-principal` variant is not implemented in `probe.run`; the self-check harness
  substitutes `principal:nobody` as caller input. Through the declared surface,
  `run --principal principal:claude-fable-5 --variant unregistered-principal` reads `PASS`,
  exit 0, labelled `[unregistered-principal]`. A declared defeating variant that passes is a
  defeating fixture that does not defeat, and a reader of the `run` output cannot tell.
- **F4 - MEDIUM, defect. `scripts/sovfresh/probe.py:146`.** `"oral_history_used": False` is a
  constant. The instrument's oral-history check (`conformance/commissioning.py:31-32`) can never
  fire from this probe. Nothing derives the flag from where each field came from; the principal
  id itself is supplied by the operator and written into the resolver's environment by
  `layers.speaking_as` (`layers.py:33-47`). Asserted, not earned.
- **F5 - MEDIUM, defect. `scripts/sovfresh/probe.py:131-133`.** The custody declares
  `cleanup_obligations: []`, `contracts/work-lease.schema.json` carries no cleanup field, and the
  two strings the observation reports are composed by the probe. `durable work missing
  cleanup_obligations` cannot fire on the positive path. The strings name the participant's own
  inventory; P15-Q1.2 asks for the work's obligations that survive the session. Written by the
  participant that ran it, which is what `contracts/work-circuit.json` VERTICAL_SLICE evidence
  forbids.
- **F6 - MEDIUM, defect. `scripts/sovfresh/probe.py:163-164`.** `interface_binding_id` falls
  back to `layers.SESSION_BINDING`, a probe constant, when the product refused the binding. In
  the unidentified path the binding was `REFUSED SESSION_IDENTITY_REQUIRED` and the observation
  still carries a non-empty interface binding. Q1.3 fails there for another reason, so the
  fallback is masked today; it hides a product refusal behind a probe-written identity.
- **F7 - LOW, defect. `scripts/sovfresh/probe.py:127`.** `cross_session` is any `REFUSED`
  verdict, not `SESSION_ATTRIBUTION_CONFLICT`. In the unidentified path a
  `SESSION_IDENTITY_REQUIRED` refusal counts as the cross-session refusal.
- **F8 - LOW, residual. `scripts/sov_fresh.py:126`.** `--json` is on the root parser;
  `run --principal X --json` exits 2. `--json run ...` works. The report's command table does
  not claim the failing form, so no false claim; the surface is awkward.
- **F9 - LOW, residual. `scripts/sovfresh/layers.py:166-176`.** The authority request declares
  `evidence.checks verify/lint PASS`, `branch main` and a path; declared, not measured. It is
  what makes `borrowed-authority` read `PERMITTED`, so that variant's reading rests on a
  declaration.
- **F10 - LOW, residual. `scripts/sovsession/principals.py:46-49`; `scripts/sovfresh/layers.py:52-59`.**
  `run` reads `SOV_PRINCIPAL_REGISTRY` from the operator's environment through the resolver and
  the observation drops `claim["registry"]`, so an environment that swaps the registry leaves
  no trace in the grade. This is the one input read from the environment other than the
  declared principal.
- **F11 - LOW, residual. `scripts/sovfresh/probe.py:117-120`.** `survives_session` is true
  whenever a lease was taken: the session end is a raw `end` event, the product's
  `sov_session.py end` does not release leases either, and `lease_store.leases` projects `HELD`
  regardless of session events. Derived, but only the probe declining to take a lease can
  defeat it.
- **F12 - MEDIUM, judgement on the stage claim.** Against `contracts/work-circuit.json`
  VERTICAL_SLICE: both admission predicates are met (an ordered path is named; the path closes on
  a re-runnable check). The evidence predicate, "its result is derived from the run, never
  written by the participant that ran it", is met in part: F2, F4, F5 and F6 are written. Also,
  `contracts/custody.schema.json` `$defs/member` carries no evidence field and
  `scripts/sovcustody/model.py` never calls `circuit.judge_advance` on a member, so the stage is a
  declaration nothing measures. That is the custody model's design, not this builder's; it is
  why this record, not the board, is where the stage claim gets read.
- **F13 - LOW, residual. `scripts/sovverify/__init__.py:11-15`; `scripts/sovverify/checks.py:19,301`.**
  `COMMISSIONING_CHECKS` is spliced in twice, in two orders (the package init also includes
  `INTEGRITY_CHECKS`; `checks.py` does not). `verify.py` imports after the package init, so the
  run reads 51 distinct checks (measured). Sound today; a drift hazard. The named ceiling of
  1.5s is set from evidence: 0.456-0.463s alone, 1.107s pooled.
- **F14 - LOW, residual. `contracts/custodies/phase-1-5.json` closure; `scripts/sovverify/commissioning.py:17`.**
  No reader executes a custody's closure command (`sovcustody/board.py` prints it; its
  subprocess at `:35` is `sov_worklist.py derive`). `verify.py` runs the same command through a
  separately declared `Check`. Two declarations of one command string, nothing ties them. The
  command does run today (exit 0), so `decisions/0102`'s defeating case does not fire.
- **F15 - LOW, residual. `reports/2026-09-06-fresh-participation-slice.md:12`.** "Independent
  witness: see the section below" names a section that does not exist in the report.
- **F16 - LOW, residual. `scripts/sovfresh/layers.py:27,74-86`.** The work the fresh participant
  accepts is the custody whose member is the probe itself. The slice resolves no work other than
  its own custody.
- **F17 - LOW, residual (product, not probe). `scripts/sovfresh/layers.py:101-118`.** With an
  `UNIDENTIFIED` principal the lease is still taken with `controller_principal: null` and
  validates against `contracts/work-lease.schema.json`; Q1.2 holds for a participant nobody
  named. Whether a lease may be held under no controller is the lease contract's question.

### Conditions for a later pass to support `BUILT -> WITNESSED`

- C1 (F1, F7): derive `cross_principal_session_mismatch` from a product refusal of a request
  that carries this session's principal together with a grant or actor it does not hold, and
  compare refusal codes, not verdicts.
- C2 (F2): report `grant_id` as the grant the participant holds, `None` when it holds none, and
  let the instrument or its fixture say what shape "no grant held" takes.
- C3 (F3): make every declared variant change what `probe.run` does, so `run --variant` cannot
  pass for a variant that is declared to fail.
- C4 (F4, F5, F6): replace the three constants with values derived from a layer, or report the
  layer's honest value and let the predicate fail.

### Judgement items (questions, not the witness's to answer)

- J1. May the P15-Q1.3 instrument admit "no grant held" as a distinct identity, or must a fresh
  participant hold a grant before the clause can be observed?
- J2. Is re-pointing an exit custody's closure check away from the reader `decisions/0102`
  named an ordinary reversible default, or does it want a note in the decision record?
- J3. The model serving the builder's session is `claude-fable-5-1`; the registry names
  `principal:claude-fable-5`. Does the version drift want a registry entry? (Builder's
  residual; identity naming is owner-held.)

### Uncovered

- `docs/documentation.html` was accepted on `verify.py`'s `documentation reader` check; the 12
  changed lines were not read.
- The clarity receipt for `CLAUDE.md` was accepted on `sov_clarity.py check`; the prose was not
  re-reviewed.
- The Record Service's `evidence_projection` was not exercised beyond the probe's own call.
- No network, no `gh`, no ruleset query.

### Landing residual

`scripts/sovdocs/facets.py:66` indexes `witness/*.md`, so with this record present
`documentation reader` and `repository tooling tests` are expected to read the built page as
stale, as pass 3 of `witness/observation-service.md` recorded. The witness may not rebuild the
page; whoever lands this record runs `python scripts/sov_docs.py build`. The exact readings
after writing are recorded in the receipt's `telemetry.after_writing`.
