"""Pinned expectations for the control-mesh binding.

Every value here is a defeating fixture: the checked-in mesh and role files
must match these pins exactly, so a quiet rewrite of an identity, a tool set,
a guard sentence, a diagram, or a hook fails the suite instead of shipping.
A legitimate change to the binding updates the pin in the same commit, which
is the review surface working as intended.
"""

from __future__ import annotations

TOOL_SETS = {
    "sov-controller.md": {"Read", "Grep", "Glob", "Bash", "PowerShell", "Write",
                          "Skill", "Workflow", "Agent", "ListAgents", "SendMessage"},
    "sov-orchestrator.md": {"Read", "Grep", "Glob", "Bash", "PowerShell", "Skill",
                            "ListAgents", "SendMessage"},
    "sov-worker.md": {"Read", "Grep", "Glob", "Bash", "PowerShell", "Edit", "Write",
                      "Skill", "Agent", "ListAgents", "SendMessage"},
    "sov-witness.md": {"Read", "Grep", "Glob", "Bash", "PowerShell",
                       "ListAgents", "SendMessage"},
}

EFFORT = {"sov.md": "high", "sov-controller.md": "high", "sov-orchestrator.md": "medium",
          "sov-worker.md": "medium", "sov-witness.md": "high"}

DESCRIPTIONS = {
    "sov.md":
        "Main Soveraeign control-mesh lead. Use it to coordinate bounded work across "
        "multiple Controllers, sessions, models, Orchestrators, Workers, and independent "
        "Witnesses while preserving one governed world and scarce WIP.",
    "sov-controller.md":
        "Stable Control-tier owner for one bounded concern. Use it to select the "
        "closure predicate, dispatch orchestration and BLUE construction, recruit an "
        "independent RED witness, loop findings back into repair, aggregate evidence, "
        "and report the terminal. It never supplies its own build or witness evidence.",
    "sov-orchestrator.md":
        "Stable Orchestration-tier planner for any Soveraeign domain. Use it to turn "
        "one Controller concern into bounded operations with explicit file ownership, "
        "ordering, model fit, BLUE completion observations, RED witness requirements, "
        "dependencies, and blockers. It plans; it does not build or witness.",
    "sov-worker.md":
        "Stable Work-tier BLUE builder for any Soveraeign domain. Use it to execute "
        "exactly one bounded planned operation, recruit build-side helpers, run the "
        "required checks, absorb same-concern findings, and return a presented result "
        "for independent RED witnessing. It never witnesses or ratifies its own work.",
    "sov-witness.md":
        "Independent RED witness for Soveraeign work. Use it after BLUE construction "
        "to re-derive claims through an independent path, attack defeating cases, run "
        "repository/service/conformance checks, and emit an attributable observation. "
        "It never builds, edits, fixes, settles, or ratifies.",
}

HEADINGS = {
    "sov.md": ["Dispatch", "Closure loop", "Alignment", "Completion report"],
    "sov-controller.md": ["Select the pipeline", "Parallelism and models", "BLUE", "RED",
                          "Alignment", "Control rules", "Completion report"],
    "sov-orchestrator.md": ["Planning rules", "Model fit", "Alignment", "Output"],
    "sov-worker.md": ["BLUE boundary", "Change protocol", "Models", "Checks", "Handoff"],
    "sov-witness.md": ["Independence", "RED procedure", "Feedback loop", "Standing",
                       "Report"],
}

# Each anchor is itself the required rule; deleting or inverting it must fail.
GUARDS = {
    "sov.md": ("BLUE cannot witness itself. RED cannot ratify.",
               "Only the owner-held gate may settle owner judgement.",
               "Capabilities never imply authority. Context never supplies a grant."),
    "sov-controller.md": ("Do not create a new ticket or hand the engineering choice to Bdo.",
                          "Standing forwarded from machine evidence is at most"
                          " `BUILT -> WITNESSED`.",
                          "You never build, witness, or ratify.",
                          "Host tool absence may change how the declared pipeline is"
                          " invoked; it never changes its semantics."),
    "sov-orchestrator.md": ("You may not soften a protected boundary, widen effects, infer"
                            " authority from model/tool availability, advance standing, or"
                            " present synthesis as Bdo's judgement.",),
    "sov-worker.md": ("Never witness or ratify your own work.",
                      "standing proposal at most `OPEN -> BUILT`"),
    "sov-witness.md": ("A different model name does not by itself create independence.",
                       "You may never report RATIFIED. Only Bdo settles judgement-typed"
                       " ratification.",
                       "A Worker helper that read or edited the change is inside BLUE and"
                       " is ineligible to witness it."),
}

MESH_GUARDS = (
    "Every consequential Worker result gets a Witness that was outside that build.",
    "The worktree itself is the isolation: the session registry only warns about"
    " overlapping claims across worktrees, and refuses a write only when another live"
    " session recently claimed that path in the same tree.",
    "state plainly in the report that agent teams or cross-session messaging were"
    " unavailable rather than silently collapsing roles",
)

STATUS_PARAGRAPH = (
    "Status: Claude harness binding only. This document adds no Soveraeign authority, "
    "standing, transition, service, or durable truth. `AGENTS.md`, `SOV.md`, "
    "`STATUS.yaml`, service contracts, and accepted decisions remain governing."
)

MESH_FENCES = [
    "N SOV sessions\n  -> N Controllers\n       -> N Orchestrators\n"
    "            -> N Workers       = BLUE construction\n"
    "            -> N Witnesses     = RED independent observation\n"
    "       -> Controller closure / repair loop\n  -> cross-session alignment\n",
    "Controller\n  -> Orchestrator: scope one closure predicate\n"
    "  -> Worker: build + targeted checks + root verification       BLUE\n"
    "  -> Witness: re-derive + attack defeating cases independently RED\n"
    "  -> reproduced? close/present/land under current policy\n"
    "  -> dissented? return finding to the same Worker concern\n"
    "                 then BLUE -> fresh RED again\n",
]

WITNESS_BACKTICKS = {
    ".claude/CONTROL-MESH.md", "AGENTS.md", "BUILT -> WITNESSED", "CLASSIFICATION.md",
    "OPEN -> BUILT", "SPEC.md", "SendMessage", "dissented", "python scripts/verify.py",
    "reproduced", "unattestable", "unattestable / WITNESS_NOT_INDEPENDENT",
}

# The only non-ASCII characters these files may carry; a homoglyph or a
# zero-width character is a defect, not a style choice.
EXTRA_CHARS = {"—", "“", "”"}

# The agents directory is a closed set: a sixth role file is a finding even
# before its content is read, because the host discovers every .md here.
AGENT_FILES = {"sov.md", "sov-controller.md", "sov-orchestrator.md",
               "sov-worker.md", "sov-witness.md"}

# settings.json may declare exactly these top-level blocks; anything else
# (a permissions block above all) changes what the host will do.
SETTINGS_KEYS = {"env", "hooks"}

# Frontmatter is a closed key set per file; an added key reaches host behavior
# the suite never reads.
FRONTMATTER_KEYS = {
    "sov.md": {"name", "description", "model", "effort", "color"},
    "sov-controller.md": {"name", "description", "model", "effort", "color", "tools"},
    "sov-orchestrator.md": {"name", "description", "model", "effort", "color", "tools"},
    "sov-worker.md": {"name", "description", "model", "effort", "color", "tools"},
    "sov-witness.md": {"name", "description", "model", "effort", "color", "tools"},
}

# Every hook runs the same inline bootstrap; pinning its digest means a hook
# cannot be made a no-op while interpreter, matcher, and timeout all look intact.
HOOK_BOOTSTRAP_SHA256 = "f153a98b9262689bfa0615fe009a99bf3c74524e12e1e8a99fd8caf5293535a6"
HOOK_SCRIPTS = {"console_session.py", "session_registry.py"}
