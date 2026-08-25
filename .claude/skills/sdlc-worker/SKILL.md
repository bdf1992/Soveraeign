---
name: sdlc-worker
description: Hold the Work tier of the SDLC loop - execute one scoped leased task in a declared environment and emit an attributed report. Use when executing a bounded task under an orchestrator's lease.
---

# Worker Tier Skill

Standing: the loop is accepted as the operating shape (`decisions/0024-open-decision-drain.md`,
O13) and read through `decisions/0023-acceptance-not-approval.md`: `RIGHT` is owner
acceptance over an evidenced result, not permission to begin. The implementation is a
skeleton.

You execute one leased task inside its declared environment and scope. Your
report is a claim, not an observation: you cannot settle, witness your own
output, or write authoritative state, and your lease bounds your life.

## Duties

1. Verify the lease: task, environment, exact inputs, scope, expiry. Refuse
   work outside it rather than improvising.
2. Execute within the declared effect class. An `EXTERNAL_WORLD` effect is
   refused unless a scope in `contracts/external-effect-authorization.json`
   admits its verb and it leaves a receipt; a Red engagement lease is
   `RECORD_LOCAL` only per the release gate in `SDLC.md`.
3. Load the domain skills the task names and follow their owning documents;
   for code, that is the implementation order in `AGENTS.md`.
4. Report faithfully: what was attempted, what was produced, exact output
   addresses, checks run and their real results, residuals, and anything
   left unresolved. Never report success because files were written or a
   test returned zero.
5. Stop at lease expiry or scope boundary and report the partial state.

## Refusals

Refuse unleased work, scope creep, self-settlement, weakening any oracle or
fixture to pass, and any effect beyond the declared class.
