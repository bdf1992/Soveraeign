"""Stories in the epic walk: told by a participant, walked through a scenario, never taken."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sovepic import survey, walk  # noqa: E402
from sovepic.projection import Issue  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[2]


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


class StoryTests(unittest.TestCase):
    """A story is told by a participant and walked through a scenario; it is never taken."""

    def story(self, standing="PROPOSED", scenario=None, leans_on=("#6",)):
        return issue(
            60,
            metadata={
                "kind": "story",
                "parent": "#6",
                "village_issue": "#4",
                "standing": standing,
                "scenario": scenario,
                "leans_on": list(leans_on),
                "asks": [{"of": "#6", "adjustment": "exist"}],
            },
        )

    def tree(self, support_standing="OPEN", story=None):
        return {
            1: issue(1, metadata={"kind": "epic-of-epics", "child_issues": ["#4"]}),
            4: issue(4, metadata={"kind": "village", "parent": "#1", "child_issues": ["#6", "#60"]}),
            6: issue(6, metadata={"kind": "bit", "parent": "#1", "village_issue": "#4",
                                  "standing": support_standing}),
            60: story or self.story(),
        }

    def test_a_told_story_names_the_supports_still_short(self):
        reading, short = walk.story_reading(self.story(), self.tree())
        self.assertEqual((reading, short), ("told", ["#6"]))

    def test_a_bound_story_over_built_supports_is_walkable(self):
        story = self.story("DECLARED_NOT_IMPLEMENTED", "RUN-I1-PROPOSE")
        tree = self.tree("BUILT_SELF_TESTED_NOT_WITNESSED", story)
        self.assertEqual(walk.story_reading(story, tree), ("walkable", []))

    def test_a_bound_story_over_open_supports_stays_told(self):
        story = self.story("DECLARED_NOT_IMPLEMENTED", "RUN-I1-PROPOSE")
        self.assertEqual(walk.story_reading(story, self.tree(story=story)), ("told", ["#6"]))

    def test_only_a_witnessed_story_reads_as_walked(self):
        built = self.story("BUILT_SELF_TESTED_NOT_WITNESSED", "RUN-I1-PROPOSE")
        tree = self.tree("WITNESSED", built)
        self.assertEqual(walk.story_reading(built, tree)[0], "walkable")
        witnessed = self.story("WITNESSED", "RUN-I1-PROPOSE")
        self.assertEqual(walk.story_reading(witnessed, tree)[0], "walked")

    def test_a_story_must_walk_up_to_a_live_bit(self):
        self.assertEqual(walk.containment_defects(self.tree(), 1), [])
        tree = self.tree()
        tree[60] = issue(60, metadata={**tree[60].metadata, "parent": "#4"})
        self.assertIn(
            "#60: story parent #4 is not a live bit (the counter)",
            walk.containment_defects(tree, 1),
        )

    def test_a_story_leaning_on_nothing_present_is_reported(self):
        tree = self.tree(story=self.story(leans_on=("#99",)))
        self.assertIn("#60: leans on #99, which is not present", walk.containment_defects(tree, 1))

    def test_a_story_never_enters_ready_held_or_unrouted(self):
        document = {
            "source": {"root_issue": 1},
            "synced_at": "2026-08-23T00:00:00Z",
            "issues": {str(n): _record(i) for n, i in self.tree().items()},
        }
        result = survey.survey(REPO_ROOT, document, {"issue_routes": {}})
        listed = {e["issue"] for e in result["ready"] + result["held"] + result["unrouted"]}
        self.assertNotIn(60, listed)
        self.assertEqual(result["counts"]["stories"], 1)
        self.assertEqual(result["stories"][0]["reading"], "told")


def _record(item: Issue) -> dict:
    return {
        "number": item.number,
        "title": item.title,
        "state": item.state,
        "labels": list(item.labels),
        "url": item.url,
        "updated_at": item.updated_at,
        "metadata": item.metadata,
        "parse_error": item.parse_error,
    }

if __name__ == "__main__":
    unittest.main()
