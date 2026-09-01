#!/usr/bin/env python3
"""Repair pre-opening commissioning evidence envelopes without opening Phase 1.5."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"expected source block missing in {path}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


workflow = ROOT / ".claude/workflows/sov-loop.js"
text = workflow.read_text(encoding="utf-8")

start = text.index("// Harness projections of contracts/finding.schema.json.")
end = text.index("\nconst LAND = {", start)
new_schemas = r'''// Harness shape of contracts/finding.schema.json. A review result is an
// envelope around a real Finding, not a weakened Finding used to represent a
// missing projection. UNATTESTABLE therefore has no `finding` member.
const FINDING = {
  type: 'object',
  required: ['finding_schema', 'finding_id', 'subject', 'evaluator', 'scope',
             'record_projection_id', 'claims', 'evidence_addresses',
             'counterevidence_addresses', 'input_finding_ids', 'created_at',
             'frozen_at', 'authority_effect', 'settlement_effect', 'supersedes'],
  properties: {
    finding_schema: { type: 'string' },
    finding_id: { type: 'string' },
    subject: { type: 'object', required: ['kind', 'address'], properties: {
      kind: { type: 'string' }, address: { type: 'string' },
    } },
    evaluator: { type: 'object', required: ['principal_id', 'relation'], properties: {
      principal_id: { type: 'string' }, relation: { type: 'string' },
    } },
    scope: { type: 'object' },
    record_projection_id: { type: 'string' },
    claims: { type: 'array', items: { type: 'object', required: ['claim_id', 'verdict', 'detail'], properties: {
      claim_id: { type: 'string' }, verdict: { type: 'string' }, detail: { type: 'string' },
    } } },
    evidence_addresses: { type: 'array', items: { type: 'string' } },
    counterevidence_addresses: { type: 'array', items: { type: 'string' } },
    input_finding_ids: { type: 'array', items: { type: 'string' } },
    created_at: { type: 'string' },
    frozen_at: { type: 'string' },
    authority_effect: { type: 'string' },
    settlement_effect: { type: 'string' },
    supersedes: { type: 'array', items: { type: 'string' } },
  },
}

const REVIEW_RESULT = {
  type: 'object',
  required: ['concern_id', 'status'],
  properties: {
    concern_id: { type: 'string' },
    status: { type: 'string' },
    projection_as_of: { type: 'string' },
    finding: FINDING,
    defect: { type: 'string' },
    observation_file: { type: 'string' },
  },
}

// This is deliberately a comparison envelope, not a Finding. A valid
// FINDING_SET Finding needs its own real RecordProjection over durably recorded
// input Findings; pre-opening rehearsal must not invent that projection.
const COMPARISON = {
  type: 'object',
  required: ['status', 'classifications', 'input_finding_ids', 'authority_effect',
             'settlement_effect', 'detail'],
  properties: {
    status: { type: 'string' },
    classifications: { type: 'array', items: { type: 'string' } },
    input_finding_ids: { type: 'array', items: { type: 'string' } },
    authority_effect: { type: 'string' },
    settlement_effect: { type: 'string' },
    detail: { type: 'string' },
  },
}

const BAD_PROJECTION_IDS = ['NONE', 'UNAVAILABLE', 'MISSING']
function frozenFinding(result, subjectKind) {
  const finding = result && result.status === 'FINDING' ? result.finding : null
  return !!(finding && finding.finding_schema === 'soveraeign-finding/v1'
    && finding.subject && finding.subject.kind === subjectKind
    && finding.record_projection_id
    && BAD_PROJECTION_IDS.indexOf(finding.record_projection_id) === -1
    && finding.frozen_at && finding.authority_effect === 'NONE'
    && finding.settlement_effect === 'NONE')
}
function claimsConfirmed(result) {
  const claims = result && result.finding && Array.isArray(result.finding.claims)
    ? result.finding.claims : []
  return claims.length > 0 && claims.every(function (claim) { return claim.verdict === 'CONFIRMED' })
}
'''
text = text[:start] + new_schemas + text[end:]

start = text.index("let orchestrationFinding = null")
end = text.index("\nphase('Land')", start)
new_review = r'''let orchestrationReview = null
if (evidenceMode) {
  phase('Orchestrator Review')
  invocations += 1
  orchestrationReview = await agent(
    'You are in REVIEW mode under concern ' + selected.concern_id + ', not PLAN mode. Judge PARTICIPANT_IN_WORK for the bounded assignment ' + plan.operation + '. Preserve the concern id. ' +
    'Use contracts/record-projection.schema.json and contracts/finding.schema.json. Reconstruct a scoped RecordProjection through the Record service for the assignment/participant-in-work subject and your evaluator relation. ' +
    'Judge assignment, authority, scope, repair, disclosure, and terminal fidelity only; do not judge implementation correctness. Do not read or anticipate the Witness conclusion. ' +
    'If a real projection with cited Record addresses exists, return status FINDING plus projection_as_of and a fully contract-compatible frozen Finding: finding_schema soveraeign-finding/v1; subject PARTICIPANT_IN_WORK; real evaluator principal/relation; scope; real record_projection_id; claims; evidence/counterevidence; input_finding_ids; created_at/frozen_at; authority_effect NONE; settlement_effect NONE; supersedes. ' +
    'If the needed Record projection or material evidence cannot be reconstructed, return status UNATTESTABLE and a concrete defect, with NO finding object. Never use NONE, UNAVAILABLE, MISSING, an invented id, worker prose, or memory to satisfy record_projection_id.',
    { agentType: 'sov-orchestrator', schema: REVIEW_RESULT, phase: 'Orchestrator Review', label: 'review:' + selected.domain })
  if (!orchestrationReview || orchestrationReview.concern_id !== selected.concern_id) {
    return { error: 'orchestrator review returned no concern-safe envelope', concern: selected, build: built }
  }
  if (orchestrationReview.status === 'FINDING' && !frozenFinding(orchestrationReview, 'PARTICIPANT_IN_WORK')) {
    return { error: 'orchestrator labelled a malformed or projectionless value as a Finding', concern: selected }
  }
  if (orchestrationReview.status !== 'FINDING' &&
      (orchestrationReview.status !== 'UNATTESTABLE' || !orchestrationReview.defect)) {
    return { error: 'orchestrator review must be FINDING or explicit UNATTESTABLE', concern: selected }
  }
}

let witnessed = null
if (evidenceMode) {
  phase('Witness Review')
  invocations += 1
  const cutoffInstruction = frozenFinding(orchestrationReview, 'PARTICIPANT_IN_WORK')
    ? 'Use this exact shared Record cutoff: ' + orchestrationReview.projection_as_of + '. The cutoff is projection metadata, not the Orchestrator conclusion. '
    : 'No common cutoff was supplied. Establish an exact Record cutoff yourself before writing any observation; comparison will remain a Record defect unless both real Findings exist. '
  witnessed = await agent(
    'You are the independent evaluator of WORK under concern ' + selected.concern_id + '. Concern: ' + selected.concern + '. Operation: ' + plan.operation + '. Preserve the concern id; independence comes from evaluator/session relation, not changing the concern. ' +
    'Use contracts/record-projection.schema.json and contracts/finding.schema.json. Inspect the exact repository state and governing contract/fixtures yourself. ' + cutoffInstruction +
    'Do not read the worker conclusion, Orchestrator Finding, or Controller expectation before freezing your own result. Builder paths may locate the work but are not evidence. ' +
    'If a real WORK RecordProjection exists, freeze a fully contract-compatible Finding first, then write your independent observation JSON under reports/observations/; the observation write occurs after the Finding is frozen so it cannot enter its own evidence basis. Return status FINDING, projection_as_of, finding, and observation_file. ' +
    'If the projection/evidence cannot be reconstructed, write an observation that reports the work UNATTESTABLE, then return status UNATTESTABLE, the concrete Record defect, and observation_file with NO finding object. Never invent a projection id or substitute prose for Record evidence.',
    { agentType: 'sov-witness', schema: REVIEW_RESULT, phase: 'Witness Review', label: 'witness-review:' + selected.domain })
} else {
  phase('Witness')
  invocations += 1
  witnessed = await agent(
    'You are the independent observation for work you did not do and must not touch. Concern id: ' + selected.concern_id + '. Concern: ' + selected.concern + '. Preserve the concern id while keeping an independent session/evaluator relation. ' +
    'The builder reports it changed: ' + (built.changed_paths || []).join(', ') + '. Treat that as a claim, not evidence. ' +
    'Read git status and git diff yourself, read the owning contract and the defeating fixture, and run python scripts/verify.py and python scripts/lint.py observing the real exit codes. ' +
    'Confirm the defeating case actually fails as declared; a fixture that passes when it should fail is a DISSENTED verdict, not a residual. ' +
    'Then write your observation to reports/observations/ as JSON with exactly these fields: observer_id (your agent label), contributed_to_build (false - and if that is not true, say so and set verdict DISSENTED), verdict (CONFIRMED or DISSENTED), concern, and checks. ' +
    'You must not edit, fix, build, or commit anything outside that one observation file. ' +
    'Return concern_id, verdict, what you independently confirmed, residuals, the path you wrote the observation to, and any judgement items only Bdo can settle.',
    { agentType: 'sov-witness', schema: WITNESS, phase: 'Witness', label: 'witness:' + selected.domain })
}

if (!witnessed) {
  return { error: 'witness returned no observation; nothing may land unwitnessed', concern: selected, build: built }
}
if (witnessed.concern_id !== selected.concern_id) {
  return { error: 'witness changed the work concern instead of independently evaluating it', expected: selected.concern_id, observed: witnessed.concern_id }
}
if (evidenceMode && witnessed.status === 'FINDING' && !frozenFinding(witnessed, 'WORK')) {
  return { error: 'witness labelled a malformed or projectionless value as a Finding', concern: selected }
}
if (evidenceMode && witnessed.status !== 'FINDING' &&
    (witnessed.status !== 'UNATTESTABLE' || !witnessed.defect)) {
  return { error: 'witness review must be FINDING or explicit UNATTESTABLE', concern: selected }
}
log('Witness: ' + (evidenceMode ? witnessed.status : witnessed.verdict))

let comparison = null
if (evidenceMode) {
  const haveParticipantFinding = frozenFinding(orchestrationReview, 'PARTICIPANT_IN_WORK')
  const haveWorkFinding = frozenFinding(witnessed, 'WORK')
  if (haveParticipantFinding && haveWorkFinding) {
    phase('Compare')
    invocations += 1
    comparison = await agent(
      'Compare these two already-frozen Findings. You do not witness, ratify, settle, average, or rewrite them. Preserve both subjects, input ids, and citations. ' +
      'Participant-in-work Finding: ' + JSON.stringify(orchestrationReview.finding) + '. WORK Finding: ' + JSON.stringify(witnessed.finding) + '. ' +
      'Use only these classifications: NO_CONFLICT, EVIDENCE_DIFFERENCE, INTERPRETATION_DIFFERENCE, WORK_DEFECT, WORKER_DEFECT, ORCHESTRATION_DEFECT, WITNESS_DEFECT, RECORD_DEFECT, POLICY_SEAM. ' +
      'Return status CLASSIFIED; both finding ids as input_finding_ids; authority_effect NONE; settlement_effect NONE; classifications; and concise evidence-based detail. This comparison envelope is not itself a Finding because this pre-opening workflow has no durable RecordProjection over the Finding set.',
      { agentType: 'sov-controller', schema: COMPARISON, phase: 'Compare', label: 'compare:' + selected.domain })
  } else {
    const ids = []
    if (haveParticipantFinding) ids.push(orchestrationReview.finding.finding_id)
    if (haveWorkFinding) ids.push(witnessed.finding.finding_id)
    comparison = {
      status: 'UNATTESTABLE', classifications: ['RECORD_DEFECT'], input_finding_ids: ids,
      authority_effect: 'NONE', settlement_effect: 'NONE',
      detail: 'Comparison requires two real frozen Findings backed by real Record projections; at least one review is UNATTESTABLE.',
    }
  }
}
'''
text = text[:start] + new_review + text[end:]

old_land = r'''phase('Land')
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
'''
new_land = r'''phase('Land')
const evidenceReviewsConfirmed = !evidenceMode || (
  frozenFinding(orchestrationReview, 'PARTICIPANT_IN_WORK') && claimsConfirmed(orchestrationReview)
  && frozenFinding(witnessed, 'WORK') && claimsConfirmed(witnessed))
const comparisonBlocks = evidenceMode && (!comparison || comparison.status !== 'CLASSIFIED'
  || (comparison.classifications || []).length !== 1
  || comparison.classifications[0] !== 'NO_CONFLICT')
const witnessConfirmed = evidenceMode
  ? (evidenceReviewsConfirmed && !!witnessed.observation_file)
  : witnessed.verdict === 'CONFIRMED'
const mode = planOnly || !selected.in_grant_scope || !witnessConfirmed || comparisonBlocks ? 'plan' : 'land'
if (mode === 'plan') {
  const reason = planOnly ? 'plan_only was set'
    : (!selected.in_grant_scope ? 'concern is outside the grant'
      : (comparisonBlocks ? 'evidence comparison is not one classified NO_CONFLICT'
        : (!evidenceReviewsConfirmed ? 'one evidence review lacks a confirmed real Finding'
          : 'independent observation is missing or unconfirmed')))
  log('Rehearsing the gate only: ' + reason)
}

const pathArgs = (built.changed_paths || []).map(function (p) { return '--path ' + p }).join(' ')
const observationArg = witnessed.observation_file ? ' --observation ' + witnessed.observation_file : ''
invocations += 1
const landed = await agent(
  'Run the landing gate and report exactly what it said. You did not build this change and you do not decide whether it lands; the gate does. '
  + 'Run this command from the repository root and nothing else that writes:\n\n'
  + '  python scripts/sov_land.py ' + mode + ' ' + pathArgs
  + observationArg
  + ' --target ' + target
'''
if old_land not in text:
    raise SystemExit("landing block missing")
text = text.replace(old_land, new_land, 1)
text = text.replace(
    "  orchestration_finding: orchestrationFinding,\n",
    "  orchestration_review: orchestrationReview,\n  orchestration_finding: orchestrationReview && orchestrationReview.finding ? orchestrationReview.finding : null,\n",
    1,
)
workflow.write_text(text, encoding="utf-8", newline="\n")

replace(
    ".claude/agents/sov-orchestrator.md",
    """- Cite only Record addresses available through that projection. If material\n  evidence is absent, return `UNATTESTABLE`; do not fill the gap from the worker's\n  prose or your own memory.\n- Freeze the resulting `Finding` before any Witness conclusion is shown to you.\n""",
    """- Cite only Record addresses available through that projection. If the projection\n  itself or material evidence cannot be reconstructed, return a review envelope\n  with `status: UNATTESTABLE` and the concrete Record defect, **without a\n  `Finding` object**. Do not put `NONE`, `UNAVAILABLE`, `MISSING`, invented ids,\n  worker prose, or memory into `record_projection_id`.\n- Only when a real projection exists may you freeze the resulting `Finding` before\n  any Witness conclusion is shown to you.\n""",
)
replace(
    ".claude/agents/sov-orchestrator.md",
    """In REVIEW mode output the frozen `Finding` over `PARTICIPANT_IN_WORK` instead; do\nnot combine the two subjects into one judgement.\n""",
    """In REVIEW mode output a `FINDING | UNATTESTABLE` review envelope. `FINDING`\ncontains the frozen contract-compatible Finding over `PARTICIPANT_IN_WORK`;\n`UNATTESTABLE` contains the Record defect and no Finding. Do not combine the two\nsubjects into one judgement.\n""",
)

replace(
    ".claude/agents/sov-witness.md",
    "tools: Read, Grep, Glob, Bash, PowerShell\n",
    "tools: Read, Grep, Glob, Bash, PowerShell, Write\n",
)
replace(
    ".claude/agents/sov-witness.md",
    """Your evaluative output is a `Finding` whose subject is `WORK`. Every cited Record\naddress must be present in the supplied/reconstructed `RecordProjection` at the\ndeclared cutoff. If the projection cannot be reconstructed, the cutoff moved, or\nmaterial evidence is unavailable, the correct verdict is `UNATTESTABLE`; surface\nthat as a Record defect rather than accepting persuasive prose. Freeze the Finding\nbefore any participant-in-work Finding is disclosed. Observation records remain\nobservations; the Finding interprets them and grants no authority or settlement.\n""",
    """Your evaluative result is a `FINDING | UNATTESTABLE` review envelope. A\n`FINDING` contains a contract-compatible `Finding` whose subject is `WORK`; every\ncited Record address must be present in the supplied/reconstructed\n`RecordProjection` at the declared cutoff. If the projection cannot be\nreconstructed, the cutoff moved, or material evidence is unavailable, return\n`UNATTESTABLE` with the concrete Record defect and **no Finding**. Never invent a\nprojection id to satisfy the schema.\n\nFreeze a real Finding before any participant-in-work Finding is disclosed and\nbefore you emit your observation record. The only file you may write is your own\n`reports/observations/*.json` observation after the independent reading/freeze;\nyou may not edit the work, fixtures, contracts, or implementation. Observation\nrecords remain observations; a Finding interprets evidence and grants no authority\nor settlement.\n""",
)

replace(
    ".claude/agents/sov-controller.md",
    """A comparison consumes frozen Findings and the exact Record projections/citations\nthey name. It is itself a `Finding` over a `FINDING_SET`, not a ratification. Keep\n`WORK` and `PARTICIPANT_IN_WORK` separate and preserve both inputs unchanged.\nClassify what the evidence establishes using only: `NO_CONFLICT`,\n""",
    """A comparison consumes two **real** frozen Findings and the exact Record\nprojections/citations they name. If either review is `UNATTESTABLE`, classify the\nmissing basis as `RECORD_DEFECT` outside a Finding; never manufacture a placeholder\nFinding to make comparison possible. Keep `WORK` and `PARTICIPANT_IN_WORK`\nseparate and preserve both inputs unchanged.\n\nA valid comparison `Finding` over a `FINDING_SET` requires the input Findings to\nbe durably recorded and a real RecordProjection over that set. The pre-opening\n`sov-loop` evidence rehearsal does not yet have that durable step, so its Controller\noutput is explicitly a non-authoritative comparison envelope rather than a fake\nFinding. Once the durable basis exists, the same classification may be expressed\nas a `FINDING_SET` Finding. Classify what the evidence establishes using only:\n`NO_CONFLICT`,\n""",
)

replace(
    ".claude/README.md",
    """- `agents/sov-witness.md` — stable read-only witness; independently evaluates\n  `WORK` from a scoped Record projection, freezes its Finding before comparison,\n  and may dissent or report the evidence unattestable.\n""",
    """- `agents/sov-witness.md` — stable witness, read-only over the work itself; it\n  independently evaluates `WORK` from a scoped Record projection, freezes a real\n  Finding before comparison, and may write only its own observation record after\n  that freeze. Missing projection/evidence returns an `UNATTESTABLE` envelope with\n  no placeholder Finding.\n""",
)
replace(
    ".claude/README.md",
    """  inserts Orchestrator Review (`PARTICIPANT_IN_WORK`) and independent Witness\n  Review (`WORK`), freezes both Findings, then lets Controller Compare before the\n  landing gate. Missing Record evidence keeps that rehearsal in plan mode rather\n  than fabricating proof. The Land phase runs `python scripts/sov_land.py`, the only place in\n""",
    """  inserts Orchestrator Review (`PARTICIPANT_IN_WORK`) and independent Witness\n  Review (`WORK`). Each returns a `FINDING | UNATTESTABLE` envelope; only real\n  projection-backed Findings are compared. Missing Record evidence yields\n  `RECORD_DEFECT` and keeps the run in plan mode—there is no sentinel projection\n  id and no placeholder Finding. Controller Compare is a non-authoritative\n  classification envelope until the input Findings themselves are durably recorded\n  and projected, at which point Phase 1.5 can earn a real `FINDING_SET` Finding.\n  The Land phase runs `python scripts/sov_land.py`, the only place in\n""",
)

# Opening readiness should prove the rehearsal fails honestly when evidence is absent.
replace(
    "scripts/sov_opening_readiness.py",
    """        "sov_context_order": _has(root / "SOV.md", "**Phase authority.**",\n                                  "**Assigned work.**", "`RecordProjection`",\n                                  "**Operation.**"),\n""",
    """        "sov_context_order": _has(root / "SOV.md", "**Phase authority.**",\n                                  "**Assigned work.**", "`RecordProjection`",\n                                  "**Operation.**"),\n        "evidence_review_envelopes": _has(root / ".claude/workflows/sov-loop.js",\n                                          "const REVIEW_RESULT",\n                                          "status: 'UNATTESTABLE'",\n                                          "BAD_PROJECTION_IDS",\n                                          "comparison envelope is not itself a Finding"),\n""",
)

# Source-contract tests protect the exact safety property without pretending to
# execute the external agent harness in repository CI.
test = ROOT / "scripts/tests/test_commissioning_evidence_workflow.py"
test.write_text(r'''"""Defeating checks for the prepared commissioning evidence workflow."""

from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".claude/workflows/sov-loop.js"


class FindingContract(unittest.TestCase):
    def test_workflow_names_every_required_finding_field(self) -> None:
        schema = json.loads((ROOT / "contracts/finding.schema.json").read_text(encoding="utf-8"))
        text = WORKFLOW.read_text(encoding="utf-8")
        for field in schema["required"]:
            self.assertIn(field, text, field)

    def test_missing_projection_is_envelope_not_fake_finding(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("const REVIEW_RESULT", text)
        self.assertIn("status: 'UNATTESTABLE'", text)
        self.assertIn("BAD_PROJECTION_IDS = ['NONE', 'UNAVAILABLE', 'MISSING']", text)
        self.assertNotIn("record_projection_id NONE", text)
        self.assertNotIn("record_projection_id: 'NONE'", text)
        self.assertNotIn("record_projection_id: \"NONE\"", text)

    def test_comparison_requires_two_real_frozen_findings(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("haveParticipantFinding && haveWorkFinding", text)
        self.assertIn("classifications: ['RECORD_DEFECT']", text)
        self.assertIn("comparison envelope is not itself a Finding", text)
        self.assertIn("input_finding_ids", text)

    def test_evidence_landing_requires_confirmed_findings_and_observation(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("evidenceReviewsConfirmed", text)
        self.assertIn("claimsConfirmed(orchestrationReview)", text)
        self.assertIn("claimsConfirmed(witnessed)", text)
        self.assertIn("!!witnessed.observation_file", text)
        self.assertIn("const observationArg = witnessed.observation_file", text)
        self.assertNotIn("witnessed.observation_file || 'MISSING'", text)


class RoleContracts(unittest.TestCase):
    def test_orchestrator_refuses_placeholder_finding(self) -> None:
        text = (ROOT / ".claude/agents/sov-orchestrator.md").read_text(encoding="utf-8")
        self.assertIn("without a `Finding` object", text)
        self.assertIn("invented ids", text)

    def test_witness_freezes_before_observation_write(self) -> None:
        text = (ROOT / ".claude/agents/sov-witness.md").read_text(encoding="utf-8")
        self.assertIn("Freeze a real Finding", text)
        self.assertIn("before you emit your observation record", text)
        self.assertIn("reports/observations/*.json", text)

    def test_controller_does_not_promote_missing_basis(self) -> None:
        text = (ROOT / ".claude/agents/sov-controller.md").read_text(encoding="utf-8")
        self.assertIn("RECORD_DEFECT", text)
        self.assertIn("never manufacture a placeholder", text)
        self.assertIn("non-authoritative comparison envelope", text)


if __name__ == "__main__":
    unittest.main()
''', encoding="utf-8", newline="\n")
