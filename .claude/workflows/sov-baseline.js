export const meta = {
  name: 'sov-baseline',
  description: 'Foundational control loop: orient, scout every domain read-only, reconcile cross-domain conflicts, and return a baseline report before a long-horizon federation run',
  whenToUse: 'Before a long-horizon or multi-domain sov-federation session: establishes current standing, legitimately available operations, blockers, file-overlap and ownership seams between domains, and the judgement queue Bdo should clear first. Builds nothing; every agent is a planner or a witness.',
  phases: [
    { title: 'Orient', detail: 'sov-orchestrator turns the horizon into per-domain probe briefs and cross-cutting concerns' },
    { title: 'Scout', detail: 'one read-only scout per domain: standing, checks, available operations, blockers, touchpoints' },
    { title: 'Reconcile', detail: 'control loop: detect cross-domain conflicts, witness-probe each, repeat until dry or round cap' },
    { title: 'Report', detail: 'assemble readiness per domain, ordering, seams, dependencies, and the judgement queue' },
  ],
}

// args: { domains?: string[], horizon?: string, max_rounds?: number, max_probes_per_round?: number, run_date?: string }
// Leaf workflow: it never nests child workflows. Read-only with respect to the repository:
// Orient and Scout run sov-orchestrator (plans, edits nothing); Reconcile runs sov-witness (observes, edits nothing).
// The invoking controller (interactive session or agents/sov-controller.md) writes the human-facing report.

const KNOWN = ['governance', 'contracts', 'conformance', 'asset', 'proofing', 'console', 'byom', 'verification']

const requested = args && Array.isArray(args.domains) && args.domains.length > 0 ? args.domains : KNOWN
const selected = requested.filter(function (d) { return KNOWN.indexOf(d) !== -1 })
const horizon = args && args.horizon ? args.horizon : 'a long-horizon sov-federation session advancing every domain one bounded, witnessed operation at a time, concurrently, under the current open decisions O1-O12'
const maxRounds = args && typeof args.max_rounds === 'number' ? args.max_rounds : 2
const maxProbes = args && typeof args.max_probes_per_round === 'number' ? args.max_probes_per_round : 4
const runDate = args && args.run_date ? args.run_date : 'unstamped'

if (selected.length === 0) {
  return { error: 'no known domains selected', known: KNOWN }
}

const ORIENT_SCHEMA = {
  type: 'object',
  required: ['briefs', 'crosscutting', 'judgement_queue'],
  properties: {
    briefs: { type: 'array', items: { type: 'object', required: ['domain', 'focus', 'questions'], properties: { domain: { type: 'string' }, focus: { type: 'string' }, questions: { type: 'array', items: { type: 'string' } } } } },
    crosscutting: { type: 'array', items: { type: 'object', required: ['id', 'concern', 'domains'], properties: { id: { type: 'string' }, concern: { type: 'string' }, domains: { type: 'array', items: { type: 'string' } }, paths: { type: 'array', items: { type: 'string' } } } } },
    judgement_queue: { type: 'array', items: { type: 'string' } },
  },
}

const SCOUT_SCHEMA = {
  type: 'object',
  required: ['domain', 'standing', 'checks', 'observations', 'available_operations', 'blocked', 'touchpoints', 'judgement_items', 'readiness', 'first_operation'],
  properties: {
    domain: { type: 'string' },
    standing: { type: 'string' },
    checks: { type: 'array', items: { type: 'object', required: ['command', 'exit_code'], properties: { command: { type: 'string' }, exit_code: { type: 'integer' } } } },
    observations: { type: 'array', items: { type: 'string' } },
    available_operations: { type: 'array', items: { type: 'object', required: ['id', 'description', 'files', 'effect_class'], properties: { id: { type: 'string' }, description: { type: 'string' }, files: { type: 'array', items: { type: 'string' } }, effect_class: { type: 'string', enum: ['RECORD_LOCAL', 'RESOURCE_CONSUMPTION'] }, depends_on: { type: 'array', items: { type: 'string' } } } } },
    blocked: { type: 'array', items: { type: 'object', required: ['what', 'gated_by'], properties: { what: { type: 'string' }, gated_by: { type: 'string' } } } },
    touchpoints: { type: 'array', items: { type: 'object', required: ['path_or_term', 'other_domain', 'nature'], properties: { path_or_term: { type: 'string' }, other_domain: { type: 'string' }, nature: { type: 'string', enum: ['reads', 'writes', 'shared_vocabulary', 'ownership_claim'] }, note: { type: 'string' } } } },
    judgement_items: { type: 'array', items: { type: 'string' } },
    readiness: { type: 'string', enum: ['READY', 'PARTIAL', 'BLOCKED'] },
    first_operation: { type: 'string' },
  },
}

const PROBE_SCHEMA = {
  type: 'object',
  required: ['conflict_id', 'real', 'finding', 'resolution', 'ordering', 'further_conflicts', 'judgement_items'],
  properties: {
    conflict_id: { type: 'string' },
    real: { type: 'boolean' },
    finding: { type: 'string' },
    owner_per_skills: { type: 'string' },
    resolution: { type: 'string', enum: ['not_a_conflict', 'serialize', 'split_files', 'judgement'] },
    ordering: { type: 'array', items: { type: 'string' } },
    further_conflicts: { type: 'array', items: { type: 'object', required: ['id', 'concern', 'domains'], properties: { id: { type: 'string' }, concern: { type: 'string' }, domains: { type: 'array', items: { type: 'string' } }, paths: { type: 'array', items: { type: 'string' } } } } },
    judgement_items: { type: 'array', items: { type: 'string' } },
  },
}

function unique(list) {
  const out = []
  list.forEach(function (x) { if (out.indexOf(x) === -1) { out.push(x) } })
  return out
}

function norm(p) {
  return String(p).split('\\').join('/').replace(/^\.\//, '')
}

// ---------------------------------------------------------------- Orient

phase('Orient')
log('Orient: framing the horizon across ' + selected.length + ' domain(s)')

const orient = await agent(
  'You are the orienting planner for a Soveraeign baseline run (workflow sov-baseline). Repository root: the working directory. ' +
  'Horizon the baseline prepares for: ' + horizon + '. Domains in scope: ' + selected.join(', ') + '. ' +
  'Read AGENTS.md, STATUS.yaml, OPEN-SEAMS.md, .claude/README.md, and for each domain the "Owns / Must not", "Standing and blockers", and "Named operations" sections of .claude/skills/sov-<domain>/SKILL.md (bounded excerpts; grep before opening broad files). ' +
  'Produce: (1) briefs - exactly one per domain named above, with the domain string exactly as given, a one-sentence focus for this horizon, and three to five concrete questions the domain scout must answer; ' +
  '(2) crosscutting - concerns that span two or more domains when they execute concurrently: shared files, shared vocabulary, ownership collisions between skills, ordering dependencies, and open decisions that gate more than one domain; each with an id, the concern, the domains involved, and paths where applicable; ' +
  '(3) judgement_queue - questions only Bdo can decide that the horizon run will hit, stated as questions. ' +
  'You plan briefs only; you do not plan operations, edit files, or decide judgement items.',
  { agentType: 'sov-orchestrator', schema: ORIENT_SCHEMA, phase: 'Orient', label: 'orient' }
)

const briefs = {}
if (orient && Array.isArray(orient.briefs)) {
  orient.briefs.forEach(function (b) { briefs[b.domain] = b })
}
const crosscutting = orient && Array.isArray(orient.crosscutting) ? orient.crosscutting : []
const orientQueue = orient && Array.isArray(orient.judgement_queue) ? orient.judgement_queue : []
if (!orient) { log('Orient: planner returned nothing; scouts will run on default briefs') }

// ---------------------------------------------------------------- Scout

phase('Scout')
log('Scout: dispatching ' + selected.length + ' read-only scout(s)')

function scoutPrompt(d) {
  const b = briefs[d] || { focus: 'current standing and legitimately available work for the horizon', questions: [] }
  const qs = b.questions.length > 0 ? ' Answer these questions in observations: ' + b.questions.join(' | ') + '.' : ''
  return 'You are the read-only scout for the Soveraeign ' + d + ' domain in a baseline run (workflow sov-baseline). Repository root: the working directory. ' +
    'Load the sov-' + d + ' skill (or read .claude/skills/sov-' + d + '/SKILL.md), then AGENTS.md and STATUS.yaml. ' +
    'Horizon: ' + horizon + '. Focus: ' + b.focus + '.' + qs + ' ' +
    'Do, in order: (1) standing - the STATUS.yaml status field value(s) that cover this domain, or "none"; ' +
    '(2) git status --short and git diff --stat restricted to the domain key files, summarized as observations; ' +
    '(3) run python scripts/verify.py from the repository root plus every domain verification command the skill names, recording exact commands and exit codes in checks; ' +
    '(4) available_operations - every operation legitimately available now under open decisions O1-O12, taken from the skill named operations and bounded: id, description, exact repo-relative files it would change, effect_class RECORD_LOCAL or RESOURCE_CONSUMPTION, depends_on other operation ids; these are candidates for concurrent execution so file lists must be exact and complete; ' +
    '(5) blocked - what this domain cannot do and the open decision or boundary that gates it; ' +
    '(6) touchpoints - every file or vocabulary term outside this domain Owns clause that the available operations would read, write, share, or claim: nature is reads, writes, shared_vocabulary, or ownership_claim, with the other domain named; ' +
    '(7) judgement_items - questions only Bdo can decide; ' +
    '(8) readiness - READY when at least one operation is available and none of them writes outside this domain; PARTIAL when operations exist but write into another domain or need an open decision to be meaningful; BLOCKED when nothing is available; first_operation is the id you would run first, or "none". ' +
    'You must not edit, build, commit, or push. Never treat a green build or any report as authority; report standing exactly as STATUS.yaml states it and note drift as an observation.'
}

const scoutResults = await parallel(selected.map(function (d) {
  return function () { return agent(scoutPrompt(d), { agentType: 'sov-orchestrator', schema: SCOUT_SCHEMA, phase: 'Scout', label: 'scout:' + d }) }
}))

const scouts = []
const residuals = []
selected.forEach(function (d, i) {
  const r = scoutResults[i]
  if (!r) {
    residuals.push(d + ': scout returned no report; domain state unscouted')
    return
  }
  r.domain = d
  scouts.push(r)
})
log('Scout: ' + scouts.length + '/' + selected.length + ' domain(s) reported')

// ---------------------------------------------------------------- Reconcile (control loop)

phase('Reconcile')

function detectConflicts(seen) {
  const out = []
  const fileOwners = {}
  scouts.forEach(function (s) {
    s.available_operations.forEach(function (op) {
      op.files.forEach(function (f) {
        const k = norm(f)
        if (!fileOwners[k]) { fileOwners[k] = [] }
        fileOwners[k].push(s.domain + ':' + op.id)
      })
    })
  })
  Object.keys(fileOwners).forEach(function (f) {
    const doms = unique(fileOwners[f].map(function (x) { return x.split(':')[0] }))
    if (doms.length > 1) {
      out.push({ id: 'file:' + f, concern: 'planned operations in ' + doms.join(' and ') + ' would all change ' + f + ' (' + fileOwners[f].join(', ') + ')', domains: doms, paths: [f], source: 'file-overlap' })
    }
  })
  crosscutting.forEach(function (c) {
    out.push({ id: 'xc:' + c.id, concern: c.concern, domains: c.domains, paths: c.paths || [], source: 'orient' })
  })
  scouts.forEach(function (s) {
    s.touchpoints.forEach(function (t) {
      if (t.nature !== 'writes' && t.nature !== 'ownership_claim') { return }
      if (!t.other_domain || t.other_domain === s.domain) { return }
      out.push({ id: 'touch:' + s.domain + '>' + t.other_domain + ':' + norm(t.path_or_term), concern: s.domain + ' reports ' + t.nature + ' on ' + t.other_domain + ' territory: ' + t.path_or_term + (t.note ? ' - ' + t.note : ''), domains: [s.domain, t.other_domain], paths: [t.path_or_term], source: 'touchpoint' })
    })
  })
  return out.filter(function (c) { return !seen.has(c.id) })
}

function probePrompt(c) {
  const doms = unique(c.domains)
  return 'You are an independent witness probing one suspected cross-domain conflict surfaced by the sov-baseline control loop. Repository root: the working directory. ' +
    'Conflict ' + c.id + ' (source: ' + c.source + '): ' + c.concern + '. Domains: ' + doms.join(', ') + '. Paths or terms: ' + (c.paths.length ? c.paths.join(', ') : 'none given') + '. ' +
    'Read the Design System of Record and Directory boundaries sections of AGENTS.md, and the "Owns / Must not" section of ' + doms.map(function (d) { return '.claude/skills/sov-' + d + '/SKILL.md' }).join(' and ') + '. Then inspect the actual files or terms involved (grep first; bounded excerpts only). ' +
    'Determine: real - whether this is a genuine hazard for concurrent execution (two domains writing the same file, or claiming the same ownership, or one domain needing the other to finish first); owner_per_skills - which Owns clause covers it, quoted; ' +
    'resolution - not_a_conflict (say why), serialize (ordering lists which domain or operation goes first and why), split_files (propose which domain owns which part, as a proposal), or judgement (only Bdo can decide; put the question in judgement_items). ' +
    'further_conflicts - hazards you observed while inspecting that were not handed to you. ' +
    'You must not edit anything, and you must not pick a side on a judgement-typed question.'
}

const seen = new Set()
const probed = []
let unprobed = []
let candidates = detectConflicts(seen)
let round = 0

while (candidates.length > 0 && round < maxRounds) {
  round++
  const batch = candidates.slice(0, maxProbes)
  const deferred = candidates.slice(maxProbes)
  batch.forEach(function (c) { seen.add(c.id) })
  log('Reconcile round ' + round + ': probing ' + batch.length + ' conflict(s)' + (deferred.length ? ', ' + deferred.length + ' deferred to next round' : ''))

  const results = await parallel(batch.map(function (c) {
    return function () { return agent(probePrompt(c), { agentType: 'sov-witness', schema: PROBE_SCHEMA, phase: 'Reconcile', label: 'probe:' + c.id }) }
  }))

  const fresh = []
  batch.forEach(function (c, i) {
    const r = results[i]
    probed.push({ conflict: c, probe: r || null })
    if (!r) {
      residuals.push('reconcile: probe for ' + c.id + ' returned nothing; conflict unattested')
      return
    }
    r.further_conflicts.forEach(function (fc) {
      fresh.push({ id: 'probe:' + fc.id, concern: fc.concern, domains: fc.domains, paths: fc.paths || [], source: 'probe:' + c.id })
    })
  })

  candidates = deferred.concat(fresh).filter(function (c) { return !seen.has(c.id) })
  if (fresh.length > 0) { log('Reconcile round ' + round + ': probes surfaced ' + fresh.length + ' further conflict(s)') }
}

if (candidates.length > 0) {
  unprobed = candidates
  log('Reconcile: round cap ' + maxRounds + ' reached with ' + unprobed.length + ' conflict(s) left unprobed - listed in the report, not dropped')
} else {
  log('Reconcile: dry after ' + round + ' round(s)')
}

// ---------------------------------------------------------------- Report

phase('Report')

const domains = {}
const readiness = {}
const judgementQueue = []
const ordering = []
const dependencies = []
const realConflicts = []
const dismissed = []

function queue(item) {
  if (judgementQueue.indexOf(item) === -1) { judgementQueue.push(item) }
}

orientQueue.forEach(function (q) { queue('orient: ' + q) })

selected.forEach(function (d) {
  const s = scouts.filter(function (x) { return x.domain === d })[0]
  if (!s) {
    domains[d] = { error: 'unscouted' }
    readiness[d] = 'UNSCOUTED'
    return
  }
  domains[d] = s
  readiness[d] = s.readiness
  s.judgement_items.forEach(function (q) { queue(d + ': ' + q) })
  s.touchpoints.forEach(function (t) {
    if (t.nature === 'reads' || t.nature === 'shared_vocabulary') {
      dependencies.push({ domain: d, other_domain: t.other_domain, nature: t.nature, path_or_term: t.path_or_term, note: t.note || '' })
    }
  })
  s.checks.forEach(function (c) {
    if (c.exit_code !== 0) { residuals.push(d + ': check failed - ' + c.command + ' exit ' + c.exit_code) }
  })
})

probed.forEach(function (p) {
  const r = p.probe
  if (!r) { return }
  r.judgement_items.forEach(function (q) { queue('reconcile ' + p.conflict.id + ': ' + q) })
  if (r.real) {
    realConflicts.push({ id: p.conflict.id, domains: p.conflict.domains, finding: r.finding, owner_per_skills: r.owner_per_skills || '', resolution: r.resolution, ordering: r.ordering })
    r.ordering.forEach(function (o) { if (ordering.indexOf(o) === -1) { ordering.push(o) } })
  } else {
    dismissed.push({ id: p.conflict.id, finding: r.finding })
  }
})

const counts = { READY: 0, PARTIAL: 0, BLOCKED: 0, UNSCOUTED: 0 }
Object.keys(readiness).forEach(function (d) { counts[readiness[d]] = (counts[readiness[d]] || 0) + 1 })

log('Report: ' + counts.READY + ' ready, ' + counts.PARTIAL + ' partial, ' + counts.BLOCKED + ' blocked, ' + counts.UNSCOUTED + ' unscouted; ' + realConflicts.length + ' real conflict(s), ' + judgementQueue.length + ' judgement item(s) for Bdo')

return {
  workflow: 'sov-baseline',
  run_date: runDate,
  horizon: horizon,
  scouted: selected,
  rounds_run: round,
  readiness: readiness,
  readiness_counts: counts,
  domains: domains,
  crosscutting_from_orient: crosscutting,
  conflicts: { real: realConflicts, dismissed: dismissed, unprobed: unprobed },
  ordering: ordering,
  dependencies: dependencies,
  residuals: residuals,
  judgement_queue: judgementQueue,
  standing_proposal: 'none',
}
