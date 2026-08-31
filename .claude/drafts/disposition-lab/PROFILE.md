# Disposition profile contract v0.1

Status: `EXPERIMENTAL · ISSUE #200`

A profile is a deterministic projection over admitted observations for one exact subject revision.

## Identity

A profile binds:

- `subject_id`;
- `subject_revision`;
- `subject_kind`;
- subject adapter/configuration declaration;
- construct-bank digest;
- evidence digest;
- scorer/profile schema revision.

A model or agent revision must include material configuration that can alter behavior. A code subject revision should resolve to an exact source/artifact revision. A materially changed subject is not silently folded into the old profile.

## Construct estimate

For each applicable construct v0.1 records:

- status;
- observation count `n`;
- center;
- spread;
- standard error when calculable;
- observed minimum/maximum;
- represented contexts.

The current scorer uses arithmetic mean and population standard deviation over admitted normalized values. This is deliberately interpretable and provisional.

A construct with fewer than three admitted observations remains `INSUFFICIENT_EVIDENCE` even though descriptive values may be shown. A future calibrated scorer may replace this method only under a new scorer/profile revision; it must not rewrite old profile semantics.

## Evidence versus profile

The evidence ledger is append-only research evidence. The profile is rebuildable.

Deleting a profile must not remove evidence. Editing a profile cannot alter an observation. If a regenerated profile disagrees with a prior profile under the same pinned inputs/revisions, verification should fail rather than silently selecting one.

## Comparison

Profile creation and profile comparison are different operations.

A valid profile does not imply that its numerical scores are comparable to another subject, cohort, adapter, language, or subject kind. Comparison requires an admitted equivalence/calibration relation for the exact crossing being claimed.

Until then:

`profile = allowed`

`cross-kind percentile/ranking = NOT_COMPARABLE`

## Projection

A projection consumes a profile and names:

- source profile digest;
- projection/mapping revision;
- calibration standing;
- intended use;
- omitted information/loss;
- whether cohort comparison was admitted.

The projection cannot update the profile or evidence ledger.

## Reception profiles

Disposition Lab anticipates but does not yet implement a separate relational reception profile:

`reception = subject × observer × context × observation`

This is where graded language such as warmth, friction, clarity, confidence, rigidity, playfulness, or perceived agency can be studied without confusing the observer's experience with an intrinsic disposition of the subject.

Reception should become a sibling projection/evidence channel, not another field casually inserted into disposition scoring.
