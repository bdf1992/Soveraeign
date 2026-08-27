"""Drive the authoring corpus: creating a schedule declaration and editing one.

`conformance/fixtures/automation-control/cases.json` carries these under
`authoring_cases`. This module executes them against the real operations and adds what a
corpus cannot state: that the form only offers targets the save accepts, that a refused
edit leaves the file exactly as it was, and that the two holes the authority rule exists
to close stay closed.

Those two holes are worth naming, because closing the switch and leaving these open
would have been worse than leaving all three open - it would have looked finished. A
model that may not arm a schedule can otherwise create one already armed, or leave the
switch alone and repoint an armed schedule at something else.

A passing run establishes `BUILT`. It witnesses nothing.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import shutil
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovschedule import authoring, changelog, control, pageform  # noqa: E402

CORPUS = json.loads(
    (ROOT / "conformance" / "fixtures" / "automation-control" / "cases.json")
    .read_bytes().decode("utf-8"))
CASES = CORPUS["authoring_cases"]

NOW = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)

EXISTING = {
    "name": "code-review", "description": "the one already here", "enabled": False,
    "target": {"kind": "workflow", "name": "sov-review", "args": {}},
    "cron": "0 2 * * *", "mode": "observe", "effect_class": "RESOURCE_CONSUMPTION",
    "isolation": "tree", "preconditions": {"clean_tree": False},
    "limits": {"max_budget_usd": 3, "timeout_seconds": 2700},
}


class Tree(unittest.TestCase):
    """A repository holding two workflows and whatever the case declares."""

    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.schedules = self.root / ".claude" / "schedules"
        self.schedules.mkdir(parents=True)
        shutil.copy(ROOT / ".claude" / "schedules" / "schedule.schema.json", self.schedules)
        workflows = self.root / ".claude" / "workflows"
        workflows.mkdir()
        for name in ("sov-review", "sov-qa"):
            (workflows / f"{name}.js").write_text("// stub\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def actor(self, kind: str) -> control.Actor:
        return (control.owner(control.BINDING_CONSOLE) if kind == "owner"
                else control.model("urn:soveraeign:actor:test-model"))

    def place(self, overrides: dict | None, name: str = "code-review") -> Path:
        body = dict(EXISTING, name=name)
        body.update(overrides or {})
        path = self.schedules / f"{name}.json"
        path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8",
                        newline="\n")
        return path

    def body_of(self, name: str = "code-review") -> dict:
        return json.loads((self.schedules / f"{name}.json").read_text(encoding="utf-8"))


class DeclaredCorpus(Tree):
    """Every authoring case in the fixture file, run against the real operations."""

    def test_every_case_decides_what_it_declares(self) -> None:
        for case in CASES:
            with self.subTest(case=case["case_id"]):
                self.tearDown()
                self.setUp()
                if case["existing"] is not None:
                    self.place(case["existing"])
                request = case["request"]
                actor = self.actor(request["actor"])
                if case["change"] == "CREATE":
                    outcome = authoring.create(self.root, request["name"],
                                               dict(request["body"]), actor,
                                               request["reason"], now=NOW)
                else:
                    outcome = authoring.update(self.root, request["name"],
                                               dict(request["changes"]), actor,
                                               request["reason"], now=NOW)
                self.assertEqual(outcome.outcome, case["expect_outcome"])
                self.assertEqual(outcome.refusal_code, case["expect_refusal"])
                path = self.schedules / f"{request['name']}.json"
                self.assertEqual(path.is_file(), case["expect_exists_after"])

    def test_every_declared_refusal_has_a_case(self) -> None:
        """A refusal nothing exercises is prose, not a refusal."""
        reached = {case["expect_refusal"] for case in CASES} - {None}
        for code in authoring.REFUSALS:
            with self.subTest(code=code):
                self.assertIn(code, reached)

    def test_every_refusal_has_a_case_that_does_not_fire_it(self) -> None:
        for code in {c["expect_refusal"] for c in CASES} - {None}:
            with self.subTest(code=code):
                self.assertTrue([c["case_id"] for c in CASES
                                 if c["expect_refusal"] != code])


class TheTwoHoles(Tree):
    """What the switch authority would be worth without these."""

    def test_a_model_cannot_arm_by_creating_something_already_armed(self) -> None:
        body = dict(EXISTING, enabled=True)
        outcome = authoring.create(self.root, "sneaky", body,
                                   self.actor("model"), "arming by the back door", now=NOW)
        self.assertEqual(outcome.refusal_code, "GRANT_NOT_HELD")
        self.assertFalse((self.schedules / "sneaky.json").exists())

    def test_a_model_cannot_repoint_an_armed_schedule(self) -> None:
        """Leaving the switch alone and changing what it runs is the same commitment."""
        self.place({"enabled": True})
        for change in ({"target": {"kind": "workflow", "name": "sov-qa", "args": {}}},
                       {"limits": {"max_budget_usd": 500, "timeout_seconds": 2700}},
                       {"mode": "build"},
                       {"cron": "* * * * *"}):
            with self.subTest(field=next(iter(change))):
                outcome = authoring.update(self.root, "code-review", change,
                                           self.actor("model"), "while it is armed",
                                           now=NOW)
                self.assertEqual(outcome.refusal_code, "GRANT_NOT_HELD")
        self.assertEqual(self.body_of()["cron"], "0 2 * * *")

    def test_switching_it_off_first_is_the_route(self) -> None:
        """Named so the refusal's advice is executable, not just wording."""
        self.place({"enabled": True})
        model = self.actor("model")
        self.assertEqual(control.set_switch(self.root, "code-review", "DISABLE", model,
                                            "stopping it to edit it", now=NOW).outcome,
                         changelog.EFFECTED)
        self.assertEqual(authoring.update(self.root, "code-review", {"cron": "0 4 * * *"},
                                          model, "now editable", now=NOW).outcome,
                         changelog.EFFECTED)


class TheFileIsLeftAlone(Tree):
    """A validating write must not leave behind a defect the operator did not type."""

    def test_a_refused_edit_restores_every_byte(self) -> None:
        path = self.place({"enabled": False})
        before = path.read_bytes()
        outcome = authoring.update(self.root, "code-review", {"cron": "nonsense"},
                                   self.actor("owner"), "breaking it", now=NOW)
        self.assertEqual(outcome.refusal_code, "INVALID_DECLARATION")
        self.assertEqual(path.read_bytes(), before)

    def test_a_refused_create_leaves_no_file(self) -> None:
        outcome = authoring.create(self.root, "half-made",
                                   dict(EXISTING, cron="nonsense"),
                                   self.actor("owner"), "breaking it", now=NOW)
        self.assertEqual(outcome.refusal_code, "INVALID_DECLARATION")
        self.assertFalse((self.schedules / "half-made.json").exists())

    def test_the_refusal_is_the_loaders_own_wording(self) -> None:
        """Two descriptions of one defect drift. There is only one here."""
        outcome = authoring.create(self.root, "half-made",
                                   dict(EXISTING, cron="nonsense"),
                                   self.actor("owner"), "breaking it", now=NOW)
        self.assertIn("cron", outcome.detail)
        self.assertIn("half-made.json", outcome.detail)

    def test_an_edit_writes_only_the_fields_it_was_given(self) -> None:
        self.place({"enabled": False})
        authoring.update(self.root, "code-review", {"cron": "0 4 * * *"},
                         self.actor("owner"), "quieter", now=NOW)
        body = self.body_of()
        self.assertEqual(body["cron"], "0 4 * * *")
        self.assertEqual(body["description"], EXISTING["description"])
        self.assertEqual(body["target"], EXISTING["target"])
        self.assertFalse(body["enabled"])


class TheFormOffersOnlyWhatSaves(Tree):
    """A dropdown that offers a choice the save refuses is a trap, not a control."""

    def test_every_offered_target_is_one_the_loader_accepts(self) -> None:
        offered = authoring.targets(self.root)
        self.assertEqual({t["name"] for t in offered}, {"sov-review", "sov-qa"})
        for target in offered:
            with self.subTest(target=target["name"]):
                outcome = authoring.create(
                    self.root, f"probe-{target['name']}",
                    dict(EXISTING, target={"kind": target["kind"],
                                           "name": target["name"], "args": {}}),
                    self.actor("owner"), "checking the dropdown", now=NOW)
                self.assertEqual(outcome.outcome, changelog.EFFECTED, outcome.detail)

    def test_the_form_offers_no_effect_class_the_phase_refuses(self) -> None:
        self.assertNotIn("EXTERNAL_WORLD", pageform.EFFECTS)
        outcome = authoring.create(self.root, "worldly",
                                   dict(EXISTING, effect_class="EXTERNAL_WORLD"),
                                   self.actor("owner"), "trying it", now=NOW)
        self.assertEqual(outcome.refusal_code, "EXTERNAL_WORLD_REFUSED")

    def test_the_form_renders_every_field_the_declaration_carries(self) -> None:
        rendered = pageform.render(authoring.targets(self.root), authoring.blank("x"),
                                   "a-token", creating=True)
        for field in ("name", "description", "target", "cron", "mode", "effect_class",
                      "isolation", "reason"):
            with self.subTest(field=field):
                self.assertIn(f'name="{field}"', rendered)

    def test_the_edit_form_cannot_rename(self) -> None:
        """The name input is disabled, and the operation refuses it anyway."""
        rendered = pageform.render([], dict(EXISTING), "a-token", creating=False)
        self.assertIn("disabled", rendered)
        self.assertNotIn("name", authoring.EDITABLE)


class TheRecord(Tree):
    """One log for all three changes, so an operator reads one file."""

    def test_a_create_and_an_edit_and_a_switch_land_in_one_log(self) -> None:
        owner = self.actor("owner")
        authoring.create(self.root, "code-review", dict(EXISTING), owner, "new", now=NOW)
        authoring.update(self.root, "code-review", {"cron": "0 4 * * *"}, owner,
                         "quieter", now=NOW)
        control.set_switch(self.root, "code-review", "ENABLE", owner, "arming", now=NOW)
        entries = changelog.read(self.root)
        self.assertEqual([e.change for e in entries],
                         [changelog.CREATE, changelog.UPDATE, changelog.SWITCH])
        self.assertEqual([e.outcome for e in entries], [changelog.EFFECTED] * 3)

    def test_an_edit_records_which_fields_moved(self) -> None:
        self.place({"enabled": False})
        authoring.update(self.root, "code-review",
                         {"cron": "0 4 * * *", "description": "reworded"},
                         self.actor("owner"), "two at once", now=NOW)
        entry = changelog.read(self.root)[-1]
        self.assertEqual(sorted(entry.fields), ["cron", "description"])
        self.assertNotEqual(entry.before_digest, entry.after_digest)

    def test_a_refused_authoring_attempt_is_recorded(self) -> None:
        authoring.create(self.root, "sneaky", dict(EXISTING, enabled=True),
                         self.actor("model"), "arming by the back door", now=NOW)
        entry = changelog.read(self.root)[-1]
        self.assertEqual(entry.outcome, changelog.REFUSED)
        self.assertEqual(entry.refusal_code, "GRANT_NOT_HELD")
        self.assertEqual(entry.change, changelog.CREATE)


if __name__ == "__main__":
    unittest.main()
