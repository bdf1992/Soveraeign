"""Cases for the discovery and reuse probe, the P15-X3 vertical slice.

Every case reads a fixture artifact built under a temporary directory by a fixture
principal under a fixture root, so the suite asserts nothing about which model this host
runs or about the repository's own witness records. The positive variant must satisfy
both P15-Q3 predicates through the independent instrument; each defeating variant must
fail exactly the predicates it declares; and the layers must read what they claim to.
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

from sovreuse import discover, fixture, settle  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


class FixtureCase(unittest.TestCase):
    """One fixture per class: the builder's run costs more than every reading of it."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._temp = tempfile.TemporaryDirectory()
        cls.temp = Path(cls._temp.name)
        cls.fixture = fixture.build(cls.temp)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temp.cleanup()


class PositiveRun(FixtureCase):
    def test_both_q3_predicates_hold(self) -> None:
        result = fixture.run_variant(self.fixture, "positive", self.temp)
        self.assertTrue(result["passed"], result["grades"])
        self.assertEqual(result["other_defects"], [])

    def test_every_reading_comes_from_the_artifact(self) -> None:
        result = fixture.run_variant(self.fixture, "positive", self.temp)
        q32 = result["observations"]["P15-Q3.2"]
        self.assertEqual(q32["result_address"], fixture.FIXTURE_SUBJECT)
        self.assertEqual(q32["standing"], "WITNESSED")
        self.assertEqual(q32["receipt_addresses"], [fixture.FIXTURE_RECEIPT])
        self.assertIn("restore-journal nodes/node-local/journal/", q32["capability"])
        self.assertTrue(q32["fresh_participant_used_result"])
        self.assertTrue(result["observations"]["P15-Q3.1"]["closure_receipt"])
        self.assertEqual(result["facts"]["work_state_derived"], "LANDED")
        self.assertEqual(result["result"]["basis"]["read_from"], "prose")


class DefeatingVariants(FixtureCase):
    def test_each_variant_fails_its_predicates_for_its_reason(self) -> None:
        for variant, expected in fixture.EXPECTED_FAILURES.items():
            result = fixture.run_variant(self.fixture, variant, self.temp)
            failed = {p for p, defects in result["grades"].items() if defects}
            self.assertEqual(failed, set(expected), f"{variant}: {result['grades']}")
            for predicate, reason in expected.items():
                self.assertIn(reason, result["grades"][predicate], variant)

    def test_no_grant_reaches_the_node_and_is_refused_by_it(self) -> None:
        result = fixture.run_variant(self.fixture, "positive", self.temp)
        self.assertIsNotNone(result["reached"]["capability"])
        result = fixture.run_variant(self.fixture, "no-grant", self.temp)
        self.assertFalse(result["used"]["used"])
        self.assertIn("principal:bdo", result["used"]["reason"])

    def test_head_private_never_restores(self) -> None:
        result = fixture.run_variant(self.fixture, "head-private", self.temp)
        self.assertIsNone(result["reached"]["capability"])
        self.assertIn("outside the export", result["reached"]["reason"])
        self.assertFalse(result["used"]["used"])


class Layers(unittest.TestCase):
    def test_basis_addresses_come_from_prose_or_nowhere(self) -> None:
        member = {"stage_observed_by": "pass 6 (witness/a.md; witness/observations/b.json)"}
        basis = discover.basis_addresses(member)
        self.assertEqual(basis, {"record": ["witness/a.md"],
                                 "receipts": ["witness/observations/b.json"],
                                 "read_from": "prose"})
        self.assertEqual(discover.basis_addresses({})["read_from"], "none")

    def test_current_state_tells_drift_from_absence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "same").write_bytes(b"x")
            (root / "moved").write_bytes(b"y")
            digest = "sha256:2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881"
            receipts = [{"observed": {"same": digest, "moved": digest, "gone": digest}}]
            self.assertEqual(settle.current_state(root, receipts, "same"),
                             {"matching": ["same"], "drifted": ["moved"], "missing": ["gone"],
                              "covers_result": True})

    def test_independence_needs_a_record_and_an_independent_receipt(self) -> None:
        receipt = {"exists": True, "standing_supported": "WITNESSED",
                   "observer_relation": "INDEPENDENT_OF_BUILDER"}
        self.assertTrue(settle.independent_observation(
            {"standing_supported": "WITNESSED"}, [receipt])[0])
        self.assertFalse(settle.independent_observation(None, [receipt])[0])
        self.assertFalse(settle.independent_observation(
            {"standing_supported": "WITNESSED"}, [dict(receipt, observer_relation="BUILDER")])[0])

    def test_landing_is_the_merge_that_carried_the_revision(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            artifact = Path(temp) / "artifact"
            revision = fixture._fixture_history(artifact)
            landed = settle.landing(artifact, revision)
            self.assertEqual(landed["subject"], "merge: fixture landing")
            self.assertEqual(settle.landing(artifact, "0" * 40), {"commit": None, "subject": None})
            self.assertEqual(settle.temporary_inventory(artifact, None, None, revision), [])
            fixture._git(artifact, "branch", "-q", "feat/left", revision)
            self.assertEqual(settle.temporary_inventory(artifact, None, None, revision),
                             ["branch feat/left"])

    def test_a_receipt_that_skips_the_result_settles_nothing_about_it(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "other").write_bytes(b"x")
            digest = "sha256:2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881"
            state = settle.current_state(root, [{"observed": {"other": digest}}], "result")
            self.assertFalse(state["covers_result"])
            self.assertEqual(settle.current_state(root, [{"observed": None}], "result"),
                             {"matching": [], "drifted": [], "missing": [],
                              "covers_result": False})

    def test_malformed_artifact_reads_as_defects_not_tracebacks(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / discover.CUSTODY_COLLECTION
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({"custodies": ["not a custody", {"custody_id": "c",
                                        "members": [7, {"standing": "WITNESSED"}]}]}))
            result = discover.discover(root, "c")
            self.assertIn("the member names no witness record", result["defects"])
            receipt = root / "witness/observations/r.json"
            receipt.parent.mkdir(parents=True)
            malformed = {"observed_state_addresses": ["a"], "observed_state_digests": [],
                         "node_state": {"head_held_outside_the_export": 5}}
            receipt.write_text(json.dumps({"observed": malformed}))
            read = discover.read_receipt(root, "witness/observations/r.json")
            self.assertIsNone(read["observed"])
            self.assertIsNone(read["outside_head"])


class Refusals(unittest.TestCase):
    def test_run_refuses_to_guess_a_principal(self) -> None:
        done = subprocess.run([sys.executable, "scripts/sov_reuse.py", "run"], cwd=ROOT,
                              capture_output=True, text=True,
                              env={k: v for k, v in os.environ.items() if k != "SOV_PRINCIPAL"})
        self.assertEqual(done.returncode, 2, done.stdout)
        self.assertIn("PRINCIPAL_REQUIRED", done.stdout)

    def test_json_output_is_machine_readable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            built = fixture.build(Path(temp))
            result = fixture.run_variant(built, "positive", Path(temp))
        json.dumps(result, default=str)


if __name__ == "__main__":
    unittest.main()
