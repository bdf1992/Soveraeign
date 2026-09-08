# Disposition Lab candidate quality metrics

Status: `EXPERIMENTAL · ISSUE #200`

These metrics are proposed observations for research runs, not pass/fail thresholds until enough pilot data exists.

## Software integrity

- deterministic replay equality;
- ledger chain verification rate;
- derived report rebuild equality;
- refusal coverage for invalid/missing inputs.

## Probe behavior

- completion/refusal/missing rate by probe and adapter;
- paraphrase sensitivity;
- context sensitivity;
- within-probe repeatability;
- scorer disagreement where human coding is required;
- floor/ceiling effects.

## Construct behavior

- observations per construct/context;
- center, spread, standard error;
- short-term retest correlation where applicable;
- inter-construct correlation matrix;
- same-construct versus cross-construct probe coherence;
- candidate factor structures and residuals.

## Crosswalk behavior

- convergent association with target framework dimensions;
- discriminant association with non-target dimensions;
- held-out mapping error;
- calibration drift across cohorts/contexts;
- categorical instability introduced by thresholding continuous scores.

## Adapter/equivalence behavior

- configuration sensitivity;
- adapter method effects;
- differential probe functioning;
- configural/metric/scalar equivalence where the statistical model makes those tests meaningful;
- explicitly narrower partial-equivalence claims when full equivalence fails.

## Report behavior

- percentage of statements directly resolvable to recorded observations;
- number of disclosed omissions;
- projection loss declaration present;
- calibration standing present;
- unsupported percentile/rank claims: target `0`;
- official-instrument impersonation by `-like` projections: target `0`.
