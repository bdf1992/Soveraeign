# 0035 · How seats speak to each other

Status: `PROPOSED · DRAFTED AT OWNER DIRECTION · RATIFICATION PENDING`

Numbering note: drafted as 0034 and renumbered to 0035 when an in-flight
`git merge origin/main` landed `0034-spec-transition-refusal-codes.md` in the
same working tree. `decisions/0020` records the same collision at 0018/0019;
concurrent branches minting decision numbers is a standing seam.

Drafted by Claude at Bdo's direction (2026-08-23 conversation). Bdo asked for
contracts over the structured outputs of Sov, Controller, Orchestrator, and
Worker, and framed the intent precisely: declarations that carry the
*relationships* — a lightweight etiquette and a culture, not a specific schema
for what each role emits.

## Decision

Contract the **envelope and the edge**, not the report. What a seat says stays
freeform; who may say it, to whom, and what a listener owes onward becomes
machine-checkable.

Three claims:

1. **A message is an envelope around an unconstrained body.** Six fields carry
   everything the system needs: who is speaking, from which seat, to which
   seat, what kind of statement it is, the highest standing it proposes, and
   what it carries onward. The body — the actual report, plan, or verdict — is
   deliberately unconstrained, and no checker reads inside it.

2. **The relationship layer is one table, not four prose blocks.** Which acts
   each seat type may speak, in which direction, and how far each act may
   propose standing lives in `contracts/seat-etiquette.json`. It is generative:
   a new seat type or a new act is a change to that table alone. The message
   schema, the fixtures, and the checker all read from it.

3. **The culture is the duty of carriage.** A seat that receives a judgement
   question, a dissent, a residual, or a proven stall owes every one of them to
   its own listener, unedited. That single duty is what stops a builder's
   self-report arriving at the root looking like verified fact, and it is
   checkable without constraining how anyone writes.

### The acts

| Seat type | May speak | Highest standing it can propose |
| --- | --- | --- |
| `root` | DISPATCH, RATIFY, ACCEPT, HOLD | `WITNESSED -> RATIFIED` |
| `control` | DISPATCH, AGGREGATE, ASK, REFUSE, STALL | none; it forwards |
| `orchestration` | PLAN, DISPATCH, AGGREGATE, ASK, REFUSE, STALL | none |
| `work` | REPORT, ATTEST, DISSENT, UNATTESTABLE, ASK, REFUSE, STALL | `OPEN -> BUILT` as a builder, `BUILT -> WITNESSED` as a witness |

Every act is a proposal. The kernel and the root seat settle.

### Witness is a stance, not a seat type

`decisions/0020` types seats as `root`, `control`, `orchestration`, `work` —
there is no witness seat, and this decision does not add one. Instead every
speaker declares `relation_to_subject`: `PERFORMED` (I did this work),
`INDEPENDENT` (I did not, and I did not rely on the performer's report), or
`FORWARDED` (I am carrying someone else's statement).

A work seat is therefore a builder or a witness for a given operation,
decided by that field, never both. The prohibition in `AGENTS.md` — a build
report cannot witness itself — becomes one mechanical rule: no `INDEPENDENT`
statement about an operation may come from an `actor_id` that earlier made a
`PERFORMED` statement about the same operation. That is stronger than a seat
type would have been, because it catches the same actor changing hats.

### Sov has no row

`Sov` is a portable profile loaded into a seat, not a seat (`SOV.md`,
`CLAUDE.md`). It speaks with whatever acts the seat it occupies may speak.
Giving it a row would make it a fifth tier, which it is not.

## Machine form

| Artifact | Owns |
| --- | --- |
| `contracts/seat-message.schema.json` | the envelope; refuses an unknown act, an empty body, an omitted carriage claim, a half-proven stall |
| `contracts/seat-etiquette.json` | the acts, the per-seat act lists, the standing ceilings, the carriage duties, and what is explicitly out of scope |
| `contracts/fixtures/seat-message.fixtures.json` | 19 entries in the `contracts/fixtures` convention: five positive statements forming one chain, four the envelope refuses outright, and ten that are schema-valid and refused by the etiquette guard, each naming what it defeats |
| `contracts/fixtures/seat-topology.reference.json` | the seat projection the corpus is graded against, itself validated against `seat-registry.schema.json` |
| `scripts/sovkernel/seat_etiquette.py` | the guard; reads every rule from the etiquette table and reports an unimplemented duty as a defect rather than skipping it |
| `scripts/tests/test_seat_etiquette.py` | executes the corpus; `scripts/verify.py` already discovers `scripts/tests` |

Etiquette is a property of a sequence, not of one record, so a fixture entry
may carry `context`: the statements made before its record. The guard runs over
`context + [record]`. The corpus is graded against a checked-in seat projection
validated by `seat-registry.schema.json`, so the two contracts are proven to
compose rather than merely coexist.

## Standing

`BUILT` for the contract only: the schema, the table, the corpus, and the
guard execute and every defeating case fails for its declared reason. The
etiquette itself is a proposal. Nothing witnesses it, and nothing enforces it
against live agent output yet — see the next section.

## Defaults taken

- **Declarative before enforced.** No `scripts/verify.py` check parses live
  agent output against this contract. Agent output is free text today, so a
  parse gate would produce false failures while the shape is still settling.
  The fixtures prove the rules are real; the gate is the next step, and it is
  reversible in either direction. (Bdo's choice, 2026-08-23.)
- **Kernel contract, not harness plumbing.** These files live in `contracts/`
  rather than under `.claude/`, so a future non-Claude participant inherits
  them. (Bdo's choice, 2026-08-23.)
- **Witness as stance rather than a fifth seat type**, to avoid widening
  `decisions/0020` without Bdo's hand. Reversible: adding a `witness` seat
  type is a change to the registry schema and one line of this table.
- **Thirteen acts.** Chosen to cover exactly what the four agent definitions
  in `.claude/agents/` already claim to do, no more. Six of them
  (ACCEPT, ASK, DISPATCH, PLAN, REFUSE, UNATTESTABLE) have no fixture yet; the
  test asserts that exact list so the gap cannot widen unnoticed.
- **One record per fixture entry, with prior statements in `context`.** Carriage
  cannot be checked on a single record, but `contracts/fixtures/*.fixtures.json`
  is a flat entry list by convention (`scripts/tests/test_contract_fixtures.py`),
  so the sequence rides in an extra field rather than reshaping the file.

## What this decision does not do

- It does not constrain any report body, and it does not replace the report
  formats written into the four `.claude/agents/*.md` files. Those become
  instances of this envelope when Bdo says so.
- It does not enforce anything at runtime. No agent is required to emit a seat
  message today.
- It does not settle, ratify, or move any standing.
- It does not add a seat type, name a seat, or touch `decisions/0020`.
- It does not amend `AGENTS.md`, `SPEC.md`, or `CLASSIFICATION.md`. If the act
  vocabulary is to become governed terminology, that is a `CLASSIFICATION.md`
  amendment for Bdo's hand.

## Judgement queue for Bdo

1. Ratify, amend, or strike the act vocabulary. Thirteen acts is a guess at the
   right granularity; DISSENT and UNATTESTABLE could collapse into one, and
   ACCEPT and HOLD could be seen as one act with a reason field.
2. Should the four `.claude/agents/*.md` report formats be rewritten as this
   envelope, or should they keep their prose and reference it?
3. Do the act names belong in `CLASSIFICATION.md` as governed vocabulary, or
   do they stay contract-local?
4. Witness as a stance, or as a fifth seat type in `decisions/0020`?
5. When does the enforcing check land in `scripts/verify.py`, and does it fail
   the build or only warn?
6. Is the carriage duty right at four kinds (judgement items, dissents,
   residuals, stalls), or should reported outcomes and standing proposals also
   be carried by id?
