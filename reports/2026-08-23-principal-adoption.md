# Retroactive principal adoption, 2026-08-23

Status: `RECORDED · RETROACTIVE · NOTHING RATIFIED`

`decisions/0048-principal-identity.md` (ID-1) requires every `actor_id` to
resolve to a registered principal. Every actor string written before that
decision is folklore: a name someone typed, resolved by convention. This
report adopts those strings onto the principals declared in the positive
fixture of `contracts/fixtures/principal.fixtures.json`, in the same form as
`reports/2026-08-23-seat-adoption.md`. An adoption states what the string
meant; it does not verify the claim (ID-7) and grants nothing (ID-8). Bdo may
adopt, amend, or strike any row.

## Adopted strings

| String on record | Adopted by principal | Where it appears | Basis |
| --- | --- | --- | --- |
| `Bdo` (bare) | `principal:bdo` | decision records, STATUS.yaml authority holders, commit authorship | decisions/0001; sole human operator of this node |
| `urn:soveraeign:actor:bdo` | `principal:bdo` | seat-registry fixture occupancy, adoption reports | same |
| `urn:soveraeign:actor:claude-interactive-session` | `principal:session-2026-08-23` | seat-registry fixture, seat adoptions A1-A6 | interactive session launched and directed by Bdo, 2026-08-23 |
| witness agent `a34f27a` | `principal:witness-a34f27a` | seat adoptions A2-A5; kernel witness report on the PR #61 branch | sov-witness instance launched by the session |

## Deliberately not adopted

- Actor strings inside test fixtures and conformance controls (for example
  `urn:soveraeign:actor:worker` in kernel tests, `human-bdo` in
  `oracle-controls.json`): fixture data portraying actors, not acts by
  actors. Adopting them would fabricate history (ID-2's defeat).
- Actor strings in reports on unmerged branches beyond those named above:
  listed when their branches merge, adopted by whoever launched them.

## Residuals

- Every claim above is `UNVERIFIED` and says so (ID-7). Verification arrives
  with keys, which arrive when a forged-claim conformance case demands them.
- `principal:claude-fable-5` (the durable model operator) is adopted as the
  operator behind both instances; its anchor is the declared-but-unexecuted
  binding surface (`BYOM.md`), which is honest and thin until O12 lands.
