"""Concern-scoped session attribution stays open-world and non-authoritative."""

from __future__ import annotations

from pathlib import Path
import os
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import sov_session  # noqa: E402
from sovsession import concerns, store  # noqa: E402


class ConcernResolution(unittest.TestCase):
    def setUp(self) -> None:
        self.saved = {name: os.environ.get(name) for name in
                      ("SOV_CONCERN", "SOV_SOURCE_SESSION", "SOV_SOURCES", "SOV_QUEUES")}
        for name in self.saved:
            os.environ.pop(name, None)
        self.addCleanup(self.restore)

    def restore(self) -> None:
        for name, value in self.saved.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    def test_explicit_concern_is_open_address_not_enum(self) -> None:
        value, source = concerns.resolve("concern:any/future-citizen-form", "alpha")
        self.assertEqual(value, "concern:any/future-citizen-form")
        self.assertEqual(source, "EXPLICIT")

    def test_environment_supplies_launcher_binding(self) -> None:
        os.environ["SOV_CONCERN"] = "concern:phase-1-5/dev"
        self.assertEqual(concerns.resolve(None, "alpha"),
                         ("concern:phase-1-5/dev", "ENVIRONMENT"))

    def test_legacy_session_gets_traceable_fallback_not_denial(self) -> None:
        self.assertEqual(concerns.resolve(None, "alpha"),
                         ("concern:session/alpha", "SESSION_FALLBACK"))

    def test_live_binding_cannot_silently_switch(self) -> None:
        existing = {"concern": "concern:a", "live": True}
        self.assertIn("SESSION_CONCERN_IMMUTABLE",
                      concerns.binding_defect(existing, "concern:b") or "")
        self.assertIsNone(concerns.binding_defect(existing, "concern:a"))


class ConcernTopology(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name) / "sessions"

    def test_route_preserves_lineage_and_grants_nothing(self) -> None:
        session = {"session": "alpha", "concern": "concern:dev",
                   "source_session": "root"}
        route = concerns.record_route(self.directory, session, "concern:ops",
                                      ["record:event/1"], "queue:ops/intake", "SEEN")
        self.assertEqual(route["source_concern"], "concern:dev")
        self.assertEqual(route["destination_concern"], "concern:ops")
        self.assertEqual(route["authority_effect"], "NONE")
        self.assertEqual(route["custody_effect"], "NONE")
        self.assertEqual(concerns.enumerate_concerns(self.directory),
                         ["concern:dev", "concern:ops"])

    def test_empty_store_is_an_empty_enumerable_stub(self) -> None:
        self.assertEqual(concerns.enumerate_concerns(self.directory), [])


class SkillDiscovery(unittest.TestCase):
    def test_new_skill_needs_no_registry_edit(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skill = root / ".claude" / "skills" / "future-citizen-skill"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("# skill\n", encoding="utf-8")
            self.assertEqual(concerns.available_skills(root), ["future-citizen-skill"])


class CliShape(unittest.TestCase):
    def test_parser_accepts_arbitrary_concern_queue_and_disposition(self) -> None:
        args = sov_session.build_parser().parse_args([
            "register", "--concern", "concern:novel/thing",
            "--source", "source:any/1", "--queue", "queue:any/1"])
        self.assertEqual(args.concern, "concern:novel/thing")
        route = sov_session.build_parser().parse_args([
            "route", "--to", "concern:never-seen-before", "--disposition", "CUSTOM"])
        self.assertEqual(route.to_concern, "concern:never-seen-before")
        self.assertEqual(route.disposition, "CUSTOM")


class RepositoryContract(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[2]

    def test_workflow_has_no_closed_domain_enum_and_carries_concern(self) -> None:
        text = (self.ROOT / ".claude" / "workflows" / "sov-loop.js").read_text("utf-8")
        self.assertNotIn("const DOMAINS", text)
        for token in ("concern_id", "source_session", "queue_refs", "source_refs",
                      "cross_concern_routes"):
            self.assertIn(token, text)

    def test_global_rule_makes_concern_routing_not_authority(self) -> None:
        text = (self.ROOT / "AGENTS.md").read_text("utf-8")
        self.assertIn("One session, one concern", text)
        self.assertIn("Concern mismatch routes by default", text)
        self.assertIn("is **not authority**", text)

    def test_commissioning_roles_inherit_concern_without_closed_vocabulary(self) -> None:
        for name in ("sov.md", "sov-controller.md", "sov-orchestrator.md",
                     "sov-worker.md", "sov-witness.md"):
            text = (self.ROOT / ".claude" / "agents" / name).read_text("utf-8")
            self.assertIn("## Concern/session discipline", text)
            self.assertIn("Concern is attribution and routing, never authority", text)


if __name__ == "__main__":
    unittest.main()
