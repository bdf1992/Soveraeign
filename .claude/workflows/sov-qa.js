export const meta = {
  name: 'sov-qa',
  description: 'Independent QA sweep: sov-witness agents verify the current working tree per domain without building anything',
  whenToUse: 'After build work (workflow or ad hoc) or before review: witnesses the current state of each selected domain, runs the verification harness, and aggregates residuals and judgement items. Read-only with respect to the repository.',
  phases: [
    { title: 'Witness', detail: 'one independent witness per selected domain' },
    { title: 'Aggregate', detail: 'merge observations, residuals, and judgement items' },
  ],
}

// args: { domains?: string[], focus?: string }

const KNOWN = ['governance', 'contracts', 'conformance', 'asset', 'proofing', 'console', 'byom', 'verification']

const OBS_SCHEMA = {
  type: 'object',
  required: ['domain', 'checks', 'observations', 'residuals', 'judgement_items'],
  properties: {
    domain: { type: 'string' },
    checks: { type: 'array', items: { type: 'object', required: ['command', 'exit_code'], properties: { command: { type: 'string' }, exit_code: { type: 'integer' } } } },
    observations: { type: 'array', items: { type: 'string' } },
    residuals: { type: 'array', items: { type: 'string' } },
    judgement_items: { type: 'array', items: { type: 'string' } },
  },
}

const requested = args && Array.isArray(args.domains) && args.domains.length > 0 ? args.domains : KNOWN
const selected = requested.filter(function (d) { return KNOWN.indexOf(d) !== -1 })
const focus = args && args.focus ? args.focus : 'the current working tree, uncommitted changes first'

if (selected.length === 0) {
  return { error: 'no known domains selected', known: KNOWN }
}

phase('Witness')
log('QA: witnessing ' + selected.length + ' domain(s) - read-only, no building')

function qaPrompt(d) {
  return 'You are performing an independent QA observation of the Soveraeign ' + d + ' domain. Focus: ' + focus + '. '
    + 'First read .claude/skills/sov-' + d + '/SKILL.md for the domain scope, key files, blockers, and verification commands, then read AGENTS.md. '
    + 'Inspect the domain: git status and git diff for its files, current content against its owning contracts and CLASSIFICATION.md/SPEC.md vocabulary, and run the verification commands the skill names (always python scripts/verify.py from the repository root), observing real exit codes yourself. '
    + 'You must not edit, fix, build, commit, or push anything - observe and report only. A green build alone is not authority; a builder self-report is not evidence. '
    + 'Return: domain, checks (command and exit code), observations (what you independently confirmed), residuals (defects, gaps, drift), and judgement_items (questions only Bdo can decide).'
}

const results = await parallel(selected.map(function (d) {
  return function () { return agent(qaPrompt(d), { agentType: 'sov-witness', schema: OBS_SCHEMA, phase: 'Witness', label: 'qa:' + d }) }
}))

phase('Aggregate')

const domains = {}
const residuals = []
const judgementQueue = []

selected.forEach(function (d, i) {
  const r = results[i]
  if (!r) {
    domains[d] = { error: 'witness returned no observation' }
    residuals.push(d + ': witness returned no observation; domain state unattested')
    return
  }
  domains[d] = r
  r.residuals.forEach(function (x) { residuals.push(d + ': ' + x) })
  r.judgement_items.forEach(function (q) { judgementQueue.push(d + ': ' + q) })
})

log('QA complete: ' + residuals.length + ' residual(s), ' + judgementQueue.length + ' judgement item(s) for Bdo')

return {
  focus: focus,
  witnessed: selected,
  domains: domains,
  residuals: residuals,
  judgement_queue: judgementQueue,
}
