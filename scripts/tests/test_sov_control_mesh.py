"""Defeating checks for the Claude SOV control mesh.

The harness may accelerate coordination, but it must not collapse BLUE into RED,
turn model choice into authority, or remove the bounds that keep fan-out
attributable. These tests inspect the checked-in host binding only; they do not
claim a Claude session ran or independently witness product behavior.

Two layers. Structural checks parse frontmatter, the routing table, headings,
tool lists, and the closure checklist, so a deleted section or a widened tool
set fails loudly. A deny-list scanner then walks every prose sentence of the
mesh and role files for authority-granting language that carries no denial, so
a sentence added beside a guard rule cannot quietly invert it. Substring
anchors remain only where the anchor itself is the required rule.
"""

from __future__ import annotations

from pathlib import Path
import json
import re
import unittest

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


def tool_set(name: str) -> set[str]:
    return {tool.strip() for tool in frontmatter(name)["tools"].split(",")}


def prose_lines(raw: str) -> list[str]:
    """Body lines with frontmatter, fenced code, tables, and headings removed."""
    body = raw.split("---\n", 2)[2] if raw.startswith("---\n") else raw
    lines, fenced = [], False
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            fenced = not fenced
            continue
        if fenced or stripped.startswith("|") or stripped.startswith("#"):
            continue
        lines.append(stripped.lstrip("-*").strip())
    return lines


def sentences(raw: str) -> list[str]:
    """Lowercased prose sentences; bullets and semicolon clauses count as sentences."""
    joined = " ".join(line for line in prose_lines(raw) if line)
    return [part.strip().lower()
            for part in re.split(r"(?<=[.;!?])\s+", joined) if part.strip()]


def mesh_section(title: str) -> str:
    raw = MESH.read_text(encoding="utf-8")
    match = re.search(rf"^## {re.escape(title)}\n(.*?)(?=^## |\Z)", raw,
                      re.MULTILINE | re.DOTALL)
    if match is None:
        raise AssertionError(f"CONTROL-MESH.md lacks section {title!r}")
    return match.group(1)


DENIAL = re.compile(r"\b(not|no|never|cannot)\b")
OWNED = re.compile(r"\b(bdo|owner|owner-held)\b")
# Always-deny shapes: no surrounding denial excuses these.
SELF_WITNESS = re.compile(
    r"\b(may|can|could|should|must)\s+witness\s+((your|its|their)\s+own|itself|yourself)")
CLOSE_WITHOUT = re.compile(
    r"\b(close[sd]?|complete[sd]?|land[sd]?|ratif\w+|settle[sd]?)\b[^.;]*\bwithout\b"
    r"[^.;]*\b(red|witness\w*|observation|bdo|owner)\b")
# Deny-unless-denied shapes.
AUTHORITY_VERB = re.compile(r"\b(confer\w*|ratif\w*)\b")
SETTLE_CLAIM = re.compile(r"\bsettle[sd]?\s+(\w+\s+){0,2}(judgement|judgment|standing)\b")
GRANT_STANDING = re.compile(r"\b(add\w*|grant\w*|confer\w*)\b[^.;]*\b(authority|standing)\b")
MODEL_INDEPENDENCE = re.compile(
    r"\bmodel\b(\W+\w+){0,6}\W+independen|independen\w*(\W+\w+){0,6}\W+model\b")


def authority_findings(raw: str) -> list[str]:
    """Sentences that grant, permit, or launder authority without carrying a denial."""
    findings = []
    for sentence in sentences(raw):
        if SELF_WITNESS.search(sentence) or CLOSE_WITHOUT.search(sentence):
            findings.append(sentence)
            continue
        denied = DENIAL.search(sentence) or OWNED.search(sentence)
        if (AUTHORITY_VERB.search(sentence) or SETTLE_CLAIM.search(sentence)) and not denied:
            findings.append(sentence)
            continue
        if GRANT_STANDING.search(sentence) and not DENIAL.search(sentence):
            findings.append(sentence)
            continue
        if MODEL_INDEPENDENCE.search(sentence) and not DENIAL.search(sentence):
            findings.append(sentence)
    return findings


class HostBounds(unittest.TestCase):
    def test_agent_teams_and_subagents_are_bounded(self) -> None:
        settings = json.loads(text(".claude/settings.json"))
        env = settings["env"]
        self.assertEqual(env["CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"], "1")
        self.assertEqual(env["CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH"], "3")
        self.assertEqual(env["CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS"], "12")

    def test_existing_session_guards_are_not_replaced_by_the_mesh(self) -> None:
        settings = json.loads(text(".claude/settings.json"))
        encoded = json.dumps(settings["hooks"], sort_keys=True)
        for guard in ("session_registry.py", "console_session.py", "pre-write", "post-write"):
            self.assertIn(guard, encoded)


class RoleShape(unittest.TestCase):
    def test_models_are_execution_hints_not_one_shared_setting(self) -> None:
        self.assertEqual(frontmatter("sov.md")["model"], "inherit")
        for name in ("sov-controller.md", "sov-orchestrator.md",
                     "sov-worker.md", "sov-witness.md"):
            self.assertEqual(frontmatter(name)["model"], "sonnet", name)

    def test_witness_tools_are_exactly_the_observation_set(self) -> None:
        """An allow-list, so a quietly added edit or spawn capability fails."""
        self.assertEqual(
            tool_set("sov-witness.md"),
            {"Read", "Grep", "Glob", "Bash", "PowerShell", "ListAgents", "SendMessage"})

    def test_orchestrator_tools_are_exactly_the_planning_set(self) -> None:
        self.assertEqual(
            tool_set("sov-orchestrator.md"),
            {"Read", "Grep", "Glob", "Bash", "PowerShell", "Skill",
             "ListAgents", "SendMessage"})

    def test_worker_is_blue_and_cannot_be_its_witness(self) -> None:
        lowered = text(".claude/agents/sov-worker.md").lower()
        self.assertIn("blue construction participant", lowered)
        self.assertIn("can never be its witness", lowered)
        self.assertIn("never witness or ratify your own work", lowered)

    def test_witness_is_red_and_returns_the_three_verdicts(self) -> None:
        witness = text(".claude/agents/sov-witness.md")
        self.assertIn("independent RED participant", witness)
        for verdict in ("reproduced", "dissented", "unattestable"):
            self.assertIn(verdict, witness)

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
        raw = MESH.read_text(encoding="utf-8")
        headings = [line[3:].strip() for line in raw.splitlines()
                    if line.startswith("## ")]
        self.assertEqual(headings, [
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
            self.assertNotIn("Haiku", " ".join(rows[role]), role)
        self.assertIn("performance mechanism, never authority or standing",
                      mesh_section("Model routing"))

    def test_closure_checklist_still_demands_red_and_forbids_externalizing(self) -> None:
        section = compact(mesh_section("BLUE and RED")).lower()
        self.assertIn("only when", section)
        for required in ("red reproduced", "externalized", "standing is not inflated",
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

    def test_mesh_disclaims_authority_in_its_status_line(self) -> None:
        self.assertIn("adds no soveraeign authority, standing",
                      compact(MESH.read_text(encoding="utf-8")).lower())


class AuthorityLanguage(unittest.TestCase):
    """No sentence in the mesh or role files may grant what the harness cannot hold."""

    def test_mesh_prose_grants_nothing(self) -> None:
        self.assertEqual(authority_findings(MESH.read_text(encoding="utf-8")), [])

    def test_role_prose_grants_nothing(self) -> None:
        for name in ROLE_FILES:
            raw = (AGENTS / name).read_text(encoding="utf-8")
            self.assertEqual(authority_findings(raw), [], name)

    def test_mesh_never_routes_findings_into_tickets(self) -> None:
        for sentence in sentences(MESH.read_text(encoding="utf-8")):
            if "ticket" in sentence:
                self.assertTrue(DENIAL.search(sentence), sentence)


if __name__ == "__main__":
    unittest.main()
