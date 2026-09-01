from pathlib import Path

# Keep the opening sentinel wrap-safe.
path = Path("scripts/sov_opening_readiness.py")
text = path.read_text(encoding="utf-8")
text = text.replace('"Resolve current phase state",', '"current phase state from",')
text = text.replace(
    '"next_work_precedence": _has(root / "scripts/sov_next.py",\n'
    '                                     "active phase work", "prepared successor context",\n'
    '                                     "roadmap forecast (non-authoritative)"),',
    '"next_work_precedence": _has(root / "scripts/sovnext_phase.py",\n'
    '                                     "active phase work", "prepared successor context",\n'
    '                                     "roadmap forecast (non-authoritative)"),',
)
path.write_text(text, encoding="utf-8", newline="\n")

# Phase/custody precedence belongs with the phase reader, not in the generic
# signpost reconciler. This keeps sov_next.py under the repository's 300-line
# production ceiling without weakening that ceiling.
phase_path = Path("scripts/sovnext_phase.py")
phase_path.write_text('''"""Phase-authority and custody projection for the non-authoritative next-work reader."""\n\nfrom __future__ import annotations\n\nfrom pathlib import Path\nimport re\n\nfrom sovcustody import collections as custody_collections\nfrom sovsession import phase_context\n\n\ndef position(root: Path) -> tuple[dict, list[dict]]:\n    """Current phase authority plus only that active phase's custody records."""\n    state = phase_context.collect(root)\n    active = state.get("active")\n    if active is None or state.get("defects"):\n        return state, []\n    phase_id = str(active.get("phase_id"))\n    records = custody_collections.records(\n        root / "contracts" / "custodies.json", root / "contracts" / "custodies", phase_id)\n    return state, records\n\n\ndef prepared_horizons(root: Path) -> list[str]:\n    """Prepared human-readable successor horizons; never phase standing."""\n    contracts = root / "contracts"\n    if not contracts.is_dir():\n        return []\n    return [path.relative_to(root).as_posix()\n            for path in sorted(contracts.glob("phase-*-horizon.md")) if path.is_file()]\n\n\ndef active_custody_members(custodies: list[dict], ready: list[dict[str, str]]) -> list[dict]:\n    """Work already drawn under active-phase custody, without promoting it."""\n    ready_by_number = {row["number"]: row for row in ready}\n    rows = []\n    for custody in custodies:\n        if custody.get("terminal"):\n            continue\n        custody_id = str(custody.get("custody_id") or "")\n        for member in custody.get("members") or []:\n            if member.get("work_state") == "RETIRED":\n                continue\n            row = {\n                "custody_id": custody_id,\n                "address": str(member.get("address") or ""),\n                "member_kind": member.get("member_kind"),\n                "stage": member.get("stage"),\n                "standing": member.get("standing"),\n                "work_state": member.get("work_state"),\n                "epic_reachable": False,\n            }\n            match = re.search(r"(?:issue:)?#(\\d+)$", row["address"])\n            if match and match.group(1) in ready_by_number:\n                row["epic_reachable"] = True\n                row["ticket"] = ready_by_number[match.group(1)]\n            rows.append(row)\n    return rows\n\n\ndef render_precedence(active_phase: dict | None, custodies: list[dict],\n                      members: list[dict], horizons: list[str]) -> list[str]:\n    """Render the authority-first portion of next-work output."""\n    lines: list[str] = []\n    if active_phase is not None:\n        lines.append("== active phase custody ==")\n        if custodies:\n            for custody in custodies:\n                terminal = custody.get("terminal")\n                state = terminal.get("outcome") if isinstance(terminal, dict) else "OPEN"\n                lines.append(\n                    f"  {custody.get('custody_id')}  {state}: {custody.get('initiative', '')}")\n        else:\n            lines.append("  none — active phase has no phase-scoped custody; this is opening debt")\n        lines.extend(["", "== active phase work =="])\n        if members:\n            for member in members:\n                marker = "epic-reachable" if member.get("epic_reachable") else "drawn"\n                lines.append(f"  {member['address']} [{member.get('work_state')}] {marker}")\n                lines.append(f"      custody {member['custody_id']}")\n        else:\n            lines.append("  none drawn under active phase custody")\n    else:\n        lines.append("== prepared successor context ==")\n        if horizons:\n            lines.extend(f"  {horizon}  (context only; no standing)" for horizon in horizons)\n        else:\n            lines.append("  none")\n    lines.extend(["", "== roadmap forecast (non-authoritative) =="])\n    return lines\n\n\n__all__ = ["position", "prepared_horizons", "active_custody_members", "render_precedence"]\n''', encoding="utf-8", newline="\n")

next_path = Path("scripts/sov_next.py")
text = next_path.read_text(encoding="utf-8")
start = text.index("\ndef prepared_horizons(root: Path = ROOT) -> list[str]:")
end = text.index("\ndef stale_views(root: Path) -> list[tuple[str, list[str]]]:", start)
text = text[:start] + "\n" + text[end:]
text = text.replace(
    "phase_position = sovnext_phase.position\n",
    "phase_position = sovnext_phase.position\nprepared_horizons = sovnext_phase.prepared_horizons\nactive_custody_members = sovnext_phase.active_custody_members\n",
    1,
)
old = '''    if active_phase is not None:\n        print("\\n== active phase custody ==")\n        if active_custodies:\n            for custody in active_custodies:\n                terminal = custody.get("terminal")\n                state = terminal.get("outcome") if isinstance(terminal, dict) else "OPEN"\n                print(f"  {custody.get('custody_id')}  {state}: {custody.get('initiative', '')}")\n        else:\n            print("  none — active phase has no phase-scoped custody; this is opening debt")\n        print("\\n== active phase work ==")\n        if active_members:\n            for member in active_members:\n                marker = "epic-reachable" if member.get("epic_reachable") else "drawn"\n                print(f"  {member['address']} [{member.get('work_state')}] {marker}")\n                print(f"      custody {member['custody_id']}")\n        else:\n            print("  none drawn under active phase custody")\n    else:\n        print("\\n== prepared successor context ==")\n        if horizons:\n            for horizon in horizons:\n                print(f"  {horizon}  (context only; no standing)")\n        else:\n            print("  none")\n\n    print("\\n== roadmap forecast (non-authoritative) ==")\n'''
new = '''    print("")\n    for line in sovnext_phase.render_precedence(\n            active_phase, active_custodies, active_members, horizons):\n        print(line)\n'''
if old not in text:
    raise SystemExit("generated phase precedence render block missing")
text = text.replace(old, new, 1)
next_path.write_text(text, encoding="utf-8", newline="\n")
