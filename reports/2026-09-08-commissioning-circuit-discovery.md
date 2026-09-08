# Discovery report: reaching the most recently settled work from a cold start

Written 2026-09-08 by a participant with no prior history at this node, working
read-only on `this repository` except for this file. Nothing was committed
anywhere. The capability found was run, not modified.

This is the exercise `P15-X3` names: "Another fresh participant can then discover
the accepted result, reconstruct why it stands, reach the capability it produced,
and use it without builder-private state or oral history."

---

## 1. What was found

**The most recently closed piece of work at this node is
`lease:concern-schematically-golden-rendered-text`, closed 2026-09-08T15:25:20Z
at standing `BUILT`.**

The work it carried is a golden-corpus rendered-text QA check in a *different*
repository, `schematically`, at
`schematically/tests/golden_rendered_text_qa.py`
(commits `3f652a7`, repaired at `e51b999`, on branch
`claude/movement-72-hours-2claax`, four commits ahead of `origin/dev` at `6e0fe55`).

It is closed, and it is not settled in the full sense this repository means. The
closing act attempted `WITNESSED` and was refused; `BUILT` is what the record
carries. Section 2 states exactly what that buys and what it does not.

### The exact path, in order, including the dead ends

| # | Command | Result |
| --- | --- | --- |
| 1 | `ls -la this repository` | Layout. Noted `acceptance/`, `witness/`, `reports/`, `decisions/`, `.local/`. |
| 2 | `git log --oneline -20`, then `git log --format='%h %ad %s' --date=short -60` | Newest commits are `report:` commits dated 2026-09-08 on `claude/movement-72-hours-2claax`. A commit is not a settlement, so this only narrowed the window. |
| 3 | `ls -t reports/`, `ls -tR acceptance/` | Newest report `reports/2026-09-08-commissioning-circuit-reconnaissance.md`. Acceptance packets `A1`-`A24`; ten under `acceptance/accepted/`. |
| 4 | `sed -n '1,120p' STATUS.yaml` | Phase `phase:1-5`, open since 2026-09-03. Line 88 names `.local/acceptance/ledger.ndjson` as the record of owner acceptances. |
| 5 | **Dead end.** `cat .local/acceptance/ledger.ndjson` | `No such file or directory`. `.local/` is gitignored and holds only `registrar/` and `landing/`. The record STATUS.yaml calls authoritative for acceptance is not in the artifact at all. |
| 6 | `grep -n "owner_accepted" -A 60 STATUS.yaml` | Newest owner `ACCEPT` is `A19`, 2026-08-28T18:04:42Z; newest dispositions 2026-08-30. Too old to be the answer, but it fixes the ceiling for "owner-accepted". |
| 7 | **Near dead end.** `tail -3 .local/landing/ledger.ndjson` | Twelve landing records, all `"grant_id": "grant:test"`, `"from_branch": "work"`, all stamped `2026-09-08T14:38:05Z`. These are fixtures written by a test run, not landings. A reader who took the newest row here would report a landed change that never existed. |
| 8 | `ls -la witness/ witness/observations/` | Witness records to 2026-09-06 (`fresh-participation`), plus `reports/observations/*` to 2026-09-08 for CI-retention work. Candidates, but all attached to work already merged and older than the window in step 2. |
| 9 | `sed -n '1,80p' reports/2026-09-08-commissioning-circuit-reconnaissance.md` | **The hinge.** A committed report describing a Phase 1.5 commissioning lap whose payload is `concern:schematically/golden-rendered-text` "in the schematically repository". Names the lease, the closure condition, the defeating condition, and the stage-by-stage trace. |
| 10 | `sed -n '80,400p'` on the same file | Stages 6-12: execution carried, two independent readings formed, comparison and repair done, settlement **refused** at `WITNESSED`, lease closed at `BUILT`, no receipt produced. Findings F1-F20. |
| 11 | **Dead end.** `python3 scripts/sov_lease.py status --json` | `{"leases": [], "orphaned": []}`. The status projection shows live leases only; the closed lease that is the answer is invisible through the node's own CLI. |
| 12 | `sed -n '1,60p' scripts/sovlease/store.py` | Module docstring gives the store location: two ndjson logs "under the repository's common git directory". |
| 13 | `find / -name "*.ndjson" -path "*sov*"` then read `.git/sov-sessions/leases.ndjson` | The settlement record itself: one `take` at 2026-09-08T14:45:26Z, one `close` at 2026-09-08T15:25:20Z with `standing_reached: BUILT`, `receipt_id: receipt:lap/golden-rendered-text`, `witnessed_by: null`, and four evidence addresses. |
| 14 | `python3 -c` over `nodes/node-local/journal/a8b989484adf.json` | Cross-check for anything newer in the operational Record: 173 entries, last one a `console.close-session` receipt at 2026-09-07T17:27:10Z. Older. |
| 15 | `python3 scripts/sov_accept.py audit` | `PASS: 16 ruling(s), 6 presented for acceptance, 1 admissible hold(s), 0 open questions`. Nothing newer waiting on the owner. |
| 16 | `python3 scripts/sov_active_phase_progress.py` | `6 exit clause(s); 0 earned`. `P15-X5` reads `ROOT_POINT`, 2 members, `NOT_EARNED`. The lap earned the phase nothing. Consistent with a close at `BUILT`. |
| 17 | `python3 scripts/sov_session.py brief` | Run late, as a check on the front door. It gives phase, gate, exit clauses and "discover what this node exposes"; it names no recent work and would not have led here. |

Four settlement stores were checked before answering: the acceptance ledger
(missing), the landing ledger (test fixtures), the node journal (2026-09-07),
and the lease log (2026-09-08T15:25:20Z). The lease close is the newest.

### The ambiguity, stated rather than resolved

"Settled" has two defensible readings here and the record does not choose:

- **Most recently *closed*** — the lease above. Closed with evidence, at `BUILT`,
  by the participant that held it. This is what this report answers.
- **Most recently *witnessed and merged*** — the discovery-and-reuse slice of
  2026-09-07 (`reports/2026-09-07-discovery-and-reuse-slice.md`,
  `witness/discovery-and-reuse.md`, packet `acceptance/A24.json`, merge `6498fc7`).
  Independently witnessed, merged to the trunk, and presented for acceptance.
- Under the strictest reading — root acceptance — the answer is much older:
  `A19`, 2026-08-28.

I chose the lease because it is the newest act that *terminated* a piece of work
with evidence, and because the capability it produced exists and can be run,
which is what parts 3 and 4 ask for. A reader who wants "the newest thing that
reached `WITNESSED`" should read 2026-09-07 instead.

---

## 2. Why it stands, and what could not be reconstructed

### The claim

From `.git/sov-sessions/leases.ndjson`, the closure condition fixed at lease time
(14:45:26Z, before any work):

> A golden-corpus check exists that compares rendered text; it passes on
> schematically dev and fails at `1f213c7` where the caption regression was live

Defeating condition, fixed at the same moment:

> The check passes at `1f213c7`, or it only passes because it asserts nothing
> about text

That both conditions were required at `take` and refused without is finding F6 of
the lap report, and it is the strongest thing about this record: the bar was set
before the work, by the same mechanism that later refused to inflate the result.

### The evidence

Four addresses in the close event:

- `schematically@e51b999 tests/golden_rendered_text_qa.py` - the check
- `schematically@fb56f9c LAP-EXECUTION-REPORT.md` - the builder's account
- `schematically FINDING-WORK.md` - independent reading of the work
- `schematically FINDING-PARTICIPANT.md` - independent reading of the carrying

Note that two of the four carry no revision. `FINDING-WORK.md` and
`FINDING-PARTICIPANT.md` are cited by filename only; both were committed at
`d406790`, after the repair `e51b999` that they caused. Nothing in the record
pins them.

### Who observed it

Two participants that did not build the change and could not see each other:

- `FINDING-WORK.md`, subject `claude/movement-72-hours-2claax` at `fb56f9c`.
  Verdict **MET WITH QUALIFICATION**. It reproduced both halves of the closure
  condition, then went past the builder: it reintroduced the `1f213c7` defect into
  current `src/10-model.js` and the check killed it, so the suite tracks a defect
  class rather than one historical commit.
- `FINDING-PARTICIPANT.md`, subject the conduct in `LAP-EXECUTION-REPORT.md`.
  Verdict **CARRIED WELL**, with four minor reporting defects named.

Both independently ran the same counterfactual - the nine pre-existing corpus
documents at `1f213c7` with the new anchor removed - and both got a pass. That is
what makes the corpus extension a build of the check rather than a rig of it.

### The standing, and why it is only `BUILT`

The close attempted `WITNESSED` citing both readings by address and was refused:

```
REFUSED UNWITNESSED_STANDING_CLAIM
```

`scripts/sovkernel/work_lease.py:220-231` is the rule: a `WITNESSED` claim needs a
child lease whose holder relation is `WITNESS` and whose `principal_id` differs
from the holder's. Citations, names and evidence addresses buy nothing. The two
readings were launched as participants, never recruited under
`sov_lease.py helper`, so settlement could not see them. A lap produced exactly
the evidence the clause asks for and still could not rise above `BUILT`. That is
finding F18, and I confirmed the mechanism in the source rather than taking the
report's word.

### What would defeat it

- The check passing at `1f213c7` (the recorded defeating condition). **Tested. It
  does not.** See section 3.
- The check being vacuous about text (the other half). **Tested. It is not** - it
  fails on exactly the three captions, by name.
- The anchor document acquiring an authored `labelMode`, which would make the
  demonstration pass on the broken build too. This was the defect the independent
  reading found; the repair `e51b999` guards it. **Tested. The guard fires.**
- Standing above `BUILT` claimed for it later. It has no witness lease. Any record
  showing this work as `WITNESSED` is wrong unless a witness lease appears.

### What I could not reconstruct

- **No receipt.** `receipt:lap/golden-rendered-text` is named in the close and
  exists nowhere. The lap's own finding F19 says no operation in this repository
  has ever emitted a receipt satisfying `contracts/receipt.schema.json`; I did not
  find one either.
- **The retained lease record drops the evidence.** The closed lease projects
  holder, state and `readings: []`. The receipt id, the four evidence addresses
  and the standing survive only in the raw close event in
  `.git/sov-sessions/leases.ndjson`, a file inside the git directory that is not
  and cannot be committed. Everything I reconstructed above came from the
  committed report plus that uncommitted log. Had the container been reset, the
  authoritative settlement record would be gone and only the narrative report
  would remain.
- **No custody or phase movement.** `P15-X5` still reads `ROOT_POINT`,
  `NOT_EARNED`. The lease carries no custody identifier and the custody board
  cannot see the lease (finding F3). I could not reconstruct any link between the
  closed work and the clause it was run for, other than prose.
- **Whether the work is wanted.** It is on a branch, not merged to `dev`, with no
  pull request. Nothing in either repository records a decision to keep it.
- **Who the principal is.** The lease holder is
  `urn:soveraeign:principal:instance:session-6352b5`; `sov_session.py brief`
  reports `principal: unidentified`. The identity was asserted at the lease and
  never established at the registry (finding F4).

---

## 3. Reaching the capability, and using it

The capability is not in this repository. The lap report and the lease both name
it: `concern:schematically/golden-rendered-text`, in `schematically`, which is on
this machine at `the schematically repository` - checked out on a branch with the same
name as this node's branch, `claude/movement-72-hours-2claax`, HEAD `d406790`,
clean tree.

**Run 1 - the check at HEAD. Failed, on the environment.**

```
$ python3 tests/golden_rendered_text_qa.py
playwright._impl._errors.Error: BrowserType.launch: Executable doesn't exist at
/opt/pw-browsers/chromium_headless_shell-1200/chrome-headless-shell-linux64/chrome-headless-shell
```

`playwright==1.57.0` is installed and wants browser revision 1200; `/opt/pw-browsers`
holds revision 1194. `tests/browser_runtime.py` accepts `CHROMIUM_PATH` for exactly
this, and `/opt/pw-browsers/chromium` is a symlink to the 1194 binary.

**Run 2 - the check at HEAD, with the browser named. Passed.**

```
$ CHROMIUM_PATH=/opt/pw-browsers/chromium-1194/chrome-linux/chrome \
  python3 tests/golden_rendered_text_qa.py
PASS golden rendered text QA (10 documents, 101 text nodes)
```

**Run 3 - the registered suite, the way the readings ran it. Passed.**

```
$ CHROMIUM_PATH=/opt/pw-browsers/chromium python3 scripts/qa.py --quick
PASS golden rendered text QA (10 documents, 101 text nodes)
QA PASS tests/golden_rendered_text_qa.py (3.93s)
...
RC QA PASS: 37 suites + 17 JS syntax checks (89.96s test time)
```

The check is registered in `scripts/qa.py` `BROWSER`, not a private runner.

**Run 4 - the recorded defeating condition, reproduced.** The closure condition
says the check must fail at `1f213c7`. Done without touching either repository:
`git archive 1f213c7` into a scratch directory, the new check plus its expectation
plus the anchor document copied in, `python3 build.py`, then:

```
FAIL 09-typed-captions.sov: expected rendered text ['component:src', 'component-label', 'ACT'] and it was not drawn
FAIL 09-typed-captions.sov: expected rendered text ['component:check', 'component-label', 'GATE'] and it was not drawn
FAIL 09-typed-captions.sov: expected rendered text ['component:store', 'component-label', 'HOLD'] and it was not drawn
FAIL 09-typed-captions.sov: rendered text differs from the expectation
EXIT=1
```

Both halves of the closure condition are reproduced by a participant that did not
build the change, did not read the builder's report first, and used no oral
history. The defeating condition does not hold.

**Run 5 - the repair `e51b999`, exercised.** In a scratch copy of HEAD I wrote
`"labelMode": "boundary"` into the four components of `examples/09-typed-captions.sov`,
the exact disarming the independent reading found:

```
FAIL 09-typed-captions.sov: component:src authors labelMode 'boundary'; the anchor is
disarmed because a component with an authored mode draws its caption on a broken build
too. Re-author the document without it rather than blessing this.
(and the same for component:check, component:store, component:log)
EXIT=1
```

The guard fires.

**Run 6 - the disclosed residual, confirmed.** The lap attributed one defect to the
definition rather than the work: a caption rendered at `opacity: 0` leaves the text
in the DOM and passes. In a scratch copy of HEAD I appended
`.component-label { opacity: 0; }` to `styles/app.css`, rebuilt, and ran:

```
PASS golden rendered text QA (10 documents, 101 text nodes)
```

Every caption is invisible and the suite is green. The residual is real, is
disclosed in the commit message of `e51b999`, and is correctly attributed: the
closure condition said *rendered text*, and rendered text is what was built. The
commit subject of `3f652a7` - "compared by what it draws, not only what it says" -
still overstates it.

The four scratch runs wrote only under the session scratchpad. Run 3, the full
`scripts/qa.py --quick` suite, is a different matter: it left five tracked files
modified in `schematically` - `tests/beta17-read-write.png`,
`tests/beta18-inline-wire.png`, `tests/file-menu.png`, `tests/saved-test.sov`,
`tests/saved-test.sovpak`. That is finding F16 of the lap report reproduced by a
second participant: the suite writes its run artifacts into the directory holding
its own source, so running it dirties the tree and restoring the tree destroys any
change under test. I had authored nothing in `tests/`, so `git checkout --` on
exactly those five paths was safe here; for the builder it was not, and the lap
report records it silently reverting its own repair that way. Both repositories are
now clean apart from this file.

---

## 4. Where the artifact did not carry me

| What I needed | Was it in the artifact? | What I did |
| --- | --- | --- |
| Where owner acceptances are recorded | `STATUS.yaml:88` names `.local/acceptance/ledger.ndjson`. **It does not exist.** `.local/` is gitignored. | Fell back to the `owner_accepted` block inside `STATUS.yaml` itself, which is committed and dated. |
| Whether the landing ledger rows were real | No. `.local/landing/ledger.ndjson` holds twelve rows that look like landings. | Read the fields: `grant:test`, branch `work`, all one timestamp. Discarded them as test fixtures. A less suspicious reader reports a false landing here. |
| Where a closed lease is recorded | `sov_lease.py status` shows live leases only and returned empty. | Read `scripts/sovlease/store.py`, whose docstring names `.git/sov-sessions/`. The answer lives in the git directory: never committed, gone with the container. |
| That the payload lived in another repository | Yes, and clearly - the lap report names `concern:schematically/golden-rendered-text` and pull request #32 there. | Nothing needed. This was the one hand-off the artifact made well. |
| Which browser to run the QA with | **No.** `CHROMIUM_PATH` appears in no document in `schematically` except `FINDING-WORK.md` and `FINDING-PARTICIPANT.md` - the evidence of this very work. `AGENTS.md` there says only "run the QA scripts"; `LOCAL-SETUP.md` does not name it. | Hit the failure first, then read `tests/browser_runtime.py` and found `/opt/pw-browsers/chromium`. This is finding F8 of the lap, met by the next fresh participant exactly as predicted, one lap later, unfixed. |
| Whether the work is merged or wanted | Partially. The commit messages say nothing was pushed and no PR opened; I confirmed with `git branch -a --contains`. | Reported as unmerged. No record says whether it should be. |
| What the receipt contains | **No.** The receipt id is recorded and the receipt does not exist. | Reported as missing. |

I asked nobody anything and used no information from outside these two
repositories and the running container.

---

## 5. How long the trail was, and where it nearly went cold

Seventeen commands to the answer, of which four were dead ends and one was a
near-miss that would have produced a false report.

It nearly went cold twice.

**First, at the settlement stores.** The three obvious places to look for "what
settled most recently" all fail differently: the acceptance ledger is absent, the
landing ledger contains only test fixtures dated today, and the node journal stops
a day short. If I had trusted any of the three I would have answered 2026-08-28,
2026-09-08 (wrongly, from fixtures), or 2026-09-07. The thing that saved it was a
narrative document - `reports/2026-09-08-commissioning-circuit-reconnaissance.md` -
which is prose, not a record, and is the only committed artifact that names the
lease at all.

**Second, at the lease itself.** The node's own reader for leases returns an empty
list for the very lease that is the answer, because it projects live leases only.
The authoritative record is in `.git/sov-sessions/leases.ndjson`: outside the
commit graph, outside any clone, invisible to `git`, and reachable only after
reading the storage module's docstring. A participant arriving from a fresh clone
of this repository - rather than in this container - could read the report and
would find no settlement record whatsoever. The evidence addresses in it point to
a second repository that a fresh clone would also not have.

The trail held because two things were true at once: the payload work is
scrupulously self-documenting, in commit messages that state their own
overstatements and disclose their own residuals; and the container still had both
repositories and the container-local lease log. The first is a property of the
work. The second is an accident of where I was standing.

The lap's own conclusion is the honest summary of the layer beneath it, and my
run corroborates it from the far side: settlement refused correctly, the evidence
was real, and nothing in the record connects the two.
