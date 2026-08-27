"""Cases for deterministic session launch.

Nothing here starts `claude`. A launcher whose product is an interactive
process can only be proven by reading the launch it builds before it runs, so
every case reads the spec, the generated script, or a recorder standing in for
the terminal.

Each precondition has a positive form and the form proving its refusal. The
refusals are the point: a lane that starts on the wrong branch, under a name
that collides, or with no orders, is worse than one that never started, because
it looks like it is working.
"""

from __future__ import annotations

from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sovhypervisor import launch as launchmod  # noqa: E402
from sovhypervisor import plan as planmod  # noqa: E402

TREE = "C:/trees/fleet-alpha"
SHA = "31e1b91aa0b1c2d3e4f5061728394a5b6c7d8e9f"


def lane(**overrides: object) -> dict[str, object]:
    """A ready write lane, before whatever this case changes about it."""
    base = {
        "name": "fleet-alpha", "worktree": TREE,
        "expected_ref": "feat/sov-control-mesh", "mode": "write",
        "model": "", "agent": "", "orders_file": "", "orders": "Do the thing.",
        "remote_control": True,
    }
    base.update(overrides)
    return base


def watching(**overrides: object):
    """An observer answering for one worktree and refusing every other path."""
    seen = {"is_worktree": True, "branch": "feat/sov-control-mesh", "sha": SHA}
    seen.update(overrides)
    return lambda path: dict(seen) if path == TREE else {"is_worktree": False}


def grade(subject: dict[str, object], observe=None,
          live: dict | None = None) -> dict:
    """Grade one lane in isolation."""
    return planmod.check(subject, observe or watching(), live or {}, set())


class LanePreconditions(unittest.TestCase):
    """A lane is graded against the machine before a process exists."""

    def test_a_matching_lane_is_ready(self) -> None:
        self.assertEqual(grade(lane())["verdict"], planmod.READY)

    def test_a_missing_worktree_refuses(self) -> None:
        verdict = grade(lane(worktree="C:/trees/nope"))
        self.assertEqual(verdict["refusal"], planmod.WORKTREE_MISSING)

    def test_the_wrong_branch_refuses(self) -> None:
        """ALPHA must not quietly begin on main."""
        verdict = grade(lane(), observe=watching(branch="main"))
        self.assertEqual(verdict["refusal"], planmod.REF_MISMATCH)
        self.assertIn("main", verdict["because"])

    def test_a_commit_prefix_is_a_legal_ref(self) -> None:
        subject = lane(expected_ref=SHA[:7], mode="read-only")
        verdict = grade(subject, observe=watching(branch="", sha=SHA))
        self.assertEqual(verdict["verdict"], planmod.READY)

    def test_a_short_prefix_is_not_a_ref(self) -> None:
        verdict = grade(lane(expected_ref=SHA[:4]), observe=watching(branch=""))
        self.assertEqual(verdict["refusal"], planmod.REF_MISMATCH)

    def test_a_read_only_lane_on_a_branch_refuses(self) -> None:
        """A witness sitting on a writable branch can land what it reviewed."""
        verdict = grade(lane(mode="read-only"))
        self.assertEqual(verdict["refusal"], planmod.READ_ONLY_LANE_ON_BRANCH)

    def test_a_lane_with_no_orders_refuses(self) -> None:
        verdict = grade(lane(orders=""))
        self.assertEqual(verdict["refusal"], planmod.ORDERS_MISSING)

    def test_a_name_already_live_refuses(self) -> None:
        live = {"fleet-alpha": {"live": True, "pid": 4321, "tree": TREE}}
        self.assertEqual(grade(lane(), live=live)["refusal"], planmod.LANE_OCCUPIED)

    def test_a_dead_holder_does_not_block_the_name(self) -> None:
        live = {"fleet-alpha": {"live": False, "pid": 4321, "tree": TREE}}
        self.assertEqual(grade(lane(), live=live)["verdict"], planmod.READY)

    def test_a_bad_name_refuses(self) -> None:
        self.assertEqual(grade(lane(name="Fleet Alpha"))["refusal"],
                         planmod.LANE_NAME_INVALID)

    def test_a_name_declared_twice_refuses(self) -> None:
        seen: set[str] = set()
        observe = watching()
        first = planmod.check(lane(), observe, {}, seen)
        second = planmod.check(lane(), observe, {}, seen)
        self.assertEqual(first["verdict"], planmod.READY)
        self.assertEqual(second["refusal"], planmod.LANE_DUPLICATED)


class TerminalRefusal(unittest.TestCase):
    """`TERMINAL_MISSING` was declared and never raised.

    With no terminal on PATH the launcher reached `Popen` and let
    `FileNotFoundError` escape, from inside the per-lane loop. Earlier ready
    lanes in the same batch had already started, so the operator got a
    traceback and no record of what was now running. A declared refusal is
    raised, and this one is raised before any lane starts.
    """

    def test_a_present_terminal_is_available(self) -> None:
        """The positive control, against a terminal the running platform actually has.

        This named `powershell`, which is on PATH on the host this launcher targets
        and not on ubuntu-latest, so the case that proves the check can say yes
        failed on every Linux runner. A test whose answer depends on which machine
        ran it is not a control. `sh` stands in on POSIX; the assertion is
        unchanged - a real executable resolves.
        """
        present = "powershell" if os.name == "nt" else "sh"
        self.assertTrue(launchmod.terminal_available(present))

    def test_no_terminal_declared_is_not_a_missing_terminal(self) -> None:
        """A lane launched without a terminal opens its own console; that is legal."""
        self.assertTrue(launchmod.terminal_available(None))
        self.assertTrue(launchmod.terminal_available(""))

    def test_an_absent_terminal_is_unavailable(self) -> None:
        self.assertFalse(launchmod.terminal_available("no-such-terminal-binary.exe"))

    def test_start_raises_the_declared_refusal_not_a_bare_oserror(self) -> None:
        spec = launchmod.spec(lane(), claude="claude")
        with tempfile.TemporaryDirectory() as raw:
            script = launchmod.write_script(spec, Path(raw))
            with self.assertRaises(launchmod.TerminalMissing) as caught:
                launchmod.start(spec, script, terminal="no-such-terminal-binary.exe")
        self.assertEqual(caught.exception.refusal, launchmod.TERMINAL_MISSING)

    def test_the_refusal_names_the_terminal_it_could_not_find(self) -> None:
        error = launchmod.TerminalMissing("wt.exe")
        self.assertEqual(error.terminal, "wt.exe")
        self.assertIn("wt.exe", str(error))


class RefusalShape(unittest.TestCase):
    """Every verdict answers the same keys, refusal and `READY` alike.

    `--partial` renders ready and refused lanes in one pass, reading one key off
    each. A refusal that omitted `lane` crashed that render with `KeyError`, so
    the operator lost every refusal reason at exactly the moment the refusals
    were the output. The shape is the contract, not the rendering.
    """

    def test_a_ready_verdict_names_its_lane(self) -> None:
        verdict = grade(lane())
        self.assertEqual(verdict["verdict"], planmod.READY)
        self.assertEqual(verdict["lane"], "fleet-alpha")

    def test_every_refusal_names_its_lane(self) -> None:
        refusals = {
            planmod.LANE_NAME_INVALID: grade(lane(name="Fleet Alpha")),
            planmod.WORKTREE_MISSING: grade(lane(worktree="C:/trees/absent")),
            planmod.REF_MISMATCH: grade(lane(expected_ref="")),
            planmod.READ_ONLY_LANE_ON_BRANCH: grade(lane(mode="read-only")),
            planmod.ORDERS_MISSING: grade(lane(orders="")),
            planmod.LANE_OCCUPIED: grade(
                lane(), live={"fleet-alpha": {"live": True, "pid": 1, "tree": TREE}}),
        }
        for expected, verdict in refusals.items():
            with self.subTest(refusal=expected):
                self.assertEqual(verdict["refusal"], expected)
                self.assertIn("lane", verdict, f"{expected} dropped its lane name")
                self.assertTrue(verdict["lane"], f"{expected} named an empty lane")

    def test_a_duplicate_refusal_names_its_lane(self) -> None:
        seen: set[str] = set()
        observe = watching()
        planmod.check(lane(), observe, {}, seen)
        second = planmod.check(lane(), observe, {}, seen)
        self.assertEqual(second["refusal"], planmod.LANE_DUPLICATED)
        self.assertEqual(second["lane"], "fleet-alpha")

    def test_a_mixed_batch_renders_without_reaching_for_a_missing_key(self) -> None:
        """The exact render `--partial` performs, over one ready and one refused lane."""
        verdicts = [grade(lane()), grade(lane(name="second-lane", orders=""))]
        rendered = [f"{v['lane']:<14} {v['verdict']}" for v in verdicts]
        self.assertIn("fleet-alpha", rendered[0])
        self.assertIn("second-lane", rendered[1])
        self.assertIn(planmod.ORDERS_MISSING, rendered[1])


class PlanDocument(unittest.TestCase):
    """A plan is read strictly or refused by name."""

    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp.cleanup)
        self.dir = Path(self._temp.name)

    def _write(self, body: str) -> Path:
        path = self.dir / "plan.json"
        path.write_text(body, encoding="utf-8")
        return path

    def test_a_plan_round_trips(self) -> None:
        path = self._write(json.dumps(
            {"campaign": "c", "sessions": [{"name": "a", "worktree": TREE}]}))
        self.assertEqual(planmod.lanes(planmod.load(path))[0]["name"], "a")

    def test_an_absent_plan_refuses(self) -> None:
        with self.assertRaises(planmod.PlanError) as caught:
            planmod.load(self.dir / "absent.json")
        self.assertEqual(caught.exception.refusal, planmod.PLAN_UNREADABLE)

    def test_a_plan_with_no_sessions_refuses(self) -> None:
        with self.assertRaises(planmod.PlanError) as caught:
            planmod.load(self._write(json.dumps({"campaign": "c", "sessions": []})))
        self.assertEqual(caught.exception.refusal, planmod.PLAN_INVALID)

    def test_an_unknown_mode_refuses(self) -> None:
        with self.assertRaises(planmod.PlanError) as caught:
            planmod.lanes({"campaign": "c", "sessions": [
                {"name": "a", "worktree": TREE, "mode": "supervisor"}]})
        self.assertEqual(caught.exception.refusal, planmod.PLAN_INVALID)


class LaunchSpec(unittest.TestCase):
    """What the launcher hands the host, read before anything runs."""

    def test_the_session_carries_one_name(self) -> None:
        """The Claude display name and the registry name are the same string."""
        spec = launchmod.spec(lane())
        self.assertEqual(spec["argv"][spec["argv"].index("--name") + 1], "fleet-alpha")
        self.assertEqual(spec["env"]["SOV_SESSION"], "fleet-alpha")

    def test_remote_control_is_named_and_optional(self) -> None:
        self.assertIn("--remote-control", launchmod.spec(lane())["argv"])
        self.assertNotIn("--remote-control",
                         launchmod.spec(lane(remote_control=False))["argv"])

    def test_persistence_is_forced(self) -> None:
        self.assertEqual(
            launchmod.spec(lane())["env"]["CLAUDE_CODE_FORCE_SESSION_PERSISTENCE"], "1")

    def test_parentage_is_never_erased(self) -> None:
        """Independence is bought with the documented override, not by hiding."""
        parent = {"CLAUDE_CODE_SESSION_ID": "abc", "CLAUDE_CODE_ENTRYPOINT": "cli",
                  "PATH": "/usr/bin"}
        env = launchmod.environment(launchmod.spec(lane()), base=parent)
        self.assertEqual(env["CLAUDE_CODE_SESSION_ID"], "abc")
        self.assertEqual(env["CLAUDE_CODE_ENTRYPOINT"], "cli")
        self.assertEqual(env["SOV_SESSION"], "fleet-alpha")

    def test_inline_orders_are_the_opening_prompt(self) -> None:
        self.assertEqual(launchmod.spec(lane())["argv"][-1], "Do the thing.")

    def test_orders_in_a_file_are_read_not_pasted(self) -> None:
        """A long order overruns a command line; a path never does."""
        spec = launchmod.spec(lane(orders="", orders_file=".local/alpha.md"))
        self.assertIn(".local/alpha.md", spec["argv"][-1])
        self.assertNotIn("--", spec["argv"][-1])

    def test_a_read_only_lane_cannot_edit(self) -> None:
        argv = launchmod.spec(lane(mode="read-only"))["argv"]
        self.assertEqual(argv[argv.index("--permission-mode") + 1], "plan")

    def test_a_write_lane_is_not_pinned_to_plan_mode(self) -> None:
        self.assertNotIn("--permission-mode", launchmod.spec(lane())["argv"])

    def test_the_model_and_agent_travel_when_declared(self) -> None:
        argv = launchmod.spec(lane(model="opus", agent="sov"))["argv"]
        self.assertEqual(argv[argv.index("--model") + 1], "opus")
        self.assertEqual(argv[argv.index("--agent") + 1], "sov")

    def test_the_working_directory_is_the_declared_worktree(self) -> None:
        self.assertEqual(launchmod.spec(lane())["cwd"], TREE)


class GeneratedScript(unittest.TestCase):
    """The PowerShell a lane's terminal runs."""

    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp.cleanup)

    def test_the_script_sets_the_environment_and_the_directory(self) -> None:
        text = launchmod.script_text(launchmod.spec(lane()))
        self.assertIn("$env:SOV_SESSION = 'fleet-alpha'", text)
        self.assertIn("$env:CLAUDE_CODE_FORCE_SESSION_PERSISTENCE = '1'", text)
        self.assertIn("Set-Location -LiteralPath 'C:/trees/fleet-alpha'", text)

    def test_a_quote_in_the_orders_cannot_break_out(self) -> None:
        text = launchmod.script_text(launchmod.spec(lane(orders="it's fine")))
        self.assertIn("'it''s fine'", text)

    def test_the_script_lands_where_a_human_can_read_it(self) -> None:
        into = Path(self._temp.name) / "hypervisor"
        path = launchmod.write_script(launchmod.spec(lane()), into)
        self.assertEqual(path.name, "fleet-alpha.ps1")
        self.assertIn("--remote-control", path.read_text(encoding="utf-8"))

    def test_the_terminal_opens_the_lane_in_its_own_directory(self) -> None:
        argv = launchmod.terminal_argv(launchmod.spec(lane()),
                                       Path("C:/x/fleet-alpha.ps1"))
        self.assertEqual(argv[argv.index("-d") + 1], TREE)
        self.assertEqual(argv[argv.index("--title") + 1], "fleet-alpha")

    def test_without_a_terminal_the_shell_runs_the_script_directly(self) -> None:
        argv = launchmod.terminal_argv(launchmod.spec(lane()),
                                       Path("C:/x/a.ps1"), terminal=None)
        self.assertEqual(argv[0], "powershell")
        self.assertNotIn("new-tab", argv)


class RealChildProcess(unittest.TestCase):
    """A recorder stands in for the terminal; `claude` is never reached."""

    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp.cleanup)
        self.dir = Path(self._temp.name)
        self.record = self.dir / "seen.json"
        self.recorder = self.dir / "recorder.py"
        self.recorder.write_text(
            "import json, os, sys\n"
            "json.dump({'argv': sys.argv[1:], 'cwd': os.getcwd(),\n"
            "           'env': dict(os.environ)},\n"
            "          open(sys.argv[1], 'w'))\n",
            encoding="utf-8")

    def test_the_lane_environment_reaches_a_real_child(self) -> None:
        spec = launchmod.spec(lane())
        env = launchmod.environment(spec, base=dict(
            os.environ, CLAUDE_CODE_SESSION_ID="parent-abc"))
        subprocess.run([sys.executable, str(self.recorder), str(self.record)],
                       cwd=str(self.dir), env=env, check=True, capture_output=True)
        seen = json.loads(self.record.read_text(encoding="utf-8"))["env"]
        self.assertEqual(seen["SOV_SESSION"], "fleet-alpha")
        self.assertEqual(seen["CLAUDE_CODE_FORCE_SESSION_PERSISTENCE"], "1")
        self.assertEqual(seen["CLAUDE_CODE_SESSION_ID"], "parent-abc")


class Registration(unittest.TestCase):
    """A launched process is not a lane until the registry says so."""

    def _wait(self, reads: list[dict], **kwargs) -> dict:
        ticks = iter(range(0, 10_000, 10))
        return launchmod.await_registration(
            "fleet-alpha", TREE, lambda: reads.pop(0) if reads else {},
            clock=lambda: float(next(ticks)), sleep=lambda _: None, **kwargs)

    def test_a_registered_lane_reads_ready(self) -> None:
        verdict = self._wait([{}, {"fleet-alpha": {
            "live": True, "pid": 99, "tree": TREE, "branch": "feat/x"}}])
        self.assertEqual(verdict["verdict"], launchmod.READY)
        self.assertEqual(verdict["pid"], 99)

    def test_a_session_that_never_registers_fails_visibly(self) -> None:
        """Not `launched`. The window may be open and the session unstarted."""
        verdict = self._wait([], timeout=30.0)
        self.assertEqual(verdict["refusal"], launchmod.REGISTRATION_TIMEOUT)

    def test_a_lane_that_registered_in_the_wrong_tree_is_not_ready(self) -> None:
        verdict = self._wait([{"fleet-alpha": {
            "live": True, "pid": 99, "tree": "C:/trees/somewhere-else"}}])
        self.assertEqual(verdict["refusal"], launchmod.REGISTERED_ELSEWHERE)


if __name__ == "__main__":
    unittest.main()
