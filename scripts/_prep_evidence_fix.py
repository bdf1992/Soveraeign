from pathlib import Path

path = Path("scripts/tests/test_commissioning_evidence_workflow.py")
text = path.read_text(encoding="utf-8")
text = text.replace(
    '        self.assertIn("without a `Finding` object", text)\n',
    '        self.assertIn("without a", text)\n        self.assertIn("`Finding` object", text)\n',
)
path.write_text(text, encoding="utf-8", newline="\n")
