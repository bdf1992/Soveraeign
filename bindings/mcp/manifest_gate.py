"""Judge the manifest before any store opens.

`gateway.py` owns the one path a call takes. This module owns the question asked
before any call is possible: does what the manifest declares line up with what this
binding can actually serve. It is a separate responsibility and a separate moment.

`validate` reads the manifest alone, before any store opens, so its refusal costs
nothing at all. `audit_handlers` cannot: it reads the signatures of handlers already
bound to live services, so by then the state directory exists and its stores are
open. `Gateway.__init__` closes them before re-raising, so a refused start leaves no
open handle - but it does leave the directory, and this file claimed otherwise.

The vocabulary lives here too, because it is what the judgement is made against:
which tiers exist, which authority modes an acting endpoint may declare, and which
endpoint names this binding has code behind.
"""

from __future__ import annotations

from inspect import Parameter, signature
from typing import Any, Callable, NewType, get_args, get_type_hints

#: A participant whose authority some service will check. Distinct from `str` so the
#: census below can tell a principal from any other string without being handed a list
#: of names. A parameter typed this way is either supplied by the dispatcher from the
#: authenticated caller, or declared as somebody the caller is naming rather than
#: claiming to be - and the manifest has to say which.
Principal = NewType("Principal", str)

TIERS = ("read", "observe", "act")
AUTHORITY_MODES = ("gateway", "service-enforced", "bootstrap")

# The endpoints this gateway can actually reach. Held as names rather than bound
# callables so the manifest can be judged before anything opens a store - `validate`
# reads this and nothing else. It is a declaration, and `audit_handlers` refuses a
# binding whose `_bind()` disagrees with it, so the two cannot drift apart.
IMPLEMENTED = (
    "authority_open_session",
    "authority_grant",
    "asset_ingest",
    "asset_search",
    "record_entries",
    "console_operations",
    "observe_verify",
)


class UnbuiltEndpoint(RuntimeError):
    """A manifest endpoint names an operation with no reachable implementation."""


def validate(endpoints: dict[str, dict[str, Any]],
              withheld: dict[str, dict[str, Any]] | None = None) -> None:
    """Judge the manifest before any store opens.

    A declared operation with nothing behind it is the failure this exists for:
    it keeps a written-but-unbuilt service visibly unbuilt instead of letting it
    become a tool that errors at call time.

    The reverse - an implementation the manifest does not declare - is normally the
    same defect read from the other side, and is admitted only when the manifest
    withholds that tool and says why. Withholding is how a built endpoint stops
    being served without the code that serves it being deleted, and a withheld
    entry with no stated reason is refused so a capability cannot quietly vanish.
    """
    withheld = withheld or {}
    missing = sorted(set(endpoints) - set(IMPLEMENTED))
    if missing:
        raise UnbuiltEndpoint(
            "manifest declares endpoints with no implementation: " + ", ".join(missing))
    for tool, entry in sorted(withheld.items()):
        if tool in endpoints:
            raise UnbuiltEndpoint(f"{tool} is both declared and withheld")
        if not entry.get("withheld_because"):
            raise UnbuiltEndpoint(f"{tool} is withheld without a stated reason")
    undeclared = sorted(set(IMPLEMENTED) - set(endpoints) - set(withheld))
    if undeclared:
        raise UnbuiltEndpoint(
            "gateway implements endpoints the manifest neither declares nor withholds: "
            + ", ".join(undeclared))
    for tool, entry in endpoints.items():
        if entry["tier"] not in TIERS:
            raise UnbuiltEndpoint(f"{tool} declares unknown tier {entry['tier']!r}")
        caller = entry.get("caller_argument")
        if caller is not None and caller in entry.get("arguments", {}):
            # Declaring it as an input invites a caller to send one, and a reader of
            # the tool schema would believe it decides something. The dispatcher
            # overwrites it, so the two together would be a contradiction on the wire.
            raise UnbuiltEndpoint(
                f"{tool} declares {caller!r} as an argument and as its caller_argument")
        if entry["tier"] != "act":
            continue
        mode = entry.get("authority")
        if mode not in AUTHORITY_MODES:
            raise UnbuiltEndpoint(f"{tool} acts but declares no authority mode")
        if (mode == "gateway") != ("capability" in entry):
            raise UnbuiltEndpoint(
                f"{tool} declares authority {mode!r}, which does not match its capability")


def _is_principal(hint: Any) -> bool:
    """Whether an annotation carries `Principal`, including inside a union.

    `is Principal` matched only the bare NewType, so `actor: Principal | None` - an
    honest annotation, and idiomatic here because two shipped handlers already take
    `float | None` - read as a plain value and passed on a single false statement.
    """
    return hint is Principal or Principal in get_args(hint)


def audit_handlers(endpoints: dict[str, dict[str, Any]],
                   handlers: dict[str, Callable[..., Any]],
                   withheld: dict[str, dict[str, Any]] | None = None,
                   implemented: tuple[str, ...] = IMPLEMENTED) -> None:
    """Judge every dispatched handler against what the manifest says about it.

    Derived, not enumerated. It walks whatever `Gateway._bind` returns and reads each
    signature, so an endpoint added tomorrow is audited without anyone editing a list.
    The check this replaces named four tools in a test, and a new endpoint taking a
    principal straight from caller arguments passed it - the enumeration failure this
    binding exists to prevent, sitting inside the fix for it.

    Two independent statements about every parameter have to agree: the Python
    annotation, and the manifest's `principal` flag. Neither may be omitted. That is
    what makes the grantee/principal distinction machine-readable rather than a matter
    for a reviewer's eye - `authority_grant.actor` is a principal the caller *names*,
    so it is declared under `subject_arguments` with a reason, while `issuer` is the
    principal the caller *is* and is supplied by the dispatcher.

    What this refuses, exactly:

    - a bound tool set that disagrees with `IMPLEMENTED`, either way;
    - a bound handler the manifest neither serves nor withholds;
    - a parameter of a bound handler, read from the undecorated signature, that is
      neither the `caller_argument` nor declared in `arguments`;
    - a declared argument carrying no `principal` boolean;
    - a `principal` boolean disagreeing with the annotation, where an annotation
      counts as a principal if it is `Principal` or a union containing it;
    - a principal taken from caller arguments without a `subject_arguments` reason.

    What it does not reach, and no reader should assume otherwise:

    - a parameter declared `"principal": false` and annotated `str` when it is in
      fact a principal. Two statements, both false, agreeing. Nothing here sees it;
    - anything about handlers this gateway does not bind, or about services those
      handlers call;
    - whether a value the caller sends is *used* as a principal downstream. This
      reads declarations and signatures, not dataflow;
    - the *classification* of a parameter added by a `functools.wraps` decorator.
      `wraps` overwrites `__annotations__`, so such a parameter has no recoverable
      annotation and only the accounting rule reaches it - which is enough to refuse
      it, but not enough to say what it carries.

    Three earlier versions of this docstring each claimed a universal the code did
    not keep, each narrower than the last. The list above is deliberately not one.
    """
    # `IMPLEMENTED` is a declaration; `handlers` is the measurement. `validate` grades
    # the manifest against the declaration alone and never against `Gateway._bind()`,
    # so a name in both the tuple and the manifest with nothing bound constructed
    # cleanly, was published by `tools()`, and raised `KeyError` when somebody called
    # it. Requiring the two to agree is the whole fix, and it is what stops this module
    # grading a declaration in the file written to end that.
    measured, declared_impl = set(handlers), set(implemented)
    if measured != declared_impl:
        raise UnbuiltEndpoint(
            "IMPLEMENTED does not match what the gateway binds: "
            f"declared-only={sorted(declared_impl - measured)} "
            f"bound-only={sorted(measured - declared_impl)}")

    withheld = withheld or {}
    for tool, handler in sorted(handlers.items()):
        entry = endpoints.get(tool)
        if entry is None:
            # A handler with no served endpoint is admitted only when it is withheld.
            # This used to `continue` unconditionally under a comment claiming
            # `validate` had required a stated reason - true only of names that reach
            # `withheld`, and a handler in neither list reached here and was waved past.
            if tool not in withheld:
                raise UnbuiltEndpoint(
                    f"{tool} is bound but the manifest neither declares nor withholds it")
            continue
        declared = entry.get("arguments", {})
        bound = entry.get("caller_argument")
        subjects = entry.get("subject_arguments", {})
        # The real signature, not the one `functools.wraps` points at.
        # `inspect.signature` follows `__wrapped__`, so a decorator that wraps a
        # handler hid every parameter it added: a wrapper taking an extra
        # `probe_actor: Principal` audited as the unwrapped function, constructed
        # cleanly, and then took that argument from the wire. `functools.partial`
        # was named as the hazard here and is not one - `get_type_hints` raises on
        # it, so it fails closed and loudly. This is the construct an author
        # actually reaches for, and it fails open.
        #
        # Hints come from the same object the parameters do. `functools.wraps`
        # overwrites `__annotations__` with the wrapped function's, so a parameter
        # the wrapper added has no recoverable annotation on either object - it is
        # caught by the accounting rule below, which needs no annotation, and its
        # classification cannot be cross-checked. That limit is in the docstring.
        hints = get_type_hints(handler)

        for name in subjects:
            if name not in declared:
                raise UnbuiltEndpoint(
                    f"{tool} declares subject argument {name!r} that it does not accept")
            if not str(subjects[name]).strip():
                raise UnbuiltEndpoint(
                    f"{tool} declares subject argument {name!r} with no stated reason")

        for name, param in signature(handler, follow_wrapped=False).parameters.items():
            if param.kind in (Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD):
                raise UnbuiltEndpoint(
                    f"{tool} takes {name!r} as a variadic, which no manifest can describe")
            typed = _is_principal(hints.get(name))
            if name == bound:
                if not typed:
                    raise UnbuiltEndpoint(
                        f"{tool} binds {name!r} to the caller but does not type it a "
                        f"Principal, so nothing states what it carries")
                continue
            if name not in declared:
                # No exemption for a default, and none for an annotation. A parameter
                # the manifest does not mention is the case with the *least* stated
                # about it, and it used to be the easiest to pass: a default sent it
                # straight to `continue` with no manifest statement read at all, so
                # `def _grants_held(self, reader: str = "operator")` with no declared
                # arguments was admitted, and dropping the annotation made that zero
                # statements rather than one. `server.py` forwards caller arguments
                # unvalidated and the dispatcher overwrites only `caller_argument`, so
                # that parameter took its value from the wire.
                raise UnbuiltEndpoint(
                    f"{tool} takes {name!r}, which the manifest does not declare and "
                    f"the dispatcher does not bind. A default does not exempt it: the "
                    f"caller can still send one")
            flagged = declared[name].get("principal")
            if not isinstance(flagged, bool):
                raise UnbuiltEndpoint(
                    f"{tool} declares {name!r} without saying whether it is a principal")
            if flagged != typed:
                raise UnbuiltEndpoint(
                    f"{tool} declares {name!r} principal={flagged} and types it "
                    f"{'a Principal' if typed else 'a plain value'}")
            if typed and name not in subjects:
                raise UnbuiltEndpoint(
                    f"{tool} takes the principal {name!r} from caller arguments "
                    f"without declaring it a subject the caller names")
