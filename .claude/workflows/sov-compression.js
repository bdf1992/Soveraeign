export const meta = {
  name: 'sov-compression',
  description: 'Observe-only daily/weekly compression ritual: deterministic repository reading followed by bounded synthesis; creates no policy, standing, phase, or ledger',
  whenToUse: 'Daily during a gap/active construction period to keep lessons and duplicated observations from accumulating; weekly for a deeper subtraction/compression pass before the next work cycle.',
  phases: [
    { title: 'Measure', detail: 'run the deterministic compression reader at the exact current revision' },
    { title: 'Route', detail: 'separate observations from lesson, decision, concern, skill, and subtraction candidates' },
    { title: 'Compress', detail: 'weekly only: identify duplicated producers/recomputation and the smallest safe subtraction plan' },
  ],
}

// args: { mode?: 'daily' | 'weekly', focus?: string }

const mode = args && args.mode === 'weekly' ? 'weekly' : 'daily'
const focus = args && args.focus ? args.focus : 'current gap/pre-opening work and cross-phase engineering substrate'

const MEASURE_SCHEMA = {
  type: 'object',
  required: ['command', 'exit_code', 'reading', 'observations', 'residuals'],
  properties: {
    command: { type: 'string' },
    exit_code: { type: 'integer' },
    reading: { type: 'object' },
    observations: { type: 'array', items: { type: 'string' } },
    residuals: { type: 'array', items: { type: 'string' } },
  },
}

const ROUTE_SCHEMA = {
  type: 'object',
  required: [
    'new_defects', 'corroboration', 'redundant_observations', 'representation_pressure',
    'lesson_routing', 'decision_candidates', 'concern_candidates', 'skill_candidates',
    'subtraction_candidates', 'owner_items', 'next_smallest_action',
  ],
  properties: {
    new_defects: { type: 'array', items: { type: 'string' } },
    corroboration: { type: 'array', items: { type: 'string' } },
    redundant_observations: { type: 'array', items: { type: 'string' } },
    representation_pressure: { type: 'array', items: { type: 'string' } },
    lesson_routing: { type: 'array', items: { type: 'string' } },
    decision_candidates: { type: 'array', items: { type: 'string' } },
    concern_candidates: { type: 'array', items: { type: 'string' } },
    skill_candidates: { type: 'array', items: { type: 'string' } },
    subtraction_candidates: { type: 'array', items: { type: 'string' } },
    owner_items: { type: 'array', items: { type: 'string' } },
    next_smallest_action: { type: 'string' },
  },
}

phase('Measure')
log('compression: ' + mode + ' reading, observe-only')

const measurePrompt = 'You are an independent read-only observer for the Soveraeign compression ritual. '
  + 'Read AGENTS.md and .claude/skills/sov-compression/SKILL.md first. Focus: ' + focus + '. '
  + 'Run exactly `python scripts/sov_compression.py ' + mode + ' --json` from the repository root. '
  + 'Record the real exit code and parse the emitted JSON into `reading`. Inspect enough repository context to explain anomalies, but do not edit, fix, commit, push, open a phase, change standing, or create a report/lesson/decision/concern. '
  + 'Return command, exit_code, reading, observations, and residuals. Churn and repeated failure are observations, not defects by themselves.'

const measured = await agent(measurePrompt, {
  agentType: 'sov-witness',
  schema: MEASURE_SCHEMA,
  phase: 'Measure',
  label: 'compression:measure:' + mode,
})

if (!measured || measured.exit_code !== 0) {
  return {
    mode: mode,
    focus: focus,
    error: 'compression reader did not produce a clean observation',
    measurement: measured || null,
  }
}

phase('Route')

const routePrompt = 'You are routing one already-measured Soveraeign compression observation. '
  + 'Read .claude/skills/sov-compression/SKILL.md, AGENTS.md, LESSONS.md, contracts/lessons-loop.json, STATUS.yaml, and only the governing/current files needed to interpret the measurement. '
  + 'You are not a witness of the measurement and you must not edit anything. '
  + 'Use the routing law exactly: report observes; lesson generalizes an evidenced invariant; decision changes policy/authority/boundary; concern creates concrete work. '
  + 'Independent corroboration is allowed and must not be mislabeled as duplication. Do not create a concern merely to store an observation. '
  + 'The repository is in gap/pre-opening state unless current STATUS says otherwise; never open or name a successor phase. '
  + 'Classify the measurement below. `skill_candidates` require repeated stable procedure, not repeated prose. `owner_items` contain only questions that genuinely require root/owner judgement. '
  + 'Always prefer a subtraction/compression action over widening when both would solve the same problem. '
  + 'MEASUREMENT:\n' + JSON.stringify(measured)

const routed = await agent(routePrompt, {
  agentType: 'sov-orchestrator',
  schema: ROUTE_SCHEMA,
  phase: 'Route',
  label: 'compression:route:' + mode,
})

let weekly = null
if (mode === 'weekly') {
  phase('Compress')
  const weeklyPrompt = 'Perform the weekly super-compression synthesis for Soveraeign. Read .claude/skills/sov-compression/SKILL.md and the routed observation below. '
    + 'Stay read-only. Look across the seven-day measurement and current repository evidence for: multiple authoritative producers of one fact, projections/checks recomputing a fact already owned elsewhere, repeated repair shapes, recorded lessons that can be strengthened/superseded/left alone, and stable procedures that may now justify a skill candidate. '
    + 'Do not invent architecture and do not turn the weekly pass into governance. Return the same routing schema, but make `subtraction_candidates` the smallest safe plan for reducing next week\'s reconciliation surface and set `next_smallest_action` to the first bounded move. '
    + 'ROUTED DAILY/WEEKLY OBSERVATION:\n' + JSON.stringify(routed)
  weekly = await agent(weeklyPrompt, {
    agentType: 'sov-orchestrator',
    schema: ROUTE_SCHEMA,
    phase: 'Compress',
    label: 'compression:super',
  })
}

const result = weekly || routed
log('compression complete: ' + result.new_defects.length + ' new defect(s), '
  + result.redundant_observations.length + ' redundant observation(s), '
  + result.subtraction_candidates.length + ' subtraction candidate(s), '
  + result.owner_items.length + ' owner item(s)')

return {
  mode: mode,
  focus: focus,
  subject_revision: measured.reading.subject_revision,
  measurement: measured,
  routing: routed,
  super_compression: weekly,
  next_smallest_action: result.next_smallest_action,
}
