from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

module = ROOT / "scripts/sovnext_phase.py"
module.write_text('''"""Phase-authority reading for the non-authoritative next-work projection."""\n\nfrom __future__ import annotations\n\nfrom pathlib import Path\n\nfrom sovcustody import collections as custody_collections\nfrom sovsession import phase_context\n\n\ndef position(root: Path) -> tuple[dict, list[dict]]:\n    """Current phase authority plus only that active phase's custody records."""\n    state = phase_context.collect(root)\n    active = state.get("active")\n    if active is None or state.get("defects"):\n        return state, []\n    phase_id = str(active.get("phase_id"))\n    records = custody_collections.records(\n        root / "contracts" / "custodies.json", root / "contracts" / "custodies", phase_id)\n    return state, records\n''', encoding="utf-8", newline="\n")

path = ROOT / "scripts/sov_next.py"
text = path.read_text(encoding="utf-8")
text = text.replace(
    "import roadmap_lanes\nfrom sovcustody import collections as custody_collections\nfrom sovsession import phase_context\n",
    "import roadmap_lanes\nimport sovnext_phase\nfrom sovsession import phase_context\n",
    1,
)
start = text.index("def phase_position(root: Path = ROOT)")
end = text.index("def declared_gate(status_text: str)", start)
text = text[:start] + "phase_position = sovnext_phase.position\n\n\n" + text[end:]
path.write_text(text, encoding="utf-8", newline="\n")
