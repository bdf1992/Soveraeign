# Epic Projection

A local, checked-in view of the epic-of-epics issue tree (`#1 — Soveraeign
system of villages`) so the harness can walk it without reading an external
surface on every run. Like the rest of `.claude/`, this is plumbing: the
projection holds no standing, and reconciling it settles nothing.

## Why a projection and not a live read

GitHub is the coordination surface and the issue body remains the compressed
specification (`CONTRIBUTING.md`, Issue coordination contract). Reading it is
an external crossing. An unattended scheduled run has no business making one:
`no_external_effects_in_phase_i` stands, and the scheduled-run tool whitelist
in `scripts/sovschedule/runner.py` deliberately does not carry `gh`.

So the crossing happens once, attended, and lands in the repository:

```text
gh (attended)  ->  sov_epic.py sync  ->  .claude/epic/tree.json  ->  every unattended read
```

The consequence is honest staleness. `tree.json` carries `synced_at`; a walk
reports the age rather than pretending currency. Refreshing is a human or
interactive-session action, never a scheduled one.

## The files

| File | What it is |
| --- | --- |
| `tree.json` | Every issue: number, title, state, labels, and the parsed `soveraeign-ticket/v1` metadata block, or the parse error that stopped it. Regenerated wholesale by `sync`. |
| `villages.json` | The village-to-domain routing table. Joins the issue tree's four villages to the harness domains in `.claude/README.md` and owns neither side. An issue routes only where a repository artifact evidences the ownership; `unrouted_reason` says what an absent route does and does not mean. |
| `NARRATIVE.md` | The same issues told by front office (where an actor meets the system) and back office (what holds that meeting up). A second reading for talking about participants and supports; it routes nothing and holds no standing. |
| `offices.json` | The issue-to-office grouping behind `NARRATIVE.md`, in machine shape. Every issue sits in exactly one office or in `outside_both`. |

## Three readings, none of which settles anything

`sov_epic.py validate` reports three independent kinds of drift:

- **contract** — each open issue's block against `contracts/issue-metadata.schema.json`;
- **label projection** — the visible GitHub labels against the block they project,
  per `.github/labels.yml` and `CONTRIBUTING.md`;
- **containment** — the epic to village to bit/stub tree. `village_issue` is the
  containment edge for a bit or stub, not `parent`: the schema lets a bit name
  the epic as its parent while its village issue is the node that must contain
  it.

## Three states, kept apart

Merging any two of these sends ordinary work upward, so the walk names them
separately and never lets one imply another.

| State | Means | Who moves it |
| --- | --- | --- |
| `HELD` | an unsatisfied `requires` edge | whichever tier can build the prerequisite |
| `UNROUTED` | no repository artifact evidences a domain owner | whichever tier can write the charter, contract, or tests |
| `OWNER_HELD` | an open `unblock` ticket asking the owner for a judgement | Bdo, and only here |

Routing and readiness are **independent readings of the same issue**. An issue
with no domain owner can also be waiting on a prerequisite, so every entry
carries both `routing` (`ROUTED`/`UNROUTED`) and `readiness`
(`REACHABLE`/`HELD`). Eighteen of the twenty issues that are unrouted today are
`HELD` as well, which the old three-way split could not show.

`OWNER_HELD` membership is decided by `contracts/issue-metadata.schema.json`
rather than by the walk's opinion: an open `unblock` ticket whose
`requested_provision` is a judgement, which the schema requires to be addressed
to the owner and to no one else. There are none today, and
`python scripts/sov_epic.py owner-held` says so.

Selection then puts each open bit and stub in exactly one dispatch bucket, in the
order that decides who moves it next: **owner-held**, then **unrouted**, then
**held**, then **ready** (routed with every `requires` edge satisfied).
Reachability is evidence about the tree, never a grant — an issue being ready
says nothing about whether an open decision in `STATUS.yaml` admits the work.
Adding the artifact that would route an unrouted issue is ordinary reversible
work at this tier (`AGENTS.md`, Closure ownership), not a question for Bdo.

## Operating it

```bash
python scripts/sov_epic.py sync        # attended: refresh from GitHub via gh
python scripts/sov_epic.py status      # counts, ready work, held work
python scripts/sov_epic.py validate    # the three readings; --strict to exit non-zero
python scripts/sov_epic.py next --village ground-and-evidence
python scripts/sov_epic.py unrouted    # open work no artifact gives a domain owner
python scripts/sov_epic.py owner-held  # open work that genuinely waits on Bdo
python scripts/sov_epic.py report      # the whole survey as JSON
```

`validate` exits zero by default and is deliberately absent from
`scripts/verify.py`: the tree carries real pre-existing drift, and whether that
drift should turn the repository red is Bdo's call, not the harness's.

## The walk

`workflows/sov-epic.js` runs Reconcile (one `sov-witness` over the three
readings) then Select (one `sov-orchestrator` per village). With
`{ advance: true }` it adds Advance and Witness — one `sov-worker` on the
selected operation, then a different agent verifying it. It never calls
`workflow()`; `sov-federation` remains the only workflow allowed to nest.

Declarations: `schedules/epic-walk.json` (observe, daily) and
`schedules/epic-advance.json` (build, weekly). Both ship disabled.
