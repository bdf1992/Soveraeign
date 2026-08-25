# Console Service Reference Gaps

Status: `OBSERVED AGAINST THE CHARTER · NOT OWNER-RATIFIED`

The continuity record path is built and self-tested
(`decisions/0036-operator-continuity-before-the-screen.md`). Five of the
`CHARTER.md` operator surfaces are named there; one of them exists. This file
says which, so the built part is not read as the whole.

| Gap | Observed behavior | Required behavior | Contract |
| --- | --- | --- | --- |
| Notifications | A `mentions_you` flag is derived when reading continuity | A notification is an addressed input record naming its source address, digest, kind, and acknowledgement | `notification.schema.json`; CONS-004 |
| Judgement requests | Not implemented | Queued requests that never block operation, with loop mode, requested authority type, and a resolution back-reference | `judgement-request.schema.json`; PROD-I-6; CONS-001, CONS-008 |
| Judgement resolutions | Not implemented | The only console record expected to reach `RATIFIED`, and only by an appended event | `judgement-resolution.schema.json`; CONS-002, CONS-009 |
| Operator settings | Not implemented | Typed, scoped preferences whose change requires named authority and never widens it | `operator-setting.schema.json`; CONS-003 |
| Dashboards and activity views | Not implemented | Declared projections over sibling-service events and receipts, naming their omissions and their rebuild operation | `projection-view.schema.json`; CONS-005, CONS-007 |
| Channel and thread reads | Only whole-journal folds exist; there is no channel listing operation | Bounded reads over channels and threads without replaying the journal per lookup | `CHARTER.md` owned records |
| Identity | Every operator is a string; anyone may record a grant naming any granter | A grant checked against the granter's own authority to grant it | `AGENTS.md` Authority; there is no Identity service to check against |
| Authority envelope | Grants carry operator, capability, and scope | Type, issuer authority, budget, validity window, and expiry must be enforced | C3; PROD-I-5; the Asset Service has the same gap |
| Two-binding proof | One binding exists, the CLI. Parity is proven by driving one path with two `actor_kind` values | A human binding and a model binding passing the same fixtures against the same kernel contract | PROD-I-3; CONS-006; `AI-NATIVE.md` check 7 |
| Independent observation | Every check here is the service's own test | An observer whose relation to the builder is independent | C7; `AI-NATIVE.md` check 3 |
| Federation | Not implemented; the manifest declares the port | A second node reachable through a governed crossing, refusing with a receipt while unconfigured | CONS-007; `SPEC.md` `cross` |
| Retraction | The journal supports counter-records; the console exposes no retract operation | An operator on the loop countering an effective record through the kernel | C8; CONS-007; `AI-NATIVE.md` retraction axis |
| Read cost | Reading continuity replays the whole journal every call | A rebuildable projection that is stored and refreshed, not recomputed per read | `SPEC.md` Projection rule |

## Where this sits against the AI-native bar

`AI-NATIVE.md` scores a surface performing a named operation. For
`console.post` and `console.session-context`, read honestly:

- **Reachability** - a stable declared CLI, a discovery command that answers what
  may be done and what it requires, JSON in and out including refusals. Strong,
  but one binding is not the two-binding proof.
- **Commitment** - records enter at `RECORDED` and the service cannot lift them;
  a model claim without a proposal is refused. This axis is the strongest one.
- **Provenance** - every post has a content address and digest, a receipt, and a
  named grant; the journal chain verifies before any read.
- **Retraction** - the substrate supports it, the console exposes no operation
  for it. `NONE` until it does.
- **`earn_it`** - a human judgement with an attributable reviewer. Not made.
  `AI-NATIVE.md` is explicit that `OPEN` is not a favorable result.

So: not `SOVERAEIGN_QUALIFIED`, and not claimed to be. That bar wants `FULL` on
reachability, commitment and provenance plus nine further checks, of which
independent observation, the two-binding proof and cold-start competence are all
unmet here. Recording the assessment is not the same as passing it.

These are unimplemented requirements and named defects, not reasons to treat the
built path as finished.
