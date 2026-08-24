export const meta = {
  name: 'sov-f2-control',
  description: 'Unattended control loop that drives the F2 milestone gate closed one witnessed tick at a time, committing only what an independent witness reproduced',
  whenToUse: 'For a long-horizon unattended run against a milestone rather than a domain. Each tick reads scripts/sov_f2_gate.py, plans against the ranked open predicates, builds, witnesses independently, and then commits or reverts. Stops when the gate closes, when repair fails twice, or at the tick cap.',
  phases: [
    { title: 'Read', detail: 'read the gate, verify.py, lint.py and the oracle' },
    { title: 'Plan', detail: 'bound the next predicates into one operation set' },
    { title: 'Build', detail: 'author the positive and defeating fixtures' },
    { title: 'Witness', detail: 'independent inspection; never skipped' },
    { title: 'Settle', detail: 'commit a reproduced tick, revert a dissented one' },
  ],
}

// args: { root: string, maxTicks?: number, perTick?: number }
//
// The loop runs in whatever working tree `root` names. It commits and reverts,
// so `root` must be a tree nothing else is writing - a dedicated git worktree.
// It never pushes, never leaves the tree dirty between ticks, and never claims
// RATIFIED: a witnessed tick proposes BUILT->WITNESSED and nothing further.

const ROOT = (args && args.root) ? args.root : '.'
const MAX_TICKS = (args && args.maxTicks) ? args.maxTicks : 40
const PER_TICK = (args && args.perTick) ? args.perTick : 3

const READ_SCHEMA = {
  type: 'object',
  required: ['gate_closed', 'predicates_total', 'predicates_covered', 'verify_exit', 'lint_exit', 'oracle_exit', 'open'],
  properties: {
    gate_closed: { type: 'boolean' },
    predicates_total: { type: 'integer' },
    predicates_covered: { type: 'integer' },
    bound_participants: { type: 'integer' },
    verify_exit: { type: 'integer' },
    verify_failures: { type: 'array', items: { type: 'string' } },
    lint_exit: { type: 'integer' },
    oracle_exit: { type: 'integer' },
    tree_clean: { type: 'boolean' },
    head: { type: 'string' },
    open: {
      type: 'array',
      items: {
        type: 'object',
        required: ['id', 'family', 'text'],
        properties: { id: { type: 'string' }, family: { type: 'string' }, text: { type: 'string' }, missing: { type: 'array', items: { type: 'string' } } },
      },
    },
    observations: { type: 'array', items: { type: 'string' } },
  },
}

const PLAN_SCHEMA = {
  type: 'object',
  required: ['blocked', 'operations', 'judgement_queue'],
  properties: {
    blocked: { type: 'boolean' },
    blocked_reason: { type: 'string' },
    operations: {
      type: 'array',
      items: {
        type: 'object',
        required: ['id', 'predicates', 'description', 'files', 'effect_class'],
        properties: {
          id: { type: 'string' },
          predicates: { type: 'array', items: { type: 'string' } },
          description: { type: 'string' },
          files: { type: 'array', items: { type: 'string' } },
          effect_class: { type: 'string', enum: ['RECORD_LOCAL', 'RESOURCE_CONSUMPTION'] },
        },
      },
    },
    defaults_taken: { type: 'array', items: { type: 'string' } },
    judgement_queue: { type: 'array', items: { type: 'string' } },
  },
}

const BUILD_SCHEMA = {
  type: 'object',
  required: ['operation_id', 'files_changed', 'checks'],
  properties: {
    operation_id: { type: 'string' },
    predicates_claimed: { type: 'array', items: { type: 'string' } },
    files_changed: { type: 'array', items: { type: 'string' } },
    checks: { type: 'array', items: { type: 'object', required: ['command', 'exit_code'], properties: { command: { type: 'string' }, exit_code: { type: 'integer' } } } },
    defaults_taken: { type: 'array', items: { type: 'string' } },
    residuals: { type: 'array', items: { type: 'string' } },
  },
}

const WITNESS_SCHEMA = {
  type: 'object',
  required: ['verdicts', 'fabricated_coverage', 'verify_exit', 'verify_failures', 'oracle_weakened', 'gate_covered_after', 'residuals', 'standing_supported'],
  properties: {
    verdicts: { type: 'array', items: { type: 'object', required: ['operation_id', 'verdict'], properties: { operation_id: { type: 'string' }, verdict: { type: 'string', enum: ['reproduced', 'dissented', 'unattestable'] }, reason: { type: 'string' } } } },
    fabricated_coverage: { type: 'array', items: { type: 'string' } },
    oracle_weakened: { type: 'array', items: { type: 'string' } },
    verify_failures: { type: 'array', items: { type: 'string' } },
    verify_exit: { type: 'integer' },
    gate_covered_after: { type: 'integer' },
    residuals: { type: 'array', items: { type: 'string' } },
    judgement_queue: { type: 'array', items: { type: 'string' } },
    standing_supported: { type: 'string', enum: ['none', 'OPEN->BUILT', 'BUILT->WITNESSED'] },
  },
}

const SETTLE_SCHEMA = {
  type: 'object',
  required: ['action', 'head', 'tree_clean'],
  properties: {
    action: { type: 'string', enum: ['committed', 'reverted', 'nothing_to_settle'] },
    head: { type: 'string' },
    subject: { type: 'string' },
    tree_clean: { type: 'boolean' },
    note: { type: 'string' },
  },
}

// ---------------------------------------------------------------- prompts

const GROUND = 'You are working in the Soveraeign repository at ' + ROOT + '. This is a dedicated git '
  + 'worktree for an unattended overnight run; treat it as the whole world and never touch any other path. '
  + 'Read ' + ROOT + '/AGENTS.md and ' + ROOT + '/STATUS.yaml before a consequential change. '
  + 'Never run git push, never create or delete a branch, never touch lineage/evidence/, and never enable an '
  + 'external-world effect. Effect classes are RECORD_LOCAL or RESOURCE_CONSUMPTION only. '

const GATE_LAW = 'The milestone under work is ROADMAP.md F2, which exits when every normative predicate in '
  + 'SPEC.md carries a positive and a defeating fixture and the suite binds to more than one implementation. '
  + 'scripts/sov_f2_gate.py is the only reading of that gate that counts. A conformance case declares which '
  + 'predicates it covers in an optional "predicates" array in conformance/oracle-controls.json. '
  + 'THE CENTRAL RULE OF THIS RUN: a predicate id may be written into that array ONLY when the case genuinely '
  + 'exercises that predicate - the positive case would still PASS if the predicate held and the defeating '
  + 'case produces a real oracle defect BECAUSE that predicate is violated. Writing an id to move the counter '
  + 'is fabricated coverage. It is the single failure this run exists to avoid, it is worse than making no '
  + 'progress at all, and the witness is instructed to hunt for it. '

const ORACLE_LAW = 'AGENTS.md: never weaken an oracle merely to make a participant pass. Specifically, in this '
  + 'run you may NOT raise BUDGET_SECONDS in scripts/verify.py, delete or skip a failing test or check, relax '
  + 'an expected_oracle value, loosen a schema to admit a defeat, or edit a defeating fixture so it stops '
  + 'defeating. If a check fails, either fix the thing it caught or report it in residuals unchanged. '

const BUDGET_LAW = 'One known host residual, measured before this run started: this working tree is a git '
  + 'worktree whose filesystem runs the tooling test suite about 0.5s slower than the main checkout, so '
  + 'scripts/verify.py fails its 3.0s wall-clock budget here (about 3.13s) while all 23 of its checks pass. '
  + 'That is an artifact of the worktree, not a repository defect and not yours to fix. Treat a verify.py run '
  + 'whose ONLY failure line is the verification budget as semantically green: record it, do not repair it, and '
  + 'do not change BUDGET_SECONDS. Any other failure line is a real failure. Always report verify_failures as '
  + 'the exact list of "FAIL:" lines verify.py printed. '

function readPrompt(tick) {
  return GROUND + GATE_LAW + BUDGET_LAW
    + 'This is tick ' + tick + '. Observe only; change nothing. From ' + ROOT + ' run exactly these and record '
    + 'each real exit code yourself: (1) python scripts/sov_f2_gate.py --json --next 12, (2) python '
    + 'scripts/verify.py, (3) python scripts/lint.py, (4) python conformance/run.py, (5) git status --porcelain, '
    + '(6) git log --oneline -1. Return gate_closed, predicates_total, predicates_covered, bound_participants, '
    + 'the three exit codes, tree_clean (true when git status --porcelain printed nothing), head (the short '
    + 'commit hash), and open (the ranked open predicates the gate printed, id/family/text/missing). Put '
    + 'anything surprising in observations. Do not edit, fix, or commit anything.'
}

function planPrompt(read, tick) {
  const ranked = (read.open || []).slice(0, 8)
  return GROUND + GATE_LAW + ORACLE_LAW + BUDGET_LAW
    + 'This is tick ' + tick + '. You are the Orchestration tier: plan, do not build. The gate currently reads '
    + read.predicates_covered + '/' + read.predicates_total + ' predicates covered. The ranked open predicates '
    + 'are: ' + JSON.stringify(ranked) + '. '
    + 'Read ' + ROOT + '/SPEC.md (Requirement predicates, Transition contract, Interface parity, Conformance '
    + 'boundary), ' + ROOT + '/conformance/README.md, ' + ROOT + '/conformance/run.py and '
    + ROOT + '/conformance/oracle-controls.json before planning. '
    + 'Plan at most ' + PER_TICK + ' operations that each close one or more open predicates by authoring a real '
    + 'positive/defeating fixture pair and, where the oracle has no check that can see the predicate, extending '
    + 'conformance/run.py with one. Twenty cases already exist and declare no predicates: where an existing case '
    + 'genuinely exercises an open predicate, declaring that honestly is legitimate work - but only where the '
    + 'oracle check would actually catch the violation, and never as a substitute for a missing fixture. '
    + 'Operations must touch disjoint files so they can run concurrently. Name every file repo-relative. '
    + 'Blocked edge is not blocked frontier (AGENTS.md): an owner-held question gates one transition, not this '
    + 'tick. Take a reversible default for every other choice and list it in defaults_taken. Set blocked true '
    + 'only when no admissible operation exists against this gate at all. Each judgement_queue entry names an '
    + 'owner-held boundary and why no evidence at this tier could settle it - Bdo is asleep and will read them '
    + 'in the morning, so never wait on one.'
}

function buildPrompt(op, tick) {
  return GROUND + GATE_LAW + ORACLE_LAW + BUDGET_LAW
    + 'This is tick ' + tick + '. You are the Work tier. Execute exactly this one bounded operation and nothing '
    + 'else: [' + op.id + '] ' + op.description + '. Predicates it must genuinely close: '
    + (op.predicates || []).join(', ') + '. Expected files: ' + (op.files || []).join(', ') + '. Effect class: '
    + op.effect_class + '. Follow the AGENTS.md change protocol and implementation order: the contract and its '
    + 'positive and defeating fixture come before implementation code, make the smallest change that satisfies '
    + 'the visible case, keep modules under 300 lines, use LF endings and a final newline. '
    + 'Stay inside the files above. Do not run git commit, git add, git checkout, git clean, or git push - the '
    + 'controller settles this tick, not you. '
    + 'Then run, from ' + ROOT + ': python conformance/run.py, python scripts/sov_f2_gate.py, python '
    + 'scripts/verify.py and python scripts/lint.py, and record each exact command and real exit code in checks. '
    + 'If your change makes verify.py red and you cannot repair it inside your own files, say so in residuals '
    + 'rather than widening scope. Report predicates_claimed honestly: list only predicates whose violation your '
    + 'new fixture actually detects. Your output is a builder self-report and establishes BUILT evidence only; '
    + 'it cannot witness or ratify itself.'
}

function witnessPrompt(claims, read, tick) {
  return GROUND + GATE_LAW + ORACLE_LAW + BUDGET_LAW
    + 'This is tick ' + tick + '. You are the independent witness. You did not build this and a build report '
    + 'cannot witness itself, so consult the repository, never the builder\'s reasoning. Claimed operations: '
    + JSON.stringify(claims) + '. The gate read ' + read.predicates_covered + '/' + read.predicates_total
    + ' before this tick, at commit ' + (read.head || 'unknown') + '. '
    + 'Independently inspect the real diff (git diff HEAD, git status --porcelain, direct reads of the changed '
    + 'files) and check it against SPEC.md, conformance/README.md and AGENTS.md. Run, observing real exit codes '
    + 'yourself: python scripts/verify.py, python scripts/lint.py, python conformance/run.py, and python '
    + 'scripts/sov_f2_gate.py --json. '
    + 'YOUR PRIMARY JOB IS TO FIND FABRICATED COVERAGE. For every predicate id newly written into '
    + 'conformance/oracle-controls.json, read SPEC.md for what that predicate actually claims, then read the '
    + 'case data and the oracle check that grades it, and answer one question: would the oracle actually produce '
    + 'a defect if this predicate were violated? If not, or if you cannot tell, list that predicate id in '
    + 'fabricated_coverage. An empty fabricated_coverage list is a positive claim that you checked each one. '
    + 'Return a verdict per operation_id - reproduced (independently confirmed in the repository), dissented '
    + '(the evidence contradicts the claim), or unattestable (cannot be independently confirmed) - plus '
    + 'verify_exit, gate_covered_after (predicates_covered from the gate JSON), residuals and any judgement '
    + 'items. Also inspect the diff for any weakening of an oracle - a changed BUDGET_SECONDS, a deleted or '
    + 'skipped test, a relaxed expected_oracle, a loosened schema, a defeating fixture that no longer '
    + 'defeats - and list each one in oracle_weakened. Report verify_failures as the exact "FAIL:" lines. '
    + 'Set standing_supported to BUILT->WITNESSED only when every verdict is reproduced, '
    + 'fabricated_coverage and oracle_weakened are both empty, and verify.py failed nothing but its wall-clock budget. Otherwise none. Never RATIFIED: ratification is '
    + 'Bdo\'s alone. Do not edit, fix or commit anything - a witness that repairs what it observes has stopped '
    + 'being independent.'
}

function settlePrompt(decision, tick, summary) {
  const base = GROUND + 'This is tick ' + tick + '. You are the Control tier settling one tick. Do exactly the '
    + 'action named below from ' + ROOT + ' and nothing else. Never push. '
  if (decision === 'commit') {
    return base
      + 'The witness reproduced every claimed operation, found no fabricated coverage, and verify.py exited 0. '
      + 'Settle it: run git add -A, then commit with a subject line of at most 72 characters in the imperative '
      + 'mood naming what closed, and a body naming the predicates covered and the F2 gate counter before and '
      + 'after. Facts for the message: ' + summary + '. End the commit message with the trailer '
      + '"Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>". Then run git status --porcelain '
      + 'and git log --oneline -1 and report action=committed, the new short head, the subject you used, and '
      + 'tree_clean.'
  }
  return base
    + 'The witness did NOT reproduce this tick (' + summary + '). Roll the tree back to its last known-good '
    + 'commit so the next tick does not build on unwitnessed work: run git checkout -- . and then git clean -fd. '
    + 'This discards the tick\'s uncommitted changes, which is the intent - everything of value is already '
    + 'committed. Then run git status --porcelain and git log --oneline -1 and report action=reverted, the '
    + 'unchanged short head, and tree_clean. Put in note exactly which paths git clean removed.'
}

// ---------------------------------------------------------------- the loop

const ticks = []
let consecutiveUnsettled = 0
let consecutiveEmptyPlans = 0
let stopReason = 'tick cap reached'
let lastRead = null

for (let tick = 1; tick <= MAX_TICKS; tick++) {
  phase('Read')
  const read = await agent(readPrompt(tick), { agentType: 'sov-witness', schema: READ_SCHEMA, phase: 'Read', label: 't' + tick + ':read', effort: 'low' })

  if (!read) {
    log('tick ' + tick + ': the gate reader returned nothing; the loop cannot see the tree, stopping')
    stopReason = 'gate reader returned no result'
    break
  }
  lastRead = read

  log('tick ' + tick + ': gate ' + read.predicates_covered + '/' + read.predicates_total
    + ' covered, verify=' + read.verify_exit + ' lint=' + read.lint_exit + ' oracle=' + read.oracle_exit
    + ' head=' + (read.head || '?'))

  if (read.gate_closed) {
    log('F2 gate reads CLOSED at tick ' + tick + '; stopping as instructed')
    stopReason = 'F2 milestone gate closed'
    ticks.push({ tick: tick, gate: read.predicates_covered + '/' + read.predicates_total, outcome: 'gate closed' })
    break
  }

  if (!read.tree_clean) {
    log('tick ' + tick + ': the tree is dirty at the start of a tick; a previous settle did not finish')
  }

  phase('Plan')
  const plan = await agent(planPrompt(read, tick), { agentType: 'sov-orchestrator', schema: PLAN_SCHEMA, phase: 'Plan', label: 't' + tick + ':plan' })

  if (!plan || plan.blocked || !plan.operations || plan.operations.length === 0) {
    consecutiveEmptyPlans++
    const why = plan && plan.blocked_reason ? plan.blocked_reason : 'planner returned no operations'
    log('tick ' + tick + ': no admissible operation (' + why + ')')
    ticks.push({ tick: tick, gate: read.predicates_covered + '/' + read.predicates_total, outcome: 'no plan', reason: why, judgement_queue: plan ? plan.judgement_queue : [] })
    if (consecutiveEmptyPlans >= 2) {
      stopReason = 'two consecutive ticks found no admissible operation: ' + why
      break
    }
    continue
  }
  consecutiveEmptyPlans = 0

  phase('Build')
  const ops = plan.operations.slice(0, PER_TICK)
  log('tick ' + tick + ': building ' + ops.length + ' operation(s) over ' + ops.map(function (o) { return (o.predicates || []).join('/') }).join(' | '))

  const built = []
  for (let i = 0; i < ops.length; i++) {
    const result = await agent(buildPrompt(ops[i], tick), { agentType: 'sov-worker', schema: BUILD_SCHEMA, phase: 'Build', label: 't' + tick + ':build:' + ops[i].id })
    if (result) { built.push(result) }
  }

  if (built.length === 0) {
    consecutiveUnsettled++
    log('tick ' + tick + ': no builder reported; reverting so the next tick starts clean')
    await agent(settlePrompt('revert', tick, 'no builder returned a report'), { agentType: 'sov-controller', schema: SETTLE_SCHEMA, phase: 'Settle', label: 't' + tick + ':revert', effort: 'low' })
    ticks.push({ tick: tick, gate: read.predicates_covered + '/' + read.predicates_total, outcome: 'no build report' })
    if (consecutiveUnsettled >= 2) { stopReason = 'two consecutive ticks produced nothing witnessable'; break }
    continue
  }

  phase('Witness')
  const claims = built.map(function (b) { return { operation_id: b.operation_id, predicates_claimed: b.predicates_claimed || [], files_changed: b.files_changed } })
  const witness = await agent(witnessPrompt(claims, read, tick), { agentType: 'sov-witness', schema: WITNESS_SCHEMA, phase: 'Witness', label: 't' + tick + ':witness', effort: 'high' })

  const verdicts = witness && witness.verdicts ? witness.verdicts : []
  const allReproduced = verdicts.length > 0 && verdicts.every(function (v) { return v.verdict === 'reproduced' })
  const fabricated = witness && witness.fabricated_coverage ? witness.fabricated_coverage : []
  const tampered = witness && witness.oracle_weakened ? witness.oracle_weakened : []
  // Semantically green: either verify.py passed outright, or its only failure was the
  // wall-clock budget this worktree is known to miss for filesystem reasons alone.
  const failures = witness && witness.verify_failures ? witness.verify_failures : []
  const budgetOnly = failures.length > 0 && failures.every(function (f) { return /budget/i.test(f) })
  const verifyGreen = witness ? (witness.verify_exit === 0 || budgetOnly) : false
  const settleIt = !!witness && allReproduced && fabricated.length === 0 && tampered.length === 0 && verifyGreen

  if (tampered.length > 0) {
    log('tick ' + tick + ': WITNESS FOUND A WEAKENED ORACLE: ' + tampered.join(', ') + ' - reverting')
  }

  if (fabricated.length > 0) {
    log('tick ' + tick + ': WITNESS FOUND FABRICATED COVERAGE: ' + fabricated.join(', ') + ' - reverting')
  }

  phase('Settle')
  const summary = settleIt
    ? ('operations ' + built.map(function (b) { return b.operation_id }).join(', ')
       + '; predicates ' + built.map(function (b) { return (b.predicates_claimed || []).join('/') }).join(', ')
       + '; F2 gate ' + read.predicates_covered + ' -> ' + witness.gate_covered_after + ' of ' + read.predicates_total
       + '; witness reproduced every operation and found no fabricated coverage')
    : (!witness ? 'the witness returned no observation, so the tick is unattestable'
       : (fabricated.length > 0 ? 'fabricated coverage: ' + fabricated.join(', ')
          : (tampered.length > 0 ? 'a weakened oracle: ' + tampered.join(', ')
          : (!verifyGreen ? 'verify.py failed: ' + failures.join('; ')
             : 'verdicts: ' + verdicts.map(function (v) { return v.operation_id + '=' + v.verdict }).join(', ')))))

  const settled = await agent(settlePrompt(settleIt ? 'commit' : 'revert', tick, summary), { agentType: 'sov-controller', schema: SETTLE_SCHEMA, phase: 'Settle', label: 't' + tick + ':settle', effort: 'low' })

  if (settleIt) {
    consecutiveUnsettled = 0
  } else {
    consecutiveUnsettled++
  }

  ticks.push({
    tick: tick,
    gate_before: read.predicates_covered + '/' + read.predicates_total,
    gate_after: witness ? witness.gate_covered_after : null,
    operations: built.map(function (b) { return b.operation_id }),
    predicates: built.reduce(function (all, b) { return all.concat(b.predicates_claimed || []) }, []),
    verdicts: verdicts,
    fabricated_coverage: fabricated,
    oracle_weakened: tampered,
    verify_failures: failures,
    standing_supported: witness ? witness.standing_supported : null,
    settled: settled ? settled.action : 'settle agent returned nothing',
    head: settled ? settled.head : null,
    residuals: witness ? witness.residuals : [],
    defaults_taken: (plan.defaults_taken || []).concat(built.reduce(function (all, b) { return all.concat(b.defaults_taken || []) }, [])),
    judgement_queue: (plan.judgement_queue || []).concat(witness && witness.judgement_queue ? witness.judgement_queue : []),
  })

  log('tick ' + tick + ': ' + (settled ? settled.action : 'unsettled') + '; gate '
    + read.predicates_covered + ' -> ' + (witness ? witness.gate_covered_after : '?')
    + ' of ' + read.predicates_total)

  if (consecutiveUnsettled >= 2) {
    stopReason = 'two consecutive ticks failed to settle; stopping rather than building on unwitnessed work'
    break
  }
}

// ---------------------------------------------------------------- report

phase('Settle')

const committed = ticks.filter(function (t) { return t.settled === 'committed' })
const reverted = ticks.filter(function (t) { return t.settled === 'reverted' })
const judgement = ticks.reduce(function (all, t) { return all.concat(t.judgement_queue || []) }, [])
const defaults = ticks.reduce(function (all, t) { return all.concat(t.defaults_taken || []) }, [])
const residuals = ticks.reduce(function (all, t) { return all.concat(t.residuals || []) }, [])
const fabricated = ticks.reduce(function (all, t) { return all.concat(t.fabricated_coverage || []) }, [])
const tamperedAll = ticks.reduce(function (all, t) { return all.concat(t.oracle_weakened || []) }, [])

log('Loop finished after ' + ticks.length + ' tick(s): ' + committed.length + ' committed, '
  + reverted.length + ' reverted. Stop reason: ' + stopReason)

return {
  milestone: 'F2',
  root: ROOT,
  stop_reason: stopReason,
  ticks_run: ticks.length,
  ticks_committed: committed.length,
  ticks_reverted: reverted.length,
  gate_first: ticks.length ? (ticks[0].gate_before || ticks[0].gate) : null,
  gate_last: lastRead ? (lastRead.predicates_covered + '/' + lastRead.predicates_total) : null,
  fabricated_coverage_caught: fabricated,
  weakened_oracles_caught: tamperedAll,
  defaults_taken: defaults,
  residuals: residuals,
  judgement_queue: judgement,
  ticks: ticks,
}
