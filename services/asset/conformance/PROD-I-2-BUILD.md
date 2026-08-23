# PROD-I-2 Derivative Reconstruction Build Record

Observed: `2026-08-22`

Participant: `asset-service-reference@feat/asset-recording-reconstruction`

Standing: `BUILT_SELF_TESTED_NOT_WITNESSED`

## Operation plan

- **Requested outcome:** make every derivative recording reconstruct its exact
  source, reader version, configuration digest, fidelity, and recoverable
  omissions under C2 and PROD-I-2.
- **Authoritative pre-state:** `BASELINE.md` records `PROD-I-2` as `FAIL`, and
  `KNOWN-GAPS.md` names both reconstruction and the over-limit Asset core.
- **Affected surfaces:** the Asset reader/recording contract, derivative
  lifecycle, participant observation adapter, positive tests, and refusals for
  undeclared readers and changed sources.
- **Effect class:** `RECORD_LOCAL` in temporary test nodes only.
- **Counteraction boundary:** the branch can be abandoned without changing a
  deployed node; payload writes remain subject to the separately named atomic
  commit gap.

## Built observation

- The former 341-line core is split into storage, control, recording,
  derivative, observation, projection, and facade modules, all below 300 lines.
- `ReaderDeclaration` requires an exact reader/version/configuration identity
  and output role.
- `LOSSY` output requires stored, non-empty omission identifiers; `EXACT` output
  refuses any omission.
- Compatibility is fail-closed: the prior undeclared-reader call shape remains
  callable but returns a `READER_UNDECLARED` refusal instead of producing an
  incomplete derivative.
- A recording resolves its derivative operation and run, immediate source
  version and digest, output CAS address and digest, reader identity,
  configuration digest, fidelity, omissions, producer, and `RECORDED` standing.
- Reporting re-verifies source bytes; reconstruction re-verifies both source and
  output bytes.

## Checks

- Asset unit tests: `6` passed, including incomplete-reader, changed-source,
  and corrupted-output defeating cases.
- Participant oracle: `RUN-I2-REMEMBER PROD-I-2` returned `PASS` with zero
  defects; the complete nine-requirement participant suite correctly remains
  `FAIL` on eight unrelated open requirements.
- Repository hygiene: `PASS`, 0 named module-size debts.
- Root `python scripts/verify.py`: `PASS` in `0.557s` on the observed host.

## Residuals and next gate

This is Blue/self-test evidence only. It does not witness the implementation,
ratify the Phase-I specification, close issue #27, or introduce a model binding.
An independent Red engagement must attempt provenance substitution, source and
output corruption, reader/configuration ambiguity, and omission erasure. Every
confirmed defect becomes a permanent defeating fixture before `WITNESSED`.
