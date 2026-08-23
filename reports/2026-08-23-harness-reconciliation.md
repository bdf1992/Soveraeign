# Harness reconciliation, 2026-08-23

Status: `PROPOSAL · NOT BUILT · NOT WITNESSED · NOTHING RATIFIED`

Governance-domain analysis of the collision between `decisions/0013-federation-harness.md`
(local, untracked) and `decisions/0013-domain-mapped-sdlc-loop.md` (merged on `main` via
pull request #33/#34). Written by the session that opened pull request #44; nothing here
is a witness observation and nothing here is Bdo's judgement.

Read it before the local tree fast-forwards onto `origin/main`, because the fast-forward
brings the second record and a second `.claude/README.md` into a tree that already holds
the first.

## The finding

**These are not competing decisions.** One is the loop; the other is the loop's binding.
The collision is a numbering and layering accident from two parallel sessions, not a
disagreement about how the repository should work.

`SDLC.md`, Bindings, says it plainly:

> The `.claude/` directory is the first such binding, admitted as a provisional target
> by owner direction.

Upstream decision 0013 admits that slot. The local federation-harness record is what
fills it: role agents, per-domain skills, per-domain workflows, and a scheduled runner.
It should be renumbered and reframed as *the `.claude/` binding of the loop decision
0013 defines*, not carried as a peer decision that happens to describe the same
directory.

That reframing costs nothing substantive. The harness already obeys the loop's law: it
caps proposals at `BUILT -> WITNESSED`, keeps builder and witness distinct, queues
judgement-typed questions instead of answering them, and claims no standing. What is
missing is the sentence that says which document it is subordinate to.

## Five items that need a real answer

The layering fix resolves the number. These five are substantive and are not resolved by
renumbering.

### 1 · `.claude/README.md` is two documents at one path

The tracked upstream version describes an `sdlc-*` skill family and calls the directory
"the first harness binding of the operating loop defined in `SDLC.md`". The untracked
local version describes `sov-*` roles, skills, and workflows as a three-tier federation.
Both are accurate about their own half. Neither mentions the other.

*Proposed resolution.* One README that opens with the binding declaration from the
upstream text — it is the one that names the governing document — and then describes the
concrete realization from the local text. The binding rules paragraph (`bindings/README.md`
applies; skills point rather than restate; the owning document prevails on divergence) is
the strongest paragraph either version has and must survive.

### 2 · `sov-witness` reads as a fourth tier, and tier depth is fixed at three

`SDLC.md` fixes the chain at Control, Orchestration, Work, and says so explicitly:

> Tier depth is fixed at three. A deeper chain adds crossings and receipts without
> adding a new kind of accountability.

The harness ships four agents. Three map cleanly — `sov-controller` to Control,
`sov-orchestrator` to Orchestration, `sov-worker` to Work. `sov-witness` maps to nothing,
because in the loop `RED` and independent observation are *stances* an operator holds
under grant, not a tier.

*Proposed resolution.* Declare `sov-witness` a Work-tier operator holding the
independent-observation duty under a scoped read-only grant — the mechanical guarantee
that the stance separation `AGENTS.md` requires cannot be quietly skipped by reusing the
builder. It is a fourth *role*, not a fourth *tier*. Left unstated, a reader who knows
`SDLC.md` will read the harness as violating it.

### 3 · Two skill families with no declared relationship

After the fast-forward `.claude/skills/` holds seventeen skills in two families that have
never been introduced to each other:

| Family | Count | Axis |
| --- | --- | --- |
| `sdlc-control`, `sdlc-orchestration`, `sdlc-worker` | 3 | tier |
| `sdlc-product`, `sdlc-development`, `sdlc-qa`, `sdlc-release`, `sdlc-feedback` | 5 | function |
| `sov-<domain>` | 9 | repository domain |

`SDLC.md` says a working operator "holds exactly one tier skill and the domain skills its
concern requires." That is satisfiable across both families, but only if someone says so.

*Proposed resolution.* Declare three axes rather than two: tier (`sdlc-`), function
(`sdlc-`), and repository domain (`sov-`). A worker on an asset gap holds `sdlc-worker`,
`sdlc-development`, and `sov-asset`. Without this, the next person to add a skill has to
guess which family it belongs to, and the guess will be wrong half the time.

### 4 · `sov-qa` and `sdlc-qa` are the same word for different kinds of thing

`sov-qa` is a workflow: a cross-domain sweep that dispatches witnesses and aggregates
residuals. `sdlc-qa` is a skill: the Blue and Red lane competence, one stance per
engagement.

*Proposed resolution.* Keep both, and state that the `sov-qa` workflow *runs* the lanes
`sdlc-qa` defines. It dispatches the stance; it does not define a second one. This is a
one-sentence fix that prevents a genuine future fork.

### 5 · The harness has no Red lane, so it cannot reach `PURPLE`

This is the one with teeth. `SDLC.md` requires a settled Red engagement receipt before a
concern advances past `BUILT`. Pull request #44 makes that mechanically checkable:
`BUILT_SELF_TESTED_NOT_WITNESSED -> WITNESSED` now refuses without a settled engagement,
with a confirmed finding lacking a permanent defeating fixture, or with a finding the Red
operator reproduced itself.

The harness produces the *other* half. `sov-witness` is independent observation, which is
what a witness receipt needs. Nothing in `.claude/` runs an adversarial engagement or
emits an engagement receipt, and `sov-qa` sweeps rather than attacks.

So today the harness can carry work to `BUILT` and produce a witness observation, and
still not clear the gate. That is not a defect in either design; it is an unbuilt lane.

*Proposed resolution.* Name the gap explicitly and pick one owner for it: either `sov-qa`
grows a Red lane that emits the engagement receipt, or the gate is satisfied outside the
harness and the harness says so. Silence here will read as the gate being optional.

## Numbering

`0013` on `main` is merged and effectively immutable. The local record moves:

| Record | Number |
| --- | --- |
| Domain-mapped SDLC loop (merged) | `0013` — unchanged |
| Console Service boundary (local draft) | `0014` — unchanged |
| Scheduled runs (local draft) | `0015` — unchanged |
| GitHub coordination registrar (pull request #44) | `0016` |
| Local federation harness (local draft) | `0013` → **`0017`** |

Three live references need the new number:

- `.claude/README.md` line 22
- `AGENTS.md`, Local orchestration harness
- `decisions/0015-scheduled-runs.md`

`reports/2026-08-22-christening.md` also names the old path. **Leave it.** A report is a
record of what was true when it was written; rewriting it would erase history to tidy a
filename, which is the counter-record rule read backwards.

## The fast-forward is not blocked by a conflict

Correcting an earlier read: local `main` is `0 ahead, 8 behind` `origin/main`, so this is
a fast-forward, not a merge. `git merge-tree` reports no conflict between the commits.
Two working-tree facts block it:

1. Uncommitted edits to four files the fast-forward also updates — `AGENTS.md`,
   `CLASSIFICATION.md`, `CONTRIBUTING.md`, `STATUS.yaml`. Local edits are small
   (12, 11, 9, and 8 added lines); upstream's are larger (6, 40, 45, and 7).
2. An untracked `.claude/README.md` that the fast-forward would create.

Both clear by committing the in-flight local work first — the line-ending operation, the
console boundary, the scheduled runs, and the harness — after which the fast-forward is
mechanical and the four files' additions are re-applied on top of upstream's.

The local edits and the upstream edits touch different sections of all four files. No
textual conflict is expected. That expectation has not been tested and should be, rather
than trusted.

## Judgement queue for Bdo

1. **Is the local harness record the binding of decision 0013, or a peer decision?** The
   analysis above assumes the former. If it is a peer, `SDLC.md`'s Bindings section names
   a slot that nothing fills, and that should be said out loud.
2. **Does `sov-witness` stand as a Work-tier role holding the observation duty**, or does
   the loop's fixed three-tier depth need amending to admit a witness tier?
3. **Three skill axes or two?** If two, one of the families has to fold into the other,
   and that is a much larger operation than this report scopes.
4. **Who owns the missing Red lane** — `sov-qa`, a new capability, or a human engagement
   outside the harness?
5. **Renumber `0013-federation-harness` to `0017`?** Mechanical once ruled, and it should
   be ruled before the fast-forward rather than after, so no commit ever holds two `0013`
   records.

Nothing in this report has been applied. The working tree was not modified.

## Concurrency note

Another session was writing to this working tree while this report was produced — it
added `.gitattributes`, repaired the `scripts/lint.py` CRLF check, and wrote
`reports/2026-08-23-line-endings.md`. That work is uncommitted. This report deliberately
touches no source file, both to avoid racing it and because every item above needs
owner judgement before it becomes an edit.
