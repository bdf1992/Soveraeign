"""Defeating checks for the Claude SOV control mesh.

The harness may accelerate coordination, but it must not collapse BLUE into RED,
turn model choice into authority, or remove the bounds that keep fan-out
attributable. These tests inspect the checked-in host binding only; they do not
claim a Claude session ran or independently witness product behavior.
"""

from __future__ import annotations

from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[2]
AGENTS = ROOT / ".claude" / "agents"


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


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
        self.assertIn("session_registry.py", encoded)
        self.assertIn("console_session.py", encoded)
        self.assertIn("pre-write", encoded)
        self.assertIn("post-write", encoded)


class RoleShape(unittest.TestCase):
    def test_models_are_execution_hints_not_one_shared_setting(self) -> None:
        self.assertEqual(frontmatter("sov.md")["model"], "inherit")
        for name in ("sov-controller.md", "sov-orchestrator.md",
                     "sov-worker.md", "sov-witness.md"):
            self.assertEqual(frontmatter(name)["model"], "sonnet", name)
        mesh = text(".claude/CONTROL-MESH.md")
        self.assertIn("performance mechanism, never authority or standing", mesh)
        self.assertIn("Haiku", mesh)
        self.assertIn("Opus", mesh)

    def test_worker_is_blue_and_cannot_be_its_witness(self) -> None:
        worker = text(".claude/agents/sov-worker.md")
        self.assertIn("BLUE construction participant", worker)
        self.assertIn("can never be its Witness", worker)
        self.assertIn("never witness or ratify your own work", worker)

    def test_witness_is_red_and_read_only(self) -> None:
        witness = text(".claude/agents/sov-witness.md")
        fm = frontmatter("sov-witness.md")
        self.assertIn("independent RED participant", witness)
        self.assertIn("reproduced", witness)
        self.assertIn("dissented", witness)
        self.assertIn("unattestable", witness)
        tools = fm["tools"]
        self.assertNotIn("Edit", tools)
        self.assertNotIn("Write", tools)
        self.assertNotIn("Agent", tools)

    def test_controller_requires_red_after_blue_and_repairs_in_place(self) -> None:
        controller = text(".claude/agents/sov-controller.md")
        self.assertIn("Worker BLUE -> Witness RED", controller)
        self.assertIn("return it to the same Worker concern", controller)
        self.assertIn("fresh independent RED", controller)
        self.assertIn("Workflow is unavailable", controller)

    def test_orchestrator_must_prove_parallel_safety_and_red_requirement(self) -> None:
        orchestrator = text(".claude/agents/sov-orchestrator.md")
        self.assertIn("parallel_safe", orchestrator)
        self.assertIn("RED defeating/witness requirement", orchestrator)
        self.assertIn("suggested_model", orchestrator)


class MeshClosure(unittest.TestCase):
    def test_sov_owns_fleet_shape_not_extra_authority(self) -> None:
        sov = text(".claude/agents/sov.md")
        self.assertIn("control mesh, not a new authority tier", sov)
        self.assertIn("Prefer fewer completed concerns over a larger active fleet", sov)
        self.assertIn("python scripts/sov_session.py brief", sov)
        self.assertIn("SendMessage", sov)

    def test_mesh_names_n_fanout_and_cross_session_alignment(self) -> None:
        mesh = text(".claude/CONTROL-MESH.md")
        for term in ("N SOV sessions", "N Controllers", "N Orchestrators",
                     "N Workers", "N Witnesses"):
            self.assertIn(term, mesh)
        self.assertIn("SendMessage", mesh)
        self.assertIn("Console continuity", mesh)
        self.assertIn("ephemeral Claude message", mesh)

    def test_red_does_not_ratify_and_blue_does_not_self_witness(self) -> None:
        mesh = text(".claude/CONTROL-MESH.md")
        self.assertIn("RED does not ratify", mesh)
        self.assertIn("BLUE does not witness itself", mesh)
        self.assertIn("no authority or standing", mesh.lower())


if __name__ == "__main__":
    unittest.main()
