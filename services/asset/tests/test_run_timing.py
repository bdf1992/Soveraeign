"""Prove a delegated run's wall clock is recoverable, and honest about what it measures.

`SPEC.md`'s `Run` declares `started_at` and `completed_at`. Until 2026-08-24 the table
carried only `created_at`, so the elapsed time of a delegated run could not be computed
even in principle - which is why `reports/2026-08-24-product-canon-attribution-discovery.md`
recorded the job window as the station where effort is spent and least is recorded.

These cases establish `BUILT` for the timing columns. They witness nothing: a recorded
duration is not a cost, not a budget, and not evidence that the work was worth doing.
"""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "services" / "asset" / "src"))

from soveraeign_asset_service.core import AssetService  # noqa: E402


class RunTimingTest(unittest.TestCase):
    """The four states a run moves through, and what each one stamps."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self._tmp.name)
        self.ticks = iter([float(n) for n in range(1, 4000)])
        self.service = AssetService(self.root / "store", clock=lambda: next(self.ticks))
        self.service.grant("Bdo", "Bdo", "operate:derive")
        payload = self.root / "source.txt"
        payload.write_bytes(b"original bytes")
        self.asset = self.service.ingest(payload, "source", "Bdo")

    def tearDown(self) -> None:
        self.service.close()
        self._tmp.cleanup()

    def _run_to_observation(self) -> str:
        run = self.service.runs.request(self.asset["asset_id"], self.asset["version_id"],
                                        "Bdo")
        fence = self.service.runs.claim(run, "worker-1")
        self.service.runs.report(run, "worker-1", fence, b'{"card": true}')
        self.service.runs.observe(run, "observer-1")
        return run

    def test_an_unclaimed_run_reports_no_elapsed_time(self) -> None:
        """A requested run has not started, and None is the honest answer."""
        run = self.service.runs.request(self.asset["asset_id"], self.asset["version_id"],
                                        "Bdo")
        self.assertIsNone(self.service.runs.elapsed(run))

    def test_a_reported_but_unobserved_run_reports_no_elapsed_time(self) -> None:
        """A worker's report does not complete a run; only observation does."""
        run = self.service.runs.request(self.asset["asset_id"], self.asset["version_id"],
                                        "Bdo")
        fence = self.service.runs.claim(run, "worker-1")
        self.service.runs.report(run, "worker-1", fence, b'{"card": true}')
        self.assertIsNone(self.service.runs.elapsed(run))

    def test_an_observed_run_reports_the_time_between_lease_and_observation(self) -> None:
        run = self._run_to_observation()
        elapsed = self.service.runs.elapsed(run)
        self.assertIsNotNone(elapsed)
        self.assertGreater(elapsed, 0)

    def test_queue_time_is_not_counted_as_work(self) -> None:
        """A run that waits for a worker did not spend that wait working."""
        run = self.service.runs.request(self.asset["asset_id"], self.asset["version_id"],
                                        "Bdo")
        for _ in range(20):
            next(self.ticks)
        fence = self.service.runs.claim(run, "worker-1")
        self.service.runs.report(run, "worker-1", fence, b'{"card": true}')
        self.service.runs.observe(run, "observer-1")
        row = self.service.db.execute(
            "SELECT created_at, started_at FROM runs WHERE id=?", (run,)).fetchone()
        self.assertGreater(row["started_at"] - row["created_at"], 10)
        self.assertLess(self.service.runs.elapsed(run), row["started_at"] - row["created_at"])

    def test_an_unknown_run_is_refused_rather_than_reported_as_open(self) -> None:
        with self.assertRaises(KeyError):
            self.service.runs.elapsed("run_does_not_exist")

    def test_a_store_written_before_the_timing_columns_is_brought_forward(self) -> None:
        """An existing store must open, not fail on the first claim."""
        service = AssetService(self.root / "legacy")
        service.db.execute("DROP TABLE runs")
        service.db.execute(
            "CREATE TABLE runs(id TEXT PRIMARY KEY, kind TEXT NOT NULL, "
            "asset_id TEXT NOT NULL, input_version_id TEXT NOT NULL, "
            "requester TEXT NOT NULL, status TEXT NOT NULL, worker TEXT, "
            "lease_fence INTEGER NOT NULL DEFAULT 0, lease_expires REAL, "
            "output_version_id TEXT, report_json TEXT, observation_id TEXT, "
            "created_at REAL NOT NULL)")
        service.db.commit()
        reopened = AssetService(self.root / "legacy")
        held = {row["name"] for row in reopened.db.execute("PRAGMA table_info(runs)")}
        self.assertIn("started_at", held)
        self.assertIn("completed_at", held)
        reopened.close()
        service.close()


if __name__ == "__main__":
    unittest.main()
