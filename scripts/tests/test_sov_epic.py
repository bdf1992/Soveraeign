from __future__ import annotations

from pathlib import Path
import json
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sovepic import metadata, projection, survey, walk  # noqa: E402
from sovepic.projection import Issue  # noqa: E402
from sovschedule import jsonshape  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[2]
ISSUE_SCHEMA = walk.load_issue_schema(REPO_ROOT)
BLOCK = """```yaml
issue_schema: soveraeign-ticket/v1
tags:
  - "kind:bit"
  - "village:ground-and-evidence"
kind: bit
standing: OPEN
last_observed_at: null
enabled_flag: true
count: 3
requires: ["#6", "#7"]
dependency_channels:
  produces:
    - record-spine
  consumes: [topology]
```

## Bounded obligation

Prose after the block is ignored.
"""


def issue(number, **overrides):
    fields = {
        "number": number,
        "title": f"Issue {number}",
        "state": "OPEN",
        "labels": [],
        "url": "",
        "updated_at": "",
        "metadata": {},
        "parse_error": None,
    }
    fields.update(overrides)
    return Issue(**fields)


class MetadataSubsetTests(unittest.TestCase):
    def test_parses_the_documented_subset(self):
        parsed = metadata.parse_body(BLOCK)
        self.assertEqual(parsed["kind"], "bit")
        self.assertEqual(parsed["tags"], ["kind:bit", "village:ground-and-evidence"])
        self.assertIsNone(parsed["last_observed_at"])
        self.assertIs(parsed["enabled_flag"], True)
        self.assertEqual(parsed["count"], 3)
        self.assertEqual(parsed["requires"], ["#6", "#7"])
        self.assertEqual(
            parsed["dependency_channels"], {"produces": ["record-spine"], "consumes": ["topology"]}
        )

    def test_timestamps_stay_strings(self):
        self.assertEqual(
            metadata.parse_block("last_observed_at: 2026-08-23T05:50:49Z")["last_observed_at"],
            "2026-08-23T05:50:49Z",
        )

    def test_refuses_a_body_without_a_block(self):
        with self.assertRaises(metadata.MetadataError):
            metadata.parse_body("## Bounded obligation\n\nNo fence here.")

    def test_refuses_constructs_outside_the_subset(self):
        with self.assertRaises(metadata.MetadataError):
            metadata.parse_block("anchor: &ref value")
        with self.assertRaises(metadata.MetadataError):
            metadata.parse_block("key:\n\tvalue")
        with self.assertRaises(metadata.MetadataError):
            metadata.parse_block("- a top-level sequence")


class SequenceOfMappingsTests(unittest.TestCase):
    def test_asks_parse_as_a_sequence_of_flat_mappings(self):
        block = "\n".join(
            ["asks:", '  - of: "#11"', '    adjustment: "exist"', '  - of: "#30"', '    adjustment: "open"']
        )
        parsed = metadata.parse_block(block)
        self.assertEqual(parsed["asks"][0], {"of": "#11", "adjustment": "exist"})
        self.assertEqual(len(parsed["asks"]), 2)

    def test_quoted_scalars_keep_their_colons(self):
        block = "\n".join(["tags:", '  - "kind:story"', '  - "village:reach-and-motion"'])
        self.assertEqual(metadata.parse_block(block)["tags"], ["kind:story", "village:reach-and-motion"])

    def test_nesting_under_a_sequence_item_is_refused(self):
        block = "\n".join(["asks:", '  - of: "#11"', "    deeper:", "      than: allowed"])
        with self.assertRaises(metadata.MetadataError):
            metadata.parse_block(block)


class SchemaSubsetTests(unittest.TestCase):
    """oneOf and if/then/else are what make the issue contract's rules checkable."""

    ONE_OF = {"oneOf": [{"type": "array"}, {"type": "object"}]}

    def test_one_of_accepts_exactly_one_branch(self):
        self.assertEqual(jsonshape.check(["a"], self.ONE_OF), [])
        self.assertTrue(jsonshape.check("neither", self.ONE_OF))

    def test_one_of_refuses_an_ambiguous_value(self):
        ambiguous = {"oneOf": [{"type": "string"}, {"minLength": 1}]}
        self.assertTrue(jsonshape.check("both", ambiguous))

    def test_if_then_applies_only_on_the_matching_branch(self):
        schema = {
            "if": {"properties": {"kind": {"const": "bit"}}, "required": ["kind"]},
            "then": {"required": ["bit_id"]},
            "else": {"required": ["stub_id"]},
        }
        self.assertEqual(jsonshape.check({"kind": "bit", "bit_id": "BIT-X"}, schema), [])
        self.assertTrue(jsonshape.check({"kind": "bit"}, schema))
        self.assertEqual(jsonshape.check({"kind": "other", "stub_id": "STUB-X"}, schema), [])

    def test_kind_conditionals_of_the_real_issue_contract_bite(self):
        block = dict(json.loads(json.dumps(MINIMAL_EPIC)))
        self.assertEqual(jsonshape.check(block, ISSUE_SCHEMA), [])
        block.pop("villages")
        self.assertTrue(any("villages" in d for d in jsonshape.check(block, ISSUE_SCHEMA)))


MINIMAL_EPIC = {
    "issue_schema": "soveraeign-ticket/v1",
    "tags": ["kind:epic", "scope:system", "effect:record-local"],
    "kind": "epic-of-epics",
    "epic_id": "EPIC-SYSTEM-OF-VILLAGES",
    "standing": "OPEN",
    "horizon": "NOW_TO_SCALE_TRUST",
    "authority": "Bdo/product-intent-and-phase-gate",
    "effect_class": "RECORD_LOCAL",
    "evidence_pointer": "PENDING",
    "last_observed_at": None,
    "walker_receipt": "PENDING",
    "demotion_pointer": "#demotion",
    "dependency_channels": ["record-spine"],
    "child_issues": ["#2"],
    "villages": ["ground-and-evidence"],
}


class LabelProjectionTests(unittest.TestCase):
    def test_every_projected_label_exists_in_the_catalogue(self):
        catalogue = (REPO_ROOT / ".github" / "labels.yml").read_text(encoding="utf-8")
        known = set(re.findall(r'^- name: "([^"]+)"$', catalogue, re.MULTILINE))
        self.assertTrue(known, "no labels parsed from .github/labels.yml")
        for table in (walk.KIND_LABEL, walk.VILLAGE_LABEL, walk.HORIZON_LABEL, walk.EFFECT_LABEL):
            for name in table.values():
                self.assertIn(name, known)

    def test_missing_projected_label_is_a_defect(self):
        block = {"kind": "bit", "village": "ground-and-evidence", "horizon": "NOW"}
        clean = issue(6, labels=["type: bit", "village: ground", "horizon: now"], metadata=block)
        self.assertEqual(walk.label_defects(clean), [])
        drifted = issue(6, labels=["type: bit"], metadata=block)
        self.assertEqual(len(walk.label_defects(drifted)), 2)

    def test_contradicting_label_is_a_defect(self):
        block = {"kind": "bit", "village": "ground-and-evidence", "horizon": "NOW"}
        wrong = issue(6, labels=["type: stub", "village: ground", "horizon: now"], metadata=block)
        self.assertTrue(any("contradicts kind" in d for d in walk.label_defects(wrong)))

    def test_effect_class_without_a_label_is_reported(self):
        block = {"kind": "bit", "effect_class": "RESOURCE_CONSUMPTION"}
        self.assertTrue(any("no label" in d for d in walk.label_defects(issue(6, metadata=block))))


class ContainmentTests(unittest.TestCase):
    def tree(self, bit_children):
        return {
            1: issue(1, metadata={"kind": "epic-of-epics", "child_issues": ["#4"]}),
            4: issue(4, metadata={"kind": "village", "parent": "#1", "child_issues": bit_children}),
            6: issue(6, metadata={"kind": "bit", "parent": "#1", "village_issue": "#4"}),
        }

    def test_village_issue_is_the_containment_edge_not_parent(self):
        self.assertEqual(walk.containment_defects(self.tree(["#6"]), 1), [])

    def test_an_issue_its_village_does_not_list_is_a_defect(self):
        defects = walk.containment_defects(self.tree([]), 1)
        self.assertEqual(defects, ["#6: village #4 does not list it in child_issues"])

    def test_closed_issues_are_not_holes_in_the_tree(self):
        tree = self.tree([])
        tree[6] = issue(6, state="CLOSED", metadata=tree[6].metadata)
        self.assertEqual(walk.containment_defects(tree, 1), [])

    def test_dangling_references_are_reported(self):
        tree = self.tree(["#6"])
        tree[6] = issue(6, metadata={**tree[6].metadata, "requires": ["#99"]})
        self.assertIn("#6: requires #99, which is not present", walk.containment_defects(tree, 1))


class ReadinessAndRoutingTests(unittest.TestCase):
    def tree(self, standing, state="OPEN"):
        return {
            6: issue(6, state=state, metadata={"kind": "bit", "standing": standing}),
            8: issue(8, metadata={"kind": "bit", "standing": "OPEN", "requires": ["#6"]}),
        }

    def test_open_prerequisite_holds_the_dependent(self):
        self.assertEqual(walk.readiness(self.tree("OPEN"))[8], ["#6"])

    def test_built_prerequisite_releases_the_dependent(self):
        self.assertEqual(walk.readiness(self.tree("BUILT_SELF_TESTED_NOT_WITNESSED"))[8], [])

    def test_closed_prerequisite_releases_the_dependent(self):
        self.assertEqual(walk.readiness(self.tree("OPEN", state="CLOSED"))[8], [])

    def test_routing_is_evidence_backed_or_absent(self):
        routing = {"issue_routes": {"8": {"domain": "asset", "evidence": "services/asset/"}}}
        self.assertEqual(walk.route(issue(8), routing), "asset")
        self.assertIsNone(walk.route(issue(11), routing))


class ProjectionTests(unittest.TestCase):
    def test_an_unparseable_body_is_recorded_not_dropped(self):
        raw = [{"number": 52, "title": "Temporary note", "state": "OPEN", "labels": [], "body": "no block"}]
        document = projection.build(raw, "owner/repo", "2026-08-23T00:00:00Z")
        record = document["issues"]["52"]
        self.assertIsNone(record["metadata"])
        self.assertIn("no fenced yaml", record["parse_error"])

    def test_checked_in_projection_loads_and_surveys(self):
        document = projection.load(REPO_ROOT)
        self.assertEqual(document["source"]["root_issue"], projection.ROOT_ISSUE)
        result = survey.survey(REPO_ROOT, document, projection.villages(REPO_ROOT))
        self.assertEqual(
            set(result["counts"]),
            {"issues", "open", "ready", "held", "unrouted", "owner_held", "stories"},
        )
        for entry in result["ready"]:
            self.assertEqual(entry["blocked_by"], [])
            self.assertIsNotNone(entry["domain"])
            self.assertEqual(entry["readiness"], walk.REACHABLE)
        for entry in result["unrouted"]:
            self.assertIsNone(entry["domain"])
            self.assertEqual(entry["routing"], walk.UNROUTED)

    def test_every_route_names_a_known_domain_and_evidence(self):
        known = json.loads((REPO_ROOT / ".claude" / "epic" / "villages.json").read_text("utf-8"))
        domains = set()
        for village in known["villages"].values():
            domains.update(village["domains"])
        for number, route in known["issue_routes"].items():
            self.assertIn(route["domain"], domains, f"issue {number} routes outside its villages")
            self.assertTrue(route["evidence"].strip())


if __name__ == "__main__":
    unittest.main()
