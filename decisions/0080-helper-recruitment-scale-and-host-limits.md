# 0080 · A helper is free; a fleet is a commitment; a withheld tool is neither

Status: `PROPOSED · BDO HAS NOT RULED`
Date: 2026-08-26
Supersedes: nothing. Adds a scale boundary to `helper_policy` in
`contracts/closure-ownership.json` and a rule for host-withheld capabilities.

## What was found

A Sov agent told Bdo: "That needs a subagent, and I'm set not to launch one unless you
ask." Three files already said the opposite. `AGENTS.md`, Closure ownership, says to
recruit a helper "whenever a second reading would help, and do it without asking".
`contracts/closure-ownership.json` sets `helper_policy.may_recruit_without_asking: true`
and makes `HELPER_NOT_RECRUITED` a refusal. `contracts/acceptance-policy.json` places
`RESOURCE_CONSUMPTION` under `presumptive_execution`, where stopping to ask is refused as
`PREAPPROVAL_REQUESTED`. The agent's own definition, `.claude/agents/sov.md`, declares no
tool restriction, so it held the capability and declined it.

The sentence came from the host. `Do not call the AgentTool unless the user requested it`
was in that session's system prompt and in none of `.claude/settings.json`,
`~/.claude/settings.json`, `~/.claude.json`, or any file in this repository. It is a host
default for how the session was launched.

Two gaps let it win. First, nothing in the contract said how much recruitment is
presumptive, so "recruit freely" and "a resource commitment is owner-held" both read onto
the same act and a caller could pick either. Second, nothing said what to do when a host
withholds a tool the contract expects, so the agent reported a host default as a rule of
this system and turned a missing capability into a permission question for Bdo.

## Ruling proposed

1. Recruiting a helper is `RESOURCE_CONSUMPTION` and presumptive up to eight helper
   invocations per concern. Below the ceiling no one is asked.
2. Above the ceiling the same act is `RESOURCE_COMMITMENT`, an admissible owner hold, and
   it is asked at `EFFECT_SEAM` before it is spent. Spending past the ceiling and
   presenting it as ordinary closure is refused as `RECRUITMENT_UNBOUNDED`.
3. A host that does not grant the helper tool has withheld a capability, not made a rule.
   The participant names the tool and the host, does the reading in-session, and asks for
   the tool as a `capability` at `DEPENDENCY_SEAM`. Routing that ask to the owner as
   judgement is refused as `HOST_LIMIT_AS_OWNER_QUESTION`.

## Defaults taken

- **Eight, per concern, counted in invocations.** A second reading is one to three agents;
  the federation run measured at roughly 1.8M subagent tokens is dozens. Eight sits above
  ordinary helper use and below any fleet. It is a guess with a stated defeater, not a
  measurement.
- **Invocations, not tokens.** Invocations are countable from a claim without a meter.
  Tokens are the truer unit and are not available to the evaluator today.
- **`capability_requested` narrows rule 3.** A first draft fired on any owner question
  from a host-limited participant, which would have refused legitimate acceptance packets.
  The rule now fires only when the handoff is asking for the helper tool itself; a
  regression test holds that boundary.

## What would defeat this ruling

Measured helper counts. If concerns routinely need more than eight helper invocations to
reach a landed result, the ceiling is set below the work and is wrong. If one under-ceiling
recruitment is ever itself a metered spend Bdo would have refused, the unit is wrong and
should be tokens.

## What this does not fix

The host instruction itself. It is outside this repository, so no contract here can lift
it; a session launched with the tool withheld still cannot recruit. What changed is that
such a session must now report that honestly instead of presenting it as policy.

## Residual

`decisions/0075` proposes that a grant should not write the files that bound it and names
`contracts/closure-ownership.json` as one of them. This change edits that file. It was not
landed under `grant:standing-landing-loop`; it is presented to Bdo directly. If 0075 is
ruled, the route by which a refusal is added to that file needs settling.
