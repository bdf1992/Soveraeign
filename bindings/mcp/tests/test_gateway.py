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
import atexit
import copy
import functools
import inspect
import io
import json
import shutil
import sqlite3
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1]))

from gateway import EndpointRefused, Gateway, UnbuiltEndpoint  # noqa: E402
from manifest_gate import (  # noqa: E402
    Principal,
    audit_handlers,
    validate,
)
from server import Server  # noqa: E402

ACTOR = "Bdo"
MODEL = "claude-opus-5"
MALLORY = "Mallory"
#: The node this gateway's console serves; a node grant is scoped to it.
NODE = "node:local"


#: An empty store with its three schemas already on disk, built once for the module.
#:
#: A `Gateway` stands up an Asset Service, a Record Service and a Console Service,
#: each creating SQLite schema, and every case below wants a store nothing else has
#: touched. Building one per test costs 83 ms here and far more on a two-core runner
#: doing it under contention; copying this template costs 6.5 ms. `scripts/verify.py`
#: runs 39 checks concurrently, so what a check spends is not its own wall time - it
#: is taken from every other check in the pool, and the slowest one sets the gate.
_TEMPLATE: dict[str, Path] = {}


def _template() -> Path:
    """The prepared store, created on first use and removed when the process exits."""
    if not _TEMPLATE:
        holder = TemporaryDirectory()
        atexit.register(holder.cleanup)
        state = Path(holder.name) / "state"
        Gateway(state).close()
        _TEMPLATE["state"] = state
    return _TEMPLATE["state"]


def _fresh_store(root: Path) -> Path:
    """A private copy of the prepared store, isolated from every other case."""
    state = root / "state"
    shutil.copytree(_template(), state)
    return state


class GatewayCase(unittest.TestCase):
    """A private store per test, because these cases mutate authority."""

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.gateway = Gateway(_fresh_store(self.root))

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
        cls.gateway = Gateway(_fresh_store(cls.root))

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

    def test_a_refused_construction_closes_the_stores_it_opened(self):
        """Asserted on the connections, not on whether a directory can be deleted.

        `validate` runs before any store opens; `audit_handlers` cannot, because it
        reads signatures of handlers already bound to live services. So this refusal
        happens with two SQLite stores open - the asset store and the record journal,
        the console keeping no store of its own - and `Gateway.__init__` closes them
        before re-raising.

        The only case for that used to be an unlink in `tearDownClass`, which fails on
        Windows and succeeds on POSIX - so on the Linux runner that actually gates this
        work, removing the `close()` regressed nothing visible. Using a closed sqlite3
        connection raises on every host, so that is what this reads.
        """
        captured: dict[str, Gateway] = {}
        original = Gateway._bind

        def capturing(gateway):
            captured["gateway"] = gateway
            return original(gateway)

        manifest = self._manifest()
        entry = next(e for e in manifest["endpoints"] if e["tool"] == "asset_ingest")
        entry["arguments"]["label"].pop("principal")

        Gateway._bind = capturing
        try:
            with self.assertRaises(UnbuiltEndpoint):
                self._start_from(manifest, "closes-its-stores.json")
        finally:
            Gateway._bind = original

        refused = captured["gateway"]
        for label, call in (("record", refused.record.entries),
                            ("asset", lambda: refused.asset.search("anything"))):
            with self.subTest(label):
                with self.assertRaises(sqlite3.ProgrammingError) as still_open:
                    call()
                self.assertIn("closed database", str(still_open.exception))

    def test_the_audit_runs_at_construction_not_only_in_a_test(self):
        """That the rule is applied, which is a different claim from the rule existing.

        Deleting the `audit_handlers` call from `Gateway.__init__` left every case
        green, because the cases called the audit directly. A rule graded but not
        wired is the same defect one layer up. This manifest passes `validate` and
        fails the audit, so only construction can refuse it.
        """
        manifest = self._manifest()
        entry = next(e for e in manifest["endpoints"] if e["tool"] == "asset_ingest")
        entry["arguments"]["label"].pop("principal")
        with self.assertRaises(UnbuiltEndpoint) as raised:
            self._start_from(manifest, "unaudited-manifest.json")
        self.assertIn("without saying whether it is a principal", str(raised.exception))

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
        self.gateway.console.grant(ACTOR, "read:journal", NODE, ACTOR)
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

    def test_a_caller_cannot_name_a_different_principal(self):
        """The guard this change added, and the three siblings that never had it.

        `server.py` hands `params["arguments"]` to the dispatcher with no schema
        validation, so a name in the arguments genuinely arrives from the wire. Every
        handler that takes a principal now has it overwritten with the authenticated
        caller. Removing `caller_argument` from the manifest, or inverting the merge
        in `gateway.py` so the argument wins, must turn this red on both halves.
        """
        # Precondition, stated because it decides what this case proves: the asset
        # store must already have a root. `AssetService.Authority` records the first
        # issuer against an empty store as that store's root, so against a *fresh*
        # store an ungranted caller still grants itself and ingests - the issuer
        # binding works throughout and the grant records issuer=mallory, but the
        # bootstrap admits it. That is the Asset Service's open question, documented
        # at services/asset/src/soveraeign_asset_service/authority.py, and not what
        # this case measures. `hold` here is what makes Bdo that root.
        self.open_session()
        self.hold("operate:ingest")
        self.assertIsNotNone(self.gateway.asset.authority.root_issuer(),
                             "this case presupposes a bootstrapped asset store")
        source = self.source("hero.txt", b"payload")

        # console_operations: naming Bdo must not read Bdo's holdings. Ungranted
        # Mallory is refused because the principal checked became Mallory; if the
        # argument won she would have been admitted on Bdo's read:session.
        self.gateway.console.grant(ACTOR, "read:session", ACTOR, ACTOR)
        with self.assertRaises(Exception) as named:
            self.gateway.call("console_operations", {"operator_id": ACTOR}, MALLORY)
        self.assertIn("read:session", str(named.exception))
        # Holding her own, she gets her own reading and not the one she asked for.
        self.gateway.console.grant(MALLORY, "read:session", MALLORY, ACTOR)
        answer = self.gateway.call("console_operations", {"operator_id": ACTOR}, MALLORY)
        self.assertEqual(answer["operator_id"], MALLORY)

        # authority_grant: the escalation. Ungranted Mallory asks for a grant in the
        # root seat's name; the issuer checked is Mallory, who may issue nothing.
        with self.assertRaises(Exception) as raised:
            self.gateway.call("authority_grant",
                              {"issuer": ACTOR, "actor": MALLORY,
                               "capability": "operate:ingest"}, MALLORY)
        self.assertNotIsInstance(raised.exception, AssertionError)
        self.assertFalse(
            self.gateway.asset.authority.authorized(MALLORY, "operate:ingest", "*"),
            "Mallory took a grant in Bdo's name")

        # asset_ingest: naming Bdo must not spend Bdo's grant.
        with self.assertRaises(EndpointRefused) as refused:
            self.gateway.call("asset_ingest",
                              {"path": str(source), "label": "Hero", "actor": ACTOR},
                              MALLORY)
        self.assertEqual(refused.exception.code, "GRANT_NOT_HELD")

        # authority_open_session: the session opens for the caller, not the name.
        opened = self.gateway.call(
            "authority_open_session",
            {"participant": ACTOR, "model_identity": MODEL}, MALLORY)
        self.assertEqual(opened["participant"], MALLORY)

    def test_a_principal_argument_is_not_a_declared_input(self):
        """A caller must not be told to send what the dispatcher overwrites.

        Two rules together: the schema does not offer the field, and the manifest
        gate refuses a manifest that declares it both ways.
        """
        for tool, name in (("authority_grant", "issuer"), ("asset_ingest", "actor"),
                           ("authority_open_session", "participant"),
                           ("console_operations", "operator_id")):
            with self.subTest(tool):
                entry = self.gateway.endpoints[tool]
                self.assertEqual(entry["caller_argument"], name)
                self.assertNotIn(name, entry.get("arguments", {}))
                schema = next(t for t in self.gateway.tools() if t["name"] == tool)
                self.assertNotIn(name, schema["inputSchema"]["properties"])

        # Against the real manifest, not a one-entry dict. A fabricated tool name is
        # refused fifteen lines earlier for having no implementation, so the case that
        # named this refusal never reached it: deleting the branch outright left the
        # suite green. The contradiction goes into an endpoint that does exist.
        intact = copy.deepcopy(self.gateway.endpoints)
        self.assertIsNone(validate(intact), "the unmodified manifest must validate")

        contradictory = copy.deepcopy(self.gateway.endpoints)
        entry = contradictory["asset_ingest"]
        entry["arguments"] = dict(entry["arguments"],
                                  actor={"type": "string", "required": True,
                                         "principal": True})
        with self.assertRaises(UnbuiltEndpoint) as raised:
            validate(contradictory)
        self.assertIn("caller_argument", str(raised.exception))
        self.assertIn("asset_ingest", str(raised.exception))

    def test_every_dispatched_handler_is_audited_from_its_own_signature(self):
        """The census, derived from the code rather than from a list of tool names.

        The check this replaces named four tools. A witness added an endpoint whose
        handler took a principal straight from caller arguments, declared no
        `caller_argument`, and the gateway constructed and accepted it with every test
        green - the enumeration failure this binding exists to prevent, inside the fix
        for it. So the audit walks whatever `_bind` returns and reads each signature.

        Driven here the same way: a new endpoint and handler, added to a live gateway
        exactly as a future author would add one. Nothing below names an existing tool.
        """
        base = copy.deepcopy(self.gateway.endpoints)
        probe = {"tool": "console_grants", "tier": "read", "service": "console",
                 "operation": "list-grants", "effect_class": "NONE",
                 "arguments": {"reader": {"type": "string", "required": True,
                                          "principal": True}}}

        def unbound(reader: Principal) -> list[str]:
            return [reader]

        # 1. A principal taken from caller arguments and not declared a subject.
        with self.assertRaises(UnbuiltEndpoint) as raised:
            audit_handlers({**base, "console_grants": probe},
                           {"console_grants": unbound},
                           implemented=("console_grants",))
        self.assertIn("without declaring it a subject", str(raised.exception))

        # 2. The same handler with the argument simply undeclared: refused for being
        #    unaccounted for, which is the more general failure and catches any
        #    parameter, principal or not.
        bare = dict(probe, arguments={})
        with self.assertRaises(UnbuiltEndpoint) as raised:
            audit_handlers({**base, "console_grants": bare},
                           {"console_grants": unbound},
                           implemented=("console_grants",))
        self.assertIn("the manifest does not declare", str(raised.exception))

        # 2b. The shape this audit was admitting until 2026-08-26: a convenience
        #     parameter with a sensible default and no manifest entry. A default is
        #     not an exemption - `server.py` forwards caller arguments unvalidated,
        #     so the caller sends one anyway - and neither is the annotation. All
        #     four combinations of defaulted/not and typed/plain must refuse, or the
        #     way past the audit is simply to say less.
        def defaulted_principal(reader: Principal = Principal("operator")) -> list[str]:
            return [reader]

        def defaulted_plain(reader: str = "operator") -> list[str]:
            return [reader]

        def bare_plain(reader: str) -> list[str]:
            return [reader]

        for label, handler in (("defaulted Principal", defaulted_principal),
                               ("defaulted plain", defaulted_plain),
                               ("undefaulted plain", bare_plain),
                               ("undefaulted Principal", unbound)):
            with self.subTest(label):
                with self.assertRaises(UnbuiltEndpoint) as hidden:
                    audit_handlers({**base, "console_grants": bare},
                                   {"console_grants": handler},
                                   implemented=("console_grants",))
                self.assertIn("the manifest does not declare", str(hidden.exception))

        # 3. Bound to the caller, it is admitted - so the audit is not refusing
        #    everything it is shown.
        bound = dict(bare, caller_argument="reader")
        self.assertIsNone(audit_handlers({**base, "console_grants": bound},
                                         {"console_grants": unbound},
                                         implemented=("console_grants",)))

    def test_the_implemented_census_is_measured_against_what_is_bound(self):
        """`IMPLEMENTED` is a declaration; `_bind()` is the measurement.

        `validate` decides whether a declared endpoint has an implementation by
        reading the hand-kept tuple and never `Gateway._bind()`, so the two could
        disagree in either direction and nothing noticed. A name in the tuple with
        nothing bound published a tool that `KeyError`ed when called; a handler in
        neither the endpoints nor the withheld list was waved past the audit under a
        comment asserting `validate` had already required a reason for it.

        Both directions, and the two-sided assertion is the point: this is the
        declaration-graded-instead-of-measured shape, inside the module written to
        end it.
        """
        base = copy.deepcopy(self.gateway.endpoints)
        bound = dict(self.gateway._handlers)

        with self.assertRaises(UnbuiltEndpoint) as declared_only:
            audit_handlers(base, bound,
                           implemented=tuple(bound) + ("console_grants",))
        self.assertIn("declared-only=['console_grants']", str(declared_only.exception))

        def stray(query: str) -> list[str]:
            return [query]

        with self.assertRaises(UnbuiltEndpoint) as bound_only:
            audit_handlers(base, {**bound, "console_grants": stray},
                           implemented=tuple(bound))
        self.assertIn("bound-only=['console_grants']", str(bound_only.exception))

    def test_a_handler_neither_declared_nor_withheld_is_refused(self):
        """The `continue` that waved one past, and the withholding path it protects."""
        base = copy.deepcopy(self.gateway.endpoints)
        bound = dict(self.gateway._handlers)

        def stray(query: str) -> list[str]:
            return [query]

        census = tuple(bound) + ("console_grants",)
        handlers = {**bound, "console_grants": stray}
        with self.assertRaises(UnbuiltEndpoint) as loose:
            audit_handlers(base, handlers, implemented=census)
        self.assertIn("neither declares nor withholds", str(loose.exception))

        # Withheld, it is admitted - so the rule is not simply refusing everything
        # the manifest does not serve, which is what withholding exists to allow.
        self.assertIsNone(audit_handlers(
            base, handlers,
            withheld={"console_grants": {"withheld_because": "not offered yet"}},
            implemented=census))

    def test_a_principal_must_be_typed_and_declared_the_same_way_twice(self):
        """The annotation and the manifest are two statements that have to agree.

        This is what makes a grantee readable as a grantee. `authority_grant.actor` is
        a principal the caller names, so it is typed `Principal`, flagged
        `principal: true`, and carries a stated reason under `subject_arguments`. A
        parameter that is a principal in one statement and not the other is refused.
        """
        base = copy.deepcopy(self.gateway.endpoints)

        def named(subject: Principal) -> list[str]:
            return [subject]

        def plain(subject: str) -> list[str]:
            return [subject]

        entry = {"tool": "console_grants", "tier": "read", "service": "console",
                 "operation": "list-grants", "effect_class": "NONE",
                 "subject_arguments": {"subject": "somebody else"},
                 "arguments": {"subject": {"type": "string", "principal": False}}}
        with self.assertRaises(UnbuiltEndpoint) as disagree:
            audit_handlers({**base, "console_grants": entry}, {"console_grants": named},
                           implemented=("console_grants",))
        self.assertIn("principal=False", str(disagree.exception))

        flipped = copy.deepcopy(entry)
        flipped["arguments"]["subject"]["principal"] = True
        with self.assertRaises(UnbuiltEndpoint) as other_way:
            audit_handlers({**base, "console_grants": flipped}, {"console_grants": plain},
                           implemented=("console_grants",))
        self.assertIn("principal=True", str(other_way.exception))

        unclassified = copy.deepcopy(entry)
        del unclassified["arguments"]["subject"]["principal"]
        with self.assertRaises(UnbuiltEndpoint) as silent:
            audit_handlers({**base, "console_grants": unclassified},
                           {"console_grants": plain},
                           implemented=("console_grants",))
        self.assertIn("without saying whether it is a principal", str(silent.exception))

        reasonless = copy.deepcopy(flipped)
        reasonless["subject_arguments"] = {"subject": "  "}
        with self.assertRaises(UnbuiltEndpoint) as mute:
            audit_handlers({**base, "console_grants": reasonless},
                           {"console_grants": named},
                           implemented=("console_grants",))
        self.assertIn("no stated reason", str(mute.exception))

    def test_a_wrapped_handler_is_audited_on_its_real_signature(self):
        """`functools.wraps` sets `__wrapped__` and `inspect.signature` follows it.

        A decorator over a handler therefore hid every parameter it added: the audit
        read the unwrapped function, construction was admitted, and the wrapper's
        extra argument then arrived from the wire through `server.py`, which forwards
        caller arguments unvalidated. `functools.partial` was named in this file as
        the hazard and is not one - `get_type_hints` raises on a partial, so it fails
        closed. This is the construct that fails open.
        """
        base = copy.deepcopy(self.gateway.endpoints)

        def inner(query: str) -> list[str]:
            return [query]

        @functools.wraps(inner)
        def wrapped(query: str, probe_actor: Principal = Principal("nobody")) -> list[str]:
            return [f"{query} as {probe_actor}"]

        self.assertEqual(list(inspect.signature(wrapped).parameters), ["query"],
                         "this case is pointless unless signature() hides the argument")

        entry = {"tool": "console_grants", "tier": "read", "service": "console",
                 "operation": "list-grants", "effect_class": "NONE",
                 "arguments": {"query": {"type": "string", "principal": False}}}
        with self.assertRaises(UnbuiltEndpoint) as hidden:
            audit_handlers({**base, "console_grants": entry},
                           {"console_grants": wrapped},
                           implemented=("console_grants",))
        self.assertIn("probe_actor", str(hidden.exception))

    def test_a_principal_inside_a_union_is_still_a_principal(self):
        """`is Principal` matched only the bare NewType.

        `actor: Principal | None` is an honest annotation - two shipped handlers
        already take `float | None` - and it read as a plain value, so declaring
        `"principal": false` beside it was one false statement rather than two.
        """
        base = copy.deepcopy(self.gateway.endpoints)

        def optional(subject: Principal | None = None) -> list[str]:
            return [subject or ""]

        entry = {"tool": "console_grants", "tier": "read", "service": "console",
                 "operation": "list-grants", "effect_class": "NONE",
                 "arguments": {"subject": {"type": "string", "principal": False}}}
        with self.assertRaises(UnbuiltEndpoint) as slipped:
            audit_handlers({**base, "console_grants": entry},
                           {"console_grants": optional},
                           implemented=("console_grants",))
        self.assertIn("principal=False", str(slipped.exception))

        # Declared honestly, it is a subject like any other named principal.
        honest = copy.deepcopy(entry)
        honest["arguments"]["subject"]["principal"] = True
        honest["subject_arguments"] = {"subject": "named by the caller, not claimed"}
        self.assertIsNone(audit_handlers({**base, "console_grants": honest},
                                         {"console_grants": optional},
                                         implemented=("console_grants",)))

    def test_the_shipped_manifest_and_handlers_pass_that_audit(self):
        """The positive control, and the one every case above is measured against.

        The second assertion used to demand that no handler exists without an
        endpoint, which contradicts the withholding path `audit_handlers` documents
        and `validate` enforces: withholding is precisely a bound handler whose
        endpoint is not served, and it is how a built capability stops being offered
        without its code being deleted. The assertion was true only because nothing is
        withheld today, and would have failed the moment anything was. The real
        invariant is that such a handler is withheld *with a stated reason*, which is
        what this reads.
        """
        self.assertIsNone(audit_handlers(self.gateway.endpoints, self.gateway._handlers))
        unserved = set(self.gateway._handlers) - set(self.gateway.endpoints)
        for tool in unserved:
            self.assertIn(tool, self.gateway.withheld,
                          "a handler is dispatched that the manifest neither declares "
                          "nor withholds")
            self.assertTrue(self.gateway.withheld[tool].get("withheld_because"))
        self.assertEqual(unserved, set(), "nothing is withheld on the shipped manifest")

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
