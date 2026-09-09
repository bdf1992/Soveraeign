"""Find every way `agent` is reached that the dispatch enumerator cannot follow into a call.

Split from `audit.py` at the line ceiling `ENGINEERING.md` sets, along the boundary that
was already there: that module grades the dispatches this package can read, and this one
answers what happens to the ones it cannot. Nine readings closed nine ways of reaching
`agent` under another name; the ninth found six more at once - a computed member, the
comma operator, an array index, `bind`, a conditional, an object member read back - each a
dispatch node executes and each returning no violation, because a call never recognised
cannot be refused.
"""

from __future__ import annotations

import re

from sovprompts.names import agent_names as _agent_names, writes_by_name as _writes_by_name
from sovprompts.scan import masked


def escaped_agent_references(source: str) -> list[str]:
    """Every place `agent` reaches an expression this reader cannot follow into a call.

    The enumerator finds dispatches by name, and nine readings closed nine ways of reaching
    `agent` under another one. The ninth found six more - a computed member, the comma
    operator, an array index, `bind`, a conditional, an object member read back - each a
    dispatch node executes and each returning no violation, because a call never
    recognised cannot be refused. Following one more construction closes one instance and
    leaves the class open, so this refuses the class: an occurrence is accounted for when
    it is called directly, or when it is the whole right-hand side of a binding the
    fixpoint already resolved. Anything else is reported rather than followed.
    """
    code = masked(source)
    out: list[str] = []
    for call in re.finditer(r"\beval\s*\(", code):
        # `eval('agent')(prompt, ...)` dispatches a real witness and reports nothing:
        # `masked` blanks string contents by design, so no name occurrence exists to find.
        # Direct eval sees lexical scope, so this is not host-specific. A workflow has no
        # reason to reach its own bindings by name at runtime, and a reader that cannot
        # see through it refuses it rather than claiming a boundary it does not hold.
        # Every `eval`, not the first. This returned on the first one, discarding every
        # other escape in the file including the ones below; an independent reading found
        # it. One refusal is enough to refuse a file and is not enough to describe it, and
        # a reader that stops at the first finding teaches the next reader to hide behind
        # a decoy.
        line = code[:call.start()].count("\n") + 1
        out.append(f"line {line}: `eval` can reach any binding by name, including `agent`, "
                   "and nothing here can read what it dispatches")
    names = _agent_names(source)
    writes = _writes_by_name(source)
    accounted = {name: {written.strip().rstrip(";").strip() for written in items}
                 for name, items in writes.items()}
    for name in sorted(names):
        for match in re.finditer(rf"\b{re.escape(name)}\b", code):
            after = code[match.end():match.end() + 24].lstrip()
            if after.startswith("(") or after.startswith(".call") or after.startswith(".apply"):
                continue
            statement = code[max(0, match.start() - 80):match.end()]
            target = re.search(r"([A-Za-z_$][\w$]*)\s*[:=]\s*$",
                               statement[:len(statement) - len(name)])
            if target and target.group(1) in names:
                continue
            if re.search(r"\b(?:const|let|var)\s+$", statement[:len(statement) - len(name)]):
                continue
            if any(name == value for values in accounted.values() for value in values) and (
                    re.search(r"[:=]\s*$", statement[:len(statement) - len(name)])):
                continue
            line = code[:match.start()].count("\n") + 1
            out.append(f"line {line}: `{name}` reaches an expression this cannot follow "
                       "into a call, so no rule reaches whatever it dispatches")
    return out
