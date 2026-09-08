"""Resolve which names in a workflow reach `agent`, and what every binding is written from.

Split out of `calls.py` so the provenance reader can consult it too. It could not before:
`derives_from_agent_result` asked whether an expression carries something an earlier
`agent(...)` produced, and answered by matching the literal text `agent(`. This module had
already resolved `const spawn = agent` to a fixpoint for *enumeration*, so a dispatch
through an alias was found and its provenance was not. An independent reading built
exactly that - `const spawn = agent`, then a witness prompt splicing `built.summary` - and
every check passed.

Two maps, not one. `writes_by_name` answers what an expression a binding carries was
written from. `member_writes` answers only the narrower question of which object members
hold `agent`, and is consulted only by `agent_names`. They used to be one map, and the
consequence was measured on the pristine tree: `BUILD_SCHEMA` resolved to an agent result,
because a JSON Schema's `properties: { summary: ... }` keys read as bindings and the walk
arrived at the dispatch through them. A resolver that convicts a schema literal is the
defect `render.py` names - a check that convicts correct code is worse than the gap it
covers.
"""

from __future__ import annotations

from functools import lru_cache
import re

from sovprompts.scan import _statement, masked

IDENT = re.compile(r"[A-Za-z_$][\w$]*")


@lru_cache(maxsize=None)
def writes_by_name(source: str) -> dict[str, tuple[str, ...]]:
    """Every binding in this source mapped to the expressions written into it, in one pass.

    Built once rather than by scanning the whole file for each candidate name. The
    name-at-a-time form was correct and cost a second per workflow, which the defeats
    corpus turned into forty seconds of the verification budget.

    Declarations, bare reassignment and destructuring only. An object literal's `key:
    value` pairs are not bindings of `key`, and reading them as such made every JSON
    Schema in a workflow resolve to whatever its property names collided with.
    """
    out: dict[str, list[str]] = {}
    code = masked(source)
    for pattern in (r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*",
                    r"\b([A-Za-z_$][\w$]*)\s*=(?!=)\s*"):
        for match in re.finditer(pattern, code):
            out.setdefault(match.group(1), []).append(_statement(source, match.end()))
    for match in re.finditer(r"\b(?:const|let|var)\s*[{\[]([^}\]]*)[}\]]\s*=\s*", code):
        written = _statement(source, match.end())
        for piece in match.group(1).split(","):
            name = piece.strip().split(":")[-1].strip()
            if IDENT.fullmatch(name or ""):
                out.setdefault(name, []).append(written)
    return {name: tuple(writes) for name, writes in out.items()}


@lru_cache(maxsize=None)
def member_writes(source: str) -> dict[str, tuple[str, ...]]:
    """Object-literal `key: value` pairs, for the one question that needs them.

    `const holder = { spawn: agent }` puts `agent` behind a member, and `agent_names` has
    to follow it or a dispatch through `holder.spawn` is never recognised. Nothing else
    consults this: a schema's property names have the same shape and mean nothing about
    what a binding carries.
    """
    out: dict[str, list[str]] = {}
    for match in re.finditer(r"([A-Za-z_$][\w$]*)\s*:\s*([A-Za-z_$][\w$]*)\s*(?![\w$(])",
                             masked(source)):
        out.setdefault(match.group(1), []).append(match.group(2))
    return {name: tuple(writes) for name, writes in out.items()}


@lru_cache(maxsize=None)
def agent_names(source: str) -> frozenset[str]:
    """`agent` and every name bound to it, however many hops away.

    `const spawn = agent` followed by `spawn(...)` was a dispatch no sweep saw, because
    the enumerator matched the literal text `agent(`: this resolved bindings for every
    name except the name of the function it enumerates. A one-hop regex closed that and
    left five more open - a two-hop alias, a bare reassignment, a member call, a
    destructured alias, and `agent` held as an object member. A call that is never
    recognised produces no refusal, so failing closed cannot reach it, which is why this
    has to be resolution to a fixpoint rather than a pattern.
    """
    writes = dict(writes_by_name(source))
    for name, written in member_writes(source).items():
        writes[name] = writes.get(name, ()) + written
    names = {"agent"}
    changed = True
    while changed:
        changed = False
        for name, written in writes.items():
            if name in names:
                continue
            for expression in written:
                candidate = expression.strip().rstrip(";").strip()
                # `const oV = { a: agent }` then `const bV = oV.a` reads the member back
                # out. Four alias shapes were closed case by case and the class came back
                # one hop further; the member a write ends on is resolved rather than the
                # write compared whole.
                tail = candidate.rsplit(".", 1)[-1].strip() if "." in candidate else candidate
                if candidate in names or tail in names:
                    names.add(name)
                    changed = True
                    break
    return frozenset(names)


def agent_call_pattern(source: str) -> re.Pattern[str]:
    """Every way this file can reach `agent`, as one pattern.

    `derives_from_agent_result` used the literal `\\bagent\\s*\\(`. An alias defeated
    it while the enumerator resolved the same alias correctly two modules away, so a
    dispatch was found and the provenance of what it returned was not.
    """
    alternatives = "|".join(sorted(re.escape(name) for name in agent_names(source)))
    return re.compile(rf"\b(?:{alternatives})\s*(?:\.\s*(?:call|apply)\s*)?\(")


__all__ = ["agent_call_pattern", "agent_names", "member_writes", "writes_by_name"]
