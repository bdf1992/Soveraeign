export const meta = {
  name: 'sov-federation',
  description: 'Dispatch selected Soveraeign domain workflows as children and aggregate their reports and judgement queues',
  whenToUse: 'When work spans more than one Soveraeign domain, or the owner asks to advance the whole stack. For single-domain work, run that domain workflow directly.',
  phases: [
    { title: 'Dispatch', detail: 'run one child workflow per selected domain' },
    { title: 'Aggregate', detail: 'merge reports, residuals, and the judgement queue' },
  ],
}

// args: { domains?: string[], objective?: string }
// Nesting note: this is the ONLY workflow allowed to call workflow() —
// domain workflows are leaf children and may never nest further.

const KNOWN = ['governance', 'contracts', 'conformance', 'asset', 'proofing', 'console', 'byom', 'verification']

const requested = args && Array.isArray(args.domains) && args.domains.length > 0 ? args.domains : KNOWN
const selected = requested.filter(function (d) { return KNOWN.indexOf(d) !== -1 })
const rejected = requested.filter(function (d) { return KNOWN.indexOf(d) === -1 })
// No objective from the caller means each child uses its own domain default.
const objective = args && args.objective ? args.objective : null

if (rejected.length > 0) {
  log('Unknown domains ignored: ' + rejected.join(', '))
}
if (selected.length === 0) {
  return { error: 'no known domains selected', known: KNOWN, rejected: rejected }
}

phase('Dispatch')
log('Dispatching ' + selected.length + ' domain workflow(s): ' + selected.join(', '))

// Parallel dispatch shares one working tree, so a green verify.py run is not
// attributable to a single domain. sequential: true trades wall-clock for
// per-domain attribution.
const childArgs = objective ? { objective: objective } : {}
const sequential = !!(args && args.sequential)
let reports = []
if (sequential) {
  log('Sequential dispatch: each domain runs against the tree left by the domains before it')
  for (const d of selected) {
    let r = null
    try { r = await workflow('sov-' + d, childArgs) } catch (e) { r = null }
    reports.push(r)
  }
} else {
  reports = await parallel(selected.map(function (d) {
    return function () { return workflow('sov-' + d, childArgs) }
  }))
}

phase('Aggregate')

const domains = {}
const judgementQueue = []
const residuals = []
const standingProposals = []

selected.forEach(function (d, i) {
  const r = reports[i]
  if (!r) {
    domains[d] = { error: 'child workflow failed or was skipped' }
    residuals.push(d + ': child workflow returned no report')
    return
  }
  domains[d] = r
  if (Array.isArray(r.judgement_queue)) {
    r.judgement_queue.forEach(function (q) { judgementQueue.push(d + ': ' + q) })
  }
  if (Array.isArray(r.residuals)) {
    r.residuals.forEach(function (x) { residuals.push(d + ': ' + x) })
  }
  const sp = r.standing_proposal
  if (sp && sp !== 'none' && sp !== 'NONE') {
    standingProposals.push({ domain: d, proposal: String(sp).split(' ').join('') })
  }
})

log('Aggregated ' + selected.length + ' report(s); ' + judgementQueue.length + ' judgement item(s) queued for Bdo')

return {
  objective: objective || 'per-domain default objective',
  dispatched: selected,
  rejected: rejected,
  domains: domains,
  standing_proposals: standingProposals,
  residuals: residuals,
  judgement_queue: judgementQueue,
}
