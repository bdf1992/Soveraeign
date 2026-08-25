"""Execute the principal fixtures: schema validity, chain soundness, derived hops, orphans.

The schema owns field shape (including refusing a stored hop, ID-3). The
semantic guards here are the parts a schema cannot express (decisions/0048):
control chains resolve, avoid cycles and revoked links, and terminate at one
root; hop distance derives from the chain; lineage links resolve; every
observed actor id resolves to a registered principal (ID-1); and a verified
claim names a declared, Phase-I-admissible channel (ID-13). Passing
establishes ``BUILT`` for the contract only.
"""

from __future__ import annotations

from pathlib import Path
import json
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sovkernel.jsonschema import validate  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads((ROOT / "contracts" / "principal.schema.json").read_text("utf-8"))
FIXTURES = json.loads(
    (ROOT / "contracts" / "fixtures" / "principal.fixtures.json").read_text("utf-8"))


def chain_defects(registry: dict) -> list[str]:
    """One root, resolving un-revoked control chains, no cycles, lineage on record."""
    defects: list[str] = []
    principals = {item["principal_id"]: item for item in registry.get("principals", [])}
    declared_root = registry.get("root_principal")
    uncontrolled = [pid for pid, item in principals.items() if item.get("controller") is None]
    if uncontrolled != [declared_root]:
        defects.append(f"uncontrolled principals {uncontrolled} do not match the declared "
                       f"root {declared_root!r}")
    root = principals.get(declared_root) or {}
    if root.get("kind") != "HUMAN":
        defects.append(f"root principal {declared_root!r} is not HUMAN (hop-0 convention)")
    for pid, item in principals.items():
        lineage = (item.get("model") or {}).get("lineage")
        if lineage is not None and lineage not in principals:
            defects.append(f"{pid}: lineage names {lineage}, which is not on record")
        seen, controller = {pid}, item.get("controller")
        while controller is not None:
            upstream = principals.get(controller)
            if upstream is None:
                defects.append(f"{pid}: control chain names missing principal {controller}")
                break
            if controller in seen:
                defects.append(f"{pid}: control chain cycles at {controller}")
                break
            if item.get("revoked") is None and upstream.get("revoked") is not None:
                defects.append(f"{pid}: control chain passes through revoked {controller}")
                break
            seen.add(controller)
            controller = upstream.get("controller")
        else:
            if item.get("controller") is not None and declared_root not in seen:
                defects.append(f"{pid}: control chain does not reach the root")
    return defects


def derive_hops(registry: dict) -> dict[str, int | None]:
    """Hop distance from human interfacing: root is 0; each control edge adds one."""
    principals = {item["principal_id"]: item for item in registry.get("principals", [])}
    hops: dict[str, int | None] = {}
    for pid in principals:
        distance, current, seen = 0, pid, set()
        while True:
            item = principals.get(current)
            if item is None or current in seen:
                hops[pid] = None
                break
            if item.get("controller") is None:
                hops[pid] = distance if current == registry.get("root_principal") else None
                break
            seen.add(current)
            current, distance = item["controller"], distance + 1
    return hops


EXTERNAL_CHANNEL = "external"


def channel_defects(registry: dict) -> list[str]:
    """ID-13: a VERIFIED claim needs a declared channel, and Phase I refuses external ones."""
    defects: list[str] = []
    for item in registry.get("principals", []):
        pid = item["principal_id"]
        channel = item.get("verification_channel")
        verified = (item.get("claim") or {}).get("verification") == "VERIFIED"
        if verified and channel is None:
            defects.append(f"{pid}: VERIFIED with no declared channel")
        if channel is not None and channel.get("kind") == EXTERNAL_CHANNEL and verified:
            defects.append(f"{pid}: verified over an external channel while Phase I "
                           "refuses EXTERNAL_WORLD effects")
    return defects


def orphan_actor_defects(registry: dict, actor_ids: list[str]) -> list[str]:
    """ID-1: every observed actor id must resolve to a registered principal."""
    known = {item["principal_id"] for item in registry.get("principals", [])}
    return [f"actor {actor_id} resolves to no principal on record"
            for actor_id in actor_ids if actor_id not in known]


class PrincipalFixtures(unittest.TestCase):
    def test_every_fixture_matches_its_declared_expectation(self) -> None:
        for case in FIXTURES:
            with self.subTest(case=case["id"]):
                defects = validate(case["record"], SCHEMA)
                if case["expected_validity"] == "VALID":
                    self.assertEqual(defects, [], case["id"])
                else:
                    self.assertNotEqual(defects, [], case["id"])
                if "expected_chain_sound" in case:
                    chain = chain_defects(case["record"])
                    if case["expected_chain_sound"]:
                        self.assertEqual(chain, [], case["id"])
                    else:
                        self.assertNotEqual(chain, [], case["id"])

    def test_channels_match_their_declared_expectation(self) -> None:
        for case in FIXTURES:
            if "expected_channels_sound" not in case:
                continue
            with self.subTest(case=case["id"]):
                defects = channel_defects(case["record"])
                if case["expected_channels_sound"]:
                    self.assertEqual(defects, [], case["id"])
                else:
                    self.assertNotEqual(defects, [], case["id"])

    def test_hops_are_derived_not_stored(self) -> None:
        positive = FIXTURES[0]
        self.assertEqual(positive["id"], "PRINCIPAL-POS")
        self.assertEqual(derive_hops(positive["record"]), positive["expected_hops"])
        for item in positive["record"]["principals"]:
            self.assertNotIn("hop", item, "ID-3: hop distance must never be stored")

    def test_observed_actors_resolve_or_are_named(self) -> None:
        for case in FIXTURES:
            if "observed_actor_ids" not in case:
                continue
            with self.subTest(case=case["id"]):
                defects = orphan_actor_defects(case["record"], case["observed_actor_ids"])
                if case["polarity"] == "positive":
                    self.assertEqual(defects, [], case["id"])
                else:
                    self.assertNotEqual(defects, [], case["id"])

    def test_fixture_hygiene(self) -> None:
        ids = [case["id"] for case in FIXTURES]
        self.assertEqual(len(ids), len(set(ids)), "duplicate fixture id")
        self.assertEqual({case["polarity"] for case in FIXTURES}, {"positive", "defeating"})
        for case in FIXTURES:
            if case["polarity"] == "defeating":
                self.assertTrue(case.get("defeats"), case["id"])
        covered = " ".join(case.get("defeats", "") for case in FIXTURES)
        for requirement in ("ID-1", "ID-2", "ID-3", "ID-4", "ID-5", "ID-6", "ID-7", "ID-13"):
            self.assertIn(requirement, covered, f"{requirement} has no defeating case")


if __name__ == "__main__":
    unittest.main()
