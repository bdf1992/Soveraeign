from __future__ import annotations

from pathlib import Path
import json


def replace(path: str, old: str, new: str, *, count: int = 1) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"expected block missing in {path}: {old[:120]!r}")
    target.write_text(text.replace(old, new, count), encoding="utf-8", newline="\n")


# The earlier migration helper briefly made the command surface auto-issue
# open:session. Remove that convenience: session identity is not authority, and a CLI
# caller may carry an existing session but may never mint permission merely by naming
# an actor.
replace(
    "scripts/sov_interface.py",
    '''from sovnode.composition import LocalActionPath  # noqa: E402
from soveraeign_console_service import authority as console_authority  # noqa: E402
from soveraeign_console_service.refusals import AuthorityRefused  # noqa: E402
''',
    '''from sovnode.composition import LocalActionPath  # noqa: E402
''',
)
replace(
    "scripts/sov_interface.py",
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
''',
    '''def command_invoke(args: argparse.Namespace) -> int:
    try:
        document = _current()
        request = invocation_request(
            document, args.operation, args.binding, args.actor, args.scope,
            _arguments(args.arguments), session_id=args.session_id or "",
            session_binding_id=args.session_binding_id or "",
            principal_id=args.principal)
    except BindingRefusal as refusal:
        print(f"REFUSED {refusal.code}: {refusal}")
        return 0
    state = Path(args.state_root) if args.state_root else DEFAULT_STATE
    with LocalActionPath(state) as node:
        receipt = node.dispatch(request)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0
''',
)
replace(
    "scripts/sov_interface.py",
    '''    invoke.add_argument("--scope", required=True)
    invoke.add_argument("--state-root")
''',
    '''    invoke.add_argument("--scope", required=True)
    invoke.add_argument("--session", dest="session_id")
    invoke.add_argument("--session-binding", dest="session_binding_id")
    invoke.add_argument("--principal")
    invoke.add_argument("--state-root")
''',
)

# Human surface forwards the same explicit provenance. Missing session facts are a
# typed binding refusal before LocalActionPath opens state.
replace(
    "scripts/sov_surface.py",
    '''def command_try(args: argparse.Namespace) -> int:
    """Delegate action construction to the canonical Human/Model binding."""
    return interface_main([
        "invoke", args.operation, *args.arguments,
        "--binding", args.binding, "--actor", args.actor, "--scope", args.scope,
        "--state-root", args.state_root or str(SCRATCH),
    ])
''',
    '''def command_try(args: argparse.Namespace) -> int:
    """Delegate action construction to the canonical Human/Model binding."""
    command = [
        "invoke", args.operation, *args.arguments,
        "--binding", args.binding, "--actor", args.actor, "--scope", args.scope,
        "--state-root", args.state_root or str(SCRATCH),
    ]
    if args.session_id:
        command.extend(["--session", args.session_id])
    if args.session_binding_id:
        command.extend(["--session-binding", args.session_binding_id])
    if args.principal:
        command.extend(["--principal", args.principal])
    return interface_main(command)
''',
)
replace(
    "scripts/sov_surface.py",
    '''    invoke.add_argument("--scope", required=True)
    invoke.add_argument("--state-root")
''',
    '''    invoke.add_argument("--scope", required=True)
    invoke.add_argument("--session", dest="session_id")
    invoke.add_argument("--session-binding", dest="session_binding_id")
    invoke.add_argument("--principal")
    invoke.add_argument("--state-root")
''',
)
replace(
    "scripts/tests/test_sov_surface.py",
    '''    def test_human_action_without_authority_returns_actual_refused_receipt(self) -> None:
        code, output = self.run_try("asset.ingest-asset")
        self.assertEqual(code, 0)
        receipt = json.loads(output)
        self.assertEqual(receipt["kind"], "RECEIPT")
        self.assertEqual(receipt["payload"]["outcome"], "REFUSED")
        self.assertEqual(receipt["payload"]["detail"]["reason_code"], "AUTHORITY_REFUSED")

    def test_model_takes_the_same_gateway_refusal_path(self) -> None:
        code, output = self.run_try("asset.ingest-asset", "MODEL")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output)["payload"]["detail"]["reason_code"],
                         "AUTHORITY_REFUSED")
''',
    '''    def test_human_action_without_session_refuses_before_state_is_opened(self) -> None:
        code, output = self.run_try("asset.ingest-asset")
        self.assertEqual(code, 0)
        self.assertIn("REFUSED SESSION_IDENTITY_REQUIRED", output)
        self.assertFalse((self.root / "human").exists())

    def test_model_requires_the_same_explicit_session_identity(self) -> None:
        code, output = self.run_try("asset.ingest-asset", "MODEL")
        self.assertEqual(code, 0)
        self.assertIn("REFUSED SESSION_IDENTITY_REQUIRED", output)
        self.assertFalse((self.root / "model").exists())
''',
)

# Rendered invocation guidance must not advertise a command that necessarily refuses.
replace(
    "scripts/sovsurface/page.py",
    '''    command = (f"python scripts/sov_surface.py try {record['operation_id']} {arguments} "
               "--binding HUMAN --actor YOUR_ACTOR --scope YOUR_SCOPE")
    return ("<dt>Request</dt><dd><pre>" + _e(command) +
            "</pre>The Gateway checks live authority for that actor and scope. "
            "The surface projects no grant and creates none.</dd>")
''',
    '''    command = (f"python scripts/sov_surface.py try {record['operation_id']} {arguments} "
               "--binding HUMAN --actor YOUR_ACTOR --scope YOUR_SCOPE "
               "--session YOUR_SESSION --session-binding YOUR_SESSION_BINDING")
    return ("<dt>Request</dt><dd><pre>" + _e(command) +
            "</pre>The Gateway first checks that session attribution, then checks live "
            "authority for that actor and scope. The surface projects no grant, creates "
            "no session, and creates no authority.</dd>")
''',
)

# Make the extracted concern part of the route's source provenance.
replace(
    "scripts/sovnode/composition.py",
    '''    "services/gateway/src/soveraeign_gateway_service/core.py",
)
''',
    '''    "services/gateway/src/soveraeign_gateway_service/core.py",
    "services/gateway/src/soveraeign_gateway_service/attribution.py",
)
''',
)

# Gateway owns attribution evidence but exposes no new public operation. Local refusal
# mapping stays distinct from typed authority: mismatch is malformed admission state;
# a closed session is stale state.
manifest_path = Path("services/gateway/contracts/service.json")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
if "session-attribution" not in manifest["owns"]:
    manifest["owns"].insert(1, "session-attribution")
manifest["local_refusals"]["ACTOR_ATTRIBUTION_MISMATCH"] = "INCOMPLETE_PROPOSAL"
manifest["local_refusals"]["SESSION_CLOSED"] = "STALE_STATE"
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")

# Historical measured evidence is immutable. Its input digest must agree with the
# contemporaneous discovery observation, not with every future capability-map rebuild.
replace(
    "scripts/tests/test_trace.py",
    '''RECEIPT = json.loads((ROOT / "bindings" / "mcp" / "observations"
                      / "journey-02-receipt.json").read_text("utf-8"))
''',
    '''RECEIPT = json.loads((ROOT / "bindings" / "mcp" / "observations"
                      / "journey-02-receipt.json").read_text("utf-8"))
DISCOVERY = json.loads((ROOT / "bindings" / "mcp" / "observations"
                        / "journey-02-discovery.json").read_text("utf-8"))
''',
)
replace(
    "scripts/tests/test_trace.py",
    '''    def test_it_pins_the_state_it_read(self) -> None:
        self.assertEqual(RECEIPT["input_state_digest"], MAP["input_state_digest"])
''',
    '''    def test_it_pins_the_state_this_observation_read(self) -> None:
        self.assertEqual(RECEIPT["input_state_digest"], DISCOVERY["capability_revision"])
''',
)
