"""Whether the capability projection is one this service can read at all.

`discovery.py` answers what may be done here, from
`contracts/fixtures/capability-map.reference.json`. That is a projection this service
consumes and does not own: it is rebuilt by `scripts/sov_capability.py`, it arrives as
a file path on the CLI, and nothing stops a caller pointing at a different one.

So there are two jobs, and this module is the first. Deciding whether a projection is
readable is a judgement about a foreign artifact; answering from it is a judgement
about this node. Keeping them apart is what lets the answer path read a field without
guarding it, because by then every field it reads has been checked here.

Presence is not enough, and checking only presence was the first repair's defect: a
row whose `endpoints` was `[{}]` passed a presence check and then died on
`endpoint["activation"]`, which the CLI's catch-all labelled `UNKNOWN_RECORD` - a code
`console.discover-operations` does not declare, and the wrong thing to say besides,
since nothing was missing from the journal. Eleven other shapes raised `TypeError` or
`AttributeError` and printed no JSON at all. The type is part of what readable means.
"""

from __future__ import annotations

from typing import Any

from soveraeign_console_service.refusals import CapabilityMapUnreadable

#: Every field the answer path reads off the projection, with the type it reads it as.
MAP_FIELDS = {"capabilities": list, "input_state_digest": str, "status": str}
#: Every field it reads off one capability row.
ROW_FIELDS = {"capability_id": str, "service_id": str, "operation": str,
              "service_standing": str, "office": str, "counter": str,
              "actor_kinds": list, "effect_class": str, "endpoints": list,
              "required_authority": str}
#: `shape` is optional and read with `.get`, so it may be absent - but when it is there
#: it is read as an object, and `None` or a string is not one.
SHAPE_FIELD = "shape"
#: The two `shape` members read as lists.
SHAPE_LISTS = ("preconditions", "refusals")
#: Read off each endpoint. One missing `activation` used to be a bare `KeyError`.
ENDPOINT_FIELDS = {"activation": str}


def _typed(subject: str, fields: dict[str, type], record: dict[str, Any]) -> None:
    """Refuse the first field of `record` that is absent or not the type declared."""
    for key, kind in fields.items():
        if key not in record:
            raise CapabilityMapUnreadable(f"{subject} carries no {key!r}")
        if not isinstance(record[key], kind):
            raise CapabilityMapUnreadable(
                f"{subject} has {key!r} as a {type(record[key]).__name__}, "
                f"not a {kind.__name__}")


def _shape(where: str, row: dict[str, Any]) -> None:
    shape = row.get(SHAPE_FIELD, {})
    if not isinstance(shape, dict):
        raise CapabilityMapUnreadable(
            f"{where} has {SHAPE_FIELD!r} as a {type(shape).__name__}, not an object")
    for name in SHAPE_LISTS:
        if name in shape and not isinstance(shape[name], list):
            raise CapabilityMapUnreadable(
                f"{where} has {SHAPE_FIELD}.{name} as a "
                f"{type(shape[name]).__name__}, not a list")


def readable(capability_map: Any) -> None:
    """Refuse a projection this service cannot read, naming the first thing wrong.

    Every field the answer path goes on to read, checked for presence *and* type, so
    no later line there can raise an untyped error at a caller.
    """
    if not isinstance(capability_map, dict):
        raise CapabilityMapUnreadable(
            f"the capability map is a {type(capability_map).__name__}, not an object")
    _typed("the capability map", MAP_FIELDS, capability_map)
    for position, row in enumerate(capability_map["capabilities"]):
        where = f"capability row {position}"
        if not isinstance(row, dict):
            raise CapabilityMapUnreadable(
                f"{where} is a {type(row).__name__}, not an object")
        _typed(where, ROW_FIELDS, row)
        _shape(where, row)
        for index, endpoint in enumerate(row["endpoints"]):
            if not isinstance(endpoint, dict):
                raise CapabilityMapUnreadable(
                    f"{where} endpoint {index} is a {type(endpoint).__name__}, "
                    f"not an object")
            _typed(f"{where} endpoint {index}", ENDPOINT_FIELDS, endpoint)
