"""Judge the receipt event names a service emits against the capability map.

A receipt is the record of one attempted crossing (`CONTRACT.md` C8), and the
event name on it is the only thing saying *which* operation was attempted. When
that name is not the operation's canonical identifier, a receipt cannot be joined
to the map that says what the operation costs, who may ask for it, and where it
is reachable - so the node can say what happened and not what it was doing.

Observed 2026-08-24: the Console emitted its capability identifiers exactly and
the Asset Service emitted seven different ones (`asset.ingest` against a declared
`asset.ingest-asset`), and nothing checked either. The founding baseline had
already carried the question - `reports/2026-08-22-baseline.md` item 24, "canonical
asset event name" - as an open naming choice for two days.

This module reads what the source actually passes, not what a table claims. It
parses each service's own modules and collects every event-shaped string literal
handed to a receipt-emitting call. An event must then be one of two things:

- a `capability_id` the map declares for that service; or
- listed in the service manifest's `undeclared_events` with a stated reason.

The second is not a loophole. It is the shape `bindings/mcp/manifest.json` already
uses for a tool that realizes no declared operation: record the gap where a reader
will find it rather than inventing an operation to close it. An entry that stops
being emitted is a defect too, so the list cannot quietly outlive its reason.

Nothing here grants anything, and a passing check says only that names agree.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import ast
import re


#: Calls whose string arguments may carry a receipt event name. Every service
#: reaches its journal through one of these, directly or through its own one-line
#: wrapper; a new emitter must be added here or its events are invisible to the
#: check. `check_emitter_coverage` refuses a service whose source reaches a
#: journal through a name this set does not carry.
EMITTING_CALLS = frozenset({"receipt", "_receipt", "emit", "_emit", "refuse", "_refuse"})

#: The shape of a capability identifier (`contracts/capability-map.schema.json`)
#: and therefore of any event that claims to be one.
EVENT_SHAPE = re.compile(r"^[a-z][a-z0-9-]*\.[a-z][a-z0-9-]*$")

#: Dotted lowercase strings that are plainly not events. A module name reaching a
#: receipt call as a payload value would otherwise read as an event.
NOT_EVENTS = re.compile(r"\.(py|json|md|yaml|yml|html|ndjson|sqlite3?|txt)$")


def _call_name(node: ast.Call) -> str | None:
    """The bare name of the function being called, attribute or plain."""
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return None


def _module_constants(tree: ast.Module) -> dict[str, str]:
    """Module-level `NAME = "value"` bindings, so a named event is not invisible.

    The Console binds `POST_OPERATION = "console.post"` and passes the name. An
    event referred to by a constant is still an event the service emits, and a
    check that only saw literals would report that service as emitting nothing.
    """
    constants: dict[str, str] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not isinstance(node.value, ast.Constant) or not isinstance(node.value.value, str):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                constants[target.id] = node.value.value
    return constants


def _event_arguments(node: ast.Call, constants: dict[str, str]) -> list[str]:
    """Every event-shaped string reaching one call, as a literal or a module constant."""
    found = []
    for argument in list(node.args) + [keyword.value for keyword in node.keywords]:
        if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
            value = argument.value
        elif isinstance(argument, ast.Name) and argument.id in constants:
            value = constants[argument.id]
        else:
            continue
        if EVENT_SHAPE.match(value) and not NOT_EVENTS.search(value):
            found.append(value)
    return found


def emitted_events(source_root: Path, repository_root: Path) -> dict[str, list[str]]:
    """Map each emitted event name to the sorted addresses that emit it.

    Reads the service's own modules. A service that emitted an event through a
    computed name would be invisible here, which is why `EMITTING_CALLS` is a
    closed set and every current emitter passes a literal.
    """
    found: dict[str, list[str]] = {}
    for module in sorted(source_root.rglob("*.py")):
        if "__pycache__" in module.parts:
            continue
        tree = ast.parse(module.read_bytes().decode("utf-8"), filename=str(module))
        address = module.relative_to(repository_root).as_posix()
        constants = _module_constants(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or _call_name(node) not in EMITTING_CALLS:
                continue
            for event in _event_arguments(node, constants):
                found.setdefault(event, []).append(f"{address}:{node.lineno}")
    return {event: sorted(set(sites)) for event, sites in sorted(found.items())}


def _declared_undeclared(manifest: dict[str, Any]) -> dict[str, str]:
    """The manifest's own record of events that realize no declared operation."""
    return {entry["event"]: entry["because"]
            for entry in manifest.get("undeclared_events", [])}


def service_defects(service_id: str, manifest: dict[str, Any], emitted: dict[str, list[str]],
                    capability_ids: set[str]) -> list[str]:
    """Judge one service's emitted vocabulary against the map and its own manifest."""
    defects: list[str] = []
    excused = _declared_undeclared(manifest)
    for event, sites in emitted.items():
        where = sites[0]
        if event in capability_ids:
            if not event.startswith(f"{service_id}."):
                defects.append(
                    f"FOREIGN_CAPABILITY_EVENT: {service_id} emits {event!r} at {where}, "
                    f"which is another service's capability"
                )
            continue
        if event in excused:
            continue
        defects.append(
            f"UNMAPPED_EVENT: {service_id} emits {event!r} at {where}, which is neither a "
            f"declared capability nor listed in undeclared_events"
        )
    for event in sorted(excused):
        if event in capability_ids:
            defects.append(
                f"EXCUSED_BUT_DECLARED: {service_id} lists {event!r} in undeclared_events "
                f"while the map declares it as a capability"
            )
        elif event not in emitted:
            defects.append(
                f"STALE_UNDECLARED_EVENT: {service_id} lists {event!r} in undeclared_events "
                f"and no longer emits it"
            )
    return defects


def run(repository_root: Path, capability_map: dict[str, Any],
        manifests: dict[str, dict[str, Any]]) -> tuple[list[str], dict[str, dict[str, list[str]]]]:
    """Judge every service that ships source. Returns defects and what was harvested."""
    capability_ids = {row["capability_id"] for row in capability_map["capabilities"]}
    defects: list[str] = []
    harvested: dict[str, dict[str, list[str]]] = {}
    for service_id, manifest in sorted(manifests.items()):
        source_root = repository_root / "services" / service_id / "src"
        if not source_root.is_dir():
            continue
        emitted = emitted_events(source_root, repository_root)
        harvested[service_id] = emitted
        defects.extend(service_defects(service_id, manifest, emitted, capability_ids))
    return defects, harvested
