"""Cases for `verify.py --observe`, the flag every CI job now depends on.

`scripts/tests/test_repository_ci_workflows.py` requires each workflow's
verification step to pass this flag and each job to keep the file it writes.
That requirement is only worth holding if the flag does what the workflows
assume, so these cases exercise the CLI surface itself rather than `observe()`
as a function: the file is written, it parses, it carries one record per check,
and it survives the failing run. The last is the one that matters. A red run is
the reading a later participant most needs, and the records are written before
`main` returns non-zero rather than on the passing path only.

The check table is replaced with two trivial commands, so this reads the CLI's
own behaviour in well under a second and never depends on the repository's
current checks passing.
"""

from __future__ import annotations

from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
import io
import json
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import verify  # noqa: E402
from sovverify.shape import ROOT, Check  # noqa: E402


def _check(name: str, code: int) -> Check:
    """One check that exits with `code` and reads one address that exists."""
    return Check(name, [sys.executable, "-c", f"raise SystemExit({code})"], ROOT,
                 f"constructed for this case; exits {code} without reading a report",
                 ("AGENTS.md",))


def _run(checks: list[Check], target: Path) -> tuple[int, list[dict]]:
    with patch.object(verify, "CHECKS", checks), redirect_stdout(io.StringIO()):
        code = verify.main(["--observe", str(target)], run_id="run_case",
                           now="2026-09-08T00:00:00+00:00")
    if not target.exists():
        return code, []
    return code, json.loads(target.read_text(encoding="utf-8"))


class ObserveWritesWhatTheWorkflowsKeep(unittest.TestCase):
    def test_a_passing_run_writes_one_record_per_check(self):
        with tempfile.TemporaryDirectory() as room:
            target = Path(room) / "observations.json"
            code, rows = _run([_check("first", 0), _check("second", 0)], target)
        self.assertEqual(0, code)
        self.assertEqual(["first", "second"], [row["subject"] for row in rows])
        self.assertEqual({"PASS"}, {row["predicate_results"]["outcome"] for row in rows})
        self.assertEqual({"run_case"}, {row["run_id"] for row in rows})

    def test_a_failing_run_still_leaves_its_records(self):
        """The red run is the reading worth keeping, so the file precedes the exit."""
        with tempfile.TemporaryDirectory() as room:
            target = Path(room) / "observations.json"
            code, rows = _run([_check("fine", 0), _check("broken", 3)], target)
        self.assertEqual(1, code)
        outcomes = {row["subject"]: row["predicate_results"] for row in rows}
        self.assertEqual("FAIL", outcomes["broken"]["outcome"])
        self.assertEqual(3, outcomes["broken"]["exit_code"])
        self.assertEqual("PASS", outcomes["fine"]["outcome"])

    def test_the_records_name_the_addresses_their_check_declared(self):
        with tempfile.TemporaryDirectory() as room:
            target = Path(room) / "observations.json"
            _, rows = _run([_check("first", 0)], target)
        self.assertEqual(["AGENTS.md"], rows[0]["observed_state_addresses"])
        self.assertEqual(1, len(rows[0]["observed_state_digests"]))
        self.assertTrue(rows[0]["observed_state_digests"][0].startswith("sha256:"))

    def test_a_missing_directory_is_created_rather_than_losing_the_run(self):
        """CI writes under $RUNNER_TEMP; a path whose parent is absent must not throw."""
        with tempfile.TemporaryDirectory() as room:
            target = Path(room) / "not" / "yet" / "observations.json"
            code, rows = _run([_check("first", 0)], target)
        self.assertEqual(0, code)
        self.assertEqual(1, len(rows))


if __name__ == "__main__":
    unittest.main()
