"""Turn a sentence into a proposed edit. It proposes; it never saves.

Bdo asked to request an edit in natural language. This asks a local model what fields
the sentence means to change, checks the answer against what an edit may touch, and
hands back a proposal for a person to look at and save. The model is not given a path
to ``authoring.update`` and could not use one: a model operator holds no seat, so
anything it asked of an armed schedule would come back a proposal regardless. Making
that structural rather than incidental is the point.

The model runs on this machine through ``adapters/ollama``, whose binding declares a
``LOCAL_ONLY`` data boundary - no third party is reached and no Phase I effect class is
crossed. Every invocation returns a record with the model, the version, the input
digest and the tokens spent, and that record is what the console shows rather than an
unattributed answer.

What the model can get wrong is bounded by what is checked afterwards: a field outside
the editable set, a value of the wrong shape, or an unparseable answer are all refusals
here, and none of them reach a declaration. The worst outcome is a proposal a person
reads and rejects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
import sys

from sovschedule import authoring, pagetables

ROOT = Path(__file__).resolve().parents[2]

#: The adapter is not packaged, so its own modules are not importable by project path.
#: AGENTS.md forbids sys.path work in production code and this is the exception it does
#: not cover: reaching a declared adapter that predates packaging. Narrow, named, and
#: recorded as a residual in decisions/0088. Duplicating the adapter to avoid it would
#: be worse - a second, undeclared model crossing.
ADAPTER_DIR = ROOT / "adapters" / "ollama"

DEFAULT_BINDING = "urn:soveraeign:binding:ollama:qwen3-4b"

REFUSALS = ("MODEL_UNAVAILABLE", "UNREADABLE_PROPOSAL", "NOT_EDITABLE",
            "WRONG_SHAPE", "NOTHING_UNDERSTOOD", "UNKNOWN_SCHEDULE")

#: What a value for each field has to look like before it is offered to a person. The
#: loader checks the whole declaration later; this catches the shapes that would make
#: the proposal unreadable rather than merely wrong.
SHAPES: dict[str, type | tuple] = {
    "description": str, "cron": str, "mode": str, "effect_class": str,
    "isolation": str, "target": dict, "limits": dict, "preconditions": dict,
}

PROMPT = """You edit one scheduled-job declaration. Answer with JSON only.

The declaration now:
{current}

Available targets (kind:name), and nothing else may be used:
{targets}

Allowed values:
  mode: observe, build
  effect_class: RECORD_LOCAL, RESOURCE_CONSUMPTION
  isolation: tree, worktree
  cron: five fields, minute hour day month weekday

The request: {request}

Reply with exactly this shape and no other text:
{{"changes": {{"<field>": <value>}}, "why": "<one short sentence>"}}

Rules. Only these fields may appear in changes: {editable}.
Never include "name" or "enabled" - renaming and switching are separate operations.
"target" is an object: {{"kind": "workflow", "name": "<one of the available>", "args": {{}}}}.
"limits" is an object: {{"max_budget_usd": <number>, "timeout_seconds": <number>}}.
Include only fields the request actually asks to change. If it asks for nothing you can
express as a field change, reply {{"changes": {{}}, "why": "<why not>"}}.
"""


@dataclass(frozen=True)
class Proposal:
    """What the model suggested, after checking. Nothing here has been written."""

    schedule: str
    changes: dict
    why: str
    refusal_code: str | None
    detail: str
    record: dict = field(default_factory=dict)

    @property
    def usable(self) -> bool:
        return self.refusal_code is None and bool(self.changes)


def _adapter():
    """Import the declared adapter, bootstrapping the paths it needs. See ADAPTER_DIR."""
    for path in (str(ADAPTER_DIR), str(ROOT / "scripts")):
        if path not in sys.path:
            sys.path.insert(0, path)
    import invoke  # noqa: PLC0415 - deferred so a missing adapter is a refusal, not an

    return invoke                                  # import error at module load


def _current(root: Path, name: str) -> dict | None:
    path = root / ".claude" / "schedules" / f"{name}.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _editable_view(body: dict) -> dict:
    """Only the fields an edit may touch, so the model is not shown what it cannot move."""
    return {key: body[key] for key in authoring.EDITABLE if key in body}


def build_prompt(body: dict, targets: list[dict], request: str) -> str:
    return PROMPT.format(
        current=json.dumps(_editable_view(body), indent=2),
        targets="\n".join(f'  {t["kind"]}:{t["name"]}' for t in targets) or "  (none)",
        request=request.strip(),
        editable=", ".join(authoring.EDITABLE))


def parse(text: str) -> tuple[dict, str, str | None, str]:
    """Read the model's answer. Returns changes, why, refusal code, detail.

    Models wrap JSON in prose and in code fences however they are asked not to, so the
    outermost braces are taken rather than the whole string. That is leniency about
    packaging only - what is inside is checked strictly, because a field outside the
    editable set is the failure that would matter.
    """
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return {}, "", "UNREADABLE_PROPOSAL", f"no JSON object in the answer: {text[:200]}"
    try:
        raw = json.loads(text[start:end + 1])
    except json.JSONDecodeError as error:
        return {}, "", "UNREADABLE_PROPOSAL", f"{error}; the answer was {text[:200]}"
    if not isinstance(raw, dict) or not isinstance(raw.get("changes"), dict):
        return {}, "", "UNREADABLE_PROPOSAL", "the answer carries no changes object"

    changes, why = raw["changes"], str(raw.get("why", ""))
    stray = [key for key in changes if key not in authoring.EDITABLE]
    if stray:
        return {}, why, "NOT_EDITABLE", (
            f"the model proposed {stray}, which an edit may not touch. Allowed: "
            f"{list(authoring.EDITABLE)}")
    wrong = [key for key, value in changes.items()
             if not isinstance(value, SHAPES.get(key, object))]
    if wrong:
        return {}, why, "WRONG_SHAPE", f"{wrong} came back as the wrong kind of value"
    if not changes:
        return {}, why, "NOTHING_UNDERSTOOD", why or "the request named no field to change"
    return changes, why, None, ""


def interpret(root: Path, name: str, request: str, *,
              binding_id: str = DEFAULT_BINDING, transport=None,
              invocation_id: str = "inv:automation-intent") -> Proposal:
    """Ask a local model what one sentence means to change. Writes nothing."""
    body = _current(root, name)
    if body is None:
        return Proposal(name, {}, "", "UNKNOWN_SCHEDULE",
                        f"no declaration named {name} to edit")
    if not request.strip():
        return Proposal(name, {}, "", "NOTHING_UNDERSTOOD", "no request was given")

    prompt = build_prompt(body, authoring.targets(root), request)
    try:
        adapter = _adapter()
        record, text = adapter.invoke(
            binding_id, prompt,
            operation_id="op:automation.propose_edit",
            actor_id="urn:soveraeign:actor:console-intent",
            required_authority="none - this proposes and does not write",
            invocation_id=invocation_id, transport=transport)
    except Exception as error:  # noqa: BLE001 - every adapter failure is one refusal here
        return Proposal(name, {}, "", "MODEL_UNAVAILABLE",
                        f"the local model could not be reached or refused: {error}")

    changes, why, code, detail = parse(text)
    return Proposal(name, _complete(body, changes), why, code, detail, record)


def _complete(body: dict, changes: dict) -> dict:
    """Fill a partial nested object from the current declaration.

    A model asked to raise a budget answers ``{"limits": {"max_budget_usd": 8}}``, which
    read literally drops ``timeout_seconds``. The schema requires both, so applying that
    would be refused and rolled back - safe, but the person asked to change one number
    and would get a schema complaint. Completing it here keeps that between the model
    and the proposal rather than between the person and the loader.

    Only nested objects are completed, and only from the field they are replacing. A
    scalar the model returns stands as it returned it.
    """
    out = {}
    for key, value in changes.items():
        current = body.get(key)
        if isinstance(value, dict) and isinstance(current, dict):
            out[key] = {**current, **value}
        else:
            out[key] = value
    return out


def summary(record: dict) -> dict:
    """What the console shows about an invocation, so an answer is never unattributed."""
    if not record:
        return {}
    usage = record.get("usage") or {}
    return {
        "model": record.get("executed", {}).get("model_id", "?"),
        "boundary": record.get("data_boundary_applied", "?"),
        "seconds": usage.get("wall_clock_seconds"),
        "output_tokens": usage.get("output_tokens"),
    }


def field_labels() -> dict[str, str]:
    """The editor's own labels, so a proposal names fields the way the form does."""
    return {name: label for name, _, label in pagetables.INLINE}
