# Witness record — office-act-and-citation (PR #225)

```witness
standing_supported  BUILT -> WITNESSED (citation-gate repair; the recorded act and reading as journal facts)
subject             office-act-and-citation
revision            a13b888f860a0b866d706f04e9eacd22fda769af
pass                1
```

## Pass 1: commit a13b888 (2026-09-07)

**Verdict: RATIFIABLE-WITH-CONDITIONS.** Every claim the builder makes about the
artifact reproduces, including the two the report itself hedges. What holds the
verdict short of clean is not a false claim: it is that the repaired gate now takes
on trust the one field it used to measure, three mutants of the changed code survive
the shipped fixtures, and the session's own attribution drift is disclosed in a note
rather than carried anywhere a later reader of the record would meet it.

- **Commit witnessed:** `a13b888f860a0b866d706f04e9eacd22fda769af`, HEAD of
  `claude/sovereign-phase-1-5-5uzffu`; base `6498fc7b3172476df54882d7b65c47f52366c8c8`;
  candidate tree `789c4348c497bcdccb0e8664c866f954185ff04d`.
- **Working tree witnessed against:** the `<this worktree>` worktree at
  `a13b888`, porcelain empty before every measurement and holding only this
  participant's own deposits after. `git rev-parse HEAD` was re-read before and after
  every command and never moved. Measurements ran in a full-history clone at the same
  commit with empty porcelain; node runs ran against this participant's own restores,
  never against `.local/node-interface`.
- **Observed:** 2026-09-07T17:45Z (UTC).
- **Receipt:** `witness/observations/2026-09-07-office-act-and-citation-observation.json`.
- **Landing record:** `.local/observations/2026-09-07-office-act-and-citation-landing.json`.
- **Principal:** `SOV_PRINCIPAL=principal:claude-fable-5-1` for every command.
- **Independence:** this participant built nothing here and edited no file under
  `scripts/`, `nodes/`, `reports/`, `contracts/` or `services/`.

### Claim

From `git show a13b888`: the node was restored from the committed export
`nodes/node-local/journal/23d3b48086be.json` into an empty state, `sov_fresh.py
open-office` was run in the root seat's name and granted `principal:claude-fable-5-1`
three capabilities, and that principal then read the registry through the node. And:
`_cited_export`/`_grade_citation` let a self-report keep its citation while the node
records more, by pinning the cited head to a position in the node's current chain
instead of to an export filename.

### Observed

**1. The act. Reproduced.** Restoring `a8b989484adf.json` into a scratch node and
querying the restored SQLite store — not the JSON — finds all three grants with the
exact identifiers the report names, at entries 118, 120 and 122, each `granted_by
principal:bdo` and naming `operator_id principal:claude-fable-5-1`:
`grant_fdf1477d279244db` `open:session`, `grant_e37a2885580a4e62` `close:session`,
`grant_553ce95769c74292` `read:registry`. Entry 85 of the same chain has digest
`23d3b48086be...`, and its 85-entry prefix is byte-identical to the export this
commit deletes, read from base `6498fc7`. That prefix carries no grant to
`principal:claude-fable-5-1` and no mention of it anywhere; its seven grants name
`principal:bdo` and `principal:claude-fable-5`.

`sov_fresh.py run --principal principal:claude-fable-5-1 --node-state <my restore>`
exits 0, `PASS`, `registry.resolve` `COMMITTED`, `P15-Q1.1`, `P15-Q1.2` and `P15-Q1.3`
all `holds`, with `foreign_session` and `other_actor_on_this_session` refused
`ACTOR_ATTRIBUTION_MISMATCH` and `beyond_the_grant` refused `AuthorityRefused`. The
same run as `principal:claude-fable-5` also exits 0 with all three predicates holding,
because that principal holds its own grants at entries 5, 7, 55, 57 and 59; so that
run is not the defeating case for this act and should not be read as one.

The defeating case this participant ran instead: the same command as
`principal:claude-fable-5-1` against a restore of the **pre-act** 85-entry export
exits 1, `FAIL`, `registry.resolve` `REFUSED SESSION_IDENTITY_REQUIRED`, `P15-Q1.3`
unmet, and the node says `principal:claude-fable-5-1 holds no live open:session grant
for this operation`. The act is what changed the outcome, and the record already
contains its own copy of that refusal at entries 111 to 117.

The report's identity claims are record-borne: entry 154 is a
`gateway-authority-check` naming `authority_grant_id grant_553ce95769c74292`,
`required_authority read:registry`, `decision ALLOWED`, inside session
`session_5bbe1d42cdd64427`, which is entries 149 to 173. The registry digest the
report quotes is the sha256 of `contracts/principals.json` at this commit.

**2. The citation repair. Reproduced.** The 2026-09-06 report cites head
`23d3b48086be...`, which is entry 85 of the 173-entry chain; it declares 85 entries,
which is that position; and the nine entry ids it names are all inside the prefix.
`python scripts/sov_node.py journals` exits 0. Independently constructed cases refuse
as claimed: a node with no export, a head that is not an entry of the chain, an entry
recorded after the cited head, a `journal` field with no head, and a traversal
address. A head that a twin node reaches only *later* is caught, because an entry
digest binds `prev_digest`, so finding the cited head in the chain proves the whole
prefix under it.

**3. What it weakened.** See F1 and F2. The node-directory derivation cannot resolve
to a *different* node — `nodes/node-other/...` fails on the directory prefix — but it
does resolve any path under the right node directory, including one naming a file
that never existed.

**4. Gates.** On a clean full-history clone at `a13b888`, empty porcelain:

| command | exit | reading |
| --- | --- | --- |
| `python3 scripts/verify.py` | 0 | `PASS: 52 checks in 15.589s`; wall-clock and per-check budget debt, no semantic failure |
| `python3 scripts/lint.py` | 0 | `PASS: repository hygiene (1225 text files, 562 Python modules, 10 named debt)` |
| `python3 scripts/sov_node.py journals` | 0 | one export replays; every citation resolves (run twice) |
| `python3 -m unittest scripts.tests.test_sov_node_journal` | 0 | 16 tests OK (run twice) |
| `python3 scripts/sov_witness_layer.py records` | 0 | 27 receipts, 0 unusable |
| `python3 scripts/sov_clarity.py check` | 0 | scope and receipts current |
| `python3 scripts/sov_diagrams.py` | 0 | 8 views, 0 stale |

The 19 `CONF-*-DEF` lines and the `FAIL: declared refusals no case fires: SELF_GRADED`
line inside the verify log are defeating fixtures and planted cases firing as
declared, not failures; `verify.py`'s own verdict is exit 0. Under `CLAUDE.md` T2,
that green means unchanged, not qualified.

**5. Diff scope.** `git diff --name-status 6498fc7..a13b888` carries exactly the five
declared paths and nothing else. No secret shape, no absolute host path, no weakened
oracle outside the one this change is about. The deleted export loses no evidence: its
85 entries are the exact prefix of the new one, and its bytes remain at `6498fc7`.
`scripts/sovnode/journal.py` is 211 lines.

### Findings

**F1 — the gate now trusts the one field it used to measure.** `_cited_export`
resolves by node directory, so `journal.address` no longer has to name a file that
exists. A report naming `nodes/node-local/journal/dddddddddddd.json`, or
`nodes/node-local/not-a-journal/z.json`, with a true head, a true count and true entry
ids, passes with no defect. This is not hypothetical: the 2026-09-06 report's address
`nodes/node-local/journal/23d3b48086be.json` is deleted **by this commit**, and the
`verify` command that report prints for a reader now names a file that is not in the
tree — and `journals` says every citation resolves. The head pin is a measurement and
is sound; the address is a declaration next to it, and the gate could compare the two
for the price of one line. Cheapest repair inside the concern: report the resolved
export when it differs from the cited address, or repair the older report's address,
or drop the field to the node and keep the head as the pin.

**F2 — three mutants of the changed code survive the shipped fixtures.** Nine were
run; six die. Survivors: the entry-count check weakened from `!= position` to
`> position`, so a report may under-declare what it read and pass — the suite only
ever over-declares; the node derivation weakened from the node directory to the
journal directory, so the granularity the new docstring asserts has no fixture; and
the head matched by `startswith` instead of equality, which would admit the
12-character head prefix this repository uses for its own export filenames. Each needs
one case.

**F3 — most of the report's identities are outside the gate's reach.** `ID_KEYS` is
`("entry_id", "receipt_id")`, unchanged. A constructed report naming
`grant_never_recorded_0000` and `session_never_recorded` passes. The new docstring
says "the report may name only entries that existed at that head", which is broader
than what `_ids_in` enforces. In the subject report, three of about twelve
record-borne identities are graded; this participant checked the rest by hand and all
are true.

**F4 — a version number doing a contract's work.** `observation_schema:
soveraeign-fresh-participation-live-node/v3`. That identifier, and `v1` and `v2`
before it, appear nowhere in the repository except in the three reports declaring
them. No schema document, nothing validating against one.

**F5 — the direction is not in the record.** `open-office` takes `--direction` and
`--directed-in` and writes them to `<node-state>/office-acts.ndjson`, which is
gitignored runtime state; the journal entries carry `granted_by` and no direction. So
the only surviving attribution of the act to Bdo is prose in the builder's own report,
which is the artifact that cannot witness itself. The report says that plainly, and
the command's own docstring says the act line "proves nothing the journal does not".
Both are honest. The gap is real anyway, and it is the reason this observation
supports no standing for the authorization.

**F6 — the model drift is noted, not seamed.** The report states that the serving
model became Claude Opus 5 partway through while the session kept declaring
`principal:claude-fable-5-1`. `contracts/principals.json` still describes that
principal as "the model the host reports serving this node's interactive sessions
since 2026-09-06", and this commit leaves it there while adding about sixty journal
entries whose actor is that principal, with no counter-record. Principal identity and
naming are owner-held under `contracts/acceptance-policy.json`, so the fix is not the
builder's to make alone — but a disclosure in a JSON `note` field is neither
presented nor held at a named seam.

**F7 — the narrative is incomplete, in the builder's own favour.** The export carries
88 entries past the restored prefix; the report narrates the office act and one run.
Unreported: entries 86–110, a committed run as `principal:claude-fable-5`; entries
111–117, `principal:claude-fable-5-1` refused `NO_LIVE_GRANT` before the act, which is
the live defeating case and the strongest thing in the file; and entries 124–148, an
earlier committed run. The report names the later run, which is correct.

**F8 — the witness deposit turns the tree red, and that is the landing path's
problem, not the change's.** `verify.py` exits 0 on a clean clone at `a13b888` and
exits 1 on this worktree once this witness's own two deposits exist, because
`sov_docs.py` counts every document under `witness/`; `docs/documentation.html` and
`docs/surface.html` then read stale. Attributed by moving the two deposits aside and
re-running `python scripts/sov_docs.py check`, which returns to `PASS: documentation
page matches 286 documents`. No defect of the builder's is involved. It matters
because `sov_land.py` runs verify before its gate, so absorbing a witness record means
rebuilding both pages in the same commit or the landing refuses for a reason that has
nothing to do with the work. The `FAIL: 1 defects in the acceptance routing` and
`FAIL: declared refusals no case fires: SELF_GRADED` lines appear in the clean-clone
log too: they are planted cases proving their checks refuse, and reading them as
failures is the trap this repository has already been bitten by.

### Judgement

Two questions this observation cannot answer and does not try to.

1. Does Bdo affirm that he directed the act recorded at entries 118 to 123 of
   `node:local`, in the words quoted in `office_act.direction`? Nothing in the node,
   the export, the report or this witness authenticates who passed the name
   `principal:bdo`. Three grants now stand in the root seat's name on the strength of
   a self-report.
2. Should `contracts/principals.json` be amended, or a counter-record recorded in the
   node, now that acts attributed to `principal:claude-fable-5-1` were performed by a
   differently-versioned serving model?

### Standing

**BUILT -> WITNESSED** for the citation-gate repair in `scripts/sovnode/journal.py`,
and for the office act and the live reading **as facts of `node:local`'s journal at
`a13b888`**. Not supported: any claim that the root seat authorized the act. This
observation settles nothing; it is an observation, not a ratification.

### Commands

```
git clone --no-local <this worktree> <clone>          exit 0
git -C <clone> checkout a13b888                                exit 0  tree 789c4348, porcelain empty
python3 scripts/sov_node.py restore-journal --export nodes/node-local/journal/a8b989484adf.json
    --node-state <scratch> --expect-head a8b989484adf...       exit 0  173 entries
python3 scripts/sov_fresh.py run --principal principal:claude-fable-5-1 --node-state <scratch>
                                                               exit 0  PASS, three predicates hold
python3 scripts/sov_fresh.py run --principal principal:claude-fable-5 --node-state <scratch2>
                                                               exit 0  PASS, three predicates hold
python3 scripts/sov_fresh.py run --principal principal:claude-fable-5-1 --node-state <pre-act>
                                                               exit 1  FAIL, P15-Q1.3 unmet
python3 scripts/verify.py                                      exit 0  PASS: 52 checks
python3 scripts/lint.py                                        exit 0
python3 scripts/sov_node.py journals                           exit 0  (twice)
python3 -m unittest scripts.tests.test_sov_node_journal        exit 0  16 tests (twice)
python3 scripts/sov_witness_layer.py records                   exit 0
python3 scripts/sov_clarity.py check                           exit 0
python3 scripts/sov_diagrams.py                                exit 0
nine-mutant run over scripts/sovnode/journal.py                6 killed, 3 survived
nine adversarial citation cases against journal.grade()        6 refused as expected, 3 admitted (F1, F3)
```
