---
name: sov-scribe
description: Cross-cutting writing capability for Soveraeign - turn a templated request into a system prompt, agent definition, skill, workflow prompt, decision-record draft, or governed document. Load on "sov-scribe", "write a prompt", "system prompt", "prompting", "self-prompting", "prompt template", "draft a document", "agent definition", or when any harness or governing artifact needs authoring from a request. Not a repo domain - it rides the stable roles (sov-orchestrator frames, sov-worker drafts, sov-witness critiques) and owns no repository files.
---

# sov-scribe

## Purpose

Turn a request into a finished written artifact - a prompt or a document -
grounded in named sources, checked by an independent reader. Writing follows
the same discipline as building: a draft cannot critique itself, invented
facts are defects, and vocabulary is not negotiable.

## Request template (the input contract)

A scribe request names:

- `artifact`: system-prompt | agent-definition | skill | workflow-prompt |
  decision-record | document
- `audience`: who reads or executes it (human, model role, harness)
- `objective`: the one job the artifact must do, in one sentence
- `sources`: repo paths the content must be grounded in - read them, never
  invent around them
- `constraints`: hard rules the artifact must obey or restate (vocabulary,
  blockers, boundaries, length)
- `output_path`: where the draft lands (default: `.claude/drafts/<slug>.md`)
- `register`: contract | instruction | narrative

A missing field that would force invention is a gap: queue the question, do
not guess silently. A missing field with an obvious default gets the default,
named in the report.

## System-prompt anatomy (house pattern)

1. Identity and root: role name, one-sentence mission, repository-root
   convention (the working directory; never a local absolute path).
2. Know-how load: which skill or files to read first.
3. Hard rules: the non-negotiables, each traceable to `AGENTS.md` or a domain
   skill - link to the owning document, never fork its wording.
4. Procedure: numbered, bounded, observable steps.
5. Report format: named fields, standing ceiling, judgement queue.

Anti-patterns: authority claims (an artifact grants no rights by existing);
vague verbs (handle, manage, ensure); duplicated rules that will drift from
their owning document; synonyms for `CLASSIFICATION.md` terms; unbounded
scope ("and anything else needed").

## Document anatomy (house pattern)

Status or frontmatter line first; purpose in two or three sentences; owned
scope and explicit not-owned; body sections matching the sibling documents of
its type (`decisions/` records use: title, Status backtick line, Decision,
Consequences, Source and authority). Match sibling voice; UTF-8, LF, final
newline; ~100-character lines; no local absolute paths, secrets, or credential
shapes.

## Self-prompting loop

Draft and critique are different agents - a draft cannot witness itself:

1. Frame (sov-orchestrator): normalize the request against the template;
   gaps become questions; propose defaults where safe.
2. Draft (sov-worker): read every named source, write the artifact to
   `output_path` following the matching anatomy.
3. Critique (sov-witness): check the draft against each request field and the
   anti-pattern list; verdict per requirement: reproduced, dissented, or
   unattestable; edit nothing.
4. Revise once on dissent (sov-worker, given only the critique residuals);
   remaining dissent stays in the report as residuals or queues for Bdo.

## Vocabulary

Soveraeign-facing artifacts use `CLASSIFICATION.md` and `SPEC.md` terms
exactly. Keep the two lifecycles distinct: artifact standing
`OPEN -> BUILT -> WITNESSED -> RATIFIED` versus record standing
`RECORDED -> ADMITTED -> RATIFIED -> EFFECTIVE`. Effect classes are
`RECORD_LOCAL`, `RESOURCE_CONSUMPTION`, `EXTERNAL_WORLD` (the last is
forbidden in Phase I).

## Verification

- `python scripts/verify.py` from the repository root (repository hygiene
  scans committed-shape text, including `.claude/*.md`).
- `python scripts/lint.py` for secret shapes and module size.
- For decision-record drafts: section structure matches `decisions/0012`.

## Report format

- artifact: output path and type
- request: fields satisfied, defaults applied, gaps queued
- critique: verdict per requirement; revision applied or not
- residuals; judgement items for Bdo
- standing proposal: at most `OPEN -> BUILT`; a critique is a reading, not a
  witness of repository standing
