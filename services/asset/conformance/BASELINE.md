# Asset Service Conformance Baseline

Observed: `2026-08-22`

Participant: `asset-service-reference@WORKTREE`

Oracle and scenarios: `conformance/run.py` + `conformance/scenarios.json`

## Result

`FAIL`

| Requirement | Verdict | Observed defects |
| --- | --- | --- |
| PROD-I-1 · Propose | FAIL | proposal lacks content address, source addresses, and cost record |
| PROD-I-2 · Remember | FAIL | derivative lacks direct source, reader version, configuration digest, and recoverable lossy omissions |
| PROD-I-3 · Cross | FAIL | no second binding or fully declared crossing exists |
| PROD-I-4 · Gate and retract | FAIL | original and counter-record survive, but the counter receipt does not link the prior receipt |
| PROD-I-5 · Typed authority | FAIL | judgement refusal exists, but the participant cannot demonstrate the paired typed verification grant and commit |
| PROD-I-6 · Founder judgement budget | FAIL | missing judgement refuses synchronously instead of leaving a visible unresolved right and spend record |
| PROD-I-7 · Independent qualification | FAIL | no clean-room witness run or competence measurement exists |
| PROD-I-8 · Joint sign | FAIL | general runtime attestation is not implemented |

## Standing

This baseline binds the reference participant to the logical scenarios. It does
not mean the implementation is unusable: its narrower asset walk and stale
lease tests pass. It means no Phase-I requirement is yet demonstrated by the
complete scenario contract.

The scenarios and oracle remain frozen during participant repair unless an
independent regression proves a scenario or oracle defect. The typed-authority
control was hardened during baseline creation because it previously allowed a
judgement-only attempt to masquerade as the required two-type test.
