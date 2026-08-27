# Witness record — Record Service (issues #7, #65)

```witness
standing_supported  none
```

**Verdict: NOT-YET.**

**Standing supported: none.** This observation does not carry `services/record`
from `BUILT` to `WITNESSED`. `record_service_status` stays
`BUILT_SELF_TESTED_NOT_WITNESSED` and was not edited.

- **Commit witnessed:** `4b96ba19df210f148bc41e4e4c2d8166bec72091`, read in an
  isolated git worktree so that other sessions writing this tree could not
  change the bytes mid-read (`CLAUDE.md` trap T6).
- **Observed:** 2026-08-26T17:06:10Z.
- **Receipt:** `witness/observations/issue-07-65-append-preserving.json`,
  conforming to `contracts/participant-observation.schema.json`.
- **Reproduce:** `python witness/probes/probe_record_journal.py`.

## What independence rests on

Git authorship establishes nothing here. Every commit in this repository carries
Bdo's identity, including the ones a model session wrote, so `git log` cannot
separate a builder from an observer. Independence rests on what is checkable
instead:

- this session did not build `services/record` and did not edit it;
- the probe never imports `soveraeign_record_service`. It reaches the service
  only as a subprocess through the CLI declared in
  `services/record/contracts/service.json`;
- the probe recomputes the digest chain from the rule written in
  `services/record/CHARTER.md`, not from `core.py`. A chain that verified only
  against its own implementation would show up here as a disagreement;
- the pre-existing walker `scripts/witness_record.py` was deliberately not read
  and not run before the probe was written, so the two are not a common-source
  pair. The 21 observations it reports were not relied on.

Re-running the participant's own `services/record/tests/` would not have been an
independent observation and was not treated as one.

## What was reproduced, and what happened

Eleven attacks, each against a fresh store, each written to defeat the claim
rather than confirm it. Ten held.

| # | Attack | Result |
| --- | --- | --- |
| 1 | Recompute every digest from the charter's stated rule alone | Held — 4/4 exact |
| 2 | Look for any entry `UPDATE`/`DELETE` on the declared surface | Held — 0 of 11 operations |
| 3 | Rewrite a committed payload directly in SQLite | Held — `DIGEST_MISMATCH`, exit 2 |
| 4 | Delete a journal row from the middle in SQLite | Held — `DIGEST_MISMATCH`, exit 2 |
| 5 | Counter an entry, then reread the original | Held — payload and digest intact, chain verifies |
| 6 | Drop every projection, rebuild, compare | Held — identical row, head unchanged, `authoritative=false` |
| 7 | Journal an entry sourced from a governing document | Held — `DESIGN_RECORD_REFUSED` on all four |
| 8 | Export a journal whose chain is already broken | Held — refused, no file written |
| 9 | Restore an export into a store that already holds entries | Held — refused, exit 2 |
| 10 | Truncate an export and rewrite its self-declared fields | Held — undetected without an external head, refused with `--expect-head`. The charter states this limitation exactly and does not overstate it |
| 11 | Rewrite the fields the digest rule does not cover | **Failed** |

## Findings

### F1 · MATERIAL · the chain covers less of an entry than the charter reads as claiming

`services/record/CHARTER.md`, "What append-preserving means here":

> Every entry carries the digest of the entry before it. A rewritten history
> stops verifying rather than quietly replacing the real one.

The declared digest rule, stated in the same file under "The digest chain",
covers `prev_digest`, `kind`, `subject`, `actor`, and the payload. The journal
table (`services/record/src/soveraeign_record_service/core.py`, table `journal`)
stores ten columns. Three of them — `entry_id`, `source_address`, and
`recorded_at` — are outside the rule.

Rewriting all three directly in SQLite leaves `reconstruct-journal` at exit 0.
Escalated to the sharpest form the gap allows: every entry's `recorded_at` was
inverted so the journal reports the reverse of the real chronological order, and
every `source_address` was rewritten to a fabricated
`lineage/evidence/...` path. The replay returned exit 0 with a **byte-identical
head digest**.

Consequence if ratified as-is: an operational System of Record whose stated
purpose is attributable history will certify a history whose event times and
input addresses have been silently changed. `AGENTS.md`, State and execution,
requires every consequential decision to emit an event carrying *actor,
operation, reason, timestamp, exact input addresses/digests*. Timestamp and
input address are two of the three fields the chain does not bind.

This is not a defect in the chain. The chain does exactly what the chain rule
says it does, and attacks 3 and 4 confirm it does so under direct assault. It is
a gap between the mechanism and the sentence that summarizes it.

### F2 · INFORMATIONAL · the projection is built only on demand

`read-projection` refuses with `MISSING_PRECONDITION` after an append and keeps
refusing until `rebuild-projections` runs. This matches the manifest's declared
precondition `projection_built` and the charter's account of the projection as
derived, so it is recorded rather than raised. A caller that expects the
projection to track appends will be surprised by a refusal, not by a wrong
answer, which is the right direction to fail in.

## Conditions that would discharge the verdict

One of these two, and the choice is the owning concern's to make, not a
witness's:

1. Extend the digest rule to cover `recorded_at`, `source_address`, and
   `entry_id`, restate the rule in `CHARTER.md` so an outside observer can still
   recompute it from the document, and add a defeating fixture for each of the
   three fields; or
2. Narrow the charter sentence to name the fields the chain actually binds,
   declare the remaining columns explicitly out of chain scope, and state the
   consequence — the same way the charter already handles truncation, which it
   documents accurately and which is why attack 10 held.

Either is a repair. `AGENTS.md` and `witness/README.md` both forbid a witness
from making one: an observation authored by a hand that touched the artifact is
void. The finding is handed back to the concern that owns `services/record`.

## Verified

Commands actually run, from the repository root, at the commit above.

```
$ python witness/probes/probe_record_journal.py
exit 0 — 11 checks, 10 held, 1 failed (history_can_be_quietly_rewritten)
    history_rewritten_undetected: true
    replay_exit_code: 0
    head_unchanged: true
    timestamps_changed: true

$ python scripts/verify.py
PASS: 39 checks in 12.058s wall, 32.476s of work
GRADE: SILVER at 12.058s; GOLD needs 6.000s or less
exit 0

$ python scripts/lint.py
PASS: repository hygiene (728 text files, 313 Python modules, 1 named debt)
exit 0
WARN: KNOWN DEBT: scripts/witness_infrastructure.py has 301 lines
```

`CLAUDE.md` trap T2 applies to the `verify.py` line: exit 0 means unchanged, not
conformant. It is reported because it was run, not as support for the verdict.

## Uncovered

Stated plainly, so a reader can calibrate this record rather than assume it is
complete.

- **Interrupted writes.** The charter claims a transaction that never commits
  leaves nothing behind. No mid-transaction kill was staged.
- **Concurrency.** Two processes appending at once was not tested.
- **Restore end to end.** A valid export replayed into an empty store was not
  exercised; only the refusal path was.
- **Counter-record linkage under a rewritten `entry_id`.** Whether rewriting an
  entry's id orphans a counter-record that points at it was not tested. It is
  the obvious next escalation of F1.
- **Media durability.** Explicitly outside the charter's claim and outside this
  observation.
- **#7 versus #65.** Both point at `services/record/` and no artifact separates
  them, so they were observed as one subject. If they are meant to be distinct,
  this record covers only the shared implementation.
- **`scripts/witness_record.py`.** Not read, not run, and therefore not graded.
  Whether its 21 observations are sound is an open question this record does not
  answer.
