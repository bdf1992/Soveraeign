from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from charting import ChartingError, ContractGraph
from charting.derive import derive_repository_graph
from charting.skill_contracts import _resolve_governing_source


ROOT = Path(__file__).resolve().parents[2]


class ContractGraphTests(unittest.TestCase):
    def setUp(self) -> None:
        self.declaration = derive_repository_graph(ROOT)
        self.graph = ContractGraph.from_dict(self.declaration)

    def test_governing_sources_derive_current_sdlc_shape(self) -> None:
        points = self.graph.points.values()
        self.assertEqual(8, sum(point.kind == "skill" for point in points))
        self.assertEqual(5, sum(point.kind == "workflow" for point in points))
        self.assertEqual(4, sum(point.kind == "stance" for point in points))
        self.assertEqual(8, sum(point.kind == "implementation" for point in points))
        self.assertEqual(2, sum(point.kind == "requirement" for point in points))
        self.assertEqual(2, sum(point.kind == "capability" for point in points))
        self.assertIn("binding:claude-code", self.graph.points)

    def test_skill_forest_reaches_explicit_qa_requirements(self) -> None:
        chart = self.graph.chart("binding:claude-code", "skill-forest")
        point_ids = {point["id"] for point in chart["points"]}
        self.assertIn("implementation:claude:sdlc-development", point_ids)
        self.assertIn("skill:development", point_ids)
        self.assertIn("skill:qa", point_ids)
        self.assertIn("requirement:qa:repository-verification", point_ids)
        self.assertIn("capability:repository.verify", point_ids)
        self.assertTrue(chart["governance"]["projection_only"])
        self.assertFalse(chart["governance"]["grants_authority"])

    def test_partial_skill_omissions_survive_chart_projection(self) -> None:
        chart = self.graph.chart("binding:claude-code", "skill-forest")
        omissions = chart["omissions"]
        self.assertTrue(any("RED generative adversarial execution" in item for item in omissions))
        self.assertTrue(any("BLUE construction capabilities" in item for item in omissions))
        self.assertTrue(any("live capability receipts" in item for item in omissions))
        self.assertTrue(
            any(item.startswith("charting/experiments/qa.skill.json:") for item in omissions)
        )

    def test_qa_path_preserves_requirement_capability_distinction(self) -> None:
        qa_requires = [
            crossing
            for crossing in self.graph.crossings.values()
            if crossing.source == "skill:qa" and crossing.kind == "requires"
        ]
        self.assertEqual(2, len(qa_requires))
        self.assertTrue(
            all(crossing.target.startswith("requirement:qa:") for crossing in qa_requires)
        )

        direct_skill_capability = [
            crossing
            for crossing in self.graph.crossings.values()
            if crossing.source == "skill:qa"
            and self.graph.points[crossing.target].kind == "capability"
        ]
        self.assertEqual([], direct_skill_capability)

        binds = [crossing for crossing in self.graph.crossings.values() if crossing.kind == "binds"]
        self.assertEqual(2, len(binds))
        self.assertTrue(
            all(self.graph.points[crossing.source].kind == "requirement" for crossing in binds)
        )
        self.assertTrue(
            all(self.graph.points[crossing.target].kind == "capability" for crossing in binds)
        )

    def test_capability_declarations_do_not_claim_live_availability(self) -> None:
        capabilities = [point for point in self.graph.points.values() if point.kind == "capability"]
        self.assertEqual(2, len(capabilities))
        self.assertTrue(all(point.attributes["declaration_only"] for point in capabilities))
        self.assertTrue(
            all(point.attributes["live_availability"] is False for point in capabilities)
        )
        self.assertNotIn("authority", {point.kind for point in self.graph.points.values()})

        chart = self.graph.chart("binding:claude-code", "operator-navigation")
        self.assertTrue(any("runtime availability" in item for item in chart["omissions"]))
        self.assertTrue(any("live authority" in item for item in chart["omissions"]))
        self.assertTrue(chart["governance"]["requires_live_gate_recheck"])

    def test_declared_effect_classes_remain_governing_vocabulary(self) -> None:
        repository_verify = self.graph.points["capability:repository.verify"]
        independent_observation = self.graph.points["capability:result.observe-independent"]
        self.assertEqual("RESOURCE_CONSUMPTION", repository_verify.attributes["effect_class"])
        self.assertEqual("RECORD_LOCAL", independent_observation.attributes["effect_class"])

    def test_source_revision_pins_actual_input_content(self) -> None:
        revision = self.declaration["source_revision"]
        self.assertTrue(revision.startswith("sha256:"))
        self.assertEqual(71, len(revision))
        self.assertIn("SDLC.md", self.declaration["source_files"])
        self.assertIn("AGENTS.md", self.declaration["source_files"])
        self.assertIn(".claude/README.md", self.declaration["source_files"])
        self.assertIn("charting/experiments/qa.skill.json", self.declaration["source_files"])

    def test_governing_source_resolution_refuses_path_escape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            governing = root / "AGENTS.md"
            governing.write_text("# rules\n", encoding="utf-8")

            resolved = _resolve_governing_source(root, "AGENTS.md#Testing", "test.skill.json")
            self.assertEqual(governing.resolve(), resolved)

            with self.assertRaises(ChartingError):
                _resolve_governing_source(root, "../AGENTS.md", "test.skill.json")
            with self.assertRaises(ChartingError):
                _resolve_governing_source(root, str(governing.resolve()), "test.skill.json")
            with self.assertRaises(ChartingError):
                _resolve_governing_source(root, "MISSING.md#Rule", "test.skill.json")

    def test_every_claude_skill_realizes_exactly_one_declared_skill(self) -> None:
        realizes = [
            crossing for crossing in self.graph.crossings.values() if crossing.kind == "realizes"
        ]
        self.assertEqual(8, len(realizes))
        self.assertEqual(8, len({crossing.target for crossing in realizes}))
        self.assertTrue(all(crossing.target.startswith("skill:") for crossing in realizes))

    def test_direct_skill_to_capability_relation_fails_closed(self) -> None:
        declaration = {
            "points": [
                {"id": "a", "kind": "skill", "label": "A", "source": "test"},
                {"id": "b", "kind": "capability", "label": "B", "source": "test"},
            ],
            "crossings": [
                {
                    "id": "x",
                    "kind": "requires",
                    "source": "a",
                    "target": "b",
                    "provenance": "test",
                }
            ],
            "paradigms": [{"id": "p", "traverse": ["requires"]}],
        }
        with self.assertRaises(ChartingError):
            ContractGraph.from_dict(declaration)

    def test_unknown_relation_fails_closed(self) -> None:
        declaration = {
            "points": [
                {"id": "a", "kind": "skill", "label": "A", "source": "test"},
                {"id": "b", "kind": "capability", "label": "B", "source": "test"},
            ],
            "crossings": [
                {
                    "id": "x",
                    "kind": "authorizes",
                    "source": "a",
                    "target": "b",
                    "provenance": "test",
                }
            ],
            "paradigms": [{"id": "p", "traverse": ["requires"]}],
        }
        with self.assertRaises(ChartingError):
            ContractGraph.from_dict(declaration)


if __name__ == "__main__":
    unittest.main()


class SkillBindingScope(unittest.TestCase):
    """The chart models the SDLC loop, so it charts the `sdlc-*` host bindings.

    `.claude/skills/` also holds twelve `sov-<domain>` skills, which are domain
    know-how rather than tier bindings and have no canonical SDLC skill to
    implement. The derivation refused the whole repository once they existed,
    which was the chart asserting a correspondence nobody had claimed.
    """

    SKILLS = ROOT / ".claude" / "skills"

    def test_the_repository_derives_with_domain_skills_present(self) -> None:
        present = [p.name for p in self.SKILLS.iterdir() if p.is_dir()]
        self.assertTrue([n for n in present if not n.startswith("sdlc-")],
                        "this case is vacuous without a non-SDLC skill on disk")
        derive_repository_graph(ROOT)

    def test_every_charted_binding_is_an_sdlc_binding(self) -> None:
        graph = ContractGraph.from_dict(derive_repository_graph(ROOT))
        charted = [p for p in graph.points if str(p).startswith("implementation:claude:")]
        self.assertTrue(charted)
        for point in charted:
            with self.subTest(point=point):
                self.assertIn(":sdlc-", str(point))

    def test_an_sdlc_binding_that_misnames_itself_still_fails(self) -> None:
        """The defeating case. Scoping the walk must not disarm the identity check."""
        with tempfile.TemporaryDirectory() as raw:
            skills = Path(raw) / "skills"
            (skills / "sdlc-control").mkdir(parents=True)
            (skills / "sdlc-control" / "SKILL.md").write_text(
                "---\nname: sdlc-wrong\ndescription: x\n---\n", encoding="utf-8")
            from charting.derive import _derive_binding_implementations
            with self.assertRaises(ChartingError):
                _derive_binding_implementations(Path(raw), skills, {"skill:control": {}})
