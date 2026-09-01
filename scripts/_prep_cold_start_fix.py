from pathlib import Path

path = Path("scripts/sov_opening_readiness.py")
text = path.read_text(encoding="utf-8")
text = text.replace('"Resolve current phase state",', '"current phase state from",')
path.write_text(text, encoding="utf-8", newline="\n")
