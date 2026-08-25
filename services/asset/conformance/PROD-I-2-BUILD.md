# PROD-I-2 Derivative Reconstruction Build Record

Observed: `2026-08-22`; reconciled with current `main` on `2026-08-25`

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

- Current main's newer storage, authority, identity, run, projection, route,
  and facade split remains canonical; recording and reconstruction are added to
  that architecture without restoring the superseded branch-local split.
- `ReaderDeclaration` requires supplied versioned reader bytes, a secret-free
  replay configuration, and an output role. Both materials receive immutable
  CAS addresses and digests before work is leased.
- `LOSSY` output requires stored, non-empty omission identifiers; `EXACT` output
  refuses any omission.
- Compatibility output created without a reader remains an Asset Version and
  produces no `Recording`; reconstruction refuses it rather than inventing
  provenance. A supplied but incomplete reader is receipted and refused.
- A recording resolves its derivative operation and run, immediate source
  version and digest, output CAS address and digest, reader identity,
  configuration digest, fidelity, omissions, producer, and `RECORDED` standing.
- Reporting re-verifies source, reader, and configuration materials;
  reconstruction re-verifies those inputs plus output bytes.
- Observation settles a derivative only after reconstructing that complete
  path; output-only success cannot conceal later source corruption.
- Reconstruction cross-checks the request plan, run, recording, and output CAS
  address instead of trusting isolated mutable metadata.

## Checks

- Asset unit tests: `96` passed after current-main reconciliation, including
  incomplete-reader, legacy-non-recording, post-report source corruption,
  changed reader/configuration materials, and tampered-output address cases.
- Participant oracle: `RUN-I2-REMEMBER PROD-I-2` returned `PASS` with zero
  defects; the complete nine-requirement participant suite correctly remains
  `FAIL` on eight unrelated open requirements.
- Repository hygiene and root verification are rerun on the exact merge
  candidate before landing; the original branch observation was `PASS` in
  `0.651s` with zero named module-size debts.

## Residuals and next gate

This is Blue/self-test evidence only. It does not witness the implementation,
ratify the Phase-I specification, close issue #27, or introduce a model binding.
It also does not attest that a worker semantically executed the addressed reader
artifact; that belongs to the later observation and model-binding gates.
An independent Red engagement must attempt provenance substitution, source and
output corruption, reader/configuration ambiguity, and omission erasure. Every
confirmed defect becomes a permanent defeating fixture before `WITNESSED`.
