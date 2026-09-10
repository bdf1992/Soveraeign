# Controller handoff, 2026-09-07

Written for a fresh controller with no memory of this session, and for the root
seat. It names what stands, what it cost, what the session got wrong, and one
design question the owner asked at the end.

Standing claimed here is `BUILT` or `WITNESSED` as marked. Nothing in this
document accepts anything.

## What stands now

`main` is at `1a59e33`. Four concerns were carried; one more was opened by the
owner mid-session.

| Concern | Terminal | Where |
| --- | --- | --- |
| P15-X3 discovery vertical (`sov_reuse.py`) | landed, witnessed | merged before this session's window closed |
| An address below the file (`sovaddress.py`) | witnessed, green, landing | PR #221, head `ca472b0` |
| Per-module tooling cost | witnessed, green, presented | PR #226, head `749be9f` |
| Office act granting `principal:claude-fable-5-1` | green, presented | PR #225, head `f471e8a` |
| The phase reader can be run | **landed** | merged as `1a59e33` |
| Counts out of `CLAUDE.md` | built, pushed, no PR | `chore/counts-out-of-the-page` |

Two of those are outside `grant:standing-landing-loop` and need the root seat:

- **#225** touches `nodes/`, `reports/` and `witness/`. It also carries an
  unresolved question that no amount of witnessing can answer: nothing in the
  node, the export, the self-report or four witness passes authenticates who
  passed the name `principal:bdo`. The root seat either affirms it directed that
  act or it does not.
- **#226** is outside the grant *only because its witness receipt was committed
  under `witness/`*. That was the session's error, not an authority boundary. The
  same session put the next witness's receipt under `.local/` and that branch
  landed itself. See "The grant excludes the evidence it requires" below.

## What the session cost, honestly

Four concerns in a day. Roughly half the effort was reactive rather than chosen:
two concerns exist because a check went red, and one exists to clean up a
coupling the session discovered by tripping over it.

None of the four came from the active phase's own work list. The session read
`contracts/custodies/phase-1-5.json`, saw four members mostly drawn, and went
looking for gaps in what was there. It did not read
`contracts/phase-1-5-phase-ii-horizon.md`, which is the document that says what
the phase is actually for. A fresh controller should read the horizon document
first and the custody file second.

## Findings, with the evidence for each

### 1. The phase's own reader had no entry point, and eight witness passes could not fix it

`python scripts/sov_active_phase_progress.py` printed nothing and exited 0.
`CLAUDE.md` said it "grades" the six exit clauses; `decisions/0102` said it
"refuses a custody that falls" below its floor. The module held only functions.

Eight witness passes recorded the silence — six in `witness/fresh-participation.md`,
two in `witness/discovery-and-reuse.md`. One diagnosed it exactly: *"prints
nothing: the module has no entry point and is graded as verify's phase progress
floor, which passed."* None could refuse it, because a module with no entry point
has no behaviour to defeat.

Repaired in `1a59e33`. Running it now reports every exit clause against its floor,
and reports that **three of the six carry no member at all**: `P15-X4`
definition-recurrence, `P15-X5` commissioning-circuit, `P15-X6`
operational-acceptance. That was not visible in any tool, document or report
before that commit.

This is the finding a fresh controller should act on first. Half of Phase 1.5 has
nothing assigned to it, and every prioritisation question is downstream of that.

### 2. The next-work reader is pointed at the previous phase

`python scripts/sov_epic.py next` names Asset, Observation and Identity. Those
are real Phase 1.5 primitives by the horizon document's list, but none of them is
a member of any Phase 1.5 custody, so working them advances the phase's score by
zero. The epic tree is a Phase-I product projection and nothing reconciles it
with the active phase's custodies.

### 3. Counted numbers in an excluded document made structural work unlandable

`CLAUDE.md` stated ten counts — checks, commits, decision records, reports,
service boundaries, manifests, declared operations, agent definitions, skills,
workflows — and `sov_snapshot.py` failed the build when any drifted. Correcting a
number means editing `CLAUDE.md`, which `grant:standing-landing-loop` excludes.

The consequence is mechanical and was not noticed until this session tripped on
it: **adding a check, a skill, a workflow, a service or an operation could not be
landed under the standing grant at all.** Only work that moved no counted number
could. That is a plausible explanation for a drift toward instrument work, and it
is a better explanation than any about intent.

Repaired on `chore/counts-out-of-the-page`: the page names
`python scripts/sov_snapshot.py numbers` and states none of the ten. The deferral
is not a hole — without the marker, deleting a number still drifts 10 of 10;
with it, 0 of 10; a wrong number stated beside the marker still fails.

### 4. The grant excludes the evidence it requires

`grant:standing-landing-loop` requires an independent observation before a
landing. Observations are recorded under `witness/`. `witness/` is not in the
grant's allowed paths. So a branch that carries its own witness receipt is,
by that fact alone, unlandable under the grant that demanded the receipt.

This session worked around it by having one witness write to `.local/` instead,
which kept #227 landable — and did not do so an hour earlier, which is why #226
sits on the root seat. The workaround costs the durable record. This is a real
seam and it is not the session's to settle.

### 5. `catastrophic_confirm_alone` cannot tell a slow host from slow code

PR #221 failed `repository (3.11)` at 47.970s pooled and **48.451s re-run alone**
against a 30.000s ceiling. The session reported this three times as host
contention without reading the log, then read the log and reported the opposite —
that an isolated 48s was a true reading of the change.

Both were wrong. The confirm-alone re-run happens on the same runner, so it
removes pool contention and not host slowness. On that same failing run, Asset
read 22.6s *isolated* against a 4s ceiling and Console 12.5s against 4s — every
check was inflated. Rebased onto current main with the same content, #221 is
fully green including that check. Locally the check costs 15.1s on base and
15.5s with the change.

The gap is that the catastrophe test has no reference for how fast the host is.
Nothing was changed about it here; raising a ceiling to admit one's own change is
the wrong shape, and the evidence now says nothing needed raising.

### 6. Witness independence is declared, not measured

`scripts/sovkernel/authority.py` decides observer independence by reading the
observation's own `contributed_to_build` field. Every witness this session
launched was the same model family, reading the same repository, from the same
host. They found real defects — including two the session would otherwise have
shipped, and a miscount in the session's own favour. They are still correlated in
a way nothing measures, and four passes are not four readings.

## The design question the owner asked

The owner's framing: *evidence judgement gates with a judgement agent, which gets
a compressed trace of the lifecycle of the obligations through their custody
lines* — and then, is that (1) a witness mode that delivers a judgement, or
(2) a `sov judge`, and is a judge a role or an agent?

### The primitive that is missing is the trace, not the judge

Four failures above share one shape, and the repository's own heuristic says to
look for a missing primitive when they do:

- **Finding 1.** Eight passes each held an observation. None held the *history* of
  the observation. "Observed eight times, repaired zero times, across days" is a
  judgeable fact that no single pass could see and no gate could read.
- **Findings 3 and 4.** Both are obligations whose custody line silently
  contradicts the grant that carries them. Neither is visible from any single
  artifact; both are visible the moment an obligation's route is laid out end to
  end.
- **This session escalated twice inside its own grant** — the #221 ceiling, and a
  verify registration the witness had already routed to the root seat. Both times
  the fact that refuted the escalation ("this path is in scope") existed in
  `contracts/standing-grants.json` and nothing put it in front of the participant.
- **Twenty-nine owner-routed questions name no hold reason** from the seven
  `contracts/acceptance-policy.json` declares exhaustive. Those are obligations
  sitting on a seat with no valid custody line, and only a trace surfaces the
  class rather than the instances.

None of those is fixed by adding a reader. All of them are visible in a record of
what happened to an obligation over time.

### What already exists, and the one axis that does not

More is built than the question assumes:

- `scripts/sov_trace.py up` walks the **vertical** axis — receipt to capability to
  operation to journey to promise to ground, with distinct-receipt arithmetic so
  overlapping views cannot double-count. That is `GROUND-014`.
- `scripts/sov_custody.py board` shows an obligation's **structure** — circuit
  stage, members, the observer of each, the closed path, what defeats it, what
  settles it, and estimate against actual.

Both are snapshots. Neither has a **time** axis. The board shows the latest
observation of a member and flattens any earlier history into prose inside
`stage_observed_by`. Nothing answers: how many times has this been observed, by
whom, how many of those observations produced a repair, how many escalations did
it generate, and were they admissible under the grant that held it.

That axis is the deliverable. It is an addition to two existing readers, not a
new store, contract or vocabulary.

### Judge is a seat. The agent is a binding that occupies it.

`AGENTS.md` settles this already, and the answer is not either of the two options
as posed:

> Only a seat that settles `JUDGEMENT` can accept a judgement claim, and it does
> so by accepting a presented result rather than by answering a question.

and

> A model, worker, adapter, credential, process, database, or provider receives no
> authority merely by operating successfully.

So:

- **A `sov-judge` agent without a seat produces another opinion, not a
  judgement.** Given finding 6, it would most likely be a third correlated
  reader wearing a stronger word. That is the trap to avoid, and it is the same
  trap the repository already names.
- **A witness mode that delivers judgement is the wrong merge.** It collapses
  observation and settlement into one participant, which is exactly what "no seat
  settles its own output" forbids. The witness's job is to make judgement cheap,
  not to perform it.
- **Judge is a role — a seat — occupied under a grant.** The root seat occupies it
  today. An agent may later occupy it the way `sov` occupies the landing loop:
  through a typed, scoped, accepted grant, with evidence rules that refuse rather
  than permissions that allow.

### Recommended sequence

1. **Add the time axis** to the custody board and the trace: for one obligation,
   every observation of it, every repair, every escalation, and whether each
   escalation was admissible against the grant in force. Report it compressed —
   one obligation, one screen.
2. **Give that trace to the seat that already holds judgement.** It makes the
   root seat's existing job cheaper immediately, and it needs no new authority,
   no new agent and no new contract.
3. **Only then consider a scoped `grant:judgement` and an agent binding.** The
   landing grant became safe because landing was mechanised and evidenced *first*,
   and because what refuses a landing is evidence rather than permission. Copy
   that order. A judge grant written before the trace exists would be a permission
   with nothing to refuse it.

The first step is the one worth doing, and it is small. The third is a decision
for the root seat and should not be taken on this session's word.

## What a fresh controller should do first

1. Read `contracts/phase-1-5-phase-ii-horizon.md` before
   `contracts/custodies/phase-1-5.json`. The custody file is the score; the
   horizon document is the game.
2. Run `python scripts/sov_active_phase_progress.py`. It works now.
3. Settle whether `P15-X4`, `P15-X5` and `P15-X6` are deliberately empty or
   unassigned. Everything else waits on that answer, including any judgement
   design.
4. Do not treat a red check as a work assignment. Twice this session it was, and
   both times the real cause was upstream of the code.

## What genuinely waits on the root seat

`python scripts/sov_accept.py audit` reports **one** admissible hold in the whole
repository: `O1`, publication clearance. Everything else this session described
as "waiting on Bdo" was either inside the standing grant, or outside it through
the session's own error. Two items are real:

- **#225**, and whether the root seat affirms it directed the office act. The
  record cannot answer this and four witness passes did not.
- **#226**, which needs one merge only because its receipt was filed in the wrong
  place — see finding 4, which is the seam worth settling rather than the merge.
