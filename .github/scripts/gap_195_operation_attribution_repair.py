from __future__ import annotations

from pathlib import Path


def replace(path: str, old: str, new: str, count: int = 1) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"expected block missing in {path}: {old[:100]!r}")
    target.write_text(text.replace(old, new, count), encoding="utf-8", newline="\n")


# The first one-shot patcher is intentionally not part of the product commit, but it
# is still visible to repository hygiene while this workflow runs. Keep the helper
# itself inside the repository's Python contract until both helpers are deleted.
patcher = Path(".github/scripts/gap_195_operation_attribution.py")
patcher_text = patcher.read_text(encoding="utf-8")
if not patcher_text.startswith("from __future__ import annotations\n"):
    patcher.write_text(
        "from __future__ import annotations\n\n" + patcher_text,
        encoding="utf-8", newline="\n")


# Keep Gateway core below the repository's 300-line ownership limit by moving the
# attribution decision into its own small internal concern. Gateway still owns the
# sequence; this module owns only how a session-attribution callback becomes durable
# ALLOWED/REFUSED/FAILED evidence.
attribution_module = Path(
    "services/gateway/src/soveraeign_gateway_service/attribution.py")
attribution_module.write_text('''"""Session-attribution evidence for one Gateway request crossing."""

from __future__ import annotations

from typing import Any

from soveraeign_record_service import RecordService

from .contract import AttributionCheck, GatewayFault, GatewayRefusal
from .evidence import record_attribution


def check(record: RecordService, request: dict[str, Any], request_id: str,
          request_entry_id: str, attribution: AttributionCheck,
          denials: tuple[type[BaseException], ...]) -> dict[str, Any]:
    """Prove the session claim before capability resolution or authority.

    Session identity and grant authority are separate questions. A valid session
    never supplies a grant; a valid grant never proves which session made the call.
    """
    try:
        attribution(
            request["actor"], request["actor_kind"], request["session_id"],
            request["session_binding_id"], request["principal_id"])
    except Exception as error:
        diagnostic = getattr(error, "reason_code", type(error).__name__)
        if denials and isinstance(error, denials):
            record_attribution(
                record, request, request_id, request_entry_id,
                decision="REFUSED", diagnostic_code=diagnostic)
            raise GatewayRefusal(
                diagnostic, str(error), stage="check-attribution",
                diagnostic_code=diagnostic) from error
        record_attribution(
            record, request, request_id, request_entry_id,
            decision="FAILED", diagnostic_code=type(error).__name__)
        raise GatewayFault(
            "ATTRIBUTION_CHECK_FAILED", str(error), event="gateway.check-attribution",
            stage="check-attribution", error_type=type(error).__name__) from error
    return record_attribution(
        record, request, request_id, request_entry_id, decision="ALLOWED")


__all__ = ["check"]
''', encoding="utf-8", newline="\n")

replace(
    "services/gateway/src/soveraeign_gateway_service/core.py",
    '''from .contract import (
''',
    '''from .attribution import check as check_attribution
from .contract import (
''')
replace(
    "services/gateway/src/soveraeign_gateway_service/core.py",
    '''    record_attribution,
    record_authority,
''',
    '''    record_authority,
''')
replace(
    "services/gateway/src/soveraeign_gateway_service/core.py",
    '''            attribution = self._check_attribution(
                accepted, request_id, request_entry["entry_id"])
''',
    '''            attribution = check_attribution(
                self.record, accepted, request_id, request_entry["entry_id"],
                self.attribution, self.attribution_denials)
''')
replace(
    "services/gateway/src/soveraeign_gateway_service/core.py",
    '''    def _check_attribution(self, request: dict[str, Any], request_id: str,
                           request_entry_id: str) -> dict[str, Any]:
        """Prove the session claim before capability resolution or authority.

        Session identity and grant authority are separate questions. A valid session
        never supplies a grant; a valid grant never proves which session made the call.
        """
        try:
            self.attribution(
                request["actor"], request["actor_kind"], request["session_id"],
                request["session_binding_id"], request["principal_id"])
        except Exception as error:
            diagnostic = getattr(error, "reason_code", type(error).__name__)
            if self.attribution_denials and isinstance(error, self.attribution_denials):
                record_attribution(
                    self.record, request, request_id, request_entry_id,
                    decision="REFUSED", diagnostic_code=diagnostic)
                raise GatewayRefusal(
                    diagnostic, str(error), stage="check-attribution",
                    diagnostic_code=diagnostic) from error
            record_attribution(
                self.record, request, request_id, request_entry_id,
                decision="FAILED", diagnostic_code=type(error).__name__)
            raise GatewayFault(
                "ATTRIBUTION_CHECK_FAILED", str(error), event="gateway.check-attribution",
                stage="check-attribution", error_type=type(error).__name__) from error
        return record_attribution(
            self.record, request, request_id, request_entry_id, decision="ALLOWED")

''',
    '')

# `console.read-thread` already owns a domain argument called session_id. Do not make
# the envelope's new session field erase that legitimate route contract. A service may
# repeat session_id only when it is byte-for-byte the same session that the Gateway
# already checked; all other attribution fields remain forbidden as service arguments.
replace(
    "services/gateway/src/soveraeign_gateway_service/core.py",
    '''        attribution = ATTRIBUTION_ARGUMENTS.intersection(request["arguments"])
        if attribution:
            raise GatewayRefusal(
                "MALFORMED_REQUEST",
                f"service arguments may not override checked attribution: {sorted(attribution)}",
                stage="accept-request", diagnostic_code="ACTOR_ATTRIBUTION_CONFLICT")
''',
    '''        attribution = ATTRIBUTION_ARGUMENTS.intersection(request["arguments"])
        conflicting = attribution - {"session_id"}
        session_conflict = ("session_id" in attribution
                            and request["arguments"]["session_id"] != request["session_id"])
        if conflicting or session_conflict:
            names = set(conflicting)
            if session_conflict:
                names.add("session_id")
            raise GatewayRefusal(
                "MALFORMED_REQUEST",
                f"service arguments may not override checked attribution: {sorted(names)}",
                stage="accept-request", diagnostic_code="ACTOR_ATTRIBUTION_CONFLICT")
''')

# Node Interface binding construction enforces the same equality before a request is
# emitted. This catches a mismatched session at the binding surface rather than relying
# on Gateway as the first reader.
replace(
    "scripts/sovnode/bindings.py",
    '''    if principal_id is not None and not principal_id:
        raise BindingRefusal("SESSION_IDENTITY_REQUIRED", operation_id)
    return {
''',
    '''    if principal_id is not None and not principal_id:
        raise BindingRefusal("SESSION_IDENTITY_REQUIRED", operation_id)
    if ("session_id" in arguments and arguments["session_id"] != session_id):
        raise BindingRefusal("SESSION_ATTRIBUTION_CONFLICT", operation_id)
    return {
''')

# The concrete command binding establishes its own operational session before building
# an invocation. It does not grant the requested operation. If the node already has a
# root issuer, that issuer must authorize the session grant; on a fresh local store the
# existing first-issuer rule records Bdo as root and gives the actor only open:session.
replace(
    "scripts/sov_interface.py",
    '''from sovnode.composition import LocalActionPath  # noqa: E402
''',
    '''from sovnode.composition import LocalActionPath  # noqa: E402
from soveraeign_console_service import authority as console_authority  # noqa: E402
from soveraeign_console_service.refusals import AuthorityRefused  # noqa: E402
''')
replace(
    "scripts/sov_interface.py",
    '''def command_invoke(args: argparse.Namespace) -> int:
    try:
        document = _current()
        request = invocation_request(
            document, args.operation, args.binding, args.actor, args.scope,
            _arguments(args.arguments))
    except BindingRefusal as refusal:
        print(f"REFUSED {refusal.code}: {refusal}")
        return 0
    state = Path(args.state_root) if args.state_root else DEFAULT_STATE
    with LocalActionPath(state) as node:
        receipt = node.dispatch(request)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0
''',
    '''def command_invoke(args: argparse.Namespace) -> int:
    try:
        document = _current()
        arguments = _arguments(args.arguments)
    except BindingRefusal as refusal:
        print(f"REFUSED {refusal.code}: {refusal}")
        return 0
    state = Path(args.state_root) if args.state_root else DEFAULT_STATE
    with LocalActionPath(state) as node:
        entries = node.record.reconstruct()
        try:
            console_authority.check(
                entries, node.node_id, args.actor, "open:session", args.actor)
        except AuthorityRefused:
            issuer = console_authority.root_issuer(entries, node.node_id) or "Bdo"
            node.console.grant(args.actor, "open:session", args.actor, issuer)
        session = node.console.open_session(
            args.actor, args.binding,
            f"urn:soveraeign:binding:sov-interface:{args.binding.lower()}")
        try:
            request = invocation_request(
                document, args.operation, args.binding, args.actor, args.scope, arguments,
                session_id=session["session_id"],
                session_binding_id=session["binding_id"],
                principal_id=session.get("principal_id"))
        except BindingRefusal as refusal:
            print(f"REFUSED {refusal.code}: {refusal}")
            return 0
        receipt = node.dispatch(request)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0
''')

# Console horizontal already opens exact HUMAN/MODEL sessions. Carry those facts into
# the envelope. A mutated actor kind now fails at attribution, deliberately before the
# later capability actor-policy check.
replace(
    "scripts/tests/test_console_horizontal.py",
    '''        return invocation_request(
            self.document, "console.read-thread", binding, actor, thread_id,
            {"thread_id": thread_id, "session_id": self.sessions[binding]["session_id"]},
        )
''',
    '''        session = self.sessions[binding]
        return invocation_request(
            self.document, "console.read-thread", binding, actor, thread_id,
            {"thread_id": thread_id, "session_id": session["session_id"]},
            session_id=session["session_id"],
            session_binding_id=session["binding_id"],
            principal_id=session.get("principal_id"),
        )
''')
replace(
    "scripts/tests/test_console_horizontal.py",
    '''        self.assertEqual(self.detail(policy_refusal)["reason_code"], "AUTHORITY_REFUSED")
        self.assertEqual(self.detail(policy_refusal)["diagnostic_code"],
                         "ACTOR_KIND_NOT_ADMITTED")
''',
    '''        self.assertEqual(
            self.detail(policy_refusal)["reason_code"], "ACTOR_ATTRIBUTION_MISMATCH")
        self.assertEqual(self.detail(policy_refusal)["stage"], "check-attribution")
''')
replace(
    "scripts/tests/test_console_horizontal.py",
    '''            self.node.record, tampered, manifests, table, authority,
            {"console:in-process": ConsoleRoutes(self.node.console).call},
            authority_denials=(AuthorityRefused,),
''',
    '''            self.node.record, tampered, manifests, table, authority,
            {"console:in-process": ConsoleRoutes(self.node.console).call},
            attribution=lambda *_: None,
            authority_denials=(AuthorityRefused,),
''')

# Host's Gateway vertical now uses real Console sessions. The session grant is setup;
# read:host-health remains a separate grant so the missing-grant defeating case still
# reaches authority and refuses there.
replace(
    "services/host/tests/test_host_service.py",
    '''from soveraeign_console_service import authority as console_authority  # noqa: E402
from soveraeign_console_service.refusals import AuthorityRefused  # noqa: E402
''',
    '''from soveraeign_console_service import authority as console_authority  # noqa: E402
from soveraeign_console_service import reads as console_reads  # noqa: E402
from soveraeign_console_service.refusals import (  # noqa: E402
    ActorAttributionMismatch, AuthorityRefused, SessionClosed, UnknownRecord,
)
''')
replace(
    "services/host/tests/test_host_service.py",
    '''        def authority(actor: str, capability: str, scope: str) -> str:
            return console_authority.check(
                self.record.reconstruct(), self.console.node_id, actor, capability,
                scope)

        self.gateway = Gateway(
''',
    '''        def authority(actor: str, capability: str, scope: str) -> str:
            return console_authority.check(
                self.record.reconstruct(), self.console.node_id, actor, capability,
                scope)

        def attribution(actor: str, actor_kind: str, session_id: str,
                        session_binding_id: str, principal_id: str | None) -> None:
            try:
                session = console_reads.session(self.record.reconstruct(), session_id)
            except UnknownRecord:
                raise ActorAttributionMismatch("test session is unknown") from None
            if (session.get("node_id") != self.console.node_id
                    or session.get("operator_id") != actor
                    or session.get("actor_kind") != actor_kind
                    or session.get("binding_id") != session_binding_id
                    or session.get("principal_id") != principal_id):
                raise ActorAttributionMismatch("test session attribution mismatch")
            if session.get("lifecycle") != "OPEN":
                raise SessionClosed(f"session {session_id} is CLOSED")

        self.sessions: dict[tuple[str, str], dict[str, Any]] = {}
        self.gateway = Gateway(
''')
replace(
    "services/host/tests/test_host_service.py",
    '''            self.record, capability_map, manifests, table, authority,
            {"host:in-process": HostRoutes(self.host).call},
            authority_denials=(AuthorityRefused,),
''',
    '''            self.record, capability_map, manifests, table, authority,
            {"host:in-process": HostRoutes(self.host).call},
            attribution=attribution,
            authority_denials=(AuthorityRefused,),
            attribution_denials=(ActorAttributionMismatch, SessionClosed),
''')
replace(
    "services/host/tests/test_host_service.py",
    '''    def request(self, actor: str, actor_kind: str = "HUMAN",
                arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "actor": actor,
            "actor_kind": actor_kind,
            "logical_endpoint": "sov://host/read-health",
''',
    '''    def request(self, actor: str, actor_kind: str = "HUMAN",
                arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        key = (actor, actor_kind)
        if key not in self.sessions:
            self.console.grant(actor, "open:session", actor, "Bdo")
            self.sessions[key] = self.console.open_session(
                actor, actor_kind, f"host-test:{actor_kind.lower()}")
        session = self.sessions[key]
        return {
            "actor": actor,
            "actor_kind": actor_kind,
            "session_id": session["session_id"],
            "session_binding_id": session["binding_id"],
            "principal_id": session.get("principal_id"),
            "interface_binding_id": f"host-test-interface:{actor_kind.lower()}",
            "interface_operation_digest": "host-test-interface-digest",
            "logical_endpoint": "sov://host/read-health",
''')

# The participant-side Gateway witness opens a real Console session and records the
# exact Node Interface operation digest. The independent observer below will verify
# that session directly from Record rows without importing participant code.
replace(
    "scripts/gateway_witness_driver.py",
    '''from soveraeign_console_service import ConsoleService
from soveraeign_console_service import authority as console_authority
from soveraeign_console_service.refusals import AuthorityRefused
''',
    '''from soveraeign_console_service import ConsoleService
from soveraeign_console_service import authority as console_authority
from soveraeign_console_service import reads as console_reads
from soveraeign_console_service.refusals import (
    ActorAttributionMismatch, AuthorityRefused, SessionClosed, UnknownRecord,
)
''')
replace(
    "scripts/gateway_witness_driver.py",
    '''        scope = f"asset:new:{actor}"
        console.grant(actor, "ingest:asset", scope, "Bdo")
        capability_map, manifests, capability_table = load_surface(ROOT)
        gateway = Gateway(
''',
    '''        scope = f"asset:new:{actor}"
        console.grant(actor, "open:session", actor, "Bdo")
        session = console.open_session(
            actor, actor_kind,
            f"urn:soveraeign:binding:gateway-witness:{actor_kind.lower()}")
        console.grant(actor, "ingest:asset", scope, "Bdo")
        capability_map, manifests, capability_table = load_surface(ROOT)
        interface = json.loads((ROOT / "contracts" / "fixtures" /
                                "node-interface.reference.json").read_text("utf-8"))
        operation = next(row for row in interface["operations"]
                         if row["operation_id"] == "asset.ingest-asset")

        def attribution(checked_actor: str, checked_kind: str, session_id: str,
                        session_binding_id: str, principal_id: str | None) -> None:
            try:
                held = console_reads.session(record.reconstruct(), session_id)
            except UnknownRecord:
                raise ActorAttributionMismatch("witness session is unknown") from None
            if (held.get("node_id") != console.node_id
                    or held.get("operator_id") != checked_actor
                    or held.get("actor_kind") != checked_kind
                    or held.get("binding_id") != session_binding_id
                    or held.get("principal_id") != principal_id):
                raise ActorAttributionMismatch("witness session attribution mismatch")
            if held.get("lifecycle") != "OPEN":
                raise SessionClosed(f"session {session_id} is CLOSED")

        gateway = Gateway(
''')
replace(
    "scripts/gateway_witness_driver.py",
    '''            {"asset:in-process": AssetRoutes(asset).call},
            authority_denials=(AuthorityRefused,),
        )
        returned = gateway.dispatch({
            "actor": actor,
            "actor_kind": actor_kind,
            "logical_endpoint": "sov://asset/ingest-asset",
''',
    '''            {"asset:in-process": AssetRoutes(asset).call},
            attribution=attribution,
            authority_denials=(AuthorityRefused,),
            attribution_denials=(ActorAttributionMismatch, SessionClosed),
        )
        returned = gateway.dispatch({
            "actor": actor,
            "actor_kind": actor_kind,
            "session_id": session["session_id"],
            "session_binding_id": session["binding_id"],
            "principal_id": session.get("principal_id"),
            "interface_binding_id": "urn:soveraeign:binding:gateway-witness-interface",
            "interface_operation_digest": operation["record_digest"],
            "logical_endpoint": "sov://asset/ingest-asset",
''')

# Independent observation now includes the attribution event and independently reads
# the Console session EVENT from the Record journal. It does not trust the Gateway's
# ALLOWED claim as proof of its own precondition.
replace(
    "scripts/gateway_observe.py",
    '''EXPECTED_KINDS = (
    "gateway-request",
    "gateway-capability-resolution",
''',
    '''EXPECTED_KINDS = (
    "gateway-request",
    "gateway-session-attribution",
    "gateway-capability-resolution",
''')
replace(
    "scripts/gateway_observe.py",
    '''        request, resolution, authority, routing, returned = (
            by_kind[name] for name in EXPECTED_KINDS
        )
''',
    '''        request, attribution, resolution, authority, routing, returned = (
            by_kind[name] for name in EXPECTED_KINDS
        )
''')
replace(
    "scripts/gateway_observe.py",
    '''        if (request["actor"] != actor
                or request["payload"].get("actor_kind") != actor_kind
                or request["subject"] != "sov://asset/ingest-asset"):
            defects.append("REQUEST_ATTRIBUTION_INVALID")
        if (resolution["payload"].get("capability_id") != "asset.ingest-asset"
                or resolution["payload"].get("route_address") != "asset:in-process"):
            defects.append("RESOLUTION_INVALID")
''',
    '''        request_payload = request["payload"]
        if (request["actor"] != actor
                or request_payload.get("actor_kind") != actor_kind
                or request["subject"] != "sov://asset/ingest-asset"):
            defects.append("REQUEST_ATTRIBUTION_INVALID")
        session_id = request_payload.get("session_id")
        session_rows = [row for row in rows if row["kind"] == "EVENT"
                        and row["payload"].get("record_kind") == "operator-session"
                        and row["payload"].get("session_id") == session_id]
        if len(session_rows) != 1:
            defects.append("SESSION_RECORD_INVALID")
        else:
            session = session_rows[0]["payload"]
            if (session_rows[0]["actor"] != actor
                    or session.get("operator_id") != actor
                    or session.get("actor_kind") != actor_kind
                    or session.get("binding_id") != request_payload.get("session_binding_id")
                    or session.get("principal_id") != request_payload.get("principal_id")
                    or session.get("lifecycle") != "OPEN"):
                defects.append("SESSION_RECORD_INVALID")
        interface = json.loads((repository / "contracts" / "fixtures" /
                                "node-interface.reference.json").read_text("utf-8"))
        operation = next((row for row in interface.get("operations", [])
                          if row.get("operation_id") == "asset.ingest-asset"), None)
        if (not isinstance(request_payload.get("interface_binding_id"), str)
                or not request_payload.get("interface_binding_id")
                or operation is None
                or request_payload.get("interface_operation_digest") != operation.get("record_digest")):
            defects.append("INTERFACE_PROVENANCE_INVALID")
        attributed = attribution["payload"]
        if (attributed.get("decision") != "ALLOWED"
                or attributed.get("request_entry_id") != request["entry_id"]
                or any(attributed.get(field) != request_payload.get(field) for field in (
                    "session_id", "session_binding_id", "principal_id",
                    "interface_binding_id", "interface_operation_digest"))):
            defects.append("SESSION_ATTRIBUTION_INVALID")
        if (resolution["payload"].get("capability_id") != "asset.ingest-asset"
                or resolution["payload"].get("route_address") != "asset:in-process"
                or resolution["payload"].get("attribution_entry_id") != attribution["entry_id"]):
            defects.append("RESOLUTION_INVALID")
''')

# Add one observer-level defeating case that rewrites the session event while preserving
# the rest of the participant output. The chain will also object, but the observer must
# name the session invariant rather than relying on a generic digest failure alone.
replace(
    "scripts/tests/test_gateway_observe.py",
    '''    def test_independent_observer_rejects_rewritten_gateway_evidence(self) -> None:
''',
    '''    def test_independent_observer_rejects_session_record_mismatch(self) -> None:
        tampered = Path(self.temporary.name) / "session-mismatch"
        shutil.copytree(self.state, tampered)
        database = tampered / "record" / "record-service.sqlite3"
        connection = sqlite3.connect(database)
        try:
            row = connection.execute(
                "SELECT seq, payload_json FROM journal WHERE payload_json LIKE ? ORDER BY seq LIMIT 1",
                ('%"record_kind":"operator-session"%',)).fetchone()
            self.assertIsNotNone(row)
            payload = json.loads(row[1])
            payload["binding_id"] = "forged-host-binding"
            connection.execute(
                "UPDATE journal SET payload_json=? WHERE seq=?",
                (json.dumps(payload, sort_keys=True, separators=(",", ":")), row[0]))
            connection.commit()
        finally:
            connection.close()
        defects = observe.crossing_defects(ROOT, tampered, self.output, self.actor, "HUMAN")
        self.assertIn("SESSION_RECORD_INVALID", defects)

    def test_independent_observer_rejects_rewritten_gateway_evidence(self) -> None:
''')

# Direct Gateway tests already proved a mismatched callback refuses. Also pin the
# legitimate same-session service argument and the cross-session defeat at Gateway's
# structural boundary.
replace(
    "services/gateway/tests/test_gateway_slice.py",
    '''    def test_session_identity_is_required_before_attribution(self) -> None:
''',
    '''    def test_service_session_argument_must_match_checked_session(self) -> None:
        request = self.request("operator", "HUMAN", self.source("same-session.txt"), "asset:new")
        request["arguments"]["session_id"] = request["session_id"]
        allowed = self.new_gateway().dispatch(request)
        self.assertNotEqual(self.reason(allowed), "MALFORMED_REQUEST")

        request = self.request("operator", "HUMAN", self.source("other-session.txt"), "asset:new")
        request["arguments"]["session_id"] = "session:someone-else"
        refused = self.new_gateway().dispatch(request)
        self.assertEqual(self.reason(refused), "MALFORMED_REQUEST")
        self.assertEqual(self.detail(refused)["diagnostic_code"], "ACTOR_ATTRIBUTION_CONFLICT")

    def test_session_identity_is_required_before_attribution(self) -> None:
''')
