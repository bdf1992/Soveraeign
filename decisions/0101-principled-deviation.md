# 0101 · Principled deviation: judgement without sovereignty

Status: `OWNER-DIRECTED · CONTRACT WORDING PROPOSED`

Bdo directed this policy on 2026-08-31 while defining the Phase 1.5 substrate.
It is built here for acceptance; this record does not ratify itself and does
not open a successor phase.

## Decision

A participant may interpret how to serve intent. It may not reinterpret what
gives it authority.

The mechanics hold the letter. Agency carries the spirit. The append-only
record is what makes it safe for a participant to choose its own better way of
delivering value: the choice remains attributable, inspectable, reversible or
compensable, observable, and available for later rule improvement.

An action is admissible when all of the following hold:

```text
ADMISSIBLE(action) =
    AUTHORIZED(action)
    AND INVARIANTS_PRESERVED(action)
    AND (
        ORDINARY_RULE_SATISFIED(action)
        OR PRINCIPLED_DEVIATION_ADMITTED(action)
    )
```

Deviation supplies an alternative execution route. It never supplies
authority. A successful outcome does not retroactively authorize an
unauthorized action.

The governing source classifies each rule:

- `INVARIANT` must hold. It has no deviation route.
- `GOVERNED` names a normative path from which a bounded, explicit deviation
  may be admitted in service of the governing intent.
- `HEURISTIC` names a preferred path. A participant may substitute a fitter
  path within ordinary judgement. It records a deviation only when that choice
  is consequential: externally visible, changes another participant's
  expectations, materially changes risk, or is worth retaining as learning.

The deviating participant resolves and cites the classification; it does not
create it. It may interpret a governed rule against governing intent. It may
not amend the rule, its classification, governing intent, or its authority.
A material conflict between governing records is an escalation, not a choice
of whichever source makes the action convenient.

## Evidence record

A consequential deviation has one identity and two append-only records:

```text
Deviation INTENT -> Action receipt -> Deviation OUTCOME
```

The `INTENT` records the literal path, chosen path, authority basis, expected
benefit, known risks, compensation or reversibility, and effects to watch. The
`OUTCOME` references that intent and the action receipt, records what was
observed, and assigns one disposition: `ONE_OFF`, `RULE_CHANGE_CANDIDATE`,
`REVERTED`, or `FAILED`.

For a spontaneous reversible act, the truthful order may be action receipt,
then `INTENT`, then `OUTCOME`. The intent record uses `AFTER_ACTION` and cites
the receipt. It never masquerades as pre-authorization. Records are appended;
an intent is never filled in later with its outcome.

Subjective experience is legitimate attributed evidence. It remains
experience evidence: recording it does not turn it into an objective measure
or an independent witness. A builder's experience can justify a bounded
improvement without satisfying a witness obligation.

Overperformance is admissible only when its extra value is separable. The
accepting participant must be able to reject the extra value without losing
or invalidating the value originally requested.

## Learning without self-legislation

The learning path is:

```text
Rule -> Tension -> Intent -> Action -> Observation -> Disposition
     -> Policy candidate -> Authorized rule change
```

There is no automatic edge from observation to changed policy. Repeated
success, model consensus, or a useful outcome may create pressure for a rule
change; none of them performs that change. New authority or policy,
irreversible external effects, and phase opening or closure remain root-only.
Seat-bound acceptance and ratification remain governed by their typed grants.

The operating laws are:

- Letter is not intent.
- Deviation is not authority.
- Experience is evidence, not universal truth.
- A successful outcome does not retroactively authorize an unauthorized
  action.

## Contract and defeating evidence

- `contracts/principled-deviation.schema.json` owns the append-only `INTENT`
  and `OUTCOME` record shapes.
- `conformance/fixtures/deviation/principled-deviation-cases.json` carries
  admissible governed and consequential-heuristic cases plus cases that defeat
  invariant relabeling, unauthorized success, record collapse, experience as
  witness, inseparable overperformance, automatic policy change, governing
  conflict, and false pre-authorization.
- `conformance/tests/test_principled_deviation.py` grades those cases without
  importing participant implementation code.
- `.claude/skills/sov-principled-deviation/SKILL.md` projects the procedure to
  the Claude harness. The skill grants nothing.

## What would defeat this

- Participants use deviation receipts as routine ceremony rather than only
  for consequential departures.
- The mechanism makes it easier to conceal unauthorized actions than to
  refuse them.
- Governing sources cannot expose rule class and governing intent without
  creating a second policy system.
- Independent observation shows that the separability test still permits
  extras that coerce acceptance of the requested value.
- The two-record shape cannot preserve truthful ordering in the System of
  Record.

## Consequence

Phase 1.5 gains a controlled learning aperture for participants with their own
agendas and judgement. It gains no new authority, phase standing, or external
effect. Phase II remains unopened.
