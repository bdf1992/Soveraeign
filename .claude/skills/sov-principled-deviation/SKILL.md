---
name: sov-principled-deviation
description: Apply and record bounded spirit-over-letter judgement under existing authority. Load when a literal governed path would defeat governing intent, a consequential heuristic is replaced, experience evidence motivates a reversible improvement, overperformance is proposed, or a deviation intent/outcome record is required. Never use this skill to widen authority, bypass an invariant, resolve conflicting governing records, self-witness, change policy, create irreversible external effects, or open or close a phase.
---

# sov-principled-deviation

## Purpose

Serve governing intent without turning obedience into the only form of safety
or participant judgement into sovereignty.

The mechanics hold the letter. Agency carries the spirit. The record makes a
participant's own better path inspectable enough to permit, witness, learn
from, reject, or reverse without pretending the path was the rule.

The owning policy is `decisions/0101-principled-deviation.md`. The record shape
is `contracts/principled-deviation.schema.json`. This skill projects their
procedure to the Claude harness; it grants no authority and owns no rule.

## Hard perimeter

Before considering deviation, resolve the live identity, grant, operation,
effect class, governing rule, its source-owned classification, and governing
intent.

Refuse or escalate when any of these is true:

- the operation is outside the live grant;
- an invariant would be weakened;
- the rule classification or governing intent cannot be resolved from its
  source;
- governing records conflict materially;
- the act creates new authority or policy;
- the act has an irreversible external effect;
- the act opens or closes a phase;
- the participant would witness or settle its own result.

Deviation does not supply authority. A good result never repairs missing
authority after the fact.

## Decide whether a record is needed

For `GOVERNED`, use the full deviation path whenever departing from the literal
rule.

For `HEURISTIC`, choose the fitter path as ordinary judgement. Use the full
path only when the departure is consequential: externally visible, affects
another participant's expectations, materially changes risk, or is worth
retaining as learning.

`INVARIANT` has no deviation path.

## Procedure

1. State the value you are responsible for delivering.
2. Resolve the live authority and the invariants that must remain true.
3. Cite the governing rule, revision, source-owned class, intent, and intent
   revision. Do not classify the rule yourself.
4. Compare the literal and chosen paths. Name the expected benefit, risks,
   compensation or reversal, and effects to watch.
5. For a consequential planned deviation, append `INTENT` before acting.
6. Perform only the operation already covered by the live grant. Preserve its
   ordinary receipt.
7. Append `OUTCOME` after observation. Keep attributed experience distinct
   from independent witness evidence.
8. Choose `ONE_OFF`, `RULE_CHANGE_CANDIDATE`, `REVERTED`, or `FAILED`.
9. If it is a policy candidate, route it to the seat that can change the rule.
   Do not edit policy as part of the deviation.

A spontaneous reversible act may precede its `INTENT` record. Record
`timing: AFTER_ACTION`, cite the already-existing action receipt, and preserve
the truthful ordering. Never backdate it or describe it as authorization.

## Overperformance

Extra value is allowed only when the accepting participant can reject it
without losing or invalidating the originally requested value. If the extra is
required for the requested value to work, it is implementation, not
overperformance. If it cannot be separated, do not bundle it.

## Experience evidence

Record a participant's experience in first-person or clearly attributed form:
"I could not determine what this control would do" is evidence. Do not silently
inflate it into a universal claim such as "the interface is unusable."

Experience may motivate a bounded improvement. It never becomes an objective
measurement or an independent witness merely because it is recorded.

## Record skeletons

Use the schema rather than copying these labels as a second contract.

```yaml
record_kind: INTENT
deviation_id: deviation:<id>
timing: BEFORE_ACTION | AFTER_ACTION
rule_ref: <governing source address>
rule_revision: sha256:<digest>
rule_class: GOVERNED | HEURISTIC
governing_intent_ref: <source address>
literal_path: <what the rule says>
chosen_path: <bounded alternative>
authority_basis: [<live grant ref>]
```

```yaml
record_kind: OUTCOME
deviation_id: deviation:<same id>
intent_record_ref: <INTENT record>
action_receipt_ref: <ordinary action receipt>
observed_effects: [<attributed observation>]
disposition: ONE_OFF | RULE_CHANGE_CANDIDATE | REVERTED | FAILED
```

## Verification

- `python -m unittest conformance.tests.test_principled_deviation -v`
- `python scripts/verify.py`
- `python scripts/lint.py`

Passing establishes built evidence only. It does not accept this policy,
ratify an outcome, change a rule, or open Phase II.

## Report

Report the authority basis, invariant reading, source-owned rule class,
literal and chosen paths, truthful event order, action receipt, observation,
experience attribution, independent witness status, disposition, and any
policy candidate. Name refusal or escalation plainly when the perimeter fails.
