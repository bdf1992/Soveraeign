"""What may be done at the local door, by a click or by a model, through one table.

`CALLS` is every operation the Console Service exposes here, by name. `NODE_ACTS`
is the pair of acts on the store itself, which run with no service open because
they replace the store a service would otherwise be holding. `operations` is the
discovery answer both a page and a model build their controls from.

Nothing here decides anything: every commit and every refusal is the Console
Service's, appended to the journal before this module returns. `views.py` owns
what may be read; `serve.py` owns the HTTP dispatch over both.
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator
import json
import shutil
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "services" / "console" / "src"))
sys.path.insert(0, str(ROOT / "services" / "record" / "src"))
sys.path.insert(0, str(HERE))

from soveraeign_console_service import ConsoleRefusal, ConsoleService  # noqa: E402
from soveraeign_record_service import RecordService  # noqa: E402

import content  # noqa: E402
import seed as seeder  # noqa: E402

STORE = ROOT / ".local" / "console"
NODE = "node:local"
SURFACE_BINDING = "binding:console-surface"


@contextmanager
def console() -> Iterator[ConsoleService]:
    """A service over the journal for the length of one call, then closed.

    State lives in the journal, not in this process, so nothing is kept between
    calls. The connection is closed on the way out: a handle held open per request
    would pile up until the store could not be replaced, which is exactly how the
    seeder first failed on Windows.
    """
    record = RecordService(STORE / "journal")
    try:
        yield ConsoleService(record, STORE, NODE)
    finally:
        record.db.close()


# ---- the operation registry the surface renders itself from -----------------

def _post(svc: ConsoleService, i: dict[str, Any]) -> dict[str, Any]:
    return svc.post(i["session_id"], i["thread_id"], i["body"].encode("utf-8"),
                    i.get("mentions", ()), bool(i.get("claims")), i.get("proposal_id"))


# Each entry is the call and the inputs it takes, in one place, because those two
# facts go wrong together. This used to import a declared tuple from the service's
# `continuity` module; that tuple moved when discovery was rebuilt around the
# capability map, and a door that cannot start because a list it reads was
# refactored elsewhere is a door with a dependency it never needed. What this door
# dispatches is the door's own fact. Capability and scope still come from the
# service contract, which is where they are decided.
CALLS = {
    "console.open-channel": (
        lambda s, i: s.open_channel(i["operator_id"], i["name"], i["domain"]),
        ["operator_id", "name", "domain"]),
    "console.open-thread": (
        lambda s, i: s.open_thread(i["operator_id"], i["channel_id"], i["title"],
                                   i.get("pinned_address"), i.get("pinned_digest")),
        ["operator_id", "channel_id", "title", "pinned_address?", "pinned_digest?"]),
    "console.archive-thread": (
        lambda s, i: s.archive_thread(i["operator_id"], i["thread_id"]),
        ["operator_id", "thread_id"]),
    "console.publish-thread": (
        lambda s, i: s.publish_thread(i["operator_id"], i["thread_id"]),
        ["operator_id", "thread_id"]),
    "console.withdraw-publication": (
        lambda s, i: s.withdraw_publication(i["operator_id"], i["publication_id"]),
        ["operator_id", "publication_id"]),
    "console.open-session": (
        lambda s, i: s.open_session(i["operator_id"], i["actor_kind"], i["binding_id"]),
        ["operator_id", "actor_kind", "binding_id"]),
    "console.close-session": (
        lambda s, i: s.close_session(i["session_id"]), ["session_id"]),
    "console.post": (
        _post, ["session_id", "thread_id", "body", "mentions?", "claims?", "proposal_id?"]),
    "console.grant": (
        lambda s, i: s.grant(i["operator_id"], i["capability"], i["scope"]),
        ["operator_id", "capability", "scope"]),
}


# ---- acts on the store itself, dispatched with no service open ---------------
#
# A console that can only be filled or emptied by a command typed somewhere else
# has moved its own first move onto the person. These do it. They are handled
# before a service is opened because Windows will not let the store be replaced
# while a SQLite handle is on it.

def _fill(_inputs: dict[str, Any]) -> dict[str, Any]:
    """Rebuild the store from the repository's actual state, through the service."""
    summary = seeder.seed(STORE)
    return {"act": "console.fill", **summary}


def _empty(inputs: dict[str, Any]) -> dict[str, Any]:
    """Drop the store and leave a new, empty journal in its place.

    A new journal, not a rewritten one: append-preserving holds within a journal,
    and emptying the node starts a different one rather than erasing this one's
    entries in place.

    It asks to be meant. This is the one act on the door that destroys records, and
    the surface renders a control for every declared operation, so without the word
    a stray press would drop a journal nobody agreed to drop.
    """
    if inputs.get("confirm") != "empty":
        raise PermissionError("say confirm=empty; this drops every entry in the store")
    if STORE.exists():
        shutil.rmtree(STORE)
    with console() as svc:
        svc.record.reconstruct()
    return {"act": "console.empty", "store": str(STORE), "entries": 0}


NODE_ACTS = {"console.fill": _fill, "console.empty": _empty}


def _contract() -> dict[str, dict[str, Any]]:
    """The service's own declaration, by operation name, for what it decides.

    The door decides what it dispatches and with which inputs; the contract decides
    what an operation costs in authority and how it refuses. Reading both keeps the
    answer from becoming a hand-maintained list that is wrong the first time an
    operation moves.
    """
    path = ROOT / "services" / "console" / "contracts" / "service.json"
    declared = json.loads(path.read_text(encoding="utf-8"))["operations"]
    return {"console." + op["operation"]: op for op in declared}


def operations() -> dict[str, Any]:
    """What may be done here, and what each operation requires.

    The same answer a model gets, built from what this door dispatches and what the
    service contract says each of those costs. `grant`, `fill` and `empty` are added
    because this door exposes them and the contract does not declare them; saying so
    is cheaper than a surface that can do something its own declaration denies.
    """
    contract = _contract()
    declared = []
    for name, (_call, inputs) in CALLS.items():
        said = contract.get(name, {})
        declared.append({"operation": name, "inputs": inputs, "callable_here": True,
                         "standing": said.get("standing"),
                         "preconditions": said.get("preconditions", []),
                         "refusals": said.get("refusals", []),
                         "declared_in_contract": name in contract})
    declared.append({"operation": "console.grant", "capability": None, "scope": None,
                     "inputs": ["operator_id", "capability", "scope"], "callable_here": True})
    declared.append({"operation": "console.fill", "capability": None, "scope": None,
                     "inputs": [], "callable_here": True,
                     "note": "rebuild the store from the repository's state"})
    declared.append({"operation": "console.empty", "capability": None, "scope": None,
                     "inputs": ["confirm"], "callable_here": True,
                     "note": "drop the store and start a new, empty journal; "
                             "destroys records, so confirm must be the word empty"})
    return {"node_id": NODE, "operations": declared, "entry_standing": "RECORDED",
            "note": "a console record never enters above RECORDED",
            "call": {"method": "POST", "path": "/api/call",
                     "body": {"operation": "<name>", "inputs": {}},
                     "refusal": "HTTP 409 with reason_code and the receipt it wrote"}}
