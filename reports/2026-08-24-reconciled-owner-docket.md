# One docket, from two that disagreed, 2026-08-24

Status: `SYNTHESIS · NOT WITNESSED · NOTHING RATIFIED`

Two independent readings of what waits on Bdo landed within an hour of each
other and produced different numbers.

`reports/2026-08-23-qa-witness-sweep-c296c25.md` — six witness agents over the
nine commits `3341df8..c296c25` — counts **eighteen** items, deduplicated from
58 raised across the six. `contracts/acceptance-routing.json` in this branch
counts **three**.

Both are mine to reconcile because the smaller number is mine, and it is the
one that was wrong in the more misleading direction.

## Why they differ

They answer different questions and neither says so.

The routing table asks *which of the forty decision records needs Bdo*. The
sweep asks *which questions raised by observing nine commits need Bdo*. Most of
Bdo's real queue turns out not to live in decision records at all: it lives in
seams, in contracts that disagree with their implementations, and in vocabulary
that no document owns. Answering the narrow question and reporting the answer as
"three decisions wait on you" understated the desk by a lot, and this record
exists to correct that.

The correction runs one way only. The routing table is still right about the
forty records; it was the framing around it that was too small.

## Applying the routing test to the sweep's eighteen

`decisions/0023` reserves five categories to the owner: product intent, public
naming, external commitment, irreversible external effect, and the acceptance
standing itself. `decisions/0033` Ruling 1 says everything else settles at the
lowest tier that can produce defeating evidence. Run the sweep's items through
that test and the eighteen do not all survive it.

### Already answered, and can leave the list — 1

**The 3.000s budget** (sweep item 5). Resolved while the sweep was being
written: `scripts/verify.py` now reads `BUDGET_SECONDS = 15.0`, committed in
`7cae8bf`. The margin problem the sweep correctly identified is gone. Whether 15
seconds is the right number is a verification-domain question, not his.

### Settleable below the owner — 5

- **Should the manifest check be bidirectional** (item 6). The sweep itself says
  "buildable now". A checker that proves everything implemented is declared is
  defeasible by a fixture, which is what Ruling 1 means by evidence at the lower
  tier. Work.
- **Should witnessing run against a committed ref by rule** (item 18).
  Verification-domain policy, and the evidence is already in hand: two
  consecutive independent reports were partly invalidated by concurrent edits.
  Control.
- **Correcting the stale numbers in `0038` and `0040`** (item 15). An edit, not a
  judgement.
- **S18, the gateway naming collision** (item 12). An internal service name, not
  public naming. `decisions/0023` reserves *public* naming; nothing is published.
  Control, and the sweep is right that it is cheap now and expensive later.
- **Should `STATUS.yaml` gain entries for the capability map, MCP binding, and
  seat etiquette** (item 14). The sharper half of that item is not a judgement at
  all: *nothing validates `STATUS.yaml`*. That is buildable and belongs at Work.

### Genuinely his — 12, and three of them are new to me

Product intent or vocabulary that no lower tier can settle:

1. **Is `NONE` an admissible effect class** (item 1), with the same question for
   `DERIVED`, `REBUILT`, `SUPERSEDE`, `REBUILD`, `counters`. Either
   `CLASSIFICATION.md` grows or six manifests are wrong. `CLASSIFICATION.md` is
   owner-accepted vocabulary, so changing it touches the acceptance standing.
2. **Does `bindings/mcp/` need a decision record before it stays a required
   check** (item 2). 820 lines that open sessions, issue grants, write to the
   operational record, and one endpoint spawns the repository gate itself.
3. **Is `decisions/0038` admitted retroactively** (item 3). It states as a
   constraint that no capability is served on MCP and that standing up a stdio
   surface is not admitted by it. The next commit did exactly that.
4. **Is caller-asserted attribution acceptable over a binding** (item 4).
5. **Which scope semantics is the node's** (item 8) — console matches `*` by
   string equality, asset treats it as a wildcard.
6. **Does a `COUNTERED` crossing admit its origin** (item 9).
7. **Is `contracts/public-projection.schema.json` the target, or is the console's
   simpler view the real one** (item 10).
8. **S17: which reading of `INCOMPLETE_PROPOSAL` holds** (item 11).
9. **Should a manifest carry `standing` at all** (item 7), given a build cannot
   witness itself.
10. **S19: is outward publication a root-seat judgement or work any seat may do**
    (item 13).
11. **`.claude/settings.json` is checked in** (item 16), so opening this
    repository in any Claude Code host writes an operator session to the console
    journal at session start. That is a default applying to anyone who clones it.
12. **Is a self-authored subprocess-only checker an independence claim** (item
    17). This one is about what witnessing means, so it reaches the acceptance
    standing directly.

Plus the three decision records from the routing table — `0020` seat topology,
`0035` seat etiquette, `0039` the node surface — which the sweep did not cover
because it read commits rather than records.

**Fifteen, not eighteen and not three.**

## Where the two readings collide

Sweep item 3 challenges this branch's own routing. `contracts/acceptance-routing.json`
marks `0038` `reaches_owner: false`, reasoning that a rebuildable projection over
existing manifests touches nothing owner-held. The sweep found that `0038`
explicitly rules MCP is served nowhere, and that the following commit served it.

If a decision record's stated constraint was contradicted by the next commit,
the question of whether the record still stands is not a projection question and
not mine to route away. **That routing entry is probably wrong**, and it is
recorded here rather than quietly corrected, because a routing table that edits
itself when challenged is worth less than one that shows where it was pushed.

The same doubt does not extend to `0036` and `0040`; nothing in the sweep touches
their routing.

## Two things the sweep says about the evidence itself

Worth carrying because they change how much any of tonight's reports are worth.

**Six of six witnesses reported the required gate as failing, and it was not.**
They measured `verify.py` at 3.17–3.78s against a 3.000s budget while six agents
ran a 21-way subprocess fan-out concurrently on one machine. Measured cleanly at
`c296c25` it was 2.56–2.67s, all 21 green. A seventh witness reported the honest
split and drew no conclusion from it. The real finding was margin, not failure,
and the difference between those two claims is the entire value of witnessing.

**The oracles are not decorative.** One witness mutation-tested six of them and
every one failed as it should; a seventh mutation turned the full gate red. Every
new contract in the range carries both polarities. That is the finding that makes
the rest of the sweep believable, and it is easy to miss under nine defects.

## What this record is not

A witness. It is a synthesis by the same session that wrote the smaller of the
two lists it reconciles, which is the defect it opens by admitting. An
independent reading of the routing has been requested and had not arrived when
this was written.

It also settles nothing and closes no record. Fifteen items is a claim about
whose each question is, not an answer to any of them.
