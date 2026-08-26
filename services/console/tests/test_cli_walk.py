"""Every console command, driven through the entry point an operator actually has.

The gap this closes is not a missing assertion about behaviour. It is that nothing
called some of these functions the way the CLI calls them. A refactor that moved
`post` into its own module left the import behind in `core.py`; the package still
imported, `python -c "import soveraeign_console_service"` still printed ok, and the
`NameError` waited in the one line that runs when somebody actually posts. The suite
caught it only because other cases happened to post. A function nothing drives
end to end is a function whose first real caller is a user.

So this walks the whole declared surface through `cli.main`, in order, against a
throwaway root: open a channel, open a thread, open sessions, post as a human and as
a model, read the thread back, publish it, list publications, withdraw, archive,
grant, list grants, revoke, discover, resume. Every command in `build_parser` is
driven at least once, and the test that says so fails when a command is added
without one.

`cli.main` rather than a subprocess, and the difference is worth stating: this
crosses the argument parser, the command table, the service and the journal, which
is where a name goes missing. It does not cross the process boundary, so it would
not catch a packaging or `__main__` fault. `test_node_bound_grants.ReproducedThroughTheCLI`
spends real subprocesses on the two chains where that boundary is the point, and
the verification budget pays for those deliberately rather than for all of these.
"""

from __future__ import annotations

from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
import contextlib
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "services" / "console" / "src"))
sys.path.insert(0, str(ROOT / "services" / "record" / "src"))

from soveraeign_console_service import cli  # noqa: E402

NODE = "node:local"
BDO = "Bdo"
SOV = "sov"
MAP = str(ROOT / "contracts" / "fixtures" / "capability-map.reference.json")


class ConsoleCLIWalk(unittest.TestCase):
    """One store, every command, in the order an operator would reach them."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = TemporaryDirectory(ignore_cleanup_errors=True)
        cls.store = Path(cls._tmp.name) / "console"
        cls.reached: set[str] = set()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def run_cli(self, *args: str, expect: int = 0) -> Any:
        """One command through `cli.main`, returning the JSON object it printed."""
        type(self).reached.add(args[0])
        out = StringIO()
        with contextlib.redirect_stdout(out):
            code = cli.main(["--root", str(self.store), "--node", NODE, *args])
        self.assertEqual(code, expect, f"{args[0]}: {out.getvalue()[:400]}")
        return json.loads(out.getvalue())

    def grant(self, operator: str, capability: str, scope: str) -> dict[str, Any]:
        """One grant, always naming its issuer.

        `--granted-by` is required. It defaulted to `Bdo`, and this walk was built on
        that default - which is how a flag that decides whose authority is spent went
        four rounds without a caller ever naming it.
        """
        return self.run_cli("grant", "--operator", operator, "--granted-by", BDO,
                            "--capability", capability, "--scope", scope)

    def test_the_whole_surface_runs_end_to_end(self) -> None:
        """Not a behaviour claim: a claim that every command has a caller at all."""
        # The permits office opens on its first grant, and the root seat buys what the
        # walk is about to spend. Every one of these is a declared capability.
        for capability, scope in (("open:channel", "governance"),
                                  ("open:session", BDO),
                                  ("close:session", BDO),
                                  ("read:session", BDO),
                                  ("read:authority", NODE),
                                  ("read:thread", NODE)):
            self.grant(BDO, capability, scope)
        for capability in ("open:session", "read:session"):
            self.grant(SOV, capability, SOV)

        channel = self.run_cli("open-channel", "--operator", BDO,
                               "--name", "governance", "--domain", "governance")
        self.assertEqual(channel["node_id"], NODE)

        self.grant(BDO, "open:thread", channel["channel_id"])
        thread = self.run_cli("open-thread", "--operator", BDO,
                              "--channel", channel["channel_id"], "--title", "walk")
        thread_id = thread["thread_id"]
        self.assertEqual(thread["node_id"], NODE)

        human = self.run_cli("open-session", "--operator", BDO,
                             "--actor-kind", "HUMAN", "--binding", "cli")
        model = self.run_cli("open-session", "--operator", SOV,
                             "--actor-kind", "MODEL", "--binding", "model-binding")
        self.assertEqual(human["node_id"], NODE)

        for operator, session in ((BDO, human), (SOV, model)):
            self.grant(operator, "post:message", thread_id)
            written = self.run_cli("post", "--operator", operator,
                                   "--session", session["session_id"],
                                   "--thread", thread_id, "--body", f"from {operator}")
            self.assertEqual(written["actor_id"], operator)
            self.assertEqual(written["node_id"], NODE)

        self.grant(BDO, "read:thread", thread_id)
        read = self.run_cli("read-thread", "--operator", BDO, "--thread", thread_id,
                            "--binding", "cli")
        self.assertEqual([post["actor_id"] for post in read["posts"]], [BDO, SOV])
        self.assertFalse(read["authoritative"])

        self.grant(BDO, "publish:thread", thread_id)
        published = self.run_cli("publish-thread", "--operator", BDO, "--thread", thread_id)
        listed = self.run_cli("list-publications", "--operator", BDO)
        self.assertEqual([row["thread_id"] for row in listed["published"]], [thread_id])
        self.run_cli("withdraw-publication", "--operator", BDO,
                     "--publication", published["publication_id"])
        self.assertEqual(self.run_cli("list-publications", "--operator", BDO)["published"], [])

        self.run_cli("close-session", "--operator", BDO, "--session", human["session_id"])
        resumed = self.run_cli("session-context", "--reader", BDO)
        self.assertEqual(resumed["operator_id"], BDO)

        answer = self.run_cli("operations", "--operator", BDO, "--capability-map", MAP)
        self.assertEqual(answer["counts"]["authority"].get("NOT_ENFORCED", 0), 0)

        live = self.run_cli("grants", "--reader", BDO, "--operator", BDO)["live_grants"]
        self.assertTrue(all(record["node_id"] == NODE for record in live))
        posting = next(record["grant_id"] for record in live
                       if record["capability"] == "post:message")
        self.run_cli("revoke", "--grant", posting, "--revoked-by", BDO)

        self.grant(BDO, "archive:thread", channel["channel_id"])
        archived = self.run_cli("archive-thread", "--operator", BDO, "--thread", thread_id)
        self.assertEqual(archived["lifecycle"], "ARCHIVED")

        # The census belongs to the walk rather than to a case of its own: as a
        # separate test it re-ran the whole walk to populate `reached`, which doubled
        # the most expensive module in this suite and asserted nothing extra.
        # A command added to the parser without a caller fails here.
        parser = cli.build_parser()
        declared: set[str] = set()
        for action in parser._subparsers._group_actions:  # noqa: SLF001 - argparse census
            declared.update(action.choices)
        self.assertEqual(declared - self.reached, set())

    def test_the_issuer_flags_cannot_be_left_unnamed(self) -> None:
        """A flag that decides whose authority is spent must be typed, not defaulted.

        `--granted-by` and `--revoked-by` defaulted to `Bdo`. Bootstrap the office as
        Bdo, then omit the flag, and the console issued in the root seat's name at
        exit 0 - `--granted-by Eve` was correctly refused, so the check worked and
        the default walked straight past it. This change is what turned that flag
        from a label into the principal whose grant is checked.
        """
        with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            store = Path(tmp) / "console"
            cases = ((("grant", "--operator", "Mallory", "--capability",
                       "grant:authority", "--scope", NODE), "--granted-by"),
                     (("revoke", "--grant", "grant_0000000000000000"), "--revoked-by"))
            for args, omitted in cases:
                with self.subTest(args[0]):
                    out, err = StringIO(), StringIO()
                    with self.assertRaises(SystemExit) as exited:
                        with contextlib.redirect_stderr(err):
                            with contextlib.redirect_stdout(out):
                                cli.main(["--root", str(store), "--node", NODE, *args])
                    # A usage error, at the code this module reserves for one, and in
                    # JSON: exit 2 is a refusal, and a caller must be able to tell a
                    # refused operation from a command it typed wrongly.
                    self.assertEqual(exited.exception.code, 1)
                    answer = json.loads(out.getvalue())
                    self.assertEqual(answer["outcome"], "USAGE_ERROR")
                    self.assertIn(omitted, answer["message"])
                    self.assertEqual(err.getvalue(), "")

    def test_a_refusal_comes_back_as_json_with_its_reason_code(self) -> None:
        """Exit 2 and a machine-readable reason, not a traceback, at the real boundary."""
        with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            store = Path(tmp) / "console"
            out = StringIO()
            with contextlib.redirect_stdout(out):
                code = cli.main(["--root", str(store), "--node", NODE, "open-channel",
                                 "--operator", "stranger", "--name", "x",
                                 "--domain", "governance"])
            self.assertEqual(code, 2)
            self.assertEqual(json.loads(out.getvalue())["reason_code"], "NO_LIVE_GRANT")

    def test_revoking_a_grant_that_does_not_exist_is_refused(self) -> None:
        """`revoke --grant ""` appended a revocation naming nothing and exited 0.

        Two callers, because the answer depends on what the caller holds and that is
        the point. One holding nothing is told it holds nothing, and learns nothing
        about whether the id names a grant. One holding `revoke:authority` is told the
        grant is not there, which is the `grant_exists` precondition the manifest
        declares.
        """
        with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            store = Path(tmp) / "console"
            out = StringIO()
            with contextlib.redirect_stdout(out):
                code = cli.main(["--root", str(store), "--node", NODE,
                                 "revoke", "--grant", "",
                                 "--revoked-by", BDO])
            self.assertEqual(code, 2)
            self.assertEqual(json.loads(out.getvalue())["reason_code"], "NO_LIVE_GRANT")

            # Opening the office makes Bdo its root, which is the only way to hold
            # `revoke:authority` on a journal that has never carried a grant.
            with contextlib.redirect_stdout(StringIO()):
                cli.main(["--root", str(store), "--node", NODE, "grant",
                          "--operator", "reader", "--capability", "read:thread",
                          "--scope", "t", "--granted-by", BDO])
            out = StringIO()
            with contextlib.redirect_stdout(out):
                code = cli.main(["--root", str(store), "--node", NODE,
                                 "revoke", "--grant", "",
                                 "--revoked-by", BDO])
            self.assertEqual(code, 3)
            self.assertEqual(json.loads(out.getvalue())["reason_code"], "UNKNOWN_RECORD")


if __name__ == "__main__":
    unittest.main()
