"""Defeating checks for the Claude SOV control mesh.

The harness may accelerate coordination, but it must not collapse BLUE into RED,
turn model choice into authority, or remove the bounds that keep fan-out
attributable. These tests inspect the checked-in host binding only; they do not
claim a Claude session ran or independently witness product behavior.

Two layers. Structural checks compare the files against the pins in
`sov_mesh_pins` - frontmatter identity, tool sets, section skeletons, guard
sentences, the routing table, the pipeline diagrams, hook commands and
matchers, and the character inventory. The `sov_mesh_prose` scanner then walks
every text region for authority-granting language that carries no denial in
its own clause. The scanner is a tripwire for careless drift, not proof
against adversarial authorship - a synonym the deny-list does not name still
passes, which is an accepted residual; the authority boundary itself is
`AGENTS.md` and the kernel gates. Skill and workflow prompts under `.claude/`
are outside this suite's subject.
"""

from __future__ import annotations

from pathlib import Path
import json
import re
import unittest

from scripts.tests import sov_mesh_pins as pins
from scripts.tests.sov_mesh_prose import DENIAL, authority_findings, sentences

ROOT = Path(__file__).resolve().parents[2]
AGENTS = ROOT / ".claude" / "agents"
MESH = ROOT / ".claude" / "CONTROL-MESH.md"
ROLE_FILES = ("sov.md", "sov-controller.md", "sov-orchestrator.md",
              "sov-worker.md", "sov-witness.md")


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


def headings(raw: str) -> list[str]:
    return [line[3:].strip() for line in raw.splitlines() if line.startswith("## ")]


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

    def test_settings_declare_only_env_and_hooks(self) -> None:
        """An added block (permissions above all) changes host behavior unseen."""
        self.assertEqual(set(json.loads(text(".claude/settings.json"))), pins.SETTINGS_KEYS)

    def test_every_hook_can_actually_execute(self) -> None:
        """The hooks are the only mechanical restraint; a renamed interpreter, a
        zero timeout, or a rewritten bootstrap disables them while everything
        else looks intact, so the bootstrap is pinned by digest."""
        import hashlib
        hooks = json.loads(text(".claude/settings.json"))["hooks"]
        for event, entries in hooks.items():
            for entry in entries:
                for hook in entry["hooks"]:
                    self.assertEqual(hook["command"], "python", event)
                    self.assertGreaterEqual(hook.get("timeout", 0), 5, event)
                    self.assertEqual(hook["args"][0], "-c", event)
                    self.assertEqual(
                        hashlib.sha256(hook["args"][1].encode()).hexdigest(),
                        pins.HOOK_BOOTSTRAP_SHA256, event)
                    self.assertIn(hook["args"][2], pins.HOOK_SCRIPTS, event)

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
    def test_agents_directory_is_a_closed_set(self) -> None:
        """A sixth role file would be discovered by the host but read by no test."""
        self.assertEqual({path.name for path in AGENTS.glob("*.md")}, pins.AGENT_FILES)

    def test_frontmatter_keys_are_a_closed_set(self) -> None:
        for name, expected in pins.FRONTMATTER_KEYS.items():
            self.assertEqual(set(frontmatter(name)), expected, name)

    def test_frontmatter_identity_is_pinned(self) -> None:
        """Name, model, effort, and description route an agent; none may drift."""
        self.assertEqual(frontmatter("sov.md")["model"], "inherit")
        for name in pins.TOOL_SETS:
            self.assertEqual(frontmatter(name)["model"], "sonnet", name)
        for name, effort in pins.EFFORT.items():
            fm = frontmatter(name)
            self.assertEqual(fm["name"], name[:-3], name)
            self.assertEqual(fm["effort"], effort, name)
            self.assertEqual(compact(fm["description"]), pins.DESCRIPTIONS[name], name)

    def test_every_role_tool_set_is_pinned_exactly(self) -> None:
        """Allow-lists: a quietly added capability fails. Bash/PowerShell stay in
        every set, so read-only and no-edit claims rest on prose plus the hooks."""
        for name, expected in pins.TOOL_SETS.items():
            declared = {tool.strip() for tool in frontmatter(name)["tools"].split(",")}
            self.assertEqual(declared, expected, name)

    def test_every_role_keeps_its_section_skeleton(self) -> None:
        for name, expected in pins.HEADINGS.items():
            self.assertEqual(headings(text(f".claude/agents/{name}")), expected, name)

    def test_every_role_keeps_its_guard_sentences(self) -> None:
        for name, guards in pins.GUARDS.items():
            flat = compact(text(f".claude/agents/{name}"))
            for guard in guards:
                self.assertIn(guard, flat, name)

    def test_witness_verdicts_are_exactly_three(self) -> None:
        witness = text(".claude/agents/sov-witness.md")
        self.assertIn("`reproduced`, `dissented`, or `unattestable`", witness)
        self.assertEqual(set(re.findall(r"`([^`]+)`", witness)), pins.WITNESS_BACKTICKS)

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

    def test_status_paragraph_is_exactly_the_disclaimer(self) -> None:
        """assertEqual, not assertIn: an appended exception clause must fail."""
        paragraph = MESH.read_text(encoding="utf-8").split("\n\n")[1]
        self.assertEqual(compact(paragraph), pins.STATUS_PARAGRAPH)

    def test_pipeline_diagrams_are_pinned(self) -> None:
        raw = MESH.read_text(encoding="utf-8")
        self.assertEqual(re.findall(r"```text\n(.*?)```", raw, re.DOTALL),
                         pins.MESH_FENCES)

    def test_mesh_keeps_its_guard_sentences(self) -> None:
        flat = compact(MESH.read_text(encoding="utf-8"))
        for guard in pins.MESH_GUARDS:
            self.assertIn(guard, flat)

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

    def test_mesh_names_n_fanout_and_cross_session_alignment(self) -> None:
        mesh = MESH.read_text(encoding="utf-8")
        for term in ("N SOV sessions", "N Controllers", "N Orchestrators",
                     "N Workers", "N Witnesses"):
            self.assertIn(term, mesh)
        self.assertIn("SendMessage", mesh)
        self.assertIn("Console continuity", mesh)
        self.assertIn("ephemeral Claude message", mesh)


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
                if re.search(r"\b(ticket|issue)s?\b", sentence):
                    self.assertTrue(DENIAL.search(sentence), f"{path.name}: {sentence}")

    def test_character_inventory_is_closed(self) -> None:
        """A homoglyph or zero-width character defeats a lexical rule invisibly,
        an HTML entity spells a deny-listed word in pure ASCII, and a comment
        hides text from the scanner that a model reading the file still sees -
        so comments are banned outright, malformed closers included."""
        allowed = {chr(code) for code in range(32, 127)} | {"\n"} | pins.EXTRA_CHARS
        for name in (".claude/CONTROL-MESH.md",
                     *(f".claude/agents/{role}" for role in ROLE_FILES)):
            raw = text(name)
            strange = {ch for ch in raw if ch not in allowed}
            self.assertEqual(strange, set(), name)
            self.assertNotRegex(raw, r"&#\w+;|&[a-z]+;", name)
            self.assertNotIn("<!--", raw, name)


if __name__ == "__main__":
    unittest.main()
