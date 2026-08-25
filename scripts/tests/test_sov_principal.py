"""Cases for resolving which principal a session speaks as.

Every case builds its own registry in a temporary directory, so the suite proves the logic
with no registry checked in, no session registered, and no dependence on the host.

The refusals carry the weight. A resolver that reports whatever the registry claims is not
an identity check, it is a transcription: the cases below fix that a `VERIFIED` claim with
nothing behind it is reported `UNVERIFIED`, that a control chain which cycles or leaves the
registry yields an unknown hop distance rather than a plausible number, and that an absent
registry and an unreadable one are different answers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sovsession import principals  # noqa: E402

ROOT_ID = "principal:bdo"
SESSION_ID = "principal:session-a1"


def principal(pid: str, controller: str | None, **overrides: Any) -> dict[str, Any]:
    """One well-formed principal record, before a case bends it."""
    record = {
        "principal_id": pid,
        "kind": "HUMAN" if controller is None else "MODEL",
        "durability": "DURABLE" if controller is None else "INSTANCE",
        "controller": controller,
        "anchor": {"kind": "decision", "reference": "decisions/0001-founding-boundary.md"},
        "crossing_class": "in-node",
        "model": None,
        "delegation": None,
        "claim": {"claimed_at": "2026-08-24T00:00:00Z", "claim_basis": "a stated basis",
                  "verification": "UNVERIFIED"},
        "verification_channel": {"kind": "console-session", "reference": "interactive"},
        "revoked": None,
    }
    record.update(overrides)
    return record


def registry(*records: dict[str, Any], root: str = ROOT_ID) -> dict[str, Any]:
    """A registry holding the given principals."""
    return {"registry_schema": "soveraeign-principal-registry/v1", "status": "PROPOSED",
            "root_principal": root, "principals": list(records)}


class RegistryCase(unittest.TestCase):
    """A temporary node root, with the registry path and any override pointed at it."""

    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self._temp.name)
        (self.root / "contracts").mkdir()
        self._environment = dict(os.environ)
        for name in (principals.ENV_REGISTRY, principals.ENV_PRINCIPAL):
            os.environ.pop(name, None)

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._environment)
        self._temp.cleanup()

    def write(self, record: Any) -> None:
        """Put a registry at the declared path."""
        path = self.root / principals.REGISTRY_PATH
        text = record if isinstance(record, str) else json.dumps(record, indent=2)
        path.write_text(text, encoding="utf-8", newline="\n")

    def resolve(self, session: str = "session-a1") -> dict[str, Any]:
        """Resolve a session against whatever this case wrote."""
        return principals.resolve(self.root, session)


class AbsentCase(RegistryCase):
    """A node that has not written its registry, which is this branch today."""

    def test_no_registry_is_unidentified_and_names_the_file(self) -> None:
        claim = self.resolve()
        self.assertEqual(claim["verification"], principals.UNIDENTIFIED)
        self.assertIsNone(claim["principal"])
        self.assertIn(principals.REGISTRY_PATH, claim["basis"])

    def test_an_unreadable_registry_is_not_reported_as_an_absent_one(self) -> None:
        self.write("{ this is not json")
        claim = self.resolve()
        self.assertEqual(claim["verification"], principals.UNIDENTIFIED)
        self.assertIn("could not be read", claim["basis"])

    def test_a_file_that_is_not_a_registry_says_so(self) -> None:
        self.write({"registry_schema": "soveraeign-principal-registry/v1"})
        self.assertIn("is not a registry", self.resolve()["basis"])

    def test_a_registry_with_no_matching_principal_names_what_it_looked_for(self) -> None:
        self.write(registry(principal(ROOT_ID, None)))
        claim = self.resolve()
        self.assertEqual(claim["verification"], principals.UNIDENTIFIED)
        self.assertIn(SESSION_ID, claim["basis"])

    def test_the_render_of_an_unidentified_session_says_why(self) -> None:
        self.assertIn("unidentified", principals.render(self.resolve()))


class ResolveCase(RegistryCase):
    """A session the registry does name."""

    def setUp(self) -> None:
        super().setUp()
        self.write(registry(principal(ROOT_ID, None),
                            principal(SESSION_ID, ROOT_ID)))

    def test_a_named_session_resolves_to_its_principal(self) -> None:
        claim = self.resolve()
        self.assertEqual(claim["principal"], SESSION_ID)
        self.assertEqual(claim["kind"], "MODEL")
        self.assertEqual(claim["controller"], ROOT_ID)
        self.assertEqual(claim["basis"], "a stated basis")

    def test_hop_distance_is_derived_by_walking_controllers(self) -> None:
        self.assertEqual(self.resolve()["hops"], 1)
        self.assertEqual(principals.resolve(self.root, "bdo")["hops"], 0)

    def test_being_registered_is_not_being_verified(self) -> None:
        self.assertEqual(self.resolve()["verification"], principals.UNVERIFIED)
        self.assertEqual(self.resolve()["defects"], [])

    def test_an_explicit_principal_overrides_the_derived_name(self) -> None:
        os.environ[principals.ENV_PRINCIPAL] = ROOT_ID
        claim = self.resolve()
        self.assertEqual(claim["principal"], ROOT_ID)
        self.assertEqual(claim["hops"], 0)

    def test_a_session_already_named_as_a_principal_is_not_prefixed_twice(self) -> None:
        self.assertEqual(principals.resolve(self.root, SESSION_ID)["principal"], SESSION_ID)

    def test_the_render_names_the_principal_and_its_distance(self) -> None:
        line = principals.render(self.resolve())
        self.assertIn(SESSION_ID, line)
        self.assertIn("UNVERIFIED", line)
        self.assertIn("1 hop from", line)


class VerificationCase(RegistryCase):
    """What the resolver will and will not believe about a claim's strength."""

    def with_claim(self, **claim: Any) -> dict[str, Any]:
        """A registry whose session principal carries the given claim fields."""
        base = {"claimed_at": "2026-08-24T00:00:00Z", "claim_basis": "a stated basis"}
        base.update(claim)
        self.write(registry(principal(ROOT_ID, None),
                            principal(SESSION_ID, ROOT_ID, claim=base)))
        return self.resolve()

    def test_a_verified_claim_naming_what_verified_it_is_believed(self) -> None:
        claim = self.with_claim(verification="VERIFIED",
                                verification_basis="challenge chal-1 presented")
        self.assertEqual(claim["verification"], principals.VERIFIED)
        self.assertEqual(claim["defects"], [])

    def test_a_verified_claim_with_no_basis_is_reported_unverified(self) -> None:
        claim = self.with_claim(verification="VERIFIED")
        self.assertEqual(claim["verification"], principals.UNVERIFIED)
        self.assertIn("names no verification_basis", claim["defects"][0])

    def test_a_verified_claim_with_no_channel_is_reported_unverified(self) -> None:
        self.write(registry(
            principal(ROOT_ID, None),
            principal(SESSION_ID, ROOT_ID, verification_channel=None,
                      claim={"claimed_at": "2026-08-24T00:00:00Z",
                             "claim_basis": "a stated basis", "verification": "VERIFIED",
                             "verification_basis": "challenge chal-1 presented"})))
        claim = self.resolve()
        self.assertEqual(claim["verification"], principals.UNVERIFIED)
        self.assertIn("declares no verification channel", claim["defects"][0])

    def test_an_unknown_verification_value_is_not_treated_as_verified(self) -> None:
        claim = self.with_claim(verification="TRUSTED")
        self.assertEqual(claim["verification"], principals.UNVERIFIED)
        self.assertIn("unknown verification", claim["defects"][0])

    def test_a_revoked_principal_reports_revoked(self) -> None:
        self.write(registry(
            principal(ROOT_ID, None),
            principal(SESSION_ID, ROOT_ID,
                      revoked={"revoked_at": "2026-08-24T01:00:00Z",
                               "revoked_by": ROOT_ID, "reason": "session closed"})))
        self.assertEqual(self.resolve()["verification"], principals.REVOKED)


class ChainCase(RegistryCase):
    """The derived hop distance, and every way the walk can fail to produce one."""

    def test_a_cycle_on_the_walk_yields_an_unknown_distance_rather_than_a_number(self) -> None:
        self.write(registry(principal(ROOT_ID, None),
                            principal("principal:a", "principal:b"),
                            principal("principal:b", "principal:a"),
                            principal(SESSION_ID, "principal:a")))
        claim = self.resolve()
        self.assertIsNone(claim["hops"])
        self.assertTrue(any("revisits" in defect for defect in claim["defects"]))

    def test_a_controller_outside_the_registry_is_a_defect(self) -> None:
        self.write(registry(principal(ROOT_ID, None),
                            principal(SESSION_ID, "principal:ghost")))
        claim = self.resolve()
        self.assertIsNone(claim["hops"])
        self.assertIn("not a registered principal", claim["defects"][0])

    def test_a_chain_through_a_revoked_controller_is_a_defect(self) -> None:
        self.write(registry(
            principal(ROOT_ID, None),
            principal("principal:middle", ROOT_ID,
                      revoked={"revoked_at": "2026-08-24T01:00:00Z",
                               "revoked_by": ROOT_ID, "reason": "withdrawn"}),
            principal(SESSION_ID, "principal:middle")))
        claim = self.resolve()
        self.assertIsNone(claim["hops"])
        self.assertTrue(any("revoked" in defect for defect in claim["defects"]))

    def test_a_chain_that_never_reaches_the_root_is_a_defect(self) -> None:
        self.write(registry(principal(ROOT_ID, None),
                            principal(SESSION_ID, None), root=ROOT_ID))
        claim = self.resolve()
        self.assertIsNone(claim["hops"])
        self.assertTrue(any("does not reach the root" in d for d in claim["defects"]))

    def test_a_long_chain_terminates_instead_of_walking_forever(self) -> None:
        links = [principal(ROOT_ID, None)]
        previous = ROOT_ID
        for step in range(principals.MAX_CHAIN + 5):
            current = f"principal:link-{step}"
            links.append(principal(current, previous))
            previous = current
        links.append(principal(SESSION_ID, previous))
        self.write(registry(*links))
        claim = self.resolve()
        self.assertIsNone(claim["hops"])
        self.assertTrue(any("exceeds" in defect for defect in claim["defects"]))


if __name__ == "__main__":
    unittest.main()
