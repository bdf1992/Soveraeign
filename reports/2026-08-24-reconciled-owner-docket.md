# One docket, from two that disagreed, 2026-08-24

Status: `SYNTHESIS · NOT WITNESSED · NOTHING RATIFIED`

Two independent readings of what waits on Bdo landed within an hour of each
other and produced different numbers.

`reports/2026-08-23-qa-witness-sweep-c296c25.md` — six witness agents over the
nine commits `3341df8..c296c25` — counts **eighteen** items, deduplicated from
58 raised across the six. `contracts/acceptance-routing.json` in this branch
counted **three** when this reconciliation began.

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

Plus the questions the routing table carries, which the sweep did not cover
because it read commits rather than records: `0020` seat topology, `0035` seat
etiquette, `0039` the node surface, `0042` this record's own machinery, and — after
the witness — `0036-B` and `0038-A`.

Two of those are the same question the sweep already had. `0036-B` is the sweep's
item 16, and `0038-A` overlaps its item 3. Counting the union rather than the sum:

| | count |
|---|---|
| from the sweep, genuinely his | 12 |
| from the routing, genuinely his | 6 |
| the same question counted twice — item 16 = `0036-B`, item 3 folded into `0038-A` | −2 |
| **union** | **16** |

**Sixteen**, against the sweep's eighteen and this branch's original three. Both
starting numbers were wrong in opposite directions and for different reasons: the
sweep counted questions the lower tiers can settle, and this branch lost questions
its unit could not express.

## Where the two readings collided, and what happened

Sweep item 3 challenged this branch's routing of `0038`, which marked it
`reaches_owner: false` on the reasoning that a rebuildable projection over
existing manifests touches nothing owner-held.

That was recorded as a doubt rather than corrected, on the principle that a
routing table which rewrites itself when challenged is worth less than one that
shows where it was pushed. It was then corrected, because an independent witness
of `06be56c` confirmed it on firmer ground than the sweep had:
`contracts/capability-offices.json` is not the projection at all. It is an
authored input carrying 79 assignments, each setting `required_authority`, and
assigning an authority type to every operation in the node is typed authority.

The original challenge stays on the entry as `contested_by`. The doubt was right;
the reason given for it was not the strongest one available, and neither was the
reason it was originally routed away.

`0040` is flagged and unmoved: it declares per-operation refusal codes and
`CLASSIFICATION.md` owns vocabulary. The witness was not confident either way and
neither is this record.

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

## The unit was the real problem

An independent witness of `06be56c` reached the reconciliation from a better
angle than "different frames", and it is worth recording because it makes the
disagreement disappear rather than explaining it away.

This branch routes **records**. A record can carry several questions with
different answers — `decisions/0036` names three, one for Control and one for
Bdo — and a per-record `reaches_owner` boolean cannot represent that. So the
count was not merely scoped differently from the sweep's; it *structurally lost
questions* whenever a record was mixed. Route questions and the two readings
reconcile without either being wrong.

The contract is now `soveraeign-acceptance-routing/v2`, keyed by question. Two
of the fifteen above changed as a direct result: `0036` split into a Control
question and an owner question, and `0038` moved to the owner on the
`required_authority` ground rather than the door-inventory argument its author
had been having with himself.

Nineteen questions against eighteen open records today. That ratio is close to
one because exactly one record enumerates its own questions; the others are
routed on their headline and any further question they carry implicitly is not
yet visible. `enumerated_from` says which is which, and the checker refuses to
let a record be split into several questions unless it declared them.

## What this record is not

A witness. It is a synthesis by the same session that wrote the smaller of the
two lists it reconciles, which is the defect it opens by admitting. An
independent reading of the routing has been requested and had not arrived when
this was written.

It also settles nothing and closes no record. Sixteen items is a claim about
whose each question is, not an answer to any of them.
