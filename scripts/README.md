# Command surface

Thirty-six `sov_*.py` entrypoints plus the two verification commands. This is the
whole of how the node is operated from a terminal, and it is the index
`contracts/publication-surface.json` requires: an entrypoint absent from this
page is unreachable by anyone who did not write it.

Every command reads local files. None reaches the network unless its own
documentation says so. Nothing here grants authority, and no command settles its
own output — `AGENTS.md` owns that rule and these tools are subject to it.

Run any of them with `--help` for exact arguments.

## Start here

| Command | Answers |
| --- | --- |
| `python scripts/verify.py` | Does the repository pass? The required local and CI gate, graded on wall time (`decisions/0050`). |
| `python scripts/lint.py` | Is the repository text clean — endings, module size, secret shapes, absolute host paths? |
| `python scripts/sov_next.py` | What happens next? Reconciles five signposts and reports disagreements rather than resolving them. |
| `python scripts/sov_traps.py` | Are the hazards recorded in `CLAUDE.md` still real? Fails when one stops being true. |

## Where the work stands

| Command | Subcommands | Answers |
| --- | --- | --- |
| `sov_docket.py` | `check` `holds` `queue` `unrouted` | The owner's queue, rebuilt from the decision records rather than hand-written. |
| `sov_accept.py` | `audit` `present` `queue` `rulings` | The owner gate: what is presented for acceptance and what sits on a seat without a packet. |
| `sov_epic.py` | `status` `validate` `next` `unrouted` `sync` `report` | The epic-of-epics issue tree, from its checked-in projection. |
| `sov_backlog.py` | — | Every branch that never reached the trunk, so a disposition can be judged. |
| `sov_strand.py` | — | Work left lying around. Fails when any commit exists only on this disk. |
| `sov_branch.py` | `ledger` `retire` `worktrees` | Branch, worktree and merge management across many checked-out trees. |
| `sov_lease.py` | `take` `status` `close` `release` `fail` `draw` `helper` `selfcheck` | Who is holding which concern, under what envelope. |
| `sov_unblock.py` | `draft` `list` | Files a proven stall as an unblock request. `BLOCKED` is a claim that must be proven. |

## What the system claims to be

| Command | Subcommands | Answers |
| --- | --- | --- |
| `sov_canon.py` | `ground` `promises` `facts` `trace` `rollup` `check` | Product ground and canon, traced down to what is reachable. |
| `sov_spec.py` | `trace` | What the logical specification has actually earned. |
| `sov_service.py` | `check` `crud` `endpoints` | The declared service surface, judged. |
| `sov_capability.py` | `show` `build` `check` `offices` `events` | Which office answers which operation, and how. |
| `sov_kernel.py` | `table` `check` `parity` `drift` `closure` `binding-check` `selfcheck` | Shared Kernel projections and conformance. |
| `sov_node.py` | `status` `peers` `validate` | This node's identity and the peers it has admitted. |
| `sov_owners.py` | `status` `check` | The domain owner register. |
| `sov_interface.py` | `show` `build` `check` `invoke` `prove` | The derived Node Interface a model reader receives. |
| `sov_surface.py` | `render` `check` `try` | The same Node Interface rendered for a person. |

## Authority, standing and landing

| Command | Subcommands | Answers |
| --- | --- | --- |
| `sov_grant.py` | `list` `check` `selfcheck` | The standing authority grants, and whether one request is inside them. |
| `sov_standing.py` | — | Refuses a standing claim in `STATUS.yaml` that no witness record supports. |
| `sov_closure.py` | `loop` `judge` `selfcheck` | Whether a handoff is a genuine seam or a concern being abandoned. |
| `sov_custody.py` | `list` `board` `circuit` `lifecycle` `estimate` `reconcile` `orphans` `selfcheck` | Durable responsibility, active-work joins, closure, landing, settlement, and the charted extensions around them. |
| `sov_land.py` | — | The landing gate. The only place a witnessed change becomes a commit on `main`. |
| `sov_witness.py` | `semantic` | The semantic task a fresh witness can judge without reading the code. |

## Evidence and drift

| Command | Subcommands | Answers |
| --- | --- | --- |
| `sov_publication.py` | `audit` `check` `queue` `selfcheck` | Which surface each tracked path occupies, and where the tree and the declaration disagree. |
| `sov_diagrams.py` | `grade` `stamp` `selfcheck` | Whether each diagram still reads the source bytes it claims to have read. |
| `sov_snapshot.py` | `check` `selfcheck` | Whether the orientation snapshot in `CLAUDE.md` still matches the record. |
| `sov_docs.py` | `ingest` `build` `check` | The node's own documentation reader, with each document's custody shown beside it. |
| `sov_baseline.py` | — | Holds the Asset Service to its recorded conformance baseline. |
| `sov_mutate.py` | `sites` `run` `selfcheck` | How much the test suite actually asserts, by mutating what it tests. |
| `sov_trace.py` | `up` | One measured execution, walked up to the product intention that justified it. |
| `sov_f2_gate.py` | — | The F2 milestone gate, exactly as `SPEC.md` states it. |

## Coordination and scheduling

| Command | Subcommands | Answers |
| --- | --- | --- |
| `sov_session.py` | `list` `who` `brief` `new` `claim` `release` `end` `reserve-decision` `heartbeat` `guard` `contested` `prune` `principal` `worktree` `register` `selfcheck` | Which live sessions share this tree and who holds which path. Git answers what changed, never who is changing it. |
| `sov_board.py` | `review` `apply` `selfcheck` | The coordination surface: survey it, then apply what is approved. |
| `sov_ticket.py` | `transition` `selfcheck` | The ticket coordination contract. |
| `sov_schedule.py` | `validate` `list` `due` `run` `tick` `ledger` `task-command` | Scheduled runs of harness workflows. Every shipped schedule is disabled. |

## Not entrypoints

`scripts/sov*/` packages hold the implementations these commands drive;
`scripts/tests/` holds their tests, run by `scripts/run_tooling_tests.py` inside
`verify.py`. `scripts/verify_bootstrap.py` checks a fresh checkout's structure
and evidence digests before anything else runs.

`AGENTS.md` fixes what this directory may own: verification and bounded
repository maintenance, never product business logic.
