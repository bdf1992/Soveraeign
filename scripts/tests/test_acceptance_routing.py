"""Prove the acceptance docket both admits a sound routing and refuses a broken one.

Every case has a defeating counterpart (`AGENTS.md`, Testing and verification). A
checker that only ever sees the checked-in file proves nothing about what it would
catch, and this one exists precisely to catch a claim that `STATUS.yaml` already
answers something when it does not.
"""

from __future__ import annotations

from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_accept  # noqa: E402

STANDING = json.loads((ROOT / "contracts" / "decision-standing.json").read_text("utf-8"))
ROUTING = json.loads((ROOT / "contracts" / "acceptance-routing.json").read_text("utf-8"))


class CheckedInState(unittest.TestCase):
    """The repository as it stands passes its own gate."""

    def test_the_checked_in_routing_has_no_defect(self) -> None:
        self.assertEqual(sov_accept.check(), 0)

    def test_every_open_record_is_routed(self) -> None:
        """An open record nobody routed is one nobody can say whose it is."""
        rows, unknown = sov_accept.graded()
        self.assertEqual(unknown, [], "a status line is missing from the crosswalk")
        unrouted = [row["id"] for row in rows if not row["settled"] and not row["routing"]]
        self.assertEqual(unrouted, [])

    def test_the_crosswalk_covers_every_status_line_in_use(self) -> None:
        in_use = {record["status_line"] for record in sov_accept.records()}
        self.assertEqual(in_use - set(STANDING["crosswalk"]), set())

    def test_every_crosswalk_target_is_a_declared_standing(self) -> None:
        targets = set(STANDING["crosswalk"].values())
        self.assertEqual(targets - set(STANDING["standings"]), set())


class Defeats(unittest.TestCase):
    """Each declared check, given exactly the input it exists to refuse."""

    def setUp(self) -> None:
        self.routing = json.loads(json.dumps(ROUTING))
        self.original = sov_accept.ROUTING

    def tearDown(self) -> None:
        sov_accept.ROUTING = self.original

    def _check_with(self, routing: dict, tmp: Path) -> int:
        path = tmp / "routing.json"
        path.write_text(json.dumps(routing), encoding="utf-8")
        sov_accept.ROUTING = path
        return sov_accept.check()

    def _in_tmp(self, mutate) -> int:
        from tempfile import TemporaryDirectory
        mutate(self.routing["routing"])
        with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            return self._check_with(self.routing, Path(tmp))

    def test_a_status_key_that_is_not_in_status_yaml_fails(self) -> None:
        """The defect this checker caught in its own author's first draft."""
        def mutate(routing: dict) -> None:
            routing["0001"]["already_recorded_as"] = "no_such_field_exists_anywhere"
        self.assertEqual(self._in_tmp(mutate), 1)

    def test_routing_a_record_that_does_not_exist_fails(self) -> None:
        def mutate(routing: dict) -> None:
            routing["9999"] = {"title": "invented", "reaches_owner": False, "categories": [],
                               "reason": "none", "action_if_confirmed": "none"}
        self.assertEqual(self._in_tmp(mutate), 1)

    def test_reaching_the_owner_without_naming_a_category_fails(self) -> None:
        def mutate(routing: dict) -> None:
            routing["0039"]["categories"] = []
        self.assertEqual(self._in_tmp(mutate), 1)

    def test_naming_a_category_without_reaching_the_owner_fails(self) -> None:
        def mutate(routing: dict) -> None:
            routing["0038"]["categories"] = ["product_intent"]
        self.assertEqual(self._in_tmp(mutate), 1)

    def test_an_undeclared_owner_held_category_fails(self) -> None:
        def mutate(routing: dict) -> None:
            routing["0039"]["categories"] = ["vibes"]
        self.assertEqual(self._in_tmp(mutate), 1)

    def test_a_routing_entry_missing_its_reason_fails(self) -> None:
        """A routing with no reason is an assertion, and assertions are what this replaces."""
        def mutate(routing: dict) -> None:
            del routing["0020"]["reason"]
        self.assertEqual(self._in_tmp(mutate), 1)


class Routing(unittest.TestCase):
    """What the routing says, held against the rules it claims to apply."""

    def test_a_routing_entry_has_no_field_that_could_record_a_settlement(self) -> None:
        """decisions/0023 reserves acceptance to Bdo, so the file cannot express one.

        Structural rather than textual: an entry's reason may well mention that
        something was accepted, because saying so is the whole point of
        `already_recorded_as`. What must not exist is a field this file could
        write an acceptance into.
        """
        allowed = set(ROUTING["entry_keys"])
        forbidden = {"settled", "settled_by", "accepted", "accepted_by", "accepted_at",
                     "ratified", "ratified_by", "standing", "outcome", "owner_action"}
        self.assertEqual(allowed & forbidden, set())
        for identifier, entry in ROUTING["routing"].items():
            self.assertEqual(set(entry) - allowed, set(),
                             f"{identifier} carries a key outside the declared vocabulary")

    def test_a_record_reaching_the_owner_names_an_owner_held_category(self) -> None:
        declared = set(STANDING["owner_held_categories"])
        for identifier, entry in ROUTING["routing"].items():
            if entry["reaches_owner"]:
                self.assertTrue(set(entry["categories"]) <= declared, identifier)
                self.assertTrue(entry["categories"], identifier)


if __name__ == "__main__":
    unittest.main()
