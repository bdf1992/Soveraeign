"""Cases for the fresh participation probe, the P15-X1 vertical slice.

Every case runs against a temporary store and a temporary registry copy carrying one
declared fixture principal, so the suite asserts nothing about which model this host
runs. The positive run must satisfy the three P15-Q1 predicates through the independent
instrument; each defeating variant must fail exactly the predicates it declares; and the
probe must refuse to guess a principal.
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

from sovfresh import probe  # noqa: E402
from sovsession import principals  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = "principal:fresh-probe"


class ProbeCase(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp.cleanup)
        self.temp = Path(self._temp.name)
        registry, reason = principals.load(ROOT)
        self.assertIsNotNone(registry, reason)
        registry["principals"].append({
            "principal_id": FIXTURE, "kind": "MODEL", "durability": "EPHEMERAL",
            "controller": registry["root_principal"],
            "anchor": {"kind": "fixture", "reference": __file__},
            "crossing_class": "in-node", "model": None, "delegation": None,
            "claim": {"claimed_at": "2026-09-06T00:00:00Z", "claim_basis": "test fixture",
                      "verification": "UNVERIFIED"},
            "verification_channel": {"kind": "local-file", "reference": "temporary"},
            "revoked": None,
        })
        path = self.temp / "principals.json"
        path.write_text(json.dumps(registry), encoding="utf-8")
        self._saved = os.environ.get(principals.ENV_REGISTRY)
        os.environ[principals.ENV_REGISTRY] = str(path)

    def tearDown(self) -> None:
        if self._saved is None:
            os.environ.pop(principals.ENV_REGISTRY, None)
        else:
            os.environ[principals.ENV_REGISTRY] = self._saved

    def run_variant(self, variant: str = "positive", principal: str = FIXTURE) -> dict:
        return probe.run(ROOT, self.temp / variant, principal, variant)


class PositiveRun(ProbeCase):
    def test_every_q1_predicate_holds(self) -> None:
        result = self.run_variant()
        self.assertTrue(result["passed"], json.dumps(result["grades"], indent=1))
        self.assertEqual(result["other_defects"], [])

    def test_identities_are_four_distinct_values(self) -> None:
        identities = self.run_variant()["observations"]["P15-Q1.3"]["identities"]
        self.assertEqual(len(set(identities.values())), 4)
        self.assertEqual(identities["principal_id"], FIXTURE)
        self.assertTrue(identities["session_id"].startswith("fresh-"))
        self.assertEqual(identities["grant_id"], "grant:standing-landing-loop")

    def test_work_survives_and_names_its_cleanup(self) -> None:
        work = self.run_variant()["observations"]["P15-Q1.2"]
        self.assertTrue(work["survives_session"])
        self.assertTrue(work["work"]["custody_or_lease"].startswith("lease:"))
        self.assertTrue(any(item.startswith("release lease:")
                            for item in work["work"]["cleanup_obligations"]))
        self.assertTrue(any(item.startswith("end session ")
                            for item in work["work"]["cleanup_obligations"]))

    def test_projection_is_derived_not_declared(self) -> None:
        first = self.run_variant()["observations"]["P15-Q1.1"]["record_projection_id"]
        self.assertTrue(first.startswith("urn:soveraeign:record-projection:sha256:")
                        or first.startswith("urn:soveraeign:record-projection:"))
        self.assertGreater(len(first.rsplit(":", 1)[-1]), 32)

    def test_own_principal_holds_no_standing_grant(self) -> None:
        trace = "\n".join(self.run_variant()["trace"])
        self.assertIn(f"authority for '{FIXTURE}': REFUSED AUTHORITY_REFUSED", trace)
        self.assertIn("foreign session SESSION_ATTRIBUTION_CONFLICT", trace)


class DefeatingVariants(ProbeCase):
    def test_unregistered_principal_defeats_entry_and_separation(self) -> None:
        result = self.run_variant("unregistered-principal", "principal:nobody")
        self.assertTrue(result["grades"]["P15-Q1.1"])
        self.assertTrue(result["grades"]["P15-Q1.3"])
        self.assertFalse(result["grades"]["P15-Q1.2"])
        self.assertIsNone(result["principal"])

    def test_work_bound_to_the_session_does_not_survive_it(self) -> None:
        result = self.run_variant("work-dies-with-session")
        self.assertEqual(result["grades"]["P15-Q1.2"],
                         ["durable work missing custody_or_lease",
                          "work does not survive the carrying session"])
        self.assertFalse(result["grades"]["P15-Q1.1"])
        self.assertFalse(result["grades"]["P15-Q1.3"])

    def test_borrowed_actor_is_caught_by_the_instrument(self) -> None:
        result = self.run_variant("borrowed-authority")
        self.assertEqual(result["grades"]["P15-Q1.3"],
                         ["cross-principal/session mismatch did not refuse"])
        self.assertEqual(
            result["observations"]["P15-Q1.3"]["cross_principal_session_mismatch"],
            "PERMITTED")
        self.assertFalse(result["grades"]["P15-Q1.1"])

    def test_unknown_variant_is_refused_by_name(self) -> None:
        with self.assertRaises(ValueError):
            self.run_variant("made-up")


class CommandLine(unittest.TestCase):
    def test_run_without_a_principal_refuses_rather_than_guessing(self) -> None:
        env = {key: value for key, value in os.environ.items()
               if key != principals.ENV_PRINCIPAL}
        completed = subprocess.run(
            [sys.executable, "scripts/sov_fresh.py", "run"], cwd=str(ROOT), env=env,
            capture_output=True, text=True, check=False)
        self.assertEqual(completed.returncode, 2)
        self.assertIn("PRINCIPAL_REQUIRED", completed.stdout)

    def test_selfcheck_passes(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/sov_fresh.py", "selfcheck"], cwd=str(ROOT),
            capture_output=True, text=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("PASS", completed.stdout)


if __name__ == "__main__":
    unittest.main()
