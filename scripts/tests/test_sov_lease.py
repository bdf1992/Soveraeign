"""Prove the lease command line accepts both spellings of a principal and records cleanup.

``scripts/tests/test_work_lease.py`` judges lease records against the kernel evaluator.
This module covers the tooling in front of it: the mapping from the registry's
``principal:<id>`` to the contract's URN (``reports/2026-09-05-thin-circuit-1.md``,
fizzle 1), and the ``--cleanup`` obligations a lease now carries for
``conformance/commissioning.py`` Q1.2.

Every command runs against a temporary store; nothing here touches the shared session
directory. A passing run establishes ``BUILT`` for the tooling and witnesses nothing.
"""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock
import io
import json
import os
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_lease  # noqa: E402
from sovlease import commands  # noqa: E402
from sovlease import principals  # noqa: E402
from sovlease import store  # noqa: E402
from sovsession import principals as registry  # noqa: E402

TAKE = ["take", "#1", "--definition", "sov-worker", "--closure", "it lands",
        "--defeat", "it does not land"]
HELPER = ["helper", "lease:1", "part", "--definition", "sov-worker",
          "--closure", "the part lands", "--defeat", "it does not land"]


def _registry(tmp: Path, revoked: tuple[str, ...] = (), **principals_by_kind: str) -> Path:
    """A registry holding one principal per named kind, written where the loader looks."""
    path = tmp / "principals.json"
    path.write_text(json.dumps({
        "registry_schema": "soveraeign-principal-registry/v1",
        "status": "PROPOSED",
        "root_principal": "principal:root",
        "principals": [{"principal_id": f"principal:{name}", "kind": kind,
                        "revoked": {"at": "2026-09-05T00:00:00Z"} if name in revoked else None}
                       for name, kind in principals_by_kind.items()],
    }), encoding="utf-8")
    return path


class MappingTests(unittest.TestCase):
    """One function, both spellings, kind read from the registry and never assumed."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        path = _registry(self.root, revoked=("gone",), worker="MODEL", operator="HUMAN",
                         gone="MODEL")
        patcher = mock.patch.dict(os.environ, {registry.ENV_REGISTRY: str(path)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_registry_spelling_maps_to_the_urn_with_the_registry_kind(self) -> None:
        self.assertEqual("urn:soveraeign:principal:model:worker",
                         principals.instance_principal("principal:worker", self.root))
        self.assertEqual("urn:soveraeign:principal:human:operator",
                         principals.instance_principal("principal:operator", self.root))

    def test_an_unregistered_spelling_is_refused_by_name(self) -> None:
        with self.assertRaises(principals.UnregisteredPrincipal) as caught:
            principals.instance_principal("principal:nobody", self.root)
        self.assertIn(principals.UNREGISTERED_PRINCIPAL, str(caught.exception))
        self.assertIn("principal:nobody", str(caught.exception))

    def test_a_revoked_principal_is_refused_and_the_same_id_unrevoked_maps(self) -> None:
        with self.assertRaises(principals.RevokedPrincipal) as caught:
            principals.instance_principal("principal:gone", self.root)
        self.assertIn(principals.REVOKED_PRINCIPAL, str(caught.exception))
        path = _registry(self.root, gone="MODEL")
        with mock.patch.dict(os.environ, {registry.ENV_REGISTRY: str(path)}):
            self.assertEqual("urn:soveraeign:principal:model:gone",
                             principals.instance_principal("principal:gone", self.root))

    def test_a_urn_passes_through_unchanged(self) -> None:
        urn = "urn:soveraeign:principal:instance:session-000000"
        self.assertEqual(urn, principals.instance_principal(urn, self.root))

    def test_an_unreadable_registry_refuses_rather_than_guessing(self) -> None:
        with mock.patch.dict(os.environ, {registry.ENV_REGISTRY: str(self.root / "gone")}):
            with self.assertRaises(principals.UnregisteredPrincipal):
                principals.instance_principal("principal:worker", self.root)

    def test_the_live_registry_maps_the_principal_the_report_named(self) -> None:
        """The exact spelling that failed on 2026-09-05, graded against the live file."""
        with mock.patch.dict(os.environ, {registry.ENV_REGISTRY: ""}):
            loaded, reason = registry.load(ROOT)
            self.assertIsNotNone(loaded, reason)
            kind = registry.index(loaded)["principal:claude-fable-5"]["kind"].lower()
            self.assertEqual(f"urn:soveraeign:principal:{kind}:claude-fable-5",
                             principals.instance_principal("principal:claude-fable-5", ROOT))


class CommandLineTests(unittest.TestCase):
    """`take` and `helper` through the parser, against a temporary store."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name) / "store"
        self.directory.mkdir()
        path = _registry(Path(self.tmp.name), revoked=("gone",), worker="MODEL", gone="MODEL")
        patcher = mock.patch.dict(os.environ, {registry.ENV_REGISTRY: str(path)})
        patcher.start()
        self.addCleanup(patcher.stop)
        context = mock.patch.object(commands, "_context",
                                    return_value=(ROOT, self.directory, "session-test"))
        context.start()
        self.addCleanup(context.stop)

    def _run(self, argv: list[str]) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = sov_lease.main(argv)
        return code, out.getvalue(), err.getvalue()

    def _lease(self, lease_id: str) -> dict:
        return store.leases(self.directory)[lease_id]

    def test_take_accepts_the_registry_spelling(self) -> None:
        code, _, err = self._run(TAKE + ["--principal", "principal:worker"])
        self.assertEqual(0, code, err)
        self.assertEqual("urn:soveraeign:principal:model:worker",
                         self._lease("lease:1")["holder"]["principal_id"])

    def test_take_refuses_an_unregistered_spelling_with_exit_1(self) -> None:
        code, _, err = self._run(TAKE + ["--principal", "principal:nobody"])
        self.assertEqual(1, code)
        self.assertIn(principals.UNREGISTERED_PRINCIPAL, err)
        self.assertEqual({}, store.leases(self.directory), "a refused take wrote a lease")

    def test_take_refuses_a_revoked_spelling_with_exit_1(self) -> None:
        code, _, err = self._run(TAKE + ["--principal", "principal:gone"])
        self.assertEqual(1, code)
        self.assertIn(principals.REVOKED_PRINCIPAL, err)
        self.assertEqual({}, store.leases(self.directory), "a refused take wrote a lease")

    def test_helper_accepts_the_registry_spelling_through_the_same_mapping(self) -> None:
        self.assertEqual(0, self._run(TAKE)[0])
        with mock.patch.object(principals, "instance_principal",
                               wraps=principals.instance_principal) as mapping:
            code, _, err = self._run(HELPER + ["--principal", "principal:worker"])
        self.assertEqual(0, code, err)
        self.assertEqual("urn:soveraeign:principal:model:worker",
                         self._lease("lease:1-part")["holder"]["principal_id"])
        mapping.assert_called_once()

    def test_cleanup_obligations_land_under_closure(self) -> None:
        code, _, err = self._run(TAKE + ["--cleanup", "release the lease",
                                         "--cleanup", "remove the worktree"])
        self.assertEqual(0, code, err)
        self.assertEqual(["release the lease", "remove the worktree"],
                         self._lease("lease:1")["closure"]["cleanup_obligations"])

    def test_no_cleanup_option_records_an_empty_list_not_an_absence(self) -> None:
        self.assertEqual(0, self._run(TAKE)[0])
        self.assertEqual([], self._lease("lease:1")["closure"]["cleanup_obligations"])

    def test_an_empty_cleanup_obligation_is_refused_by_the_contract(self) -> None:
        code, _, err = self._run(TAKE + ["--cleanup", ""])
        self.assertEqual(1, code)
        self.assertIn("cleanup_obligations", err)
        self.assertEqual({}, store.leases(self.directory), "a refused take wrote a lease")


if __name__ == "__main__":
    unittest.main()
