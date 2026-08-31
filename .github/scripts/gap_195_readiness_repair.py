from __future__ import annotations

from pathlib import Path

path = Path(__file__).with_name("gap_195_readiness_definition.py")
text = path.read_text(encoding="utf-8")
old = '''def refresh_clarity() -> None:
    for path in (
        "PRD.md",
        "SPEC.md",
        "contracts/README.md",
        "diagrams/source-reader-recording.md",
        "diagrams/crossing-typology.md",
        "diagrams/requirement-lifecycle.md",
    ):
'''
new = '''def refresh_clarity() -> None:
    for path in (
        "PRD.md",
        "SPEC.md",
        "contracts/README.md",
    ):
'''
if old not in text:
    raise SystemExit("expected refresh_clarity tuple absent")
text = text.replace(old, new, 1)
old_reviews = '    candidates = list(coverage.get("artifacts", coverage).keys())\n'
new_reviews = '    candidates = list(coverage.get("reviews", {}).keys())\n'
if old_reviews not in text:
    raise SystemExit("expected legacy clarity coverage lookup absent")
text = text.replace(old_reviews, new_reviews, 1)
path.write_text(text, encoding="utf-8", newline="\n")
