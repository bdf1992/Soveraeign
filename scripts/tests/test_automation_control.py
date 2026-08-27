"""Drive the automation-control corpus, and the couplings a fixture cannot state.

`conformance/fixtures/automation-control/cases.json` holds one case per refusal and a
quiet case for each. This module executes that corpus against the real operation and
adds what a corpus cannot reach: that both bindings land on the same function, that the
console refuses a non-loopback bind and a wrong token, that the declaration diff is one
line, and that a switch is countered rather than erased.

A passing run establishes `BUILT`. It witnesses nothing.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import shutil
import sys
import threading
import unittest
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovschedule import console, control, page, report, changelog  # noqa: E402

CORPUS = json.loads(
    (ROOT / "conformance" / "fixtures" / "automation-control" / "cases.json")
    .read_bytes().decode("utf-8"))
TABLE = json.loads(
    (ROOT / "contracts" / "automation-control.json").read_bytes().decode("utf-8"))

NOW = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)


class Tree(unittest.TestCase):
    """A repository with one schedule in it, built per test and thrown away."""

    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.schedules = self.root / ".claude" / "schedules"
        self.schedules.mkdir(parents=True)
        shutil.copy(ROOT / ".claude" / "schedules" / "schedule.schema.json", self.schedules)
        (self.root / ".claude" / "workflows").mkdir()
        (self.root / "contracts").mkdir()
        shutil.copy(ROOT / "contracts" / "automation-health.json", self.root / "contracts")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def declare(self, name: str = "nightly-qa", *, enabled: bool = False,
                target_exists: bool = True, valid: bool = True) -> Path:
        path = self.schedules / f"{name}.json"
        if not valid:
            path.write_text('{"name": "' + name + '", "enabled": false}\n', encoding="utf-8")
            return path
        if target_exists:
            (self.root / ".claude" / "workflows" / "sov-qa.js").write_text(
                "// stub\n", encoding="utf-8")
        path.write_text(json.dumps({
            "name": name, "description": "a schedule", "enabled": enabled,
            "target": {"kind": "workflow", "name": "sov-qa",
                       "args": {"focus": "kept inline on purpose"}},
            "cron": "0 2 * * *", "mode": "observe", "effect_class": "RESOURCE_CONSUMPTION",
            "preconditions": {"clean_tree": False},
            "limits": {"max_budget_usd": 5, "timeout_seconds": 600},
        }, indent=2) + "\n", encoding="utf-8")
        return path

    def actor(self, kind: str) -> control.Actor:
        return (control.owner(control.BINDING_COMMAND) if kind == "owner"
                else control.model("urn:soveraeign:actor:test-model"))

    def enabled_of(self, name: str = "nightly-qa") -> bool:
        return json.loads((self.schedules / f"{name}.json").read_text(encoding="utf-8"))["enabled"]


class DeclaredCorpus(Tree):
    """Every case in the fixture file, run against the real operation."""

    def test_every_case_decides_what_it_declares(self) -> None:
        for case in CORPUS["cases"]:
            with self.subTest(case=case["case_id"]):
                # A fresh tree per case, balanced so the outer fixture is not orphaned.
                self.tearDown()
                self.setUp()
                declared = case["schedule"]
                self.declare(declared["name"], enabled=declared["enabled"],
                             target_exists=declared["target_exists"],
                             valid=declared["valid"])
                request = case["request"]
                outcome = control.set_switch(
                    self.root, request["name"], request["direction"],
                    self.actor(request["actor"]), request["reason"], now=NOW)
                self.assertEqual(outcome.outcome, case["expect_outcome"])
                self.assertEqual(outcome.refusal_code, case["expect_refusal"])
                if declared["valid"]:
                    self.assertEqual(self.enabled_of(declared["name"]),
                                     case["expect_enabled_after"])
                self.assertEqual(len(changelog.read(self.root)),
                                 case["expect_log_lines"])

    def test_every_declared_refusal_is_assigned_a_layer(self) -> None:
        """No refusal may sit outside the partition, because that is where a skip hides.

        Every layer, read out of the table rather than named here. An earlier version
        listed the two layers that existed and a third arrived with the proposal
        operation - the test then passed over two refusals it was written to catch.
        """
        layered = {code for key, codes in TABLE["refusal_layer"].items()
                   if key != "note" for code in codes}
        self.assertEqual(layered, set(TABLE["refusals"]))

    def test_every_operation_refusal_has_a_corpus_case(self) -> None:
        """A refusal nothing exercises is prose, not a refusal.

        Both corpora, because the operations split across two files: the switch cases
        here and the authoring cases beside them. Checking one would let a refusal
        declared for either operation sit uncovered as long as the other corpus grew.
        """
        reached = {case["expect_refusal"]
                   for case in CORPUS["cases"] + CORPUS["authoring_cases"]} - {None}
        missing = [code for code in TABLE["refusal_layer"]["operation"]
                   if code not in reached]
        self.assertEqual(missing, [], f"operation refusals with no case: {missing}")

    def test_every_transport_refusal_is_asserted_somewhere_in_this_module(self) -> None:
        """A socket refusal cannot come from a fixture, so a named test stands for it.

        Each transport test asserts the declared code out of the refusal it triggers, so
        the code appears in this file because something checks it. Deleting that test
        fails here rather than quietly leaving the refusal undefended. The scan is only
        as good as what it scans for: matching an exception class name would have passed
        while no test looked at the code at all.
        """
        source = Path(__file__).read_text(encoding="utf-8")
        missing = [code for code in TABLE["refusal_layer"]["transport"]
                   if code not in source]
        self.assertEqual(missing, [], f"transport refusals no test asserts: {missing}")

    def test_every_refusal_has_a_case_that_does_not_fire_it(self) -> None:
        """One case that fires proves nothing about what a check lets past."""
        for code in {c["expect_refusal"] for c in CORPUS["cases"]} - {None}:
            quiet = [c["case_id"] for c in CORPUS["cases"] if c["expect_refusal"] != code]
            with self.subTest(code=code):
                self.assertTrue(quiet)


class TheAuthoritySplit(Tree):
    """The part that must not regress: who can arm, and who can only ask."""

    def test_a_model_cannot_arm_through_any_binding(self) -> None:
        """Hiding the button is not an authority check; this is the check.

        Both bindings name their actor and call one function. A model reaching the
        console binding directly - which anything importing this module can do - gets
        the same recorded proposal as one reaching the command line.
        """
        for binding in (control.BINDING_COMMAND, control.BINDING_CONSOLE):
            with self.subTest(binding=binding):
                self.declare(enabled=False)
                actor = control.model("urn:soveraeign:actor:test-model", binding)
                outcome = control.set_switch(self.root, "nightly-qa", "ENABLE", actor,
                                             "let me in", now=NOW)
                self.assertEqual(outcome.outcome, changelog.PROPOSED)
                self.assertEqual(outcome.refusal_code, "GRANT_NOT_HELD")
                self.assertFalse(self.enabled_of())

    def test_the_grant_table_is_what_decides_and_not_the_derivation(self) -> None:
        """Flip which direction needs the seat, and the outcome must flip with it."""
        self.declare(enabled=True)
        actor = control.model("urn:soveraeign:actor:test-model")
        original = dict(control.GRANT_FOR)
        try:
            control.GRANT_FOR[changelog.DISABLE] = "seat:root"
            outcome = control.set_switch(self.root, "nightly-qa", "DISABLE", actor,
                                         "stop it", now=NOW)
            self.assertEqual(outcome.outcome, changelog.PROPOSED)
        finally:
            control.GRANT_FOR.clear()
            control.GRANT_FOR.update(original)

    def test_the_contract_and_the_code_agree_on_which_direction_needs_a_seat(self) -> None:
        declared = TABLE["authority"]["grants"]
        self.assertEqual(control.GRANT_FOR[changelog.ENABLE], declared["ENABLE"]["held_by"])
        self.assertEqual(control.GRANT_FOR[changelog.DISABLE], "")
        self.assertEqual(declared["ENABLE"]["reason"], "RESOURCE_COMMITMENT")


class TheRecord(Tree):
    """What the switch log has to be able to answer afterwards."""

    def test_the_declaration_diff_is_one_line(self) -> None:
        """A reserialise would bury the changed field in a reformat nobody reviews."""
        path = self.declare(enabled=False)
        before = path.read_text(encoding="utf-8").splitlines()
        control.set_switch(self.root, "nightly-qa", "ENABLE", self.actor("owner"),
                           "arming it", now=NOW)
        after = path.read_text(encoding="utf-8").splitlines()
        changed = [(a, b) for a, b in zip(before, after) if a != b]
        self.assertEqual(len(before), len(after))
        self.assertEqual(len(changed), 1)
        self.assertIn("enabled", changed[0][0])
        self.assertIn('"focus": "kept inline on purpose"', "\n".join(after))

    def test_a_switch_is_countered_and_never_erased(self) -> None:
        """Retraction adds a record. The arming stays visible after it is undone."""
        self.declare(enabled=False)
        control.set_switch(self.root, "nightly-qa", "ENABLE", self.actor("owner"),
                           "armed for the overnight run", now=NOW)
        control.set_switch(self.root, "nightly-qa", "DISABLE", self.actor("model"),
                           "it failed twice, stopping it", now=NOW)
        entries = changelog.read(self.root)
        self.assertEqual([e.direction for e in entries], ["ENABLE", "DISABLE"])
        self.assertEqual([e.outcome for e in entries], ["EFFECTED", "EFFECTED"])
        self.assertEqual(entries[0].reason, "armed for the overnight run")
        self.assertFalse(self.enabled_of())

    def test_a_refused_attempt_is_recorded_too(self) -> None:
        """A log of only what succeeded cannot answer who tried."""
        self.declare(enabled=False)
        control.set_switch(self.root, "ghost", "ENABLE", self.actor("owner"),
                           "fat-fingered the name", now=NOW)
        entries = changelog.read(self.root)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].outcome, changelog.REFUSED)
        self.assertEqual(entries[0].refusal_code, "UNKNOWN_SCHEDULE")

    def test_the_record_carries_every_field_the_contract_names(self) -> None:
        self.declare(enabled=False)
        outcome = control.set_switch(self.root, "nightly-qa", "ENABLE",
                                     self.actor("owner"), "arming it", now=NOW)
        for field in ("schedule", "direction", "from_enabled", "to_enabled", "actor_id",
                      "actor_kind", "binding", "reason", "occurred_at", "outcome",
                      "before_digest", "after_digest"):
            self.assertIn(field, outcome.entry, field)
        self.assertNotEqual(outcome.entry["before_digest"], outcome.entry["after_digest"])

    def test_a_truncated_log_line_does_not_take_down_the_reader(self) -> None:
        """This log is read by the surface that would tell you the console crashed."""
        self.declare(enabled=False)
        control.set_switch(self.root, "nightly-qa", "DISABLE", self.actor("owner"),
                           "already off, so nothing", now=NOW)
        path = changelog.log_path(self.root)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write('{"schedule": "half-writ')
        self.assertEqual(changelog.read(self.root), [])


class ConsoleTransport(Tree):
    """The refusals that belong to the socket rather than to the operation."""

    def serve(self):
        server, token = console.build_server(self.root)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        return server, token, console.url_for(server, token)

    def post(self, base: str, payload: dict):
        request = urllib.request.Request(
            base + "/switch", data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        return json.loads(urllib.request.urlopen(request).read())

    def test_a_non_loopback_bind_is_refused_rather_than_warned_about(self) -> None:
        for host in ("0.0.0.0", "::", "192.168.1.10"):
            with self.subTest(host=host):
                with self.assertRaises(console.NonLoopbackBind) as caught:
                    console.build_server(self.root, host=host)
                self.assertTrue(str(caught.exception).startswith("NON_LOOPBACK_BIND"))

    def test_the_wrong_token_reaches_neither_the_page_nor_the_operation(self) -> None:
        self.declare(enabled=True)
        server, _, url = self.serve()
        base = url.split("?")[0].rstrip("/")
        try:
            with self.assertRaises(urllib.error.HTTPError) as caught:
                urllib.request.urlopen(base + "/?t=wrong")
            self.assertEqual(caught.exception.code, 403)
            self.assertIn("BAD_TOKEN", caught.exception.read().decode("utf-8"))
            with self.assertRaises(urllib.error.HTTPError) as caught:
                self.post(base, {"token": "wrong", "schedule": "nightly-qa",
                                 "direction": "DISABLE", "reason": "from another page"})
            self.assertEqual(caught.exception.code, 403)
            self.assertIn("BAD_TOKEN", caught.exception.read().decode("utf-8"))
            self.assertTrue(self.enabled_of(), "a wrong token still moved the switch")
        finally:
            server.shutdown()
            server.server_close()

    def test_the_served_page_and_the_command_line_reach_one_operation(self) -> None:
        """Two-binding proof: same cases, same decisions, different actors."""
        self.declare(enabled=False)
        server, token, url = self.serve()
        base = url.split("?")[0].rstrip("/")
        try:
            answer = self.post(base, {"token": token, "schedule": "nightly-qa",
                                      "direction": "ENABLE", "reason": "clicked arm"})
            self.assertEqual(answer["outcome"], changelog.EFFECTED)
            self.assertTrue(self.enabled_of())
            outcome = control.set_switch(self.root, "nightly-qa", "DISABLE",
                                         self.actor("model"), "stopped from the CLI",
                                         now=NOW)
            self.assertEqual(outcome.outcome, changelog.EFFECTED)
            self.assertFalse(self.enabled_of())
            bindings = [entry.binding for entry in changelog.read(self.root)]
            self.assertEqual(bindings, [control.BINDING_CONSOLE, control.BINDING_COMMAND])
        finally:
            server.shutdown()
            server.server_close()

    def test_a_port_that_is_already_listening_is_refused(self) -> None:
        """Found by running it, not by reading it.

        allow_reuse_address defaults to true in the stdlib, and on Windows that flag
        permits binding a port another process is actively listening on - no error, and
        no defined winner for incoming connections. This console did exactly that: it
        bound a port an unrelated application already held, printed a URL, and sent the
        operator to that application. A page of switches pointed at somebody else's
        server is the worst failure this surface has, because it looks like it worked.
        """
        first, _ = console.build_server(self.root)
        port = first.server_address[1]
        try:
            with self.assertRaises(console.PortInUse) as caught:
                console.build_server(self.root, port=port)
            self.assertTrue(str(caught.exception).startswith("PORT_IN_USE"))
        finally:
            first.server_close()

    def test_an_unknown_route_is_a_refusal_not_a_page(self) -> None:
        server, token, url = self.serve()
        base = url.split("?")[0].rstrip("/")
        try:
            for path in ("/admin", "/../etc/passwd", "/switch/extra"):
                with self.subTest(path=path):
                    with self.assertRaises(urllib.error.HTTPError) as caught:
                        urllib.request.urlopen(f"{base}{path}?t={token}")
                    self.assertEqual(caught.exception.code, 404)
        finally:
            server.shutdown()
            server.server_close()


class TwoSurfacesOneRender(Tree):
    """The static page and the served page differ in exactly one declared way."""

    def test_the_static_page_carries_no_button_and_says_where_they_are(self) -> None:
        self.declare(enabled=False)
        digest = report.assemble(self.root, NOW, source=report.WORKTREE)
        static = page.render(digest)
        self.assertNotIn("<button", static)
        self.assertNotIn("<script", static)
        self.assertIn("sov_schedule.py console", static)
        self.assertIn("read-only page", static)

    def test_the_served_page_carries_a_button_for_every_schedule(self) -> None:
        self.declare(enabled=False)
        self.declare("code-review", enabled=True)
        digest = report.assemble(self.root, NOW, source=report.WORKTREE)
        live = page.render(digest, controls="a-token")
        # Counted by element, not by class: edit links and the new-schedule link carry
        # the same class, and a bare class count would pass with the switches removed.
        # Two switch buttons, two edit toggles, two save/cancel pairs, and the new
        # row's own set. Counted by role rather than by class: edit toggles and switch
        # buttons share a class and a bare count would pass with the switches gone.
        self.assertEqual(live.count("data-direction="), 2)
        self.assertEqual(live.count("data-edit="), 3)
        self.assertEqual(live.count('data-edit="__new__"'), 1)
        self.assertEqual(live.count("data-save="), 3)
        self.assertIn('data-direction="ENABLE"', live)
        self.assertIn('data-direction="DISABLE"', live)
        self.assertIn("live console", live)

    def test_a_running_console_does_not_move_the_committed_bytes(self) -> None:
        """The graded page is what render() produces with controls off, always."""
        self.declare(enabled=False)
        digest = report.assemble(self.root, NOW, source=report.WORKTREE)
        first = page.render(digest)
        page.render(digest, controls="a-token")
        self.assertEqual(page.render(digest), first)


if __name__ == "__main__":
    unittest.main()
