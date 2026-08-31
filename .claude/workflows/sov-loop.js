export const meta = {
  name: 'sov-loop',
  description: 'One concern through control, orchestration, work, independent witness, and the landing gate',
  whenToUse: 'The ordinary way to move one bounded concern from selected to landed. Every other workflow in this repository stops at an uncommitted tree and a queue pointed at Bdo; this one ends at the landing gate, which either commits and merges under contracts/standing-grants.json or refuses with the reason. Use sov-federation for multi-domain sweeps and sov-qa to observe without building.',
  phases: [
    { title: 'Select', detail: 'controller names the one concern and its scope' },
    { title: 'Plan', detail: 'orchestrator turns it into one bounded operation' },
    { title: 'Build', detail: 'worker executes it and reports the paths it changed' },
    { title: 'Orchestrator Review', detail: 'evidence mode forms a frozen participant-in-work Finding' },
    { title: 'Witness Review', detail: 'independent evidence mode forms a frozen WORK Finding' },
    { title: 'Compare', detail: 'controller compares frozen cited Findings without ratifying them' },
    { title: 'Land', detail: 'the landing gate grades the request against the standing grant' },
  ],
}

// args: { objective: string, domain?: string, target?: string, plan_only?: boolean, evidence_mode?: boolean }
//
// The gate, not this script, is what decides whether anything lands. A workflow
// cannot grant itself authority, so every phase here is evidence-gathering and
// the last step hands that evidence to scripts/sov_land.py to be refused or not.

const DOMAINS = ['governance', 'contracts', 'conformance', 'asset', 'proofing', 'console', 'projection', 'byom', 'verification']

const objective = args && args.objective ? args.objective : null
if (!objective) {
  return { error: 'sov-loop needs an objective; it selects nothing on its own' }
}
const domain = args && args.domain && DOMAINS.indexOf(args.domain) !== -1 ? args.domain : null
const target = args && args.target ? args.target : 'main'
const planOnly = !!(args && args.plan_only)
const evidenceMode = !!(args && args.evidence_mode)

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

const WITNESS = {
  type: 'object',
  required: ['verdict', 'observations', 'residuals', 'observation_file'],
  properties: {
    verdict: { type: 'string' },
    observations: { type: 'array', items: { type: 'string' } },
    residuals: { type: 'array', items: { type: 'string' } },
    observation_file: { type: 'string' },
    judgement_items: { type: 'array', items: { type: 'string' } },
  },
}

// Harness projections of contracts/finding.schema.json. The shared contract owns
// the semantics; this compact shape only carries what this workflow must route.
const FROZEN_FINDING = {
  type: 'object',
  required: ['finding_id', 'subject_kind', 'subject_address', 'record_projection_id',
             'projection_as_of', 'verdict', 'evidence_addresses', 'frozen_at', 'detail'],
  properties: {
    finding_id: { type: 'string' },
    subject_kind: { type: 'string' },
    subject_address: { type: 'string' },
    record_projection_id: { type: 'string' },
    projection_as_of: { type: 'string' },
    verdict: { type: 'string' },
    evidence_addresses: { type: 'array', items: { type: 'string' } },
    frozen_at: { type: 'string' },
    detail: { type: 'string' },
  },
}

const COMPARISON = {
  type: 'object',
  required: ['classifications', 'detail'],
  properties: {
    classifications: { type: 'array', items: { type: 'string' } },
    detail: { type: 'string' },
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
  + 'Then decide whether the whole concern falls inside the standing grant scope: the grant admits services/, contracts/, conformance/, scripts/, .claude/, adapters/, bindings/, workers/, and diagrams/, and excludes decisions/, lineage/, STATUS.yaml, and every root governing document. '
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
  + 'You plan only; you do not build, witness, or dispatch. Return the operation, the exact files, the effect class, the checks that must pass, the defeating case that must fail as declared, and any blockers.',
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
  + 'Do not commit, merge, push, or edit decisions/ or STATUS.yaml. Do not witness your own work. '
  + 'Return every path you changed, a one-paragraph summary, the checks you ran with exit codes, and every residual you know about.',
  { agentType: 'sov-worker', schema: BUILD, phase: 'Build', label: 'build:' + selected.domain })

if (!built) {
  return { error: 'worker returned no report', concern: selected, plan: plan }
}
log('Built: ' + (built.changed_paths || []).length + ' path(s) changed')

let orchestrationFinding = null
if (evidenceMode) {
  phase('Orchestrator Review')
  invocations += 1
  orchestrationFinding = await agent(
    'You are in REVIEW mode, not PLAN mode. Judge PARTICIPANT_IN_WORK for the bounded assignment ' + plan.operation + '. ' +
    'Use contracts/record-projection.schema.json and contracts/finding.schema.json. Reconstruct a scoped RecordProjection through the Record service for the assignment/work subject and your evaluator relation. ' +
    'Judge assignment, authority, scope, repair, disclosure, and terminal fidelity only; do not judge implementation correctness. ' +
    'Do not read or anticipate the Witness conclusion. Cite only addresses in the projection. If the needed Record evidence does not exist, return verdict UNATTESTABLE with record_projection_id NONE and explain the Record defect; never fill it from the worker report. ' +
    'Freeze the Finding before returning it. Return finding_id, subject_kind PARTICIPANT_IN_WORK, subject_address, record_projection_id, projection_as_of, verdict, evidence_addresses, frozen_at, and detail.',
    { agentType: 'sov-orchestrator', schema: FROZEN_FINDING, phase: 'Orchestrator Review', label: 'review:' + selected.domain })
  if (!orchestrationFinding || !orchestrationFinding.frozen_at) {
    return { error: 'orchestrator review did not return a frozen Finding', concern: selected, build: built }
  }
}

let witnessed = null
if (evidenceMode) {
  phase('Witness Review')
  invocations += 1
  const cutoff = orchestrationFinding ? orchestrationFinding.projection_as_of : 'NONE'
  witnessed = await agent(
    'You are the independent evaluator of WORK. Concern: ' + selected.concern + '. Operation: ' + plan.operation + '. ' +
    'Use contracts/record-projection.schema.json and contracts/finding.schema.json. Inspect the exact repository state and governing contract/fixtures yourself. ' +
    'Reconstruct a WORK RecordProjection at this shared cutoff if available: ' + cutoff + '. The cutoff is projection metadata, not an evaluator conclusion. ' +
    'Do not read the worker conclusion, Orchestrator Finding, or Controller expectation before freezing your own Finding. Builder paths may locate the work but are not evidence. ' +
    'Cite only addresses present in your projection. If the projection/evidence is missing or cannot be reconstructed, return UNATTESTABLE rather than substituting prose. ' +
    'Freeze before returning. Return finding_id, subject_kind WORK, subject_address, record_projection_id, projection_as_of, verdict, evidence_addresses, frozen_at, and detail.',
    { agentType: 'sov-witness', schema: FROZEN_FINDING, phase: 'Witness Review', label: 'witness-review:' + selected.domain })
} else {
  phase('Witness')
  invocations += 1
  witnessed = await agent(
    'You are the independent observation for work you did not do and must not touch. Concern: ' + selected.concern + '. ' +
    'The builder reports it changed: ' + (built.changed_paths || []).join(', ') + '. Treat that as a claim, not evidence. ' +
    'Read git status and git diff yourself, read the owning contract and the defeating fixture, and run python scripts/verify.py and python scripts/lint.py observing the real exit codes. ' +
    'Confirm the defeating case actually fails as declared; a fixture that passes when it should fail is a DISSENTED verdict, not a residual. ' +
    'Then write your observation to reports/observations/ as JSON with exactly these fields: observer_id (your agent label), contributed_to_build (false - and if that is not true, say so and set verdict DISSENTED), verdict (CONFIRMED or DISSENTED), concern, and checks. ' +
    'You must not edit, fix, build, or commit anything outside that one observation file. ' +
    'Return the verdict, what you independently confirmed, residuals, the path you wrote the observation to, and any judgement items only Bdo can settle.',
    { agentType: 'sov-witness', schema: WITNESS, phase: 'Witness', label: 'witness:' + selected.domain })
}

if (!witnessed) {
  return { error: 'witness returned no observation; nothing may land unwitnessed', concern: selected, build: built }
}
log('Witness: ' + witnessed.verdict)

let comparison = null
if (evidenceMode) {
  if (!witnessed.frozen_at) {
    return { error: 'witness review did not return a frozen Finding', concern: selected }
  }
  phase('Compare')
  invocations += 1
  comparison = await agent(
    'Compare these two already-frozen Findings. You do not witness, ratify, or average them. Preserve both subjects and citations. ' +
    'Participant-in-work Finding: ' + JSON.stringify(orchestrationFinding) + '. WORK Finding: ' + JSON.stringify(witnessed) + '. ' +
    'Use only these classifications: NO_CONFLICT, EVIDENCE_DIFFERENCE, INTERPRETATION_DIFFERENCE, WORK_DEFECT, WORKER_DEFECT, ORCHESTRATION_DEFECT, WITNESS_DEFECT, RECORD_DEFECT, POLICY_SEAM. ' +
    'A missing/unreconstructable projection or citation is RECORD_DEFECT; an actually undefined governing choice is POLICY_SEAM. ' +
    'Return classifications and a concise evidence-based detail. Do not create standing.',
    { agentType: 'sov-controller', schema: COMPARISON, phase: 'Compare', label: 'compare:' + selected.domain })
}

phase('Land')
const comparisonBlocks = evidenceMode && (!comparison ||
  (comparison.classifications || []).length !== 1 ||
  comparison.classifications[0] !== 'NO_CONFLICT')
const mode = planOnly || !selected.in_grant_scope || witnessed.verdict !== 'CONFIRMED' || comparisonBlocks ? 'plan' : 'land'
if (mode === 'plan') {
  log('Rehearsing the gate only: ' + (planOnly ? 'plan_only was set' : (!selected.in_grant_scope ? 'concern is outside the grant' : (comparisonBlocks ? 'evidence comparison is not a single NO_CONFLICT' : 'witness verdict is ' + witnessed.verdict))))
}

const pathArgs = (built.changed_paths || []).map(function (p) { return '--path ' + p }).join(' ')
invocations += 1
const landed = await agent(
  'Run the landing gate and report exactly what it said. You did not build this change and you do not decide whether it lands; the gate does. '
  + 'Run this command from the repository root and nothing else that writes:\n\n'
  + '  python scripts/sov_land.py ' + mode + ' ' + pathArgs
  + ' --observation ' + (witnessed.observation_file || 'MISSING')
  + ' --target ' + target
  + ' --spend ' + (invocations + 1)
  + ' --message "' + (selected.domain + ': ' + selected.concern).replace(/"/g, "'") + '"\n\n'
  + 'Report its real exit code and its output verbatim in the detail field. Do not retry it with different arguments, do not edit contracts/standing-grants.json, and do not commit or merge by hand if it refuses. A refusal is the correct outcome to report, not a problem to route around.',
  { agentType: 'sov-controller', schema: LAND, phase: 'Land', label: 'land' })

const gate = landed || { exit_code: null, verdict: 'UNKNOWN', detail: 'the gate agent returned nothing', command: 'python scripts/sov_land.py ' + mode }

const residuals = [].concat(built.residuals || [], witnessed.residuals || [])
const judgementQueue = [].concat(witnessed.judgement_items || [])
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
  witness: evidenceMode ? witnessed : { verdict: witnessed.verdict, observations: witnessed.observations, observation_file: witnessed.observation_file },
  orchestration_finding: orchestrationFinding,
  comparison: comparison,
  evidence_mode: evidenceMode,
  gate: gate,
  mode: mode,
  agent_invocations: invocations,
  residuals: residuals,
  judgement_queue: judgementQueue,
  standing: gate.exit_code === 0 ? 'LANDED_BUILT_AND_WITNESSED_NOT_RATIFIED' : 'HELD_AT_THE_GATE',
}
