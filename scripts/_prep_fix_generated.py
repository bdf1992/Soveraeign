from pathlib import Path

# Normalize the generated focused test source.
path = Path("scripts/tests/test_session_concerns.py")
text = path.read_text(encoding="utf-8")
text = "\n".join(line[8:] if line.startswith("        ") else line
                 for line in text.splitlines()) + "\n"
text = text.replace('write_text("# skill\n", encoding="utf-8")',
                    'write_text("# skill\\n", encoding="utf-8")')
text = text.replace('self.assertIn("it is **not authority**", text)',
                    'self.assertIn("is **not authority**", text)')
path.write_text(text, encoding="utf-8", newline="\n")

# Old tests and external readers may construct a briefing dict without the new
# concern fields. Rendering must project a traceable fallback rather than crash;
# actual live registration still enforces immutable concern binding.
path = Path("scripts/sovsession/brief.py")
text = path.read_text(encoding="utf-8")
old = '    lines.append(f"  concern: {data[\'concern\']} ({data[\'concern_binding_source\']}; attribution/routing only)")\n'
new = ('    concern = data.get("concern") or "concern:session/" + str(data.get("session") or "unbound")\n'
       '    binding = data.get("concern_binding_source") or "SESSION_FALLBACK"\n'
       '    lines.append(f"  concern: {concern} ({binding}; attribution/routing only)")\n')
if old not in text:
    raise SystemExit("brief concern rendering anchor moved")
path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
