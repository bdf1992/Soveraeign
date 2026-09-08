"""Prove a verification run writes nothing into the operational landing ledger.

`scripts/sov_land.py` bound `ROOT = repo.ROOT` at import. `sovland.repo` reads its own
`ROOT` at call time, so a test pointing it at a temporary repository moved the git
operations there and left the stale copy behind: git ran against the temporary tree while
`ledger.record(ROOT, ...)` appended to the real checkout's `.local/landing/ledger.ndjson`.
An independent reading found 144 rows of pure test traffic in operational accounting, and
running the verification suite added more.

Two readings here. The first is the mechanism, on a temporary repository, so it fails when
the two roots diverge again. The second runs the three modules that exercise the landing
path - `test_repository_candidate_effects`, `test_landing_ledger` and
`test_landing_isolation` - as a subprocess against this checkout, and asserts the
operational ledger's bytes do not move. That is the property that was actually violated
and the one a mechanism test alone would not have caught.

An earlier form of this sentence called that second reading "the whole suite". It is not,
and an independent reading caught the overclaim: a check describing itself as wider than
it is understates what could still slip past it.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_land  # noqa: E402
from sovland import ledger, repo  # noqa: E402

OPERATIONAL = ROOT / ledger.LEDGER_PATH


def digest(path: Path) -> str:
    """The ledger's bytes, or a stable marker when it does not exist."""
    return sha256(path.read_bytes()).hexdigest() if path.exists() else "absent"


class TheEffectiveRootIsOne(unittest.TestCase):
    def test_the_landing_root_follows_the_repository_root(self):
        """The mechanism. A copy taken at import does not move when the root is patched."""
        with TemporaryDirectory() as tmp:
            elsewhere = Path(tmp)
            with mock.patch.object(repo, "ROOT", elsewhere):
                self.assertEqual(sov_land._root(), elsewhere)
        self.assertEqual(sov_land._root(), repo.ROOT)

    def test_the_ledger_path_resolves_inside_the_repository_root(self):
        """The consequence, asserted on the path and never by writing to it.

        The first form of this case computed `ledger_path(_root())` and wrote a row to it,
        which under the very defect it was written to detect is the operational ledger. It
        destroyed 156 rows of that ledger on its first defeating run. A case that proves a
        write goes to the wrong place must never perform the write.
        """
        with TemporaryDirectory() as tmp:
            elsewhere = Path(tmp)
            with mock.patch.object(repo, "ROOT", elsewhere):
                target = ledger.ledger_path(sov_land._root())
            self.assertEqual(target, elsewhere / ledger.LEDGER_PATH)
            self.assertFalse(
                str(target.resolve()).startswith(str(ROOT.resolve()) + "/"),
                "the ledger path resolved inside the real checkout while the root was "
                "pointed elsewhere")


class VerificationLeavesTheOperationalLedgerAlone(unittest.TestCase):
    """The property that was violated, read on the real checkout rather than a fixture."""

    def test_the_tooling_suite_appends_no_row(self):
        before = digest(OPERATIONAL)
        done = subprocess.run(
            [sys.executable, "-m", "unittest",
             "scripts.tests.test_repository_candidate_effects",
             "scripts.tests.test_landing_ledger",
             "scripts.tests.test_landing_isolation"],
            cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr[-2000:])
        self.assertEqual(digest(OPERATIONAL), before,
                         "running the landing tests changed the operational ledger")


if __name__ == "__main__":
    unittest.main()
