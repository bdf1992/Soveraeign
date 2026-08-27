# 0068 · Every tracked path declares the surface it occupies

Status: `PROPOSED · BUILT AND SELF-TESTED · RATIFICATION PENDING`

## Decision

`contracts/publication-surface.json` classifies every tracked top-level path into one of
six surfaces, and `scripts/sov_publication.py` grades the working tree against it. A path
that is tracked and unclassified is a defect. So is generated output with no builder, a
scratch directory with nothing that retires it, an entry document that does not reach what
its audience needs, and a document describing a completed operation with no marker saying
so.

The six surfaces and the rule each carries:

| Surface | Tracked | The rule it carries |
| --- | --- | --- |
| `HUB` | yes | The product a stranger clones. A newcomer route may name it. |
| `HOST` | yes | One host binding's harness, kept by owner choice, naming its host. |
| `DERIVED` | yes | Generated output, admitted only with a builder and a check that exist. |
| `JOURNAL` | yes | The record of work done. Never routed to as documentation. |
| `SCRATCH` | yes | Work in progress, declaring what retires it. |
| `LOCAL` | no | The operator's machine. Tracking one is a defect, not a preference. |

## Why this was reachable without asking

`PUBLICATION.md` is an active safety boundary and it answers one question: what may never
be published. It has no opinion on generated output, one vendor's harness, the work
journal, or scratch, because none of those were leaks. They were simply never classified,
so they accumulated in a public repository and a reader has no way to tell the product
from the workshop.

Naming that distinction is a `RECORD_LOCAL` change that a revert undoes. Deciding which
side a path belongs on is ordinary engineering judgement held by whoever carries the
concern (`AGENTS.md`, Closure ownership; `decisions/0033`, Ruling 1). What is *not*
reachable is removing anything: this record classifies and reports, and every removal it
implies is a separate change with its own evidence.

## Holder, and why the gate does not fail on owner-held findings

Each finding names a holder. A `sov`-held finding fails `check`. An `owner`-held finding
is printed and does not fail, because a declared gate stops one transition and not the
frontier (`AGENTS.md`, Authority). Today exactly one finding is owner-held: `README.md`
does not name a `LICENSE`, because no licence exists and choosing one is Bdo's
(`STATUS.yaml`, `owner_holds` O1, `PUBLICATION`).

That asymmetry is the point. A checker that failed on owner-held items would either block
work that is admissible or teach every participant to disable it.

## What this observed on first reading

Five defects held by `sov`, one finding held by the owner:

- `scripts/README.md` does not exist, so the node's 34 `sov_*.py` entrypoints have no
  index and `README.md` names one of them;
- the person route does not reach that index;
- the machine route does not reach `adapters/README.md`, so a reader arriving at
  `bindings/README.md` cannot find the three adapters that already exist;
- the machine route does not reach `bindings/INTEGRATING.md`, which does not exist, so
  nothing in the repository says how to add a binding or an adapter;
- `AGENT-BOOTSTRAP-PROMPT.md` instructs an agent to copy a ZIP seed into an empty
  directory and create the founding commit, an operation completed 2026-08-22, and carries
  no marker saying so while sorting first alphabetically at the repository root;
- `README.md` names no `LICENSE` (owner-held).

The tree passed the checks that would have been alarming: every tracked top-level path is
classified, no `LOCAL` path has tracked files, and every `DERIVED` path names a builder and
a check that exist. The repository's local-versus-hub separation is intact. Its routing and
its stale signposts are not.

## What would defeat this

- A path whose correct surface is genuinely ambiguous under all six, which would mean the
  vocabulary is wrong rather than the path.
- A route requirement satisfied by naming a path in prose while the reader still cannot
  reach it, which would mean substring matching is too weak a test for routing.
- `sov_publication.py check` passing over a tree a fresh reader still cannot navigate,
  which would mean these five checks are not the ones that matter.

## What still waits on Bdo

One thing, and it is already in `STATUS.yaml` as `owner_holds` O1: this repository is
public and carries no `LICENSE`, so a stranger reading it has no stated right to use it.
Which licence, and whether public is correct today, are naming and publication judgements
this record does not take.

Two further questions are owner-held but not blocking: whether `.claude/` stays in the
public tree at all, and whether `lineage/recordings/` and `lineage/SOURCES.lock` are worth
committing when no public checkout can verify either. Both are classified and reported
here; neither is changed.

## Consequences

`sov_publication.py check` is deliberately **not** wired into `scripts/verify.py` yet.
Wiring it while five `sov`-held findings stand would fail the build for every other session
in this tree over work none of them opened. It is wired in once the queue of `sov`-held
findings is empty, and that wiring is what makes this contract a gate rather than a report.

`python scripts/sov_publication.py queue` emits the findings as JSON with stable ids, which
is what a cleanup loop drains one item at a time.
