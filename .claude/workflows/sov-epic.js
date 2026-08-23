export const meta = {
  name: 'sov-epic',
  description: 'Walk the epic-of-epics issue tree from its checked-in projection: reconcile it against its contracts, then select the next bounded operation per village',
  whenToUse: 'When the objective is the whole system of villages rather than one domain - a standing walk of issue #1, unattended or interactive. For domain-shaped work run sov-<domain>; to advance several domains at once run sov-federation.',
  phases: [
    { title: 'Reconcile', detail: 'independently observe the projection against its contracts' },
    { title: 'Select', detail: 'one orchestrator per village with reachable work' },
    { title: 'Advance', detail: 'build one bounded operation (only when advance is set)' },
    { title: 'Witness', detail: 'independently verify what Advance changed' },
  ],
}

// args: { advance?: boolean, villages?: string[], max_operations?: number, objective?: string }
// Read-only unless advance is true. This workflow never calls workflow():
// sov-federation is the only workflow allowed to nest.

const VILLAGES = [
  'ground-and-evidence',
  'trust-and-control',
  'reach-and-motion',
  'domain-and-qualification',
]

const CHECKS = { type: 'array', items: { type: 'object', required: ['command', 'exit_code'], properties: { command: { type: 'string' }, exit_code: { type: 'integer' } } } }
const STRINGS = { type: 'array', items: { type: 'string' } }

const RECON_SCHEMA = {
  type: 'object',
  required: ['checks', 'counts', 'confirmed_defects', 'observations', 'residuals', 'judgement_items'],
  properties: {
    checks: CHECKS,
    counts: { type: 'object' },
    confirmed_defects: STRINGS,
    observations: STRINGS,
    residuals: STRINGS,
    judgement_items: STRINGS,
  },
}

const PLAN_SCHEMA = {
  type: 'object',
  required: ['village', 'operation', 'issue', 'domain', 'blocked_by', 'rationale', 'judgement_items'],
  properties: {
    village: { type: 'string' },
    operation: { type: 'string' },
    issue: { type: 'string' },
    domain: { type: 'string' },
    blocked_by: STRINGS,
    rationale: { type: 'string' },
    files: STRINGS,
    effect_class: { type: 'string' },
    judgement_items: STRINGS,
  },
}

const BUILD_SCHEMA = {
  type: 'object',
  required: ['issue', 'domain', 'changed', 'checks', 'standing_proposal', 'residuals'],
  properties: {
    issue: { type: 'string' },
    domain: { type: 'string' },
    changed: STRINGS,
    checks: CHECKS,
    standing_proposal: { type: 'string' },
    residuals: STRINGS,
  },
}

const WITNESS_SCHEMA = {
  type: 'object',
  required: ['issue', 'verdict', 'checks', 'observations', 'dissent'],
  properties: {
    issue: { type: 'string' },
    verdict: { type: 'string' },
    checks: CHECKS,
    observations: STRINGS,
    dissent: STRINGS,
  },
}

const advance = !!(args && args.advance)
const requested = args && Array.isArray(args.villages) && args.villages.length > 0 ? args.villages : VILLAGES
const selectedVillages = requested.filter(function (v) { return VILLAGES.indexOf(v) !== -1 })
const rejected = requested.filter(function (v) { return VILLAGES.indexOf(v) === -1 })
const maxOperations = args && args.max_operations ? args.max_operations : 1
const objective = args && args.objective
  ? args.objective
  : 'advance the epic-of-epics tree by the smallest legal operation available now'

if (rejected.length > 0) {
  log('Unknown villages ignored: ' + rejected.join(', '))
}
if (selectedVillages.length === 0) {
  return { error: 'no known villages selected', known: VILLAGES, rejected: rejected }
}

phase('Reconcile')
log('Reconciling the projected epic tree' + (advance ? ' (advance mode)' : ' (observe only)'))

const recon = await agent(
  'You are independently reconciling the Soveraeign epic-of-epics issue tree against its own contracts. '
  + 'Read .claude/epic/README.md, then AGENTS.md and the Issue coordination contract section of CONTRIBUTING.md. '
  + 'Run these from the repository root, observing the real exit codes yourself: `python scripts/sov_epic.py validate` and `python scripts/sov_epic.py report`. '
  + 'The projection under .claude/epic/tree.json is a derived and possibly stale view - check its synced_at field and say so if it is old. '
  + 'Independently confirm a sample of at least five reported defects by reading the projected metadata block of the named issue in tree.json against contracts/issue-metadata.schema.json, .github/labels.yml, and CONTRIBUTING.md. Report any defect you could NOT confirm as a residual against the checker, not against the issue. '
  + 'You must not edit, fix, sync, commit, or push anything. '
  + 'Return: checks (command and exit code), counts (from the report), confirmed_defects, observations, residuals, and judgement_items (questions only Bdo can decide).',
  { agentType: 'sov-witness', schema: RECON_SCHEMA, phase: 'Reconcile', label: 'reconcile:tree' }
)

if (!recon) {
  return { error: 'reconciliation returned no observation; the tree state is unattested' }
}

phase('Select')
log('Selecting the next bounded operation across ' + selectedVillages.length + ' village(s)')

function planPrompt(v) {
  return 'You are planning the next bounded operation for the Soveraeign village "' + v + '" of the epic-of-epics tree (issue #1). Objective: ' + objective + '. '
    + 'Read .claude/epic/README.md and .claude/epic/villages.json, then run `python scripts/sov_epic.py next --village ' + v + '` and `python scripts/sov_epic.py unrouted` from the repository root. '
    + 'For each candidate issue read its projected metadata in .claude/epic/tree.json, load the .claude/skills/sov-<domain>/SKILL.md of the routed domain, and read the open_decisions block of STATUS.yaml. '
    + 'Choose ONE issue: prefer horizon NOW, reachable (no unsatisfied requires), routed to a domain, and not blocked by an open decision. If every candidate is blocked, say so and return the blockers rather than inventing work. '
    + 'An unrouted issue is never a valid selection - routing it is a judgement only Bdo makes; report it as a judgement item instead. '
    + 'You plan only; edit nothing. '
    + 'Return: village, operation (one bounded sentence), issue (as "#N" or "none"), domain (or "unrouted"), blocked_by (open-decision ids and unsatisfied requires), rationale, files, effect_class, and judgement_items.'
}

const plans = await parallel(selectedVillages.map(function (v) {
  return function () {
    return agent(planPrompt(v), { agentType: 'sov-orchestrator', schema: PLAN_SCHEMA, phase: 'Select', label: 'select:' + v })
  }
}))

const selected = []
const judgementQueue = []
const residuals = []

recon.judgement_items.forEach(function (q) { judgementQueue.push('reconcile: ' + q) })
recon.residuals.forEach(function (x) { residuals.push('reconcile: ' + x) })

selectedVillages.forEach(function (v, i) {
  const plan = plans[i]
  if (!plan) {
    residuals.push(v + ': orchestrator returned no plan; village unplanned this run')
    return
  }
  plan.judgement_items.forEach(function (q) { judgementQueue.push(v + ': ' + q) })
  const legal = plan.issue && plan.issue !== 'none'
    && plan.domain && plan.domain !== 'unrouted'
    && plan.blocked_by.length === 0
  if (legal) {
    selected.push(plan)
  } else if (plan.blocked_by.length > 0) {
    residuals.push(v + ': no legal operation; held by ' + plan.blocked_by.join(', '))
  }
})

log(selected.length + ' legal operation(s) selected; ' + judgementQueue.length + ' judgement item(s) queued for Bdo')

const builds = []
const witnesses = []

if (advance && selected.length > 0) {
  const queue = selected.slice(0, maxOperations)
  phase('Advance')
  log('Advance mode: building ' + queue.length + ' of ' + selected.length + ' selected operation(s); the rest stay planned only')
  const outcomes = await pipeline(
    queue,
    function (plan) {
      return agent(
        'Execute exactly one bounded Soveraeign operation in the ' + plan.domain + ' domain, closing part of issue ' + plan.issue + '. '
        + 'Operation: ' + plan.operation + '. Rationale: ' + plan.rationale + '. '
        + 'Load .claude/skills/sov-' + plan.domain + '/SKILL.md and AGENTS.md first, and honour every blocker the skill names. '
        + 'Stay inside this operation: do not widen scope, do not touch other issues, never run git commit or git push, and never enable an external effect. '
        + 'Run `python scripts/verify.py` from the repository root before reporting, and report its real exit code. '
        + 'Return: issue, domain, changed (file paths), checks (command and exit code), standing_proposal (at most "BUILT -> WITNESSED", or "none"), and residuals.',
        { agentType: 'sov-worker', schema: BUILD_SCHEMA, phase: 'Advance', label: 'build:' + plan.issue }
      )
    },
    function (build, plan) {
      if (!build) { return null }
      return agent(
        'Independently witness a build claim for Soveraeign issue ' + plan.issue + ' in the ' + plan.domain + ' domain. '
        + 'The builder reported these changed files: ' + (build.changed || []).join(', ') + '. '
        + 'Do not trust that report. Inspect the changes yourself with git status and git diff, read them against the owning contract and .claude/skills/sov-' + plan.domain + '/SKILL.md, and run `python scripts/verify.py` yourself, observing the real exit code. '
        + 'You must not edit, fix, commit, or push; a witness that edits the work it witnesses is void. Dissent freely. '
        + 'Return: issue, verdict (one of CONFIRMED, PARTIAL, REFUTED), checks, observations, and dissent.',
        { agentType: 'sov-witness', schema: WITNESS_SCHEMA, phase: 'Witness', label: 'witness:' + plan.issue }
      ).then(function (verdict) { return { build: build, verdict: verdict } })
    }
  )
  outcomes.filter(Boolean).forEach(function (outcome) {
    builds.push(outcome.build)
    outcome.build.residuals.forEach(function (x) { residuals.push('build ' + outcome.build.issue + ': ' + x) })
    if (!outcome.verdict) {
      residuals.push(outcome.build.issue + ': build is unwitnessed; standing stays BUILT at most')
      return
    }
    witnesses.push(outcome.verdict)
    outcome.verdict.dissent.forEach(function (d) { residuals.push('witness ' + outcome.verdict.issue + ': ' + d) })
  })
} else if (advance) {
  residuals.push('advance requested but no legal operation was available this run')
}

return {
  mode: advance ? 'advance' : 'observe',
  objective: objective,
  root_issue: '#1',
  reconciliation: recon,
  villages: selectedVillages,
  plans: plans.filter(Boolean),
  selected: selected,
  builds: builds,
  witnesses: witnesses,
  residuals: residuals,
  judgement_queue: judgementQueue,
  standing_note: 'A walk observes and at most proposes BUILT -> WITNESSED. Only Bdo ratifies.',
}
