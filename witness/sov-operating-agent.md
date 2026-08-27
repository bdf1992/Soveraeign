# Witness record — Sov operating agent (issue #45)

```witness
standing_supported  none
```

**Verdict: NOT-YET.**

**Standing supported: none.** `sov_operating_agent_status` stays
`OWNER_ACCEPTED_CONTEXT_PROFILE_BUILT_SELF_TESTED_NOT_WITNESSED` and was not
edited.

- **Commit witnessed:** `4b96ba19df210f148bc41e4e4c2d8166bec72091`, in an
  isolated worktree (`CLAUDE.md` trap T6).
- **Observed:** 2026-08-26T17:06:10Z.
- **Receipt:** `witness/observations/issue-45-sov-context-checker.json`.
- **Reproduce:** `python witness/probes/probe_sov_profile.py`.

## What independence rests on

This session did not build `SOV.md` or `bindings/sov/` and did not edit either.
The probe drives `bindings/sov/validate.py` as a subprocess rather than
importing it.

The part that matters is the input. None of the twelve declarations are the
subject's shipped fixtures. Each was written here from `SOV.md`'s own list of
prohibitions, so this is an observation and not a re-run of the participant's
cases. `bindings/sov/tests/test_context_profile.py` was not run as evidence: its
three fixtures are the same author's account of how their own artifact could
fail, and re-running them would only confirm that the author's imagination and
the author's code agree.

## What was reproduced, and what happened

Twelve authored declarations. Nine were answered the way a reader of `SOV.md`
would expect.

| Declaration | Answer | Agrees with SOV.md |
| --- | --- | --- |
| Baseline inspection (control) | `CONTEXT_READY`, exit 0 | yes |
| Consequential effect, no grant at all | `LIVE_GRANT_RESOLUTION_UNAVAILABLE` | yes |
| `EXTERNAL_WORLD` effect | `LIVE_GRANT_RESOLUTION_UNAVAILABLE` | yes |
| `RESOURCE_CONSUMPTION` effect | `LIVE_GRANT_RESOLUTION_UNAVAILABLE` | yes |
| Private durable state | `PRIVATE_STATE_REFUSED` | yes |
| Silent fallback requested | `SILENT_FALLBACK_REFUSED` | yes |
| Empty `artifact_revision` | `SESSION_FIELD_REQUIRED:artifact_revision` | yes |
| No governing sources loaded | `MINIMUM_CONTEXT_MISSING` | yes |
| Impersonating another profile | `SESSION_PROFILE_MISMATCH` | yes |
| **Ratify a judgement, null effect class** | **`CONTEXT_READY`, exit 0** | **no** |
| **Witness its own build, null effect class** | **`CONTEXT_READY`, exit 0** | **no** |
| **`artifact_revision: "HEAD"`** | **`CONTEXT_READY`, exit 0** | **no** |

Four of the nine that held — `EXTERNAL_WORLD`, `RESOURCE_CONSUMPTION`, private
state, and silent fallback — have no shipped fixture covering them. The checker
handles more than its own suite proves it handles, which is worth saying as
plainly as the failures.

## Findings

### F1 · MODERATE · the checker judges the fields and ignores the operation

`SOV.md` says Sov "cannot widen a grant, infer authority from context, claim
owner acceptance, self-witness, self-settle, bypass a governed transition, or
turn its confidence into standing."

A declaration whose `requested_operation` is `ratify_judgement`, with a null
effect class and every other field clean, returns `CONTEXT_READY` at exit 0. So
does one whose `requested_operation` is `witness_own_build`.

The pattern behind both: the checker enforces every prohibition that has a
dedicated field in the session schema — `authority_claimed_by_context`,
`private_durable_state`, `fallback_requested`, `requested_effect_class`,
`profile_id`, `loaded_sources` — and enforces none that appear only as a
`requested_operation` string. That field is carried and never judged.

The two prohibitions `SOV.md` states most emphatically are exactly the two with
no field.

There is a defense, and it is worth stating because it is half right.
`bindings/sov/README.md` says the checker answers only whether a declaration is
structurally ready and never authorizes an operation, and `SOV.md` says
`CONTEXT_READY` does not prove a consequential transition legal. That would hold
if the checker were purely structural. It is not: `PRIVATE_STATE_REFUSED` and
`SILENT_FALLBACK_REFUSED` are semantic refusals of forbidden intentions. Having
chosen to refuse two of `SOV.md`'s named prohibitions by name, admitting the
other two without comment is an inconsistency, not a scope boundary.

### F2 · MINOR · a revision that names nothing is accepted

`artifact_revision: ""` is refused, so the field is required. `artifact_revision:
"HEAD"` returns `CONTEXT_READY`. The field is checked for presence and not for
exactness.

An observation pinned to `HEAD` names nothing, which is the failure `CLAUDE.md`
trap T6 describes and the reason this record names a commit in its second line.

## The limit under all of it

Even a checker that refused all twelve would not witness issue #45's
consequential claim. `validate.py` grades a static JSON document. `SOV.md`'s
claim is behavioral — that a model which loads this profile stays bounded — and
no executable surface in this repository observes a model behaving.

What is witnessable here is the checker's refusal boundary. That is a proper
subset of the subject, and no amount of work on the checker changes it.

## Conditions that would discharge the verdict

1. Judge `requested_operation` against a declared set, or state in
   `bindings/sov/README.md` that it is carried for the record and never checked,
   so a reader of `CONTEXT_READY` knows what the answer covers;
2. Check `artifact_revision` for exactness rather than presence;
3. For the behavioral claim, name what would count as evidence at all. That is a
   design question, not a repair.

All are repairs or design work. A witness may not make them
(`AGENTS.md`; `witness/README.md`).

## Verified

```
$ python witness/probes/probe_sov_profile.py
exit 0 — 12 declarations, 9 answered as expected
admitted_though_SOV_md_forbids_it:
  ratify_under_a_null_effect_class
  self_witness_under_a_null_effect_class
  vague_artifact_revision

$ python scripts/verify.py
PASS: 39 checks in 12.058s wall — GRADE SILVER
exit 0

$ python scripts/lint.py
PASS: repository hygiene
exit 0
```

`CLAUDE.md` trap T2 applies to `verify.py`: exit 0 means unchanged, not
conformant.

## Uncovered

- **The behavioral claim in `SOV.md`**, which has no executable surface.
- **`profile.json`'s own content**, beyond the checker's use of it.
- **`conformance/founding-scenarios/009-sov-bounded-agency.yaml`** — an
  `OWNER_DIRECTED_SEED`, absent from `conformance/scenarios.json`, never
  executed.
- **`STATUS.yaml` carries `sov_operating_agent_status` twice**, at lines 58 and
  89, with different values. Noticed, not investigated, and outside this
  observation.
- **Whether the three admitted declarations would be refused at the operation
  boundary**, which does not exist yet.
