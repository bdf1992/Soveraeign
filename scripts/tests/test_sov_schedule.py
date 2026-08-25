from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import shutil
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sovschedule import cron, jsonshape, ledger, runner  # noqa: E402
from sovschedule.declaration import DeclarationError, load_all, load_declaration  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[2]
ENVELOPE_SCHEMA = json.loads(
    (REPO_ROOT / "contracts" / "event-envelope.schema.json").read_text(encoding="utf-8")
)
FIXED_NOW = datetime(2026, 8, 22, 2, 0, tzinfo=timezone.utc)
BASE = {
    "name": "nightly-qa",
    "enabled": True,
    "target": {"kind": "workflow", "name": "sov-qa", "args": {"focus": "tree"}},
    "cron": "0 2 * * *",
    "mode": "observe",
    "effect_class": "RESOURCE_CONSUMPTION",
    "preconditions": {"clean_tree": False},
    "limits": {"max_budget_usd": 5, "timeout_seconds": 600},
}


def clean_probe(_: Path) -> dict:
    return {"head": "abc123\n", "status": ""}


def dirty_probe(_: Path) -> dict:
    return {"head": "abc123\n", "status": " M AGENTS.md\n?? reports/\n"}


class ScheduleRoot(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        schedules = self.root / ".claude" / "schedules"
        schedules.mkdir(parents=True)
        shutil.copy(REPO_ROOT / ".claude" / "schedules" / "schedule.schema.json", schedules)
        (self.root / ".claude" / "workflows").mkdir()
        (self.root / ".claude" / "workflows" / "sov-qa.js").write_text("// stub\n", encoding="utf-8")
        (self.root / ".claude" / "skills" / "sov-scribe").mkdir(parents=True)
        (self.root / ".claude" / "skills" / "sov-scribe" / "SKILL.md").write_text("# stub\n", encoding="utf-8")
        (self.root / "reports").mkdir()
        self.calls: list[list[str]] = []

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def declare(self, **overrides):
        raw = json.loads(json.dumps(BASE))
        raw.update(overrides)
        path = self.root / ".claude" / "schedules" / f"{raw['name']}.json"
        path.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
        return load_declaration(self.root, path)

    def invoker(self, exit_code: int = 0, write_report: bool = True):
        def invoke(command: list[str], cwd: Path, timeout: int) -> tuple[int, str, str]:
            self.calls.append(command)
            if write_report:
                (cwd / "reports" / "2026-08-22-nightly-qa.md").write_text("# report\n", encoding="utf-8")
            return exit_code, '{"result": "ok"}', ""
        return invoke

    def events(self, name: str = "nightly-qa") -> list[dict]:
        return [entry["event"] for entry in ledger.read(self.root, name)]


class DeclarationChecks(ScheduleRoot):
    def test_valid_declaration_loads(self):
        decl = self.declare()
        self.assertEqual(decl.target_name, "sov-qa")
        self.assertEqual(decl.spec.expression, "0 2 * * *")
        self.assertFalse(decl.clean_tree)

    def test_external_world_is_refused(self):
        with self.assertRaisesRegex(DeclarationError, "EXTERNAL_WORLD refused"):
            self.declare(effect_class="EXTERNAL_WORLD")

    def test_unknown_workflow_is_refused(self):
        with self.assertRaisesRegex(DeclarationError, "not found under .claude/"):
            self.declare(target={"kind": "workflow", "name": "sov-nope"})

    def test_bad_cron_is_refused(self):
        with self.assertRaisesRegex(DeclarationError, "cron"):
            self.declare(cron="61 2 * * *")

    def test_schema_defect_is_refused(self):
        with self.assertRaisesRegex(DeclarationError, "limits"):
            self.declare(limits={"max_budget_usd": 5})

    def test_build_on_dirty_shared_tree_is_refused_at_load(self):
        with self.assertRaisesRegex(DeclarationError, "clean_tree true or isolation worktree"):
            self.declare(mode="build", preconditions={"clean_tree": False})

    def test_build_defaults_to_clean_tree(self):
        decl = self.declare(mode="build", preconditions={})
        self.assertTrue(decl.clean_tree)

    def test_repository_declarations_validate(self):
        names = [decl.name for decl in load_all(REPO_ROOT)]
        self.assertIn("nightly-qa", names)
        self.assertTrue(all(not decl.enabled for decl in load_all(REPO_ROOT)))


class CronMatching(unittest.TestCase):
    def test_daily_due_once_in_window(self):
        spec = cron.parse("0 2 * * *")
        due = cron.first_due(spec, datetime(2026, 8, 22, 1, 0), datetime(2026, 8, 22, 3, 0))
        self.assertEqual(due, datetime(2026, 8, 22, 2, 0))
        self.assertIsNone(cron.first_due(spec, datetime(2026, 8, 22, 2, 0), datetime(2026, 8, 22, 3, 0)))

    def test_step_and_weekday_subset(self):
        self.assertTrue(cron.matches(cron.parse("*/15 * * * *"), datetime(2026, 8, 22, 4, 45)))
        weekdays = cron.parse("0 9 * * 1-5")
        self.assertFalse(cron.matches(weekdays, datetime(2026, 8, 22, 9, 0)))  # Saturday
        self.assertTrue(cron.matches(weekdays, datetime(2026, 8, 24, 9, 0)))  # Monday
        self.assertTrue(cron.matches(cron.parse("0 9 * * 7"), datetime(2026, 8, 23, 9, 0)))  # Sunday

    def test_rejects_out_of_range_and_wrong_arity(self):
        with self.assertRaises(ValueError):
            cron.parse("0 24 * * *")
        with self.assertRaises(ValueError):
            cron.parse("0 2 * *")


class RunnerGates(ScheduleRoot):
    def test_observe_run_records_attempt_and_report(self):
        decl = self.declare()
        result = runner.execute(self.root, decl, clock=lambda: FIXED_NOW,
                                invoke=self.invoker(), probe=dirty_probe)
        self.assertEqual(result.phase, "REPORTED")
        self.assertEqual(result.outcome, "ATTEMPTED")
        self.assertEqual(result.report_paths, ["reports/2026-08-22-nightly-qa.md"])
        events = self.events()
        self.assertEqual([e["event_phase"] for e in events], ["ATTEMPTED", "REPORTED"])
        self.assertEqual([e["actor_kind"] for e in events], ["SYSTEM", "MODEL"])
        for event in events:
            self.assertEqual(jsonshape.check(event, ENVELOPE_SCHEMA), [])
        self.assertTrue(any(o["address"] == "reports/2026-08-22-nightly-qa.md" for o in events[1]["outputs"]))
        self.assertTrue(result.capture_path.is_file())
        self.assertFalse(ledger.Lock(self.root).holder())

    def test_command_is_headless_controller_without_commit_rights(self):
        decl = self.declare()
        runner.execute(self.root, decl, clock=lambda: FIXED_NOW, invoke=self.invoker(), probe=clean_probe)
        command = self.calls[0]
        self.assertEqual(command[:2], ["claude", "-p"])
        self.assertIn('Run the workflow named "sov-qa"', command[2])
        self.assertIn("sov-controller", command)
        self.assertIn("dontAsk", command)
        allowed = command[command.index("--allowedTools") + 1]
        forbidden = command[command.index("--disallowedTools") + 1]
        self.assertIn("Workflow", allowed)
        self.assertNotIn("Edit", allowed)
        self.assertIn("Bash(git commit*)", forbidden)
        self.assertIn("Bash(git push*)", forbidden)

    def test_build_mode_refuses_dirty_tree_without_invoking(self):
        decl = self.declare(name="nightly-build", mode="build", preconditions={"clean_tree": True})
        result = runner.execute(self.root, decl, clock=lambda: FIXED_NOW,
                                invoke=self.invoker(), probe=dirty_probe)
        self.assertEqual((result.phase, result.outcome, result.reason_code), ("ATTEMPTED", "REFUSED", "TREE_DIRTY"))
        self.assertEqual(self.calls, [])
        events = self.events("nightly-build")
        self.assertEqual(events[-1]["outcome"], "REFUSED")
        self.assertEqual(jsonshape.check(events[-1], ENVELOPE_SCHEMA), [])

    def test_build_mode_allows_edit_and_clean_tree(self):
        decl = self.declare(name="nightly-build", mode="build", preconditions={"clean_tree": True})
        result = runner.execute(self.root, decl, clock=lambda: FIXED_NOW, invoke=self.invoker(), probe=clean_probe)
        self.assertEqual(result.phase, "REPORTED")
        self.assertIn("Edit", self.calls[0][self.calls[0].index("--allowedTools") + 1])

    def test_held_lock_refuses_run_in_progress(self):
        decl = self.declare()
        ledger.Lock(self.root).acquire("other-run", FIXED_NOW, 3600)
        result = runner.execute(self.root, decl, clock=lambda: FIXED_NOW, invoke=self.invoker(), probe=clean_probe)
        self.assertEqual(result.reason_code, "RUN_IN_PROGRESS")
        self.assertEqual(self.calls, [])

    def test_disabled_schedule_refused_unless_forced(self):
        decl = self.declare(enabled=False)
        refused = runner.execute(self.root, decl, clock=lambda: FIXED_NOW, invoke=self.invoker(), probe=clean_probe)
        self.assertEqual(refused.reason_code, "SCHEDULE_DISABLED")
        forced = runner.execute(self.root, decl, clock=lambda: FIXED_NOW, invoke=self.invoker(),
                                probe=clean_probe, force=True)
        self.assertEqual(forced.phase, "REPORTED")

    def test_nonzero_exit_is_reported_failed(self):
        decl = self.declare()
        result = runner.execute(self.root, decl, clock=lambda: FIXED_NOW,
                                invoke=self.invoker(exit_code=3, write_report=False), probe=clean_probe)
        self.assertEqual(result.outcome, "FAILED")
        self.assertEqual(self.events()[-1]["outcome"], "FAILED")

    def test_skill_target_prompt_and_worktree_flag(self):
        decl = self.declare(name="weekly-scribe", target={"kind": "skill", "name": "sov-scribe", "args": {}},
                            isolation="worktree")
        runner.execute(self.root, decl, clock=lambda: FIXED_NOW, invoke=self.invoker(), probe=clean_probe)
        self.assertIn('Invoke the "/sov-scribe" skill', self.calls[0][2])
        self.assertIn("--worktree", self.calls[0])

    def test_due_uses_lookback_then_last_attempt(self):
        decl = self.declare()
        self.assertEqual(runner.is_due(self.root, decl, FIXED_NOW, tz=timezone.utc),
                         datetime(2026, 8, 22, 2, 0))
        runner.execute(self.root, decl, clock=lambda: FIXED_NOW, invoke=self.invoker(), probe=clean_probe)
        self.assertIsNone(runner.is_due(self.root, decl, FIXED_NOW, tz=timezone.utc))
        later = datetime(2026, 8, 23, 2, 30, tzinfo=timezone.utc)
        self.assertEqual(runner.is_due(self.root, decl, later, tz=timezone.utc), datetime(2026, 8, 23, 2, 0))


class EnvelopeShape(unittest.TestCase):
    def test_defeating_envelope_fails_contract(self):
        event = ledger.envelope(
            event_id="e", operation_id="o", phase="REPORTED", actor_id="a", actor_kind="MODEL",
            reason="r", occurred_at="2026-08-22T00:00:00Z", inputs=[], outputs=[],
            effect_class="RESOURCE_CONSUMPTION", outcome="ATTEMPTED",
        )
        self.assertEqual(jsonshape.check(event, ENVELOPE_SCHEMA), [])
        event["effect_class"] = "EXTERNAL_WORLD_LATER"
        event["extra"] = True
        defects = jsonshape.check(event, ENVELOPE_SCHEMA)
        self.assertTrue(any("effect_class" in d for d in defects))
        self.assertTrue(any("unexpected property 'extra'" in d for d in defects))


if __name__ == "__main__":
    unittest.main()
