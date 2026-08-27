export const meta = {
  name: 'sov-backlog',
  description: 'Survey every branch that never reached the trunk and return one evidenced disposition per branch',
  whenToUse: 'When unlanded work has piled up and somebody needs to decide what happens to each branch. Measures with scripts/sov_backlog.py, judges each branch with an independent agent, checks the judgements against each other, and returns a landing order. Read-only: it never merges, commits, pushes, or deletes.',
  phases: [
    { title: 'Survey', detail: 'measure every unlanded branch against the trunk' },
    { title: 'Judge', detail: 'one agent per batch of branches, disposition with evidence' },
    { title: 'Check', detail: 'an independent pass over the dispositions that claim work is disposable' },
    { title: 'Order', detail: 'sequence the landings against the contested files' },
  ],
}

// args: { batch_size?: number, only?: string[] }

const DISPOSITIONS = ['LAND', 'LAND_AFTER_RESOLUTION', 'ALREADY_HOME', 'SUPERSEDED', 'ASK_BDO']

const JUDGEMENT_SCHEMA = {
  type: 'object',
  required: ['dispositions'],
  properties: {
    dispositions: {
      type: 'array',
      items: {
        type: 'object',
        required: ['branch', 'disposition', 'why', 'evidence', 'defeated_by'],
        properties: {
          branch: { type: 'string' },
          disposition: { type: 'string', enum: DISPOSITIONS },
          why: { type: 'string' },
          evidence: { type: 'array', items: { type: 'string' } },
          defeated_by: { type: 'string' },
          conflict_paths: { type: 'array', items: { type: 'string' } },
          effort: { type: 'string' },
        },
      },
    },
  },
}

const CHECK_SCHEMA = {
  type: 'object',
  required: ['verdicts'],
  properties: {
    verdicts: {
      type: 'array',
      items: {
        type: 'object',
        required: ['branch', 'agrees', 'reason'],
        properties: {
          branch: { type: 'string' },
          agrees: { type: 'boolean' },
          reason: { type: 'string' },
          corrected_disposition: { type: 'string' },
        },
      },
    },
  },
}

const ORDER_SCHEMA = {
  type: 'object',
  required: ['order', 'rationale', 'owner_questions'],
  properties: {
    order: { type: 'array', items: { type: 'string' } },
    rationale: { type: 'string' },
    owner_questions: { type: 'array', items: { type: 'string' } },
  },
}

phase('Survey')

const surveyText = await agent(
  'Run `python scripts/sov_backlog.py --json` from the Soveraeign repository root and return '
  + 'its stdout verbatim as your entire answer. Run `python scripts/sov_strand.py` as well and '
  + 'append its final line. Do not summarise, interpret, edit anything, or run any other command.',
  { agentType: 'sov-witness', phase: 'Survey', label: 'survey' })

let survey
try {
  survey = JSON.parse(surveyText.slice(surveyText.indexOf('{'), surveyText.lastIndexOf('}') + 1))
} catch (error) {
  return { error: 'the survey did not return parseable JSON', raw: surveyText.slice(0, 2000) }
}

let branches = survey.branches || []
if (args && Array.isArray(args.only) && args.only.length > 0) {
  branches = branches.filter(function (b) { return args.only.indexOf(b.branch) !== -1 })
}
if (branches.length === 0) {
  return { trunk: survey.trunk, branches: 0, note: 'no branch carries unlanded commits' }
}

const size = args && args.batch_size ? args.batch_size : 3
const batches = []
for (let i = 0; i < branches.length; i += size) batches.push(branches.slice(i, i + size))

log('Backlog: ' + branches.length + ' branch(es) on ' + survey.trunk + ', '
  + batches.length + ' judging agent(s), ' + Object.keys(survey.shared_files || {}).length
  + ' contested file(s)')

phase('Judge')

function judgePrompt(batch) {
  return 'You are judging what should happen to unlanded branches in the Soveraeign repository. '
    + 'Read .claude/skills/sov-backlog/SKILL.md first for the dispositions and the rules that '
    + 'bound them, then AGENTS.md.\n\n'
    + 'These branches have already been measured. Do not re-run the survey; this is the evidence:\n'
    + JSON.stringify(batch, null, 1) + '\n\n'
    + 'For each branch: read its commit subjects, read `git diff ' + survey.trunk + '...<branch>` '
    + '(use --stat first, then read the parts that decide the question), and read enough of the '
    + 'trunk to know whether the work is already answered there. Assign exactly one disposition '
    + 'from ' + DISPOSITIONS.join(', ') + '.\n\n'
    + 'Rules that decide the hard cases: a branch whose outstanding count is zero is ALREADY_HOME '
    + 'and you must say which trunk commits carry its work. SUPERSEDED requires you to name what '
    + 'supersedes it, not to observe that it is old. ASK_BDO is only for product intent, naming, '
    + 'external commitment, secrets, destructive administration, or two settled constraints in '
    + 'genuine conflict - contracts/acceptance-policy.json states that list is exhaustive, so '
    + 'wanting a second opinion is not a reason and neither is a branch nobody remembers.\n\n'
    + 'You must not merge, commit, push, delete a branch, checkout, or edit any file. Read only.\n\n'
    + 'Return one entry per branch with: branch, disposition, why (one plain sentence), evidence '
    + '(exact commands you ran and what they showed), defeated_by (what observation would '
    + 'overturn your disposition), conflict_paths where relevant, and effort as one of '
    + 'trivial/hours/unclear.'
}

const judged = await parallel(batches.map(function (batch, i) {
  return function () {
    return agent(judgePrompt(batch), {
      agentType: 'sov-orchestrator', schema: JUDGEMENT_SCHEMA, phase: 'Judge',
      label: 'judge:' + (i + 1) + '/' + batches.length,
    })
  }
}))

const dispositions = []
judged.filter(Boolean).forEach(function (r) {
  (r.dispositions || []).forEach(function (d) { dispositions.push(d) })
})

const missing = branches
  .map(function (b) { return b.branch })
  .filter(function (name) {
    return !dispositions.some(function (d) { return d.branch === name })
  })
if (missing.length > 0) log('No disposition returned for: ' + missing.join(', '))

phase('Check')

// Only the dispositions that would let work be thrown away are re-derived. A wrong LAND
// costs a conflict; a wrong ALREADY_HOME or SUPERSEDED costs the work itself.
const disposable = dispositions.filter(function (d) {
  return d.disposition === 'ALREADY_HOME' || d.disposition === 'SUPERSEDED'
})

let verdicts = []
if (disposable.length > 0) {
  const checked = await agent(
    'You are independently checking claims that unlanded work in the Soveraeign repository is '
    + 'disposable. Another agent judged these branches; you did not, and you must re-derive '
    + 'rather than agree.\n\n' + JSON.stringify(disposable, null, 1) + '\n\n'
    + 'For each claim, verify it yourself with git. ALREADY_HOME means every outstanding commit '
    + 'patch is present on ' + survey.trunk + ' - check with `git cherry ' + survey.trunk
    + ' <branch>` and by reading the diff, not by trusting the count. SUPERSEDED means specific '
    + 'later work answers it - find that work or refuse the claim.\n\n'
    + 'Default to disagreeing when you cannot confirm. Losing work is worse than keeping a '
    + 'branch. You must not edit, merge, delete, or push anything.\n\n'
    + 'Return one verdict per branch: branch, agrees, reason, and corrected_disposition when '
    + 'you disagree.',
    { agentType: 'sov-witness', schema: CHECK_SCHEMA, phase: 'Check', label: 'check:disposable' })
  verdicts = (checked && checked.verdicts) || []
}

const overturned = verdicts.filter(function (v) { return v.agrees === false })
overturned.forEach(function (v) {
  const row = dispositions.find(function (d) { return d.branch === v.branch })
  if (row) {
    row.overturned_from = row.disposition
    row.disposition = v.corrected_disposition || 'ASK_BDO'
    row.why = 'independent check disagreed: ' + v.reason
  }
})

phase('Order')

const landable = dispositions.filter(function (d) {
  return d.disposition === 'LAND' || d.disposition === 'LAND_AFTER_RESOLUTION'
})

let ordering = { order: [], rationale: 'nothing is landable', owner_questions: [] }
if (landable.length > 0) {
  ordering = await agent(
    'Sequence these Soveraeign branch landings so each one does not manufacture the next '
    + 'conflict.\n\nLandable:\n' + JSON.stringify(landable, null, 1)
    + '\n\nFiles more than one branch changes:\n'
    + JSON.stringify(survey.shared_files || {}, null, 1)
    + '\n\nLand the smallest contested surface first, and put a branch that many others touch '
    + 'files with either first (so the rest rebase onto it once) or last (so it absorbs them) - '
    + 'say which and why. Read only; sequence nothing into existence, and merge nothing.\n\n'
    + 'Return: order (branch names), rationale (a short paragraph), and owner_questions - only '
    + 'items that are genuinely product intent, naming, external commitment, or a conflict '
    + 'between settled constraints.',
    { agentType: 'sov-orchestrator', schema: ORDER_SCHEMA, phase: 'Order', label: 'order' }) || ordering
}

const counts = {}
DISPOSITIONS.forEach(function (d) {
  counts[d] = dispositions.filter(function (r) { return r.disposition === d }).length
})

return {
  trunk: survey.trunk,
  measured: branches.length,
  judged: dispositions.length,
  no_disposition: missing,
  counts: counts,
  overturned_by_check: overturned.length,
  dispositions: dispositions,
  landing_order: ordering.order,
  landing_rationale: ordering.rationale,
  owner_questions: ordering.owner_questions,
  contested_files: Object.keys(survey.shared_files || {}).length,
  note: 'Dispositions are claims, not settlements. Nothing here merged, committed, pushed, or '
    + 'deleted anything. Landing is a separate act under contracts/standing-grants.json and '
    + 'requires an independent observation.',
}
