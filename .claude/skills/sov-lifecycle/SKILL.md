---
name: sov-lifecycle
description: >-
  Carry one Soveraeign concern from taken up to landed: bind the session to it, bound it against the
  standing grant, build under the implementation order, freeze the candidate, have it observed by a
  participant that did not build it, repair findings in place, and land or present. Load on
  "sov-lifecycle", "the loop", "carry this concern", "take this to landed", "who settles this", "what
  closes this", or when a session needs the whole path rather than one domain's competence. Filing an
  issue, opening a pull request, or queueing a ticket is not a terminal.
license: MIT
compatibility: >-
  A host that can read this repository, run python, and launch a second participant to observe the work -
  another session or another person, which is why the reach is external. Where no independent participant
  can be launched, the loop still runs and stops at that edge by name rather than observing its own work.
metadata:
  bdos: true
  version: 1.0.0
  hosts: [claude]
  portability:
    behavior: any
    execution: host
  instantiates:
    core: see-it-through
    digest: sha256:77115c73956ad4a9fbc549029c545bbd6ec01a7eccc08673f1a8c3365f97c921
  activation: [explicit]
  control: loop
  role: bind
  reach: external
  takes: [ask, chart, verdict]
  gives: result
  hands_off: [sov-witness]
  calls: [sov-orchestrator, sov-worker]
  reports_to: [sov-controller]
  refuses:
    - reporting a filed issue, an opened pull request, or a queued ticket as a terminal
    - observing its own work, or offering a helper that read or edited the change as the observation
    - converting a finding into another ticket instead of repairing it inside the concern
    - asking an owner seat for permission to begin reversible RECORD_LOCAL work
    - widening a grant, ratifying a judgement claim, or settling its own output
    - carrying more open concerns than it can land
    - weakening an oracle, fixture, or check so a participant passes
    - transferring witness or qualification to a candidate that was rebased, amended, or replaced
    - any EXTERNAL_WORLD effect outside a scope contracts/external-effect-authorization.json admits
  checks:
    - reads: output
      expect: the closing line names landed, presented for acceptance, or held at a named seam - and not filed, opened, or queued
      how: "read: find the completion report's last line and check it against those three"
    - reads: output
      expect: the observation names a participant absent from the changed paths and the declared helpers
      how: "read: take observer_id from the observation and look for it in the build report's authorship and helpers"
    - reads: output
      expect: every check reported as run names a real command and its real exit code
      how: "run: python scripts/verify.py; python scripts/lint.py - and compare the exit codes against what was reported"
  provenance:
    author: bdo
    origin: >-
      instance of bdos core see-it-through; the path through the eight skills SDLC.md Skill axes declares,
      which .claude/skills/sdlc-* realizes one shard each. Those eight remain: SDLC.md declares them and is
      outside the standing grant, charting/derive.py derives its chart from them, and
      .claude/workflows/sov-compression.js routes to sdlc-feedback
    adopted: 2026-09-07
  currency:
    verified: 2026-09-07
---

# sov-lifecycle

This is the binding of `see-it-through` to this repository. The move is the core's; the stations, the
owners, the commands and the refusals are this repository's. Every rule below is owned by a governing
document and cited at the sentence that applies it — `SDLC.md` owns the loop, its three tiers and its two
dyads, and prevails on any divergence. A skill that restates an owned rule as independent authority is defective by `SDLC.md`'s
own test, so nothing here is stated as if it were the source.

What grades this file, and what does not. `python -m bdos instance
.claude/skills/sov-lifecycle/SKILL.md`, run from a checkout of the bdos repository, grades it against the
core it pins: same role, control, reach and gives, an edge of every kind the core declares and none
pointing back here, and never fewer refusals. The digest covers what the core is, with its own
reading date elided, so re-reading the core does not stale this file and changing the move does. Nothing in *this* repository runs that command, so the
digest above cannot tell you here that the core has moved — that reading happens where bdos is, or not at
all. Recorded rather than implied, because a pin nothing checks is a decoration.

## The move

1. **Take up one concern, and say what done is.** `python scripts/sov_session.py register` then
   `brief`. One session, one concern, for its lifetime (`AGENTS.md`, One session, one concern). Name the
   condition that ends it, in one sentence, before starting: the terminal you are aiming at and the
   evidence that will show it reached. A concern routes and attributes; it is never authority. Discovered
   work that belongs elsewhere is routed with `sov_session.py route`, not silently absorbed.
2. **Bound it against the grant.** Read `contracts/standing-grants.json`. Work touching an excluded path
   ends at an acceptance packet under `acceptance/`, not a merge. Then apply the absorption test in
   `contracts/closure-ownership.json`: work inside the same service, effect class and authority is this
   concern discovered more fully; crossing any one of the three mints a separate concern.
3. **Plan the operation.** `AGENTS.md`, Implementation order: name the operation and its owned lifecycle,
   then the contract and its positive *and* defeating case, then the smallest change that satisfies the
   visible case. No business logic without a prior contract, fixture, or explicit experimental label.
4. **Build, and check as you go.** `python scripts/lint.py` and `python scripts/verify.py` from the
   repository root, against the state you intend to land (`AGENTS.md`, Implementation order 5, and
   Secrets and local boundaries for lint). Report real exit codes: `AGENTS.md`, Completion report, says
   work is not complete because files were written or tests returned zero. `verify.py` exiting 0 means
   unchanged, never qualified (`CLAUDE.md`, trap T2). Verify the state you will commit, not the state you
   have: several snapshot claims read committed bytes, so an uncommitted file is invisible to them and a
   green working tree can go red the moment it lands (`CLAUDE.md`, snapshot section).
5. **Freeze the candidate.** `contracts/repository-candidate-lifecycle.json` owns carrier state. Evidence
   meant to outlive construction binds an exact `FROZEN` subject: candidate commit, tree, and base. A
   repaired or rebased candidate is a new subject and earns its evidence again.
6. **Have it observed by a participant that did not build it.** Launch `sov-witness`. It receives the
   contract, the claimed invariants and the frozen artifact; the builder's plan and tests are part of
   that artifact, readable and attackable, and never its evidence or its oracle (`SDLC.md`, Release gate 6).
   A helper that read or edited the change is inside the build and cannot observe it. Launching that
   participant is this concern's own step. Where none can be launched, stop at that edge and name it.
7. **Take the reversible decisions yourself.** Which reachable design, what to name a local symbol,
   what the defeating case should be, when to split a module: these belong to whoever holds the concern,
   and asking another tier to settle one is a defect rather than caution
   (`decisions/0023-acceptance-not-approval.md`; `decisions/0033-close-the-founding-docket.md`, Ruling 1).
   Record them under `Defaults taken` and continue.
8. **Repair what comes back, here.** A finding is fixed inside the concern. Filing it moves the defect out
   of the only place that owns it (`AGENTS.md`, Closure ownership).
9. **Land, or present, or stop at a named seam.** `python scripts/sov_land.py` is the only path that
   commits and merges (`CLAUDE.md`, How we launch things), and the gate grades the request; a refusal is the correct outcome to report, not a
   problem to route around. Outside the grant, write the acceptance packet instead. Say which of the three
   happened in the closing line.

## Refuses

Reporting a filed issue, an opened pull request, or a queued ticket as a terminal. Observing its own work,
or offering a reader that touched the change as the observation. Converting a finding into another ticket.
Asking an owner seat for permission to begin reversible `RECORD_LOCAL` work, which
`contracts/acceptance-policy.json` refuses as `PREAPPROVAL_REQUESTED`. Widening a grant, ratifying a
judgement claim, or settling its own output. Carrying more open concerns than it can land. Weakening an
oracle, fixture or check so a participant passes. Transferring witness or qualification to a candidate
that was rebased, amended or replaced. Any `EXTERNAL_WORLD` effect outside an admitted scope.

## Hands off to

`sov-witness`, once there is a frozen subject and it needs a reading by a path the builder did not choose;
its findings come back here for repair, and that loop runs until clean or stops at a named seam. Calls
`sov-orchestrator` to turn a concern into one bounded operation and `sov-worker` to execute it. Reports to
`sov-controller`, which aggregates and holds the owner's judgement queue. The domain skills — `sov-asset`,
`sov-governance`, `sov-verification` and the rest under `.claude/skills/` — are loaded at step 3 by the
concern that needs them; this skill is the path, and they are the competence at a station.

## Check

Read the completion report's closing line: landed, presented for acceptance, or held at a named seam, and
not filed, opened, or queued. Take `observer_id` from the observation and look for it among the build's
authorship and declared helpers; finding it there voids the observation. Then run `python
scripts/verify.py` and `python scripts/lint.py` yourself and compare their exit codes against what the
report claimed.

## Example

"Concern: the budget grader reruns a pooled suspect but never records which read it graded. Inside the
grant (`scripts/`). Wrote the defeating case first — a suspect whose isolated read passes must not refuse —
and it failed as declared. Smallest change in `scripts/sovverify/budget.py`. lint exit 0, verify exit 0,
52 checks. Froze at `a63b89f`. Launched a witness that had not touched it: it reproduced both cases, and
found the report named a ceiling the contract does not carry. Fixed that here, re-observed clean.
`sov_land.py land` accepted it. Landed; the stale ceiling in `services/README.md` is a separate concern
and is routed, not carried."

## Experience

Record where the loop stopped short and what the stop was called at the time. "Filed for Bdo", "raised in
the packet", "waiting on the gate" are the three that read as progress here and often are not. Record
every observation that came back with a finding the build had reported as clean, because that gap is the
measure of whether step 6 is being reached for or waited on. Three concerns stopping at the same seam
means the seam is real and belongs in the move as a named stop, not in the log as a surprise.
