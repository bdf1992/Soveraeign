export const meta = {
  name: 'sov-scribe',
  description: 'Turn a templated writing request into a drafted, independently critiqued prompt or document',
  whenToUse: 'When a system prompt, agent definition, skill, workflow prompt, decision-record draft, or governed document needs authoring from a request. Cross-cutting capability, not a repo domain: Frame runs sov-orchestrator, Draft runs sov-worker, Critique runs sov-witness.',
  phases: [
    { title: 'Frame', detail: 'normalize the request against the sov-scribe template' },
    { title: 'Draft', detail: 'write the artifact grounded in the named sources' },
    { title: 'Critique', detail: 'independent per-requirement review; one revision on dissent' },
  ],
}

// args: { request: string|object, output_path?: string }

const FRAME_SCHEMA = {
  type: 'object',
  required: ['blocked', 'normalized', 'gaps', 'judgement_queue'],
  properties: {
    blocked: { type: 'boolean' },
    blocked_reason: { type: 'string' },
    normalized: {
      type: 'object',
      required: ['artifact', 'audience', 'objective', 'sources', 'constraints', 'output_path', 'register'],
      properties: {
        artifact: { type: 'string', enum: ['system-prompt', 'agent-definition', 'skill', 'workflow-prompt', 'decision-record', 'document'] },
        audience: { type: 'string' },
        objective: { type: 'string' },
        sources: { type: 'array', items: { type: 'string' } },
        constraints: { type: 'array', items: { type: 'string' } },
        output_path: { type: 'string' },
        register: { type: 'string', enum: ['contract', 'instruction', 'narrative'] },
      },
    },
    defaults_applied: { type: 'array', items: { type: 'string' } },
    gaps: { type: 'array', items: { type: 'string' } },
    judgement_queue: { type: 'array', items: { type: 'string' } },
  },
}

const DRAFT_SCHEMA = {
  type: 'object',
  required: ['output_path', 'summary', 'sources_read'],
  properties: {
    output_path: { type: 'string' },
    summary: { type: 'string' },
    sources_read: { type: 'array', items: { type: 'string' } },
    constraints_applied: { type: 'array', items: { type: 'string' } },
  },
}

const CRITIQUE_SCHEMA = {
  type: 'object',
  required: ['verdicts', 'residuals', 'revise'],
  properties: {
    verdicts: {
      type: 'array',
      items: {
        type: 'object',
        required: ['requirement', 'verdict'],
        properties: {
          requirement: { type: 'string' },
          verdict: { type: 'string', enum: ['reproduced', 'dissented', 'unattestable'] },
        },
      },
    },
    residuals: { type: 'array', items: { type: 'string' } },
    revise: { type: 'boolean' },
  },
}

const rawRequest = args && args.request ? args.request : null
if (!rawRequest) {
  return { domain: 'scribe', blocked: true, judgement_queue: ['no request was provided; a scribe run needs a request (see .claude/skills/sov-scribe/SKILL.md request template)'] }
}
const requestText = typeof rawRequest === 'string' ? rawRequest : JSON.stringify(rawRequest)
const pathOverride = args && args.output_path ? args.output_path : null

phase('Frame')
log('Frame: normalizing the writing request')

const framePrompt = 'Read .claude/skills/sov-scribe/SKILL.md, then normalize this writing request against its request template. Request: ' + requestText + '. '
  + (pathOverride ? 'The caller fixed output_path to: ' + pathOverride + '. ' : '')
  + 'Fill every template field. Apply safe defaults (name them in defaults_applied); a field that would force invention is a gap - put the question in gaps and, when only Bdo can answer it, in judgement_queue. '
  + 'Set blocked true only when drafting cannot proceed honestly without the missing answers; a missing owner answer that only gates ratification is a default to take and name, not a block.'

const frame = await agent(framePrompt, { agentType: 'sov-orchestrator', schema: FRAME_SCHEMA, phase: 'Frame', label: 'frame' })

if (!frame || frame.blocked) {
  log('Frame: blocked; returning gaps without drafting')
  return { domain: 'scribe', blocked: true, request: frame ? frame.normalized : null, residuals: frame && frame.blocked_reason ? [frame.blocked_reason] : [], gaps: frame ? frame.gaps : [], judgement_queue: frame ? frame.judgement_queue : ['frame agent returned no normalization'], standing_proposal: null }
}

const spec = frame.normalized
if (pathOverride) { spec.output_path = pathOverride }

phase('Draft')
log('Draft: writing ' + spec.artifact + ' to ' + spec.output_path)

const draftPrompt = 'Read .claude/skills/sov-scribe/SKILL.md and follow its anatomy for artifact type ' + spec.artifact + '. '
  + 'Write the artifact to ' + spec.output_path + ' (UTF-8, LF, final newline). Normalized request: ' + JSON.stringify(spec) + '. '
  + 'Read every listed source before writing; ground every claim in a source and never invent facts around them. '
  + 'Soveraeign-facing artifacts use CLASSIFICATION.md and SPEC.md vocabulary exactly, no local absolute paths, no secrets. '
  + 'Never run git commit or git push. Your draft is a builder product: it cannot critique itself.'

const draft = await agent(draftPrompt, { agentType: 'sov-worker', schema: DRAFT_SCHEMA, phase: 'Draft', label: 'draft' })

if (!draft) {
  return { domain: 'scribe', blocked: false, request: spec, artifact: null, residuals: ['draft agent returned no report; nothing was written or the write is unattested'], gaps: frame.gaps, judgement_queue: frame.judgement_queue, standing_proposal: null }
}

phase('Critique')

function critiquePrompt(spec2, note) {
  return 'Read .claude/skills/sov-scribe/SKILL.md (anatomy and anti-patterns), then independently critique the draft at ' + spec2.output_path + '. '
    + (note ? note + ' ' : '')
    + 'Normalized request it must satisfy: ' + JSON.stringify(spec2) + '. '
    + 'You did not write this draft and must not edit it - a draft cannot critique itself. '
    + 'For each request field and each constraint return a verdict: reproduced (the draft satisfies it, confirmed by reading), dissented (it does not, with the defect as a residual), or unattestable. '
    + 'Also check the anti-pattern list and vocabulary rules. Set revise true when one focused revision pass could clear the dissents.'
}

let critique = await agent(critiquePrompt(spec, null), { agentType: 'sov-witness', schema: CRITIQUE_SCHEMA, phase: 'Critique', label: 'critique' })
let revised = false

if (critique && critique.revise) {
  log('Critique: dissent; one revision pass')
  const revisePrompt = 'Read .claude/skills/sov-scribe/SKILL.md, then revise the draft at ' + spec.output_path + ' to clear exactly these critique residuals and nothing else: '
    + JSON.stringify(critique.residuals) + '. Normalized request: ' + JSON.stringify(spec) + '. Smallest change that clears each residual; never run git commit or git push.'
  const revision = await agent(revisePrompt, { agentType: 'sov-worker', schema: DRAFT_SCHEMA, phase: 'Critique', label: 'revise' })
  revised = !!revision
  critique = await agent(critiquePrompt(spec, 'This is the second critique, after one revision pass.'), { agentType: 'sov-witness', schema: CRITIQUE_SCHEMA, phase: 'Critique', label: 'critique-2' })
}

const residuals = critique && critique.residuals ? critique.residuals.slice() : ['critique agent returned no verdicts; the draft is unreviewed']
const allReproduced = !!(critique && critique.verdicts && critique.verdicts.length > 0 && critique.verdicts.every(function (v) { return v.verdict === 'reproduced' }))

log('Done: ' + (allReproduced ? 'all requirements reproduced' : residuals.length + ' residual(s)') + (revised ? ' after one revision' : ''))

return {
  domain: 'scribe',
  blocked: false,
  request: spec,
  artifact: { path: spec.output_path, type: spec.artifact, summary: draft.summary },
  critique: critique,
  revised: revised,
  residuals: residuals,
  gaps: frame.gaps,
  judgement_queue: frame.judgement_queue,
  standing_proposal: allReproduced ? 'OPEN->BUILT' : null,
}
