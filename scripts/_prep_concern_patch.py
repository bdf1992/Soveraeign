from __future__ import annotations

from pathlib import Path
import re
import textwrap

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")


def replace(path: str, old: str, new: str) -> None:
    text = read(path)
    if old not in text:
        raise SystemExit(f"missing replacement anchor in {path}: {old[:120]!r}")
    write(path, text.replace(old, new, 1))


def append_once(path: str, marker: str, block: str) -> None:
    text = read(path)
    if marker in text:
        return
    write(path, text.rstrip() + "\n\n" + textwrap.dedent(block).strip() + "\n")


write(
    "scripts/sovsession/concerns.py",
    textwrap.dedent(
        '''
        """Open-addressed concern attribution for repository sessions.

        A concern tells us what a session is serving. It is attribution and routing,
        never authority. The vocabulary is deliberately open: Phase 1.5 can exercise
        a small set of concerns while later citizens can mint new addresses without a
        kernel enum or code change.
        """

        from __future__ import annotations

        from pathlib import Path
        from typing import Any, Iterable
        import os
        import uuid

        from sovsession import store


        def _text(value: object) -> str:
            return str(value or "").strip()


        def _refs(values: Iterable[str] | None, env_name: str) -> list[str]:
            """Merge explicit references with comma-separated host hints."""
            candidates = list(values or [])
            candidates.extend(item.strip() for item in os.environ.get(env_name, "").split(","))
            result: list[str] = []
            for item in candidates:
                value = _text(item)
                if value and value not in result:
                    result.append(value)
            return result


        def resolve(explicit: str | None, session: str) -> tuple[str, str]:
            """Resolve one concern without imposing a closed concern vocabulary."""
            if _text(explicit):
                return _text(explicit), "EXPLICIT"
            if _text(os.environ.get("SOV_CONCERN")):
                return _text(os.environ["SOV_CONCERN"]), "ENVIRONMENT"
            return "concern:session/" + session, "SESSION_FALLBACK"


        def session_fields(session: str, explicit: str | None = None,
                           source_session: str | None = None,
                           sources: Iterable[str] | None = None,
                           queues: Iterable[str] | None = None) -> dict[str, Any]:
            """The concern lineage a registration event carries."""
            concern_id, binding_source = resolve(explicit, session)
            return {
                "concern": concern_id,
                "concern_binding_source": binding_source,
                "source_session": _text(source_session) or _text(os.environ.get("SOV_SOURCE_SESSION")),
                "source_refs": _refs(sources, "SOV_SOURCES"),
                "queue_refs": _refs(queues, "SOV_QUEUES"),
            }


        def binding_defect(existing: dict[str, Any] | None, proposed: str) -> str | None:
            """A live session may enrich context but may not silently change concern."""
            current = _text((existing or {}).get("concern"))
            if current and proposed and current != proposed and (existing or {}).get("live"):
                return f"SESSION_CONCERN_IMMUTABLE: {current} -> {proposed}"
            return None


        def record_route(directory: Path, session_record: dict[str, Any], destination: str,
                         sources: Iterable[str] | None = None, queue_ref: str = "",
                         disposition: str = "PENDING") -> dict[str, Any]:
            """Record a concern crossing without admitting work, custody, or authority."""
            source_concern = _text(session_record.get("concern"))
            destination = _text(destination)
            if not source_concern or not destination:
                raise ValueError("a concern route needs source and destination concerns")
            event = {
                "event": "concern-route",
                "route_id": "route:" + uuid.uuid4().hex,
                "session": _text(session_record.get("session")),
                "source_session": _text(session_record.get("source_session")),
                "source_concern": source_concern,
                "destination_concern": destination,
                "source_refs": _refs(sources, "SOV_SOURCES"),
                "queue_ref": _text(queue_ref),
                "disposition": _text(disposition) or "PENDING",
                "authority_effect": "NONE",
                "custody_effect": "NONE",
            }
            return store.append(directory, store.CONCERN_ROUTES_LOG, event)


        def routes(directory: Path) -> list[dict[str, Any]]:
            return list(store.read(directory, store.CONCERN_ROUTES_LOG))


        def enumerate_concerns(directory: Path) -> list[str]:
            """Enumerate observed addresses; an unused directory is naturally empty."""
            found: set[str] = set()
            for event in store.read(directory, store.SESSIONS_LOG):
                value = _text(event.get("concern"))
                if value:
                    found.add(value)
            for event in routes(directory):
                for key in ("source_concern", "destination_concern"):
                    value = _text(event.get(key))
                    if value:
                        found.add(value)
            return sorted(found)


        def available_skills(root: Path) -> list[str]:
            """Discover skills from repository bytes rather than a hardcoded domain list."""
            directory = root / ".claude" / "skills"
            if not directory.is_dir():
                return []
            return sorted(entry.name for entry in directory.iterdir()
                          if entry.is_dir() and (entry / "SKILL.md").is_file())
        '''
    ).lstrip(),
)

write(
    "scripts/sovsession/work_context.py",
    textwrap.dedent(
        '''
        """Concern-scoped session commands split out of commands.py."""

        from __future__ import annotations

        from pathlib import Path
        import json
        import os

        from sovsession import brief, concerns, principals, store


        def register(root: Path, directory: Path, name: str, tree: str, args) -> int:
            fields = concerns.session_fields(name, args.concern, args.source_session,
                                             args.sources, args.queues)
            existing = store.sessions(directory).get(name)
            defect = concerns.binding_defect(existing, fields["concern"])
            if defect:
                payload = {"decision": "REFUSED", "reason": defect, "session": name}
                print(json.dumps(payload, indent=2, sort_keys=True) if args.as_json else defect)
                return 1
            claim = principals.resolve(root, name)
            store.append(directory, store.SESSIONS_LOG, {
                "event": "register", "session": name,
                "principal": claim["principal"], "verification": claim["verification"],
                "pid": int(os.environ.get("CLAUDE_PID", 0) or 0),
                "tree": tree, "branch": brief.branch_of(root), "intent": args.intent or "",
                **fields,
            })
            data = brief.collect(root, directory, name, tree)
            print(json.dumps(data, indent=2, sort_keys=True) if args.as_json else brief.render(data))
            return 0


        def route(directory: Path, name: str, args) -> int:
            record = store.sessions(directory).get(name) or {}
            if not record.get("registered"):
                message = "SESSION_NOT_REGISTERED: register before routing a concern crossing"
                print(json.dumps({"decision": "REFUSED", "reason": message}, indent=2)
                      if args.as_json else message)
                return 1
            event = concerns.record_route(directory, record, args.to_concern, args.sources,
                                          args.queue or "", args.disposition or "PENDING")
            print(json.dumps(event, indent=2, sort_keys=True) if args.as_json
                  else f"{event['route_id']}: {event['source_concern']} -> {event['destination_concern']}")
            return 0


        def console(root: Path, directory: Path, name: str, tree: str, args) -> int:
            data = brief.collect(root, directory, name, tree)
            print(json.dumps(data, indent=2, sort_keys=True)
                  if args.as_json else brief.render_console(data))
            return 0
        '''
    ).lstrip(),
)

replace(
    "scripts/sovsession/store.py",
    "Two logs:\n\n  sessions.ndjson  register / heartbeat / end, one line per event\n  claims.ndjson    claim / release, one line per event\n",
    "Three logs:\n\n  sessions.ndjson        register / heartbeat / end, one line per event\n  claims.ndjson          claim / release, one line per event\n  concern-routes.ndjson  open-addressed concern crossings; no authority or custody\n",
)
replace(
    "scripts/sovsession/store.py",
    'SESSIONS_LOG = "sessions.ndjson"\nCLAIMS_LOG = "claims.ndjson"\n',
    'SESSIONS_LOG = "sessions.ndjson"\nCLAIMS_LOG = "claims.ndjson"\nCONCERN_ROUTES_LOG = "concern-routes.ndjson"\n',
)
replace(
    "scripts/sovsession/claims.py",
    '        record["branch"] = live.get(session, {}).get("branch", "")\n        by_path.setdefault(path, []).append(record)\n',
    '        record["branch"] = live.get(session, {}).get("branch", "")\n        record["concern"] = live.get(session, {}).get("concern", "")\n        by_path.setdefault(path, []).append(record)\n',
)

replace(
    "scripts/sovsession/commands.py",
    "from sovsession import worktrees as wtmod\n",
    "from sovsession import worktrees as wtmod\nfrom sovsession import work_context\n",
)
replace(
    "scripts/sovsession/commands.py",
    '''def cmd_register(args: argparse.Namespace) -> int:
    """Record that this session is live, and print the briefing it should read."""
    root, directory, name, tree = _context(args.name)
    claim = principals.resolve(root, name)
    store.append(directory, store.SESSIONS_LOG, {
        "event": "register",
        "session": name,
        "principal": claim["principal"],
        "verification": claim["verification"],
        "pid": int(os.environ.get("CLAUDE_PID", 0) or 0),
        "tree": tree,
        "branch": briefmod.branch_of(root),
        "intent": args.intent or "",
    })
    data = briefmod.collect(root, directory, name, tree)
    _emit(data, args.as_json, briefmod.render(data))
    return 0
''',
    '''def cmd_register(args: argparse.Namespace) -> int:
    """Record one immutable concern-bound session and print its starting context."""
    return work_context.register(*_context(args.name), args)


def cmd_route(args: argparse.Namespace) -> int:
    """Record cross-concern egress; destination intake remains separate."""
    _, directory, name, _ = _context(args.name)
    return work_context.route(directory, name, args)


def cmd_console(args: argparse.Namespace) -> int:
    """Project this session's concern, sources, queues, skills, and routes."""
    return work_context.console(*_context(args.name), args)
''',
)
replace(
    "scripts/sovsession/commands.py",
    '        loader.loadTestsFromName("tests.test_sov_session_guard"),\n',
    '        loader.loadTestsFromName("tests.test_sov_session_guard"),\n'
    '        loader.loadTestsFromName("tests.test_session_concerns"),\n',
)

replace(
    "scripts/sov_session.py",
    '    register.add_argument("--intent", help="what this session is building")\n',
    '    register.add_argument("--intent", help="what this session is building")\n'
    '    register.add_argument("--concern", help="open concern address; attribution, never authority")\n'
    '    register.add_argument("--source-session", help="session that sourced this session")\n'
    '    register.add_argument("--source", dest="sources", action="append", help="source address; repeatable")\n'
    '    register.add_argument("--queue", dest="queues", action="append", help="available queue reference; repeatable")\n',
)
replace(
    "scripts/sov_session.py",
    '    subparsers.add_parser(\n        "brief", help="the starting-session briefing").set_defaults(handler=commands.cmd_brief)\n',
    '    subparsers.add_parser(\n        "brief", help="the starting-session briefing").set_defaults(handler=commands.cmd_brief)\n'
    '    subparsers.add_parser(\n        "console", help="concern-scoped internal work console").set_defaults(handler=commands.cmd_console)\n\n'
    '    route = subparsers.add_parser("route", help="record work sourced for another concern")\n'
    '    route.add_argument("--to", dest="to_concern", required=True, help="destination concern address")\n'
    '    route.add_argument("--source", dest="sources", action="append", help="source address; repeatable")\n'
    '    route.add_argument("--queue", help="destination queue reference if known")\n'
    '    route.add_argument("--disposition", default="PENDING", help="open disposition word; not a closed enum")\n'
    '    route.set_defaults(handler=commands.cmd_route)\n',
)

replace(
    "scripts/sovsession/brief.py",
    "from sovsession import claims, guard, phase_context, principals, store\n",
    "from sovsession import claims, concerns, guard, phase_context, principals, store\n",
)
replace(
    "scripts/sovsession/brief.py",
    '        "intent": own.get("intent", ""),\n',
    '        "intent": own.get("intent", ""),\n'
    '        "concern": own.get("concern") or concerns.resolve(None, session)[0],\n'
    '        "concern_binding_source": own.get("concern_binding_source", "SESSION_FALLBACK"),\n'
    '        "source_session": own.get("source_session", ""),\n'
    '        "source_refs": own.get("source_refs", []),\n'
    '        "queue_refs": own.get("queue_refs", []),\n'
    '        "skills": concerns.available_skills(root),\n'
    '        "concern_routes": concerns.routes(directory),\n',
)
replace(
    "scripts/sovsession/brief.py",
    'def _phase(lines: list[str], data: dict[str, Any]) -> None:\n',
    '''def _work_context(lines: list[str], data: dict[str, Any]) -> None:
    """Show attribution/routing without confusing it with authority."""
    lines.append(f"  concern: {data['concern']} ({data['concern_binding_source']}; attribution/routing only)")
    if data.get("source_session"):
        lines.append(f"  source session: {data['source_session']}")
    if data.get("queue_refs"):
        lines.append("  available queues: " + ", ".join(data["queue_refs"][:6]))
    if data.get("source_refs"):
        lines.append("  sources: " + ", ".join(data["source_refs"][:6]))
    lines.append(f"  discoverable skills: {len(data.get('skills') or [])} under .claude/skills/")


def _phase(lines: list[str], data: dict[str, Any]) -> None:
''',
)
replace(
    "scripts/sovsession/brief.py",
    '        lines.append(f"  intent: {data[\'intent\'] or \'(not registered)\'}")\n        _phase(lines, data["phase"])\n',
    '        lines.append(f"  intent: {data[\'intent\'] or \'(not registered)\'}")\n'
    '        _work_context(lines, data)\n'
    '        _phase(lines, data["phase"])\n',
)
replace(
    "scripts/sovsession/brief.py",
    '    lines.append(f"  intent: {data[\'intent\'] or \'(not registered)\'}")\n    _phase(lines, data["phase"])\n',
    '    lines.append(f"  intent: {data[\'intent\'] or \'(not registered)\'}")\n'
    '    _work_context(lines, data)\n'
    '    _phase(lines, data["phase"])\n',
)
append_once(
    "scripts/sovsession/brief.py",
    "def render_console(",
    '''
    def render_console(data: dict[str, Any]) -> str:
        """Detailed local work projection: concern, sources, queues, skills, crossings."""
        lines = [render(data), "", "Work console (projection; grants no authority)"]
        lines.append("  concern: " + str(data.get("concern") or ""))
        lines.append("  source session: " + str(data.get("source_session") or "(none)"))
        lines.append("  sources: " + (", ".join(data.get("source_refs") or []) or "(none)"))
        lines.append("  queues: " + (", ".join(data.get("queue_refs") or []) or "(none)"))
        lines.append("  skills: " + (", ".join(data.get("skills") or []) or "(none)"))
        concern = data.get("concern")
        related = [route for route in data.get("concern_routes") or []
                   if concern in (route.get("source_concern"), route.get("destination_concern"))]
        lines.append(f"  concern routes: {len(related)}")
        for route in related[-8:]:
            lines.append("    " + str(route.get("route_id")) + ": "
                         + str(route.get("source_concern")) + " -> "
                         + str(route.get("destination_concern")) + " ["
                         + str(route.get("disposition")) + "]")
        lines.append("  route cross-concern work: python scripts/sov_session.py route --to <concern> --source <address>")
        return "\\n".join(lines)
    ''',
)

# SessionStart and first-write fallback inherit the same launcher concern hints.
replace(
    ".claude/hooks/session_registry.py",
    '    from sovsession import brief as briefmod\n    store.append(context["directory"], store.SESSIONS_LOG, {\n',
    '    from sovsession import brief as briefmod, concerns\n'
    '    store.append(context["directory"], store.SESSIONS_LOG, {\n',
)
replace(
    ".claude/hooks/session_registry.py",
    '        "intent": "registered on first write, not at session start",\n    })\n',
    '        "intent": "registered on first write, not at session start",\n'
    '        **concerns.session_fields(context["session"]),\n'
    '    })\n',
)
# Second occurrence belongs to mode_start.
replace(
    ".claude/hooks/session_registry.py",
    '    from sovsession import brief as briefmod\n    store.append(context["directory"], store.SESSIONS_LOG, {\n',
    '    from sovsession import brief as briefmod, concerns\n'
    '    store.append(context["directory"], store.SESSIONS_LOG, {\n',
)
replace(
    ".claude/hooks/session_registry.py",
    '        "tree": context["tree"], "branch": briefmod.branch_of(context["root"]),\n        "intent": "",\n    })\n',
    '        "tree": context["tree"], "branch": briefmod.branch_of(context["root"]),\n'
    '        "intent": "", **concerns.session_fields(context["session"]),\n'
    '    })\n',
)

replace(
    "AGENTS.md",
    "### Closure ownership\n",
    '''### One session, one concern

Every operational session binds to one concern for its lifetime. A concern is an
open address used for attribution, attention, source accounting, and routing; it
is **not authority** and there is no closed list of allowed concern names. A new
concern, queue, source, office, institution, or skill does not require a kernel
enum before a participant may name or discover it.

Child agents inherit the source session's concern and source-session lineage. A
session may consume evidence from other concerns without silently becoming them.
When it discovers work that belongs elsewhere, preserve the source and record a
concern route; the destination may admit, queue, delegate, refuse, or redirect it
through its own context. Concern mismatch routes by default. It is not an
authorization refusal unless a real grant, policy, effect, or custody boundary
independently refuses the attempted operation.

Queue and source references are projections of what is available to the session,
not grants. Taking custody remains a separate governed act. This keeps source
processing, queue stewardship, execution, review, witnessing, and settlement
attributable without turning a queue or concern label into authority.

Repository host sessions expose this projection through `python
scripts/sov_session.py console`; cross-concern egress is recorded with `python
scripts/sov_session.py route`. These host records coordinate work and grant no
product standing.

### Closure ownership
''',
)

role_block = '''
## Concern/session discipline

This invocation serves exactly one concern for its lifetime. Preserve the concern
address and source-session lineage you were given; child agents inherit both.
Concern is attribution and routing, never authority. Do not refuse an otherwise
authorized operation merely because its noun or domain is unfamiliar. Discover
skills from `.claude/skills/` and the owning contracts instead of relying on a
closed domain list. If this work discovers a different concern, preserve its
source and route it with `python scripts/sov_session.py route`; do not silently
retarget this session or take the destination concern's custody.
'''
for role in (
    ".claude/agents/sov.md",
    ".claude/agents/sov-controller.md",
    ".claude/agents/sov-orchestrator.md",
    ".claude/agents/sov-worker.md",
    ".claude/agents/sov-witness.md",
):
    append_once(role, "## Concern/session discipline", role_block)

text = read(".claude/agents/sov-orchestrator.md")
old = '''Your prompt names a domain. First load its know-how: invoke the
`sov-<domain>` skill, or read `.claude/skills/sov-<domain>/SKILL.md` directly.
Then read `AGENTS.md` and `STATUS.yaml`. The skill's named operations list is
your menu of legitimately available work; the current open decisions in
`STATUS.yaml` are your gates.
'''
if old not in text:
    raise SystemExit("orchestrator hardcoded skill paragraph moved")
text = text.replace(old, '''Your prompt names a concern and may name a domain hint. Discover relevant
know-how from `.claude/skills/` and load the matching skill when one exists,
then read `AGENTS.md`, `STATUS.yaml`, and the owning contract. A missing
predeclared domain word or `sov-<domain>` skill is not a refusal; actual
operations and authority come from repository contracts and live grants.
''', 1)
write(".claude/agents/sov-orchestrator.md", text)

text = read(".claude/agents/sov-worker.md")
old = '''Your prompt names a domain (governance, contracts, conformance, asset,
proofing, console, byom, or verification). Before anything else, load that domain's
know-how: invoke the `sov-<domain>` skill, or read
`.claude/skills/sov-<domain>/SKILL.md` directly if skill invocation is
unavailable. It defines what the domain owns, what it must not touch, its
open-decision blockers, and its verification commands. Then read `AGENTS.md`
and `STATUS.yaml` before any consequential change.
'''
if old not in text:
    raise SystemExit("worker hardcoded skill paragraph moved")
text = text.replace(old, '''Your prompt names one concern and may name a domain hint. Before anything
else, enumerate `.claude/skills/` and load the relevant skill when one exists,
then read `AGENTS.md`, `STATUS.yaml`, and the owning contract. A missing
hardcoded domain or skill name is not a refusal; the contract, live grant, and
operation define what is actually admissible.
''', 1)
write(".claude/agents/sov-worker.md", text)

text = read(".claude/agents/sov-controller.md")
old = '''- Decompose the goal by domain (governance, contracts, conformance, asset,
  proofing, console, byom, verification) and dispatch the matching workflows or
  agents. Consult each domain's `sov-<domain>` skill and the current open
  decisions in `STATUS.yaml` for what is legitimately available.
'''
if old not in text:
    raise SystemExit("controller hardcoded domain paragraph moved")
text = text.replace(old, '''- Decompose only when the concern actually crosses owned boundaries. Discover
  available skills from `.claude/skills/` and owning contracts rather than a
  closed domain vocabulary. A new concern or skill name is not itself a reason
  to refuse or escalate.
''', 1)
write(".claude/agents/sov-controller.md", text)

# Keep sov-loop concern-scoped while removing its closed domain enum.
path = ".claude/workflows/sov-loop.js"
text = read(path)
text = text.replace(
    "// args: { objective: string, domain?: string, target?: string, plan_only?: boolean, evidence_mode?: boolean }",
    "// args: { objective: string, concern?: string, domain?: string, source_session?: string, queue_refs?: string[], source_refs?: string[], target?: string, plan_only?: boolean, evidence_mode?: boolean }",
)
text = re.sub(r"\nconst DOMAINS = \[[^\n]+\]\n", "\n", text)
text = text.replace(
    "const domain = args && args.domain && DOMAINS.indexOf(args.domain) !== -1 ? args.domain : null",
    "const domain = args && args.domain ? args.domain : null\n"
    "const concernHint = args && args.concern ? args.concern : null\n"
    "const sourceSessionHint = args && args.source_session ? args.source_session : null\n"
    "const queueRefsHint = args && Array.isArray(args.queue_refs) ? args.queue_refs : []\n"
    "const sourceRefsHint = args && Array.isArray(args.source_refs) ? args.source_refs : []",
)
text = text.replace(
    "required: ['concern', 'domain', 'rationale', 'in_grant_scope', 'expected_paths'],",
    "required: ['concern', 'concern_id', 'domain', 'source_session', 'queue_refs', 'source_refs', 'rationale', 'in_grant_scope', 'expected_paths'],",
)
text = text.replace(
    "    concern: { type: 'string' },\n    domain: { type: 'string' },",
    "    concern: { type: 'string' },\n"
    "    concern_id: { type: 'string' },\n"
    "    domain: { type: 'string' },\n"
    "    source_session: { type: 'string' },\n"
    "    queue_refs: { type: 'array', items: { type: 'string' } },\n"
    "    source_refs: { type: 'array', items: { type: 'string' } },",
)
text = text.replace(
    "required: ['operation', 'files', 'effect_class', 'checks', 'defeating_case'],",
    "required: ['concern_id', 'operation', 'files', 'effect_class', 'checks', 'defeating_case'],",
)
text = text.replace(
    "  properties: {\n    operation: { type: 'string' },",
    "  properties: {\n    concern_id: { type: 'string' },\n    operation: { type: 'string' },",
    1,
)
text = text.replace(
    "required: ['changed_paths', 'summary', 'checks_run', 'residuals'],",
    "required: ['concern_id', 'changed_paths', 'summary', 'checks_run', 'residuals', 'cross_concern_routes'],",
)
text = text.replace(
    "  properties: {\n    changed_paths: { type: 'array', items: { type: 'string' } },",
    "  properties: {\n    concern_id: { type: 'string' },\n"
    "    changed_paths: { type: 'array', items: { type: 'string' } },\n"
    "    cross_concern_routes: { type: 'array', items: { type: 'string' } },",
    1,
)
text = text.replace(
    "required: ['verdict', 'observations', 'residuals', 'observation_file'],",
    "required: ['concern_id', 'verdict', 'observations', 'residuals', 'observation_file'],",
)
text = text.replace(
    "  properties: {\n    verdict: { type: 'string' },",
    "  properties: {\n    concern_id: { type: 'string' },\n    verdict: { type: 'string' },",
    1,
)
text = text.replace(
    "required: ['finding_id', 'subject_kind', 'subject_address', 'record_projection_id',",
    "required: ['concern_id', 'finding_id', 'subject_kind', 'subject_address', 'record_projection_id',",
)
text = text.replace(
    "  properties: {\n    finding_id: { type: 'string' },",
    "  properties: {\n    concern_id: { type: 'string' },\n    finding_id: { type: 'string' },",
    1,
)
text = text.replace(
    "  + (domain ? 'Domain: ' + domain + '. ' : 'Pick the single owning domain from: ' + DOMAINS.join(', ') + '. ')",
    "  + (domain ? 'Owning domain hint: ' + domain + '. ' : 'Resolve the owning domain from repository contracts and discoverable skills; no closed domain vocabulary exists here. ')",
)
text = text.replace(
    "  + 'Read AGENTS.md and contracts/standing-grants.json. Name exactly one bounded concern that serves the objective. '",
    "  + 'Read AGENTS.md and contracts/standing-grants.json. Read `python scripts/sov_session.py console --json` when available. Name exactly one bounded concern that serves the objective. ' + (concernHint ? 'The source session supplied concern ' + concernHint + '; preserve it. ' : '') + (sourceSessionHint ? 'Source session: ' + sourceSessionHint + '. ' : '') + (queueRefsHint.length ? 'Available queue refs: ' + queueRefsHint.join(', ') + '. ' : '') + (sourceRefsHint.length ? 'Source refs: ' + sourceRefsHint.join(', ') + '. ' : '') + 'Concern labels route and attribute work; they grant no authority. '",
)
text = text.replace(
    "  + 'Do not build anything. Return the concern, domain, rationale, in_grant_scope, out_of_scope_paths, and the paths you expect to change.',",
    "  + 'Do not build anything. Return concern, concern_id, domain, source_session, queue_refs, source_refs, rationale, in_grant_scope, out_of_scope_paths, and expected paths.',",
)
text = text.replace(
    "  'You hold the Orchestration tier. Turn this concern into exactly one bounded operation: ' + selected.concern + '. '",
    "  'You hold the Orchestration tier. Concern id: ' + selected.concern_id + '. Turn this concern into exactly one bounded operation: ' + selected.concern + '. Preserve the same concern id; do not silently switch concerns. '",
)
text = text.replace(
    "  + 'Read .claude/skills/sov-' + selected.domain + '/SKILL.md, then AGENTS.md, then the owning contract and fixture the skill names. '",
    "  + 'Enumerate .claude/skills/ and load the relevant skill if one exists, then read AGENTS.md and the owning contract/fixture. A missing skill name is not a refusal. '",
)
text = text.replace(
    "  + 'You plan only; you do not build, witness, or dispatch. Return the operation, the exact files, the effect class, the checks that must pass, the defeating case that must fail as declared, and any blockers.',",
    "  + 'You plan only; you do not build, witness, or dispatch. Return unchanged concern_id, operation, exact files, effect class, checks, defeating case, and blockers.',",
)
text = text.replace(
    "if (!plan) {\n  return { error: 'orchestrator returned no plan', concern: selected }\n}",
    "if (!plan) {\n  return { error: 'orchestrator returned no plan', concern: selected }\n}\n"
    "if (plan.concern_id !== selected.concern_id) {\n"
    "  return { error: 'orchestrator changed the session concern instead of routing it', expected: selected.concern_id, observed: plan.concern_id }\n}",
)
text = text.replace(
    "  'You hold the Work tier for exactly one operation: ' + plan.operation + '. '",
    "  'You hold the Work tier for exactly one operation under concern ' + selected.concern_id + ': ' + plan.operation + '. Preserve that concern for this session. '",
)
text = text.replace(
    "  + 'Read .claude/skills/sov-' + selected.domain + '/SKILL.md and AGENTS.md first. Write the defeating case (' + plan.defeating_case + ') and prove it fails as declared before you call the work done. '",
    "  + 'Enumerate .claude/skills/ and load the relevant skill if one exists, then read AGENTS.md. Write the defeating case (' + plan.defeating_case + ') and prove it fails as declared before you call the work done. If you discover another concern, record a route with sov_session.py route; do not retarget this session. '",
)
text = text.replace(
    "  + 'Return every path you changed, a one-paragraph summary, the checks you ran with exit codes, and every residual you know about.',",
    "  + 'Return unchanged concern_id, every path changed, summary, checks with exit codes, residuals, and route ids for cross-concern work you sourced.',",
)
text = text.replace(
    "if (!built) {\n  return { error: 'worker returned no report', concern: selected, plan: plan }\n}",
    "if (!built) {\n  return { error: 'worker returned no report', concern: selected, plan: plan }\n}\n"
    "if (built.concern_id !== selected.concern_id) {\n"
    "  return { error: 'worker changed the session concern instead of routing it', expected: selected.concern_id, observed: built.concern_id }\n}",
)
text = text.replace(
    "'You are in REVIEW mode, not PLAN mode. Judge PARTICIPANT_IN_WORK for the bounded assignment ' + plan.operation + '. ' +",
    "'You are in REVIEW mode under concern ' + selected.concern_id + ', not PLAN mode. Judge PARTICIPANT_IN_WORK for the bounded assignment ' + plan.operation + '. Preserve the concern id. ' +",
)
text = text.replace(
    "'Freeze the Finding before returning it. Return finding_id, subject_kind PARTICIPANT_IN_WORK, subject_address, record_projection_id, projection_as_of, verdict, evidence_addresses, frozen_at, and detail.',",
    "'Freeze the Finding before returning it. Return concern_id, finding_id, subject_kind PARTICIPANT_IN_WORK, subject_address, record_projection_id, projection_as_of, verdict, evidence_addresses, frozen_at, and detail.',",
)
text = text.replace(
    "'You are the independent evaluator of WORK. Concern: ' + selected.concern + '. Operation: ' + plan.operation + '. ' +",
    "'You are the independent evaluator of WORK under concern ' + selected.concern_id + '. Concern: ' + selected.concern + '. Operation: ' + plan.operation + '. Preserve the concern id; independence comes from evaluator/session relation, not changing the concern. ' +",
)
text = text.replace(
    "'Freeze before returning. Return finding_id, subject_kind WORK, subject_address, record_projection_id, projection_as_of, verdict, evidence_addresses, frozen_at, and detail.',",
    "'Freeze before returning. Return concern_id, finding_id, subject_kind WORK, subject_address, record_projection_id, projection_as_of, verdict, evidence_addresses, frozen_at, and detail.',",
)
text = text.replace(
    "'You are the independent observation for work you did not do and must not touch. Concern: ' + selected.concern + '. ' +",
    "'You are the independent observation for work you did not do and must not touch. Concern id: ' + selected.concern_id + '. Concern: ' + selected.concern + '. Preserve the concern id while keeping an independent session/evaluator relation. ' +",
)
text = text.replace(
    "'Return the verdict, what you independently confirmed, residuals, the path you wrote the observation to, and any judgement items only Bdo can settle.',",
    "'Return concern_id, verdict, what you independently confirmed, residuals, the path you wrote the observation to, and any judgement items only Bdo can settle.',",
)
text = text.replace(
    "if (!witnessed) {\n  return { error: 'witness returned no observation; nothing may land unwitnessed', concern: selected, build: built }\n}",
    "if (!witnessed) {\n  return { error: 'witness returned no observation; nothing may land unwitnessed', concern: selected, build: built }\n}\n"
    "if (witnessed.concern_id !== selected.concern_id) {\n"
    "  return { error: 'witness changed the work concern instead of independently evaluating it', expected: selected.concern_id, observed: witnessed.concern_id }\n}",
)
if "const DOMAINS" in text:
    raise SystemExit("closed DOMAINS vocabulary survived workflow patch")
write(path, text)

append_once(
    ".claude/README.md",
    "## Concern-scoped sessions",
    '''
    ## Concern-scoped sessions

    `python scripts/sov_session.py console` is the repository's internal work
    projection. Every live session carries one open concern address, optional
    source-session lineage, source references, and available queue references.
    Those values attribute and route attention; they never grant authority or
    custody. `.claude/skills/` is enumerated from repository bytes, so a new
    concern or skill does not require a central enum edit.

    Cross-concern work is recorded with `python scripts/sov_session.py route`.
    The route carries `authority_effect: NONE` and `custody_effect: NONE`; the
    destination still decides whether to admit, queue, delegate, refuse, or
    redirect it. `sov-loop` carries the source concern through Controller,
    Orchestrator, Worker, and Witness and treats a silent concern switch as a
    provenance defect rather than treating unfamiliar concern words as policy.
    ''',
)

replace(
    "scripts/sov_opening_readiness.py",
    '        "phase_progress_reader": (root / "scripts/sov_active_phase_progress.py").is_file(),\n',
    '        "phase_progress_reader": (root / "scripts/sov_active_phase_progress.py").is_file(),\n'
    '        "session_concern_accounting": _has(root / "scripts/sovsession/concerns.py",\n'
    '                                           "enumerate_concerns", "authority_effect",\n'
    '                                           "custody_effect", "available_skills"),\n'
    '        "concern_scoped_workflow": _has(root / ".claude/workflows/sov-loop.js",\n'
    '                                         "concern_id", "cross_concern_routes",\n'
    '                                         "no closed domain vocabulary"),\n',
)

write(
    "scripts/tests/test_session_concerns.py",
    textwrap.dedent(
        '''
        """Concern-scoped session attribution stays open-world and non-authoritative."""

        from __future__ import annotations

        from pathlib import Path
        import os
        import sys
        import tempfile
        import unittest

        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

        import sov_session  # noqa: E402
        from sovsession import concerns, store  # noqa: E402


        class ConcernResolution(unittest.TestCase):
            def setUp(self) -> None:
                self.saved = {name: os.environ.get(name) for name in
                              ("SOV_CONCERN", "SOV_SOURCE_SESSION", "SOV_SOURCES", "SOV_QUEUES")}
                for name in self.saved:
                    os.environ.pop(name, None)
                self.addCleanup(self.restore)

            def restore(self) -> None:
                for name, value in self.saved.items():
                    if value is None:
                        os.environ.pop(name, None)
                    else:
                        os.environ[name] = value

            def test_explicit_concern_is_open_address_not_enum(self) -> None:
                value, source = concerns.resolve("concern:any/future-citizen-form", "alpha")
                self.assertEqual(value, "concern:any/future-citizen-form")
                self.assertEqual(source, "EXPLICIT")

            def test_environment_supplies_launcher_binding(self) -> None:
                os.environ["SOV_CONCERN"] = "concern:phase-1-5/dev"
                self.assertEqual(concerns.resolve(None, "alpha"),
                                 ("concern:phase-1-5/dev", "ENVIRONMENT"))

            def test_legacy_session_gets_traceable_fallback_not_denial(self) -> None:
                self.assertEqual(concerns.resolve(None, "alpha"),
                                 ("concern:session/alpha", "SESSION_FALLBACK"))

            def test_live_binding_cannot_silently_switch(self) -> None:
                existing = {"concern": "concern:a", "live": True}
                self.assertIn("SESSION_CONCERN_IMMUTABLE",
                              concerns.binding_defect(existing, "concern:b") or "")
                self.assertIsNone(concerns.binding_defect(existing, "concern:a"))


        class ConcernTopology(unittest.TestCase):
            def setUp(self) -> None:
                self.temp = tempfile.TemporaryDirectory()
                self.addCleanup(self.temp.cleanup)
                self.directory = Path(self.temp.name) / "sessions"

            def test_route_preserves_lineage_and_grants_nothing(self) -> None:
                session = {"session": "alpha", "concern": "concern:dev",
                           "source_session": "root"}
                route = concerns.record_route(self.directory, session, "concern:ops",
                                              ["record:event/1"], "queue:ops/intake", "SEEN")
                self.assertEqual(route["source_concern"], "concern:dev")
                self.assertEqual(route["destination_concern"], "concern:ops")
                self.assertEqual(route["authority_effect"], "NONE")
                self.assertEqual(route["custody_effect"], "NONE")
                self.assertEqual(concerns.enumerate_concerns(self.directory),
                                 ["concern:dev", "concern:ops"])

            def test_empty_store_is_an_empty_enumerable_stub(self) -> None:
                self.assertEqual(concerns.enumerate_concerns(self.directory), [])


        class SkillDiscovery(unittest.TestCase):
            def test_new_skill_needs_no_registry_edit(self) -> None:
                with tempfile.TemporaryDirectory() as temp:
                    root = Path(temp)
                    skill = root / ".claude" / "skills" / "future-citizen-skill"
                    skill.mkdir(parents=True)
                    (skill / "SKILL.md").write_text("# skill\n", encoding="utf-8")
                    self.assertEqual(concerns.available_skills(root), ["future-citizen-skill"])


        class CliShape(unittest.TestCase):
            def test_parser_accepts_arbitrary_concern_queue_and_disposition(self) -> None:
                args = sov_session.build_parser().parse_args([
                    "register", "--concern", "concern:novel/thing",
                    "--source", "source:any/1", "--queue", "queue:any/1"])
                self.assertEqual(args.concern, "concern:novel/thing")
                route = sov_session.build_parser().parse_args([
                    "route", "--to", "concern:never-seen-before", "--disposition", "CUSTOM"])
                self.assertEqual(route.to_concern, "concern:never-seen-before")
                self.assertEqual(route.disposition, "CUSTOM")


        class RepositoryContract(unittest.TestCase):
            ROOT = Path(__file__).resolve().parents[2]

            def test_workflow_has_no_closed_domain_enum_and_carries_concern(self) -> None:
                text = (self.ROOT / ".claude" / "workflows" / "sov-loop.js").read_text("utf-8")
                self.assertNotIn("const DOMAINS", text)
                for token in ("concern_id", "source_session", "queue_refs", "source_refs",
                              "cross_concern_routes"):
                    self.assertIn(token, text)

            def test_global_rule_makes_concern_routing_not_authority(self) -> None:
                text = (self.ROOT / "AGENTS.md").read_text("utf-8")
                self.assertIn("One session, one concern", text)
                self.assertIn("Concern mismatch routes by default", text)
                self.assertIn("it is **not authority**", text)

            def test_commissioning_roles_inherit_concern_without_closed_vocabulary(self) -> None:
                for name in ("sov.md", "sov-controller.md", "sov-orchestrator.md",
                             "sov-worker.md", "sov-witness.md"):
                    text = (self.ROOT / ".claude" / "agents" / name).read_text("utf-8")
                    self.assertIn("## Concern/session discipline", text)
                    self.assertIn("Concern is attribution and routing, never authority", text)


        if __name__ == "__main__":
            unittest.main()
        '''
    ).lstrip(),
)

print("prepared concern-scoped session readiness slice")
