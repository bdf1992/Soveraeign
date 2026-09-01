from pathlib import Path

path = Path("scripts/tests/test_session_concerns.py")
text = path.read_text(encoding="utf-8")
text = "\n".join(line[8:] if line.startswith("        ") else line
                 for line in text.splitlines()) + "\n"
text = text.replace('write_text("# skill\n", encoding="utf-8")',
                    'write_text("# skill\\n", encoding="utf-8")')
text = text.replace('self.assertIn("it is **not authority**", text)',
                    'self.assertIn("is **not authority**", text)')
path.write_text(text, encoding="utf-8", newline="\n")
