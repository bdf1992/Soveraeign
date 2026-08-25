"""Check a conversation between seats against the declared etiquette table.

``contracts/seat-message.schema.json`` owns the envelope; this module owns the rules
that a valid envelope cannot express: which acts a seat may speak, in which direction,
how far each act may propose standing, and what a forwarding seat owes onward. Every
rule is read from ``contracts/seat-etiquette.json`` rather than written here, so adding
a seat type or an act is a change to that table alone.

Nothing here reads inside a message body. A conversation with no defects is admissible,
not correct: etiquette says who may say a thing, never whether it is so.
"""

from __future__ import annotations

from typing import Any

RELATION_ANY = "ANY"


def _seat_index(topology: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """seat_id -> seat record, from a seat-registry projection."""
    return {seat["seat_id"]: seat for seat in topology.get("seats", [])}


def _direction_defects(message: dict[str, Any], act: dict[str, Any],
                       seats: dict[str, dict[str, Any]], label: str) -> list[str]:
    """UPWARD reaches the speaker's owner seat; DOWNWARD reaches a seat the speaker owns."""
    speaker_id = message["speaker"]["seat_id"]
    target_id = message["to_seat"]
    if target_id not in seats:
        return [f"{label}: addressed to {target_id}, which is not a seat in the topology"]
    if act["direction"] == "UPWARD":
        owner = seats[speaker_id].get("owner_seat")
        if owner is None:
            return [f"{label}: {speaker_id} has no owner seat, so it cannot speak upward"]
        if target_id != owner:
            return [f"{label}: {message['act']} travels upward to {owner}, not to {target_id}"]
        return []
    if seats[target_id].get("owner_seat") != speaker_id:
        return [f"{label}: {message['act']} travels downward, but {speaker_id} does not own "
                f"{target_id}"]
    return []


def _standing_defects(message: dict[str, Any], act: dict[str, Any], label: str) -> list[str]:
    """A statement may propose exactly its act's ceiling, or nothing at all."""
    proposed = message.get("standing_proposed")
    ceiling = act["standing_ceiling"]
    if proposed is None:
        return []
    if ceiling is None:
        return [f"{label}: {message['act']} proposes no standing, but this one proposes "
                f"{proposed['from']} -> {proposed['to']}"]
    if proposed != ceiling:
        return [f"{label}: {message['act']} may propose at most {ceiling['from']} -> "
                f"{ceiling['to']}, not {proposed['from']} -> {proposed['to']}"]
    return []


def _message_defects(message: dict[str, Any], etiquette: dict[str, Any],
                     seats: dict[str, dict[str, Any]], label: str) -> list[str]:
    """Seat occupancy, admissible act, required relation, direction, and standing ceiling."""
    defects: list[str] = []
    speaker = message["speaker"]
    seat_id, seat_type, act_name = speaker["seat_id"], speaker["seat_type"], message["act"]

    if seat_id not in seats:
        return [f"{label}: speaks from {seat_id}, which is not a seat in the topology"]
    if seats[seat_id]["seat_type"] != seat_type:
        defects.append(f"{label}: claims seat type {seat_type}, but the topology records "
                       f"{seats[seat_id]['seat_type']} for {seat_id}")
    seat_rules = etiquette["seats"].get(seat_type)
    if seat_rules is None:
        return defects + [f"{label}: seat type {seat_type} has no declared acts"]
    act = etiquette["acts"].get(act_name)
    if act is None:
        return defects + [f"{label}: {act_name} is not a declared act"]
    if act_name not in seat_rules["may"]:
        defects.append(f"{label}: a {seat_type} seat may not {act_name}; it may "
                       f"{', '.join(seat_rules['may'])}")
    required = act["requires_relation"]
    if required != RELATION_ANY and speaker["relation_to_subject"] != required:
        defects.append(f"{label}: {act_name} requires relation {required}, but the speaker "
                       f"declares {speaker['relation_to_subject']}")
    defects.extend(_direction_defects(message, act, seats, label))
    defects.extend(_standing_defects(message, act, label))
    return defects


def _carriage_defects(message: dict[str, Any], by_id: dict[str, dict[str, Any]],
                      kinds: list[str], no_edit: bool, label: str) -> list[str]:
    """Every item in an aggregated message must reappear here, unedited."""
    defects: list[str] = []
    forwarded = message.get("aggregates")
    if not forwarded:
        return [f"{label}: aggregates nothing, so it forwards no statement"]
    carried = {kind: {item["item_id"]: item for item in message["carries"].get(kind, [])}
               for kind in kinds}
    for source_id in forwarded:
        source = by_id.get(source_id)
        if source is None:
            defects.append(f"{label}: forwards {source_id}, which is not in this conversation")
            continue
        for kind in kinds:
            for item in source["carries"].get(kind, []):
                held = carried[kind].get(item["item_id"])
                if held is None:
                    defects.append(f"{label}: drops {kind[:-1]} {item['item_id']} received "
                                   f"from {source_id}")
                elif no_edit and held != item:
                    defects.append(f"{label}: forwards {kind[:-1]} {item['item_id']} edited; "
                                   f"a carried item travels unchanged")
    return defects


def _self_witness_defects(message: dict[str, Any], earlier: list[dict[str, Any]],
                          label: str) -> list[str]:
    """An actor that performed an operation cannot later speak independently about it."""
    speaker = message["speaker"]
    if speaker["relation_to_subject"] != "INDEPENDENT":
        return []
    operation = message["subject"]["operation_id"]
    for prior in earlier:
        if (prior["speaker"]["actor_id"] == speaker["actor_id"]
                and prior["speaker"]["relation_to_subject"] == "PERFORMED"
                and prior["subject"]["operation_id"] == operation):
            return [f"{label}: {speaker['actor_id']} performed {operation} in "
                    f"{prior['message_id']} and now speaks independently about it"]
    return []


def _duty_defects(message: dict[str, Any], earlier: list[dict[str, Any]],
                  by_id: dict[str, dict[str, Any]], etiquette: dict[str, Any],
                  label: str) -> list[str]:
    """Dispatch the declared carriage duties. An undeclared duty name is itself a defect."""
    defects: list[str] = []
    carry_kinds: list[str] = []
    no_edit_kinds: list[str] = []
    for duty in etiquette["carriage_duties"]:
        name = duty["duty"]
        if name == "NO_SELF_WITNESS":
            if message["speaker"]["relation_to_subject"] == duty.get("applies_to_relation"):
                defects.extend(_self_witness_defects(message, earlier, label))
        elif name in {"CARRY_EVERYTHING_RECEIVED", "NO_EDIT_IN_TRANSIT"}:
            if message["act"] != duty.get("applies_to_act"):
                continue
            (carry_kinds if name == "CARRY_EVERYTHING_RECEIVED" else no_edit_kinds).extend(
                duty["kinds"])
        else:
            defects.append(f"{label}: etiquette declares duty {name}, which this checker "
                           f"does not implement")
    if carry_kinds or no_edit_kinds:
        kinds = sorted(set(carry_kinds) | set(no_edit_kinds))
        defects.extend(_carriage_defects(message, by_id, kinds, bool(no_edit_kinds), label))
    return defects


def conversation_defects(conversation: list[dict[str, Any]], topology: dict[str, Any],
                         etiquette: dict[str, Any]) -> list[str]:
    """Every etiquette defect in a conversation, in the order the statements were made.

    An empty list means every statement was one its speaker was entitled to make. It does
    not mean any statement is true, observed, settled, or ratified.
    """
    seats = _seat_index(topology)
    by_id: dict[str, dict[str, Any]] = {}
    defects: list[str] = []
    for index, message in enumerate(conversation):
        label = f"{message.get('message_id', index)}"
        defects.extend(_message_defects(message, etiquette, seats, label))
        defects.extend(_duty_defects(message, conversation[:index], by_id, etiquette, label))
        by_id[message["message_id"]] = message
    return defects
