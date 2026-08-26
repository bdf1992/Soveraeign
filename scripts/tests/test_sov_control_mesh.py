"""Defeating checks for the Claude SOV control mesh.

The harness may accelerate coordination, but it must not collapse BLUE into RED,
turn model choice into authority, or remove the bounds that keep fan-out
attributable. These tests inspect the checked-in host binding only; they do not
claim a Claude session ran or independently witness product behavior.

Two layers. Structural checks pin frontmatter, tool sets, headings at every
level of every file, the routing table, hook matchers, and the closure
checklist. The `sov_mesh_prose` scanner then walks every text region of the
mesh and role files for authority-granting language that carries no denial.
The scanner is a tripwire for careless drift, not proof against adversarial
authorship; the authority boundary itself is `AGENTS.md` and the kernel gates.
Skill and workflow prompts under `.claude/` are outside this suite's subject.
"""

from __future__ import annotations

from pathlib import Path
import json
import re
import unittest

from scripts.tests.sov_mesh_prose import DENIAL, authority_findings, sentences

ROOT = Path(__file__).resolve().parents[2]
AGENTS = ROOT / ".claude" / "agents"
MESH = ROOT / ".claude" / "CONTROL-MESH.md"
ROLE_FILES = ("sov.md", "sov-controller.md", "sov-orchestrator.md",
              "sov-worker.md", "sov-witness.md")

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

HEADINGS = {
    "sov.md": ["Dispatch", "Closure loop", "Alignment", "Completion report"],
    "sov-controller.md": ["Select the pipeline", "Parallelism and models", "BLUE", "RED",
                          "Alignment", "Control rules", "Completion report"],
    "sov-orchestrator.md": ["Planning rules", "Model fit", "Alignment", "Output"],
    "sov-worker.md": ["BLUE boundary", "Change protocol", "Models", "Checks", "Handoff"],
    "sov-witness.md": ["Independence", "RED procedure", "Feedback loop", "Standing", "Report"],
}

# Each anchor is itself the required rule; deleting or inverting it must fail.
GUARDS = {
    "sov.md": ("BLUE cannot witness itself. RED cannot ratify.",
               "Only the owner-held gate may settle owner judgement."),
    "sov-controller.md": ("Do not create a new ticket or hand the engineering choice to Bdo.",
                          "Standing forwarded from machine evidence is at most"
                          " `BUILT -> WITNESSED`."),
    "sov-worker.md": ("Never witness or ratify your own work.",
                      "standing proposal at most `OPEN -> BUILT`"),
    "sov-witness.md": ("A different model name does not by itself create independence.",
                       "You may never report RATIFIED. Only Bdo settles judgement-typed"
                       " ratification."),
}


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def compact(value: str) -> str:
    """Compare prose semantics without making Markdown line wrapping normative."""
    return " ".join(value.split())


def frontmatter(name: str) -> dict[str, str]:
    """Read the flat scalar fields used by these role files without a YAML dependency."""
    raw = (AGENTS / name).read_text(encoding="utf-8")
    if not raw.startswith("---\n"):
        raise AssertionError(f"{name} has no YAML frontmatter")
    block = raw.split("---\n", 2)[1]
    result: dict[str, str] = {}
    current = None
    for line in block.splitlines():
        if line.startswith("  "):
            if current and current in result:
                result[current] += " " + line.strip()
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        current = key.strip()
        result[current] = value.strip().rstrip(">-").strip()
    return result


def headings(raw: str, level: str = "## ") -> list[str]:
    return [line[len(level):].strip() for line in raw.splitlines()
            if line.startswith(level)]


def mesh_section(title: str) -> str:
    raw = MESH.read_text(encoding="utf-8")
    match = re.search(rf"^## {re.escape(title)}\n(.*?)(?=^## |\Z)", raw,
                      re.MULTILINE | re.DOTALL)
    if match is None:
        raise AssertionError(f"CONTROL-MESH.md lacks section {title!r}")
    return match.group(1)


class HostBounds(unittest.TestCase):
    def test_agent_teams_and_subagents_are_bounded(self) -> None:
        env = json.loads(text(".claude/settings.json"))["env"]
        self.assertEqual(env["CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"], "1")
        self.assertEqual(env["CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH"], "3")
        self.assertEqual(env["CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS"], "12")

    def test_session_registry_hooks_still_fire_on_the_tools_they_guard(self) -> None:
        """The matchers are live regexes; a renamed matcher disables the guard."""
        hooks = json.loads(text(".claude/settings.json"))["hooks"]
        fired = {"pre-write": [], "post-write": [], "pre-bash": []}
        for event in ("PreToolUse", "PostToolUse"):
            for entry in hooks.get(event, ()):
                for hook in entry["hooks"]:
                    mode = hook["args"][-1]
                    if "session_registry.py" in hook["args"] and mode in fired:
                        fired[mode].append(entry["matcher"])
        for mode, tools in (("pre-write", ("Edit", "Write")),
                            ("post-write", ("Edit", "Write")),
                            ("pre-bash", ("Bash", "PowerShell"))):
            self.assertTrue(fired[mode], f"no session_registry {mode} hook")
            for tool in tools:
                self.assertTrue(
                    any(re.fullmatch(matcher, tool) for matcher in fired[mode]),
                    f"{mode} matcher no longer fires on {tool}")

    def test_console_session_hooks_survive(self) -> None:
        encoded = json.dumps(json.loads(text(".claude/settings.json"))["hooks"])
        self.assertIn("console_session.py", encoded)


class RoleShape(unittest.TestCase):
    def test_models_are_execution_hints_not_one_shared_setting(self) -> None:
        self.assertEqual(frontmatter("sov.md")["model"], "inherit")
        for name in TOOL_SETS:
            self.assertEqual(frontmatter(name)["model"], "sonnet", name)

    def test_every_role_tool_set_is_pinned_exactly(self) -> None:
        """Allow-lists: a quietly added capability fails. Bash/PowerShell stay in
        every set, so read-only and no-edit claims rest on prose, not tooling."""
        for name, expected in TOOL_SETS.items():
            declared = {tool.strip() for tool in frontmatter(name)["tools"].split(",")}
            self.assertEqual(declared, expected, name)

    def test_every_role_keeps_its_section_skeleton(self) -> None:
        for name, expected in HEADINGS.items():
            self.assertEqual(headings(text(f".claude/agents/{name}")), expected, name)

    def test_every_role_keeps_its_guard_sentences(self) -> None:
        for name, guards in GUARDS.items():
            flat = compact(text(f".claude/agents/{name}"))
            for guard in guards:
                self.assertIn(guard, flat, name)

    def test_witness_verdicts_are_exactly_three(self) -> None:
        witness = text(".claude/agents/sov-witness.md")
        self.assertIn("`reproduced`, `dissented`, or `unattestable`", witness)
        self.assertNotIn("`accepted`", witness)

    def test_controller_requires_red_after_blue_and_repairs_in_place(self) -> None:
        controller = compact(text(".claude/agents/sov-controller.md"))
        self.assertIn("sov-worker` performs BLUE construction", controller)
        self.assertIn("sov-witness` outside that build performs RED independent observation",
                      controller)
        self.assertIn("return it to the same Worker concern", controller)
        self.assertIn("fresh independent RED", controller)
        self.assertIn("Workflow` is unavailable", controller)

    def test_orchestrator_must_prove_parallel_safety_and_red_requirement(self) -> None:
        orchestrator = text(".claude/agents/sov-orchestrator.md")
        self.assertIn("parallel_safe", orchestrator)
        self.assertIn("RED defeating/witness requirement", orchestrator)
        self.assertIn("suggested_model", orchestrator)


class MeshStructure(unittest.TestCase):
    def test_mesh_keeps_exactly_the_declared_sections(self) -> None:
        self.assertEqual(headings(MESH.read_text(encoding="utf-8")), [
            "Purpose", "Fleet, cell, pipeline", "Role counts", "Model routing",
            "Session and channel protocol", "BLUE and RED", "Host capability fallbacks"])

    def test_routing_table_never_downgrades_witness_or_controller(self) -> None:
        rows = {}
        for line in mesh_section("Model routing").splitlines():
            if line.startswith("|") and "---" not in line:
                cells = [cell.strip() for cell in line.strip("|").split("|")]
                rows[cells[0].strip("*` ")] = cells
        for role in ("Witness", "Controller", "Orchestrator", "Worker"):
            self.assertIn(role, rows, "routing table row missing")
        for role in ("Witness", "Controller"):
            self.assertEqual(rows[role][1], "Sonnet", role)
            self.assertIn("Opus", rows[role][2], role)
            self.assertNotIn("haiku", " ".join(rows[role]).lower(), role)
        self.assertIn("performance mechanism, never authority or standing",
                      mesh_section("Model routing"))

    def test_closure_checklist_still_demands_red_and_forbids_externalizing(self) -> None:
        section = compact(mesh_section("BLUE and RED")).lower()
        self.assertIn("only when", section)
        for required in ("red reproduced the consequential claims",
                         "no red finding was externalized instead of repaired",
                         "standing is not inflated beyond the evidence produced",
                         "landing/merge behavior follows the current repository policy"):
            self.assertIn(required, section)
        self.assertIn("red does not ratify", section)
        self.assertIn("blue does not witness itself", section)
        self.assertIn("built -> witnessed", section)

    def test_fallbacks_still_forbid_collapsing_roles(self) -> None:
        section = compact(mesh_section("Host capability fallbacks"))
        self.assertIn("state plainly in the report that agent teams or cross-session"
                      " messaging were unavailable rather than silently collapsing roles",
                      section)

    def test_mesh_names_n_fanout_and_cross_session_alignment(self) -> None:
        mesh = MESH.read_text(encoding="utf-8")
        for term in ("N SOV sessions", "N Controllers", "N Orchestrators",
                     "N Workers", "N Witnesses"):
            self.assertIn(term, mesh)
        self.assertIn("SendMessage", mesh)
        self.assertIn("Console continuity", mesh)
        self.assertIn("ephemeral Claude message", mesh)

    def test_mesh_disclaims_authority_in_its_status_line(self) -> None:
        self.assertIn("adds no soveraeign authority, standing",
                      compact(MESH.read_text(encoding="utf-8")).lower())


class AuthorityLanguage(unittest.TestCase):
    """No text region of the mesh or role files may grant what the harness cannot hold."""

    def test_mesh_prose_grants_nothing(self) -> None:
        self.assertEqual(authority_findings(MESH.read_text(encoding="utf-8")), [])

    def test_role_prose_grants_nothing(self) -> None:
        for name in ROLE_FILES:
            raw = (AGENTS / name).read_text(encoding="utf-8")
            self.assertEqual(authority_findings(raw), [], name)

    def test_ticket_sentences_always_carry_their_denial(self) -> None:
        for path in (MESH, AGENTS / "sov-controller.md", AGENTS / "sov-worker.md",
                     AGENTS / "sov-witness.md"):
            for sentence in sentences(path.read_text(encoding="utf-8")):
                if "ticket" in sentence:
                    self.assertTrue(DENIAL.search(sentence), f"{path.name}: {sentence}")


if __name__ == "__main__":
    unittest.main()
