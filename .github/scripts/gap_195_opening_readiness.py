from __future__ import annotations

from pathlib import Path
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SELF = ROOT / ".github" / "scripts" / "gap_195_opening_readiness.py"
WORKFLOW = ROOT / ".github" / "workflows" / "gap-195-opening-readiness.yml"


def run(*args: str, capture: bool = False) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, cwd=ROOT, text=True, capture_output=capture, check=False)
    if result.returncode:
        if capture:
            print(result.stdout)
            print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)
    return result


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise SystemExit(f"expected text absent in {path.relative_to(ROOT)}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


def insert_before(path: Path, anchor: str, addition: str) -> None:
    text = path.read_text(encoding="utf-8")
    if addition.strip() in text:
        return
    if anchor not in text:
        raise SystemExit(f"anchor absent in {path.relative_to(ROOT)}: {anchor!r}")
    path.write_text(text.replace(anchor, addition + anchor, 1), encoding="utf-8", newline="\n")


def assert_preopen() -> None:
    status = (ROOT / "STATUS.yaml").read_text(encoding="utf-8")
    phases = json.loads((ROOT / "contracts/phases.json").read_text(encoding="utf-8"))
    if "phase: NONE_ACTIVE" not in status:
        raise SystemExit("refuse: successor already active")
    if any(item.get("execution_status") == "OPEN" for item in phases.get("phases", [])):
        raise SystemExit("refuse: phase registry already contains an open phase")
    if any(item.get("phase_id") == "phase:1-5" for item in phases.get("phases", [])):
        raise SystemExit("refuse: phase:1-5 already exists in the phase registry")


def patch_roles() -> None:
    worker = ROOT / ".claude/agents/sov-worker.md"
    replace_once(
        worker,
        "  expected observable result; effect class (`RECORD_LOCAL` or\n  `RESOURCE_CONSUMPTION` only—`EXTERNAL_WORLD` is forbidden in Phase I); and\n  the rollback or refusal boundary.\n",
        "  expected observable result; the effect class admitted by the current phase and\n  live grant (never inferred from the Work role); and the rollback or refusal\n  boundary. `EXTERNAL_WORLD` requires explicit governing authority rather than a\n  role-name exception.\n",
    )
    insert_before(
        worker,
        "Report format:",
        """## Evidence handoff\n\nWhen the assignment names a `RecordProjection`, use it as context, never as\nauthority. Report the stable work/assignment subject you carried and every Record\naddress your operation emitted or relied on. Do not turn your report into a\n`Finding` about your own work: a later evaluator must form that judgement from a\nseparately reconstructed projection. Missing Record evidence is a residual to\ndisclose, not evidence you may reconstruct from memory.\n\n""",
    )

    orchestrator = ROOT / ".claude/agents/sov-orchestrator.md"
    replace_once(
        orchestrator,
        "  observations, and blockers. It plans and sequences; it does not build,\n  witness, or dispatch workflows.\n",
        "  observations, and blockers. It plans and sequences; after work, REVIEW mode\n  may evaluate how the participant carried the assignment. It does not build,\n  witness the work, settle, or dispatch workflows.\n",
    )
    replace_once(
        orchestrator,
        "  effect class (`RECORD_LOCAL` or `RESOURCE_CONSUMPTION`; `EXTERNAL_WORLD` is\n  forbidden in Phase I), and an observable completion condition.\n",
        "  effect class admitted by the current phase and live grant, and an observable\n  completion condition. A role name never widens the effect envelope.\n",
    )
    insert_before(
        orchestrator,
        "Output: the operation plan",
        """## REVIEW mode — participant-in-work\n\nWhen explicitly invoked after execution, do not re-plan and do not witness the\nresult. Your subject is `PARTICIPANT_IN_WORK`: whether the participant carried the\nassignment within its scope and authority, absorbed ordinary repair, disclosed\nhelpers/deviations/failures, and reached the declared terminal.\n\n- Receive or reconstruct the scoped `RecordProjection` for that assignment and\n  your evaluator relation. A projection is a bounded reading of common Record,\n  never private worker history and never authority.\n- Cite only Record addresses available through that projection. If material\n  evidence is absent, return `UNATTESTABLE`; do not fill the gap from the worker's\n  prose or your own memory.\n- Freeze the resulting `Finding` before any Witness conclusion is shown to you.\n  The Finding must name subject, evaluator relation, scope, projection id,\n  evidence/counterevidence, verdict, and `frozen_at`.\n- You are judging assignment fidelity, not whether the implementation is\n  technically correct. That remains the independent Witness's subject.\n\n""",
    )
    replace_once(
        orchestrator,
        "Output: the operation plan (identifier, description, files, effect class,\ncompletion observation, and ordering constraints), the defaults taken and\nwhy, a blocked flag only when no admissible operation exists for the\nobjective, and a judgement queue whose entries each name the transition they\ngate.\n",
        "Output in PLAN mode: the operation plan (identifier, description, files, effect\nclass, completion observation, and ordering constraints), defaults taken and why,\na blocked flag only when no admissible operation exists, and a judgement queue.\nIn REVIEW mode output the frozen `Finding` over `PARTICIPANT_IN_WORK` instead; do\nnot combine the two subjects into one judgement.\n",
    )

    witness = ROOT / ".claude/agents/sov-witness.md"
    replace_once(
        witness,
        "  Independent witness for Soveraeign domain work. Use it after a builder report\n  to verify claims through an independent path, run repository and conformance\n",
        "  Independent witness for Soveraeign domain work. Use it after a work subject\n  is ready to verify observable claims through an independent path, run repository\n  and conformance\n",
    )
    replace_once(
        witness,
        "1. Read the claim you were handed: what was reportedly done, which files, which\n   contracts and fixtures it touches.\n2. Read the actual changed files. Compare against the owning contract in\n",
        "1. Establish the `WORK` subject, exact revision, governing contract/fixtures, and\n   supplied `RecordProjection`. Builder-provided paths may locate the subject but\n   builder conclusions are not evidence. Do not read an Orchestrator or Controller\n   evaluative conclusion before your own Finding freezes.\n2. Read the actual changed files. Compare against the owning contract in\n",
    )
    insert_before(
        witness,
        "## Report format",
        """## Finding discipline\n\nYour evaluative output is a `Finding` whose subject is `WORK`. Every cited Record\naddress must be present in the supplied/reconstructed `RecordProjection` at the\ndeclared cutoff. If the projection cannot be reconstructed, the cutoff moved, or\nmaterial evidence is unavailable, the correct verdict is `UNATTESTABLE`; surface\nthat as a Record defect rather than accepting persuasive prose. Freeze the Finding\nbefore any participant-in-work Finding is disclosed. Observation records remain\nobservations; the Finding interprets them and grants no authority or settlement.\n\n""",
    )

    controller = ROOT / ".claude/agents/sov-controller.md"
    replace_once(
        controller,
        "- If two domain reports conflict, record the conflict as a seam; do not pick\n  a winner.\n",
        "- Never pick a winner by confidence, role, majority, or prose quality. When two\n  independently frozen Findings are presented, compare their cited bases and\n  subjects. Classification is allowed; arbitrary preference is not.\n",
    )
    insert_before(
        controller,
        "Completion report:",
        """## Comparing frozen Findings\n\nA comparison consumes frozen Findings and the exact Record projections/citations\nthey name. It is itself a `Finding` over a `FINDING_SET`, not a ratification. Keep\n`WORK` and `PARTICIPANT_IN_WORK` separate and preserve both inputs unchanged.\nClassify what the evidence establishes using only: `NO_CONFLICT`,\n`EVIDENCE_DIFFERENCE`, `INTERPRETATION_DIFFERENCE`, `WORK_DEFECT`,\n`WORKER_DEFECT`, `ORCHESTRATION_DEFECT`, `WITNESS_DEFECT`, `RECORD_DEFECT`, or\n`POLICY_SEAM`. Missing or unreconstructable evidence is `RECORD_DEFECT`; an\nactually undefined governing choice is `POLICY_SEAM`. Only the latter necessarily\nneeds owner judgement. Settle nothing beyond authority you independently hold.\n\n""",
    )


def patch_loop() -> None:
    path = ROOT / ".claude/workflows/sov-loop.js"
    text = path.read_text(encoding="utf-8")
    old_phases = """  phases: [\n    { title: 'Select', detail: 'controller names the one concern and its scope' },\n    { title: 'Plan', detail: 'orchestrator turns it into one bounded operation' },\n    { title: 'Build', detail: 'worker executes it and reports the paths it changed' },\n    { title: 'Witness', detail: 'an independent witness that did not build observes the result' },\n    { title: 'Land', detail: 'the landing gate grades the request against the standing grant' },\n  ],\n"""
    new_phases = """  phases: [\n    { title: 'Select', detail: 'controller names the one concern and its scope' },\n    { title: 'Plan', detail: 'orchestrator turns it into one bounded operation' },\n    { title: 'Build', detail: 'worker executes it and reports the paths it changed' },\n    { title: 'Orchestrator Review', detail: 'evidence mode forms a frozen participant-in-work Finding' },\n    { title: 'Witness Review', detail: 'independent evidence mode forms a frozen WORK Finding' },\n    { title: 'Compare', detail: 'controller compares frozen cited Findings without ratifying them' },\n    { title: 'Land', detail: 'the landing gate grades the request against the standing grant' },\n  ],\n"""
    if new_phases not in text:
        if old_phases not in text:
            raise SystemExit("sov-loop phase list anchor absent")
        text = text.replace(old_phases, new_phases, 1)
    text = text.replace(
        "// args: { objective: string, domain?: string, target?: string, plan_only?: boolean }",
        "// args: { objective: string, domain?: string, target?: string, plan_only?: boolean, evidence_mode?: boolean }",
        1,
    )
    text = text.replace(
        "const planOnly = !!(args && args.plan_only)\n",
        "const planOnly = !!(args && args.plan_only)\nconst evidenceMode = !!(args && args.evidence_mode)\n",
        1,
    )
    schema_anchor = "const LAND = {\n"
    if "const FROZEN_FINDING = {" not in text:
        schema = """// Harness projections of contracts/finding.schema.json. The shared contract owns\n// the semantics; this compact shape only carries what this workflow must route.\nconst FROZEN_FINDING = {\n  type: 'object',\n  required: ['finding_id', 'subject_kind', 'subject_address', 'record_projection_id',\n             'projection_as_of', 'verdict', 'evidence_addresses', 'frozen_at', 'detail'],\n  properties: {\n    finding_id: { type: 'string' },\n    subject_kind: { type: 'string' },\n    subject_address: { type: 'string' },\n    record_projection_id: { type: 'string' },\n    projection_as_of: { type: 'string' },\n    verdict: { type: 'string' },\n    evidence_addresses: { type: 'array', items: { type: 'string' } },\n    frozen_at: { type: 'string' },\n    detail: { type: 'string' },\n  },\n}\n\nconst COMPARISON = {\n  type: 'object',\n  required: ['classifications', 'detail'],\n  properties: {\n    classifications: { type: 'array', items: { type: 'string' } },\n    detail: { type: 'string' },\n  },\n}\n\n"""
        if schema_anchor not in text:
            raise SystemExit("sov-loop LAND schema anchor absent")
        text = text.replace(schema_anchor, schema + schema_anchor, 1)

    build_anchor = "log('Built: ' + (built.changed_paths || []).length + ' path(s) changed')\n\n"
    if "let orchestrationFinding = null" not in text:
        review = """let orchestrationFinding = null\nif (evidenceMode) {\n  phase('Orchestrator Review')\n  invocations += 1\n  orchestrationFinding = await agent(\n    'You are in REVIEW mode, not PLAN mode. Judge PARTICIPANT_IN_WORK for the bounded assignment ' + plan.operation + '. ' +\n    'Use contracts/record-projection.schema.json and contracts/finding.schema.json. Reconstruct a scoped RecordProjection through the Record service for the assignment/work subject and your evaluator relation. ' +\n    'Judge assignment, authority, scope, repair, disclosure, and terminal fidelity only; do not judge implementation correctness. ' +\n    'Do not read or anticipate the Witness conclusion. Cite only addresses in the projection. If the needed Record evidence does not exist, return verdict UNATTESTABLE with record_projection_id NONE and explain the Record defect; never fill it from the worker report. ' +\n    'Freeze the Finding before returning it. Return finding_id, subject_kind PARTICIPANT_IN_WORK, subject_address, record_projection_id, projection_as_of, verdict, evidence_addresses, frozen_at, and detail.',\n    { agentType: 'sov-orchestrator', schema: FROZEN_FINDING, phase: 'Orchestrator Review', label: 'review:' + selected.domain })\n  if (!orchestrationFinding || !orchestrationFinding.frozen_at) {\n    return { error: 'orchestrator review did not return a frozen Finding', concern: selected, build: built }\n  }\n}\n\n"""
        if build_anchor not in text:
            raise SystemExit("sov-loop build anchor absent")
        text = text.replace(build_anchor, build_anchor + review, 1)

    start = text.index("phase('Witness')")
    end = text.index("if (!witnessed)", start)
    old_witness = text[start:end]
    if "phase('Witness Review')" not in old_witness:
        new_witness = """let witnessed = null\nif (evidenceMode) {\n  phase('Witness Review')\n  invocations += 1\n  const cutoff = orchestrationFinding ? orchestrationFinding.projection_as_of : 'NONE'\n  witnessed = await agent(\n    'You are the independent evaluator of WORK. Concern: ' + selected.concern + '. Operation: ' + plan.operation + '. ' +\n    'Use contracts/record-projection.schema.json and contracts/finding.schema.json. Inspect the exact repository state and governing contract/fixtures yourself. ' +\n    'Reconstruct a WORK RecordProjection at this shared cutoff if available: ' + cutoff + '. The cutoff is projection metadata, not an evaluator conclusion. ' +\n    'Do not read the worker conclusion, Orchestrator Finding, or Controller expectation before freezing your own Finding. Builder paths may locate the work but are not evidence. ' +\n    'Cite only addresses present in your projection. If the projection/evidence is missing or cannot be reconstructed, return UNATTESTABLE rather than substituting prose. ' +\n    'Freeze before returning. Return finding_id, subject_kind WORK, subject_address, record_projection_id, projection_as_of, verdict, evidence_addresses, frozen_at, and detail.',\n    { agentType: 'sov-witness', schema: FROZEN_FINDING, phase: 'Witness Review', label: 'witness-review:' + selected.domain })\n} else {\n  phase('Witness')\n  invocations += 1\n  witnessed = await agent(\n    'You are the independent observation for work you did not do and must not touch. Concern: ' + selected.concern + '. ' +\n    'The builder reports it changed: ' + (built.changed_paths || []).join(', ') + '. Treat that as a claim, not evidence. ' +\n    'Read git status and git diff yourself, read the owning contract and the defeating fixture, and run python scripts/verify.py and python scripts/lint.py observing the real exit codes. ' +\n    'Confirm the defeating case actually fails as declared; a fixture that passes when it should fail is a DISSENTED verdict, not a residual. ' +\n    'Then write your observation to reports/observations/ as JSON with exactly these fields: observer_id (your agent label), contributed_to_build (false - and if that is not true, say so and set verdict DISSENTED), verdict (CONFIRMED or DISSENTED), concern, and checks. ' +\n    'You must not edit, fix, build, or commit anything outside that one observation file. ' +\n    'Return the verdict, what you independently confirmed, residuals, the path you wrote the observation to, and any judgement items only Bdo can settle.',\n    { agentType: 'sov-witness', schema: WITNESS, phase: 'Witness', label: 'witness:' + selected.domain })\n}\n\n"""
        text = text[:start] + new_witness + text[end:]

    compare_anchor = "log('Witness: ' + witnessed.verdict)\n\n"
    if "let comparison = null" not in text:
        compare = """let comparison = null\nif (evidenceMode) {\n  if (!witnessed.frozen_at) {\n    return { error: 'witness review did not return a frozen Finding', concern: selected }\n  }\n  phase('Compare')\n  invocations += 1\n  comparison = await agent(\n    'Compare these two already-frozen Findings. You do not witness, ratify, or average them. Preserve both subjects and citations. ' +\n    'Participant-in-work Finding: ' + JSON.stringify(orchestrationFinding) + '. WORK Finding: ' + JSON.stringify(witnessed) + '. ' +\n    'Use only these classifications: NO_CONFLICT, EVIDENCE_DIFFERENCE, INTERPRETATION_DIFFERENCE, WORK_DEFECT, WORKER_DEFECT, ORCHESTRATION_DEFECT, WITNESS_DEFECT, RECORD_DEFECT, POLICY_SEAM. ' +\n    'A missing/unreconstructable projection or citation is RECORD_DEFECT; an actually undefined governing choice is POLICY_SEAM. ' +\n    'Return classifications and a concise evidence-based detail. Do not create standing.',\n    { agentType: 'sov-controller', schema: COMPARISON, phase: 'Compare', label: 'compare:' + selected.domain })\n}\n\n"""
        if compare_anchor not in text:
            raise SystemExit("sov-loop compare anchor absent")
        text = text.replace(compare_anchor, compare_anchor + compare, 1)

    old_mode = "const mode = planOnly || !selected.in_grant_scope || witnessed.verdict !== 'CONFIRMED' ? 'plan' : 'land'\n"
    new_mode = """const comparisonBlocks = evidenceMode && (!comparison ||\n  (comparison.classifications || []).length !== 1 ||\n  comparison.classifications[0] !== 'NO_CONFLICT')\nconst mode = planOnly || !selected.in_grant_scope || witnessed.verdict !== 'CONFIRMED' || comparisonBlocks ? 'plan' : 'land'\n"""
    if new_mode not in text:
        if old_mode not in text:
            raise SystemExit("sov-loop mode anchor absent")
        text = text.replace(old_mode, new_mode, 1)

    old_reason = "'Rehearsing the gate only: ' + (planOnly ? 'plan_only was set' : (!selected.in_grant_scope ? 'concern is outside the grant' : 'witness verdict is ' + witnessed.verdict)))"
    new_reason = "'Rehearsing the gate only: ' + (planOnly ? 'plan_only was set' : (!selected.in_grant_scope ? 'concern is outside the grant' : (comparisonBlocks ? 'evidence comparison is not a single NO_CONFLICT' : 'witness verdict is ' + witnessed.verdict))))"
    if new_reason not in text:
        if old_reason not in text:
            raise SystemExit("sov-loop reason anchor absent")
        text = text.replace(old_reason, new_reason, 1)

    old_return = "  witness: { verdict: witnessed.verdict, observations: witnessed.observations, observation_file: witnessed.observation_file },\n  gate: gate,\n"
    new_return = """  witness: evidenceMode ? witnessed : { verdict: witnessed.verdict, observations: witnessed.observations, observation_file: witnessed.observation_file },\n  orchestration_finding: orchestrationFinding,\n  comparison: comparison,\n  evidence_mode: evidenceMode,\n  gate: gate,\n"""
    if new_return not in text:
        if old_return not in text:
            raise SystemExit("sov-loop return anchor absent")
        text = text.replace(old_return, new_return, 1)

    path.write_text(text, encoding="utf-8", newline="\n")


def patch_harness_readme() -> None:
    path = ROOT / ".claude/README.md"
    replace_once(
        path,
        "- `agents/sov-orchestrator.md` — stable planning role: turns an objective into\n  a bounded, blocker-honoring operation plan; edits nothing.\n",
        "- `agents/sov-orchestrator.md` — stable orchestration role: PLAN turns an\n  objective into a bounded operation; REVIEW forms a frozen Finding about\n  `PARTICIPANT_IN_WORK`; it edits nothing and never witnesses the work.\n",
    )
    replace_once(
        path,
        "- `agents/sov-witness.md` — stable read-only witness; verifies build claims\n  through an independent path and may dissent.\n",
        "- `agents/sov-witness.md` — stable read-only witness; independently evaluates\n  `WORK` from a scoped Record projection, freezes its Finding before comparison,\n  and may dissent or report the evidence unattestable.\n",
    )
    replace_once(
        path,
        "- `agents/sov-controller.md` — control role for headless or scheduled runs:\n  dispatches, aggregates, and packages evidenced results for Bdo's acceptance.\n",
        "- `agents/sov-controller.md` — control role for headless or scheduled runs:\n  dispatches and aggregates; when given independently frozen Findings it may\n  classify their evidence-backed relationship without ratifying either.\n",
    )
    old = """- `workflows/sov-loop.js` — one concern from selected to landed: Select\n  (sov-controller names the concern and checks it against the standing grant's\n  scope) -> Plan (sov-orchestrator) -> Build (sov-worker) -> Witness (an\n  independent sov-witness that writes its observation to `reports/observations/`)\n  -> Land. The Land phase runs `python scripts/sov_land.py`, the only place in\n"""
    new = """- `workflows/sov-loop.js` — one concern from selected to landed. Ordinary mode\n  retains Select -> Plan -> Build -> Witness -> Land. Prepared `evidence_mode`\n  inserts Orchestrator Review (`PARTICIPANT_IN_WORK`) and independent Witness\n  Review (`WORK`), freezes both Findings, then lets Controller Compare before the\n  landing gate. Missing Record evidence keeps that rehearsal in plan mode rather\n  than fabricating proof. The Land phase runs `python scripts/sov_land.py`, the only place in\n"""
    replace_once(path, old, new)


def patch_sov_next() -> None:
    path = ROOT / "scripts/sov_next.py"
    replace_once(
        path,
        "import roadmap_lanes\n",
        "import roadmap_lanes\nfrom sovcustody import collections as custody_collections\nfrom sovsession import phase_context\n",
    )
    anchor = "def declared_gate(status_text: str) -> str | None:\n"
    addition = '''def phase_position(root: Path = ROOT) -> tuple[dict, list[dict]]:\n    """Current phase authority plus only that active phase's custody records."""\n    state = phase_context.collect(root)\n    active = state.get("active")\n    if active is None or state.get("defects"):\n        return state, []\n    phase_id = str(active.get("phase_id"))\n    records = custody_collections.records(\n        root / "contracts" / "custodies.json", root / "contracts" / "custodies", phase_id)\n    return state, records\n\n\n'''
    insert_before(path, anchor, addition)
    text = path.read_text(encoding="utf-8")
    old = '''    gate = declared_gate(_text("STATUS.yaml"))\n    phases = roadmap_phases(roadmap_text)\n'''
    new = '''    gate = declared_gate(_text("STATUS.yaml"))\n    phase_state, active_custodies = phase_position(ROOT)\n    active_phase = phase_state.get("active")\n    phases = roadmap_phases(roadmap_text)\n'''
    if new not in text:
        if old not in text:
            raise SystemExit("sov_next main phase anchor absent")
        text = text.replace(old, new, 1)
    text = text.replace("    if gate and ready:\n", "    if active_phase is None and gate and ready:\n", 1)
    old_json = '''        print(json.dumps({"declared_gate": gate, "crosswalk": rows, "ready": ready,\n                          "stale_views": [{"view": v, "drifted": d} for v, d in stale],\n                          "closed_unsettled": unsettled,\n                          "conflict": conflict, "defects": defects},\n'''
    new_json = '''        print(json.dumps({"phase": phase_state, "active_phase_custodies": active_custodies,\n                          "declared_gate": gate, "crosswalk": rows, "ready": ready,\n                          "stale_views": [{"view": v, "drifted": d} for v, d in stale],\n                          "closed_unsettled": unsettled,\n                          "conflict": conflict, "defects": defects},\n'''
    if new_json not in text:
        if old_json not in text:
            raise SystemExit("sov_next json anchor absent")
        text = text.replace(old_json, new_json, 1)
    old_print = '''    print("== reachable work ==")\n    for row in ready or []:\n'''
    new_print = '''    print("== phase authority ==")\n    for line in phase_context.render(phase_state):\n        print(f"  {line}")\n    if active_phase is not None:\n        print("\\n== active phase custody ==")\n        if active_custodies:\n            for custody in active_custodies:\n                print(f"  {custody.get('custody_id')}  {custody.get('terminal', custody.get('standing', '?'))}")\n        else:\n            print("  none — active phase has no phase-scoped custody; this is opening debt")\n\n    print("\\n== roadmap reachable work ==")\n    for row in ready or []:\n'''
    if new_print not in text:
        if old_print not in text:
            raise SystemExit("sov_next output anchor absent")
        text = text.replace(old_print, new_print, 1)
    path.write_text(text, encoding="utf-8", newline="\n")


def add_readiness_command() -> None:
    path = ROOT / "scripts/sov_opening_readiness.py"
    if path.exists():
        return
    path.write_text('''#!/usr/bin/env python3\n"""Rehearse successor opening from repository evidence without opening anything."""\n\nfrom __future__ import annotations\n\nfrom pathlib import Path\nimport argparse\nimport json\nimport sys\n\nROOT = Path(__file__).resolve().parents[1]\nsys.path.insert(0, str(ROOT / "scripts"))\n\nfrom sovsession import phase_context  # noqa: E402\n\n\ndef _has(path: Path, *needles: str) -> bool:\n    if not path.is_file():\n        return False\n    text = path.read_text(encoding="utf-8")\n    return all(needle in text for needle in needles)\n\n\ndef assess(root: Path = ROOT) -> dict:\n    """Return a non-authoritative reading of whether the prepared opening is startable."""\n    state = phase_context.collect(root)\n    defects = list(state.get("defects") or [])\n    active = state.get("active")\n    if active is not None:\n        return {"state": "ACTIVE_PHASE", "phase": active.get("phase_id"),\n                "defects": defects, "authoritative": False}\n\n    if state.get("status_phase") != "NONE_ACTIVE":\n        defects.append("STATUS_NOT_NONE_ACTIVE")\n    if state.get("next_gate") != "SUCCESSOR_PHASE_OPENING":\n        defects.append("NEXT_GATE_NOT_SUCCESSOR_OPENING")\n\n    phases_path = root / "contracts/phases.json"\n    phases = json.loads(phases_path.read_text(encoding="utf-8")) if phases_path.is_file() else {}\n    if any(item.get("phase_id") == "phase:1-5" for item in phases.get("phases", [])):\n        defects.append("PHASE_1_5_ALREADY_RECORDED")\n\n    checks = {\n        "human_horizon": _has(root / "contracts/phase-1-5-phase-ii-horizon.md",\n                              "PREPARED · HUMAN-READABLE · NO PHASE STANDING",\n                              "Phase 1.5", "Phase II", "Agency learns. Record remembers."),\n        "prd_profile": _has(root / "PRD.md", "Prepared Phase 1.5 qualification profile",\n                            "P15-Q1", "P15-Q2", "P15-Q3", "P15-Q4",\n                            "prepared successor profile, not an active phase"),\n        "spec_predicates": _has(root / "SPEC.md", "Phase 1.5 commissioning predicates",\n                                "P15-Q1", "P15-Q2", "P15-Q3", "P15-Q4",\n                                "RecordProjection", "Finding"),\n        "record_projection_contract": (root / "contracts/record-projection.schema.json").is_file(),\n        "finding_contract": (root / "contracts/finding.schema.json").is_file(),\n        "phase_custody_reader": (root / "scripts/sovcustody/collections.py").is_file(),\n        "phase_progress_reader": (root / "scripts/sov_active_phase_progress.py").is_file(),\n    }\n    service_path = root / "services/record/contracts/service.json"\n    if service_path.is_file():\n        service = json.loads(service_path.read_text(encoding="utf-8"))\n        checks["record_project_evidence"] = any(\n            item.get("operation") == "project-evidence" and item.get("standing") == "BUILT"\n            for item in service.get("operations", []))\n    else:\n        checks["record_project_evidence"] = False\n\n    progress_path = root / "contracts/phase-progress.json"\n    if progress_path.is_file():\n        progress = json.loads(progress_path.read_text(encoding="utf-8"))\n        codes = {item.get("code") for item in progress.get("active_refusals", [])}\n        checks["opening_progress_refusal"] = "ACTIVE_PHASE_PROGRESS_UNINITIALIZED" in codes\n    else:\n        checks["opening_progress_refusal"] = False\n\n    for name, passed in checks.items():\n        if not passed:\n            defects.append("MISSING_" + name.upper())\n\n    future_custody = root / "contracts/custodies/phase-1-5.json"\n    if future_custody.exists():\n        defects.append("LIVE_PHASE_1_5_CUSTODY_EXISTS_BEFORE_OPENING")\n\n    return {\n        "state": "READY_TO_OPEN" if not defects else "NOT_READY",\n        "phase": None,\n        "next_gate": state.get("next_gate"),\n        "checks": checks,\n        "defects": defects,\n        "authoritative": False,\n        "note": "readiness is evidence for root judgement; this command cannot open a phase",\n    }\n\n\ndef main(argv: list[str] | None = None) -> int:\n    parser = argparse.ArgumentParser(description=__doc__)\n    parser.add_argument("--json", action="store_true")\n    parser.add_argument("--require-ready", action="store_true")\n    args = parser.parse_args(argv)\n    report = assess(ROOT)\n    if args.json:\n        print(json.dumps(report, indent=2, sort_keys=True))\n    else:\n        print(f"{report['state']}: non-authoritative opening rehearsal")\n        for name, passed in (report.get("checks") or {}).items():\n            print(f"  {'PASS' if passed else 'FAIL'} {name}")\n        for defect in report.get("defects") or []:\n            print(f"  {defect}")\n        print("  " + report.get("note", ""))\n    if report.get("defects"):\n        return 1\n    if args.require_ready and report.get("state") != "READY_TO_OPEN":\n        return 1\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n''', encoding="utf-8", newline="\n")


def patch_tests() -> None:
    loop_test = ROOT / "scripts/tests/test_sov_loop.py"
    addition = '''\n\nclass PreparedEvidenceRouting(unittest.TestCase):\n    """The harness prepares independent Findings without claiming Phase 1.5 complete."""\n\n    def test_roles_keep_work_and_participant_findings_separate(self):\n        orchestrator = (ROOT / ".claude/agents/sov-orchestrator.md").read_text(encoding="utf-8")\n        witness = (ROOT / ".claude/agents/sov-witness.md").read_text(encoding="utf-8")\n        controller = (ROOT / ".claude/agents/sov-controller.md").read_text(encoding="utf-8")\n        self.assertIn("PARTICIPANT_IN_WORK", orchestrator)\n        self.assertIn("subject is `WORK`", witness)\n        self.assertIn("independently frozen Findings", controller)\n        self.assertIn("RECORD_DEFECT", controller)\n        self.assertIn("POLICY_SEAM", controller)\n\n    def test_evidence_mode_freezes_before_comparison(self):\n        workflow = (ROOT / ".claude/workflows/sov-loop.js").read_text(encoding="utf-8")\n        self.assertIn("evidence_mode", workflow)\n        order = [workflow.index("phase('Orchestrator Review')"),\n                 workflow.index("phase('Witness Review')"),\n                 workflow.index("phase('Compare')"),\n                 workflow.index("phase('Land')", workflow.index("phase('Compare')"))]\n        self.assertEqual(order, sorted(order))\n        self.assertIn("record_projection_id", workflow)\n        self.assertIn("UNATTESTABLE", workflow)\n        self.assertIn("single NO_CONFLICT", workflow)\n'''
    text = loop_test.read_text(encoding="utf-8")
    if "class PreparedEvidenceRouting" not in text:
        marker = '\n\nif __name__ == "__main__":\n'
        if marker not in text:
            raise SystemExit("test_sov_loop main marker absent")
        loop_test.write_text(text.replace(marker, addition + marker, 1), encoding="utf-8", newline="\n")

    next_test = ROOT / "scripts/tests/test_sov_next.py"
    addition = '''\n\nclass ActivePhasePrecedence(unittest.TestCase):\n    def setUp(self):\n        self.tmp = tempfile.TemporaryDirectory()\n        self.root = Path(self.tmp.name)\n        (self.root / "contracts").mkdir()\n        self.addCleanup(self.tmp.cleanup)\n\n    def write_phase(self, status: str, open_phase: bool) -> None:\n        (self.root / "STATUS.yaml").write_text(\n            f"phase: {status}\\nnext_gate: PHASE_1_5_TERMINAL\\n", encoding="utf-8")\n        phases = [{"phase_id": "phase:i", "title": "Phase I", "execution_status": "CLOSED",\n                   "acceptance_status": "NOT_EARNED", "terminal": "CLOSED_INCOMPLETE",\n                   "exit_clauses": []}]\n        if open_phase:\n            phases.append({"phase_id": "phase:1-5", "title": "Operational Commissioning",\n                           "execution_status": "OPEN", "acceptance_status": "NOT_EARNED",\n                           "terminal": "IN_FLIGHT",\n                           "exit_clauses": [{"clause_id": "P15-X1", "text": "fresh participation"}]})\n        (self.root / "contracts/phases.json").write_text(\n            json.dumps({"phases": phases}) + "\\n", encoding="utf-8")\n\n    def test_active_phase_selects_only_its_phase_scoped_custody(self):\n        self.write_phase("phase:1-5", True)\n        (self.root / "contracts/custodies").mkdir()\n        (self.root / "contracts/custodies/phase-1-5.json").write_text(\n            json.dumps({"custodies": [{"custody_id": "custody:p15/x1",\n                                        "phase": "phase:1-5", "terminal": "OPEN"}]}) + "\\n",\n            encoding="utf-8")\n        state, records = sov_next.phase_position(self.root)\n        self.assertEqual(state["active"]["phase_id"], "phase:1-5")\n        self.assertEqual([row["custody_id"] for row in records], ["custody:p15/x1"])\n\n    def test_none_active_never_promotes_a_prepared_custody(self):\n        self.write_phase("NONE_ACTIVE", False)\n        (self.root / "contracts/custodies").mkdir()\n        (self.root / "contracts/custodies/phase-1-5.json").write_text(\n            json.dumps({"custodies": [{"custody_id": "custody:p15/x1",\n                                        "phase": "phase:1-5"}]}) + "\\n", encoding="utf-8")\n        state, records = sov_next.phase_position(self.root)\n        self.assertIsNone(state["active"])\n        self.assertEqual(records, [])\n\n    def test_phase_disagreement_is_reported_not_resolved(self):\n        self.write_phase("phase:1-5", False)\n        state, records = sov_next.phase_position(self.root)\n        self.assertIn("STATUS_PHASE_NOT_OPEN_IN_REGISTRY", state["defects"])\n        self.assertEqual(records, [])\n'''
    text = next_test.read_text(encoding="utf-8")
    if "class ActivePhasePrecedence" not in text:
        marker = '\n\nif __name__ == "__main__":\n'
        if marker not in text:
            raise SystemExit("test_sov_next main marker absent")
        next_test.write_text(text.replace(marker, addition + marker, 1), encoding="utf-8", newline="\n")

    session_test = ROOT / "scripts/tests/test_session_phase_context.py"
    text = session_test.read_text(encoding="utf-8")
    if "import sov_opening_readiness" not in text:
        text = text.replace(
            "from sovsession import brief, phase_context  # noqa: E402\n",
            "from sovsession import brief, phase_context  # noqa: E402\nimport sov_opening_readiness  # noqa: E402\n",
            1,
        )
    addition = '''\n\nclass OpeningRehearsalContract(unittest.TestCase):\n    def test_repository_reading_is_ready_or_already_active_without_hidden_defect(self):\n        report = sov_opening_readiness.assess(ROOT)\n        self.assertIn(report["state"], {"READY_TO_OPEN", "ACTIVE_PHASE"})\n        self.assertEqual(report["defects"], [])\n        self.assertFalse(report["authoritative"])\n'''
    if "class OpeningRehearsalContract" not in text:
        marker = '\n\nif __name__ == "__main__":\n'
        if marker not in text:
            raise SystemExit("session test main marker absent")
        text = text.replace(marker, addition + marker, 1)
    session_test.write_text(text, encoding="utf-8", newline="\n")


def refresh_clarity() -> None:
    coverage = json.loads((ROOT / ".clarity/coverage.json").read_text(encoding="utf-8"))
    candidates = list(coverage.get("reviews", {}).keys())
    for _ in range(6):
        result = subprocess.run([sys.executable, "scripts/sov_clarity.py", "check"], cwd=ROOT,
                                text=True, capture_output=True, check=False)
        output = result.stdout + "\n" + result.stderr
        stale = []
        for line in output.splitlines():
            if "BASIS_STALE" not in line and "TEXT_STALE" not in line:
                continue
            for candidate in candidates:
                if candidate in line and candidate not in stale:
                    stale.append(candidate)
        if not stale:
            if result.returncode:
                print(output)
                raise SystemExit(result.returncode)
            return
        for candidate in stale:
            run(sys.executable, "scripts/sov_clarity.py", "record", candidate, "--changed")
    run(sys.executable, "scripts/sov_clarity.py", "check")


def refresh_snapshot() -> None:
    sys.path.insert(0, str((ROOT / "scripts").resolve()))
    from sovsnapshot import claims
    path = ROOT / "CLAUDE.md"
    text = path.read_text(encoding="utf-8")
    derived = claims.derive_all()
    for claim in claims.CLAIMS:
        value = derived.values[claim.name] + (1 if claim.name == "commits" else 0)
        match = re.search(claim.pattern, text)
        if not match:
            raise SystemExit(f"snapshot pattern absent for {claim.name}")
        start, end = match.span(1)
        text = text[:start] + str(value) + text[end:]
    path.write_text(text, encoding="utf-8", newline="\n")


def apply() -> None:
    assert_preopen()
    patch_roles()
    patch_loop()
    patch_harness_readme()
    patch_sov_next()
    add_readiness_command()
    patch_tests()


def finalize() -> None:
    assert_preopen()
    WORKFLOW.unlink()
    SELF.unlink()
    refresh_snapshot()
    refresh_clarity()
    run(sys.executable, "scripts/sov_docs.py", "build")


COMMANDS = {"apply": apply, "finalize": finalize}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        raise SystemExit("usage: gap_195_opening_readiness.py apply|finalize")
    COMMANDS[sys.argv[1]]()
