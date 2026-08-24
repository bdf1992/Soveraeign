"""Unit tests for the registrar's write planner.

The write half of the GitHub crossing is only as safe as its plan. These tests hold the
planner to three promises: it derives every action from a local declaration, it rewrites
nothing outside its own delimiters, and applying a plan twice changes nothing the second
time. They run offline; no test here reaches GitHub.
"""

from __future__ import annotations

from pathlib import Path
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "adapters" / "github"))

import catalogue  # noqa: E402
import plan as planner  # noqa: E402

BODY = "```yaml\nissue_schema: soveraeign-ticket/v1\nkind: bit\nstanding: OPEN\n```\n\n# A bit\n\nProse.\n"


def export_file(issues: list[dict], labels: list[dict] | None = None) -> Path:
    """Write a throwaway registrar export and its label sidecar; return the export path."""
    directory = Path(tempfile.mkdtemp())
    path = directory / "tickets.json"
    path.write_text(json.dumps(issues), encoding="utf-8", newline="\n")
    sidecar = path.with_name(path.stem + ".labels.json")
    sidecar.write_text(json.dumps(labels or []), encoding="utf-8", newline="\n")
    return path


class CatalogueTests(unittest.TestCase):
    """The repository's own catalogue parses, and its two sections stay disjoint."""

    def test_the_real_catalogue_parses_into_governed_and_retired(self) -> None:
        governed, retired = catalogue.read_catalogue(ROOT)
        self.assertGreater(len(governed), 20)
        self.assertIn("standing: ratified", governed)
        self.assertIn("witness: witnessed", retired)
        self.assertEqual(set(governed) & set(retired), set())

    def test_every_governed_colour_is_a_six_digit_hex(self) -> None:
        governed, _ = catalogue.read_catalogue(ROOT)
        for name, (color, description) in governed.items():
            self.assertRegex(color, r"^[0-9A-F]{6}$", name)
            self.assertTrue(description.strip(), f"{name} has no description")

    def test_every_description_fits_what_github_accepts(self) -> None:
        """GitHub returns 422 past 100 characters, and does so mid-crossing."""
        governed, _ = catalogue.read_catalogue(ROOT)
        for name, (_, description) in governed.items():
            self.assertLessEqual(len(description), catalogue.DESCRIPTION_LIMIT, name)

    def test_an_over_long_description_is_refused_at_parse_time(self) -> None:
        directory = Path(tempfile.mkdtemp())
        (directory / ".github").mkdir()
        declared = "\n".join([
            '- name: "a"',
            '  color: "FF0000"',
            '  description: "' + "x" * 101 + '"',
            "",
        ])
        (directory / ".github" / "labels.yml").write_text(declared, encoding="utf-8", newline="\n")
        with self.assertRaises(ValueError) as caught:
            catalogue.read_catalogue(directory)
        self.assertIn("101 characters", str(caught.exception))


class LabelPlanTests(unittest.TestCase):
    """A label diff creates what is absent, edits what differs, and deletes only what is retired."""

    def test_absent_declared_label_is_created(self) -> None:
        actions = catalogue.plan_labels({"a": ("FF0000", "d")}, [], {})
        self.assertEqual([(a.verb, a.name) for a in actions], [("create", "a")])

    def test_matching_label_produces_no_action(self) -> None:
        self.assertEqual(catalogue.plan_labels({"a": ("FF0000", "d")}, [], {"a": ("FF0000", "d")}), [])

    def test_drifted_colour_or_description_is_edited(self) -> None:
        for live in (("00FF00", "d"), ("FF0000", "other")):
            actions = catalogue.plan_labels({"a": ("FF0000", "d")}, [], {"a": live})
            self.assertEqual([(a.verb, a.name) for a in actions], [("edit", "a")])

    def test_undeclared_live_label_is_left_alone(self) -> None:
        """Deleting something nobody declared is not this tool's call."""
        self.assertEqual(catalogue.plan_labels({}, [], {"stray": ("FFFFFF", "")}), [])

    def test_retired_label_is_deleted_only_when_it_exists(self) -> None:
        self.assertEqual(catalogue.plan_labels({}, ["gone"], {}), [])
        actions = catalogue.plan_labels({}, ["gone"], {"gone": ("FFFFFF", "")})
        self.assertEqual([(a.verb, a.name) for a in actions], [("delete", "gone")])


class ContainmentTests(unittest.TestCase):
    """Containment follows village_issue and the epic's children, and never doubles a parent."""

    def test_epic_contains_villages_and_village_contains_its_bits(self) -> None:
        tickets = {
            1: {"kind": "epic-of-epics", "child_issues": ["#2"]},
            2: {"kind": "village"},
            7: {"kind": "bit", "parent": "#1", "village_issue": "#2"},
        }
        edges = {(edge.parent, edge.child) for edge in planner.containment_edges(tickets)}
        self.assertEqual(edges, {(1, 2), (2, 7)})

    def test_parent_is_not_the_containment_edge(self) -> None:
        """A bit may name the epic as parent while its village is the node that contains it."""
        tickets = {7: {"kind": "bit", "parent": "#1", "village_issue": "#4"}}
        self.assertEqual([(e.parent, e.child) for e in planner.containment_edges(tickets)], [(4, 7)])

    def test_an_issue_the_epic_placed_is_not_placed_again(self) -> None:
        """GitHub allows one parent, so the first placement wins and the second is dropped."""
        tickets = {
            1: {"kind": "epic-of-epics", "child_issues": ["#2"]},
            2: {"kind": "village", "village_issue": "#3"},
        }
        self.assertEqual([(e.parent, e.child) for e in planner.containment_edges(tickets)], [(1, 2)])

    def test_a_self_edge_is_refused(self) -> None:
        tickets = {4: {"kind": "village", "village_issue": "#4"}}
        self.assertEqual(planner.containment_edges(tickets), [])

    def test_an_edge_the_surface_already_holds_is_not_planned_again(self) -> None:
        """The plan must report what would change, not what the tree looks like from nothing."""
        tickets = {7: {"kind": "bit", "village_issue": "#4"}}
        self.assertEqual(planner.containment_edges(tickets, {7: 4}), [])
        self.assertEqual(len(planner.containment_edges(tickets, {7: 3})), 1)

    def test_held_parents_reads_the_captured_graph(self) -> None:
        path = export_file([
            {"number": 4, "title": "v", "state": "OPEN", "body": BODY, "labels": [], "parent": None},
            {"number": 7, "title": "b", "state": "OPEN", "body": BODY, "labels": [], "parent": 4},
        ])
        self.assertEqual(planner.held_parents(path), {7: 4})


class BodyBlockTests(unittest.TestCase):
    """The rendered block is additive, replaceable, and idempotent."""

    def test_block_is_appended_and_the_original_body_is_preserved_byte_for_byte(self) -> None:
        block, _ = planner.render_block({"requires": ["#6"]}, {6: "Shared Kernel"})
        updated = planner.apply_block(BODY, block)
        self.assertTrue(updated.startswith(BODY.rstrip("\n")))
        self.assertIn("- #6 — Shared Kernel", updated)

    def test_applying_the_same_block_twice_is_a_no_op(self) -> None:
        block, _ = planner.render_block({"requires": ["#6"]}, {})
        once = planner.apply_block(BODY, block)
        self.assertEqual(planner.apply_block(once, block), once)

    def test_a_changed_block_replaces_the_old_one_without_stacking(self) -> None:
        first, _ = planner.render_block({"requires": ["#6"]}, {})
        second, _ = planner.render_block({"requires": ["#7"]}, {})
        updated = planner.apply_block(planner.apply_block(BODY, first), second)
        self.assertEqual(updated.count(planner.BLOCK_BEGIN), 1)
        self.assertIn("- #7", updated)
        self.assertNotIn("- #6", updated)

    def test_an_issue_with_no_edges_gets_no_block(self) -> None:
        actions = planner.plan_bodies({7: {"kind": "bit"}}, {7: BODY}, {})
        self.assertEqual(actions, [])

    def test_a_story_renders_its_asks_with_the_adjustment_text(self) -> None:
        metadata = {"kind": "story", "asks": [{"of": "#12", "adjustment": "a scoped grant"}]}
        block, edges = planner.render_block(metadata, {})
        self.assertEqual(edges["asks"], [12])
        self.assertIn("- #12 — a scoped grant", block)

    def test_a_malformed_reference_is_dropped_not_guessed_at(self) -> None:
        block, edges = planner.render_block({"requires": ["six", "#0", "#6"]}, {})
        self.assertEqual(edges["requires"], [6])


class ExportTests(unittest.TestCase):
    """Loading an export separates parseable tickets from reported defects."""

    def test_an_issue_without_a_metadata_block_is_reported_not_guessed_at(self) -> None:
        path = export_file([
            {"number": 7, "title": "A bit", "state": "OPEN", "body": BODY, "labels": []},
            {"number": 52, "title": "Note", "state": "OPEN", "body": "just prose", "labels": []},
        ])
        metadata, bodies, titles, defects = planner.load_export(path)
        self.assertEqual(set(metadata), {7})
        self.assertEqual(titles[52], "Note")
        self.assertEqual(len(defects), 1)
        self.assertIn("#52", defects[0])

    def test_the_live_catalogue_comes_from_the_sidecar_not_the_worn_labels(self) -> None:
        """An unworn label must still read as present, or the plan creates what already exists."""
        path = export_file(
            [{"number": 7, "title": "t", "state": "OPEN", "body": BODY, "labels": []}],
            [{"name": "effect: record-local", "color": "D0D7DE", "description": "Default"}],
        )
        self.assertEqual(catalogue.live_labels(path), {"effect: record-local": ("D0D7DE", "Default")})

    def test_a_missing_sidecar_refuses_rather_than_planning_from_nothing(self) -> None:
        path = export_file([{"number": 7, "title": "t", "state": "OPEN", "body": BODY, "labels": []}])
        path.with_name(path.stem + ".labels.json").unlink()
        with self.assertRaises(FileNotFoundError):
            catalogue.live_labels(path)


class IssueLabelTests(unittest.TestCase):
    """Issue labels reconcile only within the governed axes."""

    def test_projected_labels_are_added_and_stale_governed_labels_removed(self) -> None:
        projection = catalogue.load_projection(ROOT)
        tickets = {53: {"kind": "implementation-stub", "village": "ground-and-evidence",
                        "horizon": "NOW", "standing": "DEMOTED"}}
        live = {53: ["type: stub", "village: ground", "horizon: now", "witness: demoted"]}
        actions, unmapped = catalogue.plan_issue_labels(tickets, live, projection)
        self.assertEqual(unmapped, [])
        self.assertEqual(actions[0].add, ("standing: demoted",))
        self.assertEqual(actions[0].remove, ("witness: demoted",))

    def test_a_label_outside_the_governed_axes_is_never_stripped(self) -> None:
        projection = catalogue.load_projection(ROOT)
        tickets = {7: {"kind": "bit", "village": "ground-and-evidence", "horizon": "NOW",
                       "standing": "OPEN"}}
        live = {7: ["type: bit", "village: ground", "horizon: now", "pinned-by-hand"]}
        actions, _ = catalogue.plan_issue_labels(tickets, live, projection)
        self.assertEqual(actions, [])

    def test_unmapped_metadata_skips_the_issue_rather_than_stripping_its_labels(self) -> None:
        projection = catalogue.load_projection(ROOT)
        tickets = {7: {"kind": "bit", "village": "ground-and-evidence", "horizon": "INVENTED"}}
        actions, unmapped = catalogue.plan_issue_labels(tickets, {7: ["type: bit"]}, projection)
        self.assertEqual(actions, [])
        self.assertEqual(len(unmapped), 1)


if __name__ == "__main__":
    unittest.main()
