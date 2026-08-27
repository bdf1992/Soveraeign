# 0083 — An automation nobody can see is an automation nobody has

Status: `PROPOSED · BDO HAS NOT RULED`
Date: 2026-08-27
Seat: `seat:session-control`
Supersedes: nothing. Extends `decisions/0015-scheduled-runs.md`, which declared the
schedules and left nothing watching them.

## What was true before this

Every schedule declaration under `.claude/schedules/` reading `enabled: false`.
A working runner in `scripts/sov_schedule.py`. `.local/schedules/` did not exist, so
no scheduled run had ever executed on this machine and the ledger had nothing to
read. Three rendered pages under `docs/`, none about automation.

Neither Bdo nor any session would have noticed a scheduled run starting to fail,
because nothing had ever run and nothing watched. That is the request in
`.claude/drafts/automation-health-and-controls-ticket.md`, and this decision records
step one of it: the read. The switching surface is deliberately not built.

## Ruling

**1. A health reading is derived from records, and a rule that has no case does not
exist.** `contracts/automation-health.json` declares nine rules, four readings, and
five run statuses. `conformance/fixtures/automation-health/cases.json` carries, for
every rule, at least one case that proves it fires and one that proves it stays quiet
with its own inputs in front of it; for every declared threshold, a case sitting
exactly on it and a case one step inside; and for each selector a witness enumerated,
a case that holds it. No count is stated here, because the commits that add cases are
the commits that would have to remember to restate it.
`scripts/sovschedule/rules.py` holds the arithmetic and nothing else; the severity,
the thresholds, and whether a rule applies to a switched-off schedule all come from
the table, and a rule declared there with no derivation raises rather than passing as
a rule that never fires.

*What would defeat it:* a real unhealthy state the nine rules cannot express, or a
case that passes for a reason other than the one it claims to prove.

**2. An empty record set does not read green.** A schedule with no settled run reads
`UNOBSERVED`, not `HEALTHY`. So does one whose entire history is refusals, and one
whose only run is still in flight: a refusal invoked nothing and a run in flight has
not answered, so neither is evidence that the schedule works. Every schedule reads
`UNOBSERVED` today, which is the true statement about them. This is trap T2 one
level down — green means unchanged, not correct.

*What would defeat it:* a reading of `HEALTHY` over a schedule that has never
executed.

**3. The alert is a refusing check, and it cannot reach as far as it looks.**
`UNHEALTHY` exits nonzero from `python scripts/sov_schedule.py health-check`, which
`scripts/verify.py` runs, so an unhealthy automation fails the build. That is the
only alert leg taken: Phase I forbids external-world effects and nothing here opens
an outbound channel. The Console surface 1 notification record is the second
admissible leg and is not built, because the Console notification path has no
implementation.

The reach is stated rather than implied. `.local/` is gitignored, so no CI runner
holds a ledger; there, only `TARGET_MISSING` and `DECLARATION_REFUSED` can refuse.
CI watches declaration health and never run health. Reading a green CI as evidence
that the automations are running is the mistake this table exists to refuse.

**4. `CONSECUTIVE_FAILURES` does not apply to a switched-off schedule.** Two failures
in a row refuse the build, and they clear by a run that passes. The obvious operator
response to a schedule that failed twice is to switch it off; a switched-off schedule
can never produce that passing run; so applying the rule to it would refuse for ever
with the only mechanical exit being the one the table forbids — deleting gitignored
state nobody else can see. `LAST_RUN_FAILED` still reports it and does not refuse.

*What would defeat it:* a failing schedule switched off and then quietly switched
back on with the failure unaddressed and nothing having reported it.

**5. The reading layer is separable from where the records live, and the seam is one
module.** `scripts/sovschedule/history.py` is the only thing that knows the records
are `.claude/schedules/*.json` and `.local/schedules/ledger.ndjson`. Moving this onto
Console surface 3 replaces that module and leaves the rules, the table, and the fixture
corpus untouched. The Automation Service that would own those records is packet A7 -
presented, not accepted, and not committed when this was written; naming it here is a
forward reference and is marked as one in the contract. Bdo ruled the placement in the
request and this decision does not reopen it.

**6. The page is graded in two halves, and the half that cannot be graded says so.**
`docs/automation.html` is rendered the way the other three pages are, and
`health-check` compares it byte for byte. Its declaration half derives from committed
bytes and the instant the page records, and is compared everywhere. Its history half
derives from machine-local state, so it is compared only where the ledger digest
still matches what the page recorded; elsewhere the check reports that half
`UNCHECKED` and names the absent source. A page graded as current over records the
grading machine never had is the defeating case
(`services/console/CHARTER.md`: an omitted source must be declared).

The page also records the UTC offset it was rendered in, and the check re-renders in
that clock. `scripts/sovschedule/runner.py` matches cron in the host's local time, so
a read taken in UTC answers "when is it next due" hours — sometimes a day — wrong on
any host that is not on UTC, and Bdo's is not.

## Defaults taken

Reversible, recorded so a later reader can overturn them with evidence rather than
taste.

- Thresholds: two consecutive failures refuse, a run is drift at twice its
  predecessor and at least sixty seconds longer, three identical refusals are a loop,
  two missed cadences are overdue. Set from the shape of the seven declarations, not
  from measurement, because nothing has run. The corpus is what would move them.
- Occurrences are counted in the clock the read was taken in, capped at eight days,
  and a walk that hits the cap fires on its own. Without that a weekly schedule
  dead for six weeks reads healthy on six days in seven.
- A run that returned zero and wrote no completion report is `DEGRADED`
  (`EMPTY_RUN`), read off the newest run that passed. Every declaration's prompt asks
  for one; a run that spends budget and produces nothing is the refusal loop's quieter
  twin.
- Declarations are read one file at a time. `load_all` raises on the first file it
  refuses, which would mean one dead target blinding the reader to every other
  schedule — on a surface whose whole job is to say which ones are broken.

## What this does not do

No schedule was enabled; every one remains `enabled: false`. Nothing was registered
with the Windows scheduler or any OS task. `fire-trigger` is untouched and still
refuses `AUTHORITY_UNCONFIGURED`. `.claude/schedules/` was not moved into the
Automation Service. The switching surface — step two of the request — is not built,
and the request says it waits on Bdo saying the read is right.

## Residuals

Recorded in `contracts/automation-health.json` under `residuals`, and repeated here
because a reader of the decision should not have to open the table to find them:
nothing records when a schedule was switched on, so `ENABLED_NEVER_RUN` fires the
moment it is enabled rather than after a grace period; a forced manual run silences
that rule for ever even if the host tick was never registered, which `OVERDUE` covers
only from the next cadence onward; the executor's exit code is displayed and no rule
keys on it; a `REPORTED` event whose run has no attempt is skipped in silence, so a
truncated ledger reads as fewer runs rather than as an incoherent record; and the page
and the command can disagree, because one is a projection of `HEAD` and the other reads
what is on disk.

There is no claim here that the corpus defeats every possible mutation. It defeats
every rule and every threshold, and that is checked rather than asserted; it defeats
the three selectors a witness enumerated, because that witness enumerated them. Nobody
has shown the coverage is complete and this record does not say it is.

## What still waits on Bdo

Two things, both raised by the independent witness of commit `564baad` rather than by
the builder.

1. **Does this read read right?** That is the gate the request itself named, and the
   switching surface does not start until it is answered. Accepting it is accepting the
   nine rules and the four readings, not enabling anything.
2. **Whether a rendered artifact should be graded against `HEAD` as a rule, rather than
   case by case.** This change shipped a page derived from a working tree eleven
   sessions share, and its own check refused its own commit in a clean checkout. The
   repair applies the referent Bdo already ruled for the orientation page on acceptance
   packet A5. The same defect reached three places in one change - the page, the
   orientation counts, and prose asserting a schedule count true only of the shared
   tree - which suggests the rule belongs above this decision rather than inside it.

Neither blocks work. The rules and the page stand as a reversible default under the
first, and the second is a question about a rule this repository already applies in one
place and not the others.

## Standing

`PROPOSED`. The tests establish `BUILT` for the rules and witness nothing.

Four readings, in order. A helper subagent read the contract, the corpus and the
modules while they were being written and found twelve defects. A first witness ran
against the frozen commit and dissented: the page had been rendered in the shared
working tree, so the change's own check refused its own commit, and three of six
thresholds were unpinned. A second witness ran against that repair and dissented
again: three more inputs of the same page were still read from the working tree, and
three selectors were undefended. All three of those readers were started by the
building session, so none of them could witness it.

The fourth was independent. `session-796628` holds a disjoint concern, has never
edited any file in this change, and worked in its own detached worktree at `11c3f1a`.
It returned `SUPPORTS`. It attacked the load-bearing claim - that the page is a
function of the commit - with six working-tree mutations and could not move the page,
and it pinned the clock, which was the fifth input it expected to find and did not.

It raised two coverage findings, neither defeating a claim made here, and both are
repaired in the commit that carries this paragraph. `applies_to_disabled` survived
mutation on `REFUSAL_LOOP`, which declared `true` with no switched-off case to prove
that value; the mechanism had been proven on a rule declaring `false`, which is not
the same thing. `needs` survived on all nine rules, because it selects which of the
page's two findings sections prints a rule and the corpus judges readings, not pages.
The second is the sharper one: the page has exactly two call sites, so a `needs` value
naming neither prints the finding nowhere while the headline reading still counts it -
a page reading "Nothing fired." twice above a verdict of `UNHEALTHY`. `page.render`
now refuses such a table rather than rendering it.

Those repairs are themselves unobserved. The observation covers `11c3f1a`.

The reading to take from four rounds is not that the coverage is now complete. Each
round found something the round before it missed, and the fourth was the first that
could settle anything at all.
