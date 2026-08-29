export const meta = {
  name: 'sov-loop',
  description: 'One concern through control, orchestration, work, Blue verification, and the landing gate',
  whenToUse: 'The ordinary way to move one bounded concern from selected to a landed BUILT result. Independent witness is not launched per increment; named milestones queue verification-engagement separately under SDLC.md and decisions/0098. Use sov-qa or the milestone verification path when the next transition actually consumes independent observation.',
  phases: [
    { title: 'Select', detail: 'controller names the one concern and its scope' },
    { title: 'Plan', detail: 'orchestrator turns it into one bounded operation' },
    { title: 'Build', detail: 'worker executes it, runs expected tests, and reports the paths it changed' },
    { title: 'Land', detail: 'the landing gate requires Blue checks and grades the request against the standing grant' },
  ],
}

// args: { objective: string, domain?: string, target?: string, plan_only?: boolean }
//
// The gate, not this script, decides whether anything lands. A workflow cannot
// grant itself authority. Ordinary landing establishes a durable BUILT increment;
// it does not establish WITNESSED standing. Milestone witness is a separate queued
// operation under decisions/0098-milestone-witnessing.md.

const DOMAINS = ['governance', 'contracts', 'conformance', 'asset', 'proofing', 'console', 'projection', 'byom', 'verification']

const objective = args && args.objective ? args.objective : null
if (!objective) {
  return { error: 'sov-loop needs an objective; it selects nothing on its own' }
}
const domain = args && args.domain && DOMAINS.indexOf(args.domain) !== -1 ? args.domain : null
const target = args && args.target ? args.target : 'main'
const planOnly = !!(args && args.plan_only)

const CONCERN = {
  type: 'object',
  required: ['concern', 'domain', 'rationale', 'in_grant_scope', 'expected_paths'],
  properties: {
    concern: { type: 'string' },
    domain: { type: 'string' },
    rationale: { type: 'string' },
    in_grant_scope: { type: 'boolean' },
    out_of_scope_paths: { type: 'array', items: { type: 'string' } },
    expected_paths: { type: 'array', items: { type: 'string' } },
  },
}

const PLAN = {
  type: 'object',
  required: ['operation', 'files', 'effect_class', 'checks', 'defeating_case'],
  properties: {
    operation: { type: 'string' },
    files: { type: 'array', items: { type: 'string' } },
    effect_class: { type: 'string' },
    checks: { type: 'array', items: { type: 'string' } },
    defeating_case: { type: 'string' },
    blockers: { type: 'array', items: { type: 'string' } },
  },
}

const BUILD = {
  type: 'object',
  required: ['changed_paths', 'summary', 'checks_run', 'residuals'],
  properties: {
    changed_paths: { type: 'array', items: { type: 'string' } },
    summary: { type: 'string' },
    checks_run: { type: 'array', items: { type: 'object', required: ['command', 'exit_code'], properties: { command: { type: 'string' }, exit_code: { type: 'integer' } } } },
    residuals: { type: 'array', items: { type: 'string' } },
  },
}

const LAND = {
  type: 'object',
  required: ['exit_code', 'verdict', 'detail', 'command'],
  properties: {
    exit_code: { type: 'integer' },
    verdict: { type: 'string' },
    detail: { type: 'string' },
    command: { type: 'string' },
    commit: { type: 'string' },
  },
}

// Every agent this workflow spawns counts against the grant's budget, so the
// count is carried to the gate rather than estimated there.
let invocations = 0

phase('Select')
invocations += 1
const selected = await agent(
  'You hold the Control tier for one concern in Soveraeign. Objective: ' + objective + '. '
  + (domain ? 'Domain: ' + domain + '. ' : 'Pick the single owning domain from: ' + DOMAINS.join(', ') + '. ')
  + 'Read AGENTS.md and contracts/standing-grants.json. Name exactly one bounded concern that serves the objective. '
  + 'Then decide whether the whole concern falls inside the standing grant scope: the grant admits services/, contracts/, conformance/, scripts/, .claude/, adapters/, bindings/, workers/, diagrams/, and docs/, and excludes decisions/, lineage/, STATUS.yaml, .github/, and every root governing document. '
  + 'Set in_grant_scope false and list out_of_scope_paths if the concern would have to touch anything excluded - that concern is still worth doing, it just ends at an acceptance packet for Bdo instead of at a merge. '
  + 'Do not build anything. Return the concern, domain, rationale, in_grant_scope, out_of_scope_paths, and the paths you expect to change.',
  { agentType: 'sov-controller', schema: CONCERN, phase: 'Select', label: 'select' })

if (!selected) {
  return { error: 'controller returned no concern', objective: objective }
}
log('Concern: ' + selected.concern + ' (' + selected.domain + ')')
if (!selected.in_grant_scope) {
  log('Outside the standing grant: this concern ends at an acceptance packet, not a merge')
}

phase('Plan')
invocations += 1
const plan = await agent(
  'You hold the Orchestration tier. Turn this concern into exactly one bounded operation: ' + selected.concern + '. '
  + 'Read .claude/skills/sov-' + selected.domain + '/SKILL.md, then AGENTS.md, then the owning contract and fixture the skill names. '
  + 'Follow the implementation order in AGENTS.md: name the operation and owned lifecycle, then the contract and its positive and defeating case, then the smallest change. '
  + 'You plan only; you do not build, witness, or dispatch. Return the operation, the exact files, the effect class, the checks that must pass, the defeating case that must fail as declared, and any blockers. '
  + 'Do not insert an independent-witness step merely because the concern will reach BUILT. If the objective names a milestone or requests WITNESSED standing, record that as a separate verification-engagement boundary.',
  { agentType: 'sov-orchestrator', schema: PLAN, phase: 'Plan', label: 'plan:' + selected.domain })

if (!plan) {
  return { error: 'orchestrator returned no plan', concern: selected }
}
if (plan.blockers && plan.blockers.length > 0) {
  log('Planned with ' + plan.blockers.length + ' blocker(s) named')
}

phase('Build')
invocations += 1
const built = await agent(
  'You hold the Work tier for exactly one operation: ' + plan.operation + '. '
  + 'Files: ' + (plan.files || []).join(', ') + '. Effect class: ' + plan.effect_class + '. '
  + 'Read .claude/skills/sov-' + selected.domain + '/SKILL.md and AGENTS.md first. Write the defeating case (' + plan.defeating_case + ') and prove it fails as declared before you call the work done. '
  + 'Run python scripts/lint.py and python scripts/verify.py from the repository root and report their real exit codes; do not report a check you did not run. '
  + 'Do not commit, merge, push, or edit decisions/ or STATUS.yaml. Do not claim your own work is independently witnessed. '
  + 'Return every path you changed, a one-paragraph summary, the checks you ran with exit codes, and every residual you know about.',
  { agentType: 'sov-worker', schema: BUILD, phase: 'Build', label: 'build:' + selected.domain })

if (!built) {
  return { error: 'worker returned no report', concern: selected, plan: plan }
}
log('Built: ' + (built.changed_paths || []).length + ' path(s) changed')

phase('Land')
const mode = planOnly || !selected.in_grant_scope ? 'plan' : 'land'
if (mode === 'plan') {
  log('Rehearsing the gate only: ' + (planOnly ? 'plan_only was set' : 'concern is outside the grant'))
}

const pathArgs = (built.changed_paths || []).map(function (p) { return '--path ' + p }).join(' ')
invocations += 1
const landed = await agent(
  'Run the landing gate and report exactly what it said. You did not build this change and you do not decide whether it lands; the gate does. '
  + 'Ordinary landing establishes a durable BUILT increment. It does not establish WITNESSED standing and therefore needs no per-increment witness receipt under decisions/0098. '
  + 'Run this command from the repository root and nothing else that writes:\n\n'
  + '  python scripts/sov_land.py ' + mode + ' ' + pathArgs
  + ' --target ' + target
  + ' --spend ' + (invocations + 1)
  + ' --message "' + (selected.domain + ': ' + selected.concern).replace(/"/g, "'") + '"\n\n'
  + 'Report its real exit code and its output verbatim in the detail field. Do not retry it with different arguments, do not edit contracts/standing-grants.json, and do not commit or merge by hand if it refuses. A refusal is the correct outcome to report, not a problem to route around.',
  { agentType: 'sov-controller', schema: LAND, phase: 'Land', label: 'land' })

const gate = landed || { exit_code: null, verdict: 'UNKNOWN', detail: 'the gate agent returned nothing', command: 'python scripts/sov_land.py ' + mode }

const residuals = [].concat(built.residuals || [])
const judgementQueue = []
if (!selected.in_grant_scope) {
  judgementQueue.push('Acceptance: ' + selected.concern + ' touches ' + (selected.out_of_scope_paths || []).join(', ') + ', which the standing grant excludes.')
}
if (gate.exit_code !== 0) {
  judgementQueue.push('The gate refused: ' + gate.detail)
}

return {
  workflow: 'sov-loop',
  objective: objective,
  concern: selected,
  plan: plan,
  build: { summary: built.summary, changed_paths: built.changed_paths, checks_run: built.checks_run },
  witness: { status: 'DEFERRED_TO_NAMED_MILESTONE', required_for_this_landing: false },
  gate: gate,
  mode: mode,
  agent_invocations: invocations,
  residuals: residuals,
  judgement_queue: judgementQueue,
  standing: gate.exit_code === 0 ? 'LANDED_BUILT_NOT_WITNESSED' : 'HELD_AT_THE_GATE',
}
