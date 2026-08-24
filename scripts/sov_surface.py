#!/usr/bin/env python3
"""The human view of what this node can do, and a way to actually call it.

`render` writes a self-contained HTML page joining three records: the capability
map projection, the service manifests behind it, and the gateway manifest that
says what an operator can reach today. `check` refuses when the checked-in page
no longer matches those inputs, so a stale page fails a gate instead of quietly
misinforming a reader. `try` runs one exposed endpoint through the gateway
against a scratch store and prints both the result and the journal entries the
call produced - the same thing a Swagger page's "try it out" does, minus an HTTP
transport this phase does not have.

Every read is local. `try` writes only under the scratch root it is given.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from sovsurface.page import render as render_page  # noqa: E402

CAPABILITY_MAP = ROOT / "contracts" / "fixtures" / "capability-map.reference.json"
GATEWAY_MANIFEST = ROOT / "bindings" / "mcp" / "manifest.json"
MANIFEST_PATHS = sorted((ROOT / "services").glob("*/contracts/service.json"))
PAGE = ROOT / "docs" / "surface.html"
SCRATCH = ROOT / ".local" / "surface-try"


class PhantomOperation(RuntimeError):
    """A gateway endpoint named a service operation that no manifest declares."""


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _details() -> dict[str, dict[str, Any]]:
    """Per-operation detail from the service manifests, keyed by capability id."""
    detail: dict[str, dict[str, Any]] = {}
    for path in MANIFEST_PATHS:
        manifest = _load(path)
        for operation in manifest["operations"]:
            if isinstance(operation, str):
                operation = {"operation": operation}
            detail[f"{manifest['service_id']}.{operation['operation']}"] = operation
    return detail


def surface() -> dict[str, Any]:
    """Join the three records into one view, keeping their disagreements visible."""
    capabilities = _load(CAPABILITY_MAP)["capabilities"]
    detail = _details()
    gateway = _load(GATEWAY_MANIFEST)
    served = {entry["realizes"]: entry for entry in gateway["endpoints"] if entry.get("realizes")}
    undeclared = [entry["tool"] for entry in gateway["endpoints"] if not entry.get("realizes")]

    by_service: dict[str, list[dict[str, Any]]] = {}
    map_says_off = []
    for capability in capabilities:
        item = {"capability": capability,
                "detail": detail.get(capability["capability_id"], {}),
                "served": served.get(capability["capability_id"])}
        by_service.setdefault(capability["service_id"], []).append(item)
        if item["served"] and not _map_activates_mcp(capability):
            map_says_off.append(capability["capability_id"])

    known = {capability["capability_id"] for capability in capabilities}
    phantom = sorted(set(served) - known)
    if phantom:
        raise PhantomOperation(
            "gateway endpoints claim operations no service manifest declares: "
            + ", ".join(phantom))

    services = sorted(by_service)
    for operations in by_service.values():
        operations.sort(key=lambda item: item["capability"]["capability_id"])
    return {
        "services": services,
        "by_service": by_service,
        "gap": {"map_says_off": map_says_off, "undeclared": undeclared},
        "counts": {
            "declared": len(capabilities),
            "served": len(served),
            "services": len(services),
            "built_services": sum(
                1 for service in services
                if by_service[service][0]["capability"].get("service_standing") == "BUILT"),
            "undeclared": len(undeclared),
        },
    }


def _map_activates_mcp(capability: dict[str, Any]) -> bool:
    return any(endpoint.get("transport") == "MCP" and endpoint.get("activation") == "ACTIVE"
               for endpoint in capability.get("endpoints", []))


def input_digest() -> str:
    """One digest over every file the page is derived from."""
    material = sha256()
    for path in [CAPABILITY_MAP, GATEWAY_MANIFEST, *MANIFEST_PATHS,
                 ROOT / "scripts" / "sovsurface" / "page.py"]:
        material.update(path.read_bytes())
    return material.hexdigest()


def build() -> str:
    """The page bytes, with the digest of the inputs it was built from."""
    return render_page(surface()) + f"\n<!-- inputs {input_digest()} -->\n"


def cmd_render(args: argparse.Namespace) -> int:
    out = Path(args.out) if args.out else PAGE
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(), encoding="utf-8", newline="\n")
    view = surface()
    print(f"PASS: {out.relative_to(ROOT)} "
          f"({view['counts']['declared']} declared, {view['counts']['served']} served, "
          f"{len(view['gap']['map_says_off']) + view['counts']['undeclared']} disagreements)")
    return 0


def cmd_check(_: argparse.Namespace) -> int:
    """Refuse a page that no longer matches the records it claims to project."""
    if not PAGE.exists():
        print(f"FAIL: {PAGE.relative_to(ROOT)} has not been rendered")
        return 1
    if PAGE.read_text(encoding="utf-8") != build():
        print(f"FAIL: {PAGE.relative_to(ROOT)} is stale; "
              "run `python scripts/sov_surface.py render`")
        return 1
    view = surface()
    print(f"PASS: surface page matches {view['counts']['declared']} declared operations "
          f"and {view['counts']['served']} served endpoints")
    return 0


def cmd_try(args: argparse.Namespace) -> int:
    """Call one exposed endpoint for real and show what the journal recorded."""
    sys.path.insert(0, str(ROOT / "bindings" / "mcp"))
    from gateway import EndpointRefused, Gateway  # noqa: PLC0415

    arguments: dict[str, Any] = {}
    for pair in args.arguments:
        key, _, value = pair.partition("=")
        arguments[key] = value
    root = Path(args.state_root) if args.state_root else SCRATCH
    gateway = Gateway(root)
    if args.session:
        # Each invocation is its own process, so a session opened by an earlier
        # call is reattached by id. A dead or invented id fails the same check
        # every other caller faces, so this reattaches, it does not authorize.
        if not gateway.asset.authority.session_live(args.session):
            print(f"REFUSED SESSION_NOT_LIVE: {args.session} is closed, expired, or unknown")
            gateway.close()
            return 0
        gateway.session_id = args.session
    before = len(gateway.record.entries())
    try:
        result = gateway.call(args.tool, arguments, args.actor)
        print(f"RESULT {args.tool}\n{json.dumps(result, indent=2, default=str)}")
        outcome = 0
    except EndpointRefused as refusal:
        print(f"REFUSED {refusal.code}: {refusal}")
        outcome = 0
    except Exception as error:
        print(f"{type(error).__name__}: {error}")
        outcome = 1
    finally:
        entries = gateway.record.entries()[before:]
        print(f"\nJOURNAL +{len(entries)}")
        for entry in entries:
            print(f"  {entry['kind']:12} {entry['subject']:24} "
                  f"{json.dumps(entry['payload'])[:96]}")
        gateway.close()
    return outcome


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sov_surface")
    sub = parser.add_subparsers(dest="command", required=True)
    render_cmd = sub.add_parser("render", help="write the HTML surface page")
    render_cmd.add_argument("--out")
    render_cmd.set_defaults(handler=cmd_render)
    sub.add_parser("check", help="refuse a stale page").set_defaults(handler=cmd_check)
    try_cmd = sub.add_parser("try", help="call one exposed endpoint and show the journal")
    try_cmd.add_argument("tool")
    try_cmd.add_argument("arguments", nargs="*", metavar="key=value")
    try_cmd.add_argument("--actor", default="Bdo")
    try_cmd.add_argument("--session", help="reattach a session opened by an earlier call")
    try_cmd.add_argument("--state-root")
    try_cmd.set_defaults(handler=cmd_try)
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
