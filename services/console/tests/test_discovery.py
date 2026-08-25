"""Prove discovery answers from the projection, and refuse the ways it could stop.

`GROUND-006` says what may be asked of a node is discoverable from the artifact alone.
The failure this guards is not "no answer" - it is a confident answer that is no longer
true, which is what a hand-maintained list beside the capability map produces the first
time an operation moves. Every case here drives the answer against the map rather than
against a fixture written to agree with it.

The second thing under test is honesty about authority. "What exists on this node" and
"what this participant may currently do" are related readings and not the same reading,
and the second one has edges: this service reads one authority store and cannot speak for
another's. Those edges are reported per row rather than smoothed into a number.

Passing establishes `BUILT`. It witnesses nothing. `bindings/mcp/observe_journey_02.py`
walks the same path through a real binding and records what came back, because a test
proving the code does what it says is not evidence that a participant can get an answer.

`python scripts/sov_mutate.py run --target
services/console/src/soveraeign_console_service/discovery.py` is the adversarial pass over
this file: 31 mutants, 30 killed. The survivor is `return None` mutated to `return None`.
It is not part of `scripts/verify.py` and has to be run deliberately.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import copy
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "services" / "console" / "src"))
sys.path.insert(0, str(ROOT / "services" / "record" / "src"))

from soveraeign_console_service import discovery  # noqa: E402
from soveraeign_console_service.authority import ENFORCED_AUTHORITY  # noqa: E402
from soveraeign_console_service.core import ConsoleService  # noqa: E402
from soveraeign_console_service.refusals import StaleCapabilityMap  # noqa: E402
from soveraeign_record_service import RecordService  # noqa: E402

MAP = json.loads((ROOT / "contracts" / "fixtures"
                  / "capability-map.reference.json").read_text("utf-8"))
OFFICES = json.loads((ROOT / "contracts"
                      / "capability-offices.json").read_text("utf-8"))["assignments"]

#: Capabilities whose declared authority name differs from the one this service checks.
#: Empty since 2026-08-24: `console.archive-thread` was the last one, and Bdo ruled that
#: archiving THE thread needs its own grant, so the code moved to the declared name
#: (`decisions/0054`). Kept as a set rather than deleted so a new divergence fails here
#: instead of quietly making a capability's authority unanswerable.
KNOWN_DIVERGENCE: set[str] = set()


def _rows(answer: dict) -> dict[str, dict]:
    return {row["capability_id"]: row for row in answer["operations"]}


class FromTheProjectionTest(unittest.TestCase):
    """The answer is the map, read through, and not a list that resembles it."""

    def setUp(self) -> None:
        self.answer = discovery.operations(MAP, enforced=ENFORCED_AUTHORITY)

    def test_every_declared_capability_is_answered_for(self) -> None:
        self.assertEqual(len(self.answer["operations"]), len(MAP["capabilities"]))
        self.assertEqual(self.answer["counts"]["declared"], len(MAP["capabilities"]))

    def test_the_answer_names_the_revision_it_was_read_from(self) -> None:
        """Without this a reader cannot tell whether two answers described one node."""
        self.assertEqual(self.answer["capability_revision"], MAP["input_state_digest"])

    def test_reachability_is_the_projections_and_not_a_second_opinion(self) -> None:
        rows = _rows(self.answer)
        for capability in MAP["capabilities"]:
            expected = any(endpoint["activation"] == "ACTIVE"
                           for endpoint in capability["endpoints"])
            with self.subTest(capability=capability["capability_id"]):
                self.assertEqual(rows[capability["capability_id"]]["reachable"], expected)

    def test_a_capability_added_to_the_map_appears_without_touching_this_code(self) -> None:
        """The whole reason not to keep a list here."""
        wider = copy.deepcopy(MAP)
        invented = copy.deepcopy(wider["capabilities"][0])
        invented["capability_id"] = "invented.operation"
        invented["service_id"] = "invented"
        invented["operation"] = "operation"
        wider["capabilities"].append(invented)
        answer = discovery.operations(wider, enforced=ENFORCED_AUTHORITY)
        self.assertIn("invented.operation", _rows(answer))

    def test_a_row_carries_what_a_fresh_participant_has_to_know(self) -> None:
        """Identity, reachability, authority, effect, what it needs, how it refuses."""
        row = _rows(self.answer)["console.post"]
        self.assertEqual(row["capability_id"], "console.post")
        self.assertEqual(row["logical_endpoint"], "sov://console/post")
        self.assertTrue(row["endpoints"])
        self.assertTrue(row["authority"]["required"])
        self.assertEqual(row["effect_class"], "RECORD_LOCAL")
        self.assertIn("session_live", row["preconditions"])
        self.assertIn("SESSION_NOT_LIVE", row["refusals"])
        self.assertEqual(row["commits"], "COMMITTED")

    def test_the_answer_says_it_is_not_authoritative(self) -> None:
        self.assertFalse(self.answer["authoritative"])
        self.assertTrue(self.answer["omissions"])

    def test_the_counts_are_the_rows_and_not_a_number_beside_them(self) -> None:
        """A count nothing checks is the hand-maintained list again, one field down.

        Mutation scoring caught this on 2026-08-24: the reachable tally could be doubled
        and every case still passed, so a participant could have been told the node
        reaches twice what it reaches.
        """
        rows = self.answer["operations"]
        self.assertEqual(self.answer["counts"]["reachable"],
                         sum(1 for row in rows if row["reachable"]))
        self.assertEqual(self.answer["counts"]["declared"], len(rows))
        self.assertEqual(sum(self.answer["counts"]["authority"].values()), len(rows))
        self.assertLess(self.answer["counts"]["reachable"],
                        self.answer["counts"]["declared"])


class AuthorityHonestyTest(unittest.TestCase):
    """Two readings, and the second one says where it stops."""

    def test_naming_no_operator_reads_no_grants(self) -> None:
        answer = discovery.operations(MAP, enforced=ENFORCED_AUTHORITY)
        readings = {row["authority"]["reading"] for row in answer["operations"]}
        self.assertNotIn(discovery.HELD, readings)
        self.assertNotIn(discovery.NOT_HELD, readings)

    def test_a_live_grant_reads_held_and_names_its_scope(self) -> None:
        answer = discovery.operations(
            MAP, enforced=ENFORCED_AUTHORITY, operator_id="sov",
            grants=[{"capability": "post:message", "scope": "thread_1"}])
        authority = _rows(answer)["console.post"]["authority"]
        self.assertEqual(authority["reading"], discovery.HELD)
        self.assertEqual(authority["scopes"], ["thread_1"])

    def test_no_grant_reads_not_held_rather_than_unknown(self) -> None:
        answer = discovery.operations(MAP, enforced=ENFORCED_AUTHORITY,
                                      operator_id="sov", grants=[])
        self.assertEqual(_rows(answer)["console.post"]["authority"]["reading"],
                         discovery.NOT_HELD)

    def test_another_services_capability_is_never_guessed_at(self) -> None:
        """This console reads one authority store and will not speak for another's."""
        answer = discovery.operations(MAP, enforced=ENFORCED_AUTHORITY,
                                      operator_id="sov", grants=[])
        authority = _rows(answer)["asset.ingest-asset"]["authority"]
        self.assertEqual(authority["reading"], discovery.NOT_KNOWN_HERE)
        self.assertIn("own authority store", authority["because"])

    def test_a_declared_name_the_service_does_not_check_is_undeterminable(self) -> None:
        """A grant cannot be matched against a name the check does not use.

        Driven from an invented divergence rather than a real one. The node has none
        today, and the reading has to keep working for the day it grows one.
        """
        diverging = dict(ENFORCED_AUTHORITY)
        diverging["console.post"] = "post"
        answer = discovery.operations(MAP, enforced=diverging,
                                      operator_id="sov", grants=[])
        authority = _rows(answer)["console.post"]["authority"]
        self.assertEqual(authority["reading"], discovery.UNDETERMINABLE)
        self.assertEqual(authority["enforced"], "post")
        self.assertEqual(authority["required"], "post:message")

    def test_no_divergence_appears_unnoticed(self) -> None:
        """Every enforced name equals the declared one, except where a case names it."""
        diverging = {capability_id for capability_id, enforced
                     in ENFORCED_AUTHORITY.items()
                     if OFFICES[capability_id]["required_authority"] != enforced}
        self.assertEqual(diverging, KNOWN_DIVERGENCE)

    def test_archiving_the_thread_is_answered_for_rather_than_undeterminable(self) -> None:
        """Bdo's 2026-08-24 ruling, read back out of the discovery surface.

        Before it, this row read `UNDETERMINABLE` and a participant could not learn what
        archiving costs. It now names a grant that exists and can be asked for.
        """
        answer = discovery.operations(MAP, enforced=ENFORCED_AUTHORITY,
                                      operator_id="sov", grants=[])
        authority = _rows(answer)["console.archive-thread"]["authority"]
        self.assertEqual(authority["required"], "archive:thread")
        self.assertEqual(authority["reading"], discovery.NOT_HELD)
        self.assertNotEqual(authority["required"],
                            OFFICES["console.open-thread"]["required_authority"])

    def test_a_built_operation_that_checks_nothing_says_so(self) -> None:
        """The reading this surface was getting wrong about itself.

        `console.discover-operations` is BUILT, declares `read:session` and checks
        nothing. Until 2026-08-24 the row read `NOT_KNOWN_HERE ... because it is not
        built`, which was false twice over: it is built, and the reason a grant does not
        decide it is that no check exists, not that nobody could answer.
        """
        answer = discovery.operations(MAP, enforced=ENFORCED_AUTHORITY,
                                      operator_id="sov", grants=[])
        authority = _rows(answer)["console.discover-operations"]["authority"]
        self.assertEqual(authority["reading"], discovery.NOT_ENFORCED)
        self.assertEqual(authority["required"], "read:session")
        self.assertIn("any caller is admitted", authority["because"])

    def test_holding_a_grant_does_not_change_an_unenforced_reading(self) -> None:
        """`NOT_ENFORCED` is about the operation, not about the participant."""
        answer = discovery.operations(
            MAP, enforced=ENFORCED_AUTHORITY, operator_id="sov",
            grants=[{"capability": "read:session", "scope": "*"}])
        self.assertEqual(
            _rows(answer)["console.discover-operations"]["authority"]["reading"],
            discovery.NOT_ENFORCED)

    def test_an_unbuilt_operation_is_not_reported_as_unenforced(self) -> None:
        """Nothing to enforce yet is a different fact from built and enforcing nothing."""
        answer = discovery.operations(MAP, enforced=ENFORCED_AUTHORITY,
                                      operator_id="sov", grants=[])
        row = _rows(answer)["console.acknowledge-notification"]
        self.assertNotEqual(row["standing"], "BUILT")
        self.assertEqual(row["authority"]["reading"], discovery.NOT_KNOWN_HERE)
        self.assertIn("no implementation", row["authority"]["because"])

    def test_every_built_console_capability_is_either_checked_or_named_unenforced(self) -> None:
        """The count is the finding: no built operation gets a silent pass.

        This is a report, not a policy. Nine built console operations check no
        authority, `console.grant` and `console.revoke` among them. Narrowing that is
        Bdo's call the way `console.archive-thread` was; what this asserts is that the
        surface says so out loud rather than reporting them as unanswerable.
        """
        answer = discovery.operations(MAP, enforced=ENFORCED_AUTHORITY,
                                      operator_id="sov", grants=[])
        unenforced = {row["capability_id"] for row in answer["operations"]
                      if row["authority"]["reading"] == discovery.NOT_ENFORCED}
        built = {row["capability_id"] for row in answer["operations"]
                 if row["service_id"] == "console" and row["standing"] == "BUILT"}
        self.assertEqual(unenforced | set(ENFORCED_AUTHORITY), built)
        self.assertIn("console.grant", unenforced)
        self.assertIn("console.revoke", unenforced)
        self.assertIn("check none", " ".join(answer["omissions"]))

    def test_the_omissions_count_what_could_not_be_determined(self) -> None:
        answer = discovery.operations(MAP, enforced=ENFORCED_AUTHORITY,
                                      operator_id="sov", grants=[])
        joined = " ".join(answer["omissions"])
        self.assertIn("authority store this service does not read", joined)

    def test_an_undeterminable_capability_is_counted_in_the_omissions(self) -> None:
        diverging = dict(ENFORCED_AUTHORITY)
        diverging["console.post"] = "post"
        answer = discovery.operations(MAP, enforced=diverging,
                                      operator_id="sov", grants=[])
        self.assertIn("declare one authority name and enforce another",
                      " ".join(answer["omissions"]))

    def test_available_and_permitted_are_named_as_different_readings(self) -> None:
        answer = discovery.operations(MAP, enforced=ENFORCED_AUTHORITY)
        self.assertEqual(answer["readings"]["available"], discovery.AVAILABLE)
        self.assertEqual(answer["readings"]["permitted"], discovery.PERMITTED)
        self.assertNotEqual(discovery.AVAILABLE, discovery.PERMITTED)


class FreshnessTest(unittest.TestCase):
    """`capability_map_fresh` is a declared precondition, so it is answered honestly."""

    def test_a_map_the_caller_established_is_stale_is_refused(self) -> None:
        with self.assertRaises(StaleCapabilityMap) as raised:
            discovery.operations(MAP, enforced=ENFORCED_AUTHORITY, fresh=False)
        self.assertEqual(raised.exception.reason_code, "MISSING_PRECONDITION")

    def test_unverified_is_reported_as_unverified_and_not_as_fresh(self) -> None:
        answer = discovery.operations(MAP, enforced=ENFORCED_AUTHORITY)
        self.assertIsNone(answer["freshness"]["verified"])
        self.assertIn("nobody checked", answer["freshness"]["note"])

    def test_a_verified_map_says_so(self) -> None:
        answer = discovery.operations(MAP, enforced=ENFORCED_AUTHORITY, fresh=True)
        self.assertTrue(answer["freshness"]["verified"])


class EntryPointTest(unittest.TestCase):
    """`discover` against a real service, not `operations` against a dict.

    Every case above drives `operations`, which left `discover` - the function the CLI
    and the MCP binding actually call - asserted by nothing. Mutation scoring found it on
    2026-08-24: `discover` could return None, or read grants for exactly the operators it
    should not, and the suite stayed green.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = TemporaryDirectory(ignore_cleanup_errors=True)
        root = Path(cls._tmp.name) / "console"
        cls.record = RecordService(root / "journal")
        cls.console = ConsoleService(cls.record, root, "node:test")
        cls.console.grant("Bdo", "open:channel", "governance")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.record.close()
        cls._tmp.cleanup()

    def test_it_returns_an_answer(self) -> None:
        answer = discovery.discover(self.console, MAP)
        self.assertEqual(answer["counts"]["declared"], len(MAP["capabilities"]))

    def test_naming_an_operator_reads_that_operators_grants(self) -> None:
        answer = discovery.discover(self.console, MAP, operator_id="Bdo")
        self.assertEqual(answer["operator_id"], "Bdo")
        self.assertEqual(_rows(answer)["console.open-channel"]["authority"]["reading"],
                         discovery.HELD)

    def test_naming_no_operator_reads_no_grants_at_all(self) -> None:
        """The narrower answer, and the one a fresh participant gets."""
        answer = discovery.discover(self.console, MAP)
        self.assertIsNone(answer["operator_id"])
        readings = {row["authority"]["reading"] for row in answer["operations"]}
        self.assertNotIn(discovery.HELD, readings)
        self.assertNotIn(discovery.NOT_HELD, readings)

    def test_an_operator_holding_nothing_is_not_the_same_as_no_operator(self) -> None:
        """`NOT_HELD` is an answer; `NOT_KNOWN_HERE` is a refusal to guess."""
        held = _rows(discovery.discover(self.console, MAP, operator_id="nobody"))
        unnamed = _rows(discovery.discover(self.console, MAP))
        self.assertEqual(held["console.open-channel"]["authority"]["reading"],
                         discovery.NOT_HELD)
        self.assertEqual(unnamed["console.open-channel"]["authority"]["reading"],
                         discovery.NOT_KNOWN_HERE)

    def test_a_stale_map_is_refused_through_the_entry_point_too(self) -> None:
        with self.assertRaises(StaleCapabilityMap):
            discovery.discover(self.console, MAP, operator_id="Bdo", fresh=False)


class RecordedObservationTest(unittest.TestCase):
    """The observation the binding walk produced, checked against the code that made it."""

    OBSERVATION = json.loads((ROOT / "bindings" / "mcp" / "observations"
                              / "journey-02-discovery.json").read_text("utf-8"))

    def test_the_walk_left_two_journal_entries(self) -> None:
        """An EVENT before the attempt and a RECEIPT after it. GROUND-007."""
        kinds = [entry["kind"] for entry in self.OBSERVATION["journal"]]
        self.assertEqual(kinds, ["EVENT", "RECEIPT"])

    def test_the_walk_carried_no_session_and_no_grant(self) -> None:
        """A participant holding nothing still gets an answer, which is the point."""
        self.assertIsNone(self.OBSERVATION["participant"]["session"])
        self.assertEqual(self.OBSERVATION["participant"]["grants_held"], 0)

    def test_the_observation_says_what_it_does_not_establish(self) -> None:
        """It was taken by calling the gateway, so it cannot settle the gateway."""
        joined = " ".join(self.OBSERVATION["what_this_does_not_establish"])
        self.assertIn("a second endpoint, not a second observer", joined)
        self.assertIn("GROUND-010", joined)

    def test_the_observation_pins_the_revision_it_read(self) -> None:
        self.assertTrue(self.OBSERVATION["capability_revision"])


if __name__ == "__main__":
    unittest.main()
