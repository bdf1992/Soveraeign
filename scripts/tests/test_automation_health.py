"""Drive the declared automation-health corpus, and the couplings a fixture cannot state.

`conformance/fixtures/automation-health/cases.json` holds the positive and defeating
pair for every rule in `contracts/automation-health.json`. This module executes that
corpus and adds the cases a corpus cannot reach: that the table and the code agree on
which rules exist, that the corpus actually exercises both sides of every rule, and
that the runner's own refusal wording is what `history.py` parses - a coupling across
two modules that would otherwise fail silently, turning every refusal into an
unreadable one and taking REFUSAL_LOOP quiet with it.

A passing run establishes `BUILT` for the rules. It witnesses nothing.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import contextlib
import io
import json
import shutil
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovschedule import health, history, ledger, page, report, runner, surface  # noqa: E402
from sovschedule.declaration import load_declaration  # noqa: E402

CORPUS = json.loads(
    (ROOT / "conformance" / "fixtures" / "automation-health" / "cases.json")
    .read_bytes().decode("utf-8"))
TABLE = health.load()


def facts_of(case: dict) -> health.Facts:
    """Build judge input from one declared case. No file is read."""
    schedule = case["schedule"]
    return health.Facts(
        name=schedule["name"],
        enabled=schedule["enabled"],
        target_exists=schedule["target_exists"],
        cron_expression=schedule["cron"],
        timeout_seconds=schedule["timeout_seconds"],
        now=ledger.parse_timestamp(case["now"]),
        runs=tuple(history.from_records(case["runs"])),
        declaration_defect=schedule.get("declaration_defect"),
    )


class DeclaredCorpus(unittest.TestCase):
    """Every case in the fixture file, judged against the live table."""

    def test_every_case_derives_the_statuses_findings_and_reading_declared(self) -> None:
        for case in CORPUS["cases"]:
            with self.subTest(case=case["case_id"]):
                reading = health.judge(facts_of(case), TABLE)
                self.assertEqual(list(reading.statuses), case["expect_status"])
                self.assertEqual(sorted(f.rule for f in reading.findings),
                                 sorted(case["expect_findings"]))
                self.assertEqual(reading.reading, case["expect_reading"])

    def test_every_rule_carries_a_firing_case_and_a_quiet_case(self) -> None:
        """A rule with only a firing case proves nothing about what it lets past."""
        for rule in TABLE["rules"]:
            fires = [c["case_id"] for c in CORPUS["cases"] if rule in c["expect_findings"]]
            quiet = [c["case_id"] for c in CORPUS["cases"] if rule not in c["expect_findings"]]
            with self.subTest(rule=rule):
                self.assertTrue(fires, f"{rule} has no case that fires it")
                self.assertTrue(quiet, f"{rule} has no case that proves it stays quiet")

    def test_a_quiet_case_exists_that_could_have_fired_each_rule(self) -> None:
        """The stronger reading of quiet: the rule's own inputs are present and it holds.

        A rule is trivially quiet on a case that never touches it. Each entry names the
        case that puts the rule's inputs in front of it and still gets nothing.
        """
        near_misses = {
            "TARGET_MISSING": "H-002-seven-declared-none-enabled-nothing-ever-run-is-not-healthy",
            "DECLARATION_REFUSED":
                "H-001-a-declaration-pointing-at-nothing-refuses-even-switched-off",
            "ENABLED_NEVER_RUN": "H-004-one-attempt-is-enough-to-silence-never-run",
            "LAST_RUN_FAILED": "H-006-the-newest-settled-run-is-what-is-read",
            "CONSECUTIVE_FAILURES": "H-008-a-run-in-flight-is-neither-a-pass-nor-a-failure",
            "RUNTIME_REGRESSION": "H-011-a-big-multiple-of-a-tiny-number-is-not-drift",
            "REFUSAL_LOOP": "H-023-two-identical-refusals-are-not-yet-a-loop-and-are-not-healthy",
            "EMPTY_RUN": "H-004-one-attempt-is-enough-to-silence-never-run",
            "OVERDUE": "H-024-one-missed-occurrence-is-not-yet-overdue",
        }
        self.assertEqual(sorted(near_misses), sorted(TABLE["rules"]))
        by_id = {case["case_id"]: case for case in CORPUS["cases"]}
        for rule, case_id in near_misses.items():
            with self.subTest(rule=rule):
                self.assertIn(case_id, by_id, f"{rule} names a case that is not in the corpus")
                self.assertNotIn(rule, by_id[case_id]["expect_findings"])

    def test_the_corpus_reaches_every_reading_and_every_run_status(self) -> None:
        """A corpus that never produced UNHEALTHY would prove nothing refuses."""
        readings = {case["expect_reading"] for case in CORPUS["cases"]}
        self.assertEqual(readings, set(TABLE["readings"]["order"]))
        statuses = {s for case in CORPUS["cases"] for s in case["expect_status"]}
        self.assertEqual(statuses, set(TABLE["run_status"]["values"]))


class TableAndCodeAgree(unittest.TestCase):
    """The table declares the rules; this module applies them. Neither may drift."""

    def test_every_declared_rule_has_a_derivation(self) -> None:
        self.assertEqual(sorted(TABLE["rules"]), sorted(health.DERIVATIONS))

    def test_a_rule_declared_without_a_derivation_refuses_rather_than_never_firing(self) -> None:
        table = json.loads(json.dumps(TABLE))
        table["rules"]["INVENTED_RULE"] = {"severity": "UNHEALTHY", "needs": "declaration"}
        facts = facts_of(CORPUS["cases"][0])
        with self.assertRaises(health.UnderivedRule):
            health.judge(facts, table)

    def test_the_settled_statuses_match_the_table(self) -> None:
        self.assertEqual(sorted(health.SETTLED_STATUSES), sorted(TABLE["run_status"]["settled"]))

    def test_the_refusing_reading_is_the_one_the_table_names(self) -> None:
        refuses_at = TABLE["blocking"]["refuses_at"]
        fired = [health.Finding("R", refuses_at, "d")]
        self.assertEqual(health.reading_of(fired, True, TABLE), refuses_at)
        self.assertTrue(health.Reading("s", refuses_at, (), ()).refuses)

    def test_no_findings_and_no_history_is_unobserved_not_healthy(self) -> None:
        self.assertEqual(health.reading_of([], False, TABLE), "UNOBSERVED")
        self.assertEqual(health.reading_of([], True, TABLE), "HEALTHY")
        self.assertEqual(health.worst([], TABLE), "UNOBSERVED")


class LedgerReading(unittest.TestCase):
    """What history.py reads out of the records the runner actually writes."""

    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        schedules = self.root / ".claude" / "schedules"
        schedules.mkdir(parents=True)
        shutil.copy(ROOT / ".claude" / "schedules" / "schedule.schema.json", schedules)
        (self.root / ".claude" / "workflows").mkdir()
        (self.root / ".claude" / "workflows" / "sov-qa.js").write_text("// stub\n",
                                                                      encoding="utf-8")
        self.declaration = {
            "name": "nightly-qa", "enabled": False,
            "target": {"kind": "workflow", "name": "sov-qa"},
            "cron": "0 2 * * *", "mode": "observe", "effect_class": "RESOURCE_CONSUMPTION",
            "preconditions": {"clean_tree": False},
            "limits": {"max_budget_usd": 5, "timeout_seconds": 600},
        }
        (schedules / "nightly-qa.json").write_text(
            json.dumps(self.declaration, indent=2) + "\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_the_runners_refusal_wording_is_what_history_parses(self) -> None:
        """The coupling neither module can state alone.

        `runner.execute` writes the reason code inside a sentence. If that sentence
        changes, every refusal becomes unreadable here and REFUSAL_LOOP goes quiet
        forever while looking like a rule that simply never fires.
        """
        decl = load_declaration(self.root, self.root / ".claude" / "schedules"
                                / "nightly-qa.json")
        result = runner.execute(self.root, decl, probe=lambda _: {"head": "a", "status": ""},
                                invoke=lambda *_: (0, "", ""))
        self.assertEqual(result.reason_code, "SCHEDULE_DISABLED")
        runs = history.runs_for(self.root, "nightly-qa")
        self.assertEqual([run.reason_code for run in runs], ["SCHEDULE_DISABLED"])
        self.assertEqual(
            [health.run_status(run, decl.timeout_seconds, datetime.now(timezone.utc))
             for run in runs], ["REFUSED"])

    def test_a_run_is_paired_on_its_id_not_on_adjacency(self) -> None:
        """A tick that fires two schedules interleaves their events in one ledger."""
        moment = datetime(2026, 8, 27, 2, 0, tzinfo=timezone.utc)
        for name, run_id in (("nightly-qa", "qa-1"), ("code-review", "cr-1")):
            ledger.append(self.root, name, run_id, ledger.envelope(
                event_id=f"e:{run_id}:a", operation_id="op", phase="ATTEMPTED",
                actor_id="a", actor_kind="SYSTEM", reason="due",
                occurred_at=ledger.timestamp(moment), inputs=[], outputs=[],
                effect_class="RECORD_LOCAL", outcome="ATTEMPTED"))
        for name, run_id, outcome in (("code-review", "cr-1", "FAILED"),
                                      ("nightly-qa", "qa-1", "ATTEMPTED")):
            ledger.append(self.root, name, run_id, ledger.envelope(
                event_id=f"e:{run_id}:r", operation_id="op", phase="REPORTED",
                actor_id="m", actor_kind="MODEL", reason="exit",
                occurred_at=ledger.timestamp(moment.replace(minute=30)), inputs=[],
                outputs=[], effect_class="RECORD_LOCAL", outcome=outcome))
        qa = history.runs_for(self.root, "nightly-qa")
        review = history.runs_for(self.root, "code-review")
        self.assertEqual([run.report_outcome for run in qa], ["ATTEMPTED"])
        self.assertEqual([run.report_outcome for run in review], ["FAILED"])
        self.assertEqual(qa[0].duration_seconds, 1800.0)

    def test_an_absent_ledger_is_reported_as_absent_not_as_no_runs(self) -> None:
        state = history.ledger_state(self.root)
        self.assertFalse(state.present)
        self.assertEqual(state.entries, 0)
        self.assertIn(".local/schedules/ledger.ndjson", state.absent_reason)
        digest = report.assemble(self.root, datetime(2026, 8, 27, 4, 0, tzinfo=timezone.utc),
                                 utc_offset=timedelta(0))
        self.assertEqual(digest.reading, "UNOBSERVED")
        self.assertEqual(digest.counts, {"declared": 1, "enabled": 0, "with_history": 0,
                                         "findings": 0, "refusing": 0})

    def test_a_row_carries_what_bdo_asked_to_see(self) -> None:
        digest = report.assemble(self.root, datetime(2026, 8, 27, 4, 0, tzinfo=timezone.utc),
                                 utc_offset=timedelta(0))
        row = digest.rows[0]
        self.assertFalse(row.enabled)
        self.assertEqual(row.next_due, datetime(2026, 8, 28, 2, 0, tzinfo=timezone.utc))
        self.assertIsNone(row.last_attempted_at)
        self.assertIsNone(row.last_status)
        self.assertIsNone(row.last_duration_seconds)
        self.assertIsNone(row.last_reason_code)
        self.assertEqual(row.consecutive_failures, 0)
        self.assertTrue(row.target_exists)


class LiveRepository(unittest.TestCase):
    """The seven declarations as they stand, read through the same path as the page."""

    #: Pinned so these two cases read the committed declarations and never the wall
    #: clock or whatever .local/schedules/ happens to hold on the machine running them.
    NOW = datetime(2026, 8, 27, 4, 0, tzinfo=timezone.utc)

    def test_every_declared_target_exists(self) -> None:
        digest = report.assemble(ROOT, self.NOW, utc_offset=timedelta(0))
        self.assertGreater(digest.counts["declared"], 0)
        missing = [row.name for row in digest.rows if not row.target_exists]
        self.assertEqual(missing, [], "a declaration points at a file that is not there")

    def test_the_node_reading_is_one_the_table_declares(self) -> None:
        digest = report.assemble(ROOT, self.NOW, utc_offset=timedelta(0))
        self.assertIn(digest.reading, TABLE["readings"]["order"])
        for row in digest.rows:
            self.assertIn(row.reading, TABLE["readings"]["order"])


class PageAndCheck(unittest.TestCase):
    """The rendered page, and the two jobs `health-check` does over it."""

    NOW = datetime(2026, 8, 27, 4, 0, tzinfo=timezone.utc)

    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        schedules = self.root / ".claude" / "schedules"
        schedules.mkdir(parents=True)
        shutil.copy(ROOT / ".claude" / "schedules" / "schedule.schema.json", schedules)
        (self.root / ".claude" / "workflows").mkdir()
        self.target = self.root / ".claude" / "workflows" / "sov-qa.js"
        self.target.write_text("// stub\n", encoding="utf-8")
        self.path = schedules / "nightly-qa.json"
        self.write_declaration()
        self.page = self.root / "docs" / "automation.html"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write_declaration(self, **overrides) -> None:
        raw = {
            "name": "nightly-qa", "enabled": False,
            "target": {"kind": "workflow", "name": "sov-qa"},
            "cron": "0 2 * * *", "mode": "observe", "effect_class": "RESOURCE_CONSUMPTION",
            "preconditions": {"clean_tree": False},
            "limits": {"max_budget_usd": 5, "timeout_seconds": 600},
        }
        raw.update(overrides)
        self.path.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")

    def args(self, **overrides) -> object:
        values = {"root": self.root, "page_path": self.page, "now": self.NOW}
        values.update(overrides)
        return surface.namespace(**values)

    def render(self, **overrides) -> int:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            return surface.command_render(self.args(**overrides))

    def check(self, **overrides) -> tuple[int, str]:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = surface.command_check(self.args(**overrides))
        return code, buffer.getvalue()

    def record_run(self, outcome: str = "ATTEMPTED") -> None:
        """Put one completed run in the ledger, the way the runner would."""
        moment = self.NOW.replace(hour=2)
        ledger.append(self.root, "nightly-qa", "qa-1", ledger.envelope(
            event_id="e:a", operation_id="op", phase="ATTEMPTED", actor_id="a",
            actor_kind="SYSTEM", reason="due", occurred_at=ledger.timestamp(moment),
            inputs=[], outputs=[], effect_class="RECORD_LOCAL", outcome="ATTEMPTED"))
        ledger.append(self.root, "nightly-qa", "qa-1", ledger.envelope(
            event_id="e:r", operation_id="op", phase="REPORTED", actor_id="m",
            actor_kind="MODEL", reason="executor exit code 0; a report is not an observation",
            occurred_at=ledger.timestamp(moment.replace(minute=5)), inputs=[],
            outputs=[{"address": "reports/2026-08-27-nightly-qa.md", "digest": "sha256:0"}],
            effect_class="RECORD_LOCAL", outcome=outcome))

    def test_two_renders_of_an_unchanged_tree_are_identical_bytes(self) -> None:
        first = page.render(report.assemble(self.root, self.NOW))
        second = page.render(report.assemble(self.root, self.NOW))
        self.assertEqual(first, second)

    def test_a_freshly_rendered_page_passes_both_halves(self) -> None:
        self.render()
        code, out = self.check()
        self.assertEqual(code, 0, out)
        self.assertIn("both halves", out)

    def test_a_changed_declaration_makes_the_page_stale(self) -> None:
        self.render()
        self.write_declaration(cron="0 3 * * *")
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("is stale", out)

    def test_a_ledger_appearing_after_the_render_leaves_history_unchecked(self) -> None:
        """The defeating case for a naive byte comparison.

        The ledger is gitignored machine-local state. A run here would make the
        committed page fail in CI, where the ledger does not exist, so the check has
        to grade the half it can and say plainly that it did not grade the other.
        """
        self.render()
        self.record_run()
        code, out = self.check()
        self.assertEqual(code, 0, out)
        self.assertIn("UNCHECKED", out)
        self.assertIn("declared half matches", out)

    def test_a_declaration_change_fails_even_when_history_is_unchecked(self) -> None:
        """The split must not become a way to hide a declaration change behind a run."""
        self.render()
        self.record_run()
        self.write_declaration(cron="0 3 * * *")
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("stale in its declared half", out)

    def test_a_reading_that_moves_without_the_records_moving_fails(self) -> None:
        """OVERDUE becomes true by time passing and by nothing changing on disk."""
        self.record_run()
        self.write_declaration(enabled=True)
        self.render()
        code, out = self.check(now=self.NOW.replace(day=30))
        self.assertEqual(code, 1)
        self.assertIn("no longer support", out)
        self.assertIn("nightly-qa", out)

    def test_an_unhealthy_reading_refuses_once_the_page_is_current(self) -> None:
        """The alert leg the request admits: an unhealthy automation fails the build."""
        self.target.unlink()
        self.render()
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("TARGET_MISSING", out)
        self.assertIn("UNHEALTHY", out)

    def test_one_refused_declaration_does_not_hide_the_others(self) -> None:
        """load_all raises on the first bad file and shows nothing. This must not."""
        (self.path.parent / "broken.json").write_text('{"name": "broken"}\n', encoding="utf-8")
        digest = report.assemble(self.root, self.NOW)
        self.assertEqual([row.name for row in digest.rows], ["broken", "nightly-qa"])
        self.assertEqual(digest.rows[0].reading, "UNHEALTHY")
        self.assertEqual(digest.rows[1].reading, "UNOBSERVED")
        self.assertEqual({f.rule for _, f in digest.findings}, {"TARGET_MISSING"})

    def test_a_declaration_that_is_not_json_at_all_still_produces_a_row(self) -> None:
        (self.path.parent / "garbage.json").write_text("not json\n", encoding="utf-8")
        digest = report.assemble(self.root, self.NOW)
        row = next(row for row in digest.rows if row.name == "garbage")
        self.assertIsNotNone(row.defect)
        self.assertEqual(row.reading, "UNHEALTHY")

    def test_the_missing_page_is_named_rather_than_crashed_on(self) -> None:
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("has not been rendered", out)

    def test_the_elided_page_drops_the_history_block_and_the_provenance(self) -> None:
        self.render()
        text = self.page.read_text(encoding="utf-8")
        elided = page.outside_history(text)
        self.assertIn(page.HISTORY_ELIDED, elided)
        self.assertIn(page.PROVENANCE_ELIDED, elided)
        self.assertNotIn(page.HISTORY_OPEN, elided)
        self.assertNotIn(page.PROVENANCE_PREFIX, elided)
        self.assertIn("What is declared", elided)


class DisabledSchedulesAndTheNodeReading(unittest.TestCase):
    """Two things the per-schedule corpus cannot state, both load-bearing."""

    def facts(self, enabled: bool) -> health.Facts:
        return health.Facts(
            name="code-review", enabled=enabled, target_exists=True,
            cron_expression="0 */2 * * *", timeout_seconds=2700,
            now=ledger.parse_timestamp("2026-08-27T04:30:00Z"),
            runs=tuple(history.from_records([
                {"run_id": "r1", "attempted_at": "2026-08-27T02:00:00Z",
                 "attempt_outcome": "ATTEMPTED", "reported_at": "2026-08-27T02:20:00Z",
                 "report_outcome": "FAILED"},
                {"run_id": "r2", "attempted_at": "2026-08-27T04:00:00Z",
                 "attempt_outcome": "ATTEMPTED", "reported_at": "2026-08-27T04:20:00Z",
                 "report_outcome": "FAILED"},
            ])))

    def test_applies_to_disabled_is_what_decides_and_not_the_derivation(self) -> None:
        """Flipping the field in the table must change what fires.

        The derivations no longer carry their own enabled test, so this is what proves
        the field is load-bearing rather than decorative prose beside the rule.
        """
        table = json.loads(json.dumps(TABLE))
        self.assertFalse(table["rules"]["CONSECUTIVE_FAILURES"]["applies_to_disabled"])
        fired = {f.rule for f in health.judge(self.facts(False), table).findings}
        self.assertNotIn("CONSECUTIVE_FAILURES", fired)
        table["rules"]["CONSECUTIVE_FAILURES"]["applies_to_disabled"] = True
        fired = {f.rule for f in health.judge(self.facts(False), table).findings}
        self.assertIn("CONSECUTIVE_FAILURES", fired)

    def test_the_node_reading_is_the_worst_of_its_schedules(self) -> None:
        """The one line at the top of the page, and nothing else exercised it."""
        self.assertEqual(health.worst(["HEALTHY", "UNHEALTHY", "UNOBSERVED"], TABLE),
                         "UNHEALTHY")
        self.assertEqual(health.worst(["HEALTHY", "DEGRADED"], TABLE), "DEGRADED")
        self.assertEqual(health.worst(["HEALTHY", "UNOBSERVED"], TABLE), "UNOBSERVED")
        self.assertEqual(health.worst(["HEALTHY", "HEALTHY"], TABLE), "HEALTHY")

    def test_a_mixed_tree_reports_the_worst_reading_and_keeps_every_row(self) -> None:
        with TemporaryDirectory() as name:
            root = Path(name)
            schedules = root / ".claude" / "schedules"
            schedules.mkdir(parents=True)
            shutil.copy(ROOT / ".claude" / "schedules" / "schedule.schema.json", schedules)
            (root / ".claude" / "workflows").mkdir()
            (root / ".claude" / "workflows" / "sov-qa.js").write_text("//\n", encoding="utf-8")
            for schedule_name, target in (("nightly-qa", "sov-qa"), ("ghost", "sov-ghost")):
                (schedules / f"{schedule_name}.json").write_text(json.dumps({
                    "name": schedule_name, "enabled": False,
                    "target": {"kind": "workflow", "name": target},
                    "cron": "0 2 * * *", "mode": "observe",
                    "effect_class": "RESOURCE_CONSUMPTION",
                    "preconditions": {"clean_tree": False},
                    "limits": {"max_budget_usd": 5, "timeout_seconds": 600},
                }, indent=2) + "\n", encoding="utf-8")
            digest = report.assemble(root, ledger.parse_timestamp("2026-08-27T04:00:00Z"),
                                     utc_offset=timedelta(0))
        self.assertEqual([row.reading for row in digest.rows], ["UNHEALTHY", "UNOBSERVED"])
        self.assertEqual(digest.reading, "UNHEALTHY")
        self.assertEqual(digest.counts["refusing"], 1)


if __name__ == "__main__":
    unittest.main()
