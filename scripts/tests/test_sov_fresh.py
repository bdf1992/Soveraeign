"""Cases for the fresh participation probe, the P15-X1 vertical slice.

Every case runs against a temporary store, a temporary node, and a temporary registry copy
carrying one declared fixture principal, so the suite asserts nothing about which model
this host runs. The positive run must satisfy the three P15-Q1 predicates through the
independent instrument with every value read from a product record; each defeating
variant must fail exactly the predicates it declares; and the probe must refuse to guess
a principal.
"""

from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import sov_fresh  # noqa: E402
from sovfresh import node as nodelayer, probe  # noqa: E402
from sovsession import principals  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = sov_fresh.FIXTURE_PRINCIPAL
ISSUER = sov_fresh.FIXTURE_ISSUER


class ProbeCase(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp.cleanup)
        self.temp = Path(self._temp.name)
        self.registry = sov_fresh.fixture_registry(self.temp)

    def run_variant(self, variant: str = "positive", principal: str = FIXTURE,
                    issuer: str | None = ISSUER) -> dict:
        return probe.run(ROOT, self.temp / variant, principal, variant,
                         registry=self.registry, issuer=issuer)


class PositiveRun(ProbeCase):
    def test_every_q1_predicate_holds(self) -> None:
        result = self.run_variant()
        self.assertTrue(result["passed"], result["grades"])
        self.assertEqual(result["other_defects"], [])

    def test_identities_come_from_node_records(self) -> None:
        result = self.run_variant()
        identities = result["observations"]["P15-Q1.3"]["identities"]
        self.assertEqual(len(set(identities.values())), 4)
        self.assertEqual(identities["principal_id"], FIXTURE)
        self.assertTrue(identities["session_id"].startswith("session_"))
        self.assertTrue(identities["grant_id"].startswith("grant_"))
        self.assertEqual(identities["interface_binding_id"],
                         "urn:soveraeign:binding:node-interface:model-json-v1")

    def test_the_node_refused_every_borrowed_fact_and_admitted_the_owner(self) -> None:
        node = self.run_variant()["node"]
        self.assertEqual(node["own"]["outcome"], "COMMITTED")
        refusals = node["refusals"]
        self.assertEqual(refusals["foreign_session"]["diagnostic"], "ACTOR_ATTRIBUTION_MISMATCH")
        self.assertEqual(refusals["foreign_session"]["stage"], "check-attribution")
        self.assertTrue(refusals["foreign_session"]["receipt_id"])
        self.assertEqual(refusals["other_actor_on_this_session"]["diagnostic"],
                         "ACTOR_ATTRIBUTION_MISMATCH")
        self.assertEqual(refusals["beyond_the_grant"]["diagnostic"], "AuthorityRefused")
        self.assertEqual(refusals["beyond_the_grant"]["stage"], "check-authority")

    def test_work_survives_and_cleanup_is_read_from_the_stores(self) -> None:
        work = self.run_variant()["observations"]["P15-Q1.2"]
        self.assertTrue(work["survives_session"])
        lease = work["work"]["custody_or_lease"]
        self.assertTrue(lease.startswith("lease:"))
        self.assertIn(f"release {lease}", work["work"]["cleanup_obligations"])
        self.assertFalse(any(item.startswith("close console session")
                             for item in work["work"]["cleanup_obligations"]))

    def test_projection_is_derived_from_the_node_record(self) -> None:
        projection_id = self.run_variant()["observations"]["P15-Q1.1"]["record_projection_id"]
        self.assertTrue(projection_id.startswith("urn:soveraeign:record-projection:"))
        self.assertEqual(len(projection_id.rsplit(":", 1)[-1]), 64)

    def test_oral_history_is_earned_not_asserted(self) -> None:
        saved = os.environ.get(principals.ENV_REGISTRY)
        os.environ[principals.ENV_REGISTRY] = str(self.registry)
        try:
            undeclared = probe.run(ROOT, self.temp / "undeclared", FIXTURE, issuer=ISSUER)
            declared = probe.run(ROOT, self.temp / "declared", FIXTURE, issuer=ISSUER,
                                 registry=self.registry)
        finally:
            if saved is None:
                os.environ.pop(principals.ENV_REGISTRY, None)
            else:
                os.environ[principals.ENV_REGISTRY] = saved
        self.assertTrue(undeclared["observations"]["P15-Q1.1"]["oral_history_used"])
        self.assertIn("fresh participation required oral history",
                      undeclared["grades"]["P15-Q1.1"])
        self.assertFalse(undeclared["passed"])
        self.assertFalse(declared["observations"]["P15-Q1.1"]["oral_history_used"])
        self.assertTrue(declared["passed"])

    def test_an_inherited_principal_variable_does_not_reach_the_resolver(self) -> None:
        saved = os.environ.get(principals.ENV_PRINCIPAL)
        os.environ[principals.ENV_PRINCIPAL] = "principal:bdo"
        try:
            result = self.run_variant()
        finally:
            if saved is None:
                os.environ.pop(principals.ENV_PRINCIPAL, None)
            else:
                os.environ[principals.ENV_PRINCIPAL] = saved
        self.assertEqual(result["principal"], FIXTURE)
        self.assertTrue(result["passed"])

    def test_the_issuer_gate_reads_the_registry_the_resolver_reads(self) -> None:
        other = self.temp / "other-root.json"
        other.write_text(self.registry.read_text(encoding="utf-8").replace(
            f'"root_principal": "{ISSUER}"', '"root_principal": "principal:other-root"'),
            encoding="utf-8")
        saved = os.environ.get(principals.ENV_REGISTRY)
        os.environ[principals.ENV_REGISTRY] = str(other)
        try:
            result = probe.run(ROOT, self.temp / "env-root", FIXTURE, issuer=ISSUER)
        finally:
            if saved is None:
                os.environ.pop(principals.ENV_REGISTRY, None)
            else:
                os.environ[principals.ENV_REGISTRY] = saved
        self.assertEqual(result["root_principal"], "principal:other-root")
        self.assertEqual(result["registry"], str(other))
        self.assertEqual(result["observations"]["P15-Q1.1"]["registry"], str(other))
        self.assertEqual(result["node"]["refused_by"], "PROBE_ISSUER_GATE")
        self.assertIsNone(result["observations"]["P15-Q1.3"]["identities"]["grant_id"])

    def test_the_issuer_gate_names_itself_as_the_probes_rule(self) -> None:
        result = self.run_variant(issuer="principal:nobody-at-all")
        self.assertEqual(result["node"]["refused_by"], "PROBE_ISSUER_GATE")
        self.assertTrue(result["node"]["admitted"].startswith("probe rule PROBE_ISSUER_GATE:"))
        admitted = self.run_variant()["node"]
        self.assertIsNone(admitted["refused_by"])
        self.assertIsNone(admitted["admitted"])

    def test_only_the_registry_root_may_issue(self) -> None:
        for issuer in ("principal:nobody-at-all", "", "principal:bdo"):
            result = self.run_variant(issuer=issuer)
            self.assertIsNone(result["observations"]["P15-Q1.3"]["identities"]["grant_id"], issuer)
            self.assertIn("is not the registry's root principal", result["node"]["admitted"])
            self.assertFalse(result["passed"], issuer)


class DefeatingVariants(ProbeCase):
    def test_unregistered_principal_defeats_entry_and_separation(self) -> None:
        result = self.run_variant("unregistered-principal")
        self.assertTrue(result["grades"]["P15-Q1.1"])
        self.assertTrue(result["grades"]["P15-Q1.3"])
        self.assertFalse(result["grades"]["P15-Q1.2"])
        self.assertIsNone(result["principal"])

    def test_the_declared_principal_cannot_rescue_the_unregistered_variant(self) -> None:
        result = self.run_variant("unregistered-principal", principal="principal:bdo")
        self.assertIsNone(result["principal"])
        self.assertFalse(result["passed"])

    def test_work_bound_to_the_session_does_not_survive_it(self) -> None:
        result = self.run_variant("work-dies-with-session")
        self.assertIn("durable work missing custody_or_lease", result["grades"]["P15-Q1.2"])
        self.assertIn("work does not survive the carrying session", result["grades"]["P15-Q1.2"])
        self.assertFalse(result["grades"]["P15-Q1.1"])
        self.assertFalse(result["grades"]["P15-Q1.3"])

    def test_a_node_with_no_grant_cannot_show_identity_separation(self) -> None:
        result = self.run_variant("no-grant")
        self.assertIn("identity separation missing session_id", result["grades"]["P15-Q1.3"])
        self.assertIn("identity separation missing grant_id", result["grades"]["P15-Q1.3"])
        self.assertEqual(result["node"]["own"]["outcome"], "REFUSED")
        self.assertFalse(result["grades"]["P15-Q1.1"])
        self.assertFalse(result["grades"]["P15-Q1.2"])

    def test_no_grant_is_also_what_a_run_without_an_issuer_reads(self) -> None:
        result = self.run_variant(issuer=None)
        self.assertTrue(result["grades"]["P15-Q1.3"])
        self.assertFalse(result["passed"])

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

    def test_json_is_accepted_after_the_subcommand(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/sov_fresh.py", "run", "--principal", "principal:bdo",
             "--json"], cwd=str(ROOT), capture_output=True, text=True, check=False)
        self.assertEqual(completed.returncode, 1, completed.stdout[-500:])
        self.assertIn('"P15-Q1.3"', completed.stdout)

    def test_selfcheck_passes(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/sov_fresh.py", "selfcheck"], cwd=str(ROOT),
            capture_output=True, text=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("PASS", completed.stdout)


if __name__ == "__main__":
    unittest.main()


class PersistedNode(ProbeCase):
    """A node opened once by the fixture root, then entered without seeding anything."""

    def open_office(self, state: Path, operator: str = FIXTURE) -> list[dict]:
        with nodelayer.open_node_at(state) as node:
            return nodelayer.open_office(node, ISSUER, operator, {"read:registry": nodelayer.SCOPE})

    def test_open_office_records_every_grant_under_the_issuer(self) -> None:
        records = self.open_office(self.temp / "node")
        self.assertEqual([r["capability"] for r in records],
                         ["open:session", "close:session", "read:registry"])
        self.assertTrue(all(r["granted_by"] == ISSUER for r in records))
        with nodelayer.open_node_at(self.temp / "node") as node:
            entries = node.record.reconstruct()
            self.assertEqual(nodelayer.console_authority.root_issuer(entries, node.node_id),
                             ISSUER)
            export = nodelayer.export_journal(node)
            self.assertEqual(nodelayer.record_custody.verify_export(export), export["head_digest"])

    def test_a_granted_operator_enters_and_closes_its_own_session(self) -> None:
        state = self.temp / "node"
        self.open_office(state)
        result = probe.run(ROOT, self.temp / "run", FIXTURE, registry=self.registry,
                           node_state=state)
        self.assertTrue(result["passed"], result["grades"])
        self.assertEqual(result["actor"], FIXTURE)
        self.assertIsNone(result["issuer"])
        identities = result["observations"]["P15-Q1.3"]["identities"]
        self.assertTrue(identities["grant_id"].startswith("grant_"))
        self.assertTrue(any(step.endswith(" closed") for step in result["trace"]), result["trace"])
        self.assertFalse(any(item.startswith("close console session")
                             for item in result["observations"]["P15-Q1.2"]["work"]
                             ["cleanup_obligations"]))

    def test_an_operator_nobody_granted_cannot_show_identity_separation(self) -> None:
        state = self.temp / "node"
        self.open_office(state)
        result = probe.run(ROOT, self.temp / "run", "principal:bdo", registry=self.registry,
                           node_state=state)
        self.assertIn("identity separation missing grant_id", result["grades"]["P15-Q1.3"])
        self.assertIn("refused to open a session", result["node"]["admitted"])
        self.assertFalse(result["grades"]["P15-Q1.1"])
        self.assertFalse(result["grades"]["P15-Q1.2"])

    def test_a_persisted_node_refuses_the_seeding_options(self) -> None:
        state = self.temp / "node"
        self.open_office(state)
        for kwargs in ({"variant": "no-grant"}, {"issuer": ISSUER}):
            with self.assertRaises(ValueError):
                probe.run(ROOT, self.temp / "x", FIXTURE, registry=self.registry,
                          node_state=state, **kwargs)


class OfficeCommandLine(unittest.TestCase):
    def test_a_non_root_issuer_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp) / "never"
            completed = subprocess.run(
                [sys.executable, "scripts/sov_fresh.py", "open-office", "--node-state",
                 str(state), "--issuer", "principal:nobody", "--operator", "principal:x",
                 "--direction", "x", "--directed-in", "y"],
                cwd=str(ROOT), capture_output=True, text=True, check=False)
            self.assertEqual(completed.returncode, 2, completed.stdout)
            self.assertIn("PROBE_ISSUER_GATE", completed.stdout)
            self.assertFalse(state.exists())

    def test_seeding_options_on_a_persisted_node_refuse_without_a_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            completed = subprocess.run(
                [sys.executable, "scripts/sov_fresh.py", "run", "--principal", "principal:bdo",
                 "--node-state", str(Path(temp) / "node"), "--variant", "no-grant"],
                cwd=str(ROOT), capture_output=True, text=True, check=False)
            self.assertEqual(completed.returncode, 2, completed.stdout + completed.stderr)
            self.assertIn("REFUSED VARIANT_NOT_ADMITTED", completed.stdout)
            self.assertNotIn("Traceback", completed.stderr)
