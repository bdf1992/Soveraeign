from __future__ import annotations

from pathlib import Path

path = Path(__file__).with_name("gap_195_readiness_definition.py")
text = path.read_text(encoding="utf-8")
for line in (
    '        "diagrams/source-reader-recording.md",\n',
    '        "diagrams/crossing-typology.md",\n',
    '        "diagrams/requirement-lifecycle.md",\n',
):
    if line not in text:
        raise SystemExit(f"expected clarity-scope line absent: {line.strip()}")
    text = text.replace(line, "", 1)
path.write_text(text, encoding="utf-8", newline="\n")
