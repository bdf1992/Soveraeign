"""Positive and defeating cases for the MCP gateway.

The gateway's claim is that a tool call is a governed crossing: a live session, a
live grant, a journalled event, and a receipt either way. These cases prove the
claim by defeating it - an ungranted call, a sessionless call, a call after the
session closes, and a manifest naming an operation nothing implements.

BUILT evidence only (`AGENTS.md`, Testing and verification: a test may establish
`BUILT`; it may not claim `WITNESSED` or `RATIFIED`).
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import io
import json
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1]))

from gateway import EndpointRefused, Gateway, UnbuiltEndpoint  # noqa: E402
from server import Server  # noqa: E402

ACTOR = "Bdo"
MODEL = "claude-opus-5"
MALLORY = "Mallory"
#: The node this gateway's console serves; a node grant is scoped to it.
NODE = "node:local"


class GatewayCase(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.gateway = Gateway(self.root / "state")

    def tearDown(self):
        self.gateway.close()
        self.tmp.cleanup()

    def open_session(self):
        return self.gateway.call("authority_open_session",
                                 {"participant": ACTOR, "model_identity": MODEL}, ACTOR)

    def hold(self, capability: str):
        self.gateway.call("authority_grant",
                          {"issuer": ACTOR, "actor": ACTOR, "capability": capability}, ACTOR)

    def source(self, name: str, content: bytes) -> Path:
        path = self.root / name
        path.write_bytes(content)
        return path


class SharedGatewayCase(unittest.TestCase):
    """One store for the whole class: these cases read, they do not mutate authority."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        cls.gateway = Gateway(cls.root / "state")

    @classmethod
    def tearDownClass(cls):
        cls.gateway.close()
        cls.tmp.cleanup()


class ExposedSurface(SharedGatewayCase):
    def test_the_tool_list_comes_from_the_manifest(self):
        names = {tool["name"] for tool in self.gateway.tools()}
        declared = {entry["tool"] for entry in self.gateway.manifest["endpoints"]}
        self.assertEqual(names, declared)

    def test_every_tool_carries_its_tier_in_the_description(self):
        for tool in self.gateway.tools():
            self.assertRegex(tool["description"], r"^\[(read|observe|act)\] ")

    def test_an_unexposed_operation_is_refused_by_name(self):
        """The defeating case: a real service method nobody declared is not a tool."""
        with self.assertRaises(EndpointRefused) as raised:
            self.gateway.call("asset_retract", {}, ACTOR)
        self.assertEqual(raised.exception.code, "UNKNOWN_OPERATION")

    def test_a_declared_endpoint_with_no_implementation_refuses_to_start(self):
        """A written-but-unbuilt operation must fail at startup, not at call time."""
        manifest = json.loads((Path(__file__).parents[1] / "manifest.json")
                              .read_text(encoding="utf-8"))
        manifest["endpoints"].append({
            "tool": "proofing_open_session", "tier": "act", "service": "proofing",
            "operation": "open_session", "capability": "operate:proof",
            "effect_class": "RECORD_LOCAL", "description": "chartered, not implemented",
            "arguments": {},
        })
        path = self.root / "unbuilt-manifest.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(UnbuiltEndpoint) as raised:
            Gateway(self.root / "other-state", manifest_path=path)
        self.assertIn("proofing_open_session", str(raised.exception))

    def _manifest(self) -> dict:
        return json.loads((Path(__file__).parents[1] / "manifest.json")
                          .read_text(encoding="utf-8"))

    def _start_from(self, manifest: dict, name: str) -> None:
        path = self.root / name
        path.write_text(json.dumps(manifest), encoding="utf-8")
        Gateway(self.root / f"state-{name}", manifest_path=path)

    def _withholding(self, tool: str) -> dict:
        """Move one served endpoint into withheld_endpoints, with a reason.

        The checked-in manifest withholds nothing since Bdo ruled record.read-entry an
        operator act (decisions/0052), so the withholding machinery has to be exercised
        against a manifest built here rather than against whatever happens to be withheld.
        """
        manifest = self._manifest()
        entry = next(e for e in manifest["endpoints"] if e["tool"] == tool)
        manifest["endpoints"] = [e for e in manifest["endpoints"] if e["tool"] != tool]
        entry["withheld_because"] = ("withheld by this case to prove the refusal, and for "
                                     "no reason that holds outside it")
        manifest["withheld_endpoints"] = [entry]
        return manifest

    def test_nothing_is_currently_withheld(self):
        """The positive case, and the record of a ruling.

        record_entries was withheld on 2026-08-24 as the reversible default when the
        capability build fired BACK_OFFICE_EXPOSED. Bdo ruled the same day that reading
        authorized operational history is an operator act and the office table was the
        wrong side, so the binding serves it again.
        """
        self.assertEqual(self.gateway.withheld, {})
        self.assertIn("record_entries", {tool["name"] for tool in self.gateway.tools()})

    def test_an_implementation_that_is_neither_declared_nor_withheld_refuses_to_start(self):
        """Withholding is the only admitted reason for a built tool to be unserved."""
        manifest = self._manifest()
        manifest["endpoints"] = [e for e in manifest["endpoints"]
                                 if e["tool"] != "record_entries"]
        with self.assertRaises(UnbuiltEndpoint) as raised:
            self._start_from(manifest, "unwithheld-manifest.json")
        self.assertIn("record_entries", str(raised.exception))

    def test_a_withheld_endpoint_with_no_reason_refuses_to_start(self):
        """A capability may not quietly vanish; withholding states why."""
        manifest = self._withholding("record_entries")
        manifest["withheld_endpoints"][0].pop("withheld_because")
        with self.assertRaises(UnbuiltEndpoint) as raised:
            self._start_from(manifest, "unreasoned-manifest.json")
        self.assertIn("without a stated reason", str(raised.exception))

    def test_an_endpoint_both_declared_and_withheld_refuses_to_start(self):
        """One tool, one answer: served or not, never recorded as both."""
        manifest = self._manifest()
        manifest["withheld_endpoints"].append(dict(manifest["endpoints"][0],
                                                   withheld_because="x" * 50))
        with self.assertRaises(UnbuiltEndpoint) as raised:
            self._start_from(manifest, "contradictory-manifest.json")
        self.assertIn("both declared and withheld", str(raised.exception))

    def test_a_withheld_tool_is_not_offered(self):
        """The withheld endpoint must be absent from the surface a client sees."""
        manifest = self._withholding("record_entries")
        path = self.root / "withholding-manifest.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        gateway = Gateway(self.root / "state-withholding", manifest_path=path)
        try:
            self.assertNotIn("record_entries", {tool["name"] for tool in gateway.tools()})
            self.assertIn("record_entries", gateway.withheld)
        finally:
            gateway.close()


class GovernedCrossing(GatewayCase):
    def test_a_read_needs_no_session_and_no_grant(self):
        self.assertEqual(self.gateway.call("asset_search", {"query": "anything"}, ACTOR), [])

    def test_reading_the_journal_without_the_declared_grant_is_refused(self):
        """The defeating case for `record_entries`, which checked nothing until 2026-08-25.

        The read tier returned before the precheck ran, so this endpoint declared
        `read:journal`, realized `record.read-entry`, and handed any caller the whole
        journal - thread titles, post ids, actor ids, content addresses, and every
        grant record the other endpoints' guards are read out of. A guard that can be
        read around is not a guard. `decisions/0052` already said this read costs the
        grant; nothing here decides a policy that was not already decided.
        """
        with self.assertRaises(EndpointRefused) as raised:
            self.gateway.call("record_entries", {}, MALLORY)
        self.assertEqual(raised.exception.code, "GRANT_NOT_HELD")

    def test_reading_the_journal_with_the_declared_grant_is_admitted(self):
        """The positive half: the grant the office table names is enough, and no more."""
        self.gateway.console.grant(ACTOR, "read:journal", NODE)
        self.assertIsInstance(self.gateway.call("record_entries", {}, ACTOR), list)
        with self.assertRaises(EndpointRefused):
            self.gateway.call("record_entries", {}, MALLORY)

    def test_a_journal_read_grant_is_not_bought_from_the_asset_store(self):
        """Two authority stores, and the journal is not the asset service's to sell.

        `authority_grant` issues in the Asset Service's store. The console journal is
        where this node records who holds what, so a grant bought there must not open
        a read of it.
        """
        self.open_session()
        self.hold("read:journal")
        with self.assertRaises(EndpointRefused) as raised:
            self.gateway.call("record_entries", {}, ACTOR)
        self.assertEqual(raised.exception.code, "GRANT_NOT_HELD")

    def test_an_act_without_a_session_is_refused(self):
        """The defeating case: no live session, no act."""
        with self.assertRaises(EndpointRefused) as raised:
            self.gateway.call("asset_ingest",
                              {"path": "x", "label": "x", "actor": ACTOR}, ACTOR)
        self.assertEqual(raised.exception.code, "SESSION_NOT_LIVE")

    def test_an_act_without_a_grant_is_refused(self):
        """The defeating case: a session is not authority."""
        self.open_session()
        with self.assertRaises(EndpointRefused) as raised:
            self.gateway.call("asset_ingest",
                              {"path": "x", "label": "x", "actor": ACTOR}, ACTOR)
        self.assertEqual(raised.exception.code, "GRANT_NOT_HELD")

    def test_a_granted_act_commits_and_is_journalled(self):
        self.open_session()
        self.hold("operate:ingest")
        source = self.source("hero.txt", b"ORIGINAL\n")
        result = self.gateway.call(
            "asset_ingest", {"path": str(source), "label": "Hero", "actor": ACTOR}, ACTOR)
        self.assertIn("asset_id", result)
        kinds = [entry["kind"] for entry in self.gateway.record.entries()]
        self.assertIn("EVENT", kinds)
        self.assertIn("RECEIPT", kinds)

    def test_a_refusal_is_journalled_too(self):
        """A governed no leaves the same trace a yes does."""
        self.open_session()
        with self.assertRaises(EndpointRefused):
            self.gateway.call("asset_ingest",
                              {"path": "x", "label": "x", "actor": ACTOR}, ACTOR)
        outcomes = [entry["payload"].get("outcome")
                    for entry in self.gateway.record.entries()
                    if entry["kind"] == "RECEIPT"]
        self.assertIn("REFUSED", outcomes)

    def test_the_journal_records_argument_shapes_not_payloads(self):
        """Context hygiene: the journal holds addresses and shapes, never whole values."""
        self.open_session()
        self.hold("operate:ingest")
        source = self.source("hero.txt", b"ORIGINAL\n")
        self.gateway.call("asset_ingest",
                          {"path": str(source), "label": "Hero", "actor": ACTOR}, ACTOR)
        events = [entry["payload"] for entry in self.gateway.record.entries()
                  if entry["kind"] == "EVENT"]
        ingest = [event for event in events if event["tool"] == "asset_ingest"][0]
        self.assertNotIn("Hero", json.dumps(ingest["arguments"]))
        self.assertTrue(ingest["arguments"]["label"].startswith("<str:"))

    def test_closing_the_session_withdraws_the_grant_it_carried(self):
        """The defeating case that makes session-stop meaningful."""
        session = self.open_session()["session_id"]
        self.hold("operate:ingest")
        source = self.source("hero.txt", b"ORIGINAL\n")
        self.gateway.call("asset_ingest",
                          {"path": str(source), "label": "Hero", "actor": ACTOR}, ACTOR)
        self.gateway.asset.close_session(session, ACTOR)
        with self.assertRaises(EndpointRefused) as raised:
            self.gateway.call("asset_ingest",
                              {"path": str(source), "label": "Again", "actor": ACTOR}, ACTOR)
        self.assertEqual(raised.exception.code, "SESSION_NOT_LIVE")


class ProtocolLoop(SharedGatewayCase):
    """The stdio JSON-RPC surface, driven over in-memory streams."""

    def exchange(self, requests: list[dict]) -> list[dict]:
        lines = "".join(json.dumps(request) + "\n" for request in requests)
        out = io.StringIO()
        Server(self.gateway, ACTOR, io.StringIO(lines), out).serve()
        return [json.loads(line) for line in out.getvalue().splitlines()]

    def test_initialize_announces_tools(self):
        responses = self.exchange([{"jsonrpc": "2.0", "id": 1, "method": "initialize"}])
        self.assertEqual(responses[0]["result"]["capabilities"], {"tools": {}})
        self.assertEqual(responses[0]["result"]["serverInfo"]["name"], "soveraeign")

    def test_tools_list_returns_the_manifest_surface(self):
        responses = self.exchange([{"jsonrpc": "2.0", "id": 2, "method": "tools/list"}])
        self.assertEqual(len(responses[0]["result"]["tools"]),
                         len(self.gateway.manifest["endpoints"]))

    def test_a_notification_gets_no_response(self):
        self.assertEqual(self.exchange([{"jsonrpc": "2.0", "method": "notifications/initialized"}]),
                         [])

    def test_a_refusal_returns_a_tool_error_not_a_transport_error(self):
        """The caller asked a legal question; the answer is a governed no."""
        responses = self.exchange([{"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                                    "params": {"name": "asset_ingest",
                                               "arguments": {"path": "x", "label": "x",
                                                             "actor": ACTOR}}}])
        self.assertNotIn("error", responses[0])
        self.assertTrue(responses[0]["result"]["isError"])
        self.assertIn("SESSION_NOT_LIVE", responses[0]["result"]["content"][0]["text"])

    def test_an_unknown_method_is_a_transport_error(self):
        responses = self.exchange([{"jsonrpc": "2.0", "id": 4, "method": "resources/list"}])
        self.assertEqual(responses[0]["error"]["code"], -32601)

    def test_malformed_input_does_not_kill_the_loop(self):
        out = io.StringIO()
        Server(self.gateway, ACTOR,
               io.StringIO('not json\n{"jsonrpc": "2.0", "id": 5, "method": "ping"}\n'),
               out).serve()
        responses = [json.loads(line) for line in out.getvalue().splitlines()]
        self.assertEqual(responses[0]["error"]["code"], -32700)
        self.assertEqual(responses[1]["result"], {})


if __name__ == "__main__":
    unittest.main()
