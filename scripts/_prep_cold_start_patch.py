#!/usr/bin/env python3
"""Apply the Phase 1.5 cold-start/readiness slice on an isolated carrier branch."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"expected source block missing in {path}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


replace(
    "AGENTS.md",
    """The governing documents define repository invariants and boundary rules. When a\nphase is active, phase contracts define that phase's qualification gates. No\nphase is active. Historical phase material is evidence only, and\n`contracts/SUCCESSOR-PREP.md` records the closed-books residue without granting\nsuccessor standing. Treating historical phase evidence as current authority is\na category error.\n""",
    """The governing documents define repository invariants and boundary rules. Resolve\ncurrent phase state from `STATUS.yaml` and `contracts/phases.json` together; a\nreader may surface disagreement between them and may not choose one as a hidden\noverride. When a phase is active, that phase's pinned definition and exit\ncustodies precede roadmap forecasts for actionable work. When the reconciled\nstate is `NONE_ACTIVE`, historical phase material is evidence only and prepared\nsuccessor material remains context without standing until the root seat performs\nthe opening act. `contracts/SUCCESSOR-PREP.md` records closed-books residue; it\ndoes not grant successor standing. Never hardcode an assumed active phase into an\nagent profile, workflow, or next-work reader. Treating historical or prepared\nphase evidence as current authority is a category error.\n""",
)

replace(
    "SOV.md",
    """For each fresh task:\n\n1. Read `AGENTS.md` and this profile at an exact repository revision, then establish or inspect\n   the live repository session with `python scripts/sov_session.py register` and\n   `python scripts/sov_session.py brief`.\n2. Name the task, actor, host, available capabilities, required live grants, and maximum\n   admitted effect class.\n3. Discover the node through `python scripts/sov_interface.py show` and inspect the one named\n   operation or capability relevant to the task.\n4. Load only the contract, fixture, service, decision, status item, seam, and issue material\n   that owns that concern. Read `GROUND.md` and `CANON.md` when product meaning is material,\n   and `STATUS.yaml` when current standing or phase authority is material. Consequential work\n   does not require preloading unrelated governance.\n5. State material omissions, stale or unavailable sources, the expected independent\n   observation, and the refusal or counteraction boundary.\n6. Work one named operation and inspect the result through a path that does not rely only\n   on the executor's report.\n7. If the result reaches an owner-held acceptance boundary, present the result and its\n   evidence. Otherwise continue to the next eligible bounded concern.\n""",
    """For each fresh task, resolve context in this order:\n\n1. **Session.** Read `AGENTS.md` and this profile at an exact repository revision, then\n   establish or inspect the live repository session with `python scripts/sov_session.py\n   register`; read `brief`, and use `console` when you need the full local projection.\n2. **Phase authority.** Use the reconciled `STATUS.yaml` + `contracts/phases.json` reading\n   in SessionStart. If a phase is active, inspect its exit clauses and phase-scoped\n   custodies before roadmap forecasts. If the state is `NONE_ACTIVE`, prepared successor\n   material is context only and grants no permission to execute that successor.\n3. **Assigned work.** Use any live work lease held by this session as the bounded work\n   address. A concern binding without a lease is attribution, not custody. The session\n   console may show several subordinate leases; preserve their parent/witness relation.\n4. **Capability.** Resolve the capability named by the lease when present; otherwise\n   discover the node through `python scripts/sov_interface.py show` and select the one\n   operation or capability relevant to the task.\n5. **Authority and effect.** Read the lease's grant and effect ceiling, then the governing\n   grant/operation contract. No lease, concern, queue, skill, identity, or successful call\n   supplies authority by itself.\n6. **Record context.** When the work requires evidence, consume or create an addressed,\n   scoped `RecordProjection` from the Record service. Never invent a projection id or treat\n   an absent projection as evidence that none is needed.\n7. **Operation.** Load only the contract, fixture, service, decision, status item, seam, and\n   issue material that owns that operation. Read `GROUND.md` and `CANON.md` when product\n   meaning is material. Consequential work does not require preloading unrelated governance.\n8. State material omissions, stale or unavailable sources, the expected independent\n   observation, and the refusal or counteraction boundary; execute one named operation and\n   inspect the result through a path that does not rely only on the executor's report.\n9. If the result reaches an owner-held acceptance boundary, present the result and its\n   evidence. Otherwise continue to the next eligible bounded concern.\n""",
)

replace(
    "ROADMAP.md",
    """Historical `Now`/`Next` lane text below is forecast, not the live work queue.\nWhile `STATUS.yaml` says `phase: NONE_ACTIVE`, issue #148 is the closure ledger and\nno product phase is active. Issue #173 is one candidate successor aperture and gains\nno priority or authority merely by existing. The estimate is expected to be wrong\nin detail and revised often; the PRD is not.\n""",
    """Historical `Now`/`Next` lane text below is forecast, not the live work queue.\nAuthoritative phase state in `STATUS.yaml` plus `contracts/phases.json` always precedes\nthis forecast for next-work selection. `python scripts/sov_next.py` reads an active\nphase, its exit custodies, and work already drawn under those custodies before it shows\nroadmap candidates. When no phase is active it may show prepared successor horizons,\nbut those are context only and gain no priority or authority merely by existing. This\ndocument never opens a phase, creates custody, or promotes a candidate successor. The\nestimate is expected to be wrong in detail and revised often; the PRD is not.\n""",
)

# Join the existing append-preserving lease projection into SessionStart.
brief_path = ROOT / "scripts/sovsession/brief.py"
brief = brief_path.read_text(encoding="utf-8")
brief = brief.replace(
    "from sovsession import claims, concerns, guard, phase_context, principals, store\n",
    "from sovlease import store as lease_store\nfrom sovsession import claims, concerns, guard, phase_context, principals, store\n",
    1,
)
marker = "\ndef collect(root: Path, directory: Path, session: str, tree: str) -> dict[str, Any]:\n"
helper = '''\ndef session_leases(projected: dict[str, dict[str, Any]], session: str,\n                   principal_id: str = "") -> list[dict[str, Any]]:\n    """Live leases actually held by this session/principal; leases grant nothing."""\n    rows = []\n    for lease in projected.values():\n        if lease.get("state") != "HELD":\n            continue\n        holder = lease.get("holder") or {}\n        if holder.get("session") == session or (\n                principal_id and holder.get("principal_id") == principal_id):\n            rows.append(lease)\n    return sorted(rows, key=lambda item: str(item.get("lease_id", "")))\n\n'''
if marker not in brief:
    raise SystemExit("brief collect marker missing")
brief = brief.replace(marker, helper + marker, 1)
old_collect = '''    branch = branch_of(Path(tree))\n    return {\n        "session": session,\n'''
new_collect = '''    branch = branch_of(Path(tree))\n    principal = principals.resolve(root, session)\n    leases = session_leases(lease_store.leases(directory), session,\n                            str(principal.get("principal") or ""))\n    return {\n        "session": session,\n'''
if old_collect not in brief:
    raise SystemExit("brief collect body marker missing")
brief = brief.replace(old_collect, new_collect, 1)
brief = brief.replace(
    '        "next_decision": claims.next_decision_number(root, directory),\n        "principal": principals.resolve(root, session),\n        "phase": phase_context.collect(root),\n',
    '        "next_decision": claims.next_decision_number(root, directory),\n        "principal": principal,\n        "leases": leases,\n        "phase": phase_context.collect(root),\n',
    1,
)
marker = "\ndef _phase(lines: list[str], data: dict[str, Any]) -> None:\n"
lease_render = '''\ndef _lease_context(lines: list[str], data: dict[str, Any]) -> None:\n    """Render only work/effect facts that the live lease ledger actually supplies."""\n    leases = data.get("leases") or []\n    if not leases:\n        return\n    for lease in leases[:4]:\n        concern = lease.get("concern") or {}\n        grant = lease.get("grant") or {}\n        holder = lease.get("holder") or {}\n        reference = concern.get("reference") or "?"\n        capability = concern.get("capability") or "(not named)"\n        grant_id = grant.get("grant_id") or "NONE"\n        effect = grant.get("effect_ceiling") or "UNKNOWN"\n        relation = holder.get("relation") or "?"\n        lines.append(\n            f"  lease: {lease.get('lease_id')} [{relation}] {reference}; "\n            f"capability {capability}; grant {grant_id}; effect ceiling {effect}")\n\n'''
if marker not in brief:
    raise SystemExit("brief phase marker missing")
brief = brief.replace(marker, lease_render + marker, 1)
brief = brief.replace("        _work_context(lines, data)\n        _phase(lines, data[\"phase\"])\n",
                      "        _work_context(lines, data)\n        _phase(lines, data[\"phase\"])\n        _lease_context(lines, data)\n", 1)
brief = brief.replace("    _work_context(lines, data)\n    _phase(lines, data[\"phase\"])\n",
                      "    _work_context(lines, data)\n    _phase(lines, data[\"phase\"])\n    _lease_context(lines, data)\n", 1)
brief = brief.replace(
    '    lines.append("  skills: " + (", ".join(data.get("skills") or []) or "(none)"))\n',
    '    lines.append("  skills: " + (", ".join(data.get("skills") or []) or "(none)"))\n'
    '    leases = data.get("leases") or []\n'
    '    lines.append(f"  live work leases: {len(leases)}")\n'
    '    for lease in leases[:8]:\n'
    '        concern_data = lease.get("concern") or {}\n'
    '        grant = lease.get("grant") or {}\n'
    '        lines.append("    " + str(lease.get("lease_id")) + ": "\n'
    '                     + str(concern_data.get("reference")) + "; capability "\n'
    '                     + str(concern_data.get("capability") or "(not named)")\n'
    '                     + "; grant " + str(grant.get("grant_id") or "NONE")\n'
    '                     + "; effect " + str(grant.get("effect_ceiling") or "UNKNOWN"))\n'
    '    lines.append("  Record projections: only addressed projections supplied or created for this work are evidence; session/lease state does not invent one")\n',
    1,
)
brief_path.write_text(brief, encoding="utf-8", newline="\n")

# Make next-work ordering explicit without making ROADMAP or this reader authoritative.
next_path = ROOT / "scripts/sov_next.py"
text = next_path.read_text(encoding="utf-8")
text = text.replace(
    '"""Reconcile every signpost that claims to say what happens next.\n\nFive documents name the next action in five vocabularies. This reads all of\nthem, resolves the ``ROADMAP.md`` name crosswalk, grades the four-lane shape\nthat roadmap declares, and prints one answer with\nevery alias it travels under. It settles nothing: where the declared gate and\nthe reachable work name different jobs, that disagreement is reported rather\nthan resolved, because choosing between them is judgement and judgement is\nowner-held. Blocked edge is not blocked frontier: a declared gate stops one\ntransition, and the reachable work printed here stays reachable regardless\n(``AGENTS.md``, Authority).\n',
    '"""Reconcile every signpost that claims to say what happens next.\n\nThe ordering is deliberate: authoritative active phase, active-phase custody,\nwork already drawn under that custody, then ROADMAP forecast. With no active\nphase, prepared successor horizons may be shown as context but gain no standing.\nThe reader settles nothing: disagreement is reported rather than resolved, because\nchoosing between competing authoritative claims is judgement and judgement is\nowner-held. Blocked edge is not blocked frontier: a declared gate stops one\ntransition, not every reachable operation (``AGENTS.md``, Authority).\n',
    1,
)
insert = '''\n\ndef prepared_horizons(root: Path = ROOT) -> list[str]:\n    """Human-readable successor horizons present in the tree; never phase standing."""\n    contracts = root / "contracts"\n    if not contracts.is_dir():\n        return []\n    return [path.relative_to(root).as_posix()\n            for path in sorted(contracts.glob("phase-*-horizon.md")) if path.is_file()]\n\n\ndef active_custody_members(custodies: list[dict], ready: list[dict[str, str]]) -> list[dict]:\n    """Project work already drawn under active-phase custody without promoting it."""\n    ready_by_number = {row["number"]: row for row in ready}\n    rows = []\n    for custody in custodies:\n        if custody.get("terminal"):\n            continue\n        custody_id = str(custody.get("custody_id") or "")\n        for member in custody.get("members") or []:\n            if member.get("work_state") == "RETIRED":\n                continue\n            row = {\n                "custody_id": custody_id,\n                "address": str(member.get("address") or ""),\n                "member_kind": member.get("member_kind"),\n                "stage": member.get("stage"),\n                "standing": member.get("standing"),\n                "work_state": member.get("work_state"),\n                "epic_reachable": False,\n            }\n            match = re.search(r"(?:issue:)?#(\\d+)$", row["address"])\n            if match and match.group(1) in ready_by_number:\n                row["epic_reachable"] = True\n                row["ticket"] = ready_by_number[match.group(1)]\n            rows.append(row)\n    return rows\n'''
marker = "\ndef stale_views(root: Path) -> list[tuple[str, list[str]]]:\n"
if marker not in text:
    raise SystemExit("sov_next insertion marker missing")
text = text.replace(marker, insert + marker, 1)
text = text.replace(
    "    active_phase = phase_state.get(\"active\")\n    phases = roadmap_phases(roadmap_text)\n",
    "    active_phase = phase_state.get(\"active\")\n    horizons = prepared_horizons(ROOT)\n    phases = roadmap_phases(roadmap_text)\n",
    1,
)
text = text.replace(
    "    ready = epic_ready(issues)\n    stale = stale_views(ROOT)\n",
    "    ready = epic_ready(issues)\n    active_members = active_custody_members(active_custodies, ready)\n    stale = stale_views(ROOT)\n",
    1,
)
text = text.replace(
    '        print(json.dumps({"phase": phase_state, "active_phase_custodies": active_custodies,\n                          "declared_gate": gate, "crosswalk": rows, "ready": ready,\n',
    '        print(json.dumps({"phase": phase_state, "prepared_horizons": horizons,\n                          "active_phase_custodies": active_custodies,\n                          "active_custody_members": active_members,\n                          "declared_gate": gate, "crosswalk": rows, "ready": ready,\n',
    1,
)
old_render = '''    if active_phase is not None:\n        print("\\n== active phase custody ==")\n        if active_custodies:\n            for custody in active_custodies:\n                print(f"  {custody.get('custody_id')}  {custody.get('terminal', custody.get('standing', '?'))}")\n        else:\n            print("  none — active phase has no phase-scoped custody; this is opening debt")\n\n    print("\\n== roadmap reachable work ==")\n'''
new_render = '''    if active_phase is not None:\n        print("\\n== active phase custody ==")\n        if active_custodies:\n            for custody in active_custodies:\n                terminal = custody.get("terminal")\n                state = terminal.get("outcome") if isinstance(terminal, dict) else "OPEN"\n                print(f"  {custody.get('custody_id')}  {state}: {custody.get('initiative', '')}")\n        else:\n            print("  none — active phase has no phase-scoped custody; this is opening debt")\n        print("\\n== active phase work ==")\n        if active_members:\n            for member in active_members:\n                marker = "epic-reachable" if member.get("epic_reachable") else "drawn"\n                print(f"  {member['address']} [{member.get('work_state')}] {marker}")\n                print(f"      custody {member['custody_id']}")\n        else:\n            print("  none drawn under active phase custody")\n    else:\n        print("\\n== prepared successor context ==")\n        if horizons:\n            for horizon in horizons:\n                print(f"  {horizon}  (context only; no standing)")\n        else:\n            print("  none")\n\n    print("\\n== roadmap forecast (non-authoritative) ==")\n'''
if old_render not in text:
    raise SystemExit("sov_next render marker missing")
text = text.replace(old_render, new_render, 1)
text = text.replace(
    '    print("\\nPASS: every crosswalk row resolves, every phase carries its four "\n          "lanes, and no signpost disagrees")\n',
    '    print("\\nPASS: phase/custody precedence is explicit, every crosswalk row resolves, "\n          "every roadmap phase carries its four lanes, and no signpost disagrees")\n',
    1,
)
next_path.write_text(text, encoding="utf-8", newline="\n")

# Opening rehearsal should refuse if the cold-start mechanics regress before opening.
opening = ROOT / "scripts/sov_opening_readiness.py"
text = opening.read_text(encoding="utf-8")
needle = '''        "concern_scoped_workflow": _has(root / ".claude/workflows/sov-loop.js",\n                                         "concern_id", "cross_concern_routes",\n                                         "no closed domain vocabulary"),\n'''
addition = needle + '''        "cold_start_phase_resolution": _has(root / "AGENTS.md",\n                                             "Resolve current phase state",\n                                             "Never hardcode an assumed active phase"),\n        "cold_start_lease_projection": _has(root / "scripts/sovsession/brief.py",\n                                             "session_leases", "effect ceiling",\n                                             "Record projections"),\n        "next_work_precedence": _has(root / "scripts/sov_next.py",\n                                     "active phase work", "prepared successor context",\n                                     "roadmap forecast (non-authoritative)"),\n        "sov_context_order": _has(root / "SOV.md", "**Phase authority.**",\n                                  "**Assigned work.**", "`RecordProjection`",\n                                  "**Operation.**"),\n'''
if needle not in text:
    raise SystemExit("opening readiness marker missing")
opening.write_text(text.replace(needle, addition, 1), encoding="utf-8", newline="\n")

# Focused positive/defeating cases for the new joins and precedence.
test = ROOT / "scripts/tests/test_phase15_cold_start.py"
test.write_text('''"""Focused cold-start cases for the prepared Phase 1.5 operating substrate."""\n\nfrom __future__ import annotations\n\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\nimport sys\nimport unittest\n\nROOT = Path(__file__).resolve().parents[2]\nsys.path.insert(0, str(ROOT / "scripts"))\n\nimport sov_next  # noqa: E402\nfrom sovsession import brief  # noqa: E402\n\n\ndef lease(lease_id: str, session: str, state: str = "HELD", effect: str = "RECORD_LOCAL") -> dict:\n    return {\n        "lease_id": lease_id,\n        "state": state,\n        "concern": {"kind": "concern", "reference": "concern:test",\n                    "capability": "record.project-evidence"},\n        "holder": {"session": session, "principal_id": f"principal:{session}",\n                   "relation": "PARENT"},\n        "grant": {"grant_id": None, "effect_ceiling": effect},\n    }\n\n\nclass SessionLeaseProjection(unittest.TestCase):\n    def test_only_live_leases_held_by_this_session_are_projected(self) -> None:\n        projected = {\n            "lease:a": lease("lease:a", "alpha"),\n            "lease:b": lease("lease:b", "beta"),\n            "lease:c": lease("lease:c", "alpha", state="COMPLETED"),\n        }\n        rows = brief.session_leases(projected, "alpha", "principal:alpha")\n        self.assertEqual([row["lease_id"] for row in rows], ["lease:a"])\n\n    def test_principal_join_recovers_a_lease_without_session_field(self) -> None:\n        row = lease("lease:a", "alpha")\n        row["holder"]["session"] = None\n        rows = brief.session_leases({"lease:a": row}, "different", "principal:alpha")\n        self.assertEqual([item["lease_id"] for item in rows], ["lease:a"])\n\n    def test_brief_renders_actual_capability_grant_and_effect_from_lease(self) -> None:\n        lines: list[str] = []\n        brief._lease_context(lines, {"leases": [lease("lease:a", "alpha")]})\n        rendered = "\\n".join(lines)\n        self.assertIn("record.project-evidence", rendered)\n        self.assertIn("grant NONE", rendered)\n        self.assertIn("effect ceiling RECORD_LOCAL", rendered)\n\n\nclass NextWorkPrecedence(unittest.TestCase):\n    def test_prepared_horizon_is_discovered_without_becoming_phase_state(self) -> None:\n        with TemporaryDirectory() as tmp:\n            root = Path(tmp)\n            (root / "contracts").mkdir()\n            (root / "contracts" / "phase-1-5-phase-ii-horizon.md").write_text("prepared\\n")\n            self.assertEqual(sov_next.prepared_horizons(root),\n                             ["contracts/phase-1-5-phase-ii-horizon.md"])\n\n    def test_active_custody_members_preserve_arbitrary_member_kinds(self) -> None:\n        custodies = [{\n            "custody_id": "custody:test",\n            "members": [\n                {"member_kind": "TICKET", "address": "issue:#7", "stage": "ROOT_POINT",\n                 "standing": "OPEN", "work_state": "READY"},\n                {"member_kind": "OPERATION", "address": "sov://new/do-thing",\n                 "stage": "VERTICAL_SLICE", "standing": "BUILT",\n                 "work_state": "IN_PROGRESS"},\n            ],\n        }]\n        ready = [{"number": "7", "title": "ticket", "standing": "OPEN", "horizon": "NOW"}]\n        rows = sov_next.active_custody_members(custodies, ready)\n        self.assertEqual([row["address"] for row in rows], ["issue:#7", "sov://new/do-thing"])\n        self.assertTrue(rows[0]["epic_reachable"])\n        self.assertFalse(rows[1]["epic_reachable"])\n\n    def test_terminal_custody_and_retired_member_do_not_appear_as_active_work(self) -> None:\n        custodies = [\n            {"custody_id": "custody:terminal", "terminal": {"outcome": "SETTLED"},\n             "members": [{"address": "issue:#1", "work_state": "READY"}]},\n            {"custody_id": "custody:live", "members": [\n                {"member_kind": "ITEM", "address": "thing:old", "stage": "ROOT_POINT",\n                 "standing": "OPEN", "work_state": "RETIRED"}]},\n        ]\n        self.assertEqual(sov_next.active_custody_members(custodies, []), [])\n\n\nclass RepositoryContract(unittest.TestCase):\n    def test_agent_contract_does_not_hardcode_current_phase(self) -> None:\n        text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")\n        self.assertNotIn("No phase is active.", text)\n        self.assertIn("Never hardcode an assumed active phase", text)\n\n    def test_sov_orders_context_before_operation(self) -> None:\n        text = (ROOT / "SOV.md").read_text(encoding="utf-8")\n        order = [text.index(token) for token in (\n            "**Session.**", "**Phase authority.**", "**Assigned work.**",\n            "**Capability.**", "**Authority and effect.**", "**Record context.**",\n            "**Operation.**")]\n        self.assertEqual(order, sorted(order))\n\n\nif __name__ == "__main__":\n    unittest.main()\n''', encoding="utf-8", newline="\n")
